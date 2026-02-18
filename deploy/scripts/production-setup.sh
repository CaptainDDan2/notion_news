#!/bin/bash
# 프로덕션 서버 설정 및 배포 스크립트

set -e

# 변수 설정
DOMAIN="your-domain.com"
APP_DIR="/opt/semiconductor-news"
USER="www-data"

echo "=== 반도체 뉴스 애플리케이션 프로덕션 배포 ==="
echo "도메인: $DOMAIN"
echo "설치 경로: $APP_DIR"

# 시스템 업데이트
echo "시스템 패키지 업데이트..."
sudo apt update && sudo apt upgrade -y

# 필요한 패키지 설치
echo "필수 패키지 설치..."
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx ufw git

# 방화벽 설정
echo "방화벽 설정..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# 애플리케이션 디렉토리 생성
echo "애플리케이션 설치..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# 코드 배포 (Git에서 클론하거나 파일 복사)
# sudo git clone https://github.com/your-username/semiconductor-news.git $APP_DIR
# 또는 현재 코드 복사
sudo cp -r . $APP_DIR/
sudo chown -R $USER:$USER $APP_DIR

# Python 가상환경 설정
echo "Python 환경 설정..."
cd $APP_DIR
sudo -u $USER python3 -m venv venv
sudo -u $USER ./venv/bin/pip install -r requirements.txt

# 환경변수 설정
echo "환경변수 설정..."
sudo tee $APP_DIR/.env > /dev/null <<EOF
FLASK_ENV=production
OPENAI_API_KEY=your-api-key-here
SECRET_KEY=$(openssl rand -hex 32)
HOST=127.0.0.1
PORT=5000
DOMAIN=$DOMAIN
HTTPS_ONLY=true
ALLOWED_HOSTS=localhost,127.0.0.1,$DOMAIN,www.$DOMAIN
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
EOF

sudo chown $USER:$USER $APP_DIR/.env
sudo chmod 600 $APP_DIR/.env

# 데이터베이스 초기화
echo "데이터베이스 초기화..."
cd $APP_DIR
sudo -u $USER ./venv/bin/python generate_sample_data.py

# systemd 서비스 설정
echo "systemd 서비스 설정..."
sudo cp deploy/systemd/semiconductor-news.service /etc/systemd/system/
sudo sed -i "s|your-domain.com|$DOMAIN|g" /etc/systemd/system/semiconductor-news.service
sudo sed -i "s|your-api-key-here|$OPENAI_API_KEY|g" /etc/systemd/system/semiconductor-news.service
sudo systemctl daemon-reload
sudo systemctl enable semiconductor-news

# NGINX 설정
echo "NGINX 설정..."
sudo cp deploy/nginx/semiconductor-news.conf /etc/nginx/sites-available/
sudo sed -i "s|your-domain.com|$DOMAIN|g" /etc/nginx/sites-available/semiconductor-news.conf
sudo ln -sf /etc/nginx/sites-available/semiconductor-news.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# NGINX 구성 테스트
sudo nginx -t

# SSL 인증서 발급 (Let's Encrypt)
echo "SSL 인증서 발급..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# 서비스 시작
echo "서비스 시작..."
sudo systemctl start semiconductor-news
sudo systemctl reload nginx

# 상태 확인
echo "=== 배포 완료 ==="
echo "서비스 상태:"
sudo systemctl status semiconductor-news --no-pager
echo
echo "NGINX 상태:"
sudo systemctl status nginx --no-pager
echo
echo "SSL 인증서 상태:"
sudo certbot certificates
echo
echo "접속 URL: https://$DOMAIN"
echo
echo "로그 확인:"
echo "  애플리케이션: sudo journalctl -u semiconductor-news -f"
echo "  NGINX: sudo tail -f /var/log/nginx/semiconductor-news.access.log"