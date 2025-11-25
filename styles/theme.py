
THEME_CSS = {
    "dark": """
    :root {
        /* 背景色系 - 统一深灰 */
        --bg-primary: #121212;
        --bg-secondary: #1E1E1E;
        --bg-card: #2D2D2D;
        --bg-hover: #383838;
        --bg-input: #252525;
        
        /* 文字色系 - 高对比度 */
        --text-primary: #FFFFFF;
        --text-secondary: #B3B3B3;
        --text-tertiary: #808080;
        --text-disabled: #666666;
        
        /* 强调色 - 更浅更明亮的蓝色 */
        --accent: #64B5F6;
        --accent-hover: #42A5F5;
        --accent-active: #2196F3;
        --success: #4CAF50;
        --warning: #FFA726;
        --error: #EF5350;
        --info: #42A5F5;
        
        /* 边框 */
        --border: #404040;
        --border-light: #505050;
        --border-focus: #64B5F6;
    }
    
    /* ===== 全局样式 ===== */
    body, html {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }
    
    * {
        color: var(--text-secondary) !important;
    }
    
    /* ===== 主容器 ===== */
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-primary) !important;
    }
    
    .main .block-container {
        background-color: var(--bg-primary) !important;
        padding-bottom: 0 !important;
    }
    
    /* 底部区域 - 移除白色背景 */
    [data-testid="stBottom"],
    .stBottom,
    [data-testid="stBottomBlockContainer"],
    section[data-testid="stBottom"] {
        background-color: var(--bg-primary) !important;
    }
    
    /* 统一所有容器的背景为主背景色 */
    .element-container,
    .stChatFloatingInputContainer {
        background-color: var(--bg-primary) !important;
    }
    
    /* ===== 标题文字 ===== */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
    }
    
    /* 减少标题的上下间距 - 紧凑显示 */
    h3 {
        margin-top: 8px !important;
        margin-bottom: 6px !important;
        font-size: 1.1rem !important;
    }
    
    /* 减少容器的上下间距 - 紧凑显示 */
    .element-container {
        margin: 4px 0 !important;
    }
    
    /* 主内容区容器 - 更紧凑 */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* 主内容区内的元素容器 - 减少间距 */
    .main .element-container {
        margin: 2px 0 !important;
        padding: 2px 0 !important;
    }
    
    /* 输入框、选择框等的容器 */
    .stTextInput, .stSelectbox {
        margin-bottom: 6px !important;
    }
    
    /* caption 文字的间距 */
    .main p[data-testid="stCaptionContainer"] {
        margin: 2px 0 !important;
        padding: 2px 0 !important;
    }
    
    /* column 布局的间距 */
    .main div[data-testid="column"] {
        padding: 2px 4px !important;
    }
    
    /* ===== 标题栏 ===== */
    [data-testid="stHeader"] {
        background-color: var(--bg-secondary) !important;
        border-bottom: 1px solid var(--border);
    }
    
    /* 隐藏整个顶部工作区 */
    [data-testid="stToolbar"],
    #MainMenu,
    header[data-testid="stHeader"],
    header[data-testid="stHeader"] *,
    header[data-testid="stHeader"] > div,
    button[kind="header"],
    [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* ===== 侧边栏 ===== */
    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
        padding-top: 4px !important;
    }
    
    /* 侧边栏内的所有容器 - 统一缩小间距 */
    [data-testid="stSidebar"] .element-container,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] div[data-testid="column"] {
        background-color: transparent !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* 侧边栏的所有 block 容器 */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        gap: 2px !important;
    }
    
    /* 侧边栏输入框 */
    [data-testid="stSidebar"] input {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px;
    }
    
    /* 侧边栏标题 h3 */
    [data-testid="stSidebar"] h3 {
        margin-top: 4px !important;
        margin-bottom: 2px !important;
        font-size: 1rem !important;
    }
    
    /* 侧边栏分组标题（如"今天"、"昨天"）*/
    [data-testid="stSidebar"] strong,
    [data-testid="stSidebar"] .stMarkdown strong {
        color: var(--text-tertiary) !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: block;
        margin-top: 3px !important;
        margin-bottom: 2px !important;
    }
    
    /* 侧边栏按钮 - 统一深色背景（使用最高优先级选择器）*/
    [data-testid="stSidebar"] .stButton>button,
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] .stButton button,
    [data-testid="stSidebar"] button[kind="secondary"],
    section[data-testid="stSidebar"] button {
        background-color: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 5px !important;
        transition: all 0.2s ease !important;
        font-weight: 400 !important;
        padding: 5px 10px !important;
        margin: 0 !important;
        font-size: 13px !important;
        line-height: 1.4 !important;
    }
    
    /* 侧边栏分隔线 */
    [data-testid="stSidebar"] hr {
        margin: 3px 0 !important;
        border: none !important;
        border-top: 1px solid var(--border) !important;
        opacity: 0.3 !important;
    }
    
    /* 侧边栏按钮悬停 */
    [data-testid="stSidebar"] .stButton>button:hover,
    [data-testid="stSidebar"] button:hover,
    [data-testid="stSidebar"] .stButton button:hover,
    [data-testid="stSidebar"] button[kind="secondary"]:hover,
    section[data-testid="stSidebar"] button:hover {
        background-color: var(--bg-hover) !important;
        border-color: var(--accent) !important;
        color: var(--text-primary) !important;
    }
    
    /* 侧边栏选中按钮（深蓝色高亮）*/
    [data-testid="stSidebar"] .stButton>button[kind="primary"],
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] .stButton button[kind="primary"],
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #1976D2 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
    }
    
    /* 侧边栏选中按钮悬停 */
    [data-testid="stSidebar"] .stButton>button[kind="primary"]:hover,
    [data-testid="stSidebar"] button[kind="primary"]:hover,
    [data-testid="stSidebar"] .stButton button[kind="primary"]:hover,
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #1565C0 !important;
        color: #FFFFFF !important;
    }
    
    /* ===== 主按钮 ===== */
    .stButton>button {
        background-color: #1976D2 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px;
        font-weight: 600 !important;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    
    .stButton>button:hover {
        background-color: #1565C0 !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(25, 118, 210, 0.3);
    }
    
    /* ===== 表单提交按钮（登录注册）===== */
    button[kind="formSubmit"],
    .stForm button[type="submit"],
    [data-testid="stFormSubmitButton"] > button {
        background-color: #1976D2 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4) !important;
    }
    
    button[kind="formSubmit"]:hover,
    .stForm button[type="submit"]:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #1565C0 !important;
        color: #FFFFFF !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(25, 118, 210, 0.3) !important;
    }
    
    /* ===== 输入框 ===== */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div,
    input[type="text"],
    input[type="password"],
    input[type="email"],
    textarea {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px;
    }
    
    /* 禁用状态的输入框 - 确保文字可见 */
    input:disabled,
    textarea:disabled,
    .stTextInput>div>div>input:disabled,
    .stTextArea>div>div>textarea:disabled,
    input[type="text"]:disabled,
    input[type="password"]:disabled,
    input[type="email"]:disabled,
    .stTextInput input[disabled],
    .stTextInput input:disabled {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        opacity: 1 !important;
        -webkit-text-fill-color: var(--text-primary) !important;
    }
    
    /* Streamlit 输入框内部文字颜色 */
    .stTextInput input,
    .stTextInput input:not(:disabled),
    .stTextInput input:disabled {
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
    }
    
    /* 强制移除所有输入框的所有状态边框 */
    input,
    textarea,
    input:hover,
    textarea:hover,
    input:focus,
    textarea:focus,
    input:active,
    textarea:active,
    input:focus-visible,
    textarea:focus-visible,
    input:invalid,
    textarea:invalid,
    input:valid,
    textarea:valid,
    input:disabled,
    textarea:disabled {
        border-color: var(--border) !important;
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        outline-offset: 0 !important;
        box-shadow: none !important;
    }
    
    input::placeholder,
    textarea::placeholder {
        color: var(--text-disabled) !important;
    }
    
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label {
        color: var(--text-secondary) !important;
    }
    
    /* 处理浏览器自动填充的背景与文字颜色 */
    input:-webkit-autofill,
    input:-webkit-autofill:focus,
    input:-webkit-autofill:hover,
    textarea:-webkit-autofill,
    textarea:-webkit-autofill:focus,
    textarea:-webkit-autofill:hover {
        -webkit-box-shadow: 0 0 0 1000px var(--bg-card) inset !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        caret-color: var(--text-primary) !important;
        transition: background-color 5000s ease-in-out 0s;
    }

    /* 处理浏览器自动填充的背景与文字颜色 */
    input:-webkit-autofill,
    input:-webkit-autofill:focus,
    input:-webkit-autofill:hover,
    textarea:-webkit-autofill,
    textarea:-webkit-autofill:focus,
    textarea:-webkit-autofill:hover {
        -webkit-box-shadow: 0 0 0 1000px var(--bg-card) inset !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        caret-color: var(--text-primary) !important;
        transition: background-color 5000s ease-in-out 0s;
    }
    
    /* ===== 聊天输入框 - 简洁统一设计 ===== */
    /* 容器背景统一 */
    .stChatInput,
    [data-testid="stChatInput"],
    .stChatFloatingInputContainer,
    [data-testid="InputInstructions"] {
        background-color: var(--bg-primary) !important;
        background: var(--bg-primary) !important;
    }
    
    /* 确保输入框容器无padding */
    .stChatInput>div,
    [data-testid="stChatInput"]>div {
        background-color: var(--bg-primary) !important;
        padding: 0 !important;
    }
    
    .stChatInput>div>div,
    [data-testid="stChatInput"]>div>div {
        background-color: var(--bg-primary) !important;
        padding: 0 !important;
    }
    
    /* 输入框本体 - 简洁统一 */
    .stChatInput>div>div>textarea,
    [data-testid="stChatInput"] textarea,
    .stChatInput textarea {
        /* 背景：统一纯色，与主背景协调 */
        background-color: var(--bg-card) !important;
        background-image: none !important;
        
        /* 文字 */
        color: var(--text-primary) !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
        
        /* 光标颜色 - 确保可见 */
        caret-color: var(--text-primary) !important;
        
        /* 边框：柔和的边框 */
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        
        /* 内边距 */
        padding: 12px 16px !important;
        
        /* 无阴影，保持简洁 */
        box-shadow: none !important;
        
        /* 平滑过渡 */
        transition: border-color 0.2s ease, background-color 0.2s ease !important;
    }
    
    /* Placeholder */
    .stChatInput>div>div>textarea::placeholder,
    [data-testid="stChatInput"] textarea::placeholder,
    .stChatInput textarea::placeholder {
        color: var(--text-disabled) !important;
        opacity: 1 !important;
        font-weight: 400 !important;
    }
    
    /* Hover状态 - 轻微变化 */
    .stChatInput>div>div>textarea:hover,
    [data-testid="stChatInput"] textarea:hover,
    .stChatInput textarea:hover {
        border-color: var(--border-light) !important;
        background-color: var(--bg-card) !important;
        outline: none !important;
    }
    
    /* Focus状态 - 柔和反馈 */
    .stChatInput>div>div>textarea:focus,
    [data-testid="stChatInput"] textarea:focus,
    .stChatInput textarea:focus,
    .stChatInput>div>div>textarea:focus-visible,
    [data-testid="stChatInput"] textarea:focus-visible,
    .stChatInput textarea:focus-visible,
    .stChatInput>div>div>textarea:active,
    [data-testid="stChatInput"] textarea:active,
    .stChatInput textarea:active {
        border-color: var(--border-light) !important;
        background-color: var(--bg-card) !important;
        outline: none !important;
        box-shadow: none !important;
        /* 确保焦点时光标可见 */
        caret-color: var(--text-primary) !important;
    }
    
    /* 其他状态 */
    .stChatInput>div>div>textarea:invalid,
    [data-testid="stChatInput"] textarea:invalid,
    .stChatInput textarea:invalid,
    .stChatInput>div>div>textarea:valid,
    [data-testid="stChatInput"] textarea:valid,
    .stChatInput textarea:valid {
        outline: none !important;
    }
    
    /* 发送按钮区域 - 统一背景 */
    .stChatInput button,
    [data-testid="stChatInput"] button {
        background-color: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
    }
    
    .stChatInput button:hover,
    [data-testid="stChatInput"] button:hover {
        background-color: transparent !important;
        color: var(--text-primary) !important;
    }
    
    /* ===== 聊天消息 ===== */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        padding: 8px 0 !important;
    }
    
    [data-testid="stChatMessage"] * {
        color: var(--text-secondary) !important;
    }
    
    /* ===== Radio 按钮 ===== */
    .stRadio label,
    .stRadio > div {
        color: var(--text-secondary) !important;
    }
    
    /* ===== 指标卡片 ===== */
    div[data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-weight: 600;
    }
    
    div[data-testid="stMetricLabel"] {
        color: var(--text-tertiary) !important;
    }
    
    /* Metric 容器 - 统一样式，无边框无背景 */
    div[data-testid="stMetricContainer"],
    [data-testid="stMetric"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 8px 0 !important;
        margin: 0 !important;
    }
    
    /* ===== 辅助文字 ===== */
    .stCaption,
    small {
        color: var(--text-tertiary) !important;
    }
    
    /* ===== 提示框 ===== */
    .stSuccess {
        background-color: var(--bg-card) !important;
        color: var(--success) !important;
        border-left: 4px solid var(--success);
    }
    
    .stInfo {
        background-color: var(--bg-card) !important;
        color: var(--info) !important;
        border-left: 4px solid var(--info);
    }
    
    .stWarning {
        background-color: var(--bg-card) !important;
        color: var(--warning) !important;
        border-left: 4px solid var(--warning);
    }
    
    .stError {
        background-color: var(--bg-card) !important;
        color: var(--error) !important;
        border-left: 4px solid var(--error);
    }
    
    /* ===== Expander 折叠面板 ===== */
    .streamlit-expanderHeader {
        background-color: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border);
        border-radius: 8px;
    }
    
    .streamlit-expanderContent {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border);
        border-top: none;
    }
    
    /* ===== 分隔线 ===== */
    hr {
        border-color: var(--border) !important;
    }
    
    /* ===== 容器 ===== */
    .stContainer,
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    div[data-testid="column"] {
        background-color: transparent !important;
    }
    
    /* ===== Popover 弹窗 ===== */
    [data-testid="stPopover"],
    [data-baseweb="popover"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    }
    
    /* Popover 内的所有元素背景 */
    [data-testid="stPopover"] *,
    [data-baseweb="popover"] * {
        background-color: transparent !important;
    }
    
    /* Popover 内的文字 */
    [data-testid="stPopover"] p,
    [data-testid="stPopover"] span,
    [data-testid="stPopover"] div {
        color: var(--text-secondary) !important;
    }
    
    /* Popover 内的按钮 - 统一深色风格 */
    [data-testid="stPopover"] button,
    [data-baseweb="popover"] button {
        background-color: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
        font-weight: 400 !important;
        padding: 8px 16px !important;
    }
    
    /* Popover 内按钮悬停 */
    [data-testid="stPopover"] button:hover,
    [data-baseweb="popover"] button:hover {
        background-color: var(--bg-hover) !important;
        color: var(--text-primary) !important;
        border-color: var(--accent) !important;
    }
    
    /* Popover 标题 */
    [data-testid="stPopover"] strong {
        color: var(--text-primary) !important;
    }
    
    /* ===== 下拉菜单 ===== */
    [data-baseweb="select"],
    [role="listbox"],
    [data-baseweb="menu"] {
        background-color: var(--bg-card) !important;
    }
    
    [data-baseweb="menu"] li {
        background-color: var(--bg-card) !important;
        color: var(--text-secondary) !important;
    }
    
    [data-baseweb="menu"] li:hover {
        background-color: var(--bg-hover) !important;
    }
    
    /* ===== 文件上传器 ===== */
    [data-testid="stFileUploader"] section {
        background-color: var(--bg-card) !important;
        border: 2px dashed var(--border) !important;
        border-radius: 12px;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: var(--accent) !important;
    }
    
    /* ===== Tab 标签页 ===== */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 1px solid var(--border);
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-tertiary) !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom: 2px solid var(--accent) !important;
    }
    
    /* ===== 进度条 ===== */
    .stProgress > div > div {
        background-color: var(--accent) !important;
    }
    """,
    "light": """
    :root {
        /* 背景色系 - 统一浅灰白 */
        --bg-primary: #F5F5F5;
        --bg-secondary: #FAFAFA;
        --bg-card: #FFFFFF;
        --bg-hover: #EEEEEE;
        --bg-input: #FAFAFA;
        
        /* 文字色系 - 深色清晰 */
        --text-primary: #212121;
        --text-secondary: #616161;
        --text-tertiary: #9E9E9E;
        --text-disabled: #AAAAAA;
        
        /* 强调色 - 更浅更明亮的蓝色 */
        --accent: #42A5F5;
        --accent-hover: #2196F3;
        --accent-active: #1976D2;
        --success: #66BB6A;
        --warning: #FFA726;
        --error: #EF5350;
        --info: #29B6F6;
        
        /* 边框 */
        --border: #E0E0E0;
        --border-light: #D0D0D0;
        --border-focus: #42A5F5;
    }
    
    /* ===== 全局样式 ===== */
    body, html {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }
    
    * {
        color: var(--text-secondary) !important;
    }
    
    /* ===== 主容器 ===== */
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-primary) !important;
    }
    
    .main .block-container {
        background-color: var(--bg-primary) !important;
        padding-bottom: 0 !important;
    }
    
    /* 底部区域 - 移除白色背景 */
    [data-testid="stBottom"],
    .stBottom,
    [data-testid="stBottomBlockContainer"],
    section[data-testid="stBottom"] {
        background-color: var(--bg-primary) !important;
    }
    
    /* 统一所有容器的背景为主背景色 */
    .element-container,
    .stChatFloatingInputContainer {
        background-color: var(--bg-primary) !important;
    }
    
    /* ===== 标题文字 ===== */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
    }
    
    /* 减少标题的上下间距 - 紧凑显示 */
    h3 {
        margin-top: 8px !important;
        margin-bottom: 6px !important;
        font-size: 1.1rem !important;
    }
    
    /* 减少容器的上下间距 - 紧凑显示 */
    .element-container {
        margin: 4px 0 !important;
    }
    
    /* 主内容区容器 - 更紧凑 */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* 主内容区内的元素容器 - 减少间距 */
    .main .element-container {
        margin: 2px 0 !important;
        padding: 2px 0 !important;
    }
    
    /* 输入框、选择框等的容器 */
    .stTextInput, .stSelectbox {
        margin-bottom: 6px !important;
    }
    
    /* caption 文字的间距 */
    .main p[data-testid="stCaptionContainer"] {
        margin: 2px 0 !important;
        padding: 2px 0 !important;
    }
    
    /* column 布局的间距 */
    .main div[data-testid="column"] {
        padding: 2px 4px !important;
    }
    
    /* ===== 标题栏 ===== */
    [data-testid="stHeader"] {
        background-color: var(--bg-secondary) !important;
        border-bottom: 1px solid var(--border);
    }
    
    /* 隐藏整个顶部工作区 */
    [data-testid="stToolbar"],
    #MainMenu,
    header[data-testid="stHeader"],
    header[data-testid="stHeader"] *,
    header[data-testid="stHeader"] > div,
    button[kind="header"],
    [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* ===== 侧边栏 ===== */
    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
        padding-top: 4px !important;
    }
    
    /* 侧边栏内的所有容器 - 统一缩小间距 */
    [data-testid="stSidebar"] .element-container,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] div[data-testid="column"] {
        background-color: transparent !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* 侧边栏的所有 block 容器 */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        gap: 2px !important;
    }
    
    /* 侧边栏输入框 */
    [data-testid="stSidebar"] input {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px;
    }
    
    /* 侧边栏标题 h3 */
    [data-testid="stSidebar"] h3 {
        margin-top: 4px !important;
        margin-bottom: 2px !important;
        font-size: 1rem !important;
    }
    
    /* 侧边栏分组标题（如"今天"、"昨天"）*/
    [data-testid="stSidebar"] strong,
    [data-testid="stSidebar"] .stMarkdown strong {
        color: var(--text-tertiary) !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: block;
        margin-top: 3px !important;
        margin-bottom: 2px !important;
    }
    
    /* 侧边栏按钮 - 统一浅色背景（使用最高优先级选择器）*/
    [data-testid="stSidebar"] .stButton>button,
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] .stButton button,
    [data-testid="stSidebar"] button[kind="secondary"],
    section[data-testid="stSidebar"] button {
        background-color: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
        font-weight: 400 !important;
        padding: 6px 12px !important;
        margin: 0 !important;
        font-size: 14px !important;
    }
    
    /* 侧边栏分隔线 */
    [data-testid="stSidebar"] hr {
        margin: 3px 0 !important;
        border: none !important;
        border-top: 1px solid var(--border) !important;
        opacity: 0.3 !important;
    }
    
    /* 侧边栏按钮悬停 */
    [data-testid="stSidebar"] .stButton>button:hover,
    [data-testid="stSidebar"] button:hover,
    [data-testid="stSidebar"] .stButton button:hover,
    [data-testid="stSidebar"] button[kind="secondary"]:hover,
    section[data-testid="stSidebar"] button:hover {
        background-color: var(--bg-hover) !important;
        border-color: var(--accent) !important;
        color: var(--text-primary) !important;
    }
    
    /* 侧边栏选中按钮（深蓝色高亮）*/
    [data-testid="stSidebar"] .stButton>button[kind="primary"],
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] .stButton button[kind="primary"],
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #1976D2 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
    }
    
    /* 侧边栏选中按钮悬停 */
    [data-testid="stSidebar"] .stButton>button[kind="primary"]:hover,
    [data-testid="stSidebar"] button[kind="primary"]:hover,
    [data-testid="stSidebar"] .stButton button[kind="primary"]:hover,
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #1565C0 !important;
        color: #FFFFFF !important;
    }
    
    /* ===== 主按钮 ===== */
    .stButton>button {
        background-color: #1565C0 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px;
        font-weight: 600 !important;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
    
    .stButton>button:hover {
        background-color: #0D47A1 !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(13, 71, 161, 0.3);
    }
    
    /* ===== 表单提交按钮（登录注册）===== */
    button[kind="formSubmit"],
    .stForm button[type="submit"],
    [data-testid="stFormSubmitButton"] > button {
        background-color: #1565C0 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    }
    
    button[kind="formSubmit"]:hover,
    .stForm button[type="submit"]:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #0D47A1 !important;
        color: #FFFFFF !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(13, 71, 161, 0.3) !important;
    }
    
    /* ===== 输入框 ===== */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div,
    input[type="text"],
    input[type="password"],
    input[type="email"],
    textarea {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px;
    }
    
    /* 禁用状态的输入框 - 确保文字可见 */
    input:disabled,
    textarea:disabled,
    .stTextInput>div>div>input:disabled,
    .stTextArea>div>div>textarea:disabled,
    input[type="text"]:disabled,
    input[type="password"]:disabled,
    input[type="email"]:disabled,
    .stTextInput input[disabled],
    .stTextInput input:disabled {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        opacity: 1 !important;
        -webkit-text-fill-color: var(--text-primary) !important;
    }
    
    /* Streamlit 输入框内部文字颜色 */
    .stTextInput input,
    .stTextInput input:not(:disabled),
    .stTextInput input:disabled {
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
    }
    
    /* 强制移除所有输入框的所有状态边框 */
    input,
    textarea,
    input:hover,
    textarea:hover,
    input:focus,
    textarea:focus,
    input:active,
    textarea:active,
    input:focus-visible,
    textarea:focus-visible,
    input:invalid,
    textarea:invalid,
    input:valid,
    textarea:valid,
    input:disabled,
    textarea:disabled {
        border-color: var(--border) !important;
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        outline-offset: 0 !important;
        box-shadow: none !important;
    }
    
    input::placeholder,
    textarea::placeholder {
        color: var(--text-disabled) !important;
    }
    
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label {
        color: var(--text-secondary) !important;
    }
    
    /* ===== 聊天输入框 - 简洁统一设计 ===== */
    /* 容器背景统一 */
    .stChatInput,
    [data-testid="stChatInput"],
    .stChatFloatingInputContainer,
    [data-testid="InputInstructions"] {
        background-color: var(--bg-primary) !important;
        background: var(--bg-primary) !important;
    }
    
    /* 确保输入框容器无padding */
    .stChatInput>div,
    [data-testid="stChatInput"]>div {
        background-color: var(--bg-primary) !important;
        padding: 0 !important;
    }
    
    .stChatInput>div>div,
    [data-testid="stChatInput"]>div>div {
        background-color: var(--bg-primary) !important;
        padding: 0 !important;
    }
    
    /* 输入框本体 - 简洁统一 */
    .stChatInput>div>div>textarea,
    [data-testid="stChatInput"] textarea,
    .stChatInput textarea {
        /* 背景：统一纯色，与主背景协调 */
        background-color: var(--bg-card) !important;
        background-image: none !important;
        
        /* 文字 */
        color: var(--text-primary) !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
        
        /* 光标颜色 - 确保可见 */
        caret-color: var(--text-primary) !important;
        
        /* 边框：柔和的边框 */
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        
        /* 内边距 */
        padding: 12px 16px !important;
        
        /* 无阴影，保持简洁 */
        box-shadow: none !important;
        
        /* 平滑过渡 */
        transition: border-color 0.2s ease, background-color 0.2s ease !important;
    }
    
    /* Placeholder */
    .stChatInput>div>div>textarea::placeholder,
    [data-testid="stChatInput"] textarea::placeholder,
    .stChatInput textarea::placeholder {
        color: var(--text-disabled) !important;
        opacity: 1 !important;
        font-weight: 400 !important;
    }
    
    /* Hover状态 - 轻微变化 */
    .stChatInput>div>div>textarea:hover,
    [data-testid="stChatInput"] textarea:hover,
    .stChatInput textarea:hover {
        border-color: var(--border-light) !important;
        background-color: var(--bg-card) !important;
        outline: none !important;
    }
    
    /* Focus状态 - 柔和反馈 */
    .stChatInput>div>div>textarea:focus,
    [data-testid="stChatInput"] textarea:focus,
    .stChatInput textarea:focus,
    .stChatInput>div>div>textarea:focus-visible,
    [data-testid="stChatInput"] textarea:focus-visible,
    .stChatInput textarea:focus-visible,
    .stChatInput>div>div>textarea:active,
    [data-testid="stChatInput"] textarea:active,
    .stChatInput textarea:active {
        border-color: var(--border-light) !important;
        background-color: var(--bg-card) !important;
        outline: none !important;
        box-shadow: none !important;
        /* 确保焦点时光标可见 */
        caret-color: var(--text-primary) !important;
    }
    
    /* 其他状态 */
    .stChatInput>div>div>textarea:invalid,
    [data-testid="stChatInput"] textarea:invalid,
    .stChatInput textarea:invalid,
    .stChatInput>div>div>textarea:valid,
    [data-testid="stChatInput"] textarea:valid,
    .stChatInput textarea:valid {
        outline: none !important;
    }
    
    /* 发送按钮区域 - 统一背景 */
    .stChatInput button,
    [data-testid="stChatInput"] button {
        background-color: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
    }
    
    .stChatInput button:hover,
    [data-testid="stChatInput"] button:hover {
        background-color: transparent !important;
        color: var(--text-primary) !important;
    }
    
    /* ===== 聊天消息 ===== */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        padding: 8px 0 !important;
    }
    
    [data-testid="stChatMessage"] * {
        color: var(--text-secondary) !important;
    }
    
    /* ===== Radio 按钮 ===== */
    .stRadio label,
    .stRadio > div {
        color: var(--text-secondary) !important;
    }
    
    /* ===== 指标卡片 ===== */
    div[data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-weight: 600;
    }
    
    div[data-testid="stMetricLabel"] {
        color: var(--text-tertiary) !important;
    }
    
    /* Metric 容器 - 统一样式，无边框无背景 */
    div[data-testid="stMetricContainer"],
    [data-testid="stMetric"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 8px 0 !important;
        margin: 0 !important;
    }
    
    /* ===== 辅助文字 ===== */
    .stCaption,
    small {
        color: var(--text-tertiary) !important;
    }
    
    /* ===== 提示框 ===== */
    .stSuccess {
        background-color: var(--bg-card) !important;
        color: var(--success) !important;
        border-left: 4px solid var(--success);
    }
    
    .stInfo {
        background-color: var(--bg-card) !important;
        color: var(--info) !important;
        border-left: 4px solid var(--info);
    }
    
    .stWarning {
        background-color: var(--bg-card) !important;
        color: var(--warning) !important;
        border-left: 4px solid var(--warning);
    }
    
    .stError {
        background-color: var(--bg-card) !important;
        color: var(--error) !important;
        border-left: 4px solid var(--error);
    }
    
    /* ===== Expander 折叠面板 ===== */
    .streamlit-expanderHeader {
        background-color: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border);
        border-radius: 8px;
    }
    
    .streamlit-expanderContent {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border);
        border-top: none;
    }
    
    /* ===== 分隔线 ===== */
    hr {
        border-color: var(--border) !important;
    }
    
    /* ===== 容器 ===== */
    .stContainer,
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    div[data-testid="column"] {
        background-color: transparent !important;
    }
    
    /* ===== Popover 弹窗 ===== */
    [data-testid="stPopover"],
    [data-baseweb="popover"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }
    
    /* Popover 内的所有元素背景 */
    [data-testid="stPopover"] *,
    [data-baseweb="popover"] * {
        background-color: transparent !important;
    }
    
    /* Popover 内的文字 */
    [data-testid="stPopover"] p,
    [data-testid="stPopover"] span,
    [data-testid="stPopover"] div {
        color: var(--text-secondary) !important;
    }
    
    /* Popover 内的按钮 - 统一浅色风格 */
    [data-testid="stPopover"] button,
    [data-baseweb="popover"] button {
        background-color: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
        font-weight: 400 !important;
        padding: 8px 16px !important;
    }
    
    /* Popover 内按钮悬停 */
    [data-testid="stPopover"] button:hover,
    [data-baseweb="popover"] button:hover {
        background-color: var(--bg-hover) !important;
        color: var(--text-primary) !important;
        border-color: var(--accent) !important;
    }
    
    /* Popover 标题 */
    [data-testid="stPopover"] strong {
        color: var(--text-primary) !important;
    }
    
    /* ===== 下拉菜单 ===== */
    [data-baseweb="select"],
    [role="listbox"],
    [data-baseweb="menu"] {
        background-color: var(--bg-card) !important;
    }
    
    [data-baseweb="menu"] li {
        background-color: var(--bg-card) !important;
        color: var(--text-secondary) !important;
    }
    
    [data-baseweb="menu"] li:hover {
        background-color: var(--bg-hover) !important;
    }
    
    /* ===== 文件上传器 ===== */
    [data-testid="stFileUploader"] section {
        background-color: var(--bg-card) !important;
        border: 2px dashed var(--border) !important;
        border-radius: 12px;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: var(--accent) !important;
    }
    
    /* ===== Tab 标签页 ===== */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 1px solid var(--border);
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-tertiary) !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom: 2px solid var(--accent) !important;
    }
    
    /* ===== 进度条 ===== */
    .stProgress > div > div {
        background-color: var(--accent) !important;
    }
    """
}
