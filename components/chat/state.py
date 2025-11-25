"""
对话状态管理
"""
import streamlit as st
import uuid
import threading
import queue
import time
import logging
from typing import Optional, Dict, Any

from services import get_rag_service, get_session_service

logger = logging.getLogger(__name__)

def init_conversation_manager():
    """初始化对话管理器"""
    if 'active_conversations' not in st.session_state:
        st.session_state.active_conversations = {}
    if 'current_conversation_id' not in st.session_state:
        st.session_state.current_conversation_id = None

def background_generation(conv_id: str, user_id: int, question: str, update_queue: queue.Queue):
    """生成线程：执行流式生成（在独立线程中运行，不阻塞UI）"""
    rag_service = get_rag_service()
    
    try:
        logger.info(f"[生成线程] 开始生成对话 {conv_id}, 问题: {question[:50]}...")
        chunk_count = 0
        valid_chunk_count = 0
        
        for response in rag_service.query_stream(user_id, question):
            if response['type'] == 'chunk':
                chunk_count += 1
                chunk_content = response.get('content', '')
                
                # 优化：过滤空chunk，不放入队列
                if not chunk_content:
                    logger.debug(f"[生成线程] {conv_id} 跳过空 chunk #{chunk_count}")
                    continue
                
                valid_chunk_count += 1
                logger.debug(f"[生成线程] {conv_id} 收到有效 chunk #{valid_chunk_count}, 大小: {len(chunk_content)} 字符")
            elif response['type'] == 'thinking':
                logger.debug(f"[生成线程] {conv_id} 收到 thinking 更新")
            elif response['type'] == 'complete':
                logger.info(f"[生成线程] {conv_id} 生成完成，共收到 {chunk_count} 个chunk ({valid_chunk_count} 个有效)")
            
            # 只放入有效更新（空chunk已被过滤）
            update_queue.put({
                'conv_id': conv_id,
                'type': response['type'],
                'data': response
            })
        logger.info(f"[生成线程] {conv_id} 流式生成结束")
    except Exception as e:
        logger.error(f"[生成线程] {conv_id} 生成出错: {str(e)}", exc_info=True)
        update_queue.put({
            'conv_id': conv_id,
            'type': 'error',
            'error': str(e)
        })

def create_conversation(user_id: int, question: str) -> str:
    """创建新对话并启动后台线程"""
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"
    update_queue = queue.Queue()
    
    # 立即保存会话和用户消息到数据库
    # 创建会话并立即缓存清除，确保会话列表实时更新
    session_service = get_session_service()
    session_id = session_service.create_session(user_id, question)
    # 清除session缓存（新会话）
    from services import get_cached_sessions
    get_cached_sessions.clear()
    session_service.save_message(
        session_id=session_id,
        role='user',
        content=question
    )  
    
    # 创建状态
    state = {
        'conversation_id': conv_id,
        'user_id': user_id,
        'question': question,
        'messages': [{'role': 'user', 'content': question}],
        'status': 'generating',
        'current_answer': '',
        'result': None,
        'thread': None,
        'update_queue': update_queue,
        'created_at': time.time(),
        'session_id': session_id,
        'error': None,
    }
    
    # 启动线程
    thread = threading.Thread(
        target=background_generation,
        args=(conv_id, user_id, question, update_queue),
        daemon=True
    )
    state['thread'] = thread
    thread.start()
    
    # 保存状态
    st.session_state.active_conversations[conv_id] = state
    st.session_state.current_conversation_id = conv_id
    
    logger.info(f"[UI线程] 创建对话 {conv_id}，已立即保存会话 {session_id} 和用户消息")
    
    return conv_id

def save_conversation_to_db(conv_id: str):
    """保存AI回复到数据库（用户消息已在创建对话时保存）"""
    state = st.session_state.active_conversations.get(conv_id)
    if not state or state['status'] != 'completed':
        return
    
    session_id = state.get('session_id')
    if not session_id:
        session_service = get_session_service()
        session_id = session_service.create_session(state['user_id'], state['question'])
        state['session_id'] = session_id
        session_service.save_message(
            session_id=session_id,
            role='user',
            content=state['question']
        )
        logger.info(f"[UI线程] 对话 {conv_id} 延迟创建会话 {session_id} 和用户消息")
    
    if state.get('ai_message_saved'):
        return
    
    session_service = get_session_service()
    result = state['result']
    
    session_service.save_message(
        session_id=session_id,
        role='assistant',
        content=result['answer'],
        retrieved_docs=result.get('retrieved_docs'),
        thinking_process=result.get('thinking_process'),
        tokens_used=result.get('tokens_used', 0)
    )
    
    state['ai_message_saved'] = True
    logger.info(f"[UI线程] 对话 {conv_id} 保存AI回复到会话 {session_id}")

def process_all_updates() -> dict:
    """
    处理所有对话的Queue更新
    
    Returns:
        dict: {
            'updated': bool,  # 是否有更新
            'chunk_count': int,  # 处理的chunk数量
            'total_count': int,  # 处理的总更新数量
        }
    """
    current_conv_id = st.session_state.current_conversation_id
    current_updated = False
    chunk_count = 0
    total_count = 0
    
    # 批量处理配置
    MAX_BATCH_SIZE = 10  # 每批最多处理10个更新
    
    # 优先处理当前对话的更新
    if current_conv_id:
        current_state = st.session_state.active_conversations.get(current_conv_id)
        if current_state and not current_state['update_queue'].empty():
            batch_size = 0
            
            # 批量处理：一次性处理队列中的多个chunk
            while not current_state['update_queue'].empty() and batch_size < MAX_BATCH_SIZE:
                try:
                    update = current_state['update_queue'].get_nowait()
                    batch_size += 1
                    total_count += 1
                    
                    if update['type'] == 'chunk':
                        chunk_content = update['data'].get('content', '')
                        # 空chunk已在生成线程过滤，这里直接累积
                        current_state['current_answer'] += chunk_content
                        current_updated = True
                        chunk_count += 1
                        
                    elif update['type'] == 'complete':
                        # 遇到complete立即处理并退出批处理
                        current_state['status'] = 'completed'
                        current_state['result'] = update['data']
                        current_state['current_answer'] = update['data']['answer']
                        current_state['messages'].append({
                            'role': 'assistant',
                            'content': update['data']['answer'],
                            'retrieved_docs': update['data'].get('retrieved_docs'),
                            'thinking_process': update['data'].get('thinking_process')
                        })
                        save_conversation_to_db(current_conv_id)
                        current_updated = True
                        break  # complete后立即退出批处理
                        
                    elif update['type'] == 'error':
                        # 遇到error立即处理并退出批处理
                        current_state['status'] = 'error'
                        current_state['error'] = update.get('error', '未知错误')
                        current_updated = True
                        break  # error后立即退出批处理
                        
                except queue.Empty:
                    break
            
            if current_updated and total_count > 0:
                logger.info(f"[UI线程] 当前对话 {current_conv_id} 批量处理 {total_count} 个更新 (其中 {chunk_count} 个chunk), 累积长度: {len(current_state['current_answer'])} 字符")
    
    # 处理其他对话的更新（也使用批量处理）
    for conv_id, state in st.session_state.active_conversations.items():
        if conv_id == current_conv_id:
            continue
        
        if not state['update_queue'].empty():
            batch_size = 0
            
            while not state['update_queue'].empty() and batch_size < MAX_BATCH_SIZE:
                try:
                    update = state['update_queue'].get_nowait()
                    batch_size += 1
                    
                    if update['type'] == 'chunk':
                        chunk_content = update['data'].get('content', '')
                        state['current_answer'] += chunk_content
                        
                    elif update['type'] == 'complete':
                        state['status'] = 'completed'
                        state['result'] = update['data']
                        state['current_answer'] = update['data']['answer']
                        state['messages'].append({
                            'role': 'assistant',
                            'content': update['data']['answer'],
                            'retrieved_docs': update['data'].get('retrieved_docs'),
                            'thinking_process': update['data'].get('thinking_process')
                        })
                        save_conversation_to_db(conv_id)
                        break
                        
                    elif update['type'] == 'error':
                        state['status'] = 'error'
                        state['error'] = update.get('error', '未知错误')
                        break
                        
                except queue.Empty:
                    break
    
    return {
        'updated': current_updated,
        'chunk_count': chunk_count,
        'total_count': total_count
    }

def cleanup_completed_threads():
    """清理已完成的线程"""
    if 'active_conversations' in st.session_state:
        for conv_id, state in list(st.session_state.active_conversations.items()):
            if state['status'] in ['completed', 'error']:
                if state.get('thread') and not state['thread'].is_alive():
                    state['thread'] = None

def load_session_messages(session_id: str, session_service):
    """加载历史会话到新的对话管理系统"""
    init_conversation_manager()
    
    existing_conv_id = None
    for conv_id, state in st.session_state.active_conversations.items():
        if state.get('session_id') == session_id:
            existing_conv_id = conv_id
            break
    
    if existing_conv_id:
        st.session_state.current_conversation_id = existing_conv_id
        return
    
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"
    messages = session_service.get_session_messages(session_id)
    
    from database import SessionDAO
    from utils.db_error_handler import safe_db_operation, show_db_error_ui
    
    session_dao = SessionDAO()
    try:
        session = safe_db_operation(
            lambda: session_dao.get_session(session_id),
            default_value=None,
            error_context="获取会话信息"
        )
        user_id = session.user_id if session else None
    except Exception as e:
        show_db_error_ui(e, "获取会话信息")
        user_id = None
    
    chat_messages = []
    for msg in messages:
        chat_messages.append({
            "role": msg['role'],
            "content": msg['content'],
            "retrieved_docs": msg.get('retrieved_docs'),
            "thinking_process": msg.get('thinking_process')
        })
    
    state = {
        'conversation_id': conv_id,
        'session_id': session_id,
        'user_id': user_id,
        'question': chat_messages[0]['content'] if chat_messages and chat_messages[0]['role'] == 'user' else '',
        'messages': chat_messages,
        'status': 'completed',
        'current_answer': '',
        'result': None,
        'thread': None,
        'update_queue': queue.Queue(),
        'created_at': time.time(),
        'error': None,
    }
    
    st.session_state.active_conversations[conv_id] = state
    st.session_state.current_conversation_id = conv_id
