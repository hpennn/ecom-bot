"""
API路由模块
"""

from api.auth import router as auth_router
from api.stores import router as stores_router
from api.knowledge import router as knowledge_router
from api.conversations import router as conversations_router
from api.webhook import router as webhook_router
from api.settings import router as settings_router
from api.wechat_pay import router as wechat_pay_router
from api.payment import router as payment_router
from api.admin import router as admin_router

__all__ = [
    "auth_router",
    "stores_router",
    "knowledge_router",
    "conversations_router",
    "webhook_router",
    "settings_router",
    "wechat_pay_router",
    "payment_router",
    "admin_router",
]
