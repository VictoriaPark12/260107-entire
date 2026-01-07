"""
구글 인증 서비스
"""
import httpx
from app.config import GoogleProperties
from app.dto.provider import GoogleTokenResponse, GoogleUserInfo


class GoogleAuthService:
    """구글 OAuth 인증 서비스"""
    
    def __init__(self, google_properties: GoogleProperties):
        self.google_properties = google_properties
    
    def get_google_token(self, authorization_code: str) -> GoogleTokenResponse:
        """구글 인증 코드로 토큰 요청"""
        print("[GoogleAuthService] 구글 토큰 요청 시작")
        
        form_data = {
            "grant_type": "authorization_code",
            "client_id": self.google_properties.client_id,
            "client_secret": self.google_properties.client_secret,
            "redirect_uri": self.google_properties.redirect_uri,
            "code": authorization_code
        }
        
        try:
            print("[GoogleAuthService] 구글 API에 토큰 요청 전송 중...")
            with httpx.Client() as client:
                response = client.post(
                    self.google_properties.token_uri,
                    data=form_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                token_data = response.json()
            
            token_response = GoogleTokenResponse(**token_data)
            print("[GoogleAuthService] 구글 토큰 요청 성공!")
            return token_response
            
        except Exception as e:
            print(f"[GoogleAuthService] 구글 토큰 요청 실패: {e}")
            raise RuntimeError(f"구글 토큰 요청 실패: {e}")
    
    def get_google_user_info(self, access_token: str) -> GoogleUserInfo:
        """구글 액세스 토큰으로 사용자 정보 조회"""
        print("[GoogleAuthService] 구글 사용자 정보 조회 시작")
        
        try:
            print("[GoogleAuthService] 구글 API에 사용자 정보 요청 전송 중...")
            with httpx.Client() as client:
                response = client.get(
                    self.google_properties.user_info_uri,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                user_data = response.json()
            
            user_info = GoogleUserInfo(**user_data)
            print("[GoogleAuthService] 구글 사용자 정보 조회 성공!")
            return user_info
            
        except Exception as e:
            print(f"[GoogleAuthService] 구글 사용자 정보 조회 실패: {e}")
            raise RuntimeError(f"구글 사용자 정보 조회 실패: {e}")
    
    def login_with_authorization_code(self, authorization_code: str) -> GoogleUserInfo:
        """인증 코드로 구글 로그인 처리"""
        print("[GoogleAuthService] 인증 코드로 로그인 처리 시작")
        token_response = self.get_google_token(authorization_code)
        return self.get_google_user_info(token_response.access_token)
    
    def login_with_access_token(self, access_token: str) -> GoogleUserInfo:
        """액세스 토큰으로 구글 로그인 처리"""
        print("[GoogleAuthService] 액세스 토큰으로 로그인 처리 시작")
        return self.get_google_user_info(access_token)

