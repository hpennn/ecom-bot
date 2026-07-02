# 电商客服机器人 SaaS 后端

基于 FastAPI + SQLAlchemy + SQLite 构建的电商客服机器人 SaaS 后端系统。

## 功能特性

- 🏪 **多租户系统**：商家注册/登录，每个商家可管理多个店铺
- 📚 **知识库管理**：每个店铺独立知识库，支持 FAQ、商品信息、话术模板
- 🤖 **智能自动回复**：基于知识库匹配 + 豆包AI生成回复
- 📱 **平台接入**：预留拼多多 Webhook 接口，支持扩展淘宝、京东

## 技术栈

- **框架**：FastAPI
- **ORM**：SQLAlchemy
- **数据库**：SQLite
- **AI**：豆包 API (Volcengine)
- **认证**：JWT + bcrypt

## 项目结构

```
ecom-bot/
├── backend/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置文件
│   ├── database.py          # 数据库连接
│   ├── schemas.py           # Pydantic 模型
│   ├── models/              # SQLAlchemy 模型
│   │   ├── user.py          # 用户模型
│   │   ├── store.py         # 店铺模型
│   │   ├── knowledge.py     # 知识库模型
│   │   └── conversation.py  # 对话/消息模型
│   ├── api/                 # API 路由
│   │   ├── auth.py          # 认证接口
│   │   ├── stores.py        # 店铺管理接口
│   │   ├── knowledge.py     # 知识库接口
│   │   ├── conversations.py  # 对话管理接口
│   │   └── webhook.py       # 拼多多 Webhook
│   ├── services/            # 业务逻辑
│   │   ├── auth_service.py  # 认证服务
│   │   ├── ai_service.py    # AI 回复服务
│   │   └── pinduoduo_service.py  # 拼多多服务
│   └── data/                # SQLite 数据库目录
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 豆包 API 配置
export ARK_API_KEY="your-ark-api-key"
export DOUBAO_ENDPOINT="https://ark.cn-beijing.volces.com/api/v3"
export DOUBAO_MODEL_ID="your-model-id"

# JWT 密钥（生产环境务必修改）
export SECRET_KEY="your-secret-key-change-in-production"

# 拼多多 API 配置（可选）
export PINDUODUO_CLIENT_ID="your-client-id"
export PINDUODUO_CLIENT_SECRET="your-client-secret"
```

### 3. 启动服务

```bash
cd backend
python main.py
# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 文档

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 商家注册 |
| POST | `/api/auth/login` | 登录（返回 JWT） |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 店铺管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stores` | 获取店铺列表 |
| POST | `/api/stores` | 创建店铺 |
| PUT | `/api/stores/{id}` | 更新店铺 |
| DELETE | `/api/stores/{id}` | 删除店铺 |

### 知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stores/{id}/knowledge` | 获取知识库列表 |
| POST | `/api/stores/{id}/knowledge` | 添加知识条目 |
| PUT | `/api/knowledge/{id}` | 更新知识条目 |
| DELETE | `/api/knowledge/{id}` | 删除知识条目 |
| POST | `/api/stores/{id}/knowledge/batch` | 批量导入 |
| POST | `/api/stores/{id}/reply` | 测试自动回复 |

### 对话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stores/{id}/conversations` | 获取对话列表 |
| GET | `/api/conversations/{id}` | 获取对话详情 |
| GET | `/api/conversations/{id}/messages` | 获取消息记录 |
| POST | `/api/conversations/{id}/transfer` | 转人工 |
| POST | `/api/conversations/{id}/close` | 关闭对话 |
| GET | `/api/stores/{id}/stats` | 获取统计 |

### 拼多多 Webhook

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/webhook/pinduoduo/verify` | 验证回调 URL |
| POST | `/api/webhook/pinduoduo` | 接收消息 |
| GET | `/api/webhook/pinduoduo/stores` | 获取已配置店铺 |
| POST | `/api/webhook/pinduoduo/test` | 测试集成 |

## 使用示例

### 1. 注册商家

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "merchant001",
    "password": "password123",
    "email": "merchant@example.com"
  }'
```

### 2. 登录获取 Token

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -d "username=merchant001&password=password123"
```

### 3. 创建店铺

```bash
curl -X POST "http://localhost:8000/api/stores" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的拼多多店铺",
    "platform": "pinduoduo"
  }'
```

### 4. 添加知识库条目

```bash
curl -X POST "http://localhost:8000/api/stores/1/knowledge" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "faq",
    "question": "发货时间",
    "answer": "我们会在付款后24小时内发货，默认使用圆通快递，预计3-5天送达。",
    "keywords": "发货,快递,物流,几天到",
    "priority": 10
  }'
```

### 5. 测试自动回复

```bash
curl -X POST "http://localhost:8000/api/stores/1/reply" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "几天能发货？"}'
```

## 拼多多接入配置

### 1. 配置 Webhook URL

在拼多多商家后台配置回调 URL：
```
https://your-domain.com/api/webhook/pinduoduo?store_id=1
```

### 2. 验证回调 URL

访问验证接口：
```
GET https://your-domain.com/api/webhook/pinduoduo/verify
```

### 3. 消息接收

拼多多会 POST 消息到配置的 URL，系统自动：
1. 解析消息内容
2. 匹配知识库
3. 调用 AI 生成回复
4. 发送回复给客户
5. 记录对话日志

## 部署建议

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 生产环境注意事项

1. **修改 SECRET_KEY**：务必设置强密码
2. **使用 PostgreSQL/MySQL**：替换 SQLite
3. **配置 HTTPS**：使用 SSL 证书
4. **添加限流**：防止 API 滥用
5. **日志管理**：配置日志输出
6. **健康检查**：配置负载均衡健康检查

## 许可证

MIT License
