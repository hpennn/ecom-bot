"""
知识库管理API路由
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse,
    KnowledgeBatchImport, ReplyTestRequest, ReplyTestResponse
)
from models.store import Store
from models.knowledge import KnowledgeItem
from api.auth import get_current_user_dependency
from services.ai_service import AIService

router = APIRouter(prefix="/api", tags=["知识库"])


def verify_store_ownership(store_id: int, user_id: int, db: Session) -> Store:
    """
    验证店铺所有权
    
    Args:
        store_id: 店铺ID
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        店铺对象
        
    Raises:
        HTTPException: 店铺不存在或无权限
    """
    store = db.query(Store).filter(
        Store.id == store_id,
        Store.user_id == user_id
    ).first()
    
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺不存在")
    
    return store


@router.get("/stores/{store_id}/knowledge", response_model=List[KnowledgeResponse])
def list_knowledge(
    store_id: int,
    category: str = Query(None, description="按分类筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    获取店铺知识库列表
    
    支持分页和分类筛选
    """
    # 验证店铺所有权
    verify_store_ownership(store_id, current_user.id, db)
    
    query = db.query(KnowledgeItem).filter(KnowledgeItem.store_id == store_id)
    
    if category:
        query = query.filter(KnowledgeItem.category == category)
    
    # 分页
    total = query.count()
    items = query.order_by(KnowledgeItem.priority.desc(), KnowledgeItem.created_at.desc())\
                 .offset((page - 1) * page_size)\
                 .limit(page_size)\
                 .all()
    
    return [KnowledgeResponse.model_validate(item) for item in items]


@router.post("/stores/{store_id}/knowledge", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge(
    store_id: int,
    knowledge_data: KnowledgeCreate,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    添加知识库条目
    """
    # 验证店铺所有权
    verify_store_ownership(store_id, current_user.id, db)
    
    item = KnowledgeItem(
        store_id=store_id,
        category=knowledge_data.category,
        question=knowledge_data.question,
        answer=knowledge_data.answer,
        keywords=knowledge_data.keywords,
        priority=knowledge_data.priority
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return KnowledgeResponse.model_validate(item)


@router.get("/knowledge/{item_id}", response_model=KnowledgeResponse)
def get_knowledge(
    item_id: int,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    获取知识库条目详情
    """
    item = db.query(KnowledgeItem).join(Store).filter(
        KnowledgeItem.id == item_id,
        Store.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识条目不存在")
    
    return KnowledgeResponse.model_validate(item)


@router.put("/knowledge/{item_id}", response_model=KnowledgeResponse)
def update_knowledge(
    item_id: int,
    knowledge_data: KnowledgeUpdate,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    更新知识库条目
    """
    item = db.query(KnowledgeItem).join(Store).filter(
        KnowledgeItem.id == item_id,
        Store.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识条目不存在")
    
    # 更新字段
    update_data = knowledge_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.commit()
    db.refresh(item)
    
    return KnowledgeResponse.model_validate(item)


@router.delete("/knowledge/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge(
    item_id: int,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    删除知识库条目
    """
    item = db.query(KnowledgeItem).join(Store).filter(
        KnowledgeItem.id == item_id,
        Store.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识条目不存在")
    
    db.delete(item)
    db.commit()
    
    return None


@router.post("/stores/{store_id}/knowledge/batch", response_model=List[KnowledgeResponse])
def batch_import_knowledge(
    store_id: int,
    import_data: KnowledgeBatchImport,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    批量导入知识库条目
    
    最多一次导入100条
    """
    # 验证店铺所有权
    store = verify_store_ownership(store_id, current_user.id, db)
    
    if len(import_data.items) > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="单次最多导入100条")
    
    created_items = []
    for item_data in import_data.items:
        item = KnowledgeItem(
            store_id=store_id,
            category=item_data.category,
            question=item_data.question,
            answer=item_data.answer,
            keywords=item_data.keywords,
            priority=item_data.priority
        )
        db.add(item)
        created_items.append(item)
    
    db.commit()
    
    return [KnowledgeResponse.model_validate(item) for item in created_items]


@router.post("/stores/{store_id}/reply", response_model=ReplyTestResponse)
async def test_auto_reply(
    store_id: int,
    request: ReplyTestRequest,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    测试自动回复
    
    输入一个问题，返回AI生成的回复
    """
    # 验证店铺所有权
    verify_store_ownership(store_id, current_user.id, db)
    
    # 生成回复
    reply, matched_id, source = await AIService.generate_reply(db, store_id, request.question)
    
    # 获取匹配的问题
    matched_question = None
    if matched_id:
        item = db.query(KnowledgeItem).filter(KnowledgeItem.id == matched_id).first()
        if item:
            matched_question = item.question
    
    return ReplyTestResponse(
        reply=reply,
        matched_knowledge_id=matched_id,
        matched_question=matched_question,
        source=source
    )
