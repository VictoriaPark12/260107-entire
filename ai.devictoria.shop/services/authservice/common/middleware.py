"""
로깅 미들웨어
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging


class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 요청 로깅
        logger = logging.getLogger("auth_service")
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # 응답 처리
        response = await call_next(request)
        
        # 응답 시간 계산
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
        
        return response

