# 📱 모바일 앱 배포 가이드 (무료~$10/월)

## 1단계: GitHub Repository 설정 (무료)

```bash
# GitHub에 코드 푸시
git init
git add .
git commit -m "반도체 뉴스 앱 초기 커밋"
git branch -M main
git remote add origin https://github.com/your-username/semiconductor-news.git
git push -u origin main
```

## 2단계: Render에 배포 (무료 호스팅)

### A. 계정 생성 및 연결
1. https://render.com 접속
2. GitHub 계정으로 로그인
3. Repository 연결

### B. 웹 서비스 배포
```
1. "New +" → "Web Service"
2. Repository 선택: semiconductor-news
3. Environment: Python 3.11
4. Build command: pip install -r requirements.txt
5. Start command: gunicorn --workers=1 --bind=0.0.0.0:$PORT wsgi:app
6. Plan: Free (무료)
7. "Create Web Service" 클릭
```

### C. 백그라운드 크롤러 배포
```
1. "New +" → "Background Worker"
2. 같은 Repository 선택
3. Start command: python news_crawler.py --schedule
4. Plan: Free (무료)
5. "Create Background Worker" 클릭
```

**배포 시간**: 약 5-10분

## 3단계: PWA 앱 설정

### A. manifest.json 등록
HTML 헤드에 추가:
```html
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#1a1a1a">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
```

### B. Service Worker 등록
```html
<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/service-worker.js')
    .then(reg => console.log('Service Worker 등록됨'))
    .catch(err => console.error('등록 실패:', err));
}
</script>
```

## 4단계: 모바일 앱 설치

### iOS (Safari)
1. `share` → "홈 화면에 추가"
2. 앱 이름 입력
3. 완료!

### Android (Chrome)
1. 메뉴 (⋮) → "앱 설치"
2. 또는 자동 팝업 표시
3. "설치" 클릭

## 5단계: 환경 변수 설정

Render 대시보드에서:
```
1. 웹 서비스 선택
2. "Environment" → "Add Environment Variable"
3. 추가할 변수:
   - OPENAI_API_KEY: sk-... (무료 또는 저가 사용)
   - SECRET_KEY: 랜덤 문자열
   - FLASK_ENV: production
   - DATABASE_URL: sqlite:///news_database.db
```

## 6단계: 도메인 설정 (선택사항)

### 무료 도메인
- Render에서 자동으로 제공: `https://semiconductor-news.onrender.com`

### 커스텀 도메인 (선택사항)
```
1. Freenom.com에서 무료 도메인 구매 (.tk, .ml 등)
2. Render 설정 → "Custom Domain"
3. DNS 레코드 설정 (CNAME)
```

## 💰 비용 분석

| 서비스 | 무료 플랜 | 비용 | 비고 |
|--------|----------|------|------|
| Render 호스팅 | ✅ 750시간/월 | $0 | 웹 서비스 + 크롤러 |
| Render DB | ✅ 무료 | $0 | PostgreSQL 또는 SQLite |
| GitHub | ✅ 무료 | $0 | 코드 호스팅 |
| OpenAI API | ⚠️ 유료 | $5~10 | 요약 생성 (필수) |
| 도메인 | ⚠️ 선택 | $0~12 | Render 기본 도메인 무료 |
| **총계** | | **$5~10/월** | |

## ✅ 배포 확인

```bash
# 1. 배포 상태 확인
curl https://your-app.onrender.com/health

# 2. API 테스트
curl https://your-app.onrender.com/api/articles

# 3. 뉴스 크롤링 상태
curl https://your-app.onrender.com/api/crawler-status
```

## 🔒 보안 체크리스트

- [ ] HTTPS 활성화 (Render 기본 제공)
- [ ] OpenAI API 키 환경 변수로 설정
- [ ] CORS 동일 출처 정책 적용
- [ ] 데이터베이스 백업 자동화
- [ ] 로그 모니터링 설정

## 🚀 배포 후 최적화

### 1. 성능 개선
```bash
# 요청 로깅 최소화
FLASK_ENV=production gunicorn --workers=1 --log-level warning wsgi:app
```

### 2. 자동 업데이트
GitHub Push → 자동으로 Render 배포

### 3. 모니터링
- Render 대시보드에서 실시간 로그 확인
- 일일 크롤링 성공/실패 로그 확인

## 💡 팁

### 절전 모드 방지
```python
# Render는 15분 이상 요청 없으면 절전
# Health check 엔드포인트 추가
@app.route('/health')
def health():
    return {'status': 'ok'}, 200

# 외부에서 정기적 ping
# https://cron-job.org 리셋기 사용
```

### 비용 절감
1. **OpenAI 토큰 절감**
   - 직전 요약은 캐싱
   - 배치 처리로 API 호출 최소화

2. **크롤링 최적화**
   - 6시간마다 자동 크롤링
   - 30일 이상 된 기사 자동 삭제

3. **데이터베이스 최적화**
   - 인덱스 추가
   - 정기적 백업

## 📞 문제 해결

### 배포 실패
```
1. Build logs 확인: Render 대시보드
2. requirements.txt 의존성 확인
3. Python 버전 호환성 확인
```

### 크롤링 실패
```
1. 백그라운드 워커 로그 확인
2. 뉴스 사이트 접근 가능 확인
3. API 키 유효성 확인
```

### 느린 응답
```
1. 데이터베이스 쿼리 최적화
2. 캐싱 강화
3. 정적 파일 CDN 사용 (선택사항)
```
