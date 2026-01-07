from pydantic import BaseModel, Field
from typing import Optional


# Emotion 라벨 정의
# 0: 중립 (Neutral)
# 1: 긍정 (Positive)
# 2: 부정 (Negative)
EMOTION_LABELS = {
    0: "중립",
    1: "긍정",
    2: "부정"
}


class DailyEmotion(BaseModel):
    """일기 감정 정보 모델"""
    
    id: int = Field(..., description="일기 ID")
    localdate: str = Field(..., description="날짜")
    title: str = Field(..., description="제목")
    content: str = Field(..., description="내용")
    userId: int = Field(..., description="사용자 ID")
    emotion: int = Field(
        ..., 
        description="감정 라벨 (0: 중립, 1: 긍정, 2: 부정)",
        ge=0,
        le=2
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "localdate": "1594-10-30",
                "title": "<임진>",
                "content": "맑고 따뜻하다. 충청수사, 순천부사, 사도첨사가 와서 활을 쏘았다.",
                "userId": 1,
                "emotion": 1
            }
        }

