# Streamlit Cloud 部署指南

本文档详细说明如何将 RAG 智能问答系统部署到 Streamlit Cloud。

## 📋 部署前准备

### 1. 云服务配置

确保以下云服务已正确配置：

- ✅ **Supabase Storage**：文件存储服务
- ✅ **Supabase PostgreSQL**：数据库服务
- ✅ **Pinecone**：向量库服务
- ✅ **MiniMax API**：LLM API 服务

### 2. 环境变量准备

所有配置通过 Streamlit Cloud Secrets 管理，参考 `.streamlit/secrets.toml.example`

## 🚀 部署步骤

### 步骤 1: 准备代码

1. 确保所有代码已提交到 Git 仓库
2. 确认 `.gitignore` 排除了敏感文件（`.env`, `.streamlit/secrets.toml`）

### 步骤 2: 在 Streamlit Cloud 创建应用

1. 访问 [Streamlit Cloud](https://share.streamlit.io/)
2. 使用 GitHub 账号登录
3. 点击 "New app"
4. 选择你的仓库和分支
5. 设置主文件为 `app.py`

### 步骤 3: 配置 Secrets

1. 在应用设置中，进入 "Secrets" 页面
2. 参考 `.streamlit/secrets.toml.example` 配置所有环境变量
3. **重要**：确保以下模式全部设置为 `cloud`：
   - `STORAGE_MODE = "cloud"`
   - `VECTOR_DB_MODE = "cloud"`
   - `DATABASE_MODE = "cloud"`

### 步骤 4: 首次部署

1. 点击 "Deploy" 或等待自动部署
2. 查看构建日志，确认没有错误
3. 如果构建失败，检查：
   - `requirements.txt` 是否完整
   - Secrets 配置是否正确
   - 云服务连接是否正常

### 步骤 5: 验证部署

部署成功后，测试以下功能：

- [ ] 用户注册/登录
- [ ] 文件上传（验证 Supabase Storage）
- [ ] 创建会话（验证 PostgreSQL）
- [ ] 向量检索（验证 Pinecone）
- [ ] 智能问答功能

## ⚙️ 必需的环境变量

### 基础配置（必须）

```toml
ANTHROPIC_API_KEY = "sk-xxx"
ANTHROPIC_BASE_URL = "https://api.minimaxi.com/anthropic"
```

### 模式配置（必须全部为 cloud）

```toml
STORAGE_MODE = "cloud"
VECTOR_DB_MODE = "cloud"
DATABASE_MODE = "cloud"
```

### Supabase 配置（STORAGE_MODE=cloud 时必需）

```toml
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "your_publishable_key"
SUPABASE_SERVICE_KEY = "your_service_key"
SUPABASE_STORAGE_BUCKET = "rag"
```

### PostgreSQL 配置（DATABASE_MODE=cloud 时必需）

```toml
DATABASE_URL = "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"
```

### Pinecone 配置（VECTOR_DB_MODE=cloud 时必需）

```toml
PINECONE_API_KEY = "xxx-xxx-xxx"
PINECONE_ENVIRONMENT = "us-east-1"
PINECONE_INDEX_NAME = "rag-system"
```

### 认证配置（必须）

```toml
AUTH_COOKIE_NAME = "rag_auth_token"
AUTH_COOKIE_KEY = "your_random_secret_key"  # 使用: python -c "import secrets; print(secrets.token_urlsafe(32))"
AUTH_COOKIE_EXPIRY_DAYS = "30"
MIN_PASSWORD_LENGTH = "6"
```

## 🔍 故障排查

### 问题 1: 构建失败

**可能原因：**
- `requirements.txt` 不完整
- 依赖版本冲突

**解决方法：**
- 检查构建日志
- 更新 `requirements.txt`

### 问题 2: 应用启动失败

**可能原因：**
- Secrets 配置不完整
- 云服务连接失败

**解决方法：**
- 检查应用日志
- 验证所有 Secrets 已正确配置
- 测试云服务连接

### 问题 3: 文件上传失败

**可能原因：**
- Supabase Storage 未配置
- Bucket 不存在

**解决方法：**
- 检查 `SUPABASE_STORAGE_BUCKET` 配置
- 在 Supabase Dashboard 中创建 Bucket

### 问题 4: 数据库连接失败

**可能原因：**
- `DATABASE_URL` 格式错误
- 数据库未初始化

**解决方法：**
- 检查连接字符串格式
- 运行数据库初始化脚本

### 问题 5: 向量检索失败

**可能原因：**
- Pinecone Index 不存在
- API Key 无效

**解决方法：**
- 检查 `PINECONE_INDEX_NAME` 配置
- 在 Pinecone Dashboard 中创建 Index（维度 1024）

## 📝 注意事项

1. **不要使用本地模式**：Streamlit Cloud 文件系统是临时的，必须使用云服务
2. **保护 Secrets**：不要将包含真实密钥的文件提交到 Git
3. **监控资源**：注意云服务的配额限制
4. **定期备份**：虽然使用云服务，但建议定期备份重要数据

## 🔗 相关文档

- [Streamlit Cloud 文档](https://docs.streamlit.io/streamlit-cloud)
- [Supabase 文档](https://supabase.com/docs)
- [Pinecone 文档](https://docs.pinecone.io/)

