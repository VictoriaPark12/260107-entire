# DevVictoria CI/CD 설정 체크리스트

이 체크리스트를 사용하여 CI/CD 파이프라인 설정의 모든 단계를 완료했는지 확인하세요.

## ✅ 1. GitHub 설정

### 저장소 생성
- [ ] `api.devictoria.shop` 저장소 생성 및 코드 업로드
- [ ] `chat.devictoria.shop` 저장소 생성 및 코드 업로드
- [ ] `yolo.devictoria.shop` 저장소 생성 및 코드 업로드
- [ ] `devictoria-infrastructure` 메인 저장소 생성

### 서브모듈 설정
- [ ] api 서비스 서브모듈 추가
- [ ] chat 서비스 서브모듈 추가
- [ ] yolo 서비스 서브모듈 추가
- [ ] `.gitmodules` 파일 커밋

### GitHub Secrets 설정
- [ ] `DOCKER_USERNAME` 추가
- [ ] `DOCKER_PASSWORD` 추가
- [ ] `EC2_HOST` 추가
- [ ] `EC2_SSH_KEY` 추가
- [ ] `AWS_ACCESS_KEY_ID` 추가
- [ ] `AWS_SECRET_ACCESS_KEY` 추가
- [ ] `KAKAO_REST_API_KEY` 추가
- [ ] `GOOGLE_CLIENT_ID` 추가
- [ ] `GOOGLE_CLIENT_SECRET` 추가
- [ ] `NAVER_CLIENT_ID` 추가
- [ ] `NAVER_CLIENT_SECRET` 추가
- [ ] `JWT_SECRET` 추가 (32바이트 이상)
- [ ] `GH_PAT` (Personal Access Token) 추가
- [ ] `SLACK_WEBHOOK` 추가 (선택사항)

### GitHub Actions 워크플로우
- [ ] `.github/workflows/api-deploy.yml` 추가
- [ ] `.github/workflows/chat-deploy.yml` 추가
- [ ] `.github/workflows/yolo-deploy.yml` 추가
- [ ] `.github/workflows/deploy-all.yml` 추가
- [ ] 워크플로우 파일에서 경로 확인

---

## ✅ 2. Docker Hub 설정

- [ ] Docker Hub 계정 생성
- [ ] Access Token 생성
- [ ] `devictoria/api` 저장소 생성 (자동 생성 가능)
- [ ] `devictoria/chatbot` 저장소 생성 (자동 생성 가능)
- [ ] `devictoria/yolo` 저장소 생성 (자동 생성 가능)

---

## ✅ 3. AWS 인프라 설정

### EC2 인스턴스
- [ ] EC2 인스턴스 생성 (Ubuntu 22.04)
- [ ] 적절한 인스턴스 타입 선택 (t3.medium 이상)
- [ ] 보안 그룹 설정:
  - [ ] SSH (22) - 내 IP만
  - [ ] HTTP (80) - 0.0.0.0/0
  - [ ] HTTPS (443) - 0.0.0.0/0
  - [ ] API (8080) - 0.0.0.0/0
  - [ ] Services (9001-9002) - 0.0.0.0/0
- [ ] Elastic IP 할당 및 연결
- [ ] 키 페어 다운로드 및 안전하게 보관

### IAM 역할
- [ ] EC2용 IAM 역할 생성
- [ ] S3 액세스 권한 추가
- [ ] CloudWatch 권한 추가 (선택사항)
- [ ] EC2 인스턴스에 IAM 역할 연결

### S3 버킷
- [ ] S3 버킷 생성 (`devictoria-resources`)
- [ ] 버킷 정책 설정 (프라이빗)
- [ ] 폴더 구조 생성:
  - [ ] `models/yolo/`
  - [ ] `models/diffusers/`
  - [ ] `images/uploads/`
  - [ ] `images/results/`
  - [ ] `images/samples/`
  - [ ] `configs/`
- [ ] 라이프사이클 정책 설정 (선택사항)

### DNS 설정
- [ ] `api.devictoria.shop` A 레코드 추가
- [ ] `chat.devictoria.shop` A 레코드 추가
- [ ] `yolo.devictoria.shop` A 레코드 추가
- [ ] `cv.devictoria.shop` A 레코드 추가
- [ ] DNS 전파 확인 (`nslookup api.devictoria.shop`)

---

## ✅ 4. EC2 초기 설정

### SSH 접속
- [ ] SSH 키 권한 설정 (`chmod 600`)
- [ ] EC2에 SSH 접속 성공 확인

### 시스템 설정
- [ ] 시스템 패키지 업데이트
- [ ] Docker 설치 및 활성화
- [ ] Docker Compose 설치
- [ ] AWS CLI 설치
- [ ] Nginx 설치
- [ ] Docker 그룹에 사용자 추가
- [ ] 재로그인 후 Docker 명령어 권한 확인

### 디렉토리 생성
- [ ] `/home/ubuntu/logs` 생성
- [ ] `/home/ubuntu/chatbot-data` 생성
- [ ] `/home/ubuntu/yolo-models` 생성
- [ ] `/home/ubuntu/yolo-results` 생성

### 환경 변수 설정
- [ ] `/home/ubuntu/.env` 파일 생성
- [ ] 모든 필요한 환경 변수 입력
- [ ] 파일 권한 설정 (`chmod 600`)

---

## ✅ 5. 서비스별 설정

### API Service (Spring Boot)
- [ ] `Dockerfile` 작성 및 테스트
- [ ] `application.yaml` 프로덕션 설정
- [ ] Health Check 엔드포인트 구현 (`/actuator/health`)
- [ ] 로컬에서 Docker 빌드 테스트

### Chat Service (FastAPI)
- [ ] `Dockerfile` 작성 및 테스트
- [ ] `requirements.txt` 확인
- [ ] Health Check 엔드포인트 구현 (`/health`)
- [ ] 로컬에서 Docker 빌드 테스트

### YOLO Service (FastAPI)
- [ ] `Dockerfile` 작성 및 테스트
- [ ] `requirements.txt` 확인
- [ ] Health Check 엔드포인트 구현 (`/health`)
- [ ] 모델 파일 S3 업로드
- [ ] 로컬에서 Docker 빌드 테스트

---

## ✅ 6. Nginx 설정

- [ ] Nginx 설정 파일 작성 (`/etc/nginx/sites-available/devictoria`)
- [ ] 심볼릭 링크 생성
- [ ] 기본 설정 비활성화
- [ ] 설정 테스트 (`sudo nginx -t`)
- [ ] Nginx 재시작
- [ ] 각 도메인 접속 테스트 (HTTP)

---

## ✅ 7. SSL 인증서 설정

- [ ] Certbot 설치
- [ ] `api.devictoria.shop` SSL 인증서 발급
- [ ] `chat.devictoria.shop` SSL 인증서 발급
- [ ] `yolo.devictoria.shop` SSL 인증서 발급
- [ ] `cv.devictoria.shop` SSL 인증서 발급
- [ ] 자동 갱신 활성화
- [ ] 갱신 테스트 (`sudo certbot renew --dry-run`)
- [ ] 각 도메인 HTTPS 접속 테스트

---

## ✅ 8. 첫 배포

### 수동 배포 (테스트)
- [ ] `docker-compose.prod.yml` EC2에 업로드
- [ ] Docker Hub 로그인
- [ ] Docker Compose로 서비스 시작
- [ ] 모든 컨테이너 정상 실행 확인

### GitHub Actions 배포
- [ ] main 브랜치에 커밋 푸시
- [ ] GitHub Actions 워크플로우 실행 확인
- [ ] 빌드 성공 확인
- [ ] Docker Hub에 이미지 업로드 확인
- [ ] EC2에 배포 완료 확인
- [ ] 슬랙 알림 수신 확인 (설정한 경우)

---

## ✅ 9. 검증 및 테스트

### Health Check
- [ ] API: `curl https://api.devictoria.shop/actuator/health`
- [ ] Chat: `curl https://chat.devictoria.shop/health`
- [ ] YOLO: `curl https://yolo.devictoria.shop/health`
- [ ] 모든 서비스 "UP" 상태 확인

### 기능 테스트
- [ ] API 엔드포인트 테스트
- [ ] Chat 서비스 기능 테스트
- [ ] YOLO 이미지 처리 테스트
- [ ] 프론트엔드와 백엔드 연동 테스트

### 로그 확인
- [ ] Docker 컨테이너 로그 확인
- [ ] Nginx 액세스 로그 확인
- [ ] Nginx 에러 로그 확인
- [ ] 오류 없이 실행되는지 확인

---

## ✅ 10. 모니터링 및 알림

- [ ] CloudWatch Logs 설정 (선택사항)
- [ ] CloudWatch 알람 설정 (선택사항)
- [ ] 슬랙 알림 테스트
- [ ] Health Check 자동화 스크립트 작성 (선택사항)

---

## ✅ 11. 문서화

- [ ] README.md 작성
- [ ] CICD_STRATEGY.md 검토
- [ ] SETUP_GUIDE.md 검토
- [ ] QUICK_REFERENCE.md 검토
- [ ] 팀원과 문서 공유

---

## ✅ 12. 보안 체크

- [ ] GitHub Secrets 노출 여부 확인
- [ ] .env 파일이 Git에 커밋되지 않았는지 확인
- [ ] SSH 키 권한 확인 (600)
- [ ] S3 버킷 퍼블릭 액세스 차단 확인
- [ ] IAM 역할 최소 권한 원칙 적용
- [ ] EC2 보안 그룹 규칙 검토
- [ ] Docker 컨테이너 non-root 사용자 실행 (권장)

---

## ✅ 13. 백업 및 롤백 준비

- [ ] 롤백 스크립트 테스트
- [ ] 이전 버전 이미지 보관 확인 (Docker Hub)
- [ ] 데이터베이스 백업 전략 수립 (필요시)
- [ ] S3 버전 관리 활성화 확인

---

## ✅ 14. 최종 확인

- [ ] 모든 서비스 정상 작동 확인
- [ ] 프로덕션 환경에서 전체 플로우 테스트
- [ ] 부하 테스트 (선택사항)
- [ ] 팀원에게 배포 완료 알림
- [ ] 운영 매뉴얼 공유

---

## 📊 완료 상태

- **총 항목:** 150+
- **완료:** ___ / 150+
- **진행률:** ____%

---

## 🎉 완료 후 다음 단계

1. **모니터링 강화**
   - Prometheus + Grafana 설정
   - APM 도구 도입

2. **성능 최적화**
   - 캐시 레이어 추가 (Redis)
   - CDN 설정 (CloudFront)
   - 데이터베이스 최적화

3. **비용 최적화**
   - EC2 Spot Instance 고려
   - S3 Intelligent-Tiering
   - 리소스 사용량 분석

4. **보안 강화**
   - AWS WAF 설정
   - 정기 보안 스캔
   - 침투 테스트

5. **확장성 개선**
   - Kubernetes 마이그레이션 고려
   - 자동 스케일링 설정
   - 로드 밸런서 추가

---

**완료 날짜:** ___________  
**담당자:** ___________  
**검토자:** ___________

