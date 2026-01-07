from fastapi import APIRouter, HTTPException, Path, Query
from app.daily_emotion.daily_emotion_service import DailyEmotionService
from app.daily_emotion.daily_emotion_model import DailyEmotion

# 라우터 생성
router = APIRouter(prefix="/api/daily-emotion", tags=["daily-emotion"])

# 서비스 인스턴스 생성
daily_emotion_service = DailyEmotionService()


@router.get("/")
async def root():
    """일기 감정 서비스 루트 엔드포인트"""
    return {
        "service": "Daily Emotion ML Service",
        "message": "일기 감정 데이터 서비스 API",
        "status": "running"
    }


@router.get("/emotions/top10")
async def get_top_10_emotions():
    """상위 10개의 일기 정보 조회"""
    try:
        emotions = daily_emotion_service.get_top_emotions(limit=10)
        return {
            "count": len(emotions),
            "emotions": [emotion.dict() for emotion in emotions]
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "일기 정보 조회 실패"
        }


@router.get(
    "/emotions/id/{emotion_id}",
    response_model=DailyEmotion,
    summary="일기 ID로 검색",
    description="일기 ID를 입력하여 해당 일기의 상세 정보를 조회합니다.",
    responses={
        200: {
            "description": "일기 정보 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "localdate": "1594-10-30",
                        "title": "<임진>",
                        "content": "맑고 따뜻하다.",
                        "userId": 1,
                        "emotion": 1
                    }
                }
            }
        },
        404: {
            "description": "일기를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "일기 ID 999를 찾을 수 없습니다."
                    }
                }
            }
        },
        500: {
            "description": "서버 오류",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "일기 정보 조회 실패: ..."
                    }
                }
            }
        }
    }
)
async def get_emotion_by_id(
    emotion_id: int = Path(
        ...,
        description="조회할 일기의 ID",
        example=1,
        ge=1
    )
):
    """
    일기 ID로 일기 정보 조회
    
    - **emotion_id**: 조회할 일기의 ID
    - 반환값: 일기의 상세 정보 (DailyEmotion 모델)
    """
    try:
        emotion = daily_emotion_service.get_emotion_by_id(emotion_id)
        if emotion is None:
            raise HTTPException(
                status_code=404,
                detail=f"일기 ID {emotion_id}를 찾을 수 없습니다."
            )
        return emotion
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 정보 조회 실패: {str(e)}"
        )


@router.get("/emotions/user/{user_id}")
async def get_emotions_by_user_id(
    user_id: int = Path(..., description="사용자 ID", example=1, ge=1)
):
    """사용자 ID로 일기 목록 조회"""
    try:
        emotions = daily_emotion_service.get_emotions_by_user_id(user_id)
        return {
            "count": len(emotions),
            "userId": user_id,
            "emotions": [emotion.dict() for emotion in emotions]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"사용자별 일기 조회 실패: {str(e)}"
        )


@router.get("/emotions/label/{emotion_label}")
async def get_emotions_by_label(
    emotion_label: int = Path(
        ..., 
        description="감정 라벨 (0: 중립, 1: 긍정, 2: 부정)", 
        example=1, 
        ge=0,
        le=2
    )
):
    """
    감정 라벨로 일기 목록 조회
    
    - **emotion_label**: 감정 라벨
        - 0: 중립 (Neutral)
        - 1: 긍정 (Positive)
        - 2: 부정 (Negative)
    """
    try:
        emotions = daily_emotion_service.get_emotions_by_emotion_label(emotion_label)
        # 라벨 이름 매핑
        label_names = {0: "중립", 1: "긍정", 2: "부정"}
        return {
            "count": len(emotions),
            "emotionLabel": emotion_label,
            "emotionLabelName": label_names.get(emotion_label, "Unknown"),
            "emotions": [emotion.dict() for emotion in emotions]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"감정별 일기 조회 실패: {str(e)}"
        )


@router.get("/emotions/label-distribution")
async def get_label_distribution():
    """
    라벨링 분포 통계 조회
    
    각 감정 라벨(0: 중립, 1: 긍정, 2: 부정)의 개수와 전체 대비 비율(%)을 반환합니다.
    """
    try:
        distribution = daily_emotion_service.get_label_distribution()
        return distribution
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"라벨 분포 조회 실패: {str(e)}"
        )


@router.post("/train")
async def train_model():
    """
    ML 모델 학습 실행
    
    일기 감정 분류 모델을 학습합니다.
    """
    try:
        accuracy = daily_emotion_service.train_model()
        return {
            "status": "success",
            "message": "모델 학습이 완료되었습니다.",
            "accuracy": accuracy
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"모델 학습 실패: {str(e)}"
        )


@router.post("/evaluate")
async def evaluate_model():
    """
    ML 모델 평가 실행
    
    학습된 모델의 상세 평가 메트릭을 계산합니다.
    """
    try:
        evaluation = daily_emotion_service.evaluate_model()
        return {
            "status": "success",
            "message": "모델 평가가 완료되었습니다.",
            "evaluation": evaluation
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"모델 평가 실패: {str(e)}"
        )


@router.get("/accuracy")
async def get_model_accuracy():
    """
    학습된 모델의 정확도 조회
    
    모델이 학습된 경우 정확도를 반환하고, 학습되지 않은 경우 안내 메시지를 반환합니다.
    """
    try:
        result = daily_emotion_service.get_model_accuracy()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"정확도 조회 실패: {str(e)}"
        )

