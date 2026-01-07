#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KoELECTRA 감성 분석 API 라우터
FastAPI 엔드포인트 정의
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
import logging

from app.koelectra.koelectra_service import get_service

logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/api/v1/sentiment",
    tags=["sentiment"]
)


# 요청 모델
class SentimentRequest(BaseModel):
    """감성 분석 요청 모델"""
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="분석할 텍스트",
        examples=["이 영화 정말 재미있어요!"]
    )
    return_probabilities: bool = Field(
        default=False,
        description="각 감성별 확률값 반환 여부"
    )


# 응답 모델
class SentimentResponse(BaseModel):
    """감성 분석 응답 모델"""
    status: str = Field(default="success", description="응답 상태")
    data: Dict = Field(..., description="분석 결과")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="응답 시각"
    )


@router.post(
    "/analyze",
    response_model=SentimentResponse,
    summary="감성 분석",
    description="입력된 텍스트의 감성을 분석합니다 (긍정/부정)",
    responses={
        200: {"description": "분석 성공"},
        400: {"description": "잘못된 요청"},
        500: {"description": "서버 오류"}
    }
)
async def analyze_sentiment(request: SentimentRequest):
    """
    텍스트 감성 분석
    
    - **text**: 분석할 텍스트
    - **return_probabilities**: 각 감성별 확률값 반환 여부
    
    **예시:**
    ```json
    {
        "text": "이 영화 정말 재미있어요!",
        "return_probabilities": true
    }
    ```
    
    **응답:**
    ```json
    {
        "status": "success",
        "data": {
            "text": "이 영화 정말 재미있어요!",
            "sentiment": "긍정",
            "score": 0.9234,
            "label_id": 1,
            "probabilities": {
                "부정": 0.0766,
                "긍정": 0.9234
            },
            "processing_time_ms": 45.2
        },
        "timestamp": "2024-12-15T10:30:00Z"
    }
    ```
    """
    try:
        # 서비스 인스턴스 가져오기
        service = get_service(device="cpu", max_length=512)
        
        # 감성 분석 실행
        result = service.predict(
            text=request.text,
            return_probabilities=request.return_probabilities
        )
        
        return SentimentResponse(
            status="success",
            data=result,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"감성 분석 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"감성 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/health",
    summary="헬스 체크",
    description="서비스 상태를 확인합니다"
)
async def health_check():
    """
    서비스 헬스 체크
    
    모델 로드 상태를 확인합니다.
    """
    try:
        service = get_service()
        return {
            "status": "healthy",
            "model_loaded": service.model is not None,
            "tokenizer_loaded": service.tokenizer is not None,
            "device": service.device,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"헬스 체크 오류: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }


@router.get(
    "/model-info",
    summary="모델 정보",
    description="로드된 모델의 정보를 반환합니다"
)
async def get_model_info():
    """
    모델 정보 조회
    """
    try:
        service = get_service()
        return {
            "model_path": str(service.model_path),
            "device": service.device,
            "max_length": service.max_length,
            "model_loaded": service.model is not None,
            "tokenizer_loaded": service.tokenizer is not None,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"모델 정보 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"모델 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

