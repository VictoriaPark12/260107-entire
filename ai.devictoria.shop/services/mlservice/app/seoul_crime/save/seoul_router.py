"""
Seoul Crime Router - FastAPI 라우터
서울 범죄 데이터 관련 엔드포인트를 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.seoul_crime.save.seoul_data import SeoulCrimeData
from app.seoul_crime.save.seoul_method import SeoulCrimeMethod
from app.seoul_crime.save.seoul_service import SeoulCrimeService

# 라우터 생성
router = APIRouter(
    prefix="/seoul-crime",
    tags=["seoul-crime"],
    responses={404: {"description": "Not found"}}
)

# 서비스 인스턴스
_seoul_crime_data: Optional[SeoulCrimeData] = None
_seoul_crime_method: Optional[SeoulCrimeMethod] = None
_seoul_crime_service: Optional[SeoulCrimeService] = None


@router.post("/preprocess")
async def preprocess():
    """데이터 전처리 및 머지 실행 (포스트맨용 형식으로 반환)"""
    try:
        service = get_seoul_crime_service()
        result = service.preprocess_to_dict()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"전처리 중 오류 발생: {str(e)}")


@router.get("/police-coords")
async def get_police_coordinates():
    """경찰서 주소 및 위도/경도 조회 (전체)"""
    try:
        from app.seoul_crime.save.get_police_coords import get_police_station_coordinates
        result_df = get_police_station_coordinates()
        
        # DataFrame을 딕셔너리 리스트로 변환
        result = result_df.to_dict(orient='records')
        
        return {
            "status": "success",
            "count": len(result),
            "police_stations": result,
            "summary": {
                "total": len(result),
                "success": len([r for r in result if '[OK]' in r.get('상태', '')]),
                "failed": len([r for r in result if '[FAIL]' in r.get('상태', '') or '[ERROR]' in r.get('상태', '')])
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"경찰서 좌표 조회 중 오류 발생: {str(e)}")


def get_seoul_crime_data() -> SeoulCrimeData:
    """서비스 인스턴스 싱글톤 패턴"""
    global _seoul_crime_data
    if _seoul_crime_data is None:
        _seoul_crime_data = SeoulCrimeData()
    return _seoul_crime_data


def get_seoul_crime_method() -> SeoulCrimeMethod:
    """메서드 인스턴스 싱글톤 패턴"""
    global _seoul_crime_method
    if _seoul_crime_method is None:
        _seoul_crime_method = SeoulCrimeMethod()
    return _seoul_crime_method


def get_seoul_crime_service() -> SeoulCrimeService:
    """서비스 인스턴스 싱글톤 패턴"""
    global _seoul_crime_service
    if _seoul_crime_service is None:
        _seoul_crime_service = SeoulCrimeService()
    return _seoul_crime_service


@router.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Seoul Crime Data Service",
        "description": "서울시 범죄, CCTV, 인구 데이터 조회 서비스",
        "endpoints": {
            "cctv": "/seoul-crime/cctv - CCTV 데이터 5개 조회",
            "crime": "/seoul-crime/crime - 범죄 데이터 5개 조회",
            "pop": "/seoul-crime/pop - 인구 데이터 5개 조회",
            "preprocess": "/seoul-crime/preprocess - 데이터 전처리 실행"
        }
    }


@router.get("/cctv")
async def get_cctv(limit: int = 5):
    """CCTV 데이터 조회 (기본 5개)"""
    try:
        data = get_seoul_crime_data()
        
        if data.cctv is None:
            raise HTTPException(
                status_code=404,
                detail="CCTV 데이터를 찾을 수 없습니다."
            )
        
        # DataFrame을 딕셔너리 리스트로 변환
        df = data.cctv.head(limit)
        result = df.to_dict(orient='records')
        
        return {
            "count": len(result),
            "limit": limit,
            "total_rows": len(data.cctv),
            "cctv_data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CCTV 데이터 조회 중 오류 발생: {str(e)}")


@router.get("/crime")
async def get_crime(limit: int = 5):
    """범죄 데이터 조회 (기본 5개)"""
    try:
        data = get_seoul_crime_data()
        
        if data.crime is None:
            raise HTTPException(
                status_code=404,
                detail="범죄 데이터를 찾을 수 없습니다."
            )
        
        # DataFrame을 딕셔너리 리스트로 변환
        df = data.crime.head(limit)
        result = df.to_dict(orient='records')
        
        return {
            "count": len(result),
            "limit": limit,
            "total_rows": len(data.crime),
            "crime_data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"범죄 데이터 조회 중 오류 발생: {str(e)}")


@router.get("/pop")
async def get_pop(limit: int = 5):
    """인구 데이터 조회 (기본 5개)"""
    try:
        data = get_seoul_crime_data()
        
        if data.pop is None:
            raise HTTPException(
                status_code=404,
                detail="인구 데이터를 찾을 수 없습니다."
            )
        
        # DataFrame을 딕셔너리 리스트로 변환
        df = data.pop.head(limit)
        result = df.to_dict(orient='records')
        
        return {
            "count": len(result),
            "limit": limit,
            "total_rows": len(data.pop),
            "pop_data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"인구 데이터 조회 중 오류 발생: {str(e)}")


@router.get("/features")
async def get_feature_changes():
    """전처리 과정에서 수정된 피처(컬럼) 정보만 반환"""
    try:
        from pathlib import Path
        import pandas as pd
        
        # 원본 데이터 먼저 로드 (비교용)
        data = get_seoul_crime_data()
        data_dir = Path(data.dname)
        
        # 원본 CSV 파일 직접 읽기
        original_cctv = pd.read_csv(data_dir / "cctv.csv", encoding='utf-8') if (data_dir / "cctv.csv").exists() else None
        original_crime = pd.read_csv(data_dir / "crime.csv", encoding='utf-8') if (data_dir / "crime.csv").exists() else None
        original_pop = pd.read_csv(data_dir / "pop.csv", encoding='utf-8') if (data_dir / "pop.csv").exists() else None
        
        # 전처리 실행하여 수정된 데이터 확인
        service = get_seoul_crime_service()
        cctv_df, crime_df, pop_df, merged_df = service.preprocess()
        
        feature_changes = {
            "message": "전처리 과정에서 수정된 피처 정보",
            "preprocessing_steps": {
                "pop_data": {
                    "original_columns": list(original_pop.columns) if original_pop is not None else [],
                    "original_rows": len(original_pop) if original_pop is not None else 0,
                    "modified_columns": list(pop_df.columns),
                    "modified_rows": len(pop_df),
                    "changes": [
                        "자치구(인덱스 1)와 4번째 컬럼(인덱스 3)만 선택 → '자치구', '인구'로 컬럼명 변경",
                        "인덱스 1, 2, 3 행 제거",
                        "빈 행 및 '합계' 행 제거"
                    ]
                },
                "cctv_data": {
                    "original_columns": list(original_cctv.columns) if original_cctv is not None else [],
                    "modified_columns": list(cctv_df.columns),
                    "changes": [
                        "'기관명' 컬럼에서 따옴표 제거 및 공백 제거"
                    ]
                },
                "crime_data": {
                    "original_columns": list(original_crime.columns) if original_crime is not None else [],
                    "original_rows": len(original_crime) if original_crime is not None else 0,
                    "modified_columns": list(crime_df.columns),
                    "modified_rows": len(crime_df),
                    "aggregated_rows": len(crime_df.groupby('구').size()) if '구' in crime_df.columns else 0,
                    "changes": [
                        "경찰서별 데이터 → 자치구별 집계 (groupby)",
                        "숫자 문자열에서 콤마 및 따옴표 제거 후 숫자 변환"
                    ]
                },
                "merged_data": {
                    "final_columns": list(merged_df.columns),
                    "final_rows": len(merged_df),
                    "column_changes": [
                        "'기관명' → '자치구'로 컬럼명 변경",
                        "'구' 컬럼 제거 (자치구와 동일한 값)"
                    ],
                    "merge_info": {
                        "step1": "CCTV + 인구 머지 (기관명 = 자치구)",
                        "step2": "CCTV-인구 머지 결과 + 범죄 데이터 머지 (자치구 = 구)"
                    }
                }
            },
            "summary": {
                "original_total_columns": {
                    "cctv": len(original_cctv.columns) if original_cctv is not None else 0,
                    "crime": len(original_crime.columns) if original_crime is not None else 0,
                    "pop": len(original_pop.columns) if original_pop is not None else 0
                },
                "final_merged_columns": len(merged_df.columns),
                "final_merged_rows": len(merged_df)
            }
        }
        
        return feature_changes
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"피처 정보 조회 중 오류 발생: {str(e)}")


@router.get("/status")
async def service_status():
    """서비스 상태 및 통계"""
    try:
        data = get_seoul_crime_data()
        
        status = {
            "service": "Seoul Crime Data Service",
            "version": "1.0.0",
            "data_path": data.dname,
            "data_loaded": {
                "cctv": data.cctv is not None,
                "crime": data.crime is not None,
                "pop": data.pop is not None
            },
            "data_stats": {}
        }
        
        if data.cctv is not None:
            status["data_stats"]["cctv"] = {
                "rows": len(data.cctv),
                "columns": len(data.cctv.columns),
                "column_names": list(data.cctv.columns)
            }
        
        if data.crime is not None:
            status["data_stats"]["crime"] = {
                "rows": len(data.crime),
                "columns": len(data.crime.columns),
                "column_names": list(data.crime.columns)
            }
        
        if data.pop is not None:
            status["data_stats"]["pop"] = {
                "rows": len(data.pop),
                "columns": len(data.pop.columns),
                "column_names": list(data.pop.columns)
            }
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 확인 중 오류 발생: {str(e)}")




