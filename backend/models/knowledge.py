"""
知识库模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class KnowledgeItem(Base):
    """知识库条目表"""
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    category = Column(String(20), default="faq")  # faq/product/policy/custom
    question = Column(String(500), nullable=False, index=True)  # 关键词/问题
    answer = Column(Text, nullable=False)  # 回复内容
    keywords = Column(String(500), nullable=True)  # 额外关键词，逗号分隔
    priority = Column(Integer, default=0)  # 优先级，数字越大优先级越高
    hit_count = Column(Integer, default=0)  # 命中次数
    is_active = Column(Integer, default=1)  # 是否启用
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<KnowledgeItem(id={self.id}, question={self.question[:30]}...)>"

    @property
    def keyword_list(self):
        """获取关键词列表"""
        if self.keywords:
            return [k.strip() for k in self.keywords.split(",") if k.strip()]
        return []
