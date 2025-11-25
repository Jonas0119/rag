"""
RAG 智能问答系统 - 主应用
"""
import streamlit as st
import os
import logging
import sys

# 设置环境变量
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 配置日志格式，包含文件名和行号
# 格式：时间戳 | 级别 | 文件名:行号 | 函数名 | 消息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
    force=True  # 强制重新配置，避免重复配置
)

logger = logging.getLogger(__name__)

from auth import AuthManager
from components import (
    show_login_page,
    show_logout_button,
    show_chat_interface,
    show_document_manager,
    show_session_list
)


# ==================== 主题相关 ====================
from styles.theme import THEME_CSS


def apply_theme():
    """根据 session_state 中的主题设置应用样式"""
    theme = st.session_state.get("theme_mode", "dark")
    css = THEME_CSS.get(theme, THEME_CSS["dark"])
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# 页面配置
st.set_page_config(
    page_title="RAG 智能问答系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)





# 在应用启动时预加载 Embedding 模型（异步，不阻塞）
# 使用 st.cache_resource 确保只触发一次（即使页面刷新）
@st.cache_resource
def init_embedding_model():
    try:
        from services import get_vector_store_service
        # 获取服务实例会触发后台模型加载
        _ = get_vector_store_service()
        logger.debug("[脚本初始化] 已触发 Embedding 模型后台加载 (Cached)")
    except Exception as e:
        logger.warning(f"[脚本初始化] 触发 Embedding 模型加载失败: {str(e)}")




def main():
    """主函数"""
    # 初始化主题设置
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "dark"
    apply_theme()
    
    # 检查部署配置（仅在首次运行时检查）
    if "deployment_checked" not in st.session_state:
        from utils.deployment_check import check_cloud_deployment_config
        is_ok, messages = check_cloud_deployment_config()
        if not is_ok:
            errors = [m for m in messages if not ("建议" in m or "STORAGE_MODE" in m or "VECTOR_DB_MODE" in m or "DATABASE_MODE" in m)]
            if errors:
                logger.error(f"[部署检查] 配置错误: {errors}")
                st.error("⚠️ 部署配置检查失败，请检查 Streamlit Cloud Secrets 配置")
                for error in errors:
                    st.error(f"  • {error}")
                st.stop()
        st.session_state.deployment_checked = True
    
    # 初始化认证管理器（每次脚本运行都重新创建，确保请求级缓存被重置）
    auth_manager = AuthManager()
    
    # 在应用启动时预加载 Embedding 模型
    init_embedding_model()
    
    # 获取当前用户（内存优先，Cookie兜底）
    user = auth_manager.get_current_user()
    
    if not user:
        # 未登录，显示登录页面
        logger.info("[主应用] 用户未认证，显示登录页面")
        show_login_page(auth_manager)
        return
    
    # 已登录，显示主应用
    logger.info(f"[主应用] 用户已认证: user_id={user.user_id}, username={user.username}")
    show_main_app(user, auth_manager)


def show_main_app(user, auth_manager):
    """显示主应用界面"""
    
    user_id = user.user_id
    
    # 初始化页面状态
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "💬 智能问答"
    
    # 设置侧边栏切换功能
    _setup_sidebar_toggle()
    
    # 侧边栏
    with st.sidebar:
        # 用户信息和登出
        show_logout_button(auth_manager)
        
        st.markdown("---")
        
        # 导航菜单 - 按钮样式
        st.markdown("### 📑 导航")
        
        # 智能问答按钮
        if st.button(
            "💬 智能问答",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "💬 智能问答" else "secondary"
        ):
            st.session_state.current_page = "💬 智能问答"
            st.rerun()
        
        # 知识库管理按钮
        if st.button(
            "📁 知识库管理",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "📁 知识库管理" else "secondary"
        ):
            st.session_state.current_page = "📁 知识库管理"
            st.rerun()
        
        # 系统设置按钮
        if st.button(
            "⚙️ 系统设置",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "⚙️ 系统设置" else "secondary"
        ):
            st.session_state.current_page = "⚙️ 系统设置"
            st.rerun()
        
        page = st.session_state.current_page
        
        st.markdown("---")
        
        # 根据页面显示会话列表
        if page == "💬 智能问答":
            show_session_list(user_id)
    
    # 主内容区
    if page == "💬 智能问答":
        show_chat_page(user_id)
    elif page == "📁 知识库管理":
        show_document_manager(user_id)
    elif page == "⚙️ 系统设置":
        show_settings_page(user_id)


def _setup_sidebar_toggle():
    """统一的侧边栏切换功能设置"""
    # 使用 HTML 组件创建按钮和脚本
    # 注意：我们需要通过 window.parent 来访问主页面 DOM
    toggle_script = """
    <script>
    (function() {
        // 获取父级文档对象
        const doc = window.parent.document;
        
        // 创建或获取按钮
        function getOrCreateButton() {
            let btn = doc.getElementById('sidebar-toggle-btn');
            
            if (!btn) {
                btn = doc.createElement('button');
                btn.id = 'sidebar-toggle-btn';
                btn.innerHTML = '&#187;'; // ">>" 符号
                
                // 初始样式
                Object.assign(btn.style, {
                    position: 'fixed',
                    top: '20px',
                    left: '20px',
                    zIndex: '999999',
                    width: '42px',
                    height: '42px',
                    borderRadius: '8px', // 圆角矩形
                    backgroundColor: 'var(--bg-card)', // 跟随主题卡片背景
                    color: 'var(--text-secondary)', // 跟随主题次要文字颜色
                    border: '2px solid var(--accent)', // 跟随主题强调色边框
                    fontSize: '24px',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                    transition: 'all 0.2s ease',
                    display: 'none', // 默认隐藏
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: 'inherit',
                    userSelect: 'none',
                    lineHeight: '1',
                    paddingBottom: '4px' // 微调文字垂直居中
                });
                
                // 添加到父级 body
                doc.body.appendChild(btn);
            }
            
            // 移除旧的事件监听器
            btn.onclick = null;
            btn.onmouseover = null;
            btn.onmouseout = null;
            
            // 重新绑定交互效果
            btn.onmouseover = function() {
                this.style.backgroundColor = 'var(--bg-hover)'; // 跟随主题悬停背景
                this.style.color = 'var(--accent)'; // 悬停时文字变亮
                this.style.transform = 'scale(1.05)';
                this.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.2)';
            };
            btn.onmouseout = function() {
                this.style.backgroundColor = 'var(--bg-card)';
                this.style.color = 'var(--text-secondary)';
                this.style.transform = 'scale(1)';
                this.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
            };
            
            // 重新绑定点击事件
            btn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // 点击动画反馈
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = 'scale(1.05)';
                }, 100);
                
                expandSidebar();
            };
            
            return btn;
        }

        // 检测侧边栏是否隐藏
        function isSidebarHidden() {
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            if (!sidebar) return true;
            
            const style = window.parent.getComputedStyle(sidebar);
            const width = sidebar.offsetWidth || parseFloat(style.width);
            const transform = style.transform;
            
            // 检查是否隐藏
            const isCollapsed = sidebar.getAttribute('aria-expanded') === 'false';
            
            return isCollapsed || width <= 0 || (transform && transform.includes('translateX(-'));
        }
        
        // 展开侧边栏 - 终极方案
        function expandSidebar() {
            console.log("[Sidebar Fix] Attempting to toggle sidebar...");
            
            // 步骤 1: 强制获取焦点
            try {
                window.parent.focus();
                if (doc.activeElement) {
                    doc.activeElement.blur(); // 移除当前焦点，避免干扰
                }
            } catch(e) {
                console.warn("[Sidebar Fix] Focus attempt failed:", e);
            }
            
            // 步骤 2: 模拟键盘 'V' 键 (全套事件)
            try {
                const eventProps = {
                    key: 'v',
                    code: 'KeyV',
                    keyCode: 86,
                    which: 86,
                    bubbles: true,
                    cancelable: true,
                    view: window.parent,
                    composed: true
                };
                
                // 依次触发 keydown, keypress, keyup
                doc.body.dispatchEvent(new KeyboardEvent('keydown', eventProps));
                doc.body.dispatchEvent(new KeyboardEvent('keypress', eventProps));
                doc.body.dispatchEvent(new KeyboardEvent('keyup', eventProps));
                
                console.log("[Sidebar Fix] Dispatched 'v' keyboard sequence");
                
                // 稍后检查是否成功
                setTimeout(checkAndRetry, 200);
            } catch (e) {
                console.error("[Sidebar Fix] Keyboard simulation failed:", e);
                fallbackExpand();
            }
        }
        
        // 检查是否成功展开，否则尝试备用方案
        function checkAndRetry() {
            if (isSidebarHidden()) {
                console.log("[Sidebar Fix] Keyboard simulation didn't work, trying brute-force click...");
                fallbackExpand();
            } else {
                console.log("[Sidebar Fix] Sidebar toggled successfully via keyboard");
                updateToggleButton();
            }
        }
        
        // 备用方案：地毯式搜索按钮并点击
        function fallbackExpand() {
            console.log("[Sidebar Fix] Starting brute-force button search...");
            
            const allButtons = doc.querySelectorAll('button');
            let found = false;
            
            for (let btn of allButtons) {
                // 跳过我们自己的按钮
                if (btn.id === 'sidebar-toggle-btn') continue;
                
                // 检查所有可能的属性
                const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                const title = (btn.getAttribute('title') || '').toLowerCase();
                const testId = (btn.getAttribute('data-testid') || '').toLowerCase();
                const text = (btn.innerText || '').toLowerCase();
                
                // 关键词匹配
                if (label.includes('sidebar') || label.includes('menu') || label.includes('collapse') ||
                    title.includes('sidebar') || title.includes('menu') ||
                    testId.includes('sidebar') || testId.includes('header') ||
                    text.includes('sidebar')) {
                    
                    console.log("[Sidebar Fix] Clicking candidate button:", btn);
                    try {
                        btn.click();
                        found = true;
                        // 不立即 return，可能需要点击多个（虽然不太可能）
                        // 但为了保险，找到一个最像的就停
                        if (label.includes('sidebar') || testId.includes('sidebar')) {
                            break;
                        }
                    } catch (e) {
                        console.error("[Sidebar Fix] Click failed:", e);
                    }
                }
            }
            
            if (found) {
                setTimeout(updateToggleButton, 100);
            } else {
                console.warn("[Sidebar Fix] No sidebar button found via brute-force");
                // 最后的最后：强制修改样式（虽然不推荐，但总比没反应好）
                forceStyleUpdate();
            }
        }
        
        function forceStyleUpdate() {
            console.log("[Sidebar Fix] Forcing style update as last resort");
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.setAttribute('aria-expanded', 'true');
                // 移除 transform 和 width 限制
                sidebar.style.transform = 'none';
                sidebar.style.width = '21rem';
                sidebar.style.minWidth = '21rem';
                sidebar.style.visibility = 'visible';
                sidebar.style.display = 'block';
                
                // 调整主内容
                const main = doc.querySelector('[data-testid="stAppViewContainer"]');
                if (main) {
                    main.style.marginLeft = '21rem';
                }
                
                // 触发 resize 事件以通知 Streamlit 重新计算布局
                window.parent.dispatchEvent(new Event('resize'));
                
                setTimeout(updateToggleButton, 100);
            }
        }
        
        // 更新按钮可见性
        function updateToggleButton() {
            const btn = getOrCreateButton();
            const hidden = isSidebarHidden();
            
            // 只有当侧边栏隐藏时才显示按钮
            btn.style.display = hidden ? 'flex' : 'none';
        }
        
        // 初始化
        function init() {
            updateToggleButton();
            
            // 监听父级窗口的变化
            const observer = new MutationObserver(() => {
                updateToggleButton();
            });
            
            observer.observe(doc.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['aria-expande', 'style', 'class']
            });
        }
        
        // 启动
        if (doc.readyState === 'loading') {
            doc.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
        
        // 定时检查作为兜底
        setInterval(updateToggleButton, 500);
        
    })();
    </script>
    """
    st.components.v1.html(toggle_script, height=0)


def show_chat_page(user_id: int):
    """智能问答页面"""
    show_chat_interface(user_id)


def show_settings_page(user_id: int):
    """系统设置页面"""
    st.title("⚙️ 系统设置")
    
    # 显示 Embedding 模型加载状态
    from services import get_vector_store_service
    vector_service = get_vector_store_service()
    status = vector_service.get_embeddings_loading_status()
    
    st.subheader("🤖 模型状态")
    if status['ready']:
        st.success(f"✅ Embedding 模型已就绪: {status['model_name']}")
    elif status['loading']:
        st.info(f"⏳ 正在后台加载 Embedding 模型: {status['model_name']}，请稍候...")
        st.caption("💡 模型加载完成后即可使用向量检索功能")
    else:
        st.warning(f"⚠️ Embedding 模型未加载: {status['model_name']}")
    
    st.markdown("---")

    # 用户信息
    st.subheader("👤 用户信息")
    
    from services import get_cached_user, get_cached_sessions, get_cached_user_stats
    
    # 获取缓存数据
    user_info = get_cached_user(user_id)
    sessions = get_cached_sessions(user_id)
    doc_stats = get_cached_user_stats(user_id)
    
    if user_info:
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("用户名", value=user_info.get('username', ''), disabled=True)
            st.text_input("显示名称", value=user_info.get('display_name', ''), disabled=True)
        
        with col2:
            st.text_input("邮箱", value=user_info.get('email', ''), disabled=True)
            created_at = user_info.get('created_at')
            created_at_str = str(created_at)[:19] if created_at else ""
            st.text_input("注册时间", value=created_at_str, disabled=True)
    else:
        st.warning("未找到用户信息")
    
    st.markdown("---")
    
    # 使用统计
    st.subheader("📊 使用统计")
    
    # 计算统计数据
    # sessions 是按时间分组的字典
    total_sessions = sum(len(v) for v in sessions.values())
    # 遍历所有分组计算消息总数
    total_messages = sum(s.get('message_count', 0) for group in sessions.values() for s in group)
    
    total_documents = doc_stats.get('document_count', 0)
    storage_used = doc_stats.get('storage_used', 0)
    vector_count = doc_stats.get('vector_count', 0)
    
    # 显示统计
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 会话数", total_sessions)
        st.metric("💬 消息数", total_messages)
    
    with col2:
        st.metric("📄 文档数", total_documents)
        from utils.file_handler import format_file_size
        st.metric("💾 存储空间", format_file_size(storage_used))
    
    with col3:
        st.metric("🧩 向量块数", vector_count)
        last_login = user_info.get('last_login')
        if last_login:
            last_login_str = last_login if isinstance(last_login, str) else last_login.strftime('%Y-%m-%d %H:%M:%S')
            st.metric("🕐 最后登录", last_login_str[:19])
    
    st.markdown("---")
    
    # 界面设置
    st.subheader("🎨 界面设置")
    
    current_theme = st.session_state.get("theme_mode", "dark")
    theme_option = st.radio(
        "主题模式，切换后立即生效",
        ["深色模式", "浅色模式"],
        index=0 if current_theme == "dark" else 1,
        horizontal=True
    )
    
    selected_theme = "dark" if theme_option == "深色模式" else "light"
    if selected_theme != current_theme:
        st.session_state.theme_mode = selected_theme
        st.success(f"✅ 已切换至{theme_option}，无需刷新。")
        st.rerun()
    
    # st.caption(f"🎨 当前主题：**{'深色模式' if st.session_state.theme_mode == 'dark' else '浅色模式'}**")
    # st.caption("💡 主题切换会立即生效，并自动保持在当前会话中。")



if __name__ == "__main__":
    main()

