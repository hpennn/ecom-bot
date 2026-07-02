"""
拼多多服务
处理拼多多平台的消息收发
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
from services.ai_service import AIService


class PinduoduoService:
    """拼多多服务类"""

    @staticmethod
    def generate_signature(params: Dict[str, Any], secret: str) -> str:
        """
        生成拼多多API签名
        
        Args:
            params: 请求参数
            secret: 密钥
            
        Returns:
            签名字符串
        """
        # 按字典序排序参数
        sorted_params = sorted(params.items())
        # 拼接成字符串
        param_str = "".join([f"{k}{v}" for k, v in sorted_params if v])
        # 添加密钥
        sign_str = f"{param_str}{secret}"
        # MD5加密
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    @staticmethod
    async def send_message(store: Store, customer_id: str, content: str, message_type: str = "text") -> bool:
        """
        发送消息给客户
        
        Args:
            store: 店铺对象
            customer_id: 客户ID
            content: 消息内容
            message_type: 消息类型
            
        Returns:
            是否发送成功
        """
        if not store.platform_token:
            print(f"店铺 {store.id} 未配置平台Token")
            return False
        
        # 拼多多发送消息API（示例，实际需要根据官方文档调整）
        url = f"{PINDUODUO_API_URL}/api/messages/send"
        
        params = {
            "client_id": PINDUODUO_CLIENT_ID,
            "access_token": store.platform_token,
            "timestamp": int(time.time()),
            "customer_id": customer_id,
            "content": content,
            "message_type": message_type
        }
        
        # 添加签名
        params["sign"] = PinduoduoService.generate_signature(params, PINDUODUO_CLIENT_SECRET)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, data=params)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("success", False)
                else:
                    print(f"发送消息失败: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"发送消息异常: {str(e)}")
            return False

    @staticmethod
    async def process_webhook_message(db: Session, store: Store, message_data: Dict[str, Any]) -> Optional[str]:
        """
        处理来自拼多多的Webhook消息
        
        Args:
            db: 数据库会话
            store: 店铺对象
            message_data: 消息数据
            
        Returns:
            生成的回复内容
        """
        customer_id = message_data.get("customer_id", "")
        customer_name = message_data.get("customer_name", "")
        customer_avatar = message_data.get("customer_avatar", "")
        content = message_data.get("content", "")
        message_type = message_data.get("message_type", "text")
        conversation_id = message_data.get("conversation_id", "")
        
        # 1. 查找或创建对话
        conversation = db.query(Conversation).filter(
            Conversation.store_id == store.id,
            Conversation.customer_id == customer_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                store_id=store.id,
                customer_id=customer_id,
                customer_name=customer_name,
                customer_avatar=customer_avatar,
                status="active"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # 2. 保存用户消息
        user_message = Message(
            conversation_id=conversation.id,
            role="customer",
            content=content,
            message_type=message_type,
            source="pinduoduo"
        )
        db.add(user_message)
        conversation.updated_at = conversation.updated_at  # 更新会话时间
        
        # 3. 检查自动回复是否启用
        if not store.auto_reply_enabled:
            return None
        
        # 4. 获取对话历史
        history_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        conversation_history = "\n".join([
            f"{'用户' if m.role == 'customer' else '客服'}：{m.content}"
            for m in reversed(history_messages[:-1])  # 排除刚添加的这条
        ])
        
        # 5. 生成AI回复
        reply, matched_id, source = await AIService.generate_reply(
            db, store.id, content, conversation_history
        )
        
        # 6. 保存AI回复
        bot_message = Message(
            conversation_id=conversation.id,
            role="bot",
            content=reply,
            message_type="text",
            source="pinduoduo",
            reference_knowledge_id=matched_id
        )
        db.add(bot_message)
        
        # 7. 更新对话统计
        if conversation.ai_first_reply == 0:
            conversation.ai_first_reply = 1
        
        db.commit()
        
        # 8. 发送回复（如果需要）
        # 注意：这里可以选择同步发送或队列发送
        # await PinduoduoService.send_message(store, customer_id, reply)
        
        return reply

    @staticmethod
    def verify_webhook(token: str) -> bool:
        """
        验证Webhook回调URL
        
        Args:
            token: 验证token
            
        Returns:
            是否验证通过
        """
        # 拼多多Webhook验证逻辑（示例）
        # 实际需要根据官方文档实现
        return len(token) > 0

    @staticmethod
    def parse_webhook_payload(body: bytes) -> Optional[Dict[str, Any]]:
        """
        解析Webhook请求体
        
        Args:
            body: 请求体字节
            
        Returns:
            解析后的数据
        """
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    @staticmethod
    async def get_conversation_detail(store: Store, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取对话详情
        
        Args:
            store: 店铺对象
            conversation_id: 拼多多对话ID
            
        Returns:
            对话详情
        """
        if not store.platform_token:
            return None
        
        # 调用拼多多API获取对话详情
        url = f"{PINDUODUO_API_URL}/api/conversations/{conversation_id}"
        
        params = {
            "client_id": PINDUODUO_CLIENT_ID,
            "access_token": store.platform_token,
            "timestamp": int(time.time())
        }
        
        params["sign"] = PinduoduoService.generate_signature(params, PINDUODUO_CLIENT_SECRET)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except Exception:
            return None

    @staticmethod
    async def transfer_to_human(db: Session, conversation_id: int, note: str = "") -> bool:
        """
        将对话转人工客服
        
        Args:
            db: 数据库会话
            conversation_id: 本地对话ID
            note: 备注
            
        Returns:
            是否成功
        """
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return False
        
        conversation.status = "transferred"
        conversation.human_takeover = 1
        db.commit()
        
        # 可以在这里添加通知逻辑，如发送邮件、短信等
        return True
