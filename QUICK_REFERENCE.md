# DevVictoria CI/CD 빠른 참조 가이드

## 🚀 빠른 명령어

### GitHub Actions 수동 실행

```bash
# GitHub 웹사이트
1. Actions 탭
2. 워크플로우 선택
3. "Run workflow" 버튼 클릭
```

### 서브모듈 업데이트

```bash
# 특정 서브모듈 업데이트
cd api.devictoria.shop
git pull origin main
cd ..
git add api.devictoria.shop
git commit -m "Update API submodule"
git push

# 모든 서브모듈 업데이트
git submodule update --remote --recursive
```

### 배포 스크립트

```bash
# 수동 배포
export EC2_HOST="your-ec2-host.com"
export SSH_KEY="~/.ssh/devictoria-key.pem"
./scripts/deploy-to-ec2.sh

# 롤백
./scripts/rollback.sh api previous
./scripts/rollback.sh chatbot v1.0.0
./scripts/rollback.sh vision previous

# S3 동기화
export S3_BUCKET="devictoria-resources"
./scripts/sync-s3-resources.sh
```

### Docker 명령어

```bash
# 컨테이너 상태 확인
docker ps

# 로그 확인
docker logs api -f
docker logs chatbot --tail 100
docker logs vision -f --since 10m

# 컨테이너 재시작
docker restart api
docker restart chatbot
docker restart vision

# 모든 컨테이너 재시작
docker-compose -f docker-compose.prod.yml restart

# 이미지 업데이트 및 재배포
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 정리
docker image prune -af
docker system prune -af
```

### Health Check

```bash
# 로컬
curl http://localhost:8080/actuator/health
curl http://localhost:9002/health
curl http://localhost:9001/health

# 프로덕션
curl https://api.devictoria.shop/actuator/health
curl https://chat.devictoria.shop/health
curl https://vision.devictoria.shop/health
```

### Nginx 명령어

```bash
# 설정 테스트
sudo nginx -t

# 재시작
sudo systemctl restart nginx

# 상태 확인
sudo systemctl status nginx

# 로그 확인
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### SSL 인증서

```bash
# 인증서 발급
sudo certbot --nginx -d api.devictoria.shop

# 인증서 갱신 테스트
sudo certbot renew --dry-run

# 인증서 갱신
sudo certbot renew

# 인증서 확인
sudo certbot certificates
```

## 📊 모니터링

### 시스템 리소스

```bash
# CPU, 메모리 사용률
top
htop

# 디스크 사용률
df -h

# Docker 리소스
docker stats

# 메모리 사용량
free -h
```

### 로그 확인

```bash
# Docker 로그
docker logs api --tail 100 -f
docker logs chatbot --since 30m
docker logs vision -f

# Nginx 로그
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# 시스템 로그
journalctl -u docker -f
```

## 🔧 문제 해결

### 컨테이너가 계속 재시작하는 경우

```bash
# 로그 확인
docker logs <container> --tail 50

# 컨테이너 상태 확인
docker inspect <container>

# 환경 변수 확인
docker exec <container> env

# 수동 실행 (디버깅)
docker run -it --rm <image> /bin/bash
```

### 포트가 이미 사용 중인 경우

```bash
# 포트 사용 프로세스 확인
sudo lsof -i :8080
sudo netstat -tulpn | grep 8080

# 프로세스 종료
sudo kill -9 <PID>
```

### 디스크 공간 부족

```bash
# 사용하지 않는 이미지 삭제
docker image prune -af

# 사용하지 않는 컨테이너 삭제
docker container prune -f

# 볼륨 정리
docker volume prune -f

# 전체 정리 (주의!)
docker system prune -af --volumes

# 로그 파일 정리
sudo find /var/log -type f -name "*.log" -mtime +7 -delete
```

### GitHub Actions 실패

```bash
# 1. Actions 탭에서 로그 확인
# 2. Secrets 확인
# 3. 로컬에서 Docker 빌드 테스트

cd api.devictoria.shop
docker build -t test .

# 4. 서브모듈 업데이트
git submodule update --init --recursive
```

## 🔐 보안

### SSH 키 권한 설정

```bash
chmod 600 ~/.ssh/devictoria-key.pem
```

### 환경 변수 파일 권한

```bash
chmod 600 /home/ubuntu/.env
```

### 방화벽 규칙

```bash
# UFW 상태 확인
sudo ufw status

# 포트 열기
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp

# UFW 활성화
sudo ufw enable
```

## 📦 S3 작업

```bash
# 파일 업로드
aws s3 cp local-file.txt s3://devictoria-resources/path/

# 디렉토리 동기화
aws s3 sync ./local-dir s3://devictoria-resources/models/

# 파일 다운로드
aws s3 cp s3://devictoria-resources/file.txt ./

# 버킷 내용 확인
aws s3 ls s3://devictoria-resources/ --recursive
```

## 🔄 일반적인 워크플로우

### 새 기능 배포

```bash
# 1. 코드 수정
cd api.devictoria.shop
# ... 코드 수정 ...
git add .
git commit -m "Add new feature"
git push origin main

# 2. 서브모듈 업데이트
cd ..
git add api.devictoria.shop
git commit -m "Update API submodule"
git push origin main

# 3. GitHub Actions가 자동으로 배포 실행
# 4. Health Check 확인
curl https://api.devictoria.shop/actuator/health
```

### 긴급 롤백

```bash
# 1. 문제 확인
curl https://api.devictoria.shop/actuator/health

# 2. 로그 확인
ssh ubuntu@ec2-host
docker logs api --tail 100

# 3. 즉시 롤백
./scripts/rollback.sh api previous

# 4. Health Check
curl https://api.devictoria.shop/actuator/health
```

### 정기 유지보수

```bash
# 1. 서버 업데이트
ssh ubuntu@ec2-host
sudo apt update && sudo apt upgrade -y

# 2. Docker 정리
docker system prune -af

# 3. 로그 정리
sudo find /var/log -name "*.log" -mtime +30 -delete

# 4. 인증서 갱신 확인
sudo certbot renew --dry-run

# 5. 백업 (필요시)
# ... 백업 스크립트 실행 ...
```

## 📞 긴급 연락처

- **GitHub Issues**: https://github.com/[USERNAME]/devictoria-infrastructure/issues
- **Slack**: #devictoria-alerts (설정된 경우)
- **AWS Console**: https://console.aws.amazon.com

## 🔗 유용한 링크

- [CI/CD 전략 문서](./CICD_STRATEGY.md)
- [설정 가이드](./SETUP_GUIDE.md)
- [README](./README.md)
- [API 문서](./api.devictoria.shop/PROJECT_DOCUMENTATION.md)

---

**Last Updated:** 2026-01-07

