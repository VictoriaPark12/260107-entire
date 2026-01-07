"""
카카오 인증 컨트롤러
"""
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.config import KakaoProperties
from app.dto.auth import KakaoLoginRequest, LoginResponse
from app.dto.provider import KakaoUserInfo
from app.security.jwt_provider import JwtTokenProvider
from app.services.kakao_auth_service import KakaoAuthService

router = APIRouter(prefix="/kakao", tags=["kakao"])


def create_kakao_router(
    kakao_properties: KakaoProperties,
    kakao_auth_service: KakaoAuthService,
    jwt_token_provider: JwtTokenProvider
):
    """카카오 라우터 생성"""
    
    @router.get("/start")
    async def start_kakao_login():
        """카카오 로그인 시작 (GET)"""
        print("[카카오 로그인 시작] 요청이 들어왔습니다")
        
        try:
            # 카카오 인증 URL 생성
            redirect_uri = kakao_properties.redirect_uri
            kakao_auth_url = (
                "https://kauth.kakao.com/oauth/authorize"
                f"?client_id={kakao_properties.rest_api_key}"
                f"&redirect_uri={redirect_uri}"
                "&response_type=code"
            )
            
            print(f"[카카오 로그인 시작] 생성된 인증 URL: {kakao_auth_url}")
            
            return {
                "authUrl": kakao_auth_url,
                "message": "카카오 인증 URL이 생성되었습니다"
            }
        except Exception as e:
            print(f"[카카오 로그인 시작] 에러: {e}")
            raise HTTPException(status_code=500, detail=f"카카오 인증 URL 생성 실패: {e}")
    
    @router.get("/callback")
    async def kakao_callback(code: str = None):
        """카카오 OAuth 콜백 처리 (GET)"""
        print("========================================")
        print("[카카오 콜백] GET 요청이 들어왔습니다!")
        print(f"쿼리 파라미터 - code: {code}")
        print("========================================")
        
        if not code:
            print("[카카오 콜백] 에러: 인증 코드가 없습니다")
            error_msg = urlencode({"error": "인증 코드가 필요합니다"})
            return RedirectResponse(url=f"{kakao_properties.frontend_url}?{error_msg}")
        
        try:
            # POST 엔드포인트와 동일한 로직 사용
            request = KakaoLoginRequest(authorization_code=code)
            login_response = await process_kakao_login(request)
            
            if login_response.success:
                print("[카카오 콜백] 로그인 성공! 프론트엔드로 리다이렉트")
                print("========================================")
                print(f"[카카오 콜백] 프론트엔드로 반환할 JWT 토큰:")
                print(f"JWT Access Token: {login_response.token}")
                print(f"JWT Refresh Token: {login_response.refresh_token}")
                print("(카카오 토큰은 Redis에 저장됨)")
                print("========================================")
                
                # 성공 시 프론트엔드로 리다이렉트하면서 토큰 전달
                redirect_url = (
                    f"{kakao_properties.frontend_url}/dashboard"
                    f"?token={login_response.token}"
                    f"&refreshToken={login_response.refresh_token}"
                    "&success=true"
                )
                return RedirectResponse(url=redirect_url)
            else:
                # 실패 시 프론트엔드로 리다이렉트
                error_msg = urlencode({"error": login_response.message})
                return RedirectResponse(url=f"{kakao_properties.frontend_url}?{error_msg}")
        except Exception as e:
            print(f"[카카오 콜백] 예외 발생: {e}")
            error_msg = urlencode({"error": "카카오 로그인 처리 중 오류가 발생했습니다"})
            return RedirectResponse(url=f"{kakao_properties.frontend_url}?{error_msg}")
    
    @router.post("/login")
    async def kakao_login(request: KakaoLoginRequest):
        """카카오 로그인 (POST)"""
        return await process_kakao_login(request)
    
    async def process_kakao_login(request: KakaoLoginRequest) -> LoginResponse:
        """카카오 로그인 처리 공통 로직"""
        print("========================================")
        print("[카카오 로그인] 요청이 들어왔습니다!")
        print(f"요청 데이터 - authorizationCode: {request.authorization_code}")
        print(f"요청 데이터 - accessToken: {request.access_token}")
        print("========================================")
        
        try:
            kakao_user_info: KakaoUserInfo
            
            # 1. 카카오 사용자 정보 조회
            print("[카카오 로그인] 1단계: 카카오 사용자 정보 조회 시작")
            if request.authorization_code:
                # 인증 코드로 로그인
                print("[카카오 로그인] 인증 코드로 카카오 로그인 시도")
                kakao_user_info = kakao_auth_service.login_with_authorization_code(request.authorization_code)
            elif request.access_token:
                # 액세스 토큰으로 로그인
                print("[카카오 로그인] 액세스 토큰으로 카카오 로그인 시도")
                kakao_user_info = kakao_auth_service.login_with_access_token(request.access_token)
            else:
                print("[카카오 로그인] 에러: 인증 코드 또는 액세스 토큰이 필요합니다")
                return LoginResponse(
                    success=False,
                    message="인증 코드 또는 액세스 토큰이 필요합니다"
                )
            
            print("[카카오 로그인] 1단계 완료: 카카오 사용자 정보 조회 성공")
            
            # 2. 사용자 정보 추출
            print("[카카오 로그인] 2단계: 사용자 정보 추출 시작")
            kakao_user_id = kakao_user_info.id
            email = kakao_user_info.kakao_account.email if kakao_user_info.kakao_account else None
            nickname = (
                kakao_user_info.kakao_account.profile.nickname
                if kakao_user_info.kakao_account and kakao_user_info.kakao_account.profile
                else None
            )
            
            print(f"[카카오 로그인] 추출된 사용자 정보 - ID: {kakao_user_id}, Email: {email}, Nickname: {nickname}")
            
            # 3. JWT 토큰 생성
            print("[카카오 로그인] 3단계: JWT 토큰 생성 시작")
            access_token = jwt_token_provider.create_access_token(kakao_user_id, email, nickname)
            refresh_token = jwt_token_provider.create_refresh_token(kakao_user_id)
            print("[카카오 로그인] 3단계 완료: JWT 토큰 생성 성공")
            
            # 4. 사용자 정보 맵 생성
            print("[카카오 로그인] 4단계: 사용자 정보 맵 생성")
            user = {
                "id": f"kakao_{kakao_user_id}",
                "email": email,
                "name": nickname
            }
            
            # 5. 응답 생성
            print("[카카오 로그인] 5단계: 응답 생성")
            response = LoginResponse(
                success=True,
                message="카카오 로그인 성공",
                user=user,
                token=access_token,
                refresh_token=refresh_token
            )
            
            print("========================================")
            print("[카카오 로그인] ✅ 로그인 성공!")
            print(f"사용자 ID: {kakao_user_id}")
            print(f"이메일: {email}")
            print(f"닉네임: {nickname}")
            print("--- JWT 토큰 (프론트엔드로 반환) ---")
            print(f"JWT Access Token: {access_token}")
            print(f"JWT Refresh Token: {refresh_token}")
            print("--- 카카오 토큰은 Redis에 저장됨 ---")
            print("========================================")
            return response
            
        except Exception as e:
            print(f"카카오 로그인 실패: {e}")
            return LoginResponse(
                success=False,
                message=f"카카오 로그인 실패: {e}"
            )
    
    return router

