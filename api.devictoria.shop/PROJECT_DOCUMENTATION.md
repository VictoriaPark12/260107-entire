# 소셜 로그인 시스템 구현 가이드

> 카카오, 구글, 네이버 소셜 로그인을 통합한 마이크로서비스 아키텍처 구현 가이드

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [아키텍처 이해](#2-아키텍처-이해)
3. [프로젝트 구조](#3-프로젝트-구조)
4. [구현 과정](#4-구현-과정)
5. [주요 컴포넌트](#5-주요-컴포넌트)
6. [프론트엔드 연결](#6-프론트엔드-연결)
7. [환경 설정](#7-환경-설정)
8. [문제 해결](#8-문제-해결)

---

## 1. 프로젝트 개요

### 목표
- 카카오, 구글, 네이버 소셜 로그인 통합
- 프론트엔드에서 키 노출 없이 안전한 인증
- JWT 토큰 기반 인증 시스템

### 핵심 원칙
- **보안**: 모든 OAuth 키는 백엔드에서만 관리
- **재사용성**: 동일한 패턴으로 여러 소셜 로그인 구현
- **단순성**: 프론트엔드는 API만 호출하면 됨

---

## 2. 아키텍처 이해

### 전체 구조

```
프론트엔드 (3000) 
    ↓
API Gateway (8080) ← 모든 요청의 진입점
    ↓
Auth Service (8080) ← OAuth 처리 및 JWT 생성
    ↓
카카오/구글/네이버 API
```

### 왜 이렇게 구성했나?

**문제 상황**: 
- 프론트엔드에서 OAuth 키를 사용하면 보안 위험
- 여러 서비스를 하나의 진입점으로 관리하고 싶음

**해결책**:
- API Gateway가 모든 요청을 받아서 적절한 서비스로 라우팅
- Auth Service에서만 OAuth 키를 사용
- 프론트엔드는 단순히 API만 호출

### 서비스 역할

- **Gateway**: 요청 라우팅, CORS 처리
- **Auth Service**: OAuth 인증, JWT 토큰 생성
- **User Service**: 사용자 관리 (향후 확장)

---

## 3. 프로젝트 구조

```
api.devictoria.shop/
├── gateway/                    # API Gateway
│   └── src/main/resources/
│       └── application.yaml    # 라우팅 설정
│
├── services/
│   └── authservice/            # 인증 서비스
│       ├── src/main/java/
│       │   └── shop/devictoria/api/
│       │       ├── config/     # 설정 클래스
│       │       ├── kakao/     # 카카오 로그인
│       │       ├── google/    # 구글 로그인
│       │       ├── naver/     # 네이버 로그인
│       │       └── security/  # JWT 처리
│       └── src/main/resources/
│           └── application.yaml
│
└── docker-compose.yaml         # Docker 설정
```

---

## 4. 구현 과정

### 4.1 1단계: 기본 구조 설정

**상황**: 프로젝트 초기화 및 Docker 설정

**작업**:
1. Spring Boot 프로젝트 생성 (Gateway, Auth Service)
2. `docker-compose.yaml` 작성

**핵심 포인트**:
- Gateway: 외부 포트 8080
- Auth Service: 컨테이너 내부 8080, 외부 8081 (디버깅용)
- 서비스 간 통신은 컨테이너 이름 사용 (`authservice:8080`)

### 4.2 2단계: 카카오 로그인 구현

**상황**: 카카오 로그인 기능 추가

**작업 순서**:

1. **더미 구현** (API 구조 확인)
   ```java
   @PostMapping("/login")
   public ResponseEntity<LoginResponse> kakaoLogin() {
       return ResponseEntity.ok(LoginResponse.builder()
           .success(true)
           .message("카카오 로그인 성공")
           .build());
   }
   ```

2. **실제 카카오 API 연동**
   - `KakaoProperties`: 설정 관리
   - `KakaoService`: 카카오 API 호출
   - `KakaoController`: 인증 로직 처리
   - `JwtTokenProvider`: 토큰 생성

3. **OAuth 플로우 구현**
   ```
   프론트엔드 → GET /api/auth/kakao/start (인증 URL 요청)
   ↓
   백엔드 → 카카오 인증 URL 생성 및 반환
   ↓
   프론트엔드 → 카카오 인증 페이지로 이동
   ↓
   사용자 인증 완료
   ↓
   카카오 → GET /oauth2/kakao/callback?code=xxx
   ↓
   백엔드 → 토큰 요청 → 사용자 정보 조회 → JWT 생성
   ↓
   백엔드 → 프론트엔드로 리다이렉트 (토큰 포함)
   ```

### 4.3 3단계: API Gateway 라우팅

**상황**: Gateway가 요청을 Auth Service로 전달해야 함

**문제**: 
- 외부 요청: `/api/auth/kakao/start`
- Auth Service: `/kakao/start`
- 경로가 다름!

**해결**: `StripPrefix` 필터 사용

```yaml
# gateway/application.yaml
routes:
  - id: auth-service
    uri: http://authservice:8080
    predicates:
      - Path=/api/auth/**
    filters:
      - StripPrefix=2  # /api/auth 제거
```

**동작**:
- 요청: `GET /api/auth/kakao/start`
- Gateway 처리: `/api/auth` 제거
- Auth Service 수신: `GET /kakao/start`

**OAuth 콜백 라우팅**:
```yaml
- id: kakao-oauth-callback
  uri: http://authservice:8080
  predicates:
    - Path=/oauth2/kakao/callback/**
  filters:
    - RewritePath=/oauth2/kakao/callback, /kakao/callback
```

### 4.4 4단계: 보안 강화

**상황**: 프론트엔드에서 키를 사용하지 않도록 변경

**문제**: 
- 초기에는 프론트엔드에서 카카오 인증 URL을 직접 생성하려 했음
- 키가 노출될 위험

**해결**: 백엔드에서 인증 URL 생성 및 제공

```java
@GetMapping("/start")
public ResponseEntity<Map<String, String>> startKakaoLogin() {
    String kakaoAuthUrl = "https://kauth.kakao.com/oauth/authorize" +
        "?client_id=" + kakaoProperties.getRestApiKey() + ...;
    return ResponseEntity.ok(Map.of("authUrl", kakaoAuthUrl));
}
```

**프론트엔드**:
```javascript
const response = await fetch('/api/auth/kakao/start');
const { authUrl } = await response.json();
window.location.href = authUrl;
```

### 4.5 5단계: 구글/네이버 추가

**상황**: 카카오와 동일한 패턴으로 구글, 네이버 추가

**작업**: 카카오와 동일한 구조로 구현
- `GoogleController` / `NaverController`
- `GoogleService` / `NaverService`
- `GoogleProperties` / `NaverProperties`

**차이점**: 각 제공자별 API 차이는 서비스 레이어에서 처리

### 4.6 6단계: JWT 토큰 시스템

**상황**: 로그인 성공 후 토큰 발급

**구현**:
```java
public String createAccessToken(Long userId, String email, String nickname) {
    Map<String, Object> claims = new HashMap<>();
    claims.put("userId", userId);
    claims.put("email", email);
    claims.put("nickname", nickname);
    
    return Jwts.builder()
        .claims(claims)
        .subject(String.valueOf(userId))
        .issuedAt(new Date())
        .expiration(new Date(now.getTime() + expiration))
        .signWith(getSigningKey())
        .compact();
}
```

**주의사항**: JWT는 최소 32바이트 키 필요
```java
private SecretKey getSigningKey() {
    byte[] keyBytes = secret.getBytes(StandardCharsets.UTF_8);
    if (keyBytes.length < 32) {
        // 32바이트로 패딩
        byte[] paddedKey = new byte[32];
        for (int i = 0; i < 32; i++) {
            paddedKey[i] = keyBytes[i % keyBytes.length];
        }
        keyBytes = paddedKey;
    }
    return Keys.hmacShaKeyFor(keyBytes);
}
```

---

## 5. 주요 컴포넌트

### 5.1 KakaoController

**역할**: 카카오 로그인 요청 처리

**엔드포인트**:
- `GET /kakao/start`: 인증 URL 생성 및 반환
- `GET /kakao/callback`: OAuth 콜백 처리
- `POST /kakao/login`: 로그인 처리

**핵심 로직**:
```java
private ResponseEntity<LoginResponse> processKakaoLogin(KakaoLoginRequest request) {
    // 1. 카카오 사용자 정보 조회
    KakaoUserInfo userInfo = kakaoService.loginWithAuthorizationCode(code);
    
    // 2. 사용자 정보 추출
    Long userId = userInfo.getId();
    String email = userInfo.getKakaoAccount().getEmail();
    String nickname = userInfo.getKakaoAccount().getProfile().getNickname();
    
    // 3. JWT 토큰 생성
    String accessToken = jwtTokenProvider.createAccessToken(userId, email, nickname);
    String refreshToken = jwtTokenProvider.createRefreshToken(userId);
    
    // 4. 응답 생성
    return ResponseEntity.ok(LoginResponse.builder()
        .success(true)
        .token(accessToken)
        .refreshToken(refreshToken)
        .build());
}
```

### 5.2 KakaoService

**역할**: 카카오 API와의 통신

**주요 메서드**:
- `getKakaoToken()`: 인증 코드로 토큰 요청
- `getKakaoUserInfo()`: 액세스 토큰으로 사용자 정보 조회
- `loginWithAuthorizationCode()`: 전체 로그인 처리

**WebClient 사용**:
```java
WebClient webClient = webClientBuilder.build();

// 토큰 요청
KakaoTokenResponse response = webClient.post()
    .uri(kakaoProperties.getTokenUri())
    .contentType(MediaType.APPLICATION_FORM_URLENCODED)
    .bodyValue(formData)
    .retrieve()
    .bodyToMono(KakaoTokenResponse.class)
    .block();

// 사용자 정보 조회
KakaoUserInfo userInfo = webClient.get()
    .uri(kakaoProperties.getUserInfoUri())
    .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)
    .retrieve()
    .bodyToMono(KakaoUserInfo.class)
    .block();
```

### 5.3 JwtTokenProvider

**역할**: JWT 토큰 생성 및 검증

**주요 메서드**:
- `createAccessToken()`: Access Token 생성 (1시간)
- `createRefreshToken()`: Refresh Token 생성 (30일)
- `validateToken()`: 토큰 검증
- `getClaims()`: Claims 추출

### 5.4 Properties 클래스

**역할**: 설정 관리

```java
@ConfigurationProperties(prefix = "kakao")
@Component
public class KakaoProperties {
    private String restApiKey;
    private String redirectUri;
    private String frontendUrl;
    private String tokenUri;
    private String userInfoUri;
}
```

**application.yaml 연동**:
```yaml
kakao:
  rest-api-key: ${KAKAO_REST_API_KEY}
  redirect-uri: ${KAKAO_REDIRECT_URI}
  frontend-url: ${FRONTEND_URL:http://localhost:3000}
```

---

## 6. 프론트엔드 연결

### 6.1 로그인 버튼 클릭

```javascript
const handleKakaoLogin = async () => {
  try {
    // 1. 백엔드에서 인증 URL 받기
    const response = await fetch('http://localhost:8080/api/auth/kakao/start', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    
    // 2. 받은 URL로 리다이렉트
    if (data.authUrl) {
      window.location.href = data.authUrl;
    }
  } catch (error) {
    console.error('카카오 로그인 오류:', error);
  }
};
```

### 6.2 콜백 처리 (대시보드 페이지)

```javascript
useEffect(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token');
  const refreshToken = urlParams.get('refreshToken');
  const success = urlParams.get('success');
  const error = urlParams.get('error');
  
  if (success === 'true' && token) {
    // 로그인 성공
    localStorage.setItem('accessToken', token);
    localStorage.setItem('refreshToken', refreshToken);
    
    // URL 정리
    window.history.replaceState({}, document.title, '/dashboard');
  } else if (error) {
    // 로그인 실패
    alert('로그인 실패: ' + decodeURIComponent(error));
  }
}, []);
```

### 6.3 통합 로그인 핸들러

```javascript
const handleSocialLogin = async (provider) => {
  try {
    const endpoint = `http://localhost:8080/api/auth/${provider}/start`;
    
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    
    if (data.authUrl) {
      window.location.href = data.authUrl;
    } else {
      alert(`${provider} 로그인 시작 실패: ${data.error || '알 수 없는 오류'}`);
    }
  } catch (error) {
    console.error(`${provider} 로그인 오류:`, error);
    alert(`${provider} 로그인 중 오류가 발생했습니다.`);
  }
};

// 사용
<button onClick={() => handleSocialLogin('kakao')}>카카오 로그인</button>
<button onClick={() => handleSocialLogin('google')}>구글 로그인</button>
<button onClick={() => handleSocialLogin('naver')}>네이버 로그인</button>
```

### 중요 사항

✅ **프론트엔드에 필요한 것**:
- API 엔드포인트 URL만 알면 됨
- 환경 변수나 키 설정 **완전히 불필요**

❌ **프론트엔드에 불필요한 것**:
- 카카오 REST API 키
- 구글 Client ID/Secret
- 네이버 Client ID/Secret

---

## 7. 환경 설정

### 7.1 .env 파일 생성

```env
# 카카오
KAKAO_REST_API_KEY=your_kakao_rest_api_key
KAKAO_REDIRECT_URI=http://localhost:8080/oauth2/kakao/callback

# 구글
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8080/oauth2/google/callback

# 네이버
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
NAVER_REDIRECT_URI=http://localhost:8080/oauth2/naver/callback

# JWT
JWT_SECRET=your_jwt_secret_key_minimum_32_bytes
JWT_ACCESS_TOKEN_EXPIRATION=3600000
JWT_REFRESH_TOKEN_EXPIRATION=2592000000

# 프론트엔드
FRONTEND_URL=http://localhost:3000
```

### 7.2 docker-compose.yaml 연동

```yaml
authservice:
  environment:
    - KAKAO_REST_API_KEY=${KAKAO_REST_API_KEY}
    - KAKAO_REDIRECT_URI=${KAKAO_REDIRECT_URI}
    - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
    - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    - GOOGLE_REDIRECT_URI=${GOOGLE_REDIRECT_URI}
    - NAVER_CLIENT_ID=${NAVER_CLIENT_ID}
    - NAVER_CLIENT_SECRET=${NAVER_CLIENT_SECRET}
    - NAVER_REDIRECT_URI=${NAVER_REDIRECT_URI}
    - JWT_SECRET=${JWT_SECRET}
```

### 7.3 OAuth 제공자 설정

#### 카카오 개발자 콘솔
1. https://developers.kakao.com 접속
2. 애플리케이션 생성
3. **플랫폼 설정**: Web 플랫폼 추가 `http://localhost:3000`
4. **Redirect URI**: `http://localhost:8080/oauth2/kakao/callback`
5. **REST API 키 복사**

#### 구글 클라우드 콘솔
1. https://console.cloud.google.com 접속
2. 프로젝트 생성
3. OAuth 2.0 클라이언트 ID 생성
4. **승인된 리디렉션 URI**: `http://localhost:8080/oauth2/google/callback`
5. **Client ID 및 Secret 복사**

#### 네이버 개발자 센터
1. https://developers.naver.com 접속
2. 애플리케이션 등록
3. **서비스 URL**: `http://localhost:3000`
4. **Callback URL**: `http://localhost:8080/oauth2/naver/callback`
5. **Client ID 및 Secret 복사**

---

## 8. 문제 해결

### 8.1 Docker 빌드 오류

**문제**: `Configuring project ':services:auth-service' without an existing directory is not allowed.`

**원인**: `gateway/settings.gradle`에 다른 서비스 모듈이 포함되어 있음

**해결**: 
```gradle
// gateway/settings.gradle
rootProject.name = 'gateway'
// ❌ 제거: include 'services:auth-service'
```

### 8.2 포트 연결 오류

**문제**: `Connection refused: authservice/172.18.0.2:8081`

**원인**: Gateway가 `authservice:8081`로 연결 시도하지만, Auth Service는 컨테이너 내부에서 8080 포트 사용

**해결**:
```yaml
# gateway/application.yaml
routes:
  - id: auth-service
    uri: http://authservice:8080  # ✅ 컨테이너 내부 포트 사용
```

```yaml
# docker-compose.yaml
authservice:
  ports:
    - "8081:8080"  # 호스트 8081 → 컨테이너 8080
```

### 8.3 JWT 라이브러리 버전 호환성

**문제**: `cannot find symbol Jwts.parserBuilder()`

**원인**: JJWT 라이브러리 버전 변경으로 API 변경

**해결**:
```java
// ❌ 구버전
Jwts.parserBuilder()
    .setSigningKey(key)
    .build()
    .parseClaimsJws(token);

// ✅ 신버전
Jwts.parser()
    .verifyWith(key)
    .build()
    .parseSignedClaims(token);
```

### 8.4 JWT Secret 길이 문제

**문제**: `JWT secret key must be at least 256 bits (32 bytes)`

**해결**: 키 길이가 32바이트 미만이면 패딩 처리
```java
private SecretKey getSigningKey() {
    byte[] keyBytes = secret.getBytes(StandardCharsets.UTF_8);
    if (keyBytes.length < 32) {
        byte[] paddedKey = new byte[32];
        for (int i = 0; i < 32; i++) {
            paddedKey[i] = keyBytes[i % keyBytes.length];
        }
        keyBytes = paddedKey;
    }
    return Keys.hmacShaKeyFor(keyBytes);
}
```

### 8.5 redirect_uri_mismatch 오류

**문제**: `redirect_uri_mismatch: The redirect URI in the request does not match...`

**원인**: OAuth 제공자 콘솔에 등록된 리다이렉트 URI와 백엔드 설정이 불일치

**해결**:
1. OAuth 제공자 콘솔에서 정확한 URI 확인
2. `.env` 파일의 `REDIRECT_URI` 확인
3. 정확히 일치하도록 수정

### 8.6 프론트엔드에서 로그인 화면이 안 뜨는 문제

**문제**: 로그인 버튼 클릭 시 대시보드로 바로 이동

**원인**: 프론트엔드에서 `/start` 엔드포인트를 호출하지 않고 직접 OAuth URL로 이동 시도

**해결**:
```javascript
// ❌ 잘못된 방식
window.location.href = 'https://kauth.kakao.com/oauth/authorize?...';

// ✅ 올바른 방식
const response = await fetch('/api/auth/kakao/start');
const { authUrl } = await response.json();
window.location.href = authUrl;
```

---

## 실행 방법

### 1. 환경 변수 설정
```bash
# .env 파일 생성 및 변수 설정
cp .env.example .env
# .env 파일 편집
```

### 2. Docker Compose 실행
```bash
# 빌드 및 실행
docker-compose up --build -d

# 로그 확인
docker-compose logs -f authservice
docker-compose logs -f gateway

# 서비스 중지
docker-compose down
```

### 3. API 테스트
```bash
# 카카오 로그인 시작
curl http://localhost:8080/api/auth/kakao/start
```

---

## 핵심 요약

### 설계 원칙
1. **보안**: 모든 키는 백엔드에서만 관리
2. **재사용성**: 동일한 패턴으로 여러 소셜 로그인 구현
3. **확장성**: 마이크로서비스 아키텍처로 서비스 독립적 확장

### 구현 패턴
1. **Controller**: 요청 처리 및 응답 생성
2. **Service**: 외부 API 호출 및 비즈니스 로직
3. **Provider**: 공통 기능 (JWT, WebClient 등)
4. **Properties**: 설정 관리

### 플로우
1. 프론트엔드 → `/start` 엔드포인트 호출
2. 백엔드 → 인증 URL 생성 및 반환
3. 프론트엔드 → OAuth 제공자로 리다이렉트
4. OAuth 제공자 → 콜백으로 인증 코드 전달
5. 백엔드 → 토큰 요청 → 사용자 정보 조회 → JWT 생성
6. 백엔드 → 프론트엔드로 리다이렉트 (토큰 포함)

---

**작성일**: 2024년  
**버전**: 1.0
