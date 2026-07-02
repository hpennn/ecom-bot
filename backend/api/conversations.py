"""
对话管理API路由
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import ConversationResponse, MessageResponse
from models.store import Store
from models.conversation import Conversation, Message
from api.auth import get_current_user_dependency

router = APIRouter(prefix="/api", tags=["对话管理"])


@router.get("/stores/{store_id}/conversations", response_model=List[ConversationResponse])
def list_conversations(
    store_id: int,
    status: str = Query(None, description="按状态筛选: active/closed/transferred"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    获取店铺对话列表
    
    支持按状态筛选和分页
    """
    # 验证店铺所有权
    store = db.query(Store).filter(
        Store.id == store_id,
        Store.user_id == current_user.id
    ).first()
    
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺不存在")
    
    query = db.query(Conversation).filter(Conversation.store_id == store_id)
    
    if status:
        query = query.filter(Conversation.status == status)
    
    # 分页
    conversations = query.order_by(Conversation.updated_at.desc())\
                         .offset((page - 1) * page_size)\
                         .limit(page_size)\
                         .all()
    
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    获取对话详情
    """
    conversation = db.query(Conversation).join(Store).filter(
        Conversation.id == conversation_id,
        Store.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    
    return ConversationResponse.model_validate(conversation)


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def list_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    获取对话消息列表
    
    按时间倒序返回
    """
    # 验证所有权
    conversation = db.query(Conversation).join(Store).filter(
        Conversation.id == conversation_id,
        Store.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    
    # 分页获取消息
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.desc())\
      .offset((page - 1) * page_size)\
      .limit(page_size)\
      .all()
    
    # 反转顺序，按时间正序返回
    messages.reverse()
    
    return [MessageResponse.model_validate(m) for m in messages]


@router.post("/conversations/{conversation_id}/transfer", response_model=ConversationResponse)
def transfer_to_human(
    conversation_id: int,
    note: str = Query("", description="转人工备注"),
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    将对话转人工客服
    """
    conversation = db.query(Conversation).join(Store).filter(
        Conversation.id == conversation_id,
        Store.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    
    if conversation.status == "transferred":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该对话已经是转人工状态")
    
    conversation.status = "transferred"
    conversation.human_takeover = 1
    db.commit()
    db.refresh(conversation)
    
    return ConversationResponse.model_validate(conversation)


@router.post("/conversations/{conversation_id}/close", response_model=ConversationResponse)
def close_conversation(
    conversation_id: int,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    关闭对话
    """
    conversation = db.query(Conversation).join(Store).filter(
        Conversation.id == conversation_id,
        Store.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    
    conversation.status = "closed"
    db.commit()
    db.refresh(conversation)
    
    return ConversationResponse.model_validate(conversation)


@router.get("/stores/{store_id}/stats")
def get_store_stats(
    store_id: int,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    获取店铺对话统计
    """
    # 验证店铺所有权
    store = db.query(Store).filter(
        Store.id == store_id,
        Store.user_id == current_user.id
    ).first()
    
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺不存在")
    
    # 统计各状态对话数
    from sqlalchemy import func
    
    stats = db.query(
        Conversation.status,
        func.count(Conversation.id)
    ).filter(Conversation.store_id == store_id)\
     .group_by(Conversation.status)\
     .all()
    
    stats_dict = {status: count for status, count in stats}
    
    # 统计总消息数
    total_messages = db.query(func.count(Message.id)).join(Conversation).filter(
        Conversation.store_id == store_id
    ).scalar()
    
    # 统计知识库命中率
    total_knowledge_hits = db.query(func.sum(KnowledgeItem.hit_count)).join(Store).filter(
        KnowledgeItem.store_id == store_id
    ).scalar() or 0
    
    return {
        "conversations": stats_dict,
        "total_conversations": sum(stats_dict.values()),
        "total_messages": total_messages,
        "knowledge_hits": total_knowledge_hits,
        "ai_first_reply_rate": stats_dict.get("active", 0) / max(sum(stats_dict.values()), 1)
    }
