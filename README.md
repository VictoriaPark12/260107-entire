# DevVictoria Infrastructure

DevVictoria 프로젝트의 CI/CD 파이프라인 및 인프라 관리 저장소입니다.

## 📋 프로젝트 구조

```
devictoria-infrastructure/
├── .github/workflows/          # GitHub Actions CI/CD 워크플로우
│   ├── api-deploy.yml         # API 서비스 배포
│   ├── chat-deploy.yml        # Chat 서비스 배포
│   ├── vision-deploy.yml      # Vision 서비스 배포
│   └── deploy-all.yml         # 전체 서비스 배포
├── scripts/                   # 배포 및 관리 스크립트
│   ├── setup-ec2.sh          # EC2 초기 설정
│   ├── deploy-to-ec2.sh      # 수동 배포
│   ├── rollback.sh           # 롤백 스크립트
│   └── sync-s3-resources.sh  # S3 리소스 동기화
├── api.devictoria.shop/      # API 서비스 (서브모듈)
├── chat.devictoria.shop/     # Chat 서비스 (서브모듈)
├── vision.devictoria.shop/   # Vision 서비스 (서브모듈)
├── docker-compose.prod.yml   # 프로덕션 Docker Compose
├── nginx.conf                # Nginx 설정
├── env.example               # 환경 변수 예시
└── CICD_STRATEGY.md          # CI/CD 전략 문서
```

## 🚀 서비스 구성

| 서비스 | 기술 스택 | 배포 대상 | 포트 |
|--------|----------|----------|------|
| www.devictoria.shop | Next.js | Vercel | 443 |
| admin.devictoria.shop | Next.js | Vercel | 443 |
| api.devictoria.shop | Spring Boot | EC2 + Docker | 8080 |
| chat.devictoria.shop | FastAPI | EC2 + Docker | 9002 |
| vision.devictoria.shop | FastAPI + CV/YOLO | EC2 + Docker | 9001 |

## 📦 초기 설정

### 1. 저장소 클론 및 서브모듈 초기화

```bash
# 메인 저장소 클론
git clone https://github.com/[USERNAME]/devictoria-infrastructure.git
cd devictoria-infrastructure

# 서브모듈 초기화 및 업데이트
git submodule update --init --recursive
```

### 2. GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions 에서 다음 Secrets을 추가하세요:

**필수 Secrets:**
- `DOCKER_USERNAME` - Docker Hub 사용자명
- `DOCKER_PASSWORD` - Docker Hub 비밀번호 또는 토큰
- `EC2_HOST` - EC2 퍼블릭 IP 또는 도메인
- `EC2_SSH_KEY` - EC2 SSH 프라이빗 키 (전체 내용)
- `AWS_ACCESS_KEY_ID` - AWS 액세스 키
- `AWS_SECRET_ACCESS_KEY` - AWS 시크릿 키
- `KAKAO_REST_API_KEY` - 카카오 REST API 키
- `GOOGLE_CLIENT_ID` - 구글 클라이언트 ID
- `GOOGLE_CLIENT_SECRET` - 구글 클라이언트 시크릿
- `NAVER_CLIENT_ID` - 네이버 클라이언트 ID
- `NAVER_CLIENT_SECRET` - 네이버 클라이언트 시크릿
- `JWT_SECRET` - JWT 시크릿 키 (최소 32바이트)
- `GH_PAT` - GitHub Personal Access Token

**선택 Secrets:**
- `SLACK_WEBHOOK` - 슬랙 웹훅 URL (배포 알림용)

### 3. EC2 인스턴스 설정

```bash
# SSH로 EC2 접속
ssh -i your-key.pem ubuntu@your-ec2-host

# 설정 스크립트 실행
wget https://raw.githubusercontent.com/[USERNAME]/devictoria-infrastructure/main/scripts/setup-ec2.sh
chmod +x setup-ec2.sh
./setup-ec2.sh

# 로그아웃 후 재접속 (Docker 그룹 적용)
exit
ssh -i your-key.pem ubuntu@your-ec2-host
```

### 4. 환경 변수 설정

```bash
# EC2에서 .env 파일 생성
nano /home/ubuntu/.env

# env.example 내용을 복사하여 실제 값으로 수정
# 파일 권한 설정
chmod 600 /home/ubuntu/.env
```

### 5. Nginx 설정

```bash
# Nginx 설정 파일 다운로드
sudo wget -O /etc/nginx/sites-available/devictoria \
  https://raw.githubusercontent.com/[USERNAME]/devictoria-infrastructure/main/nginx.conf

# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/devictoria /etc/nginx/sites-enabled/

# 기본 설정 제거
sudo rm /etc/nginx/sites-enabled/default

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 6. SSL 인증서 설정 (Let's Encrypt)

```bash
# Certbot 설치
sudo apt install -y certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d api.devictoria.shop
sudo certbot --nginx -d chat.devictoria.shop
sudo certbot --nginx -d vision.devictoria.shop

# 자동 갱신 테스트
sudo certbot renew --dry-run
```

## 🔄 배포 방법

### 자동 배포 (GitHub Actions)

**main 브랜치에 Push하면 자동 배포:**

```bash
# 서브모듈 업데이트
cd api.devictoria.shop
git pull origin main
cd ..

# 변경사항 커밋
git add api.devictoria.shop
git commit -m "Update API service"
git push origin main

# GitHub Actions가 자동으로 빌드 및 배포 실행
```

**수동 트리거 (GitHub Actions 탭에서):**
1. GitHub 저장소 → Actions 탭
2. 원하는 워크플로우 선택 (예: Deploy All Services)
3. "Run workflow" 버튼 클릭

### 수동 배포 (스크립트 사용)

```bash
# 환경 변수 설정
export EC2_HOST="your-ec2-host.com"
export SSH_KEY="~/.ssh/devictoria-key.pem"

# 배포 실행
./scripts/deploy-to-ec2.sh
```

## 🔙 롤백

문제가 발생한 경우 이전 버전으로 롤백:

```bash
# 특정 버전으로 롤백
./scripts/rollback.sh api v1.0.0

# 이전 버전으로 자동 롤백
./scripts/rollback.sh chatbot previous

# 모든 서비스 롤백
./scripts/rollback.sh api previous
./scripts/rollback.sh chatbot previous
./scripts/rollback.sh vision previous
```

## 📊 모니터링

### Health Check

```bash
# API 서비스
curl https://api.devictoria.shop/actuator/health

# Chat 서비스
curl https://chat.devictoria.shop/health

# Vision 서비스
curl https://vision.devictoria.shop/health
```

### 로그 확인

```bash
# EC2에서 Docker 로그 확인
docker logs api -f
docker logs chatbot -f
docker logs vision -f

# Docker Compose 로그
docker-compose -f docker-compose.prod.yml logs -f
```

### 서비스 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker ps

# Docker Compose 상태
docker-compose -f docker-compose.prod.yml ps

# 리소스 사용량
docker stats
```

## 🔧 문제 해결

### 컨테이너가 시작되지 않는 경우

```bash
# 로그 확인
docker logs <container-name>

# 컨테이너 재시작
docker restart <container-name>

# 컨테이너 재생성
docker stop <container-name>
docker rm <container-name>
docker-compose -f docker-compose.prod.yml up -d <service-name>
```

### 디스크 공간 부족

```bash
# 사용하지 않는 이미지 정리
docker image prune -af

# 볼륨 정리
docker volume prune -f

# 전체 정리 (주의!)
docker system prune -af --volumes
```

### 서브모듈 업데이트 문제

```bash
# 서브모듈 강제 업데이트
git submodule update --init --recursive --force

# 서브모듈 리셋
git submodule foreach --recursive git reset --hard
git submodule update --remote
```

## 📚 참고 문서

- [CI/CD 전략 문서](./CICD_STRATEGY.md) - 상세한 CI/CD 파이프라인 설명
- [API 문서](./api.devictoria.shop/PROJECT_DOCUMENTATION.md)
- [아키텍처 문서](./api.devictoria.shop/ARCHITECTURE.md)

## 🤝 기여

1. Feature 브랜치 생성 (`git checkout -b feature/amazing-feature`)
2. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
3. 브랜치 Push (`git push origin feature/amazing-feature`)
4. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 📞 문의

문제가 발생하거나 질문이 있으신 경우 이슈를 생성해주세요.

---

**Last Updated:** 2026-01-07  
**Version:** 1.0.0

