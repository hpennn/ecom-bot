"""
AI智能回复服务
使用豆包API生成回复
"""

import re
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
import httpx

from config import DOUBAO_API_KEY, DOUBAO_ENDPOINT, DOUBAO_MODEL_ID, KNOWLEDGE_MATCH_THRESHOLD, MAX_KNOWLEDGE_CONTEXT
from models.knowledge import KnowledgeItem


class AIService:
    """AI回复服务类"""

    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """
        计算两个文本的相似度（简单实现）
        使用关键词重叠度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数 0-1
        """
        # 简单分词
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)

    @staticmethod
    def search_knowledge(db: Session, store_id: int, query: str, limit: int = 5) -> List[Tuple[KnowledgeItem, float]]:
        """
        在知识库中搜索匹配的问题
        
        Args:
            db: 数据库会话
            store_id: 店铺ID
            query: 用户查询
            limit: 返回数量限制
            
        Returns:
            匹配的知识库条目列表，按相似度排序
        """
        # 获取店铺所有启用的知识库条目
        items = db.query(KnowledgeItem).filter(
            KnowledgeItem.store_id == store_id,
            KnowledgeItem.is_active == 1
        ).order_by(KnowledgeItem.priority.desc()).all()
        
        matches = []
        query_lower = query.lower()
        query_keywords = set(re.findall(r'\w+', query_lower))
        
        for item in items:
            # 计算与问题的相似度
            similarity = AIService._calculate_similarity(query, item.question)
            
            # 检查关键词匹配
            keyword_match = False
            if item.keywords:
                item_keywords = set(re.findall(r'\w+', item.keywords.lower()))
                if query_keywords & item_keywords:  # 有交集
                    keyword_match = True
                    similarity = max(similarity, 0.6)  # 提升分数
            
            # 检查问题是否包含在查询中，或查询是否包含在问题中
            if query_lower in item.question.lower() or item.question.lower() in query_lower:
                similarity = max(similarity, 0.8)
            
            if similarity >= KNOWLEDGE_MATCH_THRESHOLD or keyword_match:
                matches.append((item, similarity))
        
        # 按相似度排序
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches[:limit]

    @staticmethod
    def increment_hit_count(db: Session, knowledge_id: int):
        """
        增加知识库条目命中次数
        
        Args:
            db: 数据库会话
            knowledge_id: 知识库条目ID
        """
        item = db.query(KnowledgeItem).filter(KnowledgeItem.id == knowledge_id).first()
        if item:
            item.hit_count += 1
            db.commit()

    @staticmethod
    async def generate_reply(db: Session, store_id: int, question: str, conversation_history: str = "") -> Tuple[str, Optional[int], str]:
        """
        生成AI回复
        
        Args:
            db: 数据库会话
            store_id: 店铺ID
            question: 用户问题
            conversation_history: 对话历史
            
        Returns:
            (回复内容, 匹配的知识库ID, 来源: knowledge/ai)
        """
        # 1. 先查知识库匹配
        matches = AIService.search_knowledge(db, store_id, question)
        
        if matches:
            best_match, similarity = matches[0]
            
            # 如果相似度很高，直接使用知识库答案
            if similarity >= 0.8:
                AIService.increment_hit_count(db, best_match.id)
                return best_match.answer, best_match.id, "knowledge"
            
            # 构建上下文，添加前几条作为参考
            knowledge_context = "\n".join([
                f"参考问答（相似度{s:.2f}）：\n问题：{item.question}\n回答：{item.answer}"
                for item, s in matches[:MAX_KNOWLEDGE_CONTEXT]
            ])
            
            # 调用AI生成回复，带上知识库上下文
            ai_reply = await AIService._call_doubao_api(question, knowledge_context, conversation_history)
            
            # 检查AI回复是否有效
            if ai_reply and len(ai_reply.strip()) > 0:
                return ai_reply, None, "ai"
        
        # 2. 没有匹配到，使用AI直接生成
        ai_reply = await AIService._call_doubao_api(question, "", conversation_history)
        return ai_reply if ai_reply else "抱歉，我暂时无法回答这个问题，请稍后再试。", None, "ai"

    @staticmethod
    async def _call_doubao_api(question: str, knowledge_context: str, conversation_history: str = "") -> Optional[str]:
        """
        调用豆包API生成回复
        
        Args:
            question: 用户问题
            knowledge_context: 知识库上下文
            conversation_history: 对话历史
            
        Returns:
            AI生成的回复
        """
        # 构建系统提示
        system_prompt = """你是一个专业的电商客服助手。请根据以下要求回复：

1. 如果有提供知识库内容，优先参考知识库进行回复
2. 回答要专业、友好、简洁
3. 如果是商品咨询，尽量详细说明商品信息
4. 如果是售后问题，给予合理的解决方案建议
5. 如果无法回答，诚实说明并建议联系人工客服
6. 回答控制在100字以内
7. 只输出回复内容，不要输出其他内容"""

        # 构建用户消息
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
                    print(f"豆包API错误: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"调用豆包API异常: {str(e)}")
            return None

    @staticmethod
    def format_knowledge_for_context(items: List[KnowledgeItem]) -> str:
        """
        将知识库条目格式化为上下文字符串
        
        Args:
            items: 知识库条目列表
            
        Returns:
            格式化后的上下文
        """
        if not items:
            return ""
        
        lines = ["以下是店铺知识库中的相关内容："]
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. 问题：{item.question}")
            lines.append(f"   回答：{item.answer}")
        
        return "\n".join(lines)
