"""
配置文件
包含数据库、JWT、第三方API等配置
"""

import os
from datetime import timedelta

# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 确保data目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# 数据库配置
DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'ecom_bot.db')}"

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# 豆包AI配置
DOUBAO_API_KEY = os.getenv("ARK_API_KEY", "ark-4f063f47-ee3d-45a2-a6db-677cc71cf784-041e9")
DOUBAO_ENDPOINT = os.getenv("DOUBAO_ENDPOINT", "https://ark.cn-beijing.volces.com/api/v3")
DOUBAO_MODEL_ID = os.getenv("DOUBAO_MODEL_ID", "ep-20260623003404-7lqtt")

# 拼多多配置
PINDUODUO_API_URL = "https://open.pinduoduo.com"
PINDUODUO_CLIENT_ID = os.getenv("PINDUODUO_CLIENT_ID", "")
PINDUODUO_CLIENT_SECRET = os.getenv("PINDUODUO_CLIENT_SECRET", "")

# CORS配置
ALLOWED_ORIGINS = [
    "https://zhinenti.cn",
    "https://www.zhinenti.cn",
    "http://47.113.216.237",
    "http://47.113.216.237:8000",
    "http://47.113.216.237:3000",
    "http://localhost:3000",
    "http://localhost:8000",
]

# 分页配置
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# 知识库匹配配置
KNOWLEDGE_MATCH_THRESHOLD = 0.7  # 相似度阈值
MAX_KNOWLEDGE_CONTEXT = 5  # 最多返回5条知识库条目作为上下文

# 知识库匹配配置
KNOWLEDGE_MATCH_THRESHOLD = 0.7  # 相似度阈值
MAX_KNOWLEDGE_CONTEXT = 5  # 最多返回5条知识库条目作为上下文

# 微信支付配置（v3 API）
WECHAT_MCH_ID = "1747556361"  # 商户号
WECHAT_APP_ID = "wx4c2a0d007ce2a7e2"  # 公众号AppID
WECHAT_API_V2_KEY = "bOQk2mHO7RtfGxEoXN4Y1CWb01nolCDJ"
WECHAT_API_V3_KEY = "FRrHxAA7BxYXEGsFJfCJBcndbDDnkpM5"
WECHAT_PUBLIC_KEY_ID = "PUB_KEY_ID_0117475563612026070100111667001400"
WECHAT_NOTIFY_URL = "https://zhinenti.cn/api/wechat-pay/notify"  # 支付结果回调地址
WECHAT_PAY_TIMEOUT_SECONDS = 900  # 订单超时时间（15分钟）


# 虎皮椒支付配置
XUNHU_APPID = "201906182239"
XUNHU_APPSECRET = "a03834403fd0101fb1c622545967b3db"
XUNHU_API = "https://api.xunhupay.com"

# 定价配置
PLAN_PRICES = {
    "monthly": 99.0,
    "yearly": 666.0,
}
PLAN_LABELS = {
    "monthly": "月度会员",
    "yearly": "年度会员",
}
PLAN_DAYS = {
    "monthly": 30,
    "yearly": 365,
}
FREE_TRIAL_DAYS = 7

# 管理员 Token
ADMIN_TOKEN = "ecom-bot-admin-2024"
