# 반도체 뉴스 애플리케이션 배포 가이드

## Docker 빌드 및 실행

### 1. 로컬 Docker 빌드
```bash
# Docker 이미지 빌드
docker build -t semiconductor-news .

# 컨테이너 실행
docker run -p 5000:5000 -e OPENAI_API_KEY=your_api_key semiconductor-news
```

### 2. Docker Compose 사용
```bash
# 프로덕션 환경 실행
docker-compose up -d

# 개발 환경 실행
docker-compose --profile dev up -d

# 중지
docker-compose down
```

## 클라우드 배포 옵션

### 1. AWS ECS (권장)
- **Fargate 서비스**: 서버리스 컨테이너 실행
- **Application Load Balancer**: 로드 밸런싱 및 트래픽 분산  
- **RDS**: 데이터베이스 (SQLite → PostgreSQL 전환 권장)

#### ECS 배포 스크립트
```bash
# ECS 클러스터 생성
aws ecs create-cluster --cluster-name semiconductor-news

# 태스크 정의 등록 
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# 서비스 생성
aws ecs create-service \
  --cluster semiconductor-news \
  --service-name news-service \
  --task-definition news-app:1 \
  --desired-count 2
```

### 2. Google Cloud Run
```bash
# GCR에 이미지 푸시
docker tag semiconductor-news gcr.io/YOUR_PROJECT/semiconductor-news
docker push gcr.io/YOUR_PROJECT/semiconductor-news

# Cloud Run 배포
gcloud run deploy semiconductor-news \
  --image gcr.io/YOUR_PROJECT/semiconductor-news \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 3. Azure Container Instances
```bash
# 리소스 그룹 생성
az group create --name semiconductor-news --location eastus

# 컨테이너 인스턴스 생성
az container create \
  --resource-group semiconductor-news \
  --name semiconductor-news-app \
  --image semiconductor-news \
  --cpu 2 \
  --memory 4 \
  --restart-policy Always \
  --ports 5000
```

### 4. Digital Ocean App Platform
```yaml
# .do/app.yaml
name: semiconductor-news
services:
- name: web
  source_dir: /
  github:
    repo: your-username/semiconductor-news
    branch: main
  run_command: python main_run.py --web
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 5000
  env:
  - key: OPENAI_API_KEY
    scope: RUN_AND_BUILD_TIME
    value: ${OPENAI_API_KEY}
```

## 환경 변수 설정

### 필수 환경 변수
- `OPENAI_API_KEY`: OpenAI API 키
- `FLASK_ENV`: 환경 설정 (production/development)

### 선택적 환경 변수  
- `DATABASE_URL`: PostgreSQL 연결 문자열 (클라우드용)
- `REDIS_URL`: Redis 연결 문자열 (세션 관리용)

## 모니터링 및 로깅

### 1. 애플리케이션 로그
- 컨테이너 로그: `docker logs <container_id>`
- 클라우드 서비스별 로깅 시스템 활용

### 2. 헬스 체크 
- 엔드포인트: `/health`
- 모니터링 도구와 연동 가능

### 3. 백업 전략
- 데이터베이스 정기 백업
- 북마크 및 사용자 설정 데이터 보존

## 성능 최적화

### 1. 캐싱 전략
- Redis 캐시 도입
- 정적 파일 CDN 활용

### 2. 스케일링
- 수평적 확장 (여러 인스턴스)
- 로드 밸런서 설정

### 3. 보안
- HTTPS 인증서 설정
- 환경 변수를 통한 시크릿 관리
- 방화벽 및 접근 제어