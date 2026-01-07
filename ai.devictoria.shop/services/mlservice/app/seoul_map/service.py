"""
서울 범죄 지도 시각화 서비스
folium을 사용한 Choropleth 지도 생성
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import json
import folium
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
    logger = setup_logging("seoul_map_service")
except ImportError:
    import logging
    logger = logging.getLogger("seoul_map_service")


class SeoulMapService:
    """서울 범죄 지도 시각화 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        # 파일 경로 설정
        self.base_dir = Path(__file__).parent.parent / "seoul_crime"
        self.geo_json_path = self.base_dir / "data" / "kr-state.json"
        self.crime_data_path = self.base_dir / "save" / "crime_merged_by_gu.csv"
        
        self.geo_json = None
        self.crime_data = None
    
    def load_data(self) -> Dict[str, Any]:
        """
        서울 범죄 데이터 로드
        
        Returns:
            Dict[str, Any]: 로드된 데이터 정보
        """
        try:
            logger.info("서울 범죄 데이터 로드 시작")
            
            # GeoJSON 데이터 로드
            logger.info(f"GeoJSON 데이터 로드: {self.geo_json_path}")
            with open(self.geo_json_path, 'r', encoding='utf-8') as f:
                self.geo_json = json.load(f)
            
            # CSV 데이터 로드
            logger.info(f"CSV 데이터 로드: {self.crime_data_path}")
            self.crime_data = pd.read_csv(self.crime_data_path, encoding='utf-8-sig')
            
            # 범죄율 계산 (인구수 대비 10만명당 발생 건수) - 범죄율 히트맵과 동일한 방식
            if '인구' in self.crime_data.columns and '소계' in self.crime_data.columns:
                # 인구수가 있는 행만 계산 (NaN 제외)
                valid_mask = self.crime_data['인구'].notna() & (self.crime_data['인구'] > 0)
                crime_rate = np.where(
                    valid_mask,
                    (self.crime_data['소계'] / self.crime_data['인구']) * 100000,
                    np.nan
                )
                self.crime_data['범죄율'] = crime_rate
                logger.info("범죄율 계산 완료 (10만명당 발생 건수)")
            
            # 검거율 계산 (인구수 대비 10만명당 검거 건수) - 검거율 히트맵과 동일한 방식
            if '인구' in self.crime_data.columns:
                # 검거 컬럼 찾기 (검거 건수만)
                arrest_cols = [col for col in self.crime_data.columns if '검거' in col and '발생' not in col]
                if len(arrest_cols) > 0:
                    # 각 범죄 유형별 검거 건수 합계
                    total_arrest = self.crime_data[arrest_cols].sum(axis=1)
                    
                    valid_mask = self.crime_data['인구'].notna() & (self.crime_data['인구'] > 0)
                    arrest_rate = np.where(
                        valid_mask,
                        (total_arrest / self.crime_data['인구']) * 100000,
                        np.nan
                    )
                    self.crime_data['검거율'] = arrest_rate
                    logger.info("검거율 계산 완료 (10만명당 검거 건수)")
            
            logger.info(f"데이터 로드 완료: {len(self.crime_data)}개 자치구")
            
            return {
                "status": "success",
                "gu_count": len(self.crime_data),
                "columns": list(self.crime_data.columns),
                "data_preview": self.crime_data.head().to_dict('records')
            }
        except Exception as e:
            logger.error(f"데이터 로드 실패: {str(e)}")
            raise
    
    def create_map(
        self,
        data_column: str = "범죄율",
        location: list = [37.5665, 126.9780],  # 서울시청 좌표
        zoom_start: int = 11,
        fill_color: str = "YlOrRd",
        fill_opacity: float = 0.7,
        line_opacity: float = 0.3,
        legend_name: str = "범죄율 (10만명당)"
    ) -> folium.Map:
        """
        서울 범죄 Choropleth 지도 생성
        
        Args:
            data_column: 표시할 데이터 컬럼명 (기본값: "범죄율")
            location: 지도 중심 좌표 [위도, 경도] (기본값: 서울시청 [37.5665, 126.9780])
            zoom_start: 초기 줌 레벨 (기본값: 11)
            fill_color: 색상 팔레트 (기본값: "YlOrRd")
            fill_opacity: 채우기 투명도 (기본값: 0.7)
            line_opacity: 경계선 투명도 (기본값: 0.3)
            legend_name: 범례 이름 (기본값: "범죄율")
        
        Returns:
            folium.Map: 생성된 지도 객체
        """
        try:
            # 데이터가 로드되지 않았으면 먼저 로드
            if self.geo_json is None or self.crime_data is None:
                self.load_data()
            
            logger.info(f"지도 생성 시작 (컬럼: {data_column})")
            
            # 데이터 컬럼 확인
            if data_column not in self.crime_data.columns:
                available_columns = list(self.crime_data.columns)
                raise ValueError(f"컬럼 '{data_column}'이 없습니다. 사용 가능한 컬럼: {available_columns}")
            
            # 지도 생성
            m = folium.Map(location=location, zoom_start=zoom_start, tiles='OpenStreetMap')
            
            # 데이터를 자치구 이름으로 인덱싱 (popup용)
            data_dict = self.crime_data.set_index('자치구')
            
            # 각 자치구에 대한 popup 정보 생성 함수
            def on_each_feature(feature, layer):
                """각 자치구에 popup 추가"""
                gu_name = feature['id']
                if gu_name in data_dict.index:
                    row = data_dict.loc[gu_name]
                    
                    # 범죄율과 검거율 가져오기
                    crime_rate = row.get('범죄율', None)
                    arrest_rate = row.get('검거율', None)
                    
                    # 값 포맷팅
                    if pd.notna(crime_rate):
                        crime_rate_str = f"{crime_rate:.2f}"
                    else:
                        crime_rate_str = "N/A"
                    
                    if pd.notna(arrest_rate):
                        arrest_rate_str = f"{arrest_rate:.2f}"
                    else:
                        arrest_rate_str = "N/A"
                    
                    # Popup HTML 생성
                    popup_html = f"""
                    <div style="font-family: 'Malgun Gothic', Arial, sans-serif; min-width: 220px; padding: 4px;">
                        <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 18px; font-weight: bold; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;">
                            {gu_name}
                        </h3>
                        <div style="padding-top: 4px;">
                            <div style="margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                                <span style="color: #6b7280; font-size: 13px; font-weight: 500;">범죄율:</span>
                                <span style="color: #dc2626; font-size: 16px; font-weight: bold;">
                                    {crime_rate_str}
                                </span>
                                <span style="color: #9ca3af; font-size: 10px; margin-left: 4px;">(10만명당)</span>
                            </div>
                            <div style="display: flex; align-items: center; justify-content: space-between;">
                                <span style="color: #6b7280; font-size: 13px; font-weight: 500;">검거율:</span>
                                <span style="color: #059669; font-size: 16px; font-weight: bold;">
                                    {arrest_rate_str}
                                </span>
                                <span style="color: #9ca3af; font-size: 10px; margin-left: 4px;">(10만명당)</span>
                            </div>
                        </div>
                    </div>
                    """
                    layer.bind_popup(popup_html)
            
            # Choropleth 레이어 추가
            choropleth = folium.Choropleth(
                geo_data=self.geo_json,
                name="choropleth",
                data=self.crime_data,
                columns=["자치구", data_column],
                key_on="feature.id",  # kr-state.json의 id 필드와 매칭
                fill_color=fill_color,
                fill_opacity=fill_opacity,
                line_opacity=line_opacity,
                legend_name=legend_name,
            ).add_to(m)
            
            # 별도의 GeoJson 레이어로 popup 추가 (투명하게, 클릭만 가능)
            def transparent_style(feature):
                """투명한 스타일 함수"""
                return {
                    'fillColor': 'transparent',
                    'fillOpacity': 0,
                    'color': 'transparent',
                    'weight': 0,
                    'opacity': 0
                }
            
            folium.GeoJson(
                self.geo_json,
                style_function=transparent_style,
                tooltip=folium.GeoJsonTooltip(
                    fields=['name'],
                    aliases=['자치구:'],
                    labels=True,
                    sticky=True
                ),
                on_each_feature=on_each_feature
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
                html_path = str(save_dir / "seoul_crime_map.html")
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
                    image_path = str(save_dir / "seoul_crime_map.png")
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
    
    def get_statistics(self, data_column: str = "범죄율") -> Dict[str, Any]:
        """
        범죄 통계 정보 반환
        
        Args:
            data_column: 통계를 계산할 컬럼명 (기본값: "범죄율")
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            # 데이터가 로드되지 않았으면 먼저 로드
            if self.crime_data is None:
                self.load_data()
            
            if data_column not in self.crime_data.columns:
                available_columns = list(self.crime_data.columns)
                raise ValueError(f"컬럼 '{data_column}'이 없습니다. 사용 가능한 컬럼: {available_columns}")
            
            stats = {
                "status": "success",
                "total_gu": len(self.crime_data),
                "data_column": data_column,
                "statistics": {
                    "mean": float(self.crime_data[data_column].mean()),
                    "median": float(self.crime_data[data_column].median()),
                    "min": float(self.crime_data[data_column].min()),
                    "max": float(self.crime_data[data_column].max()),
                    "std": float(self.crime_data[data_column].std())
                },
                "top_5": self.crime_data.nlargest(5, data_column)[
                    ["자치구", data_column]
                ].to_dict('records'),
                "bottom_5": self.crime_data.nsmallest(5, data_column)[
                    ["자치구", data_column]
                ].to_dict('records')
            }
            
            return stats
        
        except Exception as e:
            logger.error(f"통계 정보 조회 실패: {str(e)}")
            raise

