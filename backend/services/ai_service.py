"""
AI智能回复服务 - 增强版
优先级：敏感词过滤 -> 转人工关键词 -> 关键词回复 -> 知识库匹配 -> AI生成
"""

import re
import json
import random
from typing import Optional, List, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
import httpx

from config import DOUBAO_API_KEY, DOUBAO_ENDPOINT, DOUBAO_MODEL_ID
from models.knowledge import KnowledgeItem
from models.keyword_reply import KeywordReply, TransferKeyword, SensitiveWord, ConversationMessage, DailyStats


class AIService:

    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    @staticmethod
    def check_sensitive_word(db: Session, store_id: int, text: str) -> Tuple[bool, str]:
        """检查敏感词，返回 (是否包含敏感词, 过滤后的文本)"""
        words = db.query(SensitiveWord).filter(
            (SensitiveWord.store_id == store_id) | (SensitiveWord.is_global == True),
        ).all()
        
        filtered = text
        has_sensitive = False
        for w in words:
            if w.word.lower() in text.lower():
                has_sensitive = True
                filtered = re.sub(re.escape(w.word), w.replacement, filtered, flags=re.IGNORECASE)
        
        return has_sensitive, filtered

    @staticmethod
    def check_transfer_keyword(db: Session, store_id: int, message: str) -> Optional[str]:
        """检查是否触发转人工，返回转人工提示语或None"""
        rules = db.query(TransferKeyword).filter(
            TransferKeyword.store_id == store_id,
            TransferKeyword.is_active == True
        ).all()
        
        msg_lower = message.lower()
        for rule in rules:
            try:
                keywords = json.loads(rule.keywords)
            except:
                keywords = [rule.keywords]
            
            for kw in keywords:
                if kw.lower().strip() and kw.lower().strip() in msg_lower:
                    return rule.reply_message
        
        return None

    @staticmethod
    def match_keyword_reply(db: Session, store_id: int, message: str) -> Optional[str]:
        """匹配关键词回复"""
        rules = db.query(KeywordReply).filter(
            KeywordReply.store_id == store_id,
            KeywordReply.is_active == True
        ).order_by(KeywordReply.priority.desc()).all()
        
        msg_lower = message.lower()
        for rule in rules:
            try:
                keywords = json.loads(rule.keywords)
            except:
                keywords = [rule.keywords]
            
            for kw in keywords:
                kw_stripped = kw.lower().strip()
                if not kw_stripped:
                    continue
                    
                if rule.match_type == "exact":
                    if msg_lower == kw_stripped:
                        return rule.reply
                elif rule.match_type == "regex":
                    try:
                        if re.search(kw_stripped, msg_lower):
                            return rule.reply
                    except:
                        pass
                else:  # contains
                    if kw_stripped in msg_lower:
                        return rule.reply
        
        return None

    @staticmethod
    def search_knowledge(db: Session, store_id: int, query: str, limit: int = 5) -> List[Tuple[KnowledgeItem, float]]:
        items = db.query(KnowledgeItem).filter(
            KnowledgeItem.store_id == store_id,
            KnowledgeItem.is_active == 1
        ).order_by(KnowledgeItem.priority.desc()).all()
        
        matches = []
        query_lower = query.lower()
        query_keywords = set(re.findall(r'\w+', query_lower))
        
        for item in items:
            similarity = AIService._calculate_similarity(query, item.question)
            
            if item.keywords:
                item_keywords = set(re.findall(r'\w+', item.keywords.lower()))
                if query_keywords & item_keywords:
                    similarity = max(similarity, 0.6)
            
            if query_lower in item.question.lower() or item.question.lower() in query_lower:
                similarity = max(similarity, 0.8)
            
            if similarity >= 0.7:
                matches.append((item, similarity))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]

    @staticmethod
    def save_message(db: Session, conversation_id: int, role: str, content: str, 
                     reply_type: str = None, metadata: dict = None):
        """保存会话消息"""
        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            reply_type=reply_type,
            metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else None
        )
        db.add(msg)
        db.commit()

    @staticmethod
    def update_daily_stats(db: Session, store_id: int, reply_type: str, customer_id: str = None):
        """更新每日统计"""
        today = date.today().isoformat()
        stats = db.query(DailyStats).filter(
            DailyStats.store_id == store_id,
            DailyStats.date == today
        ).first()
        
        if not stats:
            stats = DailyStats(store_id=store_id, date=today, total_messages=0,
                             keyword_replies=0, knowledge_replies=0, ai_replies=0,
                             transfer_replies=0, default_replies=0, unique_customers=0)
            db.add(stats)
            db.flush()
        
        stats.total_messages += 1
        if reply_type == "keyword":
            stats.keyword_replies += 1
        elif reply_type == "knowledge":
            stats.knowledge_replies += 1
        elif reply_type == "ai":
            stats.ai_replies += 1
        elif reply_type == "transfer":
            stats.transfer_replies += 1
        else:
            stats.default_replies += 1
        
        db.commit()

    @staticmethod
    async def generate_reply(db: Session, store_id: int, question: str, 
                           conversation_id: int = None, customer_id: str = None) -> dict:
        """
        生成回复 - 完整流程
        返回: {content, reply_type, metadata}
        """
        # 1. 敏感词过滤（输入）
        has_sensitive, filtered_question = AIService.check_sensitive_word(db, store_id, question)
        if has_sensitive:
            reply = {
                "content": "您的问题中包含不当用语，请文明提问。",
                "reply_type": "sensitive",
                "metadata": {"original": question, "filtered": filtered_question}
            }
            if conversation_id:
                AIService.save_message(db, conversation_id, "customer", question, "sensitive")
                AIService.save_message(db, conversation_id, "bot", reply["content"], "sensitive")
                AIService.update_daily_stats(db, store_id, "default", customer_id)
            return reply

        # 2. 转人工检测
        transfer_msg = AIService.check_transfer_keyword(db, store_id, filtered_question)
        if transfer_msg:
            reply = {
                "content": transfer_msg,
                "reply_type": "transfer",
                "metadata": {"matched": "transfer_keyword"}
            }
            if conversation_id:
                AIService.save_message(db, conversation_id, "customer", filtered_question, "transfer")
                AIService.save_message(db, conversation_id, "bot", transfer_msg, "transfer")
                AIService.update_daily_stats(db, store_id, "transfer", customer_id)
            return reply

        # 3. 关键词回复
        keyword_reply = AIService.match_keyword_reply(db, store_id, filtered_question)
        if keyword_reply:
            reply = {
                "content": keyword_reply,
                "reply_type": "keyword",
                "metadata": {"matched_question": filtered_question}
            }
            if conversation_id:
                AIService.save_message(db, conversation_id, "customer", filtered_question, "keyword")
                AIService.save_message(db, conversation_id, "bot", keyword_reply, "keyword")
                AIService.update_daily_stats(db, store_id, "keyword", customer_id)
            return reply

        # 4. 知识库匹配 + AI生成
        matches = AIService.search_knowledge(db, store_id, filtered_question)
        knowledge_context = ""
        reply_type = "ai"
        matched_knowledge_id = None

        if matches:
            best_match, similarity = matches[0]
            if similarity >= 0.8:
                # 高匹配直接用知识库
                knowledge_item = matches[0][0]
                knowledge_item.hit_count += 1
                db.commit()
                reply = {
                    "content": knowledge_item.answer,
                    "reply_type": "knowledge",
                    "metadata": {"matched_question": knowledge_item.question, "similarity": similarity}
                }
                if conversation_id:
                    AIService.save_message(db, conversation_id, "customer", filtered_question, "knowledge")
                    AIService.save_message(db, conversation_id, "bot", knowledge_item.answer, "knowledge")
                    AIService.update_daily_stats(db, store_id, "knowledge", customer_id)
                return reply
            
            # 有匹配但不够高，用知识库上下文辅助AI
            knowledge_context = "\n".join([
                f"问题：{item.question}\n回答：{item.answer}"
                for item, s in matches[:5]
            ])

        # 5. 调用AI
        ai_reply = await AIService._call_doubao_api(filtered_question, knowledge_context)
        if not ai_reply:
            ai_reply = "抱歉，系统暂时繁忙，请稍后再试。"
            reply_type = "default"
        
        reply = {
            "content": ai_reply,
            "reply_type": reply_type,
            "metadata": {"has_knowledge_context": bool(knowledge_context)}
        }
        
        if conversation_id:
            AIService.save_message(db, conversation_id, "customer", filtered_question, reply_type)
            AIService.save_message(db, conversation_id, "bot", ai_reply, reply_type)
            AIService.update_daily_stats(db, store_id, reply_type, customer_id)
        
        return reply

    @staticmethod
    async def _call_doubao_api(question: str, knowledge_context: str = "", 
                               conversation_history: str = "") -> Optional[str]:
        system_prompt = """你是一个专业的电商客服助手。请根据以下要求回复：

1. 如果有提供知识库内容，优先参考知识库进行回复
2. 回答要专业、友好、简洁
3. 如果是商品咨询，尽量详细说明商品信息
4. 如果是售后问题，给予合理的解决方案建议
5. 如果无法回答，诚实说明并建议联系人工客服
6. 回答控制在200字以内
7. 只输出回复内容，不要输出其他内容"""

        user_content = question
        if knowledge_context:
            user_content = f"【知识库参考】：\n{knowledge_context}\n\n【用户问题】：{question}"
        if conversation_history:
            user_content = f"【对话历史】：\n{conversation_history}\n\n{user_content}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{DOUBAO_ENDPOINT}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {DOUBAO_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": DOUBAO_MODEL_ID,
                        "messages": messages,
                        "max_tokens": 500,
                        "temperature": 0.7
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                else:
                    print(f"豆包API错误: {response.status_code}")
                    return None
        except Exception as e:
            print(f"调用豆包API异常: {str(e)}")
            return None
