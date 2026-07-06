"""
支付 API - 虎皮椒支付集成
"""

import time
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.order import Order
from config import (
    XUNHU_APPID, XUNHU_APPSECRET, XUNHU_API,
    PLAN_PRICES, PLAN_LABELS, PLAN_DAYS, FREE_TRIAL_DAYS,
)
from api.auth import get_current_user_dependency

router = APIRouter(prefix="/api/payment", tags=["支付"])


# ============ Schemas ============

class CreatePaymentRequest(BaseModel):
    plan: str  # "monthly" / "yearly" / "permanent"


class PaymentResponse(BaseModel):
    order_id: str
    amount: float
    plan: str
    pay_url: str = ""
    already_paid: bool = False


# ============ Helpers ============

def _generate_order_id() -> str:
    ts = int(time.time() * 1000)
    rand = uuid.uuid4().hex[:8]
    return f"ECOM{ts}{rand}"


def _sign_params(params: dict) -> str:
    filtered = {k: v for k, v in params.items() if k != "hash" and v != "" and v is not None}
    sorted_keys = sorted(filtered.keys())
    raw = "&".join(f"{k}={filtered[k]}" for k in sorted_keys)
    raw += XUNHU_APPSECRET
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _verify_notify_hash(params: dict) -> bool:
    received_hash = params.get("hash", "")
    if not received_hash:
        return False
    filtered = {k: v for k, v in params.items() if k != "hash" and v != "" and v is not None}
    sorted_keys = sorted(filtered.keys())
    raw = "&".join(f"{k}={filtered[k]}" for k in sorted_keys)
    raw += XUNHU_APPSECRET
    expected = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return received_hash == expected


def _get_user_payment_info(user: User) -> dict:
    """获取用户付费状态信息"""
    now = datetime.utcnow()
    is_paid = False
    expires_at = None

    if user.paid_type == "permanent":
        is_paid = True
    elif user.paid_type in ("monthly", "yearly") and user.expires_at:
        is_paid = user.expires_at > now
        expires_at = user.expires_at.isoformat()
    elif user.paid_type == "free":
        trial_end = user.created_at + timedelta(days=FREE_TRIAL_DAYS)
        is_paid = trial_end > now
        expires_at = trial_end.isoformat()

    return {
        "user_id": user.id,
        "username": user.username,
        "paid": is_paid,
        "paid_type": user.paid_type,
        "paid_at": user.paid_at.isoformat() if user.paid_at else None,
        "expires_at": expires_at,
        "is_admin": user.is_admin,
        "free_trial_days": FREE_TRIAL_DAYS,
        "registered_at": user.created_at.isoformat() if user.created_at else None,
    }


# ============ Routes ============

@router.get("/status")
def get_payment_status(current_user: User = Depends(get_current_user_dependency)):
    """查询当前用户付费状态"""
    return _get_user_payment_info(current_user)


@router.get("/prices")
def get_prices():
    """获取价格信息"""
    return {
        "prices": PLAN_PRICES,
        "plan_labels": PLAN_LABELS,
        "free_trial_days": FREE_TRIAL_DAYS,
        "description": {
            "monthly": f"月度会员 - ¥{PLAN_PRICES['monthly']}/月，有效期 30 天",
            "yearly": f"年度会员 - ¥{PLAN_PRICES['yearly']}/年，有效期 365 天",
            "permanent": "永久会员 - 一次购买，永久使用",
        },
    }


@router.post("/create", response_model=PaymentResponse)
def create_payment(
    req: CreatePaymentRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """创建支付订单"""
    if req.plan not in PLAN_PRICES and req.plan != "permanent":
        raise HTTPException(status_code=400, detail="无效的套餐类型")

    # 检查是否已付费
    if current_user.paid_type == "permanent":
        return PaymentResponse(order_id="", amount=0, plan="permanent", already_paid=True)
    if current_user.paid_type in ("monthly", "yearly") and current_user.expires_at:
        if current_user.expires_at > datetime.utcnow():
            return PaymentResponse(order_id="", amount=0, plan=req.plan, already_paid=True)

    amount = PLAN_PRICES.get(req.plan, 0)
    if amount == 0:
        raise HTTPException(status_code=400, detail="无效的金额")

    order_id = _generate_order_id()

    # 创建订单记录
    order = Order(
        order_id=order_id,
        user_id=current_user.id,
        amount=amount,
        status="pending",
        paid_type=req.plan,
    )
    db.add(order)
    db.commit()

    # 调用虎皮椒创建支付
    plan_label = PLAN_LABELS.get(req.plan, req.plan)
    nonce = str(int(time.time()))

    pay_params = {
        "version": "1.1",
        "appid": XUNHU_APPID,
        "trade_order_id": order_id,
        "total_fee": str(amount),
        "title": f"电商客服机器人 - {plan_label}",
        "body": f"电商客服机器人 {plan_label}",
        "notify_url": "/api/payment/notify",
        "nonce_str": nonce,
        "time": nonce,
        "type": "WAP",
    }
    pay_params["hash"] = _sign_params(pay_params)

    try:
        resp = requests.post(
            f"{XUNHU_API}/payment/do.html",
            json=pay_params,
            timeout=10,
        )
        data = resp.json()
        if data.get("errcode") != 0:
            raise HTTPException(
                status_code=500,
                detail=f"支付创建失败: {data.get('errmsg', '未知错误')}"
            )
        return PaymentResponse(
            order_id=order_id,
            amount=amount,
            plan=req.plan,
            pay_url=data.get("url", ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"支付服务异常: {str(e)}")


@router.post("/notify")
async def payment_notify(request: Request, db: Session = Depends(get_db)):
    """虎皮椒支付回调"""
    form = await request.form()
    params = dict(form)

    if not _verify_notify_hash(params):
        raise HTTPException(status_code=400, detail="签名验证失败")

    order_id = params.get("trade_order_id", "")
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status == "paid":
        return {"errcode": 0, "errmsg": "success"}

    # 更新订单状态
    order.status = "paid"
    order.paid_at = datetime.utcnow()

    # 更新用户付费状态
    user = db.query(User).filter(User.id == order.user_id).first()
    if user:
        now = datetime.utcnow()
        user.paid_type = order.paid_type
        user.paid_at = now

        if order.paid_type == "permanent":
            user.expires_at = None
        else:
            days = PLAN_DAYS.get(order.paid_type, 30)
            # 如果还在有效期内，在现有到期时间基础上续期
            if user.expires_at and user.expires_at > now:
                user.expires_at = user.expires_at + timedelta(days=days)
            else:
                user.expires_at = now + timedelta(days=days)

    db.commit()
    return {"errcode": 0, "errmsg": "success"}


@router.get("/check/{order_id}")
def check_payment(order_id: str, db: Session = Depends(get_db)):
    """检查支付状态"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {
        "order_id": order_id,
        "status": order.status,
        "paid_type": order.paid_type,
        "amount": order.amount,
    }
