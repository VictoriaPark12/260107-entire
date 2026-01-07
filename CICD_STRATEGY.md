# CI/CD 파이프라인 전략

## 📋 목차

1. [전체 아키텍처 개요](#1-전체-아키텍처-개요)
2. [프로젝트 구조 및 서브모듈 전략](#2-프로젝트-구조-및-서브모듈-전략)
3. [배포 환경 구성](#3-배포-환경-구성)
4. [CI/CD 파이프라인 설계](#4-cicd-파이프라인-설계)
5. [GitHub Actions 워크플로우](#5-github-actions-워크플로우)
6. [Docker Hub 전략](#6-docker-hub-전략)
7. [EC2 배포 전략](#7-ec2-배포-전략)
8. [S3 리소스 관리](#8-s3-리소스-관리)
9. [보안 및 환경 변수 관리](#9-보안-및-환경-변수-관리)
10. [모니터링 및 롤백 전략](#10-모니터링-및-롤백-전략)

---

## 1. 전체 아키텍처 개요

### 1.1 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Repository                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ api          │  │ chat         │  │ yolo         │          │
│  │ (submodule)  │  │ (submodule)  │  │ (submodule)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ www          │  │ admin        │                            │
│  │ (root)       │  │ (root)       │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ GitHub Actions (on push)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         CI Process                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Build & Test │  │ Build & Test │  │ Build & Test │          │
│  │ Spring Boot  │  │ FastAPI      │  │ FastAPI      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         │ Docker Build     │ Docker Build     │ Docker Build    │
│         ▼                  ▼                  ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Docker Image │  │ Docker Image │  │ Docker Image │          │
│  │ api:latest   │  │ chat:latest  │  │ yolo:latest  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          │ Push to Docker Hub                 │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Hub                               │
│  devictoria/api:latest                                           │
│  devictoria/chatbot:latest                                       │
│  devictoria/yolo:latest                                          │
└─────────────────────────────────────────────────────────────────┘
          │                  │                  │
          │ Pull & Deploy    │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         AWS EC2                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ api:8080     │  │ chat:9002    │  │ yolo:9001    │          │
│  │ Spring Boot  │  │ FastAPI      │  │ FastAPI      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         └─────────┬────────┴─────────┬────────┘                 │
│                   ▼                  ▼                           │
│         ┌──────────────┐   ┌──────────────┐                    │
│         │ AWS S3       │   │ Nginx        │                    │
│         │ - Models     │   │ Reverse      │                    │
│         │ - Images     │   │ Proxy        │                    │
│         │ - Resources  │   └──────────────┘                    │
│         └──────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         Vercel                                   │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ www          │  │ admin        │                            │
│  │ Next.js      │  │ Next.js      │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 서비스별 배포 방식

| 서비스 | 기술 스택 | 배포 대상 | CI/CD 도구 | 포트 |
|--------|----------|----------|-----------|------|
| www.devictoria.shop | Next.js | Vercel | Vercel CI/CD | 443 |
| admin.devictoria.shop | Next.js | Vercel | Vercel CI/CD | 443 |
| api.devictoria.shop | Spring Boot | EC2 + Docker | GitHub Actions | 8080 |
| chat.devictoria.shop | FastAPI | EC2 + Docker | GitHub Actions | 9002 |
| yolo.devictoria.shop | FastAPI + YOLO | EC2 + Docker | GitHub Actions | 9001 |

---

## 2. 프로젝트 구조 및 서브모듈 전략

### 2.1 권장 저장소 구조

```
devictoria-infrastructure/           # 메인 저장소
├── .github/
│   └── workflows/
│       ├── api-deploy.yml          # API 서비스 CI/CD
│       ├── chat-deploy.yml         # Chat 서비스 CI/CD
│       ├── yolo-deploy.yml         # YOLO 서비스 CI/CD
│       └── deploy-all.yml          # 전체 배포
├── .gitmodules                     # 서브모듈 설정
├── api.devictoria.shop/           # Git Submodule
├── chat.devictoria.shop/          # Git Submodule
├── yolo.devictoria.shop/          # Git Submodule
├── docker-compose.prod.yml        # 프로덕션 Docker Compose
├── docker-compose.local.yml       # 로컬 개발 환경
├── scripts/
│   ├── deploy-to-ec2.sh          # EC2 배포 스크립트
│   ├── sync-s3-resources.sh      # S3 리소스 동기화
│   └── rollback.sh               # 롤백 스크립트
└── CICD_STRATEGY.md              # 이 문서
```

### 2.2 서브모듈 설정

각 서비스를 별도 저장소로 관리하고 서브모듈로 연결합니다.

#### 서브모듈 추가 명령어

```bash
# 메인 저장소 생성
git init devictoria-infrastructure
cd devictoria-infrastructure

# 서브모듈 추가
git submodule add https://github.com/[USERNAME]/api.devictoria.shop.git api.devictoria.shop
git submodule add https://github.com/[USERNAME]/chat.devictoria.shop.git chat.devictoria.shop
git submodule add https://github.com/[USERNAME]/yolo.devictoria.shop.git yolo.devictoria.shop

# 서브모듈 초기화 및 업데이트
git submodule init
git submodule update --remote

# 커밋
git add .gitmodules api.devictoria.shop chat.devictoria.shop yolo.devictoria.shop
git commit -m "Add service submodules"
```

#### .gitmodules 파일

```ini
[submodule "api.devictoria.shop"]
    path = api.devictoria.shop
    url = https://github.com/[USERNAME]/api.devictoria.shop.git
    branch = main

[submodule "chat.devictoria.shop"]
    path = chat.devictoria.shop
    url = https://github.com/[USERNAME]/chat.devictoria.shop.git
    branch = main

[submodule "yolo.devictoria.shop"]
    path = yolo.devictoria.shop
    url = https://github.com/[USERNAME]/yolo.devictoria.shop.git
    branch = main
```

---

## 3. 배포 환경 구성

### 3.1 AWS 인프라 구성

#### EC2 인스턴스

- **인스턴스 타입**: `t3.medium` 이상 (YOLO 서비스는 GPU 인스턴스 권장: `g4dn.xlarge`)
- **운영체제**: Ubuntu 22.04 LTS
- **보안 그룹**:
  - 인바운드: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8080 (API), 9001-9002 (Services)
  - 아웃바운드: All traffic

#### S3 버킷

```
devictoria-resources/
├── models/
│   ├── yolo/
│   │   ├── yolov8n.pt
│   │   ├── yolov8s.pt
│   │   └── yolov8m.pt
│   └── diffusers/
│       └── stable-diffusion-v1-5/
├── images/
│   ├── uploads/
│   └── results/
└── configs/
    └── application-prod.yml
```

**버킷 정책**:
- 프라이빗 액세스
- EC2 인스턴스 역할을 통한 액세스
- CloudFront를 통한 공개 이미지 제공

#### IAM 역할

**EC2 역할 (`devictoria-ec2-role`)**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::devictoria-resources/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::devictoria-resources"
    }
  ]
}
```

### 3.2 Docker Hub 구성

**저장소**:
- `devictoria/api:latest`, `devictoria/api:v1.0.0`
- `devictoria/chatbot:latest`, `devictoria/chatbot:v1.0.0`
- `devictoria/yolo:latest`, `devictoria/yolo:v1.0.0`

**태그 전략**:
- `latest`: 최신 프로덕션 버전
- `v{major}.{minor}.{patch}`: 시맨틱 버전
- `dev`: 개발 버전
- `{branch}-{sha}`: 브랜치별 빌드

---

## 4. CI/CD 파이프라인 설계

### 4.1 파이프라인 단계

각 서비스의 CI/CD 파이프라인은 다음 단계를 거칩니다:

```
1. Trigger (Push to main/develop)
   ↓
2. Checkout Code (with submodules)
   ↓
3. Setup Environment (Java/Python)
   ↓
4. Install Dependencies
   ↓
5. Run Tests
   ↓
6. Build Docker Image
   ↓
7. Push to Docker Hub
   ↓
8. Deploy to EC2
   ↓
9. Sync Resources to S3 (if needed)
   ↓
10. Health Check
   ↓
11. Notify (Success/Failure)
```

### 4.2 트리거 전략

| 브랜치 | 트리거 조건 | 배포 대상 | 태그 |
|--------|-----------|----------|------|
| `main` | Push | Production EC2 | `latest`, `v{version}` |
| `develop` | Push | Staging EC2 | `dev` |
| `feature/*` | Push | 빌드만 수행 | `{branch}-{sha}` |
| Tag `v*` | Tag push | Production EC2 | `{tag}` |

### 4.3 병렬 처리 전략

- 각 서비스의 CI/CD는 **독립적으로 실행**
- 서브모듈에 변경사항이 있을 경우 해당 서비스만 빌드/배포
- 병렬 빌드로 전체 배포 시간 단축

---

## 5. GitHub Actions 워크플로우

### 5.1 API 서비스 워크플로우 (Spring Boot)

**파일**: `.github/workflows/api-deploy.yml`

```yaml
name: API Service CI/CD

on:
  push:
    branches:
      - main
      - develop
    paths:
      - 'api.devictoria.shop/**'
      - '.github/workflows/api-deploy.yml'
  workflow_dispatch:

env:
  DOCKER_IMAGE: devictoria/api
  EC2_HOST: ${{ secrets.EC2_HOST }}
  EC2_USER: ubuntu
  SERVICE_NAME: api

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      # 1. 코드 체크아웃 (서브모듈 포함)
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          submodules: recursive
          token: ${{ secrets.GH_PAT }}
      
      # 2. Java 21 설정
      - name: Set up JDK 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'
          cache: 'gradle'
      
      # 3. Gradle 빌드 (테스트 포함)
      - name: Build with Gradle
        working-directory: ./api.devictoria.shop
        run: |
          chmod +x gradlew
          ./gradlew clean build
      
      # 4. 테스트 결과 업로드
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: api.devictoria.shop/build/test-results/
      
      # 5. Docker 빌드 및 푸시
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Extract version
        id: version
        run: |
          if [[ "${{ github.ref }}" == refs/tags/* ]]; then
            echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
          else
            echo "VERSION=$(date +%Y%m%d-%H%M%S)-${GITHUB_SHA::7}" >> $GITHUB_OUTPUT
          fi
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./api.devictoria.shop
          push: true
          tags: |
            ${{ env.DOCKER_IMAGE }}:latest
            ${{ env.DOCKER_IMAGE }}:${{ steps.version.outputs.VERSION }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      # 6. EC2 배포
      - name: Deploy to EC2
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ env.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            # Docker 로그인
            echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
            
            # 이전 컨테이너 중지 및 제거
            docker stop ${{ env.SERVICE_NAME }} || true
            docker rm ${{ env.SERVICE_NAME }} || true
            
            # 최신 이미지 풀
            docker pull ${{ env.DOCKER_IMAGE }}:latest
            
            # 새 컨테이너 실행
            docker run -d \
              --name ${{ env.SERVICE_NAME }} \
              --restart unless-stopped \
              -p 8080:8080 \
              -e SPRING_PROFILES_ACTIVE=prod \
              -e KAKAO_REST_API_KEY="${{ secrets.KAKAO_REST_API_KEY }}" \
              -e GOOGLE_CLIENT_ID="${{ secrets.GOOGLE_CLIENT_ID }}" \
              -e GOOGLE_CLIENT_SECRET="${{ secrets.GOOGLE_CLIENT_SECRET }}" \
              -e NAVER_CLIENT_ID="${{ secrets.NAVER_CLIENT_ID }}" \
              -e NAVER_CLIENT_SECRET="${{ secrets.NAVER_CLIENT_SECRET }}" \
              -e JWT_SECRET="${{ secrets.JWT_SECRET }}" \
              -e AWS_REGION="ap-northeast-2" \
              -v /home/ubuntu/logs:/app/logs \
              ${{ env.DOCKER_IMAGE }}:latest
            
            # 오래된 이미지 정리
            docker image prune -af
      
      # 7. Health Check
      - name: Health Check
        run: |
          sleep 30
          curl -f http://${{ secrets.EC2_HOST }}:8080/actuator/health || exit 1
      
      # 8. 슬랙 알림
      - name: Slack Notification
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: |
            API Service Deployment: ${{ job.status }}
            Version: ${{ steps.version.outputs.VERSION }}
            Branch: ${{ github.ref }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 5.2 Chat 서비스 워크플로우 (FastAPI)

**파일**: `.github/workflows/chat-deploy.yml`

```yaml
name: Chat Service CI/CD

on:
  push:
    branches:
      - main
      - develop
    paths:
      - 'chat.devictoria.shop/**'
      - '.github/workflows/chat-deploy.yml'
  workflow_dispatch:

env:
  DOCKER_IMAGE: devictoria/chatbot
  EC2_HOST: ${{ secrets.EC2_HOST }}
  EC2_USER: ubuntu
  SERVICE_NAME: chatbot

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      # 1. 코드 체크아웃
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          submodules: recursive
          token: ${{ secrets.GH_PAT }}
      
      # 2. Python 3.11 설정
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      # 3. 의존성 설치 및 테스트
      - name: Install dependencies
        working-directory: ./chat.devictoria.shop
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx
      
      - name: Run tests
        working-directory: ./chat.devictoria.shop
        run: |
          pytest tests/ -v || true
      
      # 4. Docker 빌드 및 푸시
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Extract version
        id: version
        run: |
          if [[ "${{ github.ref }}" == refs/tags/* ]]; then
            echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
          else
            echo "VERSION=$(date +%Y%m%d-%H%M%S)-${GITHUB_SHA::7}" >> $GITHUB_OUTPUT
          fi
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./chat.devictoria.shop
          push: true
          tags: |
            ${{ env.DOCKER_IMAGE }}:latest
            ${{ env.DOCKER_IMAGE }}:${{ steps.version.outputs.VERSION }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      # 5. EC2 배포
      - name: Deploy to EC2
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ env.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            # Docker 로그인
            echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
            
            # 이전 컨테이너 중지 및 제거
            docker stop ${{ env.SERVICE_NAME }} || true
            docker rm ${{ env.SERVICE_NAME }} || true
            
            # 최신 이미지 풀
            docker pull ${{ env.DOCKER_IMAGE }}:latest
            
            # 새 컨테이너 실행
            docker run -d \
              --name ${{ env.SERVICE_NAME }} \
              --restart unless-stopped \
              -p 9002:9002 \
              -v /home/ubuntu/chatbot-data:/app/data \
              ${{ env.DOCKER_IMAGE }}:latest
            
            # 오래된 이미지 정리
            docker image prune -af
      
      # 6. Health Check
      - name: Health Check
        run: |
          sleep 20
          curl -f http://${{ secrets.EC2_HOST }}:9002/health || exit 1
      
      # 7. 슬랙 알림
      - name: Slack Notification
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: |
            Chat Service Deployment: ${{ job.status }}
            Version: ${{ steps.version.outputs.VERSION }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 5.3 YOLO 서비스 워크플로우 (FastAPI + Models)

**파일**: `.github/workflows/yolo-deploy.yml`

```yaml
name: YOLO Service CI/CD

on:
  push:
    branches:
      - main
      - develop
    paths:
      - 'yolo.devictoria.shop/**'
      - '.github/workflows/yolo-deploy.yml'
  workflow_dispatch:

env:
  DOCKER_IMAGE: devictoria/yolo
  EC2_HOST: ${{ secrets.EC2_HOST }}
  EC2_USER: ubuntu
  SERVICE_NAME: yolo
  S3_BUCKET: devictoria-resources

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      # 1. 코드 체크아웃
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          submodules: recursive
          token: ${{ secrets.GH_PAT }}
      
      # 2. Python 3.11 설정
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      # 3. 의존성 설치 및 테스트
      - name: Install dependencies
        working-directory: ./yolo.devictoria.shop
        run: |
          pip install -r requirements.txt
          pip install pytest
      
      - name: Run tests
        working-directory: ./yolo.devictoria.shop
        run: |
          pytest tests/ -v || true
      
      # 4. S3에 모델 업로드
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-2
      
      - name: Sync models to S3
        run: |
          if [ -d "./yolo.devictoria.shop/models" ]; then
            aws s3 sync ./yolo.devictoria.shop/models s3://${{ env.S3_BUCKET }}/models/yolo/ \
              --exclude "*.pyc" --exclude "__pycache__/*"
          fi
      
      # 5. Docker 빌드 및 푸시
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Extract version
        id: version
        run: |
          if [[ "${{ github.ref }}" == refs/tags/* ]]; then
            echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
          else
            echo "VERSION=$(date +%Y%m%d-%H%M%S)-${GITHUB_SHA::7}" >> $GITHUB_OUTPUT
          fi
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./yolo.devictoria.shop
          push: true
          tags: |
            ${{ env.DOCKER_IMAGE }}:latest
            ${{ env.DOCKER_IMAGE }}:${{ steps.version.outputs.VERSION }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      # 6. EC2 배포
      - name: Deploy to EC2
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ env.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            # Docker 로그인
            echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
            
            # 이전 컨테이너 중지 및 제거
            docker stop ${{ env.SERVICE_NAME }} || true
            docker rm ${{ env.SERVICE_NAME }} || true
            
            # 최신 이미지 풀
            docker pull ${{ env.DOCKER_IMAGE }}:latest
            
            # S3에서 모델 다운로드 (초기 설정 시)
            mkdir -p /home/ubuntu/yolo-models
            aws s3 sync s3://${{ env.S3_BUCKET }}/models/yolo/ /home/ubuntu/yolo-models/
            
            # 새 컨테이너 실행
            docker run -d \
              --name ${{ env.SERVICE_NAME }} \
              --restart unless-stopped \
              -p 9001:9001 \
              -e AWS_REGION="ap-northeast-2" \
              -e S3_BUCKET="${{ env.S3_BUCKET }}" \
              -v /home/ubuntu/yolo-models:/app/models \
              -v /home/ubuntu/yolo-results:/app/results \
              ${{ env.DOCKER_IMAGE }}:latest
            
            # 오래된 이미지 정리
            docker image prune -af
      
      # 7. Health Check
      - name: Health Check
        run: |
          sleep 30
          curl -f http://${{ secrets.EC2_HOST }}:9001/health || exit 1
      
      # 8. 슬랙 알림
      - name: Slack Notification
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: |
            YOLO Service Deployment: ${{ job.status }}
            Version: ${{ steps.version.outputs.VERSION }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 5.4 전체 배포 워크플로우

**파일**: `.github/workflows/deploy-all.yml`

```yaml
name: Deploy All Services

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'production'
        type: choice
        options:
          - production
          - staging

jobs:
  deploy-api:
    uses: ./.github/workflows/api-deploy.yml
    secrets: inherit
  
  deploy-chat:
    uses: ./.github/workflows/chat-deploy.yml
    secrets: inherit
  
  deploy-yolo:
    uses: ./.github/workflows/yolo-deploy.yml
    secrets: inherit
  
  notify:
    needs: [deploy-api, deploy-chat, deploy-yolo]
    runs-on: ubuntu-latest
    steps:
      - name: Slack Notification
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: |
            🚀 All Services Deployed Successfully!
            Environment: ${{ github.event.inputs.environment }}
            - API: ✅
            - Chat: ✅
            - YOLO: ✅
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 6. Docker Hub 전략

### 6.1 이미지 태그 규칙

```bash
# Latest (프로덕션)
devictoria/api:latest
devictoria/chatbot:latest
devictoria/yolo:latest

# 버전별 태그
devictoria/api:v1.0.0
devictoria/api:v1.1.0

# 날짜 + SHA 태그 (자동 빌드)
devictoria/api:20260107-abc1234
devictoria/chatbot:20260107-def5678

# 개발 버전
devictoria/api:dev
```

### 6.2 자동 정리 정책

Docker Hub에서 오래된 이미지 자동 삭제:
- `latest`, `v*` 태그는 유지
- 30일 이상 된 날짜 태그는 삭제
- 최근 10개 빌드는 항상 유지

---

## 7. EC2 배포 전략

### 7.1 초기 EC2 설정

```bash
#!/bin/bash
# setup-ec2.sh - EC2 인스턴스 초기 설정 스크립트

# Docker 설치
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu

# AWS CLI 설치
sudo apt install -y awscli

# Nginx 설치 (리버스 프록시)
sudo apt install -y nginx
sudo systemctl enable nginx

# 디렉토리 생성
mkdir -p /home/ubuntu/logs
mkdir -p /home/ubuntu/chatbot-data
mkdir -p /home/ubuntu/yolo-models
mkdir -p /home/ubuntu/yolo-results

# IAM 역할 확인
aws sts get-caller-identity

echo "EC2 setup completed!"
```

### 7.2 Nginx 리버스 프록시 설정

**파일**: `/etc/nginx/sites-available/devictoria`

```nginx
# API Gateway
upstream api_backend {
    server localhost:8080;
}

# Chat Service
upstream chat_backend {
    server localhost:9002;
}

# YOLO Service
upstream yolo_backend {
    server localhost:9001;
}

# www.devictoria.shop (프록시 to Vercel)
server {
    listen 80;
    server_name www.devictoria.shop;

    # Vercel로 프록시 (또는 직접 Vercel DNS 사용)
    return 301 https://www.devictoria.shop$request_uri;
}

# api.devictoria.shop
server {
    listen 80;
    server_name api.devictoria.shop;

    client_max_body_size 50M;

    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /actuator/health {
        proxy_pass http://api_backend/actuator/health;
        access_log off;
    }
}

# chat.devictoria.shop
server {
    listen 80;
    server_name chat.devictoria.shop;

    location / {
        proxy_pass http://chat_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /health {
        proxy_pass http://chat_backend/health;
        access_log off;
    }
}

# yolo.devictoria.shop
server {
    listen 80;
    server_name yolo.devictoria.shop;

    client_max_body_size 100M;

    location / {
        proxy_pass http://yolo_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 타임아웃 설정 (YOLO 처리 시간 고려)
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location /health {
        proxy_pass http://yolo_backend/health;
        access_log off;
    }
}
```

### 7.3 Docker Compose 프로덕션 구성

**파일**: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  api:
    image: devictoria/api:latest
    container_name: api
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - KAKAO_REST_API_KEY=${KAKAO_REST_API_KEY}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - NAVER_CLIENT_ID=${NAVER_CLIENT_ID}
      - NAVER_CLIENT_SECRET=${NAVER_CLIENT_SECRET}
      - JWT_SECRET=${JWT_SECRET}
      - AWS_REGION=ap-northeast-2
    volumes:
      - /home/ubuntu/logs:/app/logs
    networks:
      - devictoria-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  chatbot:
    image: devictoria/chatbot:latest
    container_name: chatbot
    restart: unless-stopped
    ports:
      - "9002:9002"
    volumes:
      - /home/ubuntu/chatbot-data:/app/data
    networks:
      - devictoria-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  yolo:
    image: devictoria/yolo:latest
    container_name: yolo
    restart: unless-stopped
    ports:
      - "9001:9001"
    environment:
      - AWS_REGION=ap-northeast-2
      - S3_BUCKET=devictoria-resources
    volumes:
      - /home/ubuntu/yolo-models:/app/models
      - /home/ubuntu/yolo-results:/app/results
    networks:
      - devictoria-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  devictoria-network:
    driver: bridge
```

### 7.4 배포 스크립트

**파일**: `scripts/deploy-to-ec2.sh`

```bash
#!/bin/bash
set -e

# 설정
EC2_HOST=${EC2_HOST:-"your-ec2-instance.com"}
EC2_USER="ubuntu"
SSH_KEY=${EC2_SSH_KEY:-"~/.ssh/devictoria-key.pem"}

echo "🚀 Deploying to EC2: $EC2_HOST"

# SSH로 배포 명령 실행
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << 'EOF'
  cd /home/ubuntu
  
  # Docker Compose 파일 다운로드 (최신 버전)
  wget -O docker-compose.prod.yml https://raw.githubusercontent.com/[USERNAME]/devictoria-infrastructure/main/docker-compose.prod.yml
  
  # 환경 변수 로드
  source /home/ubuntu/.env
  
  # 서비스 재시작
  docker-compose -f docker-compose.prod.yml pull
  docker-compose -f docker-compose.prod.yml up -d
  
  # 오래된 이미지 정리
  docker image prune -af
  
  # 로그 확인
  docker-compose -f docker-compose.prod.yml ps
EOF

echo "✅ Deployment completed!"
```

---

## 8. S3 리소스 관리

### 8.1 S3 버킷 구조

```
s3://devictoria-resources/
├── models/
│   ├── yolo/
│   │   ├── yolov8n.pt          # 6MB (나노 모델)
│   │   ├── yolov8s.pt          # 22MB (스몰 모델)
│   │   ├── yolov8m.pt          # 52MB (미디엄 모델)
│   │   └── custom-trained.pt   # 커스텀 모델
│   ├── diffusers/
│   │   └── stable-diffusion-v1-5/
│   │       ├── model_index.json
│   │       ├── unet/
│   │       ├── vae/
│   │       └── text_encoder/
│   └── transformers/
│       └── bert-base-multilingual/
├── images/
│   ├── uploads/                # 사용자 업로드 이미지
│   │   └── {user_id}/
│   │       └── {timestamp}_{filename}
│   ├── results/                # 처리된 결과 이미지
│   │   └── {user_id}/
│   │       └── {timestamp}_{result}.jpg
│   └── samples/                # 샘플 이미지
└── configs/
    ├── application-prod.yml    # 프로덕션 설정
    └── model-config.json       # 모델 설정
```

### 8.2 S3 동기화 스크립트

**파일**: `scripts/sync-s3-resources.sh`

```bash
#!/bin/bash
set -e

S3_BUCKET="devictoria-resources"
LOCAL_DIR="./resources"

echo "📦 Syncing resources to S3..."

# 모델 업로드
if [ -d "$LOCAL_DIR/models" ]; then
    echo "Uploading models..."
    aws s3 sync "$LOCAL_DIR/models" "s3://$S3_BUCKET/models/" \
        --exclude "*.pyc" --exclude "__pycache__/*" \
        --storage-class STANDARD_IA
fi

# 샘플 이미지 업로드
if [ -d "$LOCAL_DIR/samples" ]; then
    echo "Uploading sample images..."
    aws s3 sync "$LOCAL_DIR/samples" "s3://$S3_BUCKET/images/samples/" \
        --acl public-read
fi

# 설정 파일 업로드
if [ -d "$LOCAL_DIR/configs" ]; then
    echo "Uploading config files..."
    aws s3 sync "$LOCAL_DIR/configs" "s3://$S3_BUCKET/configs/" \
        --exclude "*.local.*"
fi

echo "✅ S3 sync completed!"
```

### 8.3 S3 라이프사이클 정책

```json
{
  "Rules": [
    {
      "Id": "DeleteOldUploads",
      "Status": "Enabled",
      "Prefix": "images/uploads/",
      "Expiration": {
        "Days": 30
      }
    },
    {
      "Id": "DeleteOldResults",
      "Status": "Enabled",
      "Prefix": "images/results/",
      "Expiration": {
        "Days": 7
      }
    },
    {
      "Id": "MoveModelsToGlacier",
      "Status": "Enabled",
      "Prefix": "models/",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

---

## 9. 보안 및 환경 변수 관리

### 9.1 GitHub Secrets

GitHub 저장소 설정 → Secrets → Actions에서 다음 시크릿을 추가합니다:

| Secret 이름 | 설명 | 예시 |
|-------------|------|------|
| `DOCKER_USERNAME` | Docker Hub 사용자명 | `devictoria` |
| `DOCKER_PASSWORD` | Docker Hub 비밀번호 또는 토큰 | `dckr_pat_xxx` |
| `EC2_HOST` | EC2 퍼블릭 IP 또는 도메인 | `ec2-xx-xx-xx-xx.compute.amazonaws.com` |
| `EC2_SSH_KEY` | EC2 SSH 프라이빗 키 | `-----BEGIN RSA PRIVATE KEY-----\n...` |
| `AWS_ACCESS_KEY_ID` | AWS 액세스 키 | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS 시크릿 키 | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `KAKAO_REST_API_KEY` | 카카오 REST API 키 | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `GOOGLE_CLIENT_ID` | 구글 클라이언트 ID | `xxxxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | 구글 클라이언트 시크릿 | `GOCSPX-xxxxxxxxxxxxx` |
| `NAVER_CLIENT_ID` | 네이버 클라이언트 ID | `xxxxxxxxxxxxxx` |
| `NAVER_CLIENT_SECRET` | 네이버 클라이언트 시크릿 | `xxxxxxxxxx` |
| `JWT_SECRET` | JWT 시크릿 키 (최소 32바이트) | `your-very-secure-jwt-secret-key-here` |
| `SLACK_WEBHOOK` | 슬랙 웹훅 URL (선택) | `https://hooks.slack.com/services/xxx` |
| `GH_PAT` | GitHub Personal Access Token | `ghp_xxxxxxxxxxxxxxxxxxxx` |

### 9.2 EC2 환경 변수

**파일**: `/home/ubuntu/.env`

```bash
# Docker Hub
DOCKER_USERNAME=devictoria
DOCKER_PASSWORD=your_docker_password

# OAuth
KAKAO_REST_API_KEY=your_kakao_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# JWT
JWT_SECRET=your-jwt-secret-minimum-32-bytes

# AWS
AWS_REGION=ap-northeast-2
S3_BUCKET=devictoria-resources

# Database (필요시)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=devictoria
DB_USER=postgres
DB_PASSWORD=your_db_password
```

**주의사항**:
- `.env` 파일 권한: `chmod 600 /home/ubuntu/.env`
- Git에 절대 커밋하지 말 것

### 9.3 보안 체크리스트

- [ ] GitHub Secrets 모두 설정
- [ ] EC2 보안 그룹 방화벽 설정
- [ ] IAM 역할 최소 권한 원칙 적용
- [ ] S3 버킷 퍼블릭 액세스 차단 (필요한 것만 열기)
- [ ] Nginx HTTPS 설정 (Let's Encrypt)
- [ ] Docker 컨테이너 non-root 사용자로 실행
- [ ] 민감한 로그 마스킹
- [ ] AWS CloudWatch 알람 설정
- [ ] 정기적인 보안 패치 자동화

---

## 10. 모니터링 및 롤백 전략

### 10.1 Health Check 엔드포인트

각 서비스에 Health Check 엔드포인트를 구현합니다.

#### API Service (Spring Boot)

```java
@RestController
@RequestMapping("/actuator")
public class HealthController {
    
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("timestamp", System.currentTimeMillis());
        health.put("service", "api");
        return ResponseEntity.ok(health);
    }
}
```

#### Chat Service (FastAPI)

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "UP",
        "service": "chatbot",
        "timestamp": time.time()
    }
```

#### YOLO Service (FastAPI)

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    # 모델 로드 상태 확인
    model_loaded = check_model_loaded()
    
    return {
        "status": "UP" if model_loaded else "DEGRADED",
        "service": "yolo",
        "model_loaded": model_loaded,
        "timestamp": time.time()
    }
```

### 10.2 로깅 전략

#### 로그 수집

```yaml
# docker-compose.prod.yml에 추가
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### CloudWatch Logs 통합

```bash
# EC2에 CloudWatch Agent 설치
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# 설정 파일 생성
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json \
  -s
```

**파일**: `/opt/aws/amazon-cloudwatch-agent/etc/config.json`

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/home/ubuntu/logs/api.log",
            "log_group_name": "/devictoria/api",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/lib/docker/containers/*/*.log",
            "log_group_name": "/devictoria/containers",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

### 10.3 롤백 스크립트

**파일**: `scripts/rollback.sh`

```bash
#!/bin/bash
set -e

# 사용법: ./rollback.sh <service> <version>
# 예시: ./rollback.sh api v1.0.0

SERVICE=$1
VERSION=${2:-previous}

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service> [version]"
    echo "Services: api, chatbot, yolo"
    exit 1
fi

EC2_HOST=${EC2_HOST:-"your-ec2-instance.com"}
EC2_USER="ubuntu"
SSH_KEY=${EC2_SSH_KEY:-"~/.ssh/devictoria-key.pem"}

echo "🔄 Rolling back $SERVICE to version: $VERSION"

# 이전 버전 찾기
if [ "$VERSION" == "previous" ]; then
    echo "Finding previous version..."
    PREVIOUS_VERSION=$(ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" \
        "docker images devictoria/$SERVICE --format '{{.Tag}}' | grep -v latest | head -n 1")
    
    if [ -z "$PREVIOUS_VERSION" ]; then
        echo "❌ No previous version found!"
        exit 1
    fi
    
    VERSION=$PREVIOUS_VERSION
    echo "Previous version: $VERSION"
fi

# 롤백 실행
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
    # 현재 컨테이너 중지
    docker stop $SERVICE || true
    docker rm $SERVICE || true
    
    # 이전 버전으로 실행
    docker pull devictoria/$SERVICE:$VERSION
    
    # 서비스별 실행 명령
    case "$SERVICE" in
        api)
            docker run -d \
                --name api \
                --restart unless-stopped \
                -p 8080:8080 \
                -e SPRING_PROFILES_ACTIVE=prod \
                -v /home/ubuntu/logs:/app/logs \
                devictoria/api:$VERSION
            ;;
        chatbot)
            docker run -d \
                --name chatbot \
                --restart unless-stopped \
                -p 9002:9002 \
                -v /home/ubuntu/chatbot-data:/app/data \
                devictoria/chatbot:$VERSION
            ;;
        yolo)
            docker run -d \
                --name yolo \
                --restart unless-stopped \
                -p 9001:9001 \
                -v /home/ubuntu/yolo-models:/app/models \
                -v /home/ubuntu/yolo-results:/app/results \
                devictoria/yolo:$VERSION
            ;;
    esac
    
    # Health Check
    sleep 10
    docker ps | grep $SERVICE
EOF

echo "✅ Rollback completed to version: $VERSION"
```

### 10.4 알림 설정 (Slack)

**Slack Incoming Webhook 설정**:
1. Slack Workspace → Apps → Incoming Webhooks 활성화
2. 채널 선택 (예: `#devictoria-deployments`)
3. Webhook URL 복사
4. GitHub Secrets에 `SLACK_WEBHOOK` 추가

---

## 11. 배포 플로우 요약

### 11.1 개발 플로우

```
1. 개발자가 feature 브랜치에서 작업
   ↓
2. feature/* 브랜치에 push
   ↓
3. GitHub Actions: 빌드 및 테스트만 실행
   ↓
4. PR 생성 및 리뷰
   ↓
5. develop 브랜치로 병합
   ↓
6. GitHub Actions: Staging 환경에 자동 배포
   ↓
7. QA 테스트
   ↓
8. main 브랜치로 병합
   ↓
9. GitHub Actions: Production 배포
   ↓
10. Health Check 및 모니터링
```

### 11.2 긴급 핫픽스 플로우

```
1. main 브랜치에서 hotfix/* 브랜치 생성
   ↓
2. 버그 수정
   ↓
3. hotfix/* 브랜치에 push
   ↓
4. 자동 빌드 및 테스트
   ↓
5. main 브랜치로 직접 병합
   ↓
6. 즉시 Production 배포
   ↓
7. develop 브랜치에도 병합
```

### 11.3 롤백 플로우

```
1. 프로덕션에서 문제 발견
   ↓
2. 모니터링 대시보드에서 확인
   ↓
3. 롤백 결정
   ↓
4. 수동으로 롤백 스크립트 실행:
   ./scripts/rollback.sh <service> <version>
   ↓
5. Health Check 확인
   ↓
6. 이슈 분석 및 수정
   ↓
7. 재배포
```

---

## 12. 체크리스트

### 초기 설정

- [ ] GitHub 저장소 생성 (메인 + 서브모듈)
- [ ] 서브모듈 추가 및 연결
- [ ] GitHub Secrets 설정
- [ ] Docker Hub 계정 및 저장소 생성
- [ ] AWS EC2 인스턴스 생성 및 설정
- [ ] AWS S3 버킷 생성 및 IAM 역할 설정
- [ ] EC2에 Docker, Docker Compose 설치
- [ ] Nginx 리버스 프록시 설정
- [ ] 도메인 DNS 설정
- [ ] SSL 인증서 설정 (Let's Encrypt)

### CI/CD 설정

- [ ] GitHub Actions 워크플로우 파일 작성
- [ ] 각 서비스 Dockerfile 최적화
- [ ] Health Check 엔드포인트 구현
- [ ] 테스트 코드 작성
- [ ] Docker Compose 프로덕션 파일 작성
- [ ] 배포 스크립트 작성
- [ ] 롤백 스크립트 작성

### 보안 설정

- [ ] GitHub Secrets 모두 설정
- [ ] EC2 보안 그룹 설정
- [ ] S3 버킷 정책 설정
- [ ] IAM 역할 최소 권한 설정
- [ ] 환경 변수 관리 (.env 파일)
- [ ] SSL/TLS 인증서 설정

### 모니터링 설정

- [ ] CloudWatch Logs 설정
- [ ] CloudWatch 알람 설정
- [ ] Slack 알림 설정
- [ ] Health Check 자동화
- [ ] 로그 로테이션 설정

### 테스트 및 검증

- [ ] 로컬 환경에서 전체 테스트
- [ ] Staging 환경 배포 테스트
- [ ] Production 배포 테스트
- [ ] 롤백 프로세스 테스트
- [ ] 부하 테스트
- [ ] 보안 스캔

---

## 13. 추가 개선 사항

### 13.1 향후 고려사항

1. **Kubernetes 마이그레이션**
   - Docker Compose → Kubernetes (EKS) 전환
   - 자동 스케일링 및 로드 밸런싱
   - Helm Chart 관리

2. **Database 추가**
   - RDS (PostgreSQL/MySQL) 연동
   - Redis 캐시 레이어
   - Database 마이그레이션 자동화

3. **고급 모니터링**
   - Prometheus + Grafana
   - APM (Application Performance Monitoring)
   - Distributed Tracing (Jaeger)

4. **비용 최적화**
   - EC2 Spot Instance 사용
   - S3 Intelligent-Tiering
   - CloudFront CDN 통합

5. **보안 강화**
   - AWS Secrets Manager
   - AWS WAF (Web Application Firewall)
   - DDoS 방어 (Shield)
   - 정기적인 보안 스캔 자동화

---

## 14. 참고 자료

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [AWS EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [AWS S3 Developer Guide](https://docs.aws.amazon.com/s3/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Spring Boot Deployment Guide](https://spring.io/guides/gs/spring-boot-docker/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)

---

**문서 버전**: 1.0  
**작성일**: 2026년 1월 7일  
**작성자**: DevOps Team  
**업데이트**: 초기 버전

