"""
Pydantic schemas用于请求验证
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ============ 用户相关 ============
class UserCreate(BaseModel):
    """用户注册请求"""
    username: str
    password: str
    email: EmailStr


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============ 店铺相关 ============
class StoreCreate(BaseModel):
    """创建店铺请求"""
    name: str
    platform: str = "pinduoduo"
    platform_token: Optional[str] = None


class StoreUpdate(BaseModel):
    """更新店铺请求"""
    name: Optional[str] = None
    platform: Optional[str] = None
    platform_token: Optional[str] = None
    webhook_url: Optional[str] = None
    auto_reply_enabled: Optional[bool] = None


class StoreResponse(BaseModel):
    """店铺响应"""
    id: int
    name: str
    platform: str
    auto_reply_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 知识库相关 ============
class KnowledgeCreate(BaseModel):
    """创建知识条目请求"""
    category: str = "faq"
    question: str
    answer: str
    keywords: Optional[str] = None
    priority: int = 0


class KnowledgeUpdate(BaseModel):
    """更新知识条目请求"""
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    keywords: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[int] = None


class KnowledgeResponse(BaseModel):
    """知识条目响应"""
    id: int
    store_id: int
    category: str
    question: str
    answer: str
    keywords: Optional[str] = None
    priority: int
    hit_count: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBatchImport(BaseModel):
    """批量导入请求"""
    items: List[KnowledgeCreate]


# ============ 对话相关 ============
class ConversationResponse(BaseModel):
    """对话响应"""
    id: int
    store_id: int
    customer_id: str
    customer_name: Optional[str] = None
    status: str
    ai_first_reply: int
    human_takeover: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    conversation_id: int
    role: str
    content: str
    message_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ AI回复相关 ============
class ReplyTestRequest(BaseModel):
    """测试自动回复请求"""
    question: str


class ReplyTestResponse(BaseModel):
    """测试自动回复响应"""
    reply: str
    matched_knowledge_id: Optional[int] = None
    matched_question: Optional[str] = None
    source: str  # knowledge/ai


# ============ 拼多多Webhook相关 ============
class PinduoduoMessage(BaseModel):
    """拼多多消息格式"""
    conversation_id: Optional[str] = None
    customer_id: str
    customer_name: Optional[str] = None
    customer_avatar: Optional[str] = None
    message_type: str = "text"
    content: str
    timestamp: Optional[int] = None


class PinduoduoReplyRequest(BaseModel):
    """拼多多回复请求"""
    conversation_id: str
    content: str
    message_type: str = "text"


# ============ 付费相关 ============
class PaymentStatusResponse(BaseModel):
    """付费状态响应"""
    user_id: int
    username: str
    paid: bool
    paid_type: str
    paid_at: Optional[str] = None
    expires_at: Optional[str] = None
    is_admin: bool = False
    free_trial_days: int = 7
    registered_at: Optional[str] = None


class CreatePaymentRequest(BaseModel):
    """创建支付请求"""
    plan: str  # monthly / yearly / permanent


class PaymentCreateResponse(BaseModel):
    """创建支付响应"""
    order_id: str
    amount: float
    plan: str
    pay_url: str = ""
    already_paid: bool = False


# ============ 管理后台相关 ============
class AdminStatsResponse(BaseModel):
    """管理后台统计"""
    total_users: int
    paid_users: int
    free_users: int
    paid_rate: float
    monthly_income: float
    total_income: float
    total_orders: int
    paid_orders: int


class UpdateUserPaidRequest(BaseModel):
    """修改用户付费状态"""
    paid_type: str
    expires_at: Optional[str] = None


class SetAdminRequest(BaseModel):
    """设置管理员"""
    is_admin: bool
