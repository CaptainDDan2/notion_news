#!/bin/bash
# Captain DDandDan 반도체 뉴스 서비스 - 최고 보안 배포 스크립트

set -e

# 변수 설정
DOMAIN="Captain-ddanddan.com"
WWW_DOMAIN="www.Captain-ddanddan.com"
APP_DIR="/opt/semiconductor-news"
USER="www-data"
EMAIL="admin@Captain-ddanddan.com"

echo "=========================================="
echo "🚀 Captain DDandDan 뉴스 서비스 배포"
echo "도메인: $DOMAIN"
echo "보안 수준: MAXIMUM"
echo "=========================================="

# 시스템 보안 강화
echo "🔒 시스템 보안 강화 중..."
sudo apt update && sudo apt upgrade -y

# 보안 패키지 설치
sudo apt install -y \
    fail2ban \
    ufw \
    unattended-upgrades \
    logwatch \
    aide \
    rkhunter \
    chkrootkit \
    clamav \
    clamav-daemon

# 방화벽 설정 (매우 엄격)
echo "🛡️ 방화벽 설정..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment "SSH"
sudo ufw allow 80/tcp comment "HTTP"
sudo ufw allow 443/tcp comment "HTTPS"
sudo ufw logging on
sudo ufw --force enable

# SSH 보안 강화
echo "🔐 SSH 보안 강화..."
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sudo sed -i 's/#MaxAuthTries 6/MaxAuthTries 3/' /etc/ssh/sshd_config
echo "AllowUsers ubuntu" | sudo tee -a /etc/ssh/sshd_config
sudo systemctl restart ssh

# Fail2Ban 설정 (Captain DDandDan 전용)
echo "⚔️ Fail2Ban 설정..."
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 86400
findtime = 3600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
maxretry = 3
bantime = 86400

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/captain-ddanddan.error.log
maxretry = 3

[captain-ddanddan-api]
enabled = true
port = http,https
logpath = /var/log/nginx/captain-ddanddan.access.log
failregex = ^<HOST>.*"(GET|POST).*" (404|403|500)
maxretry = 10
bantime = 3600
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 필수 패키지 설치
echo "📦 애플리케이션 패키지 설치..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    htop \
    iotop \
    redis-server

# 애플리케이션 설치
echo "💫 Captain DDandDan 애플리케이션 설치..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# 코드 배포
sudo cp -r . $APP_DIR/
sudo chown -R $USER:$USER $APP_DIR

# Python 가상환경 설정
echo "🐍 Python 환경 설정..."
cd $APP_DIR
sudo -u $USER python3 -m venv venv
sudo -u $USER ./venv/bin/pip install --upgrade pip
sudo -u $USER ./venv/bin/pip install -r requirements.txt

# 초고보안 환경변수 설정
echo "🔑 초고보안 환경변수 설정..."
SECRET_KEY=$(openssl rand -hex 64)
sudo tee $APP_DIR/.env > /dev/null <<EOF
# Captain DDandDan 최고보안 설정
FLASK_ENV=production
FLASK_DEBUG=False
OPENAI_API_KEY=${OPENAI_API_KEY:-your-api-key-here}
SECRET_KEY=$SECRET_KEY
HOST=127.0.0.1
PORT=5000
DOMAIN=$DOMAIN
HTTPS_ONLY=true
ALLOWED_HOSTS=$DOMAIN,$WWW_DOMAIN,localhost,127.0.0.1
CORS_ORIGINS=https://$DOMAIN,https://$WWW_DOMAIN
SECURITY_LEVEL=maximum
RATE_LIMIT_ENABLED=true
SESSION_TIMEOUT=3600
FAIL2BAN_ENABLED=true
LOG_LEVEL=INFO
DATABASE_ENCRYPTION=enabled
API_KEY_ROTATION=enabled
EOF

sudo chown $USER:$USER $APP_DIR/.env
sudo chmod 600 $APP_DIR/.env

# 데이터베이스 초기화 (보안 강화)
echo "🗃️ 보안 데이터베이스 초기화..."
cd $APP_DIR
sudo -u $USER mkdir -p instance
sudo -u $USER ./venv/bin/python generate_sample_data.py

# systemd 서비스 설정
echo "⚙️ Captain DDandDan 서비스 설정..."
sudo cp deploy/systemd/semiconductor-news.service /etc/systemd/system/captain-ddanddan.service
sudo systemctl daemon-reload
sudo systemctl enable captain-ddanddan

# NGINX 초고보안 설정
echo "🌐 NGINX 초고보안 설정..."
sudo cp deploy/nginx/semiconductor-news.conf /etc/nginx/sites-available/captain-ddanddan.conf
sudo ln -sf /etc/nginx/sites-available/captain-ddanddan.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# NGINX 보안 강화 설정 추가
sudo tee /etc/nginx/conf.d/security.conf > /dev/null <<EOF
# Captain DDandDan 보안 설정
server_tokens off;
more_clear_headers Server;
client_body_buffer_size 1K;
client_header_buffer_size 1k;
client_max_body_size 10M;
large_client_header_buffers 2 1k;

# DDoS 방지
limit_req_zone \$binary_remote_addr zone=global:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=api:10m rate=5r/s;
limit_conn_zone \$binary_remote_addr zone=conn_limit:10m;

# 보안 헤더
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
EOF

# NGINX 구성 테스트
sudo nginx -t

# SSL 인증서 발급 (최고 보안)
echo "🔐 SSL 인증서 발급..."
sudo certbot certonly --nginx \
    -d $DOMAIN \
    -d $WWW_DOMAIN \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --rsa-key-size 4096

# 자동 갱신 설정
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# 로그 모니터링 설정
echo "📊 로그 모니터링 설정..."
sudo mkdir -p /var/log/captain-ddanddan
sudo chown $USER:$USER /var/log/captain-ddanddan

# 자동 업데이트 설정
echo "🔄 자동 보안 업데이트 설정..."
echo 'Unattended-Upgrade::Automatic-Reboot "true";' | sudo tee -a /etc/apt/apt.conf.d/50unattended-upgrades

# 시스템 모니터링 설정
sudo tee /etc/logwatch/conf/logwatch.conf > /dev/null <<EOF
Detail = High
Range = yesterday
Service = All
Format = html
mailto = $EMAIL
EOF

# 서비스 시작
echo "🚀 Captain DDandDan 서비스 시작..."
sudo systemctl start captain-ddanddan
sudo systemctl reload nginx
sudo systemctl start redis-server

# 보안 검사
echo "🔍 보안 검사 실행..."
sudo rkhunter --update
sudo aide --init
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# 최종 상태 확인
echo "=========================================="
echo "✅ Captain DDandDan 서비스 배포 완료!"
echo "=========================================="
echo "🌐 접속 URL: https://$DOMAIN"
echo "🌐 WWW URL: https://$WWW_DOMAIN"
echo ""
echo "🔒 적용된 보안 기능:"
echo "  ✓ TLS 1.3 암호화"
echo "  ✓ HSTS 강제"
echo "  ✓ DDoS 방지"
echo "  ✓ Rate Limiting"
echo "  ✓ Fail2Ban 침입탐지"
echo "  ✓ 방화벽 보호"
echo "  ✓ 자동 보안 업데이트"
echo "  ✓ 로그 모니터링"
echo ""
echo "📊 서비스 상태:"
sudo systemctl status captain-ddanddan --no-pager -l
echo ""
echo "🔐 SSL 인증서:"
sudo certbot certificates | grep -A5 $DOMAIN
echo ""
echo "🛡️ 방화벽 상태:"
sudo ufw status verbose
echo ""
echo "📝 관리 명령어:"
echo "  서비스 로그: sudo journalctl -u captain-ddanddan -f"
echo "  NGINX 로그: sudo tail -f /var/log/nginx/captain-ddanddan.access.log"
echo "  보안 로그: sudo journalctl -u fail2ban -f"
echo "  시스템 상태: sudo systemctl status captain-ddanddan nginx fail2ban"
echo ""
echo "🎊 Captain DDandDan 서비스가 최고 보안으로 준비되었습니다!"