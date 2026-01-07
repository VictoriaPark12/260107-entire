"""
Auth Service - FastAPI 애플리케이션
"""
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import (
    AuthServiceConfig,
    KakaoProperties,
    GoogleProperties,
    NaverProperties,
    JwtProperties,
    RedisConfig
)
from app.security.jwt_provider import JwtTokenProvider
from app.services.kakao_auth_service import KakaoAuthService
from app.services.google_auth_service import GoogleAuthService
from app.services.naver_auth_service import NaverAuthService
from app.controllers.kakao_auth_controller import create_kakao_router
from app.controllers.google_auth_controller import create_google_router
from app.controllers.naver_auth_controller import create_naver_router
from common.middleware import LoggingMiddleware
from common.utils import setup_logging

# 설정 로드
config = AuthServiceConfig()
kakao_properties = KakaoProperties()
google_properties = GoogleProperties()
naver_properties = NaverProperties()
jwt_properties = JwtProperties()
redis_config = RedisConfig()

# 로깅 설정
logger = setup_logging(config.service_name)

# JWT Token Provider
jwt_token_provider = JwtTokenProvider(jwt_properties)

# Auth Services
kakao_auth_service = KakaoAuthService(kakao_properties, redis_config)
google_auth_service = GoogleAuthService(google_properties)
naver_auth_service = NaverAuthService(naver_properties)

# FastAPI 앱 생성
app = FastAPI(
    title="Auth Service API",
    description="소셜 로그인 인증 서비스 API 문서",
    version=config.service_version
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 미들웨어 추가
app.add_middleware(LoggingMiddleware)

# 라우터 등록
app.include_router(create_kakao_router(kakao_properties, kakao_auth_service, jwt_token_provider))
app.include_router(create_google_router(google_properties, google_auth_service, jwt_token_provider))
app.include_router(create_naver_router(naver_properties, naver_auth_service, jwt_token_provider))


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": config.service_name,
        "version": config.service_version,
        "message": "Auth Service API"
    }


@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 실행"""
    logger.info(f"{config.service_name} v{config.service_version} started")


@app.on_event("shutdown")
async def shutdown_event():
    """서비스 종료 시 실행"""
    logger.info(f"{config.service_name} shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.port)

