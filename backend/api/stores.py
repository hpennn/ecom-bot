"""
店铺管理API路由
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas import StoreCreate, StoreUpdate, StoreResponse
from models.store import Store
from api.auth import get_current_user_dependency

router = APIRouter(prefix="/api/stores", tags=["店铺管理"])


@router.get("", response_model=List[StoreResponse])
def list_stores(
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的店铺列表
    
    需要登录
    """
    stores = db.query(Store).filter(Store.user_id == current_user.id).all()
    return [StoreResponse.model_validate(s) for s in stores]


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
def create_store(
    store_data: StoreCreate,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    创建新店铺
    
    - name: 店铺名称
    - platform: 平台（pinduoduo/taobao/jd）
    - platform_token: 平台授权token（可选）
    """
    store = Store(
        user_id=current_user.id,
        name=store_data.name,
        platform=store_data.platform,
        platform_token=store_data.platform_token
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    
    return StoreResponse.model_validate(store)


@router.get("/{store_id}", response_model=StoreResponse)
def get_store(
    store_id: int,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    获取指定店铺详情
    """
    store = db.query(Store).filter(
        Store.id == store_id,
        Store.user_id == current_user.id
    ).first()
    
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺不存在")
    
    return StoreResponse.model_validate(store)


@router.put("/{store_id}", response_model=StoreResponse)
def update_store(
    store_id: int,
    store_data: StoreUpdate,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    更新店铺信息
    """
    store = db.query(Store).filter(
        Store.id == store_id,
        Store.user_id == current_user.id
    ).first()
    
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺不存在")
    
    # 更新字段
    update_data = store_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(store, field, value)
    
    db.commit()
    db.refresh(store)
    
    return StoreResponse.model_validate(store)


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_store(
    store_id: int,
    current_user = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    删除店铺
    """
    store = db.query(Store).filter(
        Store.id == store_id,
        Store.user_id == current_user.id
    ).first()
    
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺不存在")
    
    db.delete(store)
    db.commit()
    
    return None
