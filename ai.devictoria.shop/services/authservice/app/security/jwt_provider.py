"""
JWT Token Provider
"""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.config import JwtProperties


class JwtTokenProvider:
    """JWT 토큰 생성 및 검증"""
    
    def __init__(self, jwt_properties: JwtProperties):
        self.jwt_properties = jwt_properties
        self.secret_key = self._get_secret_key()
    
    def _get_secret_key(self) -> bytes:
        """JWT 시크릿 키 생성"""
        secret = self.jwt_properties.secret
        
        # JWT_SECRET이 비어있거나 없으면 기본값 사용
        if not secret or len(secret.strip()) == 0:
            print("[경고] JWT_SECRET이 설정되지 않았습니다. 기본값을 사용합니다.")
            secret = "default-jwt-secret-key-for-development-only-change-in-production"
        
        key_bytes = secret.encode('utf-8')
        
        # JWT는 최소 32바이트(256비트)가 필요
        if len(key_bytes) < 32:
            print(f"[경고] JWT_SECRET이 너무 짧습니다 ({len(key_bytes)}바이트). 32바이트로 패딩합니다.")
            padded_key = bytearray(32)
            for i in range(32):
                padded_key[i] = key_bytes[i % len(key_bytes)]
            key_bytes = bytes(padded_key)
        
        return key_bytes
    
    def create_access_token(self, user_id: int, email: Optional[str] = None, nickname: Optional[str] = None) -> str:
        """Access Token 생성"""
        claims: Dict[str, Any] = {
            "userId": user_id,
            "email": email,
            "nickname": nickname,
            "type": "access"
        }
        
        now = datetime.utcnow()
        expiration = now + timedelta(milliseconds=self.jwt_properties.access_token_expiration)
        
        payload = {
            **claims,
            "sub": str(user_id),
            "iat": now,
            "exp": expiration
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def create_refresh_token(self, user_id: int) -> str:
        """Refresh Token 생성"""
        claims: Dict[str, Any] = {
            "userId": user_id,
            "type": "refresh"
        }
        
        now = datetime.utcnow()
        expiration = now + timedelta(milliseconds=self.jwt_properties.refresh_token_expiration)
        
        payload = {
            **claims,
            "sub": str(user_id),
            "iat": now,
            "exp": expiration
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def validate_token(self, token: str) -> bool:
        """토큰 검증"""
        try:
            jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return True
        except Exception:
            return False
    
    def get_claims(self, token: str) -> Dict[str, Any]:
        """토큰에서 Claims 추출"""
        return jwt.decode(token, self.secret_key, algorithms=["HS256"])
    
    def get_user_id(self, token: str) -> Optional[int]:
        """토큰에서 사용자 ID 추출"""
        try:
            claims = self.get_claims(token)
            return claims.get("userId")
        except Exception:
            return None

