import requests
from pathlib import Path
from pydantic_settings import BaseSettings


def _find_project_root() -> Path:
    """프로젝트 루트 디렉토리를 찾는 함수"""
    current = Path(__file__).resolve()
    
    # .env 파일이 있는 디렉토리를 프로젝트 루트로 간주
    for parent in current.parents:
        if (parent / ".env").exists():
            return parent
    
    # .env 파일을 찾지 못한 경우, project 디렉토리를 찾음
    # ai.devictoria.shop/services/mlservice/app/seoul_crime/save/kakao_map_singleton.py
    # -> project 디렉토리까지 올라감
    current_path = current
    while current_path.parent != current_path:
        if current_path.name == "project":
            return current_path
        current_path = current_path.parent
    
    # 최후의 수단: 상대 경로로 계산
    # save -> seoul_crime -> app -> mlservice -> services -> ai.devictoria.shop -> project
    return current.parent.parent.parent.parent.parent.parent


# 프로젝트 루트의 .env 파일 경로를 미리 계산
_PROJECT_ROOT = _find_project_root()
_ENV_FILE_PATH = str(_PROJECT_ROOT / ".env")


class KakaoMapConfig(BaseSettings):
    """카카오맵 API 설정"""
    kakao_rest_api_key: str = ""
    
    class Config:
        # 프로젝트 루트 디렉토리의 .env 파일 경로
        env_file = _ENV_FILE_PATH
        case_sensitive = False
        extra = 'ignore'  # .env 파일의 다른 변수들은 무시


class KakaoMapSingleton:
    _instance = None  # 싱글턴 인스턴스를 저장할 클래스 변수
    _base_url = "https://dapi.kakao.com/v2/local"

    def __new__(cls):
        if cls._instance is None:  # 인스턴스가 없으면 생성
            cls._instance = super(KakaoMapSingleton, cls).__new__(cls)
            cls._instance._api_key = cls._instance._retrieve_api_key()  # API 키 가져오기
            cls._instance._headers = {
                "Authorization": f"KakaoAK {cls._instance._api_key}"
            }
        return cls._instance  # 기존 인스턴스 반환

    def _retrieve_api_key(self):
        """API 키를 .env 파일에서 가져오는 내부 메서드"""
        config = KakaoMapConfig()
        api_key = config.kakao_rest_api_key
        
        if not api_key:
            raise ValueError(
                "카카오맵 REST API 키가 설정되지 않았습니다. "
                "프로젝트 루트의 .env 파일에 KAKAO_REST_API_KEY를 설정해주세요."
            )
        
        return api_key

    def get_api_key(self):
        """저장된 API 키 반환"""
        return self._api_key

    def geocode(self, address, language='ko'):
        """주소를 위도, 경도로 변환하는 메서드 (키워드 검색)"""
        url = f"{self._base_url}/search/keyword.json"
        params = {
            "query": address
        }
        
        try:
            response = requests.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"카카오맵 API 요청 실패: {str(e)}")
    
    def search_address(self, address):
        """주소 검색 API 사용"""
        url = f"{self._base_url}/search/address.json"
        params = {
            "query": address
        }
        
        try:
            response = requests.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"카카오맵 주소 검색 API 요청 실패: {str(e)}")
