"""
서울 범죄 지도 Router - FastAPI 라우터
서울 자치구별 범죄 지도 시각화 관련 엔드포인트를 정의
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from typing import Dict, Optional
from pydantic import BaseModel
from pathlib import Path

from app.seoul_map.service import SeoulMapService

# 라우터 생성
router = APIRouter(
    prefix="/seoul_map",
    tags=["seoul-map"],
    responses={404: {"description": "Not found"}}
)

# 서비스 인스턴스 (싱글톤 패턴)
_seoul_map_service: Optional[SeoulMapService] = None


def get_seoul_map_service() -> SeoulMapService:
    """서비스 인스턴스 싱글톤 패턴"""
    global _seoul_map_service
    if _seoul_map_service is None:
        _seoul_map_service = SeoulMapService()
    return _seoul_map_service


@router.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Seoul Crime Map Service",
        "description": "서울 자치구별 범죄 지도 시각화 서비스",
        "endpoints": {
            "map": "/seoul_map/map - 지도 생성 및 HTML 반환",
            "map_html": "/seoul_map/map/html - 지도 HTML 반환",
            "statistics": "/seoul_map/statistics - 범죄 통계 정보",
            "load_data": "/seoul_map/data - 데이터 로드"
        }
    }


@router.get("/data")
async def load_data():
    """서울 범죄 데이터 로드"""
    try:
        service = get_seoul_map_service()
        result = service.load_data()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 중 오류 발생: {str(e)}")


@router.get("/map")
async def create_map(
    data_column: str = "범죄율",
    location: str = "37.5665,126.9780",
    zoom_start: int = 11,
    fill_color: str = "YlOrRd",
    fill_opacity: float = 0.7,
    line_opacity: float = 0.3,
    legend_name: Optional[str] = None
):
    """
    서울 범죄 Choropleth 지도 생성 및 HTML 반환 (save 폴더에 자동 저장)
    
    Args:
        data_column: 표시할 데이터 컬럼명 (기본값: "범죄율" - 인구수 대비 10만명당 발생 건수)
        location: 지도 중심 좌표 "위도,경도" (기본값: "37.5665,126.9780")
        zoom_start: 초기 줌 레벨 (기본값: 11)
        fill_color: 색상 팔레트 (기본값: "YlOrRd")
        fill_opacity: 채우기 투명도 (기본값: 0.7)
        line_opacity: 경계선 투명도 (기본값: 0.3)
        legend_name: 범례 이름 (None이면 data_column 사용)
    
    Returns:
        HTMLResponse: 지도 HTML
    """
    try:
        service = get_seoul_map_service()
        
        # location 문자열을 리스트로 변환
        location_list = [float(x.strip()) for x in location.split(",")]
        if len(location_list) != 2:
            raise HTTPException(status_code=400, detail="location은 '위도,경도' 형식이어야 합니다.")
        
        # legend_name이 없으면 data_column 사용
        if legend_name is None:
            legend_name = data_column
        
        # 지도 생성 및 save 폴더에 저장 (HTML + PNG 이미지)
        from pathlib import Path
        save_dir = Path(__file__).parent / "save"
        save_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(save_dir / "seoul_crime_map.html")
        
        # 지도 생성 및 저장 (HTML + PNG 이미지)
        save_result = service.save_map(
            output_path=output_path,
            save_image=True,  # PNG 이미지도 저장
            data_column=data_column,
            location=location_list,
            zoom_start=zoom_start,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            line_opacity=line_opacity,
            legend_name=legend_name
        )
        
        # HTML 반환
        map_html = service.get_map_html(
            data_column=data_column,
            location=location_list,
            zoom_start=zoom_start,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            line_opacity=line_opacity,
            legend_name=legend_name
        )
        
        return HTMLResponse(content=map_html)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"지도 생성 중 오류 발생: {str(e)}")


@router.get("/map/html")
async def get_map_html(
    data_column: str = "범죄율",
    location: str = "37.5665,126.9780",
    zoom_start: int = 11,
    fill_color: str = "YlOrRd",
    fill_opacity: float = 0.7,
    line_opacity: float = 0.3,
    legend_name: Optional[str] = None
):
    """
    서울 범죄 지도 HTML 반환 (별칭)
    
    Args:
        data_column: 표시할 데이터 컬럼명 (기본값: "범죄율" - 인구수 대비 10만명당 발생 건수)
        location: 지도 중심 좌표 "위도,경도" (기본값: "37.5665,126.9780")
        zoom_start: 초기 줌 레벨 (기본값: 11)
        fill_color: 색상 팔레트 (기본값: "YlOrRd")
        fill_opacity: 채우기 투명도 (기본값: 0.7)
        line_opacity: 경계선 투명도 (기본값: 0.3)
        legend_name: 범례 이름 (None이면 data_column 사용)
    
    Returns:
        HTMLResponse: 지도 HTML
    """
    return await create_map(
        data_column=data_column,
        location=location,
        zoom_start=zoom_start,
        fill_color=fill_color,
        fill_opacity=fill_opacity,
        line_opacity=line_opacity,
        legend_name=legend_name
    )


@router.get("/map/save")
@router.post("/map/save")
async def save_map(
    data_column: str = "범죄율",
    location: str = "37.5665,126.9780",
    zoom_start: int = 11,
    fill_color: str = "YlOrRd",
    fill_opacity: float = 0.7,
    line_opacity: float = 0.3,
    legend_name: Optional[str] = None,
    output_path: Optional[str] = None
):
    """
    서울 범죄 지도를 HTML 파일 및 PNG 이미지로 저장 (GET/POST 모두 지원)
    
    Args:
        data_column: 표시할 데이터 컬럼명 (기본값: "범죄율" - 인구수 대비 10만명당 발생 건수)
        location: 지도 중심 좌표 "위도,경도" (기본값: "37.5665,126.9780")
        zoom_start: 초기 줌 레벨 (기본값: 11)
        fill_color: 색상 팔레트 (기본값: "YlOrRd")
        fill_opacity: 채우기 투명도 (기본값: 0.7)
        line_opacity: 경계선 투명도 (기본값: 0.3)
        legend_name: 범례 이름 (None이면 data_column 사용)
        output_path: 저장 경로 (None이면 기본 경로 사용)
    
    Returns:
        Dict: 저장 결과 정보
    """
    try:
        service = get_seoul_map_service()
        
        # location 문자열을 리스트로 변환
        location_list = [float(x.strip()) for x in location.split(",")]
        if len(location_list) != 2:
            raise HTTPException(status_code=400, detail="location은 '위도,경도' 형식이어야 합니다.")
        
        # legend_name이 없으면 data_column 사용
        if legend_name is None:
            legend_name = data_column
        
        # 지도 저장 (HTML + PNG 이미지)
        result = service.save_map(
            output_path=output_path,
            save_image=True,  # PNG 이미지도 저장
            data_column=data_column,
            location=location_list,
            zoom_start=zoom_start,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            line_opacity=line_opacity,
            legend_name=legend_name
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"지도 저장 중 오류 발생: {str(e)}")


@router.get("/statistics")
async def get_statistics(data_column: str = "범죄율"):
    """범죄 통계 정보 반환"""
    try:
        service = get_seoul_map_service()
        stats = service.get_statistics(data_column=data_column)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 정보 조회 중 오류 발생: {str(e)}")


@router.get("/map/image")
async def get_map_image():
    """
    저장된 지도 이미지 반환 (PNG)
    
    Returns:
        FileResponse: PNG 이미지 파일
    """
    try:
        save_dir = Path(__file__).parent / "save"
        image_path = save_dir / "seoul_crime_map.png"
        
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="지도 이미지가 아직 생성되지 않았습니다. /seoul_map/map/save를 먼저 호출하세요.")
        
        return FileResponse(
            path=str(image_path),
            media_type="image/png",
            filename="seoul_crime_map.png"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 조회 중 오류 발생: {str(e)}")

