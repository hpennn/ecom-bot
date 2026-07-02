#!/usr/bin/env python3
"""
数据库初始化脚本
创建示例数据用于测试
"""

from database import SessionLocal, init_db
from models import User, Store, KnowledgeItem


def create_sample_data():
    """创建示例数据"""
    db = SessionLocal()
    
    try:
        # 检查是否已有数据
        if db.query(User).first():
            print("⚠️  数据库已存在数据，跳过示例数据创建")
            return
        
        # 创建测试用户
        from services.auth_service import AuthService
        user = User(
            username="demo",
            password_hash=AuthService.hash_password("demo123"),
            email="demo@example.com"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ 创建测试用户: demo / demo123")
        
        # 创建测试店铺
        store = Store(
            user_id=user.id,
            name="我的拼多多店铺",
            platform="pinduoduo",
            auto_reply_enabled=True
        )
        db.add(store)
        db.commit()
        db.refresh(store)
        print(f"✅ 创建测试店铺: {store.name}")
        
        # 创建示例知识库
        knowledge_items = [
            {
                "category": "faq",
                "question": "发货时间",
                "answer": "我们会在付款后24小时内发货，默认使用圆通快递，预计3-5天送达。如需发顺丰请备注或联系客服。",
                "keywords": "发货,快递,物流,几天到,什么时候发",
                "priority": 10
            },
            {
                "category": "faq",
                "question": "退换货政策",
                "answer": "本店支持7天无理由退换货（不影响二次销售）。质量问题包邮退换，尺寸问题可换码。退换货请联系客服获取退货地址。",
                "keywords": "退货,换货,退款,售后,退钱",
                "priority": 10
            },
            {
                "category": "faq",
                "question": "优惠活动",
                "answer": "店铺全场满99元包邮，关注店铺可领取5元新人券，联系客服还可获取专属优惠哦！",
                "keywords": "优惠,折扣,券,红包,满减,包邮",
                "priority": 8
            },
            {
                "category": "product",
                "question": "尺码选择",
                "answer": "我们的衣服尺码偏大，建议选择比平时小一码。如身高170体重130斤，建议选L码。具体可参考详情页尺码表或咨询客服。",
                "keywords": "尺码,大小,选码,尺寸",
                "priority": 9
            },
            {
                "category": "policy",
                "question": "支付方式",
                "answer": "支持微信支付、支付宝、花呗、信用卡等主流支付方式。暂不支持货到付款。",
                "keywords": "支付,付款,微信,支付宝,花呗",
                "priority": 5
            },
            {
                "category": "custom",
                "question": "你好",
                "answer": "您好！欢迎光临本店，有什么可以帮到您的吗？😊",
                "keywords": "你好,您好,在吗,hello,hi",
                "priority": 20
            }
        ]
        
        for item_data in knowledge_items:
            item = KnowledgeItem(store_id=store.id, **item_data)
            db.add(item)
        
        db.commit()
        print(f"✅ 创建 {len(knowledge_items)} 条知识库示例")
        
        print("\n📝 示例数据创建完成！")
        print("\n登录信息：")
        print("  用户名: demo")
        print("  密码: demo123")
        
    except Exception as e:
        print(f"❌ 创建示例数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 初始化数据库...")
    init_db()
    print("✅ 数据库表创建完成")
    
    print("\n📦 创建示例数据...")
    create_sample_data()
    
    print("\n✨ 完成！可以启动服务了：")
    print("   cd /app/data/所有对话/主对话/projects/ecom-bot/backend")
    print("   python main.py")
