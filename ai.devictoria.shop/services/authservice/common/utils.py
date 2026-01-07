"""
공통 유틸리티 함수
"""
import logging
import sys
from pathlib import Path


def setup_logging(service_name: str) -> logging.Logger:
    """로깅 설정"""
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    
    # 콘솔 핸들러 설정
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # 포맷 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

