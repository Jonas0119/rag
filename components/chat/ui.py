"""
对话界面 UI 渲染
"""
import streamlit as st
import time
import threading
import queue
import logging

from .state import (
    init_conversation_manager,
    process_all_updates,
    cleanup_completed_threads,
    create_conversation,
    background_generation,
    save_conversation_to_db
)
from services import get_session_service

logger = logging.getLogger(__name__)

def show_chat_interface(user_id: int):
    """显示对话界面"""
    
    st.title("💬 智能问答")
    
    # 初始化对话管理器
    init_conversation_manager()
    
    # 先处理所有更新（确保数据最新）
    current_conv_id = st.session_state.current_conversation_id
    current_conv = st.session_state.active_conversations.get(current_conv_id) if current_conv_id else None
    
    # 批量处理所有待处理的更新
    total_chunks = 0
    total_updates = 0
    max_iterations = 100  # 防止无限循环
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        result = process_all_updates()
        
        if result['updated']:
            total_chunks += result['chunk_count']
            total_updates += result['total_count']
        
        # 检查是否还有待处理的更新
        current_conv = st.session_state.active_conversations.get(current_conv_id) if current_conv_id else None
        if not current_conv:
            break
        
        # 如果队列为空，或者状态不是generating，退出循环
        if current_conv['update_queue'].empty() or current_conv['status'] != 'generating':
            break
    
    if total_updates > 0:
        logger.info(f"[UI线程] 本次rerun总共处理 {total_updates} 个更新 (其中 {total_chunks} 个chunk)")
    
    # 再显示消息历史（使用最新数据）
    _display_messages()
    
    # 检查当前对话是否正在生成
    is_generating = current_conv and current_conv['status'] == 'generating'
    
    # 如果正在生成，延迟刷新UI
    if is_generating:
        # 检查队列中是否还有待处理的更新
        has_pending_updates = current_conv and not current_conv['update_queue'].empty()
        if has_pending_updates:
            # 如果有待处理更新，立即刷新（不延迟）
            st.rerun()
        else:
            # 如果没有待处理更新，延迟刷新（等待新内容）
            time.sleep(0.05)
            st.rerun()
    
    # 清理已完成的线程
    cleanup_completed_threads()
    
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
        with st.chat_message("assistant"):
            if current_conv['current_answer']:
                # 有内容时显示内容（流式显示）
                st.markdown(current_conv['current_answer'])
            else:
                # 没有内容时显示"正在思考"的静态提示
                st.markdown("*🤔 大模型正在思考中...*")
    
    # 如果出错，显示错误信息
    if current_conv['status'] == 'error':
        with st.chat_message("assistant"):
            st.error(f"生成失败: {current_conv.get('error', '未知错误')}")


def _show_input_box(user_id: int):
    """显示输入框"""
    
    if prompt := st.chat_input("输入您的问题..."):
        current_conv_id = st.session_state.current_conversation_id
        current_conv = st.session_state.active_conversations.get(current_conv_id) if current_conv_id else None
        
        if current_conv and current_conv['status'] == 'completed':
            # 继续现有对话
            current_conv['messages'].append({'role': 'user', 'content': prompt})
            current_conv['question'] = prompt
            current_conv['status'] = 'generating'
            current_conv['current_answer'] = ''
            current_conv['result'] = None
            current_conv['error'] = None
            current_conv['ai_message_saved'] = False
            if not current_conv.get('user_id'):
                current_conv['user_id'] = user_id
            
            session_service = get_session_service()
            if current_conv.get('session_id'):
                session_service.save_message(
                    session_id=current_conv['session_id'],
                    role='user',
                    content=prompt
                )
            
            update_queue = queue.Queue()
            thread = threading.Thread(
                target=background_generation,
                args=(current_conv_id,
                      current_conv.get('user_id') or user_id,
                      prompt,
                      update_queue),
                daemon=True
            )
            current_conv['update_queue'] = update_queue
            current_conv['thread'] = thread
            thread.start()
        else:
            # 创建新对话
            create_conversation(user_id, prompt)
        
        st.rerun()


def _show_retrieved_docs(retrieved_docs):
    """显示检索结果"""
    
    with st.expander("📄 检索到的文档片段", expanded=False):
        for i, doc in enumerate(retrieved_docs, 1):
            similarity = doc.get('similarity', 0)
            content = doc.get('content', '')
            
            st.markdown(f"**[片段 {i}]** 相似度: {similarity:.0%}")
            st.progress(similarity)
            
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
        st.session_state.current_conversation_id = None
        st.rerun()
