"""
Captain DDandDan 서비스 - 최고 보안 모듈
외부 서비스 제공을 위한 enterprise급 보안 기능 구현
"""

import os
import time
import json
import logging
import hashlib
import ipaddress
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict, deque
from flask import request, jsonify, abort
import redis

logger = logging.getLogger(__name__)

class SecurityManager:
    """Captain DDandDan 보안 관리자"""
    
    def __init__(self):
        self.redis_client = None
        self.max_attempts = 10
        self.lockout_duration = 3600  # 1시간
        self.rate_limits = {
            'api': {'requests': 100, 'window': 3600},  # API: 시간당 100회
            'login': {'requests': 5, 'window': 900},    # 로그인: 15분당 5회
            'general': {'requests': 1000, 'window': 3600}  # 일반: 시간당 1000회
        }
        
        # Redis 연결 시도
        try:
            self.redis_client = redis.Redis(
                host='localhost', 
                port=6379, 
                db=0, 
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis 보안 저장소 연결 성공")
        except:
            logger.warning("Redis 연결 실패, 인메모리 보안 저장소 사용")
            self.memory_store = defaultdict(lambda: defaultdict(deque))
    
    def get_client_ip(self):
        """실제 클라이언트 IP 주소 가져오기 (프록시 고려)"""
        # Cloudflare, NGINX 프록시 헤더 확인
        for header in ['CF-Connecting-IP', 'X-Real-IP', 'X-Forwarded-For']:
            if header in request.headers:
                ip = request.headers[header].split(',')[0].strip()
                try:
                    ipaddress.ip_address(ip)
                    return ip
                except:
                    continue
        return request.remote_addr
    
    def is_rate_limited(self, identifier, limit_type='general'):
        """Rate limiting 검사"""
        if limit_type not in self.rate_limits:
            return False
            
        config = self.rate_limits[limit_type]
        current_time = int(time.time())
        window_start = current_time - config['window']
        
        key = f"rate_limit:{limit_type}:{identifier}"
        
        if self.redis_client:
            try:
                # Redis 사용
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.zcard(key)
                pipe.expire(key, config['window'])
                results = pipe.execute()
                
                request_count = results[2]
                return request_count > config['requests']
            except:
                pass
        
        # 메모리 저장소 사용
        requests_deque = self.memory_store[limit_type][identifier]
        
        # 윈도우 밖의 요청 제거
        while requests_deque and requests_deque[0] < window_start:
            requests_deque.popleft()
        
        # 현재 요청 추가
        requests_deque.append(current_time)
        
        return len(requests_deque) > config['requests']
    
    def is_suspicious_request(self):
        """의심스러운 요청 패턴 감지"""
        user_agent = request.headers.get('User-Agent', '').lower()
        path = request.path.lower()
        
        # 봇/스크래퍼 감지
        suspicious_agents = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 
            'python-requests', 'postman', 'insomnia'
        ]
        
        # 공격 패턴 감지
        attack_patterns = [
            'admin', 'phpmyadmin', '.env', 'config', 'backup',
            'wp-admin', 'wp-login', '.git', 'shell', 'cmd'
        ]
        
        # SQL Injection 패턴
        sql_patterns = [
            "union", "select", "insert", "update", "delete", "drop",
            "script", "javascript", "vbscript", "onload", "onerror"
        ]
        
        # User-Agent 검사
        if any(agent in user_agent for agent in suspicious_agents):
            return True, "Suspicious User-Agent"
        
        # 경로 검사
        if any(pattern in path for pattern in attack_patterns):
            return True, "Attack Pattern in Path"
        
        # SQL Injection 검사 (쿼리 파라미터)
        query_string = request.query_string.decode('utf-8', errors='ignore').lower()
        if any(pattern in query_string for pattern in sql_patterns):
            return True, "Potential SQL Injection"
        
        return False, None
    
    def log_security_event(self, event_type, details, severity="INFO"):
        """보안 이벤트 로깅"""
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'ip': self.get_client_ip(),
            'user_agent': request.headers.get('User-Agent', ''),
            'path': request.path,
            'method': request.method,
            'details': details,
            'severity': severity
        }
        
        # 구조화된 로그 출력
        logger.warning(f"SECURITY_EVENT: {json.dumps(event_data)}")
        
        # Redis에 저장 (선택사항)
        if self.redis_client:
            try:
                key = f"security_events:{datetime.now().strftime('%Y-%m-%d')}"
                self.redis_client.lpush(key, json.dumps(event_data))
                self.redis_client.expire(key, 86400 * 7)  # 7일 보관
            except:
                pass

# 전역 보안 관리자 인스턴스
security_manager = SecurityManager()

def security_required(limit_type='general'):
    """보안 검사 데코레이터"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = security_manager.get_client_ip()
            
            # Rate limiting 검사
            if security_manager.is_rate_limited(client_ip, limit_type):
                security_manager.log_security_event(
                    'RATE_LIMIT_EXCEEDED',
                    f'Rate limit exceeded for {limit_type}',
                    'WARNING'
                )
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.'
                }), 429
            
            # 의심스러운 요청 검사
            is_suspicious, reason = security_manager.is_suspicious_request()
            if is_suspicious:
                security_manager.log_security_event(
                    'SUSPICIOUS_REQUEST',
                    f'Suspicious request: {reason}',
                    'HIGH'
                )
                abort(403)
            
            # 정상 요청 로그
            if limit_type == 'api':
                security_manager.log_security_event(
                    'API_ACCESS',
                    f'API endpoint accessed: {request.endpoint}',
                    'INFO'
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def init_security(app):
    """Flask 앱에 보안 기능 초기화"""
    
    @app.before_request
    def security_check():
        """모든 요청에 대한 기본 보안 검사"""
        client_ip = security_manager.get_client_ip()
        
        # IP 화이트리스트 검사 (필요시)
        whitelist = os.getenv('IP_WHITELIST', '').split(',')
        if whitelist and whitelist[0] and client_ip not in whitelist:
            # 화이트리스트가 설정되어 있고 IP가 포함되지 않은 경우
            pass  # 프로덕션에서는 제한할 수 있음
        
        # 기본 rate limiting
        if security_manager.is_rate_limited(client_ip, 'general'):
            security_manager.log_security_event(
                'GENERAL_RATE_LIMIT',
                'General rate limit exceeded',
                'WARNING'
            )
            return jsonify({'error': 'Too many requests'}), 429
    
    @app.after_request  
    def security_headers(response):
        """보안 헤더 추가"""
        # 기본 보안 헤더는 이미 web_app.py에서 설정됨
        
        # CSP 강화 (Captain DDandDan 전용)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.socket.io; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # 추가 보안 헤더
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        return response
    
    logger.info("Captain DDandDan 최고 보안 시스템 초기화 완료")
    
    return app