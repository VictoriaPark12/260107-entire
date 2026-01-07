"""
Titanic Router - FastAPI 라우터
타이타닉 승객 관련 엔드포인트를 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import csv
from typing import List, Dict
from pydantic import BaseModel
import json
from app.titanic.titanic_model import Passenger

# 라우터 생성
router = APIRouter(
    prefix="/api/titanic",
    tags=["titanic"],
    responses={404: {"description": "Not found"}}
)

# CSV 파일 경로
TRAIN_CSV_PATH = Path(__file__).parent / "train.csv"
TEST_CSV_PATH = Path(__file__).parent / "test.csv"


def safe_int(value, default=0):
    """안전하게 문자열을 정수로 변환"""
    if value is None:
        return default
    value_str = str(value).strip()
    if not value_str:
        return default
    try:
        return int(value_str)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=None):
    """안전하게 문자열을 실수로 변환"""
    if value is None:
        return default
    value_str = str(value).strip()
    if not value_str:
        return default
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return default


def load_all_passengers(csv_path: Path) -> List[Passenger]:
    """CSV 파일에서 전체 승객 정보를 로드"""
    passengers = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 숫자 필드는 적절한 타입으로 변환하여 Passenger 모델 생성
                passenger_data = {
                    "PassengerId": safe_int(row.get("PassengerId"), 0),
                    "Pclass": safe_int(row.get("Pclass"), 0),
                    "Name": row.get("Name", "").strip() if row.get("Name") else "",
                    "Sex": row.get("Sex", "").strip() if row.get("Sex") else "",
                    "Age": safe_float(row.get("Age"), None),
                    "SibSp": safe_int(row.get("SibSp"), 0),
                    "Parch": safe_int(row.get("Parch"), 0),
                    "Ticket": row.get("Ticket", "").strip() if row.get("Ticket") else "",
                    "Fare": safe_float(row.get("Fare"), None),
                    "Cabin": row.get("Cabin", "").strip() if row.get("Cabin") else None,
                    "Embarked": row.get("Embarked", "").strip() if row.get("Embarked") else None
                }
                # Passenger 모델 인스턴스 생성 (타입 검증 및 자동 변환)
                passenger = Passenger(**passenger_data)
                passengers.append(passenger)
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"CSV 파일 읽기 오류: {e}")
        return []
    return passengers

@router.get("/")
async def root():
    """타이타닉 서비스 루트 엔드포인트"""
    return {
        "service": "Titanic ML Service",
        "message": "타이타닉 데이터 서비스 API",
        "status": "running"
    }


class PassengersResponse(BaseModel):
    """승객 목록 응답 모델"""
    count: int
    passengers: List[Passenger]
    
    class Config:
        json_schema_extra = {
            "example": {
                "count": 10,
                "passengers": [
                    {
                        "PassengerId": 892,
                        "Pclass": 3,
                        "Name": "Kelly, Mr. James",
                        "Sex": "male",
                        "Age": 34.5,
                        "SibSp": 0,
                        "Parch": 0,
                        "Ticket": "330911",
                        "Fare": 7.8292,
                        "Cabin": None,
                        "Embarked": "Q"
                    }
                ]
            }
        }


@router.get("/passengers/top10", response_model=PassengersResponse)
async def get_top_10_passengers():
    """상위 10명의 승객 정보 조회"""
    passengers = load_all_passengers(TEST_CSV_PATH)
    if not passengers:
        raise HTTPException(
            status_code=404,
            detail="승객 데이터를 찾을 수 없습니다."
        )
    return PassengersResponse(
        count=len(passengers[:10]),
        passengers=passengers[:10]
    )


@router.get("/passengers/id/{passenger_id}", response_model=Passenger)
async def get_passenger_by_id(passenger_id: int):
    """PassengerId로 승객 조회 (test.csv에서)"""
    try:
        with open(TEST_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if safe_int(row.get("PassengerId"), 0) == passenger_id:
                    # 숫자 필드는 적절한 타입으로 변환하여 Passenger 모델 생성
                    passenger_data = {
                        "PassengerId": safe_int(row.get("PassengerId"), 0),
                        "Pclass": safe_int(row.get("Pclass"), 0),
                        "Name": row.get("Name", "").strip() if row.get("Name") else "",
                        "Sex": row.get("Sex", "").strip() if row.get("Sex") else "",
                        "Age": safe_float(row.get("Age"), None),
                        "SibSp": safe_int(row.get("SibSp"), 0),
                        "Parch": safe_int(row.get("Parch"), 0),
                        "Ticket": row.get("Ticket", "").strip() if row.get("Ticket") else "",
                        "Fare": safe_float(row.get("Fare"), None),
                        "Cabin": row.get("Cabin", "").strip() if row.get("Cabin") else None,
                        "Embarked": row.get("Embarked", "").strip() if row.get("Embarked") else None
                    }
                    # Passenger 모델 인스턴스 생성 (타입 검증 및 자동 변환)
                    passenger = Passenger(**passenger_data)
                    return passenger
        raise HTTPException(status_code=404, detail=f"PassengerId {passenger_id}를 찾을 수 없습니다.")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="승객 데이터 파일을 찾을 수 없습니다.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"잘못된 데이터 형식: {str(e)}")


@router.post("/preprocess")
async def preprocess_data():
    """데이터 전처리 실행"""
    try:
        from app.titanic.titanic_service import TitanicService
        service = TitanicService()
        result = service.preprocess()
        return {
            "message": "전처리 완료",
            "data": result
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"CSV 파일을 찾을 수 없습니다: {str(e)}")
    except Exception as e:
        import traceback
        error_detail = f"전처리 중 오류 발생: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # 서버 로그에 출력
        raise HTTPException(status_code=500, detail=f"전처리 중 오류 발생: {str(e)}")

@router.post("/evaluate")
async def evaluate_model():
    """
    모델링 평가 실행
    후 모델 평가 결과 반환
    """
    try:
        from app.titanic.titanic_service import TitanicService
        service = TitanicService()
        
        # 전처리 -> 모델링 -> 학습 -> 평가 순서로 실행
        print("전처리 시작...")
        service.preprocess()
        print("전처리 완료")
        
        print("모델링 시작...")
        service.modeling()
        if not hasattr(service, 'models') or not service.models:
            raise ValueError("모델 생성에 실패했습니다. models 속성이 없습니다.")
        print(f"모델 생성 완료: {list(service.models.keys())}")
        
        print("학습 시작...")
        service.learning()
        print("학습 완료")
        
        print("평가 시작...")
        results = service.evaluate()
        print(f"평가 완료: {results}")
        
        # 결과를 퍼센티지로 변환
        results_percent = {k: v * 100 for k, v in results.items()}
        
        return {
            "message": "모델 평가 완료",
            "results": results_percent
        }
    except Exception as e:
        import traceback
        error_detail = f"평가 중 오류 발생: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # 서버 로그에 출력
        raise HTTPException(status_code=500, detail=f"평가 중 오류 발생: {str(e)}")


@router.post("/submit")
async def submit_model():
    """
    Kaggle 제출용 모델 생성 및 저장
    """
    try:
        from app.titanic.titanic_service import TitanicService
        service = TitanicService()
        
        # 전처리 -> 모델링 -> 제출 순서로 실행
        print("전처리 시작...")
        service.preprocess()
        print("전처리 완료")
        
        print("모델링 시작...")
        service.modeling()
        print("모델링 완료")
        
        print("제출용 모델 생성 시작...")
        result = service.submit()
        print(f"제출용 모델 생성 완료: {result}")
        
        return {
            "message": "Kaggle 제출용 모델 생성 완료",
            "result": result,
            "download_url": "/api/titanic/download/submission"
        }
    except Exception as e:
        import traceback
        error_detail = f"제출용 모델 생성 중 오류 발생: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # 서버 로그에 출력
        raise HTTPException(status_code=500, detail=f"제출용 모델 생성 중 오류 발생: {str(e)}")


@router.get("/download/submission")
async def download_submission():
    """
    Kaggle 제출용 submission.csv 파일 다운로드
    """
    submission_path = Path(__file__).parent / 'submission.csv'
    
    if not submission_path.exists():
        raise HTTPException(
            status_code=404,
            detail="submission.csv 파일이 없습니다. 먼저 /api/titanic/submit 엔드포인트를 실행하세요."
        )
    
    return FileResponse(
        path=str(submission_path),
        filename="submission.csv",
        media_type="text/csv"
    )


@router.get("/download/model")
async def download_kaggle_model():
    """
    Kaggle 제출용 랜덤포레스트 모델 파일 다운로드
    """
    model_path = Path(__file__).parent / 'models' / 'RandomForest_kaggle_model.pkl'
    
    if not model_path.exists():
        raise HTTPException(
            status_code=404,
            detail="RandomForest_kaggle_model.pkl 파일이 없습니다. 먼저 /api/titanic/submit 엔드포인트를 실행하세요."
        )
    
    return FileResponse(
        path=str(model_path),
        filename="RandomForest_kaggle_model.pkl",
        media_type="application/octet-stream"
    )
