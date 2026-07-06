"""
电商客服机器人 SaaS 后端
FastAPI应用入口

主要功能：
- 多租户商家系统
- 店铺知识库管理
- AI智能自动回复（豆包API）
- 拼多多平台接入
- 付费管理（虎皮椒支付）
- 管理后台
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import ALLOWED_ORIGINS
from database import init_db, add_missing_columns, engine, SessionLocal
from api import (
    auth_router,
    stores_router,
    knowledge_router,
    conversations_router,
    webhook_router,
    settings_router,
    wechat_pay_router,
    payment_router,
    admin_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化数据库
    """
    # 确保数据目录存在
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)

    # 初始化数据库
    init_db()
    # 迁移：添加新字段
    add_missing_columns()

    print("✅ 数据库初始化完成")
    print("🚀 电商客服机器人服务已启动")

    yield

    print("👋 服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="电商客服机器人 SaaS",
    description="""
## 项目简介
电商客服机器人 SaaS 后端系统，为电商商家提供智能客服解决方案。

## 核心功能
- 🏪 **多租户系统**：商家注册/登录，管理多个店铺
- 📚 **知识库管理**：FAQ、商品信息、话术模板
- 🤖 **智能回复**：基于知识库匹配 + 豆包AI生成
- 📱 **平台接入**：拼多多、淘宝、京东等
- 💰 **付费管理**：虎皮椒支付集成
- 🛡️ **管理后台**：用户/订单/配置管理

## 认证方式
使用 JWT Bearer Token 认证。
登录后获取token，在请求头中添加：
```
Authorization: Bearer <your_token>
```
    """,
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(stores_router)
app.include_router(knowledge_router)
app.include_router(conversations_router)
app.include_router(webhook_router)
app.include_router(settings_router)
app.include_router(payment_router)
app.include_router(admin_router)


@app.get("/", tags=["首页"])
def root():
    """首页"""
    return {
        "name": "电商客服机器人 SaaS",
        "version": "1.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["健康检查"])
def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


@app.get("/api/info", tags=["系统信息"])
def get_api_info():
    """获取API信息"""
    return {
        "version": "1.1.0",
        "features": [
            "商家注册/登录",
            "店铺管理",
            "知识库管理",
            "AI智能回复",
            "拼多多Webhook接入",
            "付费管理",
            "管理后台",
        ],
        "platforms": ["拼多多", "淘宝", "京东"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
