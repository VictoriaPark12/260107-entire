"""
US Unemployment Router - FastAPI 라우터
미국 실업률 지도 시각화 관련 엔드포인트를 정의
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from typing import Dict, Optional, List
from pydantic import BaseModel
from pathlib import Path

from app.us_unemployment.service import USUnemploymentService

# 라우터 생성
router = APIRouter(
    prefix="/us_map",
    tags=["us-unemployment"],
    responses={404: {"description": "Not found"}}
)

# 서비스 인스턴스 (싱글톤 패턴)
_us_unemployment_service: Optional[USUnemploymentService] = None


def get_us_unemployment_service() -> USUnemploymentService:
    """서비스 인스턴스 싱글톤 패턴"""
    global _us_unemployment_service
    if _us_unemployment_service is None:
        _us_unemployment_service = USUnemploymentService()
    return _us_unemployment_service


@router.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "US Unemployment Map Service",
        "description": "미국 실업률 지도 시각화 서비스",
        "endpoints": {
            "map": "/us_map/map - 지도 생성 및 HTML 반환",
            "map_html": "/us_map/map/html - 지도 HTML 반환",
            "statistics": "/us_map/statistics - 실업률 통계 정보",
            "load_data": "/us_map/data - 데이터 로드"
        }
    }


@router.get("/data")
async def load_data():
    """미국 실업률 데이터 로드"""
    try:
        service = get_us_unemployment_service()
        result = service.load_data()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 중 오류 발생: {str(e)}")


@router.get("/map")
async def create_map(
    location: str = "48,-102",
    zoom_start: int = 3,
    fill_color: str = "YlGn",
    fill_opacity: float = 0.7,
    line_opacity: float = 0.2,
    legend_name: str = "Unemployment Rate (%)"
):
    """
    미국 실업률 Choropleth 지도 생성 및 HTML 반환 (save 폴더에 자동 저장)
    
    Args:
        location: 지도 중심 좌표 "위도,경도" (기본값: "48,-102")
        zoom_start: 초기 줌 레벨 (기본값: 3)
        fill_color: 색상 팔레트 (기본값: "YlGn")
        fill_opacity: 채우기 투명도 (기본값: 0.7)
        line_opacity: 경계선 투명도 (기본값: 0.2)
        legend_name: 범례 이름 (기본값: "Unemployment Rate (%)")
    
    Returns:
        HTMLResponse: 지도 HTML
    """
    try:
        service = get_us_unemployment_service()
        
        # location 문자열을 리스트로 변환
        location_list = [float(x.strip()) for x in location.split(",")]
        if len(location_list) != 2:
            raise HTTPException(status_code=400, detail="location은 '위도,경도' 형식이어야 합니다.")
        
        # 지도 생성 및 save 폴더에 저장
        from pathlib import Path
        save_dir = Path(__file__).parent / "save"
        save_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(save_dir / "us_unemployment_map.html")
        
        # 지도 생성 및 저장 (HTML + PNG 이미지)
        save_result = service.save_map(
            output_path=output_path,
            save_image=True,  # PNG 이미지도 저장
            location=location_list,
            zoom_start=zoom_start,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            line_opacity=line_opacity,
            legend_name=legend_name
        )
        
        # HTML 반환
        map_html = service.get_map_html(
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
    location: str = "48,-102",
    zoom_start: int = 3,
    fill_color: str = "YlGn",
    fill_opacity: float = 0.7,
    line_opacity: float = 0.2,
    legend_name: str = "Unemployment Rate (%)"
):
    """
    미국 실업률 지도 HTML 반환 (별칭)
    
    Args:
        location: 지도 중심 좌표 "위도,경도" (기본값: "48,-102")
        zoom_start: 초기 줌 레벨 (기본값: 3)
        fill_color: 색상 팔레트 (기본값: "YlGn")
        fill_opacity: 채우기 투명도 (기본값: 0.7)
        line_opacity: 경계선 투명도 (기본값: 0.2)
        legend_name: 범례 이름 (기본값: "Unemployment Rate (%)")
    
    Returns:
        HTMLResponse: 지도 HTML
    """
    return await create_map(
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
    location: str = "48,-102",
    zoom_start: int = 3,
    fill_color: str = "YlGn",
    fill_opacity: float = 0.7,
    line_opacity: float = 0.2,
    legend_name: str = "Unemployment Rate (%)",
    output_path: Optional[str] = None
):
    """
    미국 실업률 지도를 HTML 파일 및 PNG 이미지로 저장 (GET/POST 모두 지원)
    
    Args:
        location: 지도 중심 좌표 "위도,경도" (기본값: "48,-102")
        zoom_start: 초기 줌 레벨 (기본값: 3)
        fill_color: 색상 팔레트 (기본값: "YlGn")
        fill_opacity: 채우기 투명도 (기본값: 0.7)
        line_opacity: 경계선 투명도 (기본값: 0.2)
        legend_name: 범례 이름 (기본값: "Unemployment Rate (%)")
        output_path: 저장 경로 (None이면 기본 경로 사용)
    
    Returns:
        Dict: 저장 결과 정보
    """
    try:
        service = get_us_unemployment_service()
        
        # location 문자열을 리스트로 변환
        location_list = [float(x.strip()) for x in location.split(",")]
        if len(location_list) != 2:
            raise HTTPException(status_code=400, detail="location은 '위도,경도' 형식이어야 합니다.")
        
        # 지도 저장 (HTML + PNG 이미지)
        result = service.save_map(
            output_path=output_path,
            save_image=True,  # PNG 이미지도 저장
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
async def get_statistics():
    """실업률 통계 정보 반환"""
    try:
        service = get_us_unemployment_service()
        stats = service.get_statistics()
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
        image_path = save_dir / "us_unemployment_map.png"
        
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="지도 이미지가 아직 생성되지 않았습니다. /us_map/map/save를 먼저 호출하세요.")
        
        return FileResponse(
            path=str(image_path),
            media_type="image/png",
            filename="us_unemployment_map.png"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 조회 중 오류 발생: {str(e)}")

