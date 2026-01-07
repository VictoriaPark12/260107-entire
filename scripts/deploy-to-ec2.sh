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
  # wget -O docker-compose.prod.yml https://raw.githubusercontent.com/[USERNAME]/devictoria-infrastructure/main/docker-compose.prod.yml
  
  # 환경 변수 로드
  if [ -f /home/ubuntu/.env ]; then
    source /home/ubuntu/.env
  else
    echo "⚠️ Warning: .env file not found"
  fi
  
  # Docker 로그인
  if [ -n "$DOCKER_USERNAME" ] && [ -n "$DOCKER_PASSWORD" ]; then
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
  fi
  
  # 서비스 재시작
  if [ -f docker-compose.prod.yml ]; then
    echo "📥 Pulling latest images..."
    docker-compose -f docker-compose.prod.yml pull
    
    echo "🔄 Restarting services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    echo "🧹 Cleaning up old images..."
    docker image prune -af
    
    echo "📊 Service status:"
    docker-compose -f docker-compose.prod.yml ps
  else
    echo "❌ docker-compose.prod.yml not found!"
    exit 1
  fi
EOF

echo "✅ Deployment completed!"
echo ""
echo "Check service health:"
echo "  API:    http://$EC2_HOST:8080/actuator/health"
echo "  Chat:   http://$EC2_HOST:9002/health"
echo "  Vision: http://$EC2_HOST:9001/health"

