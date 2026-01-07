# 경로 변경 사항 (YOLO/CV → Vision)

## 📋 변경 요약

서비스 이름을 `yolo.devictoria.shop` / `cv.devictoria.shop` 에서 **`vision.devictoria.shop`** 으로 통합/변경했습니다.

---

## 🔄 변경된 파일 목록

### 1. GitHub Actions 워크플로우
- ✅ `.github/workflows/yolo-deploy.yml` → **`vision-deploy.yml`** (파일명 변경)
- ✅ `.github/workflows/deploy-all.yml` (내용 업데이트)

### 2. 스크립트 파일
- ✅ `scripts/setup-ec2.sh`
- ✅ `scripts/deploy-to-ec2.sh`
- ✅ `scripts/rollback.sh`

### 3. 설정 파일
- ✅ `docker-compose.prod.yml`
- ✅ `nginx.conf`
- ✅ `.gitmodules.example`

### 4. 문서 파일
- ✅ `README.md`
- ✅ `QUICK_REFERENCE.md`
- ⚠️ `CICD_STRATEGY.md` (업데이트 필요)
- ⚠️ `SETUP_GUIDE.md` (업데이트 필요)
- ⚠️ `CHECKLIST.md` (업데이트 필요)

---

## 📝 주요 변경 사항

### 서비스 이름
```
yolo → vision
```

### Docker 이미지
```
devictoria/yolo → devictoria/vision
```

### 디렉토리 경로
```
/home/ubuntu/yolo-models  → /home/ubuntu/vision-models
/home/ubuntu/yolo-results → /home/ubuntu/vision-results
```

### S3 경로
```
s3://devictoria-resources/models/yolo/ → s3://devictoria-resources/models/vision/
```

### 도메인
```
yolo.devictoria.shop → vision.devictoria.shop
cv.devictoria.shop   → (제거, vision으로 통합)
```

### 서브모듈
```
yolo.devictoria.shop/ → vision.devictoria.shop/
```

---

## ✅ 완료된 작업

1. ✅ GitHub Actions 워크플로우 파일명 변경
2. ✅ 모든 스크립트 내 경로 변경
3. ✅ Docker Compose 설정 업데이트
4. ✅ Nginx 설정 업데이트
5. ✅ README.md 업데이트
6. ✅ QUICK_REFERENCE.md 업데이트
7. ✅ .gitmodules.example 업데이트

---

## ⚠️ 추가 작업 필요

### GitHub 저장소
```bash
# 새 저장소 이름으로 생성 필요
# 이전: yolo.devictoria.shop 또는 cv.devictoria.shop
# 신규: vision.devictoria.shop
```

### 서브모듈 재설정
```bash
# 메인 저장소에서 실행
git submodule deinit -f vision.devictoria.shop  # 기존 서브모듈 제거 (있다면)
git rm -f vision.devictoria.shop

# 새 서브모듈 추가
git submodule add https://github.com/[USERNAME]/vision.devictoria.shop.git vision.devictoria.shop

git add .gitmodules vision.devictoria.shop
git commit -m "Rename service from yolo/cv to vision"
git push
```

### DNS 설정
```
- vision.devictoria.shop A 레코드 추가 → EC2 IP
- yolo.devictoria.shop 제거 또는 vision으로 리다이렉트 설정
- cv.devictoria.shop 제거 또는 vision으로 리다이렉트 설정
```

### EC2 디렉토리 생성
```bash
# SSH로 EC2 접속 후
mkdir -p /home/ubuntu/vision-models
mkdir -p /home/ubuntu/vision-results

# 기존 데이터 마이그레이션 (필요시)
# mv /home/ubuntu/yolo-models/* /home/ubuntu/vision-models/
# mv /home/ubuntu/yolo-results/* /home/ubuntu/vision-results/
```

### S3 경로 마이그레이션 (필요시)
```bash
# 기존 모델을 새 경로로 복사
aws s3 sync s3://devictoria-resources/models/yolo/ \
            s3://devictoria-resources/models/vision/
```

### SSL 인증서
```bash
# EC2에서 실행
sudo certbot --nginx -d vision.devictoria.shop
```

### Docker Hub
```
# Docker Hub에서 새 저장소 생성 (자동 생성됨)
devictoria/vision
```

---

## 🚀 배포 체크리스트

배포 전 확인사항:

- [ ] GitHub에 `vision.devictoria.shop` 저장소 생성
- [ ] 코드를 새 저장소에 push
- [ ] 메인 저장소에 서브모듈로 추가
- [ ] GitHub Secrets 확인 (기존과 동일하게 유지)
- [ ] DNS A 레코드 추가: `vision.devictoria.shop`
- [ ] EC2 디렉토리 생성: `/home/ubuntu/vision-models`, `/home/ubuntu/vision-results`
- [ ] S3 모델 파일 경로 확인
- [ ] GitHub Actions 워크플로우 수동 실행 테스트
- [ ] SSL 인증서 발급
- [ ] Health Check: `curl https://vision.devictoria.shop/health`

---

## 📚 참고 명령어

### 서브모듈 작업
```bash
# 서브모듈 상태 확인
git submodule status

# 서브모듈 업데이트
git submodule update --remote vision.devictoria.shop

# 모든 서브모듈 초기화
git submodule update --init --recursive
```

### 배포 테스트
```bash
# Health Check
curl http://EC2_IP:9001/health
curl https://vision.devictoria.shop/health

# Docker 로그
docker logs vision -f

# 컨테이너 상태
docker ps | grep vision
```

### 롤백 (문제 발생 시)
```bash
./scripts/rollback.sh vision previous
```

---

**작성일:** 2026-01-07  
**버전:** 1.0  
**상태:** 파일 업데이트 완료, 배포 대기 중

