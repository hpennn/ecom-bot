"""
微信支付 API 路由
支持 Native 支付（扫码支付）和 JSAPI 支付（微信内H5支付）
"""

import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from services.wechat_pay_service import wechat_pay_service
from config import BASE_DIR

router = APIRouter(prefix="/api/wechat-pay", tags=["微信支付"])


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    description: str = Field(..., min_length=1, max_length=127, description="商品描述")
    amount: int = Field(..., gt=0, description="支付金额（单位：分）")
    pay_type: str = Field(default="native", description="支付类型: native=扫码支付, jsapi=JSAPI支付")
    openid: Optional[str] = Field(default=None, description="用户openid（JSAPI支付必填）")
    attach: Optional[str] = Field(default=None, description="附加数据")
    order_id: Optional[str] = Field(default=None, description="自定义订单号（可选）")


class QueryOrderRequest(BaseModel):
    """查询订单请求"""
    transaction_id: Optional[str] = Field(default=None, description="微信订单号")
    out_trade_no: Optional[str] = Field(default=None, description="商户订单号")


@router.post("/create-order")
async def create_wechat_order(request: CreateOrderRequest):
    """
    创建微信支付订单
    
    支持 Native 支付（扫码支付）和 JSAPI 支付（微信内H5支付）
    
    - **description**: 商品描述
    - **amount**: 支付金额（单位：分，如 1 元 = 100）
    - **pay_type**: 支付类型，native 或 jsapi
    - **openid**: JSAPI 支付时必填的用户 openid
    """
    # 生成订单号
    out_trade_no = request.order_id or wechat_pay_service.generate_order_id()
    
    try:
        if request.pay_type == "native":
            # Native 支付 - 扫码支付
            result = wechat_pay_service.create_native_order(
                description=request.description,
                out_trade_no=out_trade_no,
                amount=request.amount,
                attach=request.attach
            )
            
            if "code" in result and result["code"] == "ERROR":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get("message", "创建订单失败")
                )
            
            response_data = {
                "success": True,
                "order_id": out_trade_no,
                "pay_type": "native",
                "code_url": result.get("code_url"),
                "qr_code_url": None
            }
            
            # 如果生成了二维码，返回访问路径
            if result.get("qr_code_path"):
                response_data["qr_code_url"] = f"/api/wechat-pay/qrcode/{out_trade_no}"
            
            return response_data
            
        elif request.pay_type == "jsapi":
            # JSAPI 支付 - 微信内支付
            if not request.openid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="JSAPI支付需要提供 openid"
                )
            
            if not wechat_pay_service.is_jsapi_available:
                return {
                    "success": False,
                    "code": "APPID_NOT_CONFIGURED",
                    "message": "JSAPI支付暂不可用，公众号AppID尚未配置，请等待服务号审核通过"
                }
            
            result = wechat_pay_service.create_jsapi_order(
                description=request.description,
                out_trade_no=out_trade_no,
                amount=request.amount,
                payer_openid=request.openid,
                attach=request.attach
            )
            
            if "code" in result and result["code"] == "ERROR":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get("message", "创建订单失败")
                )
            
            return {
                "success": True,
                "order_id": out_trade_no,
                "pay_type": "jsapi",
                "payment_params": {
                    "appId": result.get("appId"),
                    "timeStamp": result.get("timeStamp"),
                    "nonceStr": result.get("nonceStr"),
                    "package": result.get("package"),
                    "paySign": result.get("paySign"),
                    "signType": result.get("signType")
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的支付类型: {request.pay_type}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建订单失败: {str(e)}"
        )


@router.get("/query-order/{order_id}")
async def query_wechat_order(order_id: str):
    """
    查询微信支付订单状态
    
    - **order_id**: 商户订单号或微信订单号
    """
    try:
        # 优先使用商户订单号查询
        result = wechat_pay_service.query_order_by_trade_no(out_trade_no=order_id)
        
        if "code" in result and result.get("code") == "ERROR":
            # 尝试作为微信订单号查询
            result = wechat_pay_service.query_order_by_trade_no(transaction_id=order_id)
        
        if "trade_state" in result:
            return {
                "success": True,
                "order_id": result.get("out_trade_no", order_id),
                "transaction_id": result.get("transaction_id"),
                "trade_state": result.get("trade_state"),
                "trade_state_text": wechat_pay_service.get_payment_status_text(result.get("trade_state")),
                "amount": result.get("amount", {}).get("total"),
                "payer_total": result.get("amount", {}).get("payer_total"),
                "success_time": result.get("success_time"),
                "attach": result.get("attach")
            }
        
        return {
            "success": False,
            "code": "QUERY_FAILED",
            "message": result.get("message", "查询失败，请稍后重试")
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询订单失败: {str(e)}"
        )


@router.post("/notify")
async def wechat_pay_notify(request: Request):
    """
    微信支付回调通知
    
    微信支付会在支付完成后调用此接口通知商户
    """
    try:
        # 获取原始请求体
        body = await request.body()
        
        # 解析并验证回调数据
        notify_data = wechat_pay_service.parse_notify_body(body)
        
        if not notify_data:
            return {"code": "ERROR", "message": "验签失败或解析失败"}
        
        # 处理不同事件类型
        event_type = notify_data.get("event_type", notify_data.get("msg", ""))
        
        if "pay" in event_type.lower() or "transaction" in event_type.lower():
            # 支付成功通知
            trade_state = notify_data.get("trade_state", notify_data.get("status"))
            
            if trade_state == "SUCCESS":
                # TODO: 在这里更新本地订单状态
                # 获取订单信息
                out_trade_no = notify_data.get("out_trade_no")
                transaction_id = notify_data.get("transaction_id")
                amount = notify_data.get("amount", {})
                total = amount.get("total") if isinstance(amount, dict) else 0
                
                print(f"✅ 微信支付成功: 订单号={out_trade_no}, 微信订单号={transaction_id}, 金额={total}")
                
                # 返回成功响应
                return {
                    "code": "SUCCESS",
                    "message": "接收成功"
                }
            else:
                print(f"⚠️ 微信支付状态: {trade_state}")
                return {
                    "code": "SUCCESS",
                    "message": f"状态已记录: {trade_state}"
                }
        
        # 返回成功响应（告诉微信支付我们已收到通知）
        return {
            "code": "SUCCESS",
            "message": "处理成功"
        }
    
    except Exception as e:
        print(f"处理微信支付回调失败: {e}")
        return {
            "code": "ERROR",
            "message": str(e)
        }


@router.get("/qrcode/{order_id}")
async def get_qrcode(order_id: str):
    """
    获取支付二维码图片
    
    - **order_id**: 订单号
    """
    qr_path = os.path.join(BASE_DIR, "data", "qrcodes", f"{order_id}.png")
    
    if not os.path.exists(qr_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="二维码不存在或已过期"
        )
    
    # 返回图片文件
    from fastapi.responses import FileResponse
    return FileResponse(
        qr_path,
        media_type="image/png",
        filename=f"wechat_pay_{order_id}.png"
    )


@router.get("/config")
async def get_pay_config():
    """
    获取微信支付配置信息
    
    返回前端需要的支付配置
    """
    return {
        "mch_id": wechat_pay_service.mch_id,
        "app_id": wechat_pay_service.app_id or "",
        "jsapi_available": wechat_pay_service.is_jsapi_available,
        "notify_url": wechat_pay_service.notify_url,
        "pay_timeout": wechat_pay_service.timeout_seconds
    }


@router.post("/close-order/{order_id}")
async def close_order(order_id: str):
    """
    关闭未支付订单
    
    - **order_id**: 商户订单号
    """
    try:
        result = wechat_pay_service.close_order(order_id)
        
        if result.get("code") == "SUCCESS":
            return {
                "success": True,
                "message": "订单已关闭"
            }
        
        return {
            "success": False,
            "code": result.get("code", "CLOSE_FAILED"),
            "message": result.get("message", "关闭订单失败")
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"关闭订单失败: {str(e)}"
        )
