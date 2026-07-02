"""
拼多多Webhook API路由
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from models.store import Store
from models.conversation import Conversation
from database import get_db
from services.pinduoduo_service import PinduoduoService

router = APIRouter(prefix="/api/webhook", tags=["Webhook"])


@router.get("/pinduoduo/verify")
def verify_webhook(
    token: str = "",
    challenge: str = "",
    type: str = ""
):
    """
    验证Webhook回调URL
    
    拼多多平台会调用此接口验证URL有效性
    """
    # 拼多多验证响应
    if challenge:
        return {"challenge": challenge}
    
    return {"status": "ok"}


@router.post("/pinduoduo")
async def receive_pinduoduo_message(
    request: Request,
    x_hook_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    接收拼多多消息Webhook
    
    拼多多会推送客户消息到此处
    """
    # 获取请求体
    body = await request.body()
    
    # 解析消息
    message_data = PinduoduoService.parse_webhook_payload(body)
    if not message_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的消息格式")
    
    # 提取店铺标识（需要根据实际接入方式调整）
    # 方式1：通过URL参数传递
    # 方式2：通过消息内容中的seller_id
    # 方式3：通过Webook签名验证后获取
    
    # 这里使用消息中可能包含的店铺标识
    # 实际接入时请根据拼多多开放平台文档调整
    store_id = message_data.get("seller_id") or message_data.get("mall_id")
    
    if not store_id:
        # 尝试通过Webhook URL中的参数获取
        # 需要在配置Webhook时传入store_id
        return {"error": "无法识别店铺"}
    
    # 查找店铺
    # 注意：这里需要将拼多多的店铺ID与本地店铺关联
    store = db.query(Store).filter(
        Store.platform == "pinduoduo"
    ).first()
    
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺未配置")
    
    # 处理消息并生成回复
    reply = await PinduoduoService.process_webhook_message(db, store, message_data)
    
    if reply:
        # 发送回复给客户
        customer_id = message_data.get("customer_id", "")
        success = await PinduoduoService.send_message(store, customer_id, reply)
        
        return {
            "code": 0,
            "message": "success",
            "data": {
                "reply_sent": success,
                "reply_preview": reply[:100] if len(reply) > 100 else reply
            }
        }
    
    return {"code": 0, "message": "no reply needed"}


@router.get("/pinduoduo/stores")
def list_pinduoduo_stores(
    db: Session = Depends(get_db)
):
    """
    获取已配置的拼多多店铺列表
    
    用于Webhook配置时选择目标店铺
    """
    stores = db.query(Store).filter(Store.platform == "pinduoduo").all()
    
    return [
        {
            "id": store.id,
            "name": store.name,
            "webhook_url": f"https://your-domain.com/api/webhook/pinduoduo?store_id={store.id}"
        }
        for store in stores
    ]


@router.post("/pinduoduo/test")
async def test_pinduoduo_integration(
    store_id: int,
    test_message: str = "你好，请问这款商品有优惠吗？",
    db: Session = Depends(get_db)
):
    """
    测试拼多多集成
    
    模拟发送一条测试消息
    """
    store = db.query(Store).filter(
        Store.id == store_id,
        Store.platform == "pinduoduo"
    ).first()
    
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺不存在")
    
    # 构造测试消息
    test_data = {
        "customer_id": "test_customer_001",
        "customer_name": "测试用户",
        "content": test_message,
        "message_type": "text"
    }
    
    # 处理测试消息
    reply = await PinduoduoService.process_webhook_message(db, store, test_data)
    
    return {
        "store_id": store_id,
        "store_name": store.name,
        "test_message": test_message,
        "ai_reply": reply,
        "auto_reply_enabled": store.auto_reply_enabled
    }
