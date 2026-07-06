"""
管理后台 API
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.order import Order
from config import ADMIN_TOKEN, PLAN_PRICES

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


def verify_admin(request: Request, current_user: User = None):
    """
    验证管理员权限
    支持两种方式：
    1. x-admin-token header 匹配 ADMIN_TOKEN
    2. 当前用户 is_admin=True
    """
    token = request.headers.get("x-admin-token", "")
    if token and token == ADMIN_TOKEN:
        return True

    if current_user and current_user.is_admin:
        return True

    raise HTTPException(status_code=403, detail="需要管理员权限")


# ============ Schemas ============

class UpdateUserPaidRequest(BaseModel):
    paid_type: str  # "free" / "monthly" / "yearly" / "permanent"
    expires_at: Optional[str] = None


class SetAdminRequest(BaseModel):
    is_admin: bool


class UpdatePriceRequest(BaseModel):
    plan: str
    price: float


# ============ 统计 ============

@router.get("/stats")
def get_stats(
    request: Request,
    db: Session = Depends(get_db),
):
    """获取仪表盘统计数据"""
    # 简易验证：从 Authorization 获取当前用户
    from api.auth import get_current_user_dependency
    # 直接用 header 验证
    token = request.headers.get("x-admin-token", "")
    if not (token and token == ADMIN_TOKEN):
        # 尝试从 JWT 获取用户
        from services.auth_service import AuthService
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            jwt_token = auth_header[7:]
            user = AuthService.get_current_user(db, jwt_token)
            if not user or not user.is_admin:
                raise HTTPException(status_code=403, detail="需要管理员权限")
        else:
            raise HTTPException(status_code=403, detail="需要管理员权限")

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_users = db.query(User).count()
    paid_users = db.query(User).filter(
        User.paid_type.in_(["monthly", "yearly", "permanent"]),
        (User.paid_type == "permanent") | (User.expires_at > now)
    ).count()
    free_users = total_users - paid_users
    paid_rate = round(paid_users / total_users * 100, 1) if total_users > 0 else 0

    monthly_income = db.query(Order).filter(
        Order.status == "paid",
        Order.paid_at >= month_start
    ).count()
    monthly_income_sum = db.query(Order).filter(
        Order.status == "paid",
        Order.paid_at >= month_start
    ).with_entities(db.query(Order.amount).filter(
        Order.status == "paid",
        Order.paid_at >= month_start
    ).subquery()).first()

    # 简化统计
    all_paid_orders = db.query(Order).filter(Order.status == "paid").all()
    total_income = sum(o.amount for o in all_paid_orders)
    total_orders = db.query(Order).count()
    paid_orders = len(all_paid_orders)

    this_month_orders = [o for o in all_paid_orders if o.paid_at and o.paid_at >= month_start]
    monthly_income = sum(o.amount for o in this_month_orders)

    return {
        "total_users": total_users,
        "paid_users": paid_users,
        "free_users": free_users,
        "paid_rate": paid_rate,
        "monthly_income": monthly_income,
        "total_income": total_income,
        "total_orders": total_orders,
        "paid_orders": paid_orders,
    }


# ============ 用户管理 ============

@router.get("/users")
def list_users(
    request: Request,
    db: Session = Depends(get_db),
):
    """获取所有用户列表"""
    token = request.headers.get("x-admin-token", "")
    if not (token and token == ADMIN_TOKEN):
        from services.auth_service import AuthService
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            user = AuthService.get_current_user(db, auth_header[7:])
            if not user or not user.is_admin:
                raise HTTPException(status_code=403, detail="需要管理员权限")
        else:
            raise HTTPException(status_code=403, detail="需要管理员权限")

    users = db.query(User).order_by(User.created_at.desc()).all()
    now = datetime.utcnow()
    user_list = []
    for u in users:
        is_active = False
        if u.paid_type == "permanent":
            is_active = True
        elif u.paid_type in ("monthly", "yearly") and u.expires_at and u.expires_at > now:
            is_active = True
        elif u.paid_type == "free" and u.created_at:
            is_active = (u.created_at + timedelta(days=7)) > now

        user_list.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "paid_type": u.paid_type,
            "paid_at": u.paid_at.isoformat() if u.paid_at else None,
            "expires_at": u.expires_at.isoformat() if u.expires_at else None,
            "is_admin": u.is_admin,
            "is_active": is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    return {"users": user_list, "total": len(user_list)}


@router.put("/users/{user_id}")
def update_user_paid(
    user_id: int,
    req: UpdateUserPaidRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """修改用户付费状态"""
    token = request.headers.get("x-admin-token", "")
    if not (token and token == ADMIN_TOKEN):
        from services.auth_service import AuthService
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            admin_user = AuthService.get_current_user(db, auth_header[7:])
            if not admin_user or not admin_user.is_admin:
                raise HTTPException(status_code=403, detail="需要管理员权限")
        else:
            raise HTTPException(status_code=403, detail="需要管理员权限")

    if req.paid_type not in ("free", "monthly", "yearly", "permanent"):
        raise HTTPException(status_code=400, detail="无效的付费类型")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.paid_type = req.paid_type
    if req.paid_type == "free":
        user.paid_at = None
        user.expires_at = None
    elif req.paid_type == "permanent":
        user.paid_at = datetime.utcnow()
        user.expires_at = None
    else:
        user.paid_at = datetime.utcnow()
        if req.expires_at:
            user.expires_at = datetime.fromisoformat(req.expires_at)
        else:
            from config import PLAN_DAYS
            days = PLAN_DAYS.get(req.paid_type, 30)
            user.expires_at = datetime.utcnow() + timedelta(days=days)

    db.commit()
    return {"message": "更新成功", "user_id": user_id, "paid_type": req.paid_type}


@router.post("/users/{user_id}/set-admin")
def set_user_admin(
    user_id: int,
    req: SetAdminRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """设置/取消管理员"""
    token = request.headers.get("x-admin-token", "")
    if not (token and token == ADMIN_TOKEN):
        from services.auth_service import AuthService
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            admin_user = AuthService.get_current_user(db, auth_header[7:])
            if not admin_user or not admin_user.is_admin:
                raise HTTPException(status_code=403, detail="需要管理员权限")
        else:
            raise HTTPException(status_code=403, detail="需要管理员权限")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_admin = req.is_admin
    db.commit()
    return {"message": "设置成功", "user_id": user_id, "is_admin": req.is_admin}


# ============ 订单管理 ============

@router.get("/orders")
def list_orders(
    request: Request,
    db: Session = Depends(get_db),
):
    """获取所有订单"""
    token = request.headers.get("x-admin-token", "")
    if not (token and token == ADMIN_TOKEN):
        from services.auth_service import AuthService
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            user = AuthService.get_current_user(db, auth_header[7:])
            if not user or not user.is_admin:
                raise HTTPException(status_code=403, detail="需要管理员权限")
        else:
            raise HTTPException(status_code=403, detail="需要管理员权限")

    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    order_list = []
    for o in orders:
        user = db.query(User).filter(User.id == o.user_id).first()
        order_list.append({
            "id": o.id,
            "order_id": o.order_id,
            "user_id": o.user_id,
            "username": user.username if user else "未知",
            "amount": o.amount,
            "status": o.status,
            "paid_type": o.paid_type,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "paid_at": o.paid_at.isoformat() if o.paid_at else None,
        })

    return {"orders": order_list, "total": len(order_list)}


# ============ 配置管理 ============

@router.get("/config")
def get_config(request: Request):
    """获取当前定价配置"""
    token = request.headers.get("x-admin-token", "")
    if not (token and token == ADMIN_TOKEN):
        from services.auth_service import AuthService
        from database import SessionLocal
        db = SessionLocal()
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                user = AuthService.get_current_user(db, auth_header[7:])
                if not user or not user.is_admin:
                    raise HTTPException(status_code=403, detail="需要管理员权限")
            else:
                raise HTTPException(status_code=403, detail="需要管理员权限")
        finally:
            db.close()

    return {
        "prices": PLAN_PRICES,
        "plan_labels": {
            "monthly": "月度会员",
            "yearly": "年度会员",
        },
        "admin_token": ADMIN_TOKEN,
    }


@router.get("/verify")
def verify_admin_status(request: Request, db: Session = Depends(get_db)):
    """验证当前用户是否为管理员"""
    token = request.headers.get("x-admin-token", "")
    if token and token == ADMIN_TOKEN:
        return {"is_admin": True}

    from services.auth_service import AuthService
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        user = AuthService.get_current_user(db, auth_header[7:])
        if user and user.is_admin:
            return {"is_admin": True, "user_id": user.id}

    return {"is_admin": False}
