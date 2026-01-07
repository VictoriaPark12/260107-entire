"""
Titanic Service 설정
"""
from pydantic_settings import BaseSettings


class TitanicServiceConfig(BaseSettings):
    """Titanic Service 설정 클래스"""
    service_name: str = "Titanic Service"
    service_version: str = "1.0.0"
    port: int = 9006
    
    class Config:
        env_file = ".env"
        case_sensitive = False

