# 🌐 도메인 설정 및 외부 서비스 제공 가이드

## 📋 설정 체크리스트

### 1. 도메인 설정
- [ ] 도메인 구매 (예: your-domain.com)
- [ ] DNS A 레코드 설정 → 서버 IP 주소
- [ ] DNS CNAME 레코드 설정 (www → your-domain.com)

### 2. 서버 준비 
- [ ] Ubuntu/CentOS 서버 준비
- [ ] 공인 IP 주소 할당
- [ ] SSH 접속 설정

## 🚀 빠른 배포 방법

### A. VPS/클라우드 서버 배포
```bash
# 1. 서버에 접속
ssh root@your-server-ip

# 2. 프로덕션 설치 스크립트 실행
git clone https://github.com/your-username/semiconductor-news.git
cd semiconductor-news
chmod +x deploy/scripts/production-setup.sh

# 3. 도메인 설정 후 실행
sudo ./deploy/scripts/production-setup.sh
```

### B. 환경 변수 설정
```bash
# 서버에서 .env 파일 수정
sudo nano /opt/semiconductor-news/.env
```

필수 설정:
- `DOMAIN=your-domain.com`
- `OPENAI_API_KEY=your-api-key`
- `SECRET_KEY=random-secure-key`
- `HTTPS_ONLY=true`

## 🔒 보안 강화 사항

### ✅ 현재 적용된 보안
1. **HTTPS 강제** - SSL/TLS 암호화
2. **보안 헤더** - XSS, Clickjacking 방지
3. **CORS 제한** - 허용된 도메인만 접근
4. **호스트 검증** - 허용된 호스트만 접근
5. **Session 보안** - HttpOnly, Secure 쿠키

### 🛡️ 추가 권장 보안
1. **방화벽 설정** - UFW/Firewalld
2. **SSH 키 인증** - 패스워드 로그인 비활성화
3. **자동 보안 업데이트**
4. **로그 모니터링**
5. **백업 시스템**

## 📊 성능 최적화

### 1. NGINX 설정
- 정적 파일 캐싱
- Gzip 압축
- HTTP/2 지원

### 2. 데이터베이스
- SQLite → PostgreSQL 전환 권장
- 인덱스 최적화
- 정기 백업

### 3. 캐싱
- Redis 도입
- 브라우저 캐싱

## 🌍 외부 서비스 접속 방법

### 접속 URL
```
https://your-domain.com
```

### API 엔드포인트
```
https://your-domain.com/api/articles
https://your-domain.com/api/stats  
https://your-domain.com/preferences
```

### WebSocket (실시간 알림)
```
wss://your-domain.com/socket.io/
```

## 📱 모바일 접근
- PWA 지원으로 앱처럼 설치 가능
- 모든 기능 모바일에서 사용 가능
- 오프라인 캐싱 지원

## 🔧 도메인 변경 방법

### 1. 환경 변수 업데이트
```bash
# .env 파일 수정
DOMAIN=new-domain.com
ALLOWED_HOSTS=new-domain.com,www.new-domain.com  
CORS_ORIGINS=https://new-domain.com,https://www.new-domain.com
```

### 2. NGINX 설정 업데이트
```bash
# NGINX 설정 파일 수정
sudo nano /etc/nginx/sites-available/semiconductor-news.conf
# server_name 변경

# SSL 인증서 재발급
sudo certbot --nginx -d new-domain.com -d www.new-domain.com
```

### 3. 서비스 재시작
```bash
sudo systemctl restart semiconductor-news
sudo systemctl reload nginx
```

## 🔍 모니터링 및 로그

### 애플리케이션 로그
```bash
# 실시간 로그 확인
sudo journalctl -u semiconductor-news -f

# 로그 파일 위치
/var/log/nginx/semiconductor-news.access.log
/var/log/nginx/semiconductor-news.error.log
```

### 시스템 상태 확인
```bash
# 서비스 상태
sudo systemctl status semiconductor-news
sudo systemctl status nginx

# 포트 확인
sudo netstat -tlnp | grep :5000
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

## ⚡ 트러블슈팅

### 일반적인 문제들

1. **502 Bad Gateway**
   - Flask 앱이 실행되지 않음 → systemctl status 확인
   - 포트 5000이 사용 중 → netstat 확인

2. **SSL 인증서 오류**
   - 도메인이 서버 IP를 정확히 가리키는지 확인
   - certbot renew로 갱신

3. **정적 파일 로드 실패**
   - NGINX 정적 파일 경로 확인
   - 파일 권한 확인

### 성능 문제
1. **느린 응답**
   - 데이터베이스 쿼리 최적화
   - 캐싱 도입
   
2. **높은 메모리 사용**
   - WebSocket 연결 수 제한
   - 가비지 컬렉션 조정

## 📞 지원 및 문의
- GitHub Issues: 기능 요청 및 버그 리포트
- 문서: [DEPLOYMENT.md](DEPLOYMENT.md)
- API 문서: `/api/articles` 엔드포인트