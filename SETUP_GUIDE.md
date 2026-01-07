# DevVictoria CI/CD 파이프라인 설정 가이드

이 가이드는 처음부터 끝까지 CI/CD 파이프라인을 설정하는 방법을 단계별로 설명합니다.

## 📋 목차

1. [사전 준비사항](#1-사전-준비사항)
2. [GitHub 저장소 설정](#2-github-저장소-설정)
3. [Docker Hub 설정](#3-docker-hub-설정)
4. [AWS 인프라 설정](#4-aws-인프라-설정)
5. [서비스별 Dockerfile 작성](#5-서비스별-dockerfile-작성)
6. [GitHub Actions 설정](#6-github-actions-설정)
7. [첫 배포 실행](#7-첫-배포-실행)
8. [검증 및 테스트](#8-검증-및-테스트)

---

## 1. 사전 준비사항

### 필요한 계정

- ✅ GitHub 계정
- ✅ Docker Hub 계정
- ✅ AWS 계정 (EC2, S3, IAM 권한)
- ✅ 도메인 (예: devictoria.shop)

### 필요한 도구

```bash
# Git
git --version

# Docker (로컬 테스트용)
docker --version

# AWS CLI (선택사항)
aws --version
```

---

## 2. GitHub 저장소 설정

### 2.1 서비스별 저장소 생성

각 서비스를 별도 저장소로 생성합니다:

1. **api.devictoria.shop** - Spring Boot API
2. **chat.devictoria.shop** - FastAPI Chat Service
3. **yolo.devictoria.shop** - FastAPI YOLO Service

```bash
# 각 서비스 디렉토리에서
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/[USERNAME]/api.devictoria.shop.git
git push -u origin main
```

### 2.2 메인 인프라 저장소 생성

```bash
# 메인 저장소 생성
git init devictoria-infrastructure
cd devictoria-infrastructure

# 기본 파일 복사
cp /path/to/CICD_STRATEGY.md .
cp /path/to/README.md .
cp /path/to/docker-compose.prod.yml .

git add .
git commit -m "Initial infrastructure setup"
git branch -M main
git remote add origin https://github.com/[USERNAME]/devictoria-infrastructure.git
git push -u origin main
```

### 2.3 서브모듈 추가

```bash
cd devictoria-infrastructure

# 서브모듈 추가
git submodule add https://github.com/[USERNAME]/api.devictoria.shop.git api.devictoria.shop
git submodule add https://github.com/[USERNAME]/chat.devictoria.shop.git chat.devictoria.shop
git submodule add https://github.com/[USERNAME]/yolo.devictoria.shop.git yolo.devictoria.shop

# 커밋
git add .gitmodules api.devictoria.shop chat.devictoria.shop yolo.devictoria.shop
git commit -m "Add service submodules"
git push
```

### 2.4 GitHub Secrets 설정

**GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret**

필수 Secrets 추가:

```
DOCKER_USERNAME          # Docker Hub 사용자명
DOCKER_PASSWORD          # Docker Hub 토큰
EC2_HOST                 # EC2 퍼블릭 IP 또는 도메인
EC2_SSH_KEY             # SSH 프라이빗 키 전체 내용
AWS_ACCESS_KEY_ID       # AWS 액세스 키
AWS_SECRET_ACCESS_KEY   # AWS 시크릿 키
KAKAO_REST_API_KEY      # 카카오 API 키
GOOGLE_CLIENT_ID        # 구글 클라이언트 ID
GOOGLE_CLIENT_SECRET    # 구글 클라이언트 시크릿
NAVER_CLIENT_ID         # 네이버 클라이언트 ID
NAVER_CLIENT_SECRET     # 네이버 클라이언트 시크릿
JWT_SECRET              # JWT 시크릿 (32바이트 이상)
GH_PAT                  # GitHub Personal Access Token
SLACK_WEBHOOK           # 슬랙 웹훅 (선택사항)
```

**GitHub Personal Access Token (GH_PAT) 생성:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. 권한 선택: `repo` (전체), `workflow`
4. 토큰 복사하여 저장

---

## 3. Docker Hub 설정

### 3.1 Docker Hub 계정 생성

1. https://hub.docker.com 가입
2. 사용자명 확인 (예: `devictoria`)

### 3.2 Access Token 생성

1. Docker Hub → Account Settings → Security
2. New Access Token 생성
3. 토큰 복사하여 GitHub Secrets에 `DOCKER_PASSWORD`로 추가

### 3.3 저장소 생성 (선택사항 - 자동 생성됨)

- `devictoria/api`
- `devictoria/chatbot`
- `devictoria/yolo`

---

## 4. AWS 인프라 설정

### 4.1 EC2 인스턴스 생성

**AWS Console → EC2 → Launch Instance**

**설정:**
- **이름:** devictoria-production
- **AMI:** Ubuntu 22.04 LTS
- **인스턴스 타입:** 
  - `t3.medium` (API, Chat)
  - `g4dn.xlarge` (YOLO - GPU 필요시)
- **키 페어:** 새로 생성 또는 기존 사용
- **네트워크:** VPC 기본값
- **보안 그룹:**
  - SSH (22) - 내 IP만
  - HTTP (80) - 0.0.0.0/0
  - HTTPS (443) - 0.0.0.0/0
  - Custom TCP (8080) - 0.0.0.0/0
  - Custom TCP (9001-9002) - 0.0.0.0/0
- **스토리지:** 30GB gp3

**Elastic IP 할당:**
1. EC2 → Elastic IPs → Allocate Elastic IP address
2. EC2 인스턴스에 연결

### 4.2 IAM 역할 생성

**IAM → Roles → Create role**

**설정:**
- **Use case:** EC2
- **Permissions policies:**
  - AmazonS3FullAccess (또는 커스텀 정책)
  - CloudWatchAgentServerPolicy (모니터링용)

**커스텀 S3 정책 (권장):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::devictoria-resources",
        "arn:aws:s3:::devictoria-resources/*"
      ]
    }
  ]
}
```

**EC2 인스턴스에 IAM 역할 연결:**
1. EC2 인스턴스 선택
2. Actions → Security → Modify IAM role
3. 생성한 역할 선택

### 4.3 S3 버킷 생성

**S3 → Create bucket**

**설정:**
- **Bucket name:** devictoria-resources
- **Region:** ap-northeast-2 (서울)
- **Block Public Access:** 모든 퍼블릭 액세스 차단
- **Bucket Versioning:** 활성화 (권장)

**폴더 구조 생성:**

```
devictoria-resources/
├── models/
│   ├── yolo/
│   └── diffusers/
├── images/
│   ├── uploads/
│   ├── results/
│   └── samples/
└── configs/
```

### 4.4 도메인 DNS 설정

**Route 53 또는 도메인 제공자에서:**

```
A    api.devictoria.shop       → EC2 Elastic IP
A    chat.devictoria.shop      → EC2 Elastic IP
A    yolo.devictoria.shop      → EC2 Elastic IP
A    cv.devictoria.shop        → EC2 Elastic IP
```

---

## 5. 서비스별 Dockerfile 작성

### 5.1 API Service (Spring Boot)

**파일: `api.devictoria.shop/Dockerfile`**

```dockerfile
# 빌드 단계
FROM eclipse-temurin:21-jdk AS builder
WORKDIR /app

COPY gradle/ ./gradle/
COPY gradlew ./
COPY gradlew.bat ./
COPY build.gradle ./
COPY settings.gradle ./
COPY src/ ./src/

RUN chmod +x gradlew && ./gradlew clean build -x test --no-daemon

# 실행 단계
FROM eclipse-temurin:21-jre
WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/build/libs/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

### 5.2 Chat Service (FastAPI)

**파일: `chat.devictoria.shop/Dockerfile`**

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY app ./app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:9002/health || exit 1

EXPOSE 9002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9002"]
```

**파일: `chat.devictoria.shop/app/main.py`** (Health Check 추가)

```python
from fastapi import FastAPI

app = FastAPI(title="Chat Service")

@app.get("/health")
async def health_check():
    return {
        "status": "UP",
        "service": "chatbot",
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    return {"message": "Chat Service is running"}
```

### 5.3 YOLO Service (FastAPI)

**파일: `cv.devictoria.shop/Dockerfile`** (또는 yolo.devictoria.shop)

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:9001/health || exit 1

EXPOSE 9001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9001"]
```

**파일: `cv.devictoria.shop/main.py`** (Health Check 추가)

```python
from fastapi import FastAPI
import time

app = FastAPI(title="YOLO Service")

# 모델 로드 상태 체크 함수
def check_model_loaded():
    # TODO: 실제 모델 로드 상태 확인 로직
    return True

@app.get("/health")
async def health_check():
    model_loaded = check_model_loaded()
    
    return {
        "status": "UP" if model_loaded else "DEGRADED",
        "service": "yolo",
        "model_loaded": model_loaded,
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    return {"message": "YOLO Service is running"}
```

---

## 6. GitHub Actions 설정

워크플로우 파일들은 이미 생성되어 있습니다:

- `.github/workflows/api-deploy.yml`
- `.github/workflows/chat-deploy.yml`
- `.github/workflows/yolo-deploy.yml`
- `.github/workflows/deploy-all.yml`

**확인사항:**
- [ ] 모든 Secrets이 GitHub에 등록되었는지 확인
- [ ] 워크플로우 파일의 경로가 서브모듈 경로와 일치하는지 확인
- [ ] Docker 이미지 이름이 올바른지 확인

---

## 7. 첫 배포 실행

### 7.1 EC2 초기 설정

```bash
# SSH 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# 설정 스크립트 다운로드 및 실행
wget https://raw.githubusercontent.com/[USERNAME]/devictoria-infrastructure/main/scripts/setup-ec2.sh
chmod +x setup-ec2.sh
./setup-ec2.sh

# 로그아웃 후 재접속
exit
ssh -i your-key.pem ubuntu@your-ec2-ip

# 환경 변수 설정
nano /home/ubuntu/.env
# env.example 내용을 복사하여 실제 값 입력

chmod 600 /home/ubuntu/.env
```

### 7.2 Nginx 설정

```bash
# Nginx 설정 다운로드
sudo wget -O /etc/nginx/sites-available/devictoria \
  https://raw.githubusercontent.com/[USERNAME]/devictoria-infrastructure/main/nginx.conf

# 활성화
sudo ln -s /etc/nginx/sites-available/devictoria /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# 테스트 및 재시작
sudo nginx -t
sudo systemctl restart nginx
```

### 7.3 첫 배포 트리거

**방법 1: GitHub Actions 수동 실행**

1. GitHub → devictoria-infrastructure → Actions
2. "Deploy All Services" 워크플로우 선택
3. "Run workflow" 버튼 클릭
4. Environment: production 선택
5. 배포 진행 상황 확인

**방법 2: Git Push**

```bash
# 서브모듈 변경사항이 있는 경우
cd api.devictoria.shop
# 코드 수정...
git add .
git commit -m "Update API service"
git push origin main

cd ..
git add api.devictoria.shop
git commit -m "Update API submodule"
git push origin main

# GitHub Actions 자동 실행됨
```

---

## 8. 검증 및 테스트

### 8.1 Health Check 확인

```bash
# API 서비스
curl http://your-ec2-ip:8080/actuator/health

# Chat 서비스
curl http://your-ec2-ip:9002/health

# YOLO 서비스
curl http://your-ec2-ip:9001/health
```

### 8.2 도메인 확인

```bash
curl https://api.devictoria.shop/actuator/health
curl https://chat.devictoria.shop/health
curl https://yolo.devictoria.shop/health
```

### 8.3 Docker 컨테이너 상태 확인

```bash
# SSH로 EC2 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# 실행 중인 컨테이너 확인
docker ps

# 로그 확인
docker logs api -f
docker logs chatbot -f
docker logs yolo -f
```

### 8.4 SSL 인증서 설정

```bash
# Certbot 설치
sudo apt install -y certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d api.devictoria.shop
sudo certbot --nginx -d chat.devictoria.shop
sudo certbot --nginx -d yolo.devictoria.shop
sudo certbot --nginx -d cv.devictoria.shop

# 자동 갱신 활성화
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## 9. 트러블슈팅

### GitHub Actions 실패 시

1. **Actions 탭에서 에러 로그 확인**
2. **Secrets 확인**: 모든 필수 Secrets이 설정되었는지
3. **서브모듈 확인**: 서브모듈이 올바르게 클론되었는지
4. **Docker 빌드 확인**: 로컬에서 Docker 빌드 테스트

```bash
# 로컬에서 Docker 빌드 테스트
cd api.devictoria.shop
docker build -t test-api .
docker run -p 8080:8080 test-api
```

### EC2 컨테이너가 시작되지 않는 경우

```bash
# 로그 확인
docker logs api

# 환경 변수 확인
docker exec api env

# 수동으로 컨테이너 재시작
docker-compose -f docker-compose.prod.yml restart api
```

### 포트 충돌

```bash
# 사용 중인 포트 확인
sudo netstat -tulpn | grep LISTEN

# 프로세스 종료
sudo kill -9 <PID>
```

---

## 10. 다음 단계

✅ CI/CD 파이프라인 구축 완료!

**추가 개선사항:**
- [ ] 모니터링 도구 설정 (Prometheus, Grafana)
- [ ] 로그 수집 (CloudWatch Logs, ELK Stack)
- [ ] 데이터베이스 연동 (RDS)
- [ ] Redis 캐시 추가
- [ ] 부하 테스트
- [ ] 백업 전략 수립

---

**문서 버전:** 1.0  
**작성일:** 2026-01-07  
**업데이트:** 초기 버전

