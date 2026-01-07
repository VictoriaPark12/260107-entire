#!/bin/bash
set -e

S3_BUCKET=${S3_BUCKET:-"devictoria-resources"}
LOCAL_DIR="./resources"

echo "📦 Syncing resources to S3 bucket: $S3_BUCKET"

# AWS CLI가 설치되어 있는지 확인
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed"
    exit 1
fi

# AWS 자격 증명 확인
echo "🔐 Checking AWS credentials..."
aws sts get-caller-identity || {
    echo "❌ AWS credentials not configured"
    exit 1
}

# 모델 업로드
if [ -d "$LOCAL_DIR/models" ]; then
    echo "📤 Uploading models..."
    aws s3 sync "$LOCAL_DIR/models" "s3://$S3_BUCKET/models/" \
        --exclude "*.pyc" \
        --exclude "__pycache__/*" \
        --exclude "*.git*" \
        --storage-class STANDARD_IA
    echo "✅ Models uploaded"
else
    echo "⚠️ Models directory not found: $LOCAL_DIR/models"
fi

# 샘플 이미지 업로드
if [ -d "$LOCAL_DIR/samples" ]; then
    echo "📤 Uploading sample images..."
    aws s3 sync "$LOCAL_DIR/samples" "s3://$S3_BUCKET/images/samples/" \
        --acl public-read
    echo "✅ Sample images uploaded"
else
    echo "⚠️ Samples directory not found: $LOCAL_DIR/samples"
fi

# 설정 파일 업로드
if [ -d "$LOCAL_DIR/configs" ]; then
    echo "📤 Uploading config files..."
    aws s3 sync "$LOCAL_DIR/configs" "s3://$S3_BUCKET/configs/" \
        --exclude "*.local.*" \
        --exclude "*.env"
    echo "✅ Config files uploaded"
else
    echo "⚠️ Configs directory not found: $LOCAL_DIR/configs"
fi

echo ""
echo "✅ S3 sync completed!"
echo ""
echo "View your S3 bucket:"
echo "  aws s3 ls s3://$S3_BUCKET/ --recursive --human-readable"

