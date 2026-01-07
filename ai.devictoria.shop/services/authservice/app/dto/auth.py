"""
인증 관련 DTO
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class KakaoLoginRequest(BaseModel):
    """카카오 로그인 요청"""
    authorization_code: Optional[str] = None
    access_token: Optional[str] = None
    email: Optional[str] = None
    nickname: Optional[str] = None


class GoogleLoginRequest(BaseModel):
    """구글 로그인 요청"""
    authorization_code: Optional[str] = None
    access_token: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None


class NaverLoginRequest(BaseModel):
    """네이버 로그인 요청"""
    authorization_code: Optional[str] = None
    access_token: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    state: Optional[str] = None


class LoginResponse(BaseModel):
    """로그인 응답"""
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    token: Optional[str] = None
    refresh_token: Optional[str] = None

