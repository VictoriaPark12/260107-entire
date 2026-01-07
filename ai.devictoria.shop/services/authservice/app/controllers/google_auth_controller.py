"""
구글 인증 컨트롤러
"""
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.config import GoogleProperties
from app.dto.auth import GoogleLoginRequest, LoginResponse
from app.dto.provider import GoogleUserInfo
from app.security.jwt_provider import JwtTokenProvider
from app.services.google_auth_service import GoogleAuthService

router = APIRouter(prefix="/google", tags=["google"])


def create_google_router(
    google_properties: GoogleProperties,
    google_auth_service: GoogleAuthService,
    jwt_token_provider: JwtTokenProvider
):
    """구글 라우터 생성"""
    
    @router.get("/start")
    async def start_google_login():
        """구글 로그인 시작 (GET)"""
        print("[구글 로그인 시작] 요청이 들어왔습니다")
        
        try:
            # 구글 인증 URL 생성
            redirect_uri = google_properties.redirect_uri
            google_auth_url = (
                "https://accounts.google.com/o/oauth2/v2/auth"
                f"?client_id={google_properties.client_id}"
                f"&redirect_uri={redirect_uri}"
                "&response_type=code"
                "&scope=openid email profile"
            )
            
            print(f"[구글 로그인 시작] 생성된 인증 URL: {google_auth_url}")
            
            return {
                "authUrl": google_auth_url,
                "message": "구글 인증 URL이 생성되었습니다"
            }
        except Exception as e:
            print(f"[구글 로그인 시작] 에러: {e}")
            raise HTTPException(status_code=500, detail=f"구글 인증 URL 생성 실패: {e}")
    
    @router.get("/callback")
    async def google_callback(code: str = None):
        """구글 OAuth 콜백 처리 (GET)"""
        print("========================================")
        print("[구글 콜백] GET 요청이 들어왔습니다!")
        print(f"쿼리 파라미터 - code: {code}")
        print("========================================")
        
        if not code:
            print("[구글 콜백] 에러: 인증 코드가 없습니다")
            error_msg = urlencode({"error": "인증 코드가 필요합니다"})
            return RedirectResponse(url=f"{google_properties.frontend_url}?{error_msg}")
        
        try:
            request = GoogleLoginRequest(authorization_code=code)
            login_response = await process_google_login(request)
            
            if login_response.success:
                print("[구글 콜백] 로그인 성공! 프론트엔드로 리다이렉트")
                redirect_url = (
                    f"{google_properties.frontend_url}/dashboard"
                    f"?token={login_response.token}"
                    f"&refreshToken={login_response.refresh_token}"
                    "&success=true"
                )
                return RedirectResponse(url=redirect_url)
            else:
                error_msg = urlencode({"error": login_response.message})
                return RedirectResponse(url=f"{google_properties.frontend_url}?{error_msg}")
        except Exception as e:
            print(f"[구글 콜백] 예외 발생: {e}")
            error_msg = urlencode({"error": "구글 로그인 처리 중 오류가 발생했습니다"})
            return RedirectResponse(url=f"{google_properties.frontend_url}?{error_msg}")
    
    @router.post("/login")
    async def google_login(request: GoogleLoginRequest):
        """구글 로그인 (POST)"""
        return await process_google_login(request)
    
    async def process_google_login(request: GoogleLoginRequest) -> LoginResponse:
        """구글 로그인 처리 공통 로직"""
        print("========================================")
        print("[구글 로그인] 요청이 들어왔습니다!")
        print(f"요청 데이터 - authorizationCode: {request.authorization_code}")
        print(f"요청 데이터 - accessToken: {request.access_token}")
        print("========================================")
        
        try:
            google_user_info: GoogleUserInfo
            
            # 1. 구글 사용자 정보 조회
            print("[구글 로그인] 1단계: 구글 사용자 정보 조회 시작")
            if request.authorization_code:
                google_user_info = google_auth_service.login_with_authorization_code(request.authorization_code)
            elif request.access_token:
                google_user_info = google_auth_service.login_with_access_token(request.access_token)
            else:
                return LoginResponse(
                    success=False,
                    message="인증 코드 또는 액세스 토큰이 필요합니다"
                )
            
            print("[구글 로그인] 1단계 완료: 구글 사용자 정보 조회 성공")
            
            # 2. 사용자 정보 추출
            print("[구글 로그인] 2단계: 사용자 정보 추출 시작")
            google_user_id = google_user_info.id
            email = google_user_info.email
            name = google_user_info.name
            
            # 구글 ID를 Long으로 변환
            try:
                user_id = int(google_user_id)
            except ValueError:
                user_id = abs(hash(google_user_id)) % (10**10)  # 해시코드를 숫자로 변환
            
            print(f"[구글 로그인] 추출된 사용자 정보 - ID: {user_id}, Email: {email}, Name: {name}")
            
            # 3. JWT 토큰 생성
            print("[구글 로그인] 3단계: JWT 토큰 생성 시작")
            access_token = jwt_token_provider.create_access_token(user_id, email, name)
            refresh_token = jwt_token_provider.create_refresh_token(user_id)
            print("[구글 로그인] 3단계 완료: JWT 토큰 생성 성공")
            
            # 4. 사용자 정보 맵 생성
            user = {
                "id": f"google_{google_user_id}",
                "email": email,
                "name": name
            }
            
            # 5. 응답 생성
            response = LoginResponse(
                success=True,
                message="구글 로그인 성공",
                user=user,
                token=access_token,
                refresh_token=refresh_token
            )
            
            print("========================================")
            print("[구글 로그인] ✅ 로그인 성공!")
            print(f"사용자 ID: {user_id}")
            print(f"이메일: {email}")
            print(f"이름: {name}")
            print("========================================")
            return response
            
        except Exception as e:
            print(f"구글 로그인 실패: {e}")
            return LoginResponse(
                success=False,
                message=f"구글 로그인 실패: {e}"
            )
    
    return router

