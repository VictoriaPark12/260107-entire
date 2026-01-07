"""
카카오 인증 서비스
"""
import json
import httpx
from typing import Optional
from app.config import KakaoProperties, RedisConfig
from app.dto.provider import KakaoTokenResponse, KakaoUserInfo
import redis


class KakaoAuthService:
    """카카오 OAuth 인증 서비스"""
    
    def __init__(self, kakao_properties: KakaoProperties, redis_config: Optional[RedisConfig] = None):
        self.kakao_properties = kakao_properties
        self.redis_config = redis_config
        self.redis_client = None
        
        if redis_config:
            try:
                self.redis_client = redis.Redis(
                    host=redis_config.host,
                    port=redis_config.port,
                    password=redis_config.password if redis_config.password else None,
                    username=redis_config.username if redis_config.username else None,
                    ssl=redis_config.use_ssl,
                    socket_timeout=redis_config.timeout / 1000,  # 밀리초를 초로 변환
                    decode_responses=True
                )
            except Exception as e:
                print(f"[KakaoAuthService] Redis 연결 실패: {e}")
    
    def get_kakao_token(self, authorization_code: str) -> KakaoTokenResponse:
        """카카오 인증 코드로 토큰 요청"""
        print("[KakaoAuthService] 카카오 토큰 요청 시작")
        print(f"[KakaoAuthService] 인증 코드: {authorization_code}")
        print(f"[KakaoAuthService] REST API Key: {self.kakao_properties.rest_api_key}")
        print(f"[KakaoAuthService] Redirect URI: {self.kakao_properties.redirect_uri}")
        print(f"[KakaoAuthService] Token URI: {self.kakao_properties.token_uri}")
        
        form_data = {
            "grant_type": "authorization_code",
            "client_id": self.kakao_properties.rest_api_key,
            "redirect_uri": self.kakao_properties.redirect_uri,
            "code": authorization_code
        }
        
        try:
            print("[KakaoAuthService] 카카오 API에 토큰 요청 전송 중...")
            with httpx.Client() as client:
                response = client.post(
                    self.kakao_properties.token_uri,
                    data=form_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                token_data = response.json()
            
            token_response = KakaoTokenResponse(**token_data)
            print("[KakaoAuthService] 카카오 토큰 요청 성공!")
            print(f"[KakaoAuthService] 받은 Access Token: {token_response.access_token[:20]}...")
            return token_response
            
        except Exception as e:
            print(f"[KakaoAuthService] 카카오 토큰 요청 실패: {e}")
            raise RuntimeError(f"카카오 토큰 요청 실패: {e}")
    
    def get_kakao_user_info(self, access_token: str) -> KakaoUserInfo:
        """카카오 액세스 토큰으로 사용자 정보 조회"""
        print("[KakaoAuthService] 카카오 사용자 정보 조회 시작")
        print(f"[KakaoAuthService] 사용할 Access Token: {access_token[:20]}...")
        print(f"[KakaoAuthService] User Info URI: {self.kakao_properties.user_info_uri}")
        
        try:
            print("[KakaoAuthService] 카카오 API에 사용자 정보 요청 전송 중...")
            with httpx.Client() as client:
                response = client.get(
                    self.kakao_properties.user_info_uri,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                user_data = response.json()
            
            user_info = KakaoUserInfo(**user_data)
            print("[KakaoAuthService] 카카오 사용자 정보 조회 성공!")
            print(f"[KakaoAuthService] 사용자 ID: {user_info.id}")
            if user_info.kakao_account:
                print(f"[KakaoAuthService] 이메일: {user_info.kakao_account.email}")
                if user_info.kakao_account.profile:
                    print(f"[KakaoAuthService] 닉네임: {user_info.kakao_account.profile.nickname}")
            return user_info
            
        except Exception as e:
            print(f"[KakaoAuthService] 카카오 사용자 정보 조회 실패: {e}")
            raise RuntimeError(f"카카오 사용자 정보 조회 실패: {e}")
    
    def login_with_authorization_code(self, authorization_code: str) -> KakaoUserInfo:
        """인증 코드로 카카오 로그인 처리 (토큰 요청 + 사용자 정보 조회)"""
        print("[KakaoAuthService] 인증 코드로 로그인 처리 시작")
        # 1. 인증 코드로 토큰 요청
        token_response = self.get_kakao_token(authorization_code)
        
        # 2. 토큰으로 사용자 정보 조회
        user_info = self.get_kakao_user_info(token_response.access_token)
        
        # 3. 카카오 토큰을 Redis에 저장
        self._save_kakao_token_to_redis(user_info.id, token_response)
        
        return user_info
    
    def login_with_access_token(self, access_token: str) -> KakaoUserInfo:
        """액세스 토큰으로 카카오 로그인 처리 (사용자 정보 조회만)"""
        print("[KakaoAuthService] 액세스 토큰으로 로그인 처리 시작")
        return self.get_kakao_user_info(access_token)
    
    def _save_kakao_token_to_redis(self, user_id: int, token_response: KakaoTokenResponse):
        """카카오 토큰을 Redis에 저장"""
        if not self.redis_client:
            print("[KakaoAuthService] Redis 클라이언트가 없어 토큰을 저장하지 않습니다.")
            return
        
        try:
            key = f"kakao:token:{user_id}"
            token_json = json.dumps(token_response.model_dump())
            
            # 카카오 액세스 토큰 만료 시간 설정
            expiration = token_response.expires_in if token_response.expires_in else 3600  # 기본 1시간
            
            self.redis_client.setex(key, expiration, token_json)
            
            print("========================================")
            print("[KakaoAuthService] ✅ 카카오 토큰을 Redis에 저장했습니다")
            print(f"[KakaoAuthService] Redis Key: {key}")
            print(f"[KakaoAuthService] 만료 시간: {expiration}초")
            print(f"[KakaoAuthService] 저장된 카카오 Access Token: {token_response.access_token[:20]}...")
            if token_response.refresh_token:
                print(f"[KakaoAuthService] 저장된 카카오 Refresh Token: {token_response.refresh_token[:20]}...")
            print("(이 토큰은 Redis에만 저장되고, 프론트엔드로는 반환되지 않습니다)")
            print("========================================")
        except Exception as e:
            print(f"[KakaoAuthService] Redis 저장 중 오류 발생: {e}")

