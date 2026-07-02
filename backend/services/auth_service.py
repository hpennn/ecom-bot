"""
认证服务
包含密码哈希、JWT token生成和验证
"""

from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
from sqlalchemy.orm import Session

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from models.user import User
from database import get_db


class AuthService:
    """认证服务类"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        对密码进行哈希加密
        
        Args:
            password: 明文密码
            
        Returns:
            加密后的密码哈希
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            password_hash: 加密后的密码哈希
            
        Returns:
            是否匹配
        """
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    @staticmethod
    def create_access_token(user_id: int, username: str) -> str:
        """
        创建JWT访问令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            
        Returns:
            JWT token字符串
        """
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "username": username,
            "exp": expire
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        验证JWT token
        
        Args:
            token: JWT token字符串
            
        Returns:
            解码后的payload，失败返回None
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # token已过期
        except jwt.InvalidTokenError:
            return None  # token无效

    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """
        获取当前用户
        
        Args:
            db: 数据库会话
            token: JWT token
            
        Returns:
            用户对象，未找到返回None
        """
        payload = AuthService.verify_token(token)
        if not payload:
            return None
        
        user_id = int(payload.get("sub"))
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def register_user(db: Session, username: str, password: str, email: str) -> tuple[bool, str, Optional[User]]:
        """
        注册新用户
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            email: 邮箱
            
        Returns:
            (是否成功, 消息, 用户对象)
        """
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return False, "用户名已存在", None
        
        # 检查邮箱是否已存在
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            return False, "邮箱已被注册", None
        
        # 创建用户
        password_hash = AuthService.hash_password(password)
        user = User(
            username=username,
            password_hash=password_hash,
            email=email
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return True, "注册成功", user

    @staticmethod
    def login_user(db: Session, username: str, password: str) -> tuple[bool, str, Optional[dict]]:
        """
        用户登录
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            (是否成功, 消息, token信息)
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False, "用户名或密码错误", None
        
        if not AuthService.verify_password(password, user.password_hash):
            return False, "用户名或密码错误", None
        
        # 生成token
        access_token = AuthService.create_access_token(user.id, user.username)
        
        return True, "登录成功", {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
