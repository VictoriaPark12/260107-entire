#!/bin/bash
set -e

# 사용법: ./rollback.sh <service> <version>
# 예시: ./rollback.sh api v1.0.0

SERVICE=$1
VERSION=${2:-previous}

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service> [version]"
    echo "Services: api, chatbot, vision"
    echo ""
    echo "Examples:"
    echo "  $0 api v1.0.0          # Roll back to specific version"
    echo "  $0 chatbot previous    # Roll back to previous version"
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
    echo "🛑 Stopping current container..."
    docker stop $SERVICE || true
    docker rm $SERVICE || true
    
    echo "📥 Pulling version $VERSION..."
    docker pull devictoria/$SERVICE:$VERSION
    
    # 환경 변수 로드
    if [ -f /home/ubuntu/.env ]; then
        source /home/ubuntu/.env
    fi
    
    # 서비스별 실행 명령
    echo "🚀 Starting container with version $VERSION..."
    case "$SERVICE" in
        api)
            docker run -d \
                --name api \
                --restart unless-stopped \
                -p 8080:8080 \
                -e SPRING_PROFILES_ACTIVE=prod \
                -e KAKAO_REST_API_KEY="\$KAKAO_REST_API_KEY" \
                -e GOOGLE_CLIENT_ID="\$GOOGLE_CLIENT_ID" \
                -e GOOGLE_CLIENT_SECRET="\$GOOGLE_CLIENT_SECRET" \
                -e NAVER_CLIENT_ID="\$NAVER_CLIENT_ID" \
                -e NAVER_CLIENT_SECRET="\$NAVER_CLIENT_SECRET" \
                -e JWT_SECRET="\$JWT_SECRET" \
                -e AWS_REGION="ap-northeast-2" \
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
        vision)
            docker run -d \
                --name vision \
                --restart unless-stopped \
                -p 9001:9001 \
                -e AWS_REGION="ap-northeast-2" \
                -e S3_BUCKET="\$S3_BUCKET" \
                -v /home/ubuntu/vision-models:/app/models \
                -v /home/ubuntu/vision-results:/app/results \
                devictoria/vision:$VERSION
            ;;
        *)
            echo "❌ Unknown service: $SERVICE"
            exit 1
            ;;
    esac
    
    # Health Check
    echo "⏳ Waiting for service to start..."
    sleep 10
    
    echo "📊 Container status:"
    docker ps | grep $SERVICE
EOF

echo ""
echo "✅ Rollback completed to version: $VERSION"
echo ""
echo "Verify the service is working:"
case "$SERVICE" in
    api)
        echo "  curl http://$EC2_HOST:8080/actuator/health"
        ;;
    chatbot)
        echo "  curl http://$EC2_HOST:9002/health"
        ;;
    vision)
        echo "  curl http://$EC2_HOST:9001/health"
        ;;
esac

