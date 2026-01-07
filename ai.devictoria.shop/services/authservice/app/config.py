"""
Auth Service 설정
"""
from pydantic_settings import BaseSettings


class KakaoProperties(BaseSettings):
    """카카오 OAuth 설정"""
    rest_api_key: str
    admin_key: str = ""
    redirect_uri: str
    frontend_url: str = "http://localhost:3000"
    token_uri: str = "https://kauth.kakao.com/oauth/token"
    user_info_uri: str = "https://kapi.kakao.com/v2/user/me"
    
    class Config:
        env_prefix = "KAKAO_"
        case_sensitive = False


class GoogleProperties(BaseSettings):
    """구글 OAuth 설정"""
    client_id: str
    client_secret: str
    redirect_uri: str
    frontend_url: str = "http://localhost:3000"
    token_uri: str = "https://oauth2.googleapis.com/token"
    user_info_uri: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    class Config:
        env_prefix = "GOOGLE_"
        case_sensitive = False


class NaverProperties(BaseSettings):
    """네이버 OAuth 설정"""
    client_id: str
    client_secret: str
    redirect_uri: str
    frontend_url: str = "http://localhost:3000"
    token_uri: str = "https://nid.naver.com/oauth2.0/token"
    user_info_uri: str = "https://openapi.naver.com/v1/nid/me"
    
    class Config:
        env_prefix = "NAVER_"
        case_sensitive = False


class JwtProperties(BaseSettings):
    """JWT 설정"""
    secret: str
    access_token_expiration: int = 3600000  # 1시간 (밀리초)
    refresh_token_expiration: int = 2592000000  # 30일 (밀리초)
    
    class Config:
        env_prefix = "JWT_"
        case_sensitive = False


class RedisConfig(BaseSettings):
    """Redis 설정"""
    host: str = "more-moose-17049.upstash.io"
    port: int = 6379
    password: str = ""
    username: str = "default"
    use_ssl: bool = True
    timeout: int = 2000
    
    class Config:
        env_prefix = "REDIS_"
        case_sensitive = False


class AuthServiceConfig(BaseSettings):
    """Auth Service 설정"""
    service_name: str = "Auth Service"
    service_version: str = "1.0.0"
    port: int = 8080
    
    class Config:
        env_file = ".env"
        case_sensitive = False

