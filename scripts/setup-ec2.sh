#!/bin/bash
set -e

echo "🚀 Setting up EC2 instance for DevVictoria..."

# 시스템 업데이트
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Docker 설치
echo "🐳 Installing Docker..."
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu

# AWS CLI 설치
echo "☁️ Installing AWS CLI..."
sudo apt install -y awscli

# Nginx 설치
echo "🌐 Installing Nginx..."
sudo apt install -y nginx
sudo systemctl enable nginx

# 필요한 디렉토리 생성
echo "📁 Creating directories..."
mkdir -p /home/ubuntu/logs
mkdir -p /home/ubuntu/chatbot-data
mkdir -p /home/ubuntu/vision-models
mkdir -p /home/ubuntu/vision-results

# Docker Compose 다운로드
echo "📥 Downloading docker-compose.prod.yml..."
# wget -O /home/ubuntu/docker-compose.prod.yml https://raw.githubusercontent.com/[USERNAME]/devictoria-infrastructure/main/docker-compose.prod.yml

# IAM 역할 확인
echo "🔐 Checking IAM role..."
aws sts get-caller-identity || echo "⚠️ AWS credentials not configured"

# 방화벽 설정 (UFW)
echo "🔒 Configuring firewall..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8080/tcp  # API
sudo ufw allow 9001/tcp  # Vision
sudo ufw allow 9002/tcp  # Chat
sudo ufw --force enable

# Docker 그룹 적용을 위해 로그아웃 필요
echo ""
echo "✅ EC2 setup completed!"
echo ""
echo "⚠️ Important: Log out and log back in for Docker group changes to take effect."
echo "   Run: exit"
echo "   Then reconnect to the server."
echo ""
echo "Next steps:"
echo "1. Create /home/ubuntu/.env file with your environment variables"
echo "2. Configure Nginx (see CICD_STRATEGY.md for config)"
echo "3. Run Docker Compose: docker-compose -f docker-compose.prod.yml up -d"

