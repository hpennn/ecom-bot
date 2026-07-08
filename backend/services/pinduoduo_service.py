"""
拼多多服务 - 增强版
支持关键词回复、转人工、敏感词过滤、消息记录、统计
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import httpx
import hashlib
import time
import json

from config import PINDUODUO_API_URL, PINDUODUO_CLIENT_ID, PINDUODUO_CLIENT_SECRET
from models.store import Store
from models.conversation import Conversation, Message
from models.keyword_reply import ConversationMessage
from services.ai_service import AIService


class PinduoduoService:

    @staticmethod
    def generate_signature(params: Dict[str, Any], secret: str) -> str:
        sorted_params = sorted(params.items())
        param_str = "".join([f"{k}{v}" for k, v in sorted_params if v])
        sign_str = f"{param_str}{secret}"
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    @staticmethod
    async def send_message(store: Store, customer_id: str, content: str, message_type: str = "text") -> bool:
        if not store.platform_token:
            print(f"店铺 {store.id} 未配置平台Token")
            return False
        
        url = f"{PINDUODUO_API_URL}/api/messages/send"
        params = {
            "client_id": PINDUODUO_CLIENT_ID,
            "access_token": store.platform_token,
            "timestamp": int(time.time()),
            "customer_id": customer_id,
            "content": content,
            "message_type": message_type
        }
        params["sign"] = PinduoduoService.generate_signature(params, PINDUODUO_CLIENT_SECRET)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, data=params)
                if response.status_code == 200:
                    return response.json().get("success", False)
                return False
        except Exception as e:
            print(f"发送消息异常: {str(e)}")
            return False

    @staticmethod
    async def process_webhook_message(db: Session, store: Store, message_data: Dict[str, Any]) -> Optional[str]:
        customer_id = message_data.get("customer_id", "")
        customer_name = message_data.get("customer_name", "")
        content = message_data.get("content", "")
        message_type = message_data.get("message_type", "text")
        
        # 查找或创建对话
        conversation = db.query(Conversation).filter(
            Conversation.store_id == store.id,
            Conversation.customer_id == customer_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                store_id=store.id,
                customer_id=customer_id,
                customer_name=customer_name,
                customer_avatar=message_data.get("customer_avatar", ""),
                status="active"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # 保存用户消息到原有Message表
        user_message = Message(
            conversation_id=conversation.id,
            role="customer",
            content=content,
            message_type=message_type,
            source="pinduoduo"
        )
        db.add(user_message)
        
        # 检查自动回复
        if not store.auto_reply_enabled:
            db.commit()
            return None
        
        # 使用增强的AI服务
        reply_result = await AIService.generate_reply(
            db, store.id, content,
            conversation_id=conversation.id,
            customer_id=customer_id
        )
        
        reply_content = reply_result["content"]
        reply_type = reply_result["reply_type"]
        
        # 如果是转人工，更新会话状态
        if reply_type == "transfer":
            conversation.status = "pending_human"
            conversation.human_takeover = 1
        
        # 保存AI回复到原有Message表
        bot_message = Message(
            conversation_id=conversation.id,
            role="bot",
            content=reply_content,
            message_type="text",
            source="pinduoduo"
        )
        db.add(bot_message)
        
        if conversation.ai_first_reply == 0:
            conversation.ai_first_reply = 1
        
        db.commit()
        return reply_content

    @staticmethod
    def verify_webhook(token: str) -> bool:
        return len(token) > 0

    @staticmethod
    def parse_webhook_payload(body: bytes) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    @staticmethod
    async def transfer_to_human(db: Session, conversation_id: int, note: str = "") -> bool:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return False
        conversation.status = "transferred"
        conversation.human_takeover = 1
        db.commit()
        return True
