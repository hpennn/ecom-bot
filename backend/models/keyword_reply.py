"""
关键词回复模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from database import Base


class KeywordReply(Base):
    """关键词自动回复"""
    __tablename__ = "keyword_replies"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, index=True)
    keywords = Column(Text, nullable=False)  # JSON array of keywords
    reply = Column(Text, nullable=False)
    match_type = Column(String(20), default="contains")  # contains/exact/regex
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher = matched first
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class TransferKeyword(Base):
    """转人工关键词"""
    __tablename__ = "transfer_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, index=True)
    keywords = Column(Text, nullable=False)  # JSON array
    reply_message = Column(String(500), default="正在为您转接人工客服，请稍候...")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class SensitiveWord(Base):
    """敏感词"""
    __tablename__ = "sensitive_words"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, index=True)
    word = Column(String(100), nullable=False)
    replacement = Column(String(100), default="***")
    is_global = Column(Boolean, default=False)  # 全局生效 vs 店铺级
    created_at = Column(DateTime, server_default=func.now())


class ConversationMessage(Base):
    """会话消息记录"""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, nullable=False, index=True)
    role = Column(String(20), nullable=False)  # customer/bot/system
    content = Column(Text, nullable=False)
    reply_type = Column(String(20))  # keyword/knowledge/ai/transfer/default
    metadata_json = Column(Text)  # extra info like matched keyword
    created_at = Column(DateTime, server_default=func.now())


class DailyStats(Base):
    """每日统计"""
    __tablename__ = "daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, index=True)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    total_messages = Column(Integer, default=0)
    keyword_replies = Column(Integer, default=0)
    knowledge_replies = Column(Integer, default=0)
    ai_replies = Column(Integer, default=0)
    transfer_replies = Column(Integer, default=0)
    default_replies = Column(Integer, default=0)
    unique_customers = Column(Integer, default=0)
