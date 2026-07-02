"""
认证相关API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["认证"])

# OAuth2密码模式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user_dependency(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的依赖项
    
    用于需要登录才能访问的接口
    """
    user = AuthService.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


@router.post("/register", response_model=TokenResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    商家注册接口
    
    - username: 用户名（唯一）
    - password: 密码
    - email: 邮箱（唯一）
    """
    success, message, user = AuthService.register_user(
        db, user_data.username, user_data.password, user_data.email
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    
    # 生成token
    access_token = AuthService.create_access_token(user.id, user.username)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    登录接口
    
    - username: 用户名
    - password: 密码
    
    返回JWT token
    """
    success, message, data = AuthService.login_user(db, login_data.username, login_data.password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return TokenResponse(
        access_token=data["access_token"],
        user=UserResponse.model_validate(data["user"])
    )


@router.get("/me", response_model=UserResponse)
def get_current_user(current_user = Depends(get_current_user_dependency)):
    """
    获取当前登录用户信息
    
    需要携带有效的JWT token
    """
    return UserResponse.model_validate(current_user)
