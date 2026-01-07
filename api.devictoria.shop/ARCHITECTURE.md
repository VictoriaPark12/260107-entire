# 시스템 아키텍처

## 개요

마이크로서비스 기반의 소셜 로그인 인증 시스템으로, Spring Cloud Gateway를 통한 API 라우팅과 분리된 서비스 구조를 제공합니다.

## 아키텍처 다이어그램

```
┌─────────────┐
│  Frontend   │
│  (Port 3000)│
└──────┬──────┘
       │
       │ HTTP Request
       ▼
┌─────────────────────────────────┐
│   API Gateway (Port 8080)       │
│   Spring Cloud Gateway          │
│   - 라우팅                      │
│   - CORS 처리                   │
└──────┬──────────────────────────┘
       │
       ├─────────────────┬─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│Auth Service │  │User Service │  │  Redis      │
│(Port 8081)  │  │(Port 8082)  │  │(Port 6379)  │
│             │  │             │  │             │
│- OAuth 인증 │  │- 사용자 관리 │  │- 토큰 저장  │
│- JWT 생성   │  │             │  │             │
└──────┬──────┘  └─────────────┘  └─────────────┘
       │
       ├──────────┬──────────┬──────────┐
       │          │          │          │
       ▼          ▼          ▼          ▼
  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
  │카카오│  │구글  │  │네이버│  │기타  │
  └──────┘  └──────┘  └──────┘  └──────┘
```

## 서비스 구성

### 1. API Gateway
- **기술**: Spring Cloud Gateway
- **포트**: 8080
- **역할**:
  - 모든 외부 요청의 진입점
  - 서비스별 라우팅 (`/api/auth/**` → Auth Service)
  - OAuth 콜백 라우팅 (`/oauth2/*/callback` → Auth Service)
  - CORS 처리

### 2. Auth Service
- **기술**: Spring Boot 3.5.7, Java 21
- **포트**: 8081 (외부), 8080 (컨테이너 내부)
- **역할**:
  - 소셜 로그인 처리 (카카오, 구글, 네이버)
  - OAuth 2.0 플로우 관리
  - JWT 토큰 생성 및 검증
  - Redis 연동 (토큰 저장)

### 3. User Service
- **기술**: Spring Boot 3.5.7, Java 21
- **포트**: 8082
- **역할**:
  - 사용자 정보 관리
  - 향후 확장 예정

### 4. Redis
- **이미지**: redis:7-alpine
- **포트**: 6379
- **역할**:
  - Refresh Token 저장
  - 세션 관리

## 기술 스택

### Backend
- **프레임워크**: Spring Boot 3.5.7
- **언어**: Java 21
- **빌드 도구**: Gradle
- **API Gateway**: Spring Cloud Gateway
- **인증**: JWT (jjwt 0.12.3)
- **HTTP 클라이언트**: WebFlux WebClient
- **캐시/세션**: Redis

### Infrastructure
- **컨테이너화**: Docker
- **오케스트레이션**: Docker Compose
- **네트워크**: Bridge Network (spring-network)

## 데이터 흐름

### 소셜 로그인 플로우

```
1. Frontend → GET /api/auth/{provider}/start
   ↓
2. Gateway → Auth Service (/start)
   ↓
3. Auth Service → OAuth 인증 URL 생성 및 반환
   ↓
4. Frontend → OAuth 제공자 인증 페이지로 리다이렉트
   ↓
5. 사용자 인증 완료
   ↓
6. OAuth 제공자 → GET /oauth2/{provider}/callback?code=xxx
   ↓
7. Gateway → Auth Service (/callback)
   ↓
8. Auth Service → 토큰 교환 → 사용자 정보 조회 → JWT 생성
   ↓
9. Auth Service → Frontend로 리다이렉트 (토큰 포함)
```

## 프로젝트 구조

```
api.devictoria.shop/
├── gateway/                    # API Gateway 서비스
│   ├── src/main/java/
│   │   └── shop/devictoria/api/
│   │       └── ApiApplication.java
│   └── src/main/resources/
│       └── application.yaml    # 라우팅 설정
│
├── services/
│   ├── authservice/            # 인증 서비스
│   │   ├── src/main/java/
│   │   │   └── shop/devictoria/api/
│   │   │       ├── config/     # 설정 클래스
│   │   │       ├── google/     # 구글 로그인
│   │   │       ├── kakao/      # 카카오 로그인
│   │   │       ├── naver/      # 네이버 로그인
│   │   │       └── security/   # JWT 처리
│   │   └── src/main/resources/
│   │       └── application.yaml
│   │
│   └── userservice/             # 사용자 서비스
│       └── src/main/java/
│           └── shop/devictoria/api/
│               └── ApiApplication.java
│
├── docker-compose.yaml          # 서비스 오케스트레이션
├── build.gradle                 # 루트 빌드 설정
└── settings.gradle              # 프로젝트 설정
```

## 주요 컴포넌트

### Auth Service

#### Controller Layer
- `KakaoController`, `GoogleController`, `NaverController`
  - `/start`: 인증 URL 생성
  - `/callback`: OAuth 콜백 처리
  - `/login`: 로그인 처리

#### Service Layer
- `KakaoService`, `GoogleService`, `NaverService`
  - OAuth 제공자 API 통신
  - 토큰 교환 및 사용자 정보 조회

#### Security Layer
- `JwtTokenProvider`
  - Access Token 생성 (1시간)
  - Refresh Token 생성 (30일)
  - 토큰 검증

#### Config Layer
- `KakaoProperties`, `GoogleProperties`, `NaverProperties`
  - OAuth 설정 관리
- `RedisConfig`
  - Redis 연결 설정
- `WebClientConfig`
  - HTTP 클라이언트 설정

## 네트워크 구성

### Docker Network
- **네트워크명**: spring-network
- **타입**: Bridge
- **서비스 간 통신**: 컨테이너 이름 사용 (예: `authservice:8080`)

### 포트 매핑
- Gateway: `8080:8080`
- Auth Service: `8081:8080` (외부:내부)
- User Service: `8082:8082`
- Redis: `6379:6379`

## 보안 설계

### 원칙
1. **OAuth 키 보호**: 모든 OAuth 키는 백엔드에서만 관리
2. **JWT 기반 인증**: Stateless 인증 방식
3. **HTTPS 권장**: 프로덕션 환경에서는 HTTPS 필수

### 토큰 관리
- Access Token: 짧은 수명 (1시간)
- Refresh Token: 긴 수명 (30일), Redis 저장
- JWT Secret: 최소 32바이트

## 확장성

### 수평 확장
- 각 서비스는 독립적으로 스케일 아웃 가능
- Gateway의 Load Balancer를 통한 로드 분산

### 서비스 추가
- 새로운 소셜 로그인 제공자 추가 시 동일한 패턴 적용
- User Service에 비즈니스 로직 확장 가능

## 실행 방법

```bash
# 환경 변수 설정 (.env 파일)
KAKAO_REST_API_KEY=...
GOOGLE_CLIENT_ID=...
NAVER_CLIENT_ID=...
JWT_SECRET=...

# 서비스 실행
docker-compose up --build -d

# 로그 확인
docker-compose logs -f authservice
docker-compose logs -f gateway
```

