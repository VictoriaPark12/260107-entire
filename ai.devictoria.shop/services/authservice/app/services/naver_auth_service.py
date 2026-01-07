"""
네이버 인증 서비스
"""
import httpx
from typing import Optional
from app.config import NaverProperties
from app.dto.provider import NaverTokenResponse, NaverUserInfo


class NaverAuthService:
    """네이버 OAuth 인증 서비스"""
    
    def __init__(self, naver_properties: NaverProperties):
        self.naver_properties = naver_properties
    
    def get_naver_token(self, authorization_code: str, state: Optional[str] = None) -> NaverTokenResponse:
        """네이버 인증 코드로 토큰 요청"""
        print("[NaverAuthService] 네이버 토큰 요청 시작")
        
        form_data = {
            "grant_type": "authorization_code",
            "client_id": self.naver_properties.client_id,
            "client_secret": self.naver_properties.client_secret,
            "redirect_uri": self.naver_properties.redirect_uri,
            "code": authorization_code
        }
        
        if state:
            form_data["state"] = state
        
        try:
            print("[NaverAuthService] 네이버 API에 토큰 요청 전송 중...")
            with httpx.Client() as client:
                response = client.post(
                    self.naver_properties.token_uri,
                    data=form_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                token_data = response.json()
            
            token_response = NaverTokenResponse(**token_data)
            print("[NaverAuthService] 네이버 토큰 요청 성공!")
            return token_response
            
        except Exception as e:
            print(f"[NaverAuthService] 네이버 토큰 요청 실패: {e}")
            raise RuntimeError(f"네이버 토큰 요청 실패: {e}")
    
    def get_naver_user_info(self, access_token: str) -> NaverUserInfo:
        """네이버 액세스 토큰으로 사용자 정보 조회"""
        print("[NaverAuthService] 네이버 사용자 정보 조회 시작")
        
        try:
            print("[NaverAuthService] 네이버 API에 사용자 정보 요청 전송 중...")
            with httpx.Client() as client:
                response = client.get(
                    self.naver_properties.user_info_uri,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                user_data = response.json()
            
            user_info = NaverUserInfo(**user_data)
            print("[NaverAuthService] 네이버 사용자 정보 조회 성공!")
            return user_info
            
        except Exception as e:
            print(f"[NaverAuthService] 네이버 사용자 정보 조회 실패: {e}")
            raise RuntimeError(f"네이버 사용자 정보 조회 실패: {e}")
    
    def login_with_authorization_code(self, authorization_code: str, state: Optional[str] = None) -> NaverUserInfo:
        """인증 코드로 네이버 로그인 처리"""
        print("[NaverAuthService] 인증 코드로 로그인 처리 시작")
        token_response = self.get_naver_token(authorization_code, state)
        return self.get_naver_user_info(token_response.access_token)
    
    def login_with_access_token(self, access_token: str) -> NaverUserInfo:
        """액세스 토큰으로 네이버 로그인 처리"""
        print("[NaverAuthService] 액세스 토큰으로 로그인 처리 시작")
        return self.get_naver_user_info(access_token)

