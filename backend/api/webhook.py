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
    """
    if challenge:
        return {"challenge": challenge}
    return {"status": "ok"}


@router.post("/pinduoduo")
async def receive_pinduoduo_message(
    request: Request,
    store_id: Optional[int] = None,
    x_hook_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    接收拼多多消息Webhook
    """
    body = await request.body()
    
    message_data = PinduoduoService.parse_webhook_payload(body)
    if not message_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的消息格式")
    
    # 获取店铺标识
    sid = store_id or message_data.get("seller_id") or message_data.get("mall_id")
    
    if not sid:
        return {"error": "无法识别店铺"}
    
    store = db.query(Store).filter(Store.id == sid, Store.platform == "pinduoduo").first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺未配置")
    
    reply = await PinduoduoService.process_webhook_message(db, store, message_data)
    
    if reply:
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
    
    return {"code": 0, "message": "no reply"}


@router.get("/pinduoduo/stores")
def list_pinduoduo_stores(db: Session = Depends(get_db)):
    """获取已配置的拼多多店铺列表"""
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
    """测试拼多多集成"""
    store = db.query(Store).filter(Store.id == store_id, Store.platform == "pinduoduo").first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺不存在")
    
    test_data = {
        "customer_id": "test_customer_001",
        "customer_name": "测试用户",
        "content": test_message,
        "message_type": "text"
    }
    
    reply = await PinduoduoService.process_webhook_message(db, store, test_data)
    
    return {
        "store_id": store_id,
        "store_name": store.name,
        "test_message": test_message,
        "ai_reply": reply,
        "auto_reply_enabled": store.auto_reply_enabled
    }
