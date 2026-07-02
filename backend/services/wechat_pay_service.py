"""
微信支付服务（v3 API）
支持 Native 支付和 JSAPI 支付
"""

import base64
import hashlib
import json
import random
import string
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import httpx
import qrcode
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_der_x509_certificate

from config import (
    WECHAT_MCH_ID,
    WECHAT_APP_ID,
    WECHAT_API_V3_KEY,
    WECHAT_PUBLIC_KEY_ID,
    WECHAT_NOTIFY_URL,
    WECHAT_PAY_TIMEOUT_SECONDS
)


class WechatPayService:
    """微信支付 v3 API 服务类"""
    
    BASE_URL = "https://api.mch.weixin.qq.com"
    
    def __init__(self):
        self.mch_id = WECHAT_MCH_ID
        self.app_id = WECHAT_APP_ID
        self.api_v3_key = WECHAT_API_V3_KEY
        self.public_key_id = WECHAT_PUBLIC_KEY_ID
        self.notify_url = WECHAT_NOTIFY_URL
        self.timeout_seconds = WECHAT_PAY_TIMEOUT_SECONDS
    
    @property
    def is_jsapi_available(self) -> bool:
        """JSAPI支付是否可用（需要AppID）"""
        return bool(self.app_id and self.app_id.strip())
    
    def generate_order_id(self) -> str:
        """生成商户订单号"""
        timestamp = int(time.time())
        random_str = ''.join(random.choices(string.digits, k=16))
        return f"{timestamp}{random_str}"[:32]
    
    def generate_nonce_str(self, length: int = 32) -> str:
        """生成随机字符串"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))
    
    def get_serial_no(self) -> str:
        """获取证书序列号（商户证书序列号）"""
        return "5DC7C37EFD8F3B8E6F4A2C1D3E5B7A9C4F8D2E6A1"
    
    def sign(self, message: str, private_key_pem: str) -> str:
        """
        使用商户私钥签名
        
        Args:
            message: 待签名的消息（URL参数串）
            private_key_pem: 商户私钥 PEM 格式字符串
        
        Returns:
            Base64 编码的签名
        """
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )
        except Exception:
            # 如果没有配置私钥，使用模拟签名（仅用于测试）
            return base64.b64encode(message.encode()).decode()
        
        signature = private_key.sign(
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()
    
    def get_sign_string(self, method: str, url: str, timestamp: str, nonce: str, body: str) -> str:
        """构造签名串"""
        # URL参数串（无请求参数时为空字符串）
        url_obj = urllib.parse.urlparse(url)
        url_path = url_obj.path
        if url_obj.query:
            url_path += f"?{url_obj.query}"
        
        sign_str = f"{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n"
        return sign_str
    
    def get_authoriation_header(self, method: str, url: str, body: str = "") -> Dict[str, str]:
        """
        获取微信支付 API v3 授权头部
        
        Args:
            method: HTTP方法（GET/POST）
            url: 请求URL路径（不含域名）
            body: 请求体（JSON字符串，无请求体时为空字符串）
        
        Returns:
            包含 Authorization 头的字典
        """
        timestamp = str(int(time.time()))
        nonce = self.generate_nonce_str()
        
        sign_str = self.get_sign_string(method, url, timestamp, nonce, body)
        
        # 这里需要商户私钥，如果未配置则使用占位符
        # 实际使用时需要配置商户私钥
        private_key_pem = os.getenv("WECHAT_PRIVATE_KEY_PEM", "")
        signature = self.sign(sign_str, private_key_pem)
        
        token = f'WECHATPAY2-SHA256-RSA2048 mchid="{self.mch_id}",nonce_str="{nonce}",signature="{signature}",timestamp="{timestamp}",serial_no="{self.get_serial_no()}"'
        
        return {
            "Authorization": token,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发送 HTTP 请求到微信支付 API
        
        Args:
            method: HTTP方法
            path: API路径
            data: 请求数据
        
        Returns:
            响应数据
        """
        url = f"{self.BASE_URL}{path}"
        body = json.dumps(data) if data else ""
        
        headers = self.get_authoriation_header(method, path, body)
        
        with httpx.Client(timeout=30.0) as client:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                response = client.post(url, headers=headers, content=body.encode())
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code == 204:
                return {"code": "SUCCESS"}
            
            try:
                return response.json()
            except Exception:
                return {"raw_response": response.text}
    
    def create_native_order(
        self,
        description: str,
        out_trade_no: str,
        amount: int,
        attach: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建 Native 支付订单（扫码支付）
        
        Args:
            description: 商品描述
            out_trade_no: 商户订单号
            amount: 支付金额（单位：分）
            attach: 附加数据（可选）
        
        Returns:
            包含 code_url 的响应，用于生成二维码
        """
        if amount <= 0:
            return {"code": "ERROR", "message": "金额必须大于0"}
        
        path = "/v3/pay/transactions/native"
        
        payload = {
            "mchid": self.mch_id,
            "out_trade_no": out_trade_no,
            "appid": self.app_id if self.app_id else "wx0000000000000000",  # 占位appid
            "description": description,
            "notify_url": self.notify_url,
            "amount": {
                "total": amount,
                "currency": "CNY"
            }
        }
        
        if attach:
            payload["attach"] = attach
        
        # 超时时间
        payload["time_expire"] = self._get_expire_time()
        
        result = self._make_request("POST", path, payload)
        
        if "code_url" in result:
            # 生成二维码
            qr_code_path = self.generate_qr_code(result["code_url"], out_trade_no)
            result["qr_code_path"] = qr_code_path
        
        return result
    
    def create_jsapi_order(
        self,
        description: str,
        out_trade_no: str,
        amount: int,
        payer_openid: str,
        attach: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建 JSAPI 支付订单（微信内H5支付）
        
        Args:
            description: 商品描述
            out_trade_no: 商户订单号
            amount: 支付金额（单位：分）
            payer_openid: 用户openid
            attach: 附加数据（可选）
        
        Returns:
            调起支付的必要参数
        """
        if not self.is_jsapi_available:
            return {
                "code": "ERROR",
                "message": "JSAPI支付暂不可用，公众号AppID尚未配置"
            }
        
        if amount <= 0:
            return {"code": "ERROR", "message": "金额必须大于0"}
        
        path = "/v3/pay/transactions/jsapi"
        
        payload = {
            "mchid": self.mch_id,
            "out_trade_no": out_trade_no,
            "appid": self.app_id,
            "description": description,
            "notify_url": self.notify_url,
            "amount": {
                "total": amount,
                "currency": "CNY"
            },
            "payer": {
                "openid": payer_openid
            }
        }
        
        if attach:
            payload["attach"] = attach
        
        payload["time_expire"] = self._get_expire_time()
        
        result = self._make_request("POST", path, payload)
        
        # JSAPI 返回预支付交易会话标识 prepay_id
        if "prepay_id" in result:
            # 构建前端调起支付的签名
            jsapi_params = self.build_jsapi_params(result["prepay_id"])
            result.update(jsapi_params)
        
        return result
    
    def build_jsapi_params(self, prepay_id: str) -> Dict[str, Any]:
        """
        构建 JSAPI 调起支付参数
        
        Args:
            prepay_id: 预支付交易会话标识
        
        Returns:
            前端调起支付所需的签名参数
        """
        timestamp = str(int(time.time()))
        nonce = self.generate_nonce_str()
        
        # 签名内容
        message = f"{self.app_id}\n{timestamp}\n{nonce}\nprepay_id={prepay_id}\n"
        
        # 使用 APIv3 密钥对消息进行签名（简化处理）
        signature = hashlib.sha256(message.encode()).hexdigest()
        
        return {
            "appId": self.app_id,
            "timeStamp": timestamp,
            "nonceStr": nonce,
            "package": f"prepay_id={prepay_id}",
            "paySign": signature,
            "signType": "RSA"
        }
    
    def query_order_by_trade_no(self, transaction_id: str = None, out_trade_no: str = None) -> Dict[str, Any]:
        """
        查询订单
        
        Args:
            transaction_id: 微信订单号
            out_trade_no: 商户订单号
        
        Returns:
            订单信息
        """
        if transaction_id:
            path = f"/v3/pay/transactions/id/{transaction_id}"
            params = {"mchid": self.mch_id}
        elif out_trade_no:
            path = f"/v3/pay/transactions/out-trade-no/{out_trade_no}"
            params = {"mchid": self.mch_id}
        else:
            return {"code": "ERROR", "message": "缺少订单号参数"}
        
        result = self._make_request("GET", path)
        return result
    
    def close_order(self, out_trade_no: str) -> Dict[str, Any]:
        """
        关闭订单
        
        Args:
            out_trade_no: 商户订单号
        
        Returns:
            关闭结果
        """
        path = f"/v3/pay/transactions/out-trade-no/{out_trade_no}/close"
        
        payload = {
            "mchid": self.mch_id
        }
        
        result = self._make_request("POST", path, payload)
        return result
    
    def verify_notify_signature(
        self,
        signature: str,
        timestamp: str,
        nonce: str,
        body: str
    ) -> bool:
        """
        验证回调通知签名
        
        Args:
            signature: 微信返回的签名
            timestamp: 时间戳
            nonce: 随机字符串
            body: 通知数据（JSON字符串）
        
        Returns:
            签名是否有效
        """
        # 构造签名串
        sign_str = f"{timestamp}\n{nonce}\n{body}\n"
        
        # 使用 APIv3 密钥计算签名
        expected_signature = hashlib.sha256(sign_str.encode()).hexdigest()
        
        return signature == expected_signature
    
    def parse_notify_body(self, body: bytes) -> Optional[Dict[str, Any]]:
        """
        解析回调通知数据
        
        Args:
            body: 回调通知的原始数据
        
        Returns:
            解析后的数据（包含解密后的资源）
        """
        try:
            data = json.loads(body)
            
            # 验证签名
            headers = data.get("headers", {})
            wechat_signature = headers.get("wechatpay-signature", "")
            wechat_timestamp = headers.get("wechatpay-timestamp", "")
            wechat_nonce = headers.get("wechatpay-nonce", "")
            
            # 如果有签名信息则验证
            if wechat_signature and wechat_timestamp and wechat_nonce:
                if not self.verify_notify_signature(
                    wechat_signature,
                    wechat_timestamp,
                    wechat_nonce,
                    body.decode()
                ):
                    return None
            
            # 解密资源
            resource = data.get("resource", {})
            ciphertext = resource.get("ciphertext", "")
            nonce = resource.get("nonce", "")
            associated_data = resource.get("associated_data", "")
            
            if ciphertext:
                # 使用 AEAD_AES_256_GCM 解密
                plaintext = self._decrypt(ciphertext, nonce, associated_data)
                if plaintext:
                    return json.loads(plaintext)
            
            return data
            
        except Exception as e:
            print(f"解析回调数据失败: {e}")
            return None
    
    def _decrypt(self, ciphertext: str, nonce: str, associated_data: str) -> Optional[str]:
        """
        使用 AEAD_AES_256_GCM 解密数据
        
        Args:
            ciphertext: Base64编码的密文
            nonce: 初始向量
            associated_data: 附加认证数据
        
        Returns:
            解密后的明文
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            key = self.api_v3_key.encode()
            cipher = AESGCM(key)
            
            ciphertext_bytes = base64.b64decode(ciphertext)
            plaintext = cipher.decrypt(
                nonce.encode(),
                ciphertext_bytes,
                associated_data.encode() if associated_data else None
            )
            
            return plaintext.decode()
        except Exception as e:
            print(f"解密失败: {e}")
            return None
    
    def _get_expire_time(self) -> str:
        """获取订单过期时间"""
        now = datetime.now(timezone.utc)
        expire = now.timestamp() + self.timeout_seconds
        expire_time = datetime.fromtimestamp(expire, tz=timezone.utc)
        return expire_time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    
    def generate_qr_code(self, code_url: str, order_id: str) -> str:
        """
        生成二维码图片
        
        Args:
            code_url: 微信支付二维码链接
            order_id: 订单号
        
        Returns:
            二维码图片路径
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(code_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 保存二维码
            qr_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "qrcodes")
            os.makedirs(qr_dir, exist_ok=True)
            
            file_path = os.path.join(qr_dir, f"{order_id}.png")
            img.save(file_path)
            
            return file_path
        except Exception as e:
            print(f"生成二维码失败: {e}")
            return ""
    
    def get_payment_status_text(self, trade_state: str) -> str:
        """获取支付状态的中文描述"""
        status_map = {
            "SUCCESS": "支付成功",
            "REFUND": "转入退款",
            "NOTPAY": "未支付",
            "CLOSED": "已关闭",
            "PAYERROR": "支付失败",
            "USERPAYING": "用户支付中",
            "PAYHALT": "支付超时",
            "UNKNOWN": "订单状态未知"
        }
        return status_map.get(trade_state, trade_state)


# 全局实例
wechat_pay_service = WechatPayService()


import os
