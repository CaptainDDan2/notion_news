#!/bin/bash
# AWS ECS 배포 스크립트

set -e

# 변수 설정
REGION="us-east-1"
CLUSTER_NAME="semiconductor-news"
SERVICE_NAME="news-service"
FAMILY="semiconductor-news-app"
ECR_REGISTRY=""  # YOUR_ACCOUNT.dkr.ecr.YOUR_REGION.amazonaws.com
IMAGE_TAG="latest"

echo "=== AWS ECS 배포 시작 ==="

# 1. Docker 이미지 빌드
echo "Docker 이미지 빌드 중..."
docker build -t semiconductor-news .

# 2. ECR 로그인
echo "ECR 로그인..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# 3. 이미지 태그 및 푸시
echo "이미지 태그 및 푸시..."
docker tag semiconductor-news:latest $ECR_REGISTRY/semiconductor-news:$IMAGE_TAG
docker push $ECR_REGISTRY/semiconductor-news:$IMAGE_TAG

# 4. 새 태스크 정의 등록
echo "새 태스크 정의 등록..."
TASK_DEFINITION=$(aws ecs register-task-definition \
    --cli-input-json file://deploy/aws/ecs-task-definition.json \
    --query 'taskDefinition.revision' \
    --output text)

echo "새 태스크 정의 리비전: $TASK_DEFINITION"

# 5. 서비스 업데이트
echo "서비스 업데이트..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition $FAMILY:$TASK_DEFINITION \
    --region $REGION

# 6. 배포 완료 대기
echo "배포 완료 대기..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION

echo "=== 배포 완료 ==="

# 7. 서비스 상태 확인
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'