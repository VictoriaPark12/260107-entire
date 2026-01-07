"""
OAuth Provider 관련 DTO
"""
from pydantic import BaseModel
from typing import Optional


class KakaoTokenResponse(BaseModel):
    """카카오 토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    scope: Optional[str] = None
    refresh_token_expires_in: Optional[int] = None


class KakaoAccount(BaseModel):
    """카카오 계정 정보"""
    email: Optional[str] = None
    profile: Optional['KakaoProfile'] = None


class KakaoProfile(BaseModel):
    """카카오 프로필 정보"""
    nickname: Optional[str] = None
    profile_image_url: Optional[str] = None


class KakaoUserInfo(BaseModel):
    """카카오 사용자 정보"""
    id: int
    kakao_account: Optional[KakaoAccount] = None


class GoogleTokenResponse(BaseModel):
    """구글 토큰 응답"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None


class GoogleUserInfo(BaseModel):
    """구글 사용자 정보"""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    verified_email: Optional[bool] = None


class NaverTokenResponse(BaseModel):
    """네이버 토큰 응답"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    error: Optional[str] = None
    error_description: Optional[str] = None


class NaverUserInfo(BaseModel):
    """네이버 사용자 정보"""
    resultcode: str
    message: str
    response: Optional['NaverUserResponse'] = None


class NaverUserResponse(BaseModel):
    """네이버 사용자 응답"""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    nickname: Optional[str] = None
    profile_image: Optional[str] = None

