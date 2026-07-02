# 电商机器人部署指南 — 阿里云服务器

## 快速部署（3步）

### 1. SSH 登录服务器
```bash
ssh root@47.113.216.237
```

### 2. 运行一键部署脚本
```bash
cd /www/wwwroot
git clone https://github.com/hpennn/ecom-bot.git
cd ecom-bot
bash deploy/install.sh
```

### 3. 完成！
- 访问: http://47.113.216.237
- API文档: http://47.113.216.237/docs

---

## 如果脚本遇到问题，手动部署：

### 环境准备
```bash
# 安装 Python 3（宝塔面板 → 软件商店 → 搜索 Python 项目管理器 → 安装）
# 或命令行：
apt update && apt install -y python3 python3-pip python3-venv nodejs npm
```

### 后端部署
```bash
cd /www/wwwroot/ecom-bot/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 创建 .env
cat > .env << 'EOF'
SECRET_KEY=ecom-bot-secret-key-2026
ARK_API_KEY=ark-4f063f47-ee3d-45a2-a6db-677cc71cf784-041e9
DOUBAO_ENDPOINT=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL_ID=ep-20260623003404-7lqtt
PINDUODUO_CLIENT_ID=
PINDUODUO_CLIENT_SECRET=
EOF

# 启动
pip install pm2 2>/dev/null; npm install -g pm2
pm2 start "venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2" --name ecom-bot
pm2 save
```

### 前端构建
```bash
cd /www/wwwroot/ecom-bot/frontend
npm install --registry=https://registry.npmmirror.com
npm run build
```

### Nginx 配置
在宝塔面板 → 网站 → 添加站点 → 域名填 `47.113.216.237`

然后在站点配置中添加：
```nginx
# 前端
location / {
    root /www/wwwroot/ecom-bot/frontend/dist;
    index index.html;
    try_files $uri $uri/ /index.html;
}

# API代理
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# Swagger文档
location ~ ^/(docs|redoc|openapi.json) {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
}
```

### 验证
```bash
curl http://127.0.0.1:8000/health
# 应返回: {"status":"healthy"}
```
