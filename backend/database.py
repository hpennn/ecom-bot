"""
数据库连接和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models import user, store, knowledge, conversation, order, keyword_reply
    Base.metadata.create_all(bind=engine)


def add_missing_columns():
    import sqlite3
    db_path = DATABASE_URL.replace("sqlite:///", "")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # users 表迁移
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        for col, default in [("paid_type", "'free'"), ("paid_at", None), 
                              ("expires_at", None), ("is_admin", "0")]:
            if col not in columns:
                d = f"DEFAULT {default}" if default else ""
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} VARCHAR(50) {d}")

        # 创建新表
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS keyword_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            keywords TEXT NOT NULL,
            reply TEXT NOT NULL,
            match_type VARCHAR(20) DEFAULT 'contains',
            is_active BOOLEAN DEFAULT 1,
            priority INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS transfer_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            keywords TEXT NOT NULL,
            reply_message VARCHAR(500) DEFAULT '正在为您转接人工客服，请稍候...',
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sensitive_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            word VARCHAR(100) NOT NULL,
            replacement VARCHAR(100) DEFAULT '***',
            is_global BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            reply_type VARCHAR(20),
            metadata_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            date VARCHAR(10) NOT NULL,
            total_messages INTEGER DEFAULT 0,
            keyword_replies INTEGER DEFAULT 0,
            knowledge_replies INTEGER DEFAULT 0,
            ai_replies INTEGER DEFAULT 0,
            transfer_replies INTEGER DEFAULT 0,
            default_replies INTEGER DEFAULT 0,
            unique_customers INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_keyword_replies_store ON keyword_replies(store_id);
        CREATE INDEX IF NOT EXISTS idx_transfer_keywords_store ON transfer_keywords(store_id);
        CREATE INDEX IF NOT EXISTS idx_sensitive_words_store ON sensitive_words(store_id);
        CREATE INDEX IF NOT EXISTS idx_conv_messages_conv ON conversation_messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_daily_stats_store_date ON daily_stats(store_id, date);
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")
