"""
系统设置API路由
"""

import os
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="/api/settings", tags=["系统设置"])

# 设置文件路径
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "settings.json")


def load_settings():
    """加载设置"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_settings(data):
    """保存设置"""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("")
def get_settings():
    """获取所有设置"""
    return load_settings()


@router.put("/pinduoduo")
def update_pdd_config(config: dict):
    """更新拼多多配置"""
    settings = load_settings()
    settings["pinduoduo"] = config
    save_settings(settings)
    return {"message": "拼多多配置已保存"}


@router.put("/ai")
def update_ai_config(config: dict):
    """更新AI配置"""
    settings = load_settings()
    settings["ai"] = config
    save_settings(settings)
    return {"message": "AI配置已保存"}
