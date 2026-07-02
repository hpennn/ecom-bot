"""
对话和消息模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Conversation(Base):
    """对话记录表"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    customer_id = Column(String(100), nullable=False, index=True)  # 平台客户ID
    customer_name = Column(String(100), nullable=True)
    customer_avatar = Column(String(500), nullable=True)
    status = Column(String(20), default="active")  # active/closed/transferred
    ai_first_reply = Column(Integer, default=0)  # AI是否首次回复
    human_takeover = Column(Integer, default=0)  # 是否转人工
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    messages = relationship("Message", backref="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

    def __repr__(self):
        return f"<Conversation(id={self.id}, customer_id={self.customer_id}, status={self.status})>"


class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # customer/bot/human/system
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text/image/goods
    source = Column(String(20), default="pinduoduo")  # pinduoduo/taobao/jd/web
    reference_knowledge_id = Column(Integer, ForeignKey("knowledge_items.id"), nullable=True)  # 引用的知识库ID
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    reference_knowledge = relationship("KnowledgeItem", foreign_keys=[reference_knowledge_id])

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, content={self.content[:30]}...)>"
