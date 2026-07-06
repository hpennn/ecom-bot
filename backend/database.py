"""
数据库连接和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite需要这个配置
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话的依赖项
    用于FastAPI的Depends注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    创建所有表
    """
    from models import user, store, knowledge, conversation, order
    Base.metadata.create_all(bind=engine)


def add_missing_columns():
    """
    为已存在的表添加新字段（数据库迁移）
    """
    import sqlite3
    db_path = DATABASE_URL.replace("sqlite:///", "")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查 users 表是否有 paid_type 字段
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        if "paid_type" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN paid_type VARCHAR(20) DEFAULT 'free'")
        if "paid_at" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN paid_at DATETIME")
        if "expires_at" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN expires_at DATETIME")
        if "is_admin" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")

        conn.commit()
        conn.close()
    except Exception:
        pass
