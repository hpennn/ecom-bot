"""
店铺模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Store(Base):
    """店铺表"""
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    platform = Column(String(20), default="pinduoduo")  # pinduoduo/taobao/jd
    platform_token = Column(String(500), nullable=True)  # 平台授权token
    webhook_url = Column(String(500), nullable=True)  # 回调URL
    auto_reply_enabled = Column(Boolean, default=True)  # 自动回复开关
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    owner = relationship("User", backref="stores")
    knowledge_items = relationship("KnowledgeItem", backref="store", cascade="all, delete-orphan")
    conversations = relationship("Conversation", backref="store", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Store(id={self.id}, name={self.name}, platform={self.platform})>"
