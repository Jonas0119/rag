"""
认证管理器 - 用户认证和会话管理
"""
import streamlit as st
from typing import Optional, Tuple
import os
import logging
from datetime import datetime, timedelta
import jwt
from streamlit_cookies_controller import CookieController

from database import UserDAO
from utils import hash_password, verify_password, validate_password_strength, validate_username


logger = logging.getLogger(__name__)


class AuthManager:
    """认证管理器"""
    
    def __init__(self, cookie_name: str = "rag_auth_token",
                 cookie_key: Optional[str] = None,
                 cookie_expiry_days: int = 30):
        """
        初始化认证管理器
        
        Args:
            cookie_name: Cookie 名称
            cookie_key: Cookie 加密密钥
            cookie_expiry_days: Cookie 有效期（天）
        """
        self.user_dao = UserDAO()
        self.cookie_name = cookie_name
        self.cookie_key = cookie_key or os.getenv('AUTH_COOKIE_KEY', 'default_secret_key')
        self.cookie_expiry_days = cookie_expiry_days
        
        # 请求级缓存（Request-Level Cache）
        # 仅在本次脚本执行期间有效，防止重复计算
        self._request_user_cache = None
    
    @property
    def cookies_controller(self):
        """获取 Cookie 控制器（用于读取 Cookie）"""
        # 每次访问时重新初始化，确保在页面刷新后能正确读取 Cookie
        return CookieController()
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[str], str]:
        """
        用户登录并生成设置 Cookie 的 JS 脚本
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            (登录是否成功, 设置Cookie的JS脚本, 错误信息)
        """
        # 查询用户
        user = self.user_dao.get_user_by_username(username)
        
        if not user:
            return False, None, "用户名或密码错误"
        
        if not user.is_active:
            return False, None, "账户已被禁用"
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            return False, None, "用户名或密码错误"
        
        # 更新最后登录时间
        self.user_dao.update_last_login(user.user_id)
        
        # 1. 立即写入内存 (L1 Cache)
        self._set_user_to_session(user)
        
        # 2. 生成 Token
        token = self._generate_token(user.user_id, user.username, user.display_name or user.username)
        
        # 3. 生成 JS 脚本（用于写入前端 Cookie - L2 Persistence）
        js_script = self._get_set_cookie_script(token)
        
        return True, js_script, ""
    
    def register(self, username: str, password: str, 
                email: Optional[str] = None,
                display_name: Optional[str] = None) -> Tuple[bool, Optional[str], str]:
        """
        用户注册并自动登录
        
        Returns:
            (注册是否成功, 设置Cookie的JS脚本, 错误信息)
        """
        # 验证用户名
        valid, error_msg = validate_username(username)
        if not valid:
            return False, None, error_msg
        
        # 验证密码强度
        valid, error_msg = validate_password_strength(password)
        if not valid:
            return False, None, error_msg
        
        # 检查用户名是否已存在
        if self.user_dao.username_exists(username):
            return False, None, "用户名已存在"
        
        # 检查邮箱是否已存在
        if email and self.user_dao.email_exists(email):
            return False, None, "邮箱已被使用"
        
        # 加密密码
        password_hash = hash_password(password)
        
        # 创建用户
        try:
            user_id = self.user_dao.create_user(
                username=username,
                password_hash=password_hash,
                email=email,
                display_name=display_name or username
            )
            
            # 创建用户目录
            self._create_user_directories(user_id)
            
            # 自动登录：获取用户信息
            user = self.user_dao.get_user_by_id(user_id)
            
            # 1. 写入内存
            self._set_user_to_session(user)
            
            # 2. 生成 Token
            token = self._generate_token(user.user_id, user.username, user.display_name or user.username)
            
            # 3. 生成 JS
            js_script = self._get_set_cookie_script(token)
            
            return True, js_script, ""
        
        except Exception as e:
            return False, None, f"注册失败: {str(e)}"
    
    def logout(self) -> str:
        """
        用户登出
        
        Returns:
            清除Cookie并刷新页面的JS脚本
        """
        # 1. 清除 Session State (L1 Cache)
        self._clear_session_state()
        
        # 2. 返回清除 Cookie 的 JS (L2 Persistence)
        return self._get_clear_cookie_script()
    
    def get_current_user(self):
        """
        获取当前登录用户对象
        采用三级缓存策略：Request -> Session (L1) -> Cookie (L2)
        """
        # 1. 请求级缓存 (Request Cache)
        # 避免在同一次脚本运行中重复执行逻辑
        if self._request_user_cache:
            return self._request_user_cache
            
        # 2. 内存缓存 (L1 Cache - Session State)
        # 登录后或页面交互期间命中
        if 'current_user' in st.session_state and st.session_state.current_user:
            self._request_user_cache = st.session_state.current_user
            return st.session_state.current_user
            
        # 3. 持久化缓存 (L2 Cache - Cookie)
        # 页面刷新 (F5) 或新开窗口时命中
        payload = self._get_token_payload_from_cookie()
        if payload:
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            if user:
                # 恢复到内存
                self._set_user_to_session(user)
                return user
        
        return None
    
    # ========== 兼容旧接口 (可选，逐步废弃) ==========
    
    def get_current_user_id(self) -> Optional[int]:
        user = self.get_current_user()
        return user.user_id if user else None
    
    def get_current_username(self) -> Optional[str]:
        user = self.get_current_user()
        return user.username if user else None
        
    def get_current_display_name(self) -> Optional[str]:
        user = self.get_current_user()
        return user.display_name if user else None

    # ========== 内部辅助方法 ==========

    def _create_user_directories(self, user_id: int):
        """为新用户创建目录结构"""
        from pathlib import Path
        
        # 创建用户目录
        user_dir = Path(f"data/users/user_{user_id}")
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (user_dir / "uploads").mkdir(exist_ok=True)
        (user_dir / "exports").mkdir(exist_ok=True)
        
        # 创建向量库目录
        chroma_dir = Path(f"data/chroma/user_{user_id}_collection")
        chroma_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_token(self, user_id: int, username: str, display_name: str) -> str:
        """生成 JWT Token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'display_name': display_name,
            'exp': datetime.utcnow() + timedelta(days=self.cookie_expiry_days)
        }
        return jwt.encode(payload, self.cookie_key, algorithm='HS256')
    
    def _decode_token(self, token: str) -> Optional[dict]:
        """解码并验证 JWT Token"""
        try:
            payload = jwt.decode(token, self.cookie_key, algorithms=['HS256'])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    def _get_token_payload_from_cookie(self) -> Optional[dict]:
        """从 Cookie 读取并解析 Token"""
        try:
            token = self.cookies_controller.get(self.cookie_name)
            if not token or (isinstance(token, str) and not token.strip()) or token == "logged_out":
                return None
            
            return self._decode_token(token)
        except Exception as e:
            logger.warning(f"[认证] 读取 Cookie 失败: {e}")
            return None

    def _set_user_to_session(self, user):
        """写入内存 (Session State) 并更新请求缓存"""
        st.session_state.current_user = user
        self._request_user_cache = user

    def _clear_session_state(self):
        """清理所有用户相关的 Session State"""
        keys_to_clear = [
            'current_user',
            '_auth_request_cache', # 旧的缓存键
            'active_conversations',
            'current_conversation_id',
            'current_session_id',
            'chat_messages'
        ]
        
        # 停止后台线程
        if 'active_conversations' in st.session_state:
            for _, state in st.session_state.active_conversations.items():
                thread = state.get('thread')
                if thread and thread.is_alive():
                    pass 
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # 清除当前对象的缓存
        self._request_user_cache = None

    def _get_set_cookie_script(self, token: str) -> str:
        """生成设置 Cookie 的 JS 脚本"""
        # max-age 是秒
        max_age = self.cookie_expiry_days * 24 * 3600
        return f"""
        <script>
            try {{
                document.cookie = "{self.cookie_name}={token}; path=/; max-age={max_age}; SameSite=Lax";
                console.log("Cookie set successfully");
            }} catch (e) {{
                console.error("Failed to set cookie: " + e);
            }}
        </script>
        """

    def _get_clear_cookie_script(self) -> str:
        """生成清除 Cookie 并刷新页面的 JS 脚本"""
        return f"""
        <script>
            try {{
                // 清除 Cookie (设置过期时间为过去)
                document.cookie = "{self.cookie_name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
                document.cookie = "{self.cookie_name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
                
                console.log("Cookie cleared, reloading...");
                
                // 延迟后刷新父页面
                setTimeout(function() {{
                    try {{
                        window.parent.location.reload();
                    }} catch (e) {{
                        window.location.reload();
                    }}
                }}, 100);
            }} catch (e) {{
                console.error("Error during logout: " + e);
            }}
        </script>
        <div style="text-align: center; margin-top: 20px; padding: 20px;">
            <p>正在安全退出...</p>
            <small>如果页面未自动刷新，请<a href="javascript:window.parent.location.reload()" target="_top">点击此处</a></small>
        </div>
        """
