"""
登录注册组件
"""
import streamlit as st
import time
from auth import AuthManager


def show_login_page(auth_manager: AuthManager):
    """显示登录页面"""
    
    st.markdown("""
        <div style="text-align: center; padding: 50px 0 30px 0;">
            <h1>📚 RAG 智能问答系统</h1>
            <p style="font-size: 18px; opacity: 0.7;">基于 LangChain + MiniMax 的智能文档问答</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 创建标签页
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    with tab1:
        _show_login_form(auth_manager)
    
    with tab2:
        _show_register_form(auth_manager)


def _show_login_form(auth_manager: AuthManager):
    """显示登录表单"""
    st.subheader("👤 用户登录")
    
    with st.form("login_form"):
        username = st.text_input("用户名", key="login_username")
        password = st.text_input("密码", type="password", key="login_password")
        
        submitted = st.form_submit_button("登录", use_container_width=True)
        
        if submitted:
            if not username or not password:
                st.error("请输入用户名和密码")
                return
            
            # 尝试登录（内存已写入）
            success, js_script, error_msg = auth_manager.login(username, password)
            
            if success:
                # 1. 注入 JS 设置 Cookie（异步，在后台执行）
                if js_script:
                    st.components.v1.html(js_script, height=0)
                
                st.success("登录成功！正在跳转...")
                
                # 2. 立即刷新（不需要等待，因为内存已有用户信息）
                time.sleep(0.3)  # 短暂延迟，让成功消息显示
                st.rerun()
            else:
                st.error(f"❌ {error_msg}")


def _show_register_form(auth_manager: AuthManager):
    """显示注册表单"""
    st.subheader("✨ 注册新账号")
    
    with st.form("register_form"):
        username = st.text_input(
            "用户名",
            key="register_username",
            help="至少3个字符，只能包含字母、数字和下划线"
        )
        password = st.text_input(
            "密码",
            type="password",
            key="register_password",
            help="至少6个字符"
        )
        password_confirm = st.text_input(
            "确认密码",
            type="password",
            key="register_password_confirm"
        )
        email = st.text_input(
            "邮箱（可选）",
            key="register_email"
        )
        display_name = st.text_input(
            "显示名称（可选）",
            key="register_display_name",
            help="用于在界面上显示，默认使用用户名"
        )
        
        agree_terms = st.checkbox("我已阅读并同意使用条款")
        
        submitted = st.form_submit_button("注册", use_container_width=True)
        
        if submitted:
            # 验证输入
            if not username or not password:
                st.error("请输入用户名和密码")
                return
            
            if password != password_confirm:
                st.error("两次密码输入不一致")
                return
            
            if not agree_terms:
                st.error("请先同意使用条款")
                return
            
            # 尝试注册（内存已写入）
            success, js_script, error_msg = auth_manager.register(
                username=username,
                password=password,
                email=email if email else None,
                display_name=display_name if display_name else None
            )
            
            if success:
                # 1. 注入 JS 设置 Cookie（异步，在后台执行）
                if js_script:
                    st.components.v1.html(js_script, height=0)
                
                st.success("✅ 注册成功！自动登录中...")
                
                # 2. 立即刷新（不需要等待，因为内存已有用户信息）
                time.sleep(0.3)
                st.rerun()
            else:
                st.error(f"❌ {error_msg}")


def show_logout_button(auth_manager: AuthManager):
    """显示用户信息和登出按钮（在侧边栏）"""
    user = auth_manager.get_current_user()
    if not user:
        return

    username = user.username
    display_name = user.display_name or username
    
    # 用户信息卡片样式 - 紧凑版
    st.sidebar.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(74, 158, 255, 0.1), rgba(139, 127, 249, 0.05));
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
        ">
            <div style="
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                <div style="
                    width: 36px;
                    height: 36px;
                    background: linear-gradient(135deg, #4A9EFF, #8B7FF9);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                    flex-shrink: 0;
                ">
                    👤
                </div>
                <div style="
                    flex: 1;
                    min-width: 0;
                ">
                    <div style="
                        font-size: 14px;
                        font-weight: 600;
                        color: var(--text-primary);
                        margin-bottom: 2px;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    ">
                        {display_name}
                    </div>
                    <div style="
                        font-size: 11px;
                        color: var(--text-tertiary);
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    ">
                        @{username}
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # 登出按钮
    if st.sidebar.button("🚪 登出", use_container_width=True, type="secondary"):
        # 1. 调用登出逻辑（清除内存，获取清除 Cookie 的 JS）
        js_script = auth_manager.logout()
        
        st.sidebar.success("正在安全登出...")
        
        # 2. 执行 JS：清除 Cookie + 刷新页面（由 JS 完成刷新，确保 Cookie 先删除）
        # 注意：这里不要调用 st.rerun()，让 JS 控制刷新时机
        st.components.v1.html(js_script, height=100)
