"""
对话界面组件
"""
import streamlit as st
from typing import Optional
import uuid
import threading
import queue
import time
import logging

from services import get_rag_service, get_session_service

# 获取日志记录器（日志格式已在 app.py 中配置）
logger = logging.getLogger(__name__)


def _init_conversation_manager():
    """初始化对话管理器"""
    if 'active_conversations' not in st.session_state:
        st.session_state.active_conversations = {}
    if 'current_conversation_id' not in st.session_state:
        st.session_state.current_conversation_id = None


def _background_generation(conv_id: str, user_id: int, question: str, update_queue: queue.Queue):
    """生成线程：执行流式生成（在独立线程中运行，不阻塞UI）"""
    rag_service = get_rag_service()
    
    try:
        logger.info(f"[生成线程] 开始生成对话 {conv_id}, 问题: {question[:50]}...")
        chunk_count = 0
        for response in rag_service.query_stream(user_id, question):
            if response['type'] == 'chunk':
                chunk_count += 1
                # 修复：response 结构是 {'type': 'chunk', 'content': '...'}，不是 {'type': 'chunk', 'data': {'content': '...'}}
                chunk_content = response.get('content', '')
                chunk_size = len(chunk_content)
                if chunk_size > 0:
                    logger.info(f"[生成线程] {conv_id} 收到 chunk #{chunk_count}, 大小: {chunk_size} 字符, 内容: {chunk_content[:30]}...")
                else:
                    logger.warning(f"[生成线程] {conv_id} 收到空 chunk #{chunk_count}，仍然放入队列（由UI线程决定是否处理）")
            elif response['type'] == 'thinking':
                logger.info(f"[生成线程] {conv_id} 收到 thinking 更新")
            elif response['type'] == 'complete':
                logger.info(f"[生成线程] {conv_id} 生成完成，共收到 {chunk_count} 个有效 chunk")
            
            # 将整个 response 作为 data 传递（保持兼容性）
            update_queue.put({
                'conv_id': conv_id,
                'type': response['type'],
                'data': response  # response 本身就是完整的数据结构
            })
        logger.info(f"[生成线程] {conv_id} 流式生成结束")
    except Exception as e:
        logger.error(f"[生成线程] {conv_id} 生成出错: {str(e)}", exc_info=True)
        update_queue.put({
            'conv_id': conv_id,
            'type': 'error',
            'error': str(e)
        })


def _process_all_updates() -> bool:
    """处理所有对话的Queue更新，返回当前对话是否有更新
    
    注意：为了流式显示，每次只处理一个更新，然后立即返回让UI刷新
    优先处理当前对话的更新
    """
    current_conv_id = st.session_state.current_conversation_id
    current_updated = False
    processed_count = 0
    
    # 优先处理当前对话的更新
    if current_conv_id:
        current_state = st.session_state.active_conversations.get(current_conv_id)
        if current_state and not current_state['update_queue'].empty():
            try:
                update = current_state['update_queue'].get_nowait()
                processed_count += 1
                
                if update['type'] == 'chunk':
                    # 修复：data 结构是 {'type': 'chunk', 'content': '...'}，直接访问 content
                    chunk_content = update['data'].get('content', '')
                    if chunk_content:  # 只处理非空chunk
                        current_state['current_answer'] += chunk_content
                        logger.info(f"[UI线程] 当前对话 {current_conv_id} 处理 chunk, 累积长度: {len(current_state['current_answer'])} 字符, 本次: {len(chunk_content)} 字符")
                    else:
                        logger.warning(f"[UI线程] 当前对话 {current_conv_id} 收到空 chunk，跳过")
                elif update['type'] == 'complete':
                    current_state['status'] = 'completed'
                    current_state['result'] = update['data']
                    current_state['current_answer'] = update['data']['answer']
                    logger.info(f"[UI线程] 当前对话 {current_conv_id} 处理 complete, 总长度: {len(current_state['current_answer'])} 字符")
                    # 添加助手消息
                    current_state['messages'].append({
                        'role': 'assistant',
                        'content': update['data']['answer'],
                        'retrieved_docs': update['data'].get('retrieved_docs'),
                        'thinking_process': update['data'].get('thinking_process')
                    })
                    # 保存到数据库
                    _save_conversation_to_db(current_conv_id)
                elif update['type'] == 'thinking':
                    logger.info(f"[UI线程] 当前对话 {current_conv_id} 处理 thinking 更新")
                elif update['type'] == 'error':
                    current_state['status'] = 'error'
                    current_state['error'] = update.get('error', '未知错误')
                    logger.error(f"[UI线程] 当前对话 {current_conv_id} 处理 error: {current_state['error']}")
                
                current_updated = True
                logger.info(f"[UI线程] 当前对话 {current_conv_id} 有更新，已处理 {processed_count} 个更新，立即返回以刷新UI")
                return True
                    
            except queue.Empty:
                pass
    
    # 处理其他对话的更新（非当前对话）
    for conv_id, state in st.session_state.active_conversations.items():
        if conv_id == current_conv_id:
            continue  # 已经处理过了
        
        # 关键修改：每次只处理一个更新，而不是处理所有更新
        # 这样可以确保流式显示，而不是一次性显示所有内容
        if not state['update_queue'].empty():
            try:
                update = state['update_queue'].get_nowait()
                processed_count += 1
                
                if update['type'] == 'chunk':
                    # 修复：data 结构是 {'type': 'chunk', 'content': '...'}，直接访问 content
                    chunk_content = update['data'].get('content', '')
                    if chunk_content:  # 只处理非空chunk
                        state['current_answer'] += chunk_content
                        logger.info(f"[UI线程] 后台对话 {conv_id} 处理 chunk, 累积长度: {len(state['current_answer'])} 字符")
                elif update['type'] == 'complete':
                    state['status'] = 'completed'
                    state['result'] = update['data']
                    state['current_answer'] = update['data']['answer']
                    logger.info(f"[UI线程] 后台对话 {conv_id} 处理 complete, 总长度: {len(state['current_answer'])} 字符")
                    # 添加助手消息
                    state['messages'].append({
                        'role': 'assistant',
                        'content': update['data']['answer'],
                        'retrieved_docs': update['data'].get('retrieved_docs'),
                        'thinking_process': update['data'].get('thinking_process')
                    })
                    # 保存到数据库
                    _save_conversation_to_db(conv_id)
                elif update['type'] == 'thinking':
                    logger.info(f"[UI线程] 后台对话 {conv_id} 处理 thinking 更新")
                elif update['type'] == 'error':
                    state['status'] = 'error'
                    state['error'] = update.get('error', '未知错误')
                    logger.error(f"[UI线程] 后台对话 {conv_id} 处理 error: {state['error']}")
                    
            except queue.Empty:
                break
    
    if processed_count > 0:
        logger.info(f"[UI线程] 本次处理了 {processed_count} 个更新（非当前对话）")
    
    return current_updated


def _create_conversation(user_id: int, question: str) -> str:
    """创建新对话并启动后台线程"""
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"
    update_queue = queue.Queue()
    
    # 立即保存会话和用户消息到数据库
    session_service = get_session_service()
    session_id = session_service.create_session(user_id, question)
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
        'session_id': session_id,  # 立即保存会话ID
        'error': None,
    }
    
    # 启动线程
    thread = threading.Thread(
        target=_background_generation,
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


def _cleanup_completed_threads():
    """清理已完成的线程"""
    for conv_id, state in list(st.session_state.active_conversations.items()):
        if state['status'] in ['completed', 'error']:
            if state.get('thread') and not state['thread'].is_alive():
                state['thread'] = None


def _save_conversation_to_db(conv_id: str):
    """保存AI回复到数据库（用户消息已在创建对话时保存）"""
    state = st.session_state.active_conversations.get(conv_id)
    if not state or state['status'] != 'completed':
        return
    
    # 如果会话ID不存在，说明是旧代码创建的对话，需要创建会话
    # 正常情况下，会话ID应该在创建对话时就已经存在了
    session_id = state.get('session_id')
    if not session_id:
        session_service = get_session_service()
        session_id = session_service.create_session(state['user_id'], state['question'])
        state['session_id'] = session_id
        # 保存用户消息（如果之前没有保存）
        session_service.save_message(
            session_id=session_id,
            role='user',
            content=state['question']
        )
        logger.info(f"[UI线程] 对话 {conv_id} 延迟创建会话 {session_id} 和用户消息")
    
    # 检查是否已经保存过AI回复（避免重复保存）
    if state.get('ai_message_saved'):
        return
    
    session_service = get_session_service()
    result = state['result']
    
    # 保存 AI 回复
    session_service.save_message(
        session_id=session_id,
        role='assistant',
        content=result['answer'],
        retrieved_docs=result.get('retrieved_docs'),
        thinking_process=result.get('thinking_process'),
        tokens_used=result.get('tokens_used', 0)
    )
    
    # 标记已保存
    state['ai_message_saved'] = True
    logger.info(f"[UI线程] 对话 {conv_id} 保存AI回复到会话 {session_id}")


def show_chat_interface(user_id: int):
    """显示对话界面"""
    
    st.title("💬 智能问答")
    
    # 初始化对话管理器
    _init_conversation_manager()
    
    # 显示消息历史（先显示，确保用户消息立即可见）
    _display_messages()
    
    # 处理所有更新（处理chunk更新）
    current_updated = _process_all_updates()
    
    # 检查当前对话是否正在生成
    current_conv_id = st.session_state.current_conversation_id
    current_conv = st.session_state.active_conversations.get(current_conv_id) if current_conv_id else None
    is_generating = current_conv and current_conv['status'] == 'generating'
    
    # 如果正在生成，延迟刷新UI（无论是否有更新）
    if is_generating:
        # 检查队列中是否还有待处理的更新
        has_pending_updates = current_conv and not current_conv['update_queue'].empty()
        if has_pending_updates:
            logger.info(f"[UI线程] 对话 {current_conv_id} 正在生成，队列中有待处理更新，立即刷新")
            # 如果有待处理更新，立即刷新（不延迟）
            st.rerun()
        else:
            logger.info(f"[UI线程] 对话 {current_conv_id} 正在生成，队列为空，延迟 0.05 秒后刷新")
            # 如果没有待处理更新，延迟刷新（等待新内容）
            # 减少延迟到0.05秒，提高流式显示的流畅度
            time.sleep(0.05)
            st.rerun()
    
    # 清理已完成的线程
    _cleanup_completed_threads()
    
    # 输入框
    _show_input_box(user_id)


def _display_messages():
    """显示消息历史"""
    
    # 获取当前对话
    current_conv_id = st.session_state.current_conversation_id
    if not current_conv_id:
        return
    
    current_conv = st.session_state.active_conversations.get(current_conv_id)
    if not current_conv:
        return
    
    # 显示已保存的消息
    # 如果正在生成，不显示最后一条assistant消息（因为会显示流式内容）
    messages_to_show = current_conv['messages']
    if current_conv['status'] == 'generating' and messages_to_show:
        # 检查最后一条是否是assistant消息
        if messages_to_show[-1].get('role') == 'assistant':
            messages_to_show = messages_to_show[:-1]  # 不显示最后一条assistant消息
    
    for message in messages_to_show:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # 显示检索结果（仅 assistant）
            if message["role"] == "assistant" and message.get("retrieved_docs"):
                _show_retrieved_docs(message["retrieved_docs"])
            
            # 显示思考过程（仅 assistant）
            if message["role"] == "assistant" and message.get("thinking_process"):
                _show_thinking_process(message["thinking_process"])

    # 如果正在生成，显示当前累积的答案（流式显示）
    if current_conv['status'] == 'generating':
        logger.info(f"[UI线程] 显示对话 {current_conv_id} 的生成状态，current_answer长度: {len(current_conv['current_answer'])}")
        with st.chat_message("assistant"):
            if current_conv['current_answer']:
                # 有内容时显示内容（流式显示）
                st.markdown(current_conv['current_answer'])
            else:
                # 没有内容时显示"正在思考"的静态提示（使用 markdown 保持样式一致）
                logger.info(f"[UI线程] 显示'思考中'静态提示，对话 {current_conv_id}")
                st.markdown("*🤔 大模型正在思考中...*")
    
    # 如果出错，显示错误信息
    if current_conv['status'] == 'error':
        with st.chat_message("assistant"):
            st.error(f"生成失败: {current_conv.get('error', '未知错误')}")


def _show_input_box(user_id: int):
    """显示输入框"""
    
    # 使用 chat_input 组件，返回用户输入内容，如果有输入则赋值给 prompt
    if prompt := st.chat_input("输入您的问题..."):
        # 获取当前对话的ID
        current_conv_id = st.session_state.current_conversation_id
        # 如果当前对话ID存在，则获取当前对话对象；否则为 None
        current_conv = st.session_state.active_conversations.get(current_conv_id) if current_conv_id else None
        
        # 情况1：当前对话存在且已完成，继续在本对话中追加消息
        # 情况2：当前没有可复用的对话或者对话正在生成时，创建新对话
        if current_conv and current_conv['status'] == 'completed':
            # 把用户的新问题作为消息加到当前对话的 messages 列表中
            current_conv['messages'].append({'role': 'user', 'content': prompt})
            # 更新对话的主问题
            current_conv['question'] = prompt
            # 状态改为“正在生成”，表示AI要回复新问题
            current_conv['status'] = 'generating'
            # 清空“当前答案”的内容
            current_conv['current_answer'] = ''
            # 清空生成结果
            current_conv['result'] = None
            # 清空错误信息
            current_conv['error'] = None
            # 允许新一轮AI回复保存到数据库
            current_conv['ai_message_saved'] = False
            # 确保user_id存在
            if not current_conv.get('user_id'):
                current_conv['user_id'] = user_id
            
            # 如果已有会话ID，立即把用户的新消息保存进数据库
            session_service = get_session_service()
            if current_conv.get('session_id'):
                session_service.save_message(
                    session_id=current_conv['session_id'],
                    role='user',
                    content=prompt
                )
                logger.info(f"[UI线程] 在现有会话 {current_conv['session_id']} 中保存用户消息")
            
            # 创建新的更新队列
            update_queue = queue.Queue()
            # 创建用于AI生成的后台线程
            thread = threading.Thread(
                target=_background_generation,                # 目标函数：后台流式回复
                args=(current_conv_id,                       # 对话ID
                      current_conv.get('user_id') or user_id, # 优先取历史 user_id，否则取传参
                      prompt,                                # 当前用户输入
                      update_queue),                         # 更新队列
                daemon=True                                  # 设置为守护线程
            )
            # 将新的更新队列和线程对象写回当前对话状态
            current_conv['update_queue'] = update_queue
            current_conv['thread'] = thread
            # 启动后台生成线程
            thread.start()
        else:
            # 没有可复用对话/正在生成，调用创建新对话函数（会自动启动线程）
            _create_conversation(user_id, prompt)
        
        # 立即刷新页面以显示最新内容
        st.rerun()


def _save_to_database(user_id: int, question: str, result: dict, session_service):
    """保存对话到数据库"""
    
    # 创建或使用现有会话
    if not st.session_state.current_session_id:
        # 创建新会话
        session_id = session_service.create_session(user_id, question)
        st.session_state.current_session_id = session_id
    else:
        session_id = st.session_state.current_session_id
    
    # 保存用户消息
    session_service.save_message(
        session_id=session_id,
        role='user',
        content=question
    )
    
    # 保存 AI 回复
    session_service.save_message(
        session_id=session_id,
        role='assistant',
        content=result['answer'],
        retrieved_docs=result.get('retrieved_docs'),
        thinking_process=result.get('thinking_process'),
        tokens_used=result.get('tokens_used', 0)
    )


def _show_retrieved_docs(retrieved_docs):
    """显示检索结果"""
    
    with st.expander("📄 检索到的文档片段", expanded=False):
        for i, doc in enumerate(retrieved_docs, 1):
            similarity = doc.get('similarity', 0)
            content = doc.get('content', '')
            
            # 显示相似度进度条
            st.markdown(f"**[片段 {i}]** 相似度: {similarity:.0%}")
            st.progress(similarity)
            
            # 显示内容（可折叠）
            with st.expander(f"查看内容 ({len(content)} 字符)", expanded=False):
                st.text(content)
            
            if i < len(retrieved_docs):
                st.markdown("---")


def _show_thinking_process(thinking_process):
    """显示思考过程"""
    
    with st.expander("💭 AI 思考过程", expanded=False):
        for step in thinking_process:
            step_num = step.get('step', 0)
            action = step.get('action', '')
            description = step.get('description', '')
            details = step.get('details', '')
            
            st.markdown(f"**步骤 {step_num}: {action}**")
            st.caption(description)
            
            if details:
                st.code(details, language=None)
            
            if step_num < len(thinking_process):
                st.markdown("↓")


def show_new_chat_button():
    """显示新建对话按钮"""
    
    if st.button("➕ 新建对话", use_container_width=True):
        # 只清空当前显示的对话，不停止后台对话
        st.session_state.current_conversation_id = None
        # 兼容旧代码
        if 'current_session_id' in st.session_state:
            st.session_state.current_session_id = None
        if 'chat_messages' in st.session_state:
            st.session_state.chat_messages = []
        st.rerun()


def load_session_messages(session_id: str, session_service):
    """加载历史会话到新的对话管理系统"""
    
    # 初始化对话管理器
    _init_conversation_manager()
    
    # 检查是否已经加载过这个会话
    existing_conv_id = None
    for conv_id, state in st.session_state.active_conversations.items():
        if state.get('session_id') == session_id:
            existing_conv_id = conv_id
            break
    
    if existing_conv_id:
        # 如果已经存在，直接切换到这个对话
        st.session_state.current_conversation_id = existing_conv_id
        # 兼容旧代码
        if 'current_session_id' in st.session_state:
            st.session_state.current_session_id = session_id
        return
    
    # 创建新的对话状态（用于显示历史会话）
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"
    messages = session_service.get_session_messages(session_id)
    
    # 获取会话信息（包括 user_id）
    from database import SessionDAO
    session_dao = SessionDAO()
    session = session_dao.get_session(session_id)
    user_id = session.user_id if session else None
    
    # 转换为chat格式
    chat_messages = []
    for msg in messages:
        chat_messages.append({
            "role": msg['role'],
            "content": msg['content'],
            "retrieved_docs": msg.get('retrieved_docs'),
            "thinking_process": msg.get('thinking_process')
        })
    
    # 创建对话状态（已完成状态，因为这是历史会话）
    state = {
        'conversation_id': conv_id,
        'session_id': session_id,
        'user_id': user_id,  # 从数据库获取 user_id
        'question': chat_messages[0]['content'] if chat_messages and chat_messages[0]['role'] == 'user' else '',
        'messages': chat_messages,
        'status': 'completed',  # 历史会话都是已完成状态
        'current_answer': '',
        'result': None,  # 历史会话不需要 result
        'thread': None,  # 历史会话没有线程
        'update_queue': queue.Queue(),  # 空的队列
        'created_at': time.time(),
        'error': None,
    }
    
    # 保存状态
    st.session_state.active_conversations[conv_id] = state
    st.session_state.current_conversation_id = conv_id
    
    # 兼容旧代码
    if 'current_session_id' in st.session_state:
        st.session_state.current_session_id = session_id
    if 'chat_messages' in st.session_state:
        st.session_state.chat_messages = chat_messages

