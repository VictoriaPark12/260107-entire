"""
네이버 인증 컨트롤러
"""
import uuid
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.config import NaverProperties
from app.dto.auth import NaverLoginRequest, LoginResponse
from app.dto.provider import NaverUserInfo
from app.security.jwt_provider import JwtTokenProvider
from app.services.naver_auth_service import NaverAuthService

router = APIRouter(prefix="/naver", tags=["naver"])


def create_naver_router(
    naver_properties: NaverProperties,
    naver_auth_service: NaverAuthService,
    jwt_token_provider: JwtTokenProvider
):
    """네이버 라우터 생성"""
    
    @router.get("/start")
    async def start_naver_login():
        """네이버 로그인 시작 (GET)"""
        print("[네이버 로그인 시작] 요청이 들어왔습니다")
        
        try:
            # 네이버 인증 URL 생성
            redirect_uri = naver_properties.redirect_uri
            state = str(uuid.uuid4())  # CSRF 방지를 위한 state 값
            naver_auth_url = (
                "https://nid.naver.com/oauth2.0/authorize"
                "?response_type=code"
                f"&client_id={naver_properties.client_id}"
                f"&redirect_uri={redirect_uri}"
                f"&state={state}"
            )
            
            print(f"[네이버 로그인 시작] 생성된 인증 URL: {naver_auth_url}")
            
            return {
                "authUrl": naver_auth_url,
                "message": "네이버 인증 URL이 생성되었습니다"
            }
        except Exception as e:
            print(f"[네이버 로그인 시작] 에러: {e}")
            raise HTTPException(status_code=500, detail=f"네이버 인증 URL 생성 실패: {e}")
    
    @router.get("/callback")
    async def naver_callback(code: str = None, state: str = None):
        """네이버 OAuth 콜백 처리 (GET)"""
        print("========================================")
        print("[네이버 콜백] GET 요청이 들어왔습니다!")
        print(f"쿼리 파라미터 - code: {code}")
        print(f"쿼리 파라미터 - state: {state}")
        print("========================================")
        
        if not code:
            print("[네이버 콜백] 에러: 인증 코드가 없습니다")
            error_msg = urlencode({"error": "인증 코드가 필요합니다"})
            return RedirectResponse(url=f"{naver_properties.frontend_url}?{error_msg}")
        
        try:
            request = NaverLoginRequest(authorization_code=code)
            login_response = await process_naver_login(request, state)
            
            if login_response.success:
                print("[네이버 콜백] 로그인 성공! 프론트엔드로 리다이렉트")
                redirect_url = (
                    f"{naver_properties.frontend_url}/dashboard"
                    f"?token={login_response.token}"
                    f"&refreshToken={login_response.refresh_token}"
                    "&success=true"
                )
                return RedirectResponse(url=redirect_url)
            else:
                error_msg = urlencode({"error": login_response.message})
                return RedirectResponse(url=f"{naver_properties.frontend_url}?{error_msg}")
        except Exception as e:
            print(f"[네이버 콜백] 예외 발생: {e}")
            error_msg = urlencode({"error": "네이버 로그인 처리 중 오류가 발생했습니다"})
            return RedirectResponse(url=f"{naver_properties.frontend_url}?{error_msg}")
    
    @router.post("/login")
    async def naver_login(request: NaverLoginRequest):
        """네이버 로그인 (POST)"""
        return await process_naver_login(request)
    
    async def process_naver_login(request: NaverLoginRequest, state: str = None) -> LoginResponse:
        """네이버 로그인 처리 공통 로직"""
        print("========================================")
        print("[네이버 로그인] 요청이 들어왔습니다!")
        print(f"요청 데이터 - authorizationCode: {request.authorization_code}")
        print(f"요청 데이터 - accessToken: {request.access_token}")
        print("========================================")
        
        try:
            naver_user_info: NaverUserInfo
            
            # 1. 네이버 사용자 정보 조회
            print("[네이버 로그인] 1단계: 네이버 사용자 정보 조회 시작")
            if request.authorization_code:
                naver_user_info = naver_auth_service.login_with_authorization_code(request.authorization_code, state)
            elif request.access_token:
                naver_user_info = naver_auth_service.login_with_access_token(request.access_token)
            else:
                return LoginResponse(
                    success=False,
                    message="인증 코드 또는 액세스 토큰이 필요합니다"
                )
            
            print("[네이버 로그인] 1단계 완료: 네이버 사용자 정보 조회 성공")
            
            # 2. 사용자 정보 추출
            print("[네이버 로그인] 2단계: 사용자 정보 추출 시작")
            if not naver_user_info.response:
                raise RuntimeError("네이버 사용자 정보가 없습니다")
            
            response_data = naver_user_info.response
            naver_user_id = response_data.id
            email = response_data.email
            name = response_data.name
            nickname = response_data.nickname if response_data.nickname else name
            
            # 네이버 ID를 Long으로 변환
            try:
                user_id = int(naver_user_id)
            except ValueError:
                user_id = abs(hash(naver_user_id)) % (10**10)
            
            print(f"[네이버 로그인] 추출된 사용자 정보 - ID: {user_id}, Email: {email}, Name: {name}, Nickname: {nickname}")
            
            # 3. JWT 토큰 생성
            print("[네이버 로그인] 3단계: JWT 토큰 생성 시작")
            access_token = jwt_token_provider.create_access_token(user_id, email, nickname)
            refresh_token = jwt_token_provider.create_refresh_token(user_id)
            print("[네이버 로그인] 3단계 완료: JWT 토큰 생성 성공")
            
            # 4. 사용자 정보 맵 생성
            user = {
                "id": f"naver_{naver_user_id}",
                "email": email,
                "name": nickname
            }
            
            # 5. 응답 생성
            response = LoginResponse(
                success=True,
                message="네이버 로그인 성공",
                user=user,
                token=access_token,
                refresh_token=refresh_token
            )
            
            print("========================================")
            print("[네이버 로그인] ✅ 로그인 성공!")
            print(f"사용자 ID: {user_id}")
            print(f"이메일: {email}")
            print(f"이름: {name}")
            print(f"닉네임: {nickname}")
            print("========================================")
            return response
            
        except Exception as e:
            print(f"네이버 로그인 실패: {e}")
            return LoginResponse(
                success=False,
                message=f"네이버 로그인 실패: {e}"
            )
    
    return router

