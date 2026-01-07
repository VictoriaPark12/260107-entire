#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KoELECTRA 감성 분석 API 서버
FastAPI 애플리케이션 진입점
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.koelectra import router as koelectra_router

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="KoELECTRA 감성 분석 API",
    version="1.0.0",
    description="""
    # KoELECTRA 감성 분석 API
    
    한국어 텍스트를 분석하여 긍정/부정 감성을 판단합니다.
    
    ## 주요 기능
    - 🎬 텍스트 감성 분석 (긍정/부정)
    - 📊 신뢰도 점수 제공
    - 🚀 빠른 추론 속도
    
    ## 모델 정보
    - **모델**: KoELECTRA (로컬 모델)
    - **언어**: 한국어
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(koelectra_router)


@app.get("/", tags=["root"])
async def root():
    """
    루트 엔드포인트
    API 정보 반환
    """
    return {
        "service": "KoELECTRA 감성 분석 API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/ping", tags=["health"])
async def ping():
    """
    간단한 ping 엔드포인트
    """
    return {"status": "pong"}


# 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    전역 예외 처리
    """
    logger.error(f"예상치 못한 오류: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal Server Error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("="*80)
    logger.info("KoELECTRA 감성 분석 서비스 시작")
    logger.info("="*80)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9007,
        reload=False,
        log_level="info"
    )

