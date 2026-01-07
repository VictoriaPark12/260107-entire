"""
Titanic Service - FastAPI 애플리케이션
"""
import sys
from pathlib import Path
from fastapi import FastAPI

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.titanic.config import TitanicServiceConfig
from app.titanic.titanic_router import router as titanic_router
from app.daily_emotion.router import router as daily_emotion_router
from app.seoul_crime.save.seoul_router import router as seoul_crime_router
from app.nlp.nlp_router import router as nlp_router
from app.nlp.korean.korean_router import router as korean_nlp_router
from app.nlp.samsung.samsung_router import router as samsung_router
from app.us_unemployment.router import router as us_unemployment_router
from app.seoul_map.router import router as seoul_map_router
from common.middleware import LoggingMiddleware
from common.utils import setup_logging

# 설정 로드
config = TitanicServiceConfig()

# 로깅 설정
logger = setup_logging(config.service_name)

# FastAPI 앱 생성
app = FastAPI(
    title="ML Service API",
    description="머신러닝 서비스 API 문서 (Titanic, Daily Emotion, Seoul Crime, NLP 등)",
    version=config.service_version,
    docs_url="/docs",  # Swagger UI 접근 경로
    redoc_url="/redoc",  # ReDoc 접근 경로
    openapi_url="/openapi.json"  # OpenAPI 스키마 접근 경로
)

# CORS 설정 제거 - Gateway를 통해 접근하므로 Gateway에서만 CORS 처리
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# 미들웨어 추가
app.add_middleware(LoggingMiddleware)

# 라우터 등록
app.include_router(titanic_router)
app.include_router(daily_emotion_router)
app.include_router(seoul_crime_router)
app.include_router(nlp_router)
app.include_router(korean_nlp_router)
app.include_router(samsung_router)
app.include_router(us_unemployment_router)
app.include_router(seoul_map_router)


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
    