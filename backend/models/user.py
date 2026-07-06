"""
用户/商家模型
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base


class User(Base):
    """商家用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 付费相关
    paid_type = Column(String(20), default="free")  # free / monthly / yearly / permanent
    paid_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # 管理员
    is_admin = Column(Boolean, default=False)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

    @property
    def is_paid(self) -> bool:
        """检查用户是否在有效期内"""
        if self.paid_type == "permanent":
            return True
        if self.paid_type in ("monthly", "yearly") and self.expires_at:
            return self.expires_at > datetime.utcnow()
        # free 用户：注册 7 天内免费
        if self.paid_type == "free" and self.created_at:
            return (self.created_at + timedelta(days=7)) > datetime.utcnow()
        return False

    @property
    def trial_expires_at(self) -> datetime:
        """试用到期时间"""
        if self.created_at:
            return self.created_at + timedelta(days=7)
        return datetime.utcnow()
