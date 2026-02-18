#!/bin/bash
# 빠른 배포 스크립트 - Render 무료 호스팅으로 1분 내에 배포

set -e  # 에러 발생 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  반도체 뉴스 앱 배포 스크립트${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. 필수 도구 확인
echo -e "\n${YELLOW}[1/5] 필수 도구 확인 중...${NC}"

check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1이(가) 설치되지 않았습니다.${NC}"
        echo "설치 방법: $2"
        exit 1
    fi
    echo -e "${GREEN}✓ $1 설치됨${NC}"
}

check_command "git" "https://git-scm.com/download"
check_command "python3" "https://www.python.org/downloads"

# 2. GitHub 설정
echo -e "\n${YELLOW}[2/5] GitHub 저장소 설정${NC}"

read -p "GitHub 사용자명을 입력하세요: " GITHUB_USER
read -p "저장소명을 입력하세요 (기본값: semiconductor-news): " REPO_NAME
REPO_NAME=${REPO_NAME:-semiconductor-news}

# GitHub 저장소 존재 여부 확인
REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

if [ -d ".git" ]; then
    echo -e "${GREEN}✓ Git 저장소 이미 초기화됨${NC}"
else
    echo "Git 저장소 초기화..."
    git init
    git config user.name "${GITHUB_USER}" || true
    git config user.email "${GITHUB_USER}@users.noreply.github.com" || true
fi

# 3. 코드 커밋 및 푸시
echo -e "\n${YELLOW}[3/5] GitHub에 코드 푸시${NC}"

git add .
git commit -m "Deploy: 반도체 뉴스 앱 배포" || true
git branch -M main || true

# 저장소 존재 확인 후 푸시
if git ls-remote --exit-code $REPO_URL >/dev/null 2>&1; then
    git remote set-url origin $REPO_URL || git remote add origin $REPO_URL
    echo -e "${GREEN}✓ 기존 저장소로 푸시${NC}"
else
    echo -e "${YELLOW}경고: GitHub 저장소가 아직 없습니다.${NC}"
    echo "다음 링크에서 새 저장소를 만드세요:"
    echo "https://github.com/new?name=${REPO_NAME}"
    read -p "저장소를 생성한 후 엔터를 누르세요..."
    git remote set-url origin $REPO_URL || git remote add origin $REPO_URL
fi

git push -u origin main || true
echo -e "${GREEN}✓ GitHub에 푸시 완료${NC}"

# 4. Render 배포 안내
echo -e "\n${YELLOW}[4/5] Render 배포 설정${NC}"

cat << 'EOF'

🚀 Render에서 자동 배포하기:

1. https://render.com 접속
2. GitHub 계정으로 로그인
3. "New +" → "Web Service" 선택
4. Repository 찾기: semiconductor-news
5. 다음 설정 입력:
   - Root Directory: (비워두기)
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn --workers=1 --bind=0.0.0.0:$PORT wsgi:app
   - Plan: Free (무료)
   - Environment: Python 3.11
6. "Create Web Service" 클릭
7. 배포 완료 (약 5-10분 대기)

백그라운드 크롤러 추가하기:
1. "New +" → "Background Worker"
2. 같은 Repository 선택
3. Start Command: python news_crawler.py --schedule
4. "Create Background Worker" 클릭

EOF

read -p "Render에 배포를 완료했으면 엔터를 누르세요..."

# 5. 배포 확인
echo -e "\n${YELLOW}[5/5] 배포 상태 확인 중...${NC}"

read -p "Render에서 받은 앱 URL을 입력하세요 (예: https://app.onrender.com): " APP_URL

# 헬스체크
sleep 3
if curl -s "${APP_URL}/health" > /dev/null; then
    echo -e "${GREEN}✓ 앱이 정상적으로 배포되었습니다!${NC}"
else
    echo -e "${YELLOW}⚠ 앱이 아직 시작 중일 수 있습니다. 1-2분 후 확인해주세요.${NC}"
fi

# 6. 완료 안내
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"

cat << EOF

📱 모바일 앱 설치:

**iOS (Safari):**
1. Safari에서 $APP_URL 접속
2. 공유 → "홈 화면에 추가"
3. "추가"를 탭

**Android (Chrome):**
1. Chrome에서 $APP_URL 접속
2. 메뉴 (⋮) → "앱 설치"
3. "설치" 확인

🔧 환경 변수 설정:
Render 대시보드에서 다음을 추가하세요:
- OPENAI_API_KEY: (OpenAI API 키)
- SECRET_KEY: (무작위 문자열)
- FLASK_ENV: production

📚 더 알아보기:
- Deployment Guide: cat MOBILE_DEPLOYMENT.md
- External Service Guide: cat EXTERNAL_SERVICE_GUIDE.md
- Quick Start: cat QUICK_START.md

💬 문제 발생 시:
- Render 로그 확인: https://dashboard.render.com
- GitHub Issues 생성: https://github.com/${GITHUB_USER}/${REPO_NAME}/issues

EOF

echo -e "\n${GREEN}✓ 배포 스크립트 완료!${NC}"
