"""
미국 실업률 지도 시각화 서비스
folium을 사용한 Choropleth 지도 생성
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import requests
import folium
from io import StringIO
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from common.utils import setup_logging
    logger = setup_logging("us_unemployment_service")
except ImportError:
    import logging
    logger = logging.getLogger("us_unemployment_service")


class USUnemploymentService:
    """미국 실업률 지도 시각화 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.state_geo_url = "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_states.json"
        self.state_data_url = "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_unemployment_oct_2012.csv"
        self.state_geo = None
        self.state_data = None
    
    def load_data(self) -> Dict[str, Any]:
        """
        미국 실업률 데이터 로드
        
        Returns:
            Dict[str, Any]: 로드된 데이터 정보
        """
        try:
            logger.info("미국 실업률 데이터 로드 시작")
            
            # GeoJSON 데이터 로드
            logger.info(f"GeoJSON 데이터 로드: {self.state_geo_url}")
            response = requests.get(self.state_geo_url)
            response.raise_for_status()
            self.state_geo = response.json()
            
            # CSV 데이터 로드
            logger.info(f"CSV 데이터 로드: {self.state_data_url}")
            response = requests.get(self.state_data_url)
            response.raise_for_status()
            self.state_data = pd.read_csv(StringIO(response.text))
            
            logger.info(f"데이터 로드 완료: {len(self.state_data)}개 주")
            
            return {
                "status": "success",
                "states_count": len(self.state_data),
                "columns": list(self.state_data.columns),
                "data_preview": self.state_data.head().to_dict('records')
            }
        except Exception as e:
            logger.error(f"데이터 로드 실패: {str(e)}")
            raise
    
    def create_map(
        self,
        location: list = [48, -102],
        zoom_start: int = 3,
        fill_color: str = "YlGn",
        fill_opacity: float = 0.7,
        line_opacity: float = 0.2,
        legend_name: str = "Unemployment Rate (%)"
    ) -> folium.Map:
        """
        미국 실업률 Choropleth 지도 생성
        
        Args:
            location: 지도 중심 좌표 [위도, 경도] (기본값: [48, -102])
            zoom_start: 초기 줌 레벨 (기본값: 3)
            fill_color: 색상 팔레트 (기본값: "YlGn")
            fill_opacity: 채우기 투명도 (기본값: 0.7)
            line_opacity: 경계선 투명도 (기본값: 0.2)
            legend_name: 범례 이름 (기본값: "Unemployment Rate (%)")
        
        Returns:
            folium.Map: 생성된 지도 객체
        """
        try:
            # 데이터가 로드되지 않았으면 먼저 로드
            if self.state_geo is None or self.state_data is None:
                self.load_data()
            
            logger.info("지도 생성 시작")
            
            # 지도 생성
            m = folium.Map(location=location, zoom_start=zoom_start)
            
            # Choropleth 레이어 추가
            folium.Choropleth(
                geo_data=self.state_geo,
                name="choropleth",
                data=self.state_data,
                columns=["State", "Unemployment"],
                key_on="feature.id",
                fill_color=fill_color,
                fill_opacity=fill_opacity,
                line_opacity=line_opacity,
                legend_name=legend_name,
            ).add_to(m)
            
            # 레이어 컨트롤 추가
            folium.LayerControl().add_to(m)
            
            logger.info("지도 생성 완료")
            
            return m
        
        except Exception as e:
            logger.error(f"지도 생성 실패: {str(e)}")
            raise
    
    def save_map(
        self,
        output_path: Optional[str] = None,
        save_image: bool = True,
        **map_kwargs
    ) -> Dict[str, Any]:
        """
        지도를 HTML 파일과 PNG 이미지로 저장
        
        Args:
            output_path: 저장 경로 (None이면 기본 경로 사용)
            save_image: PNG 이미지도 저장할지 여부 (기본값: True)
            **map_kwargs: create_map 메서드에 전달할 인자들
        
        Returns:
            Dict[str, Any]: 저장 결과 정보
        """
        try:
            # 저장 경로 설정
            save_dir = Path(__file__).parent / "save"
            save_dir.mkdir(parents=True, exist_ok=True)
            
            if output_path is None:
                html_path = str(save_dir / "us_unemployment_map.html")
            else:
                html_path = output_path
                if not html_path.endswith('.html'):
                    html_path += '.html'
            
            # 지도 생성
            m = self.create_map(**map_kwargs)
            
            # HTML 파일로 저장
            m.save(html_path)
            logger.info(f"HTML 지도 저장 완료: {html_path}")
            
            result = {
                "status": "success",
                "html_path": html_path,
                "html_size": Path(html_path).stat().st_size
            }
            
            # PNG 이미지 저장
            if save_image:
                try:
                    image_path = str(save_dir / "us_unemployment_map.png")
                    self._save_map_as_image(html_path, image_path)
                    result["image_path"] = image_path
                    result["image_size"] = Path(image_path).stat().st_size
                    logger.info(f"PNG 이미지 저장 완료: {image_path}")
                except Exception as e:
                    logger.warning(f"이미지 저장 실패 (HTML은 저장됨): {str(e)}")
                    result["image_error"] = str(e)
            
            return result
        
        except Exception as e:
            logger.error(f"지도 저장 실패: {str(e)}")
            raise
    
    def _save_map_as_image(self, html_path: str, image_path: str, delay: int = 3):
        """
        HTML 지도를 PNG 이미지로 변환하여 저장
        
        Args:
            html_path: HTML 파일 경로
            image_path: 저장할 이미지 파일 경로
            delay: 페이지 로드 대기 시간 (초)
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # HTML 파일을 file:// 프로토콜로 열기
            file_url = f"file://{Path(html_path).absolute()}"
            driver.get(file_url)
            
            # 지도가 로드될 때까지 대기
            time.sleep(delay)
            
            # 스크린샷 저장
            driver.save_screenshot(image_path)
            
        finally:
            if driver:
                driver.quit()
    
    def get_map_html(self, **map_kwargs) -> str:
        """
        지도를 HTML 문자열로 반환
        
        Args:
            **map_kwargs: create_map 메서드에 전달할 인자들
        
        Returns:
            str: HTML 문자열
        """
        try:
            m = self.create_map(**map_kwargs)
            return m._repr_html_()
        except Exception as e:
            logger.error(f"HTML 생성 실패: {str(e)}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        실업률 통계 정보 반환
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            # 데이터가 로드되지 않았으면 먼저 로드
            if self.state_data is None:
                self.load_data()
            
            stats = {
                "status": "success",
                "total_states": len(self.state_data),
                "unemployment_stats": {
                    "mean": float(self.state_data["Unemployment"].mean()),
                    "median": float(self.state_data["Unemployment"].median()),
                    "min": float(self.state_data["Unemployment"].min()),
                    "max": float(self.state_data["Unemployment"].max()),
                    "std": float(self.state_data["Unemployment"].std())
                },
                "top_5_unemployment": self.state_data.nlargest(5, "Unemployment")[
                    ["State", "Unemployment"]
                ].to_dict('records'),
                "bottom_5_unemployment": self.state_data.nsmallest(5, "Unemployment")[
                    ["State", "Unemployment"]
                ].to_dict('records')
            }
            
            return stats
        
        except Exception as e:
            logger.error(f"통계 정보 조회 실패: {str(e)}")
            raise

