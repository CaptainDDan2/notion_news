#!/bin/bash
# Google Cloud Run 배포 스크립트

set -e

# 변수 설정
PROJECT_ID=""  # YOUR_PROJECT_ID를 실제 프로젝트 ID로 변경
SERVICE_NAME="semiconductor-news"
REGION="us-central1" 
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "=== Google Cloud Run 배포 시작 ==="

# 1. 프로젝트 설정 확인
echo "프로젝트 확인: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# 2. API 활성화
echo "필요한 API 활성화..."
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 3. Docker 이미지 빌드
echo "Docker 이미지 빌드..."
docker build -t $SERVICE_NAME .

# 4. 이미지 태그 및 푸시
echo "GCR에 이미지 푸시..."
docker tag $SERVICE_NAME $IMAGE_NAME
docker push $IMAGE_NAME

# 5. Cloud Run 서비스 배포
echo "Cloud Run 서비스 배포..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 5000 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --set-env-vars "FLASK_ENV=production,FLASK_APP=main_run.py"

# 6. 환경 변수 설정 (OpenAI API 키)
echo "환경 변수 설정..."
echo "다음 명령어로 OpenAI API 키를 설정하세요:"
echo "gcloud run services update $SERVICE_NAME --region $REGION --set-env-vars OPENAI_API_KEY=YOUR_API_KEY"

# 7. 서비스 URL 가져오기
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

echo "=== 배포 완료 ==="
echo "서비스 URL: $SERVICE_URL"
echo "헬스 체크: $SERVICE_URL/health"