#!/bin/bash
# ============================================================
# 电商客服机器人 SaaS - 一键部署脚本
# 适用于 Ubuntu/CentOS + 宝塔面板
# 用法：bash install.sh
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

APP_DIR="/www/wwwroot/ecom-bot"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

echo "=========================================="
echo "  电商客服机器人 SaaS - 部署脚本"
echo "=========================================="

# 1. 检查 Python
echo ""
echo ">>> 步骤 1/6: 检查 Python 环境"
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log "Python $PY_VER 已安装"
else
    warn "未检测到 Python，正在安装..."
    if command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y python3 python3-pip python3-venv
    elif command -v yum &>/dev/null; then
        yum install -y python3 python3-pip
    else
        err "无法自动安装 Python，请在宝塔面板手动安装 Python 3.10+"
    fi
    log "Python 安装完成"
fi

# 2. 检查 Node.js
echo ""
echo ">>> 步骤 2/6: 检查 Node.js 环境"
if command -v node &>/dev/null; then
    NODE_VER=$(node -v)
    log "Node.js $NODE_VER 已安装"
else
    warn "未检测到 Node.js，正在安装..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - 2>/dev/null || \
    curl -fsSL https://rpm.nodesource.com/setup_18.x | bash - 2>/dev/null
    apt-get install -y nodejs 2>/dev/null || yum install -y nodejs 2>/dev/null
    log "Node.js 安装完成"
fi

# 3. 检查代码目录
echo ""
echo ">>> 步骤 3/6: 准备代码"
if [ ! -d "$APP_DIR" ]; then
    warn "代码目录不存在，正在从 GitHub 克隆..."
    
    # 先克隆到临时目录
    cd /www/wwwroot
    git clone https://github.com/hpennn/ecom-bot.git ecom-bot-tmp
    mv ecom-bot-tmp ecom-bot
    log "代码已克隆到 $APP_DIR"
else
    log "代码目录已存在: $APP_DIR"
    cd "$APP_DIR"
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || warn "git pull 失败，使用现有代码"
fi

# 4. 安装后端依赖
echo ""
echo ">>> 步骤 4/6: 安装后端依赖"
cd "$BACKEND_DIR"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log "Python 虚拟环境已创建"
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
log "后端依赖安装完成"

# 创建 .env 文件
if [ ! -f ".env" ]; then
    cat > .env << 'ENVEOF'
SECRET_KEY=ecom-bot-secret-key-2026-change-me
ARK_API_KEY=ark-4f063f47-ee3d-45a2-a6db-677cc71cf784-041e9
DOUBAO_ENDPOINT=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL_ID=ep-20260623003404-7lqtt
PINDUODUO_CLIENT_ID=
PINDUODUO_CLIENT_SECRET=
ENVEOF
    log "环境变量配置文件已创建"
else
    log ".env 文件已存在，跳过"
fi

# 初始化数据库
python3 -c "
from database import init_db
init_db()
print('数据库初始化完成')
"
log "数据库初始化完成"

# 5. 构建前端
echo ""
echo ">>> 步骤 5/6: 构建前端"
cd "$FRONTEND_DIR"

# 创建 .env.production
cat > .env.production << 'ENVEOF'
VITE_API_BASE_URL=http://47.113.216.237
ENVEOF

npm install --registry=https://registry.npmmirror.com
npm run build
log "前端构建完成 → $FRONTEND_DIR/dist"

# 6. 配置 PM2
echo ""
echo ">>> 步骤 6/6: 配置进程管理"
cd "$BACKEND_DIR"

# 检查 PM2
if ! command -v pm2 &>/dev/null; then
    npm install -g pm2
    log "PM2 安装完成"
fi

# 创建 ecosystem 配置
cat > ecosystem.config.js << 'PM2EOF'
module.exports = {
  apps: [{
    name: 'ecom-bot',
    script: 'venv/bin/uvicorn',
    args: 'main:app --host 127.0.0.1 --port 8000 --workers 2',
    cwd: '/www/wwwroot/ecom-bot/backend',
    interpreter: 'none',
    env: {
      PYTHONPATH: '/www/wwwroot/ecom-bot/backend'
    },
    max_memory_restart: '500M',
    log_date_format: 'YYYY-MM-DD HH:mm:ss'
  }]
};
PM2EOF

# 启动/重启服务
pm2 delete ecom-bot 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save
pm2 startup 2>/dev/null || true
log "后端服务已启动 (PM2)"

# 配置 Nginx
echo ""
echo ">>> 配置 Nginx 反向代理"

NGINX_CONF="/www/server/panel/vhost/nginx/ecom-bot.conf"
if [ -d "/www/server/panel/vhost/nginx" ]; then
    cat > "$NGINX_CONF" << 'NGINXEOF'
server {
    listen 80;
    server_name 47.113.216.237;

    # 前端静态文件
    location / {
        root /www/wwwroot/ecom-bot/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Swagger 文档
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    location /redoc {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
NGINXEOF
    log "Nginx 配置已写入: $NGINX_CONF"
    
    # 测试并重载 Nginx
    /www/server/nginx/sbin/nginx -t 2>/dev/null && \
    /www/server/nginx/sbin/nginx -s reload 2>/dev/null && \
    log "Nginx 已重载" || warn "Nginx 重载失败，请手动在宝塔面板中添加站点"
else
    warn "未找到宝塔 Nginx 配置目录，请手动在宝塔面板创建站点"
    echo ""
    echo "  请在宝塔面板操作："
    echo "  1. 网站 → 添加站点 → 域名填 47.113.216.237"
    echo "  2. 站点设置 → 配置文件，粘贴以下内容："
    echo ""
    cat << 'MANUAL_NGINX'
# 前端
location / {
    root /www/wwwroot/ecom-bot/frontend/dist;
    index index.html;
    try_files $uri $uri/ /index.html;
}

# 后端 API
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
MANUAL_NGINX
fi

echo ""
echo "=========================================="
echo -e "  ${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "  访问地址: http://47.113.216.237"
echo "  API文档:  http://47.113.216.237/docs"
echo ""
echo "  管理命令:"
echo "    pm2 status          # 查看状态"
echo "    pm2 logs ecom-bot   # 查看日志"
echo "    pm2 restart ecom-bot # 重启服务"
echo ""
echo "  代码目录: $APP_DIR"
echo "  更新代码: cd $APP_DIR && git pull && pm2 restart ecom-bot"
echo ""
