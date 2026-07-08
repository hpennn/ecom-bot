"""
新功能API路由：关键词回复、转人工、敏感词、消息记录、数据统计
"""

import json
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models.keyword_reply import KeywordReply, TransferKeyword, SensitiveWord, ConversationMessage, DailyStats

# ========== 关键词回复 ==========
keyword_router = APIRouter(prefix="/api/knowledge/keywords", tags=["关键词回复"])

@keyword_router.get("")
def list_keyword_replies(store_id: int, db: Session = Depends(get_db)):
    items = db.query(KeywordReply).filter(KeywordReply.store_id == store_id).order_by(KeywordReply.priority.desc()).all()
    return {"items": [{"id": i.id, "keywords": json.loads(i.keywords) if i.keywords else [], "reply": i.reply, "match_type": i.match_type, "is_active": i.is_active, "priority": i.priority} for i in items]}

@keyword_router.post("")
def create_keyword_reply(data: dict, db: Session = Depends(get_db)):
    item = KeywordReply(store_id=data["store_id"], keywords=json.dumps(data.get("keywords", []), ensure_ascii=False), reply=data["reply"], match_type=data.get("match_type", "contains"), is_active=data.get("is_active", True), priority=data.get("priority", 0))
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "message": "创建成功"}

@keyword_router.put("/{item_id}")
def update_keyword_reply(item_id: int, data: dict, db: Session = Depends(get_db)):
    item = db.query(KeywordReply).filter(KeywordReply.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="未找到")
    for k, v in data.items():
        if k == "keywords":
            item.keywords = json.dumps(v, ensure_ascii=False)
        elif hasattr(item, k):
            setattr(item, k, v)
    db.commit()
    return {"message": "更新成功"}

@keyword_router.delete("/{item_id}")
def delete_keyword_reply(item_id: int, db: Session = Depends(get_db)):
    item = db.query(KeywordReply).filter(KeywordReply.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="未找到")
    db.delete(item)
    db.commit()
    return {"message": "删除成功"}


# ========== 转人工关键词 ==========
transfer_router = APIRouter(prefix="/api/knowledge/transfer", tags=["转人工"])

@transfer_router.get("")
def list_transfer_keywords(store_id: int, db: Session = Depends(get_db)):
    items = db.query(TransferKeyword).filter(TransferKeyword.store_id == store_id).all()
    return {"items": [{"id": i.id, "keywords": json.loads(i.keywords) if i.keywords else [], "reply_message": i.reply_message, "is_active": i.is_active} for i in items]}

@transfer_router.post("")
def create_transfer_keyword(data: dict, db: Session = Depends(get_db)):
    item = TransferKeyword(store_id=data["store_id"], keywords=json.dumps(data.get("keywords", []), ensure_ascii=False), reply_message=data.get("reply_message", "正在为您转接人工客服，请稍候..."), is_active=data.get("is_active", True))
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "message": "创建成功"}

@transfer_router.put("/{item_id}")
def update_transfer_keyword(item_id: int, data: dict, db: Session = Depends(get_db)):
    item = db.query(TransferKeyword).filter(TransferKeyword.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="未找到")
    for k, v in data.items():
        if k == "keywords":
            item.keywords = json.dumps(v, ensure_ascii=False)
        elif hasattr(item, k):
            setattr(item, k, v)
    db.commit()
    return {"message": "更新成功"}

@transfer_router.delete("/{item_id}")
def delete_transfer_keyword(item_id: int, db: Session = Depends(get_db)):
    item = db.query(TransferKeyword).filter(TransferKeyword.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="未找到")
    db.delete(item)
    db.commit()
    return {"message": "删除成功"}


# ========== 敏感词管理 ==========
sensitive_router = APIRouter(prefix="/api/knowledge/sensitive", tags=["敏感词"])

@sensitive_router.get("")
def list_sensitive_words(store_id: int, db: Session = Depends(get_db)):
    items = db.query(SensitiveWord).filter((SensitiveWord.store_id == store_id) | (SensitiveWord.is_global == True)).all()
    return {"items": [{"id": i.id, "word": i.word, "replacement": i.replacement, "is_global": i.is_global} for i in items]}

@sensitive_router.post("")
def create_sensitive_word(data: dict, db: Session = Depends(get_db)):
    item = SensitiveWord(store_id=data.get("store_id", 0), word=data["word"], replacement=data.get("replacement", "***"), is_global=data.get("is_global", False))
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "message": "添加成功"}

@sensitive_router.delete("/{item_id}")
def delete_sensitive_word(item_id: int, db: Session = Depends(get_db)):
    item = db.query(SensitiveWord).filter(SensitiveWord.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="未找到")
    db.delete(item)
    db.commit()
    return {"message": "删除成功"}


# ========== 会话消息记录 ==========
message_router = APIRouter(prefix="/api/conversations", tags=["会话消息"])

@message_router.get("/{conversation_id}/messages")
def get_conversation_messages(conversation_id: int, limit: int = 50, db: Session = Depends(get_db)):
    messages = db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conversation_id).order_by(ConversationMessage.created_at.asc()).limit(limit).all()
    return {"messages": [{"id": m.id, "role": m.role, "content": m.content, "reply_type": m.reply_type, "metadata": json.loads(m.metadata_json) if m.metadata_json else None, "created_at": str(m.created_at)} for m in messages]}


# ========== 数据统计 ==========
stats_router = APIRouter(prefix="/api/stats", tags=["数据统计"])

@stats_router.get("/overview")
def get_stats_overview(store_id: Optional[int] = None, db: Session = Depends(get_db)):
    today = date.today().isoformat()
    week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    month_start = date.today().replace(day=1).isoformat()
    
    def calc(start, end, sid):
        q = db.query(DailyStats).filter(DailyStats.date >= start, DailyStats.date <= end)
        if sid:
            q = q.filter(DailyStats.store_id == sid)
        stats = q.all()
        total = sum(s.total_messages or 0 for s in stats)
        kw = sum(s.keyword_replies or 0 for s in stats)
        know = sum(s.knowledge_replies or 0 for s in stats)
        ai = sum(s.ai_replies or 0 for s in stats)
        transfer = sum(s.transfer_replies or 0 for s in stats)
        customers = sum(s.unique_customers or 0 for s in stats)
        hit = round((kw + know) / total * 100, 1) if total > 0 else 0
        return {"total_messages": total, "keyword_replies": kw, "knowledge_replies": know, "ai_replies": ai, "transfer_replies": transfer, "unique_customers": customers, "hit_rate": hit}
    
    return {"today": calc(today, today, store_id), "this_week": calc(week_start, today, store_id), "this_month": calc(month_start, today, store_id)}

@stats_router.get("/{store_id}/daily")
def get_daily_stats(store_id: int, days: int = Query(default=7, le=90), db: Session = Depends(get_db)):
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    stats = db.query(DailyStats).filter(DailyStats.store_id == store_id, DailyStats.date >= start_date.isoformat(), DailyStats.date <= end_date.isoformat()).order_by(DailyStats.date.asc()).all()
    
    date_map = {s.date: s for s in stats}
    result = []
    current = start_date
    while current <= end_date:
        d = current.isoformat()
        s = date_map.get(d)
        result.append({"date": d, "total_messages": s.total_messages if s else 0, "keyword_replies": s.keyword_replies if s else 0, "knowledge_replies": s.knowledge_replies if s else 0, "ai_replies": s.ai_replies if s else 0, "transfer_replies": s.transfer_replies if s else 0})
        current += timedelta(days=1)
    
    return {"store_id": store_id, "days": days, "data": result}
