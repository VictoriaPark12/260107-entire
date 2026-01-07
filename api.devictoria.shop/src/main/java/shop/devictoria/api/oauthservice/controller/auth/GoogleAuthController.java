package shop.devictoria.api.controller.auth;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.view.RedirectView;
import shop.devictoria.api.config.GoogleProperties;
import shop.devictoria.api.dto.auth.GoogleLoginRequest;
import shop.devictoria.api.dto.auth.LoginResponse;
import shop.devictoria.api.dto.auth.provider.GoogleUserInfo;
import shop.devictoria.api.security.JwtTokenProvider;
import shop.devictoria.api.service.auth.provider.GoogleAuthService;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequiredArgsConstructor
@RequestMapping("/google")
@CrossOrigin(origins = {"http://localhost:3000", "http://localhost:5000"}, allowCredentials = "true")
public class GoogleAuthController {
    
    private final GoogleAuthService googleAuthService;
    private final JwtTokenProvider jwtTokenProvider;
    private final GoogleProperties googleProperties;
    
    /**
     * 구글 로그인 시작 (GET)
     * 프론트엔드에서 이 엔드포인트를 호출하면 구글 인증 URL을 반환
     * 프론트엔드는 키를 알 필요 없이 이 API만 호출하면 됨
     */
    @GetMapping("/start")
    public ResponseEntity<Map<String, String>> startGoogleLogin() {
        System.out.println("[구글 로그인 시작] 요청이 들어왔습니다");
        
        try {
            // 구글 인증 URL 생성 (백엔드에서 키를 사용)
            String redirectUri = URLEncoder.encode(googleProperties.getRedirectUri(), StandardCharsets.UTF_8);
            String googleAuthUrl = "https://accounts.google.com/o/oauth2/v2/auth" +
                    "?client_id=" + googleProperties.getClientId() +
                    "&redirect_uri=" + redirectUri +
                    "&response_type=code" +
                    "&scope=openid email profile";
            
            System.out.println("[구글 로그인 시작] 생성된 인증 URL: " + googleAuthUrl);
            
            Map<String, String> response = new HashMap<>();
            response.put("authUrl", googleAuthUrl);
            response.put("message", "구글 인증 URL이 생성되었습니다");
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            System.out.println("[구글 로그인 시작] 에러: " + e.getMessage());
            e.printStackTrace();
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("error", "구글 인증 URL 생성 실패: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
    
    /**
     * 구글 OAuth 콜백 처리 (GET)
     * 구글 인증 후 이 엔드포인트로 리다이렉트됨
     * 로그인 처리 후 프론트엔드로 리다이렉트
     */
    @GetMapping("/callback")
    public RedirectView googleCallback(@RequestParam(required = false) String code) {
        System.out.println("========================================");
        System.out.println("[구글 콜백] GET 요청이 들어왔습니다!");
        System.out.println("쿼리 파라미터 - code: " + (code != null ? code : "null"));
        System.out.println("========================================");
        
        if (code == null || code.isEmpty()) {
            System.out.println("[구글 콜백] 에러: 인증 코드가 없습니다");
            // 에러 시 프론트엔드로 리다이렉트 (에러 파라미터 포함)
            return new RedirectView(googleProperties.getFrontendUrl() + "?error=인증 코드가 필요합니다");
        }
        
        try {
            // POST 엔드포인트와 동일한 로직 사용
            GoogleLoginRequest request = new GoogleLoginRequest();
            request.setAuthorizationCode(code);
            
            ResponseEntity<LoginResponse> loginResponse = processGoogleLogin(request);
            LoginResponse response = loginResponse.getBody();
            
            if (response != null && response.getSuccess()) {
                System.out.println("[구글 콜백] 로그인 성공! 프론트엔드로 리다이렉트");
                System.out.println("========================================");
                System.out.println("[구글 콜백] 프론트엔드로 반환할 JWT 토큰:");
                System.out.println("JWT Access Token: " + response.getToken());
                System.out.println("JWT Refresh Token: " + response.getRefreshToken());
                System.out.println("(구글 토큰은 Redis에 저장됨)");
                System.out.println("========================================");
                // 성공 시 프론트엔드로 리다이렉트하면서 토큰 전달
                String redirectUrl = googleProperties.getFrontendUrl() + 
                    "/home?token=" + URLEncoder.encode(response.getToken(), StandardCharsets.UTF_8) +
                    "&refreshToken=" + URLEncoder.encode(response.getRefreshToken(), StandardCharsets.UTF_8) +
                    "&success=true";
                return new RedirectView(redirectUrl);
            } else {
                // 실패 시 프론트엔드로 리다이렉트 (에러 메시지 포함)
                String errorMessage = response != null ? response.getMessage() : "로그인 실패";
                return new RedirectView(googleProperties.getFrontendUrl() + "?error=" + 
                    URLEncoder.encode(errorMessage, StandardCharsets.UTF_8));
            }
        } catch (Exception e) {
            System.out.println("[구글 콜백] 예외 발생: " + e.getMessage());
            e.printStackTrace();
            // 예외 발생 시 프론트엔드로 리다이렉트 (에러 메시지 포함)
            return new RedirectView(googleProperties.getFrontendUrl() + "?error=" + 
                URLEncoder.encode("구글 로그인 처리 중 오류가 발생했습니다", StandardCharsets.UTF_8));
        }
    }
    
    /**
     * 구글 로그인 (POST)
     * - authorizationCode가 있으면: 구글 토큰 요청 → 사용자 정보 조회
     * - accessToken이 있으면: 바로 사용자 정보 조회
     */
    @PostMapping("/login")
    public ResponseEntity<LoginResponse> googleLogin(@RequestBody GoogleLoginRequest request) {
        return processGoogleLogin(request);
    }
    
    /**
     * 구글 로그인 처리 공통 로직
     */
    private ResponseEntity<LoginResponse> processGoogleLogin(GoogleLoginRequest request) {
        System.out.println("========================================");
        System.out.println("[구글 로그인] 요청이 들어왔습니다!");
        System.out.println("요청 데이터 - authorizationCode: " + (request.getAuthorizationCode() != null ? request.getAuthorizationCode() : "null"));
        System.out.println("요청 데이터 - accessToken: " + (request.getAccessToken() != null ? request.getAccessToken() : "null"));
        System.out.println("요청 데이터 - email: " + (request.getEmail() != null ? request.getEmail() : "null"));
        System.out.println("요청 데이터 - name: " + (request.getName() != null ? request.getName() : "null"));
        System.out.println("========================================");
        
        try {
            GoogleUserInfo googleUserInfo;
            
            // 1. 구글 사용자 정보 조회
            System.out.println("[구글 로그인] 1단계: 구글 사용자 정보 조회 시작");
            if (request.getAuthorizationCode() != null && !request.getAuthorizationCode().isEmpty()) {
                // 인증 코드로 로그인
                System.out.println("[구글 로그인] 인증 코드로 구글 로그인 시도");
                googleUserInfo = googleAuthService.loginWithAuthorizationCode(request.getAuthorizationCode());
            } else if (request.getAccessToken() != null && !request.getAccessToken().isEmpty()) {
                // 액세스 토큰으로 로그인
                System.out.println("[구글 로그인] 액세스 토큰으로 구글 로그인 시도");
                googleUserInfo = googleAuthService.loginWithAccessToken(request.getAccessToken());
            } else {
                System.out.println("[구글 로그인] 에러: 인증 코드 또는 액세스 토큰이 필요합니다");
                return ResponseEntity.badRequest()
                        .body(LoginResponse.builder()
                                .success(false)
                                .message("인증 코드 또는 액세스 토큰이 필요합니다")
                                .build());
            }
            
            System.out.println("[구글 로그인] 1단계 완료: 구글 사용자 정보 조회 성공");
            
            // 2. 사용자 정보 추출
            System.out.println("[구글 로그인] 2단계: 사용자 정보 추출 시작");
            String googleUserId = googleUserInfo.getId();
            String email = googleUserInfo.getEmail();
            String name = googleUserInfo.getName();
            
            // 구글 ID를 Long으로 변환 (숫자 문자열인 경우)
            Long userId = null;
            try {
                userId = Long.parseLong(googleUserId);
            } catch (NumberFormatException e) {
                // 숫자가 아닌 경우 해시코드 사용
                userId = (long) googleUserId.hashCode();
            }
            
            System.out.println("[구글 로그인] 추출된 사용자 정보 - ID: " + userId + ", Email: " + email + ", Name: " + name);
            
            // 3. JWT 토큰 생성
            System.out.println("[구글 로그인] 3단계: JWT 토큰 생성 시작");
            String accessToken = jwtTokenProvider.createAccessToken(userId, email, name);
            String refreshToken = jwtTokenProvider.createRefreshToken(userId);
            System.out.println("[구글 로그인] 3단계 완료: JWT 토큰 생성 성공");
            
            // 4. 사용자 정보 맵 생성
            System.out.println("[구글 로그인] 4단계: 사용자 정보 맵 생성");
            Map<String, Object> user = new HashMap<>();
            user.put("id", "google_" + googleUserId);
            user.put("email", email);
            user.put("name", name);
            
            // 5. 응답 생성
            System.out.println("[구글 로그인] 5단계: 응답 생성");
            LoginResponse response = LoginResponse.builder()
                    .success(true)
                    .message("구글 로그인 성공")
                    .user(user)
                    .token(accessToken)
                    .refreshToken(refreshToken)
                    .build();
            
            System.out.println("========================================");
            System.out.println("[구글 로그인] ✅ 로그인 성공!");
            System.out.println("사용자 ID: " + userId);
            System.out.println("이메일: " + email);
            System.out.println("이름: " + name);
            System.out.println("--- JWT 토큰 (프론트엔드로 반환) ---");
            System.out.println("JWT Access Token: " + accessToken);
            System.out.println("JWT Refresh Token: " + refreshToken);
            System.out.println("--- 구글 토큰은 Redis에 저장됨 ---");
            System.out.println("========================================");
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            System.out.println("구글 로그인 실패: " + e.getMessage());
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(LoginResponse.builder()
                            .success(false)
                            .message("구글 로그인 실패: " + e.getMessage())
                            .build());
        }
    }
}

