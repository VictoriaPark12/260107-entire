from multiprocessing.process import parent_process
import pandas as pd
import os
from pydantic import BaseModel, Field
from typing import Optional
import sys
from pathlib import Path

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from common.utils import setup_logging
    logger = setup_logging("titanic_model")
except ImportError:
    import logging
    logger = logging.getLogger("titanic_model")


class TitanicModels:
    def __init__(self) -> None:
       pass


class Passenger(BaseModel):
    """타이타닉 승객 정보 모델"""
    PassengerId: int = Field(..., description="승객 ID")
    Pclass: int = Field(..., ge=1, le=3, description="승객 등급 (1, 2, 3)")
    Name: str = Field(..., description="승객 이름")
    Sex: str = Field(..., description="성별 (male, female)")
    Age: Optional[float] = Field(None, ge=0, le=120, description="나이")
    SibSp: int = Field(0, ge=0, description="형제/배우자 수")
    Parch: int = Field(0, ge=0, description="부모/자녀 수")
    Ticket: str = Field(..., description="티켓 번호")
    Fare: Optional[float] = Field(None, ge=0, description="요금")
    Cabin: Optional[str] = Field(None, description="객실 번호")
    Embarked: Optional[str] = Field(None, description="탑승 항구 (C, Q, S)")
    
    class Config:
        # JSON 직렬화 시 타입 보존 (Pydantic이 자동으로 처리하지만 명시적으로 설정)
        json_encoders = {
            int: int,  # 정수는 정수로 보장
            float: float  # 실수는 실수로 보장
        }
        json_schema_extra = {
            "example": {
                "PassengerId": 1,
                "Pclass": 3,
                "Name": "Braund, Mr. Owen Harris",
                "Sex": "male",
                "Age": 22.0,
                "SibSp": 1,
                "Parch": 0,
                "Ticket": "A/5 21171",
                "Fare": 7.25,
                "Cabin": None,
                "Embarked": "S"
            }
        }