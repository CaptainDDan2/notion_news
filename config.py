"""
설정 파일
애플리케이션 전역 설정 관리
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """기본 설정"""
    
    # 데이터베이스 설정
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./news_database.db')
    
    # OpenAI API 설정
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # 크롤링 설정
    CRAWL_INTERVAL_HOURS = int(os.getenv('CRAWL_INTERVAL_HOURS', '1'))
    MAX_ARTICLES_PER_SOURCE = int(os.getenv('MAX_ARTICLES_PER_SOURCE', '10'))
    REQUEST_DELAY_SECONDS = float(os.getenv('REQUEST_DELAY_SECONDS', '2.0'))
    
    # 웹 서버 설정
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'news_service.log')
    
    # 뉴스 분석 설정
    SUMMARY_MAX_LENGTH = int(os.getenv('SUMMARY_MAX_LENGTH', '200'))
    USE_OPENAI_SUMMARIZATION = os.getenv('USE_OPENAI_SUMMARIZATION', 'True').lower() == 'true'
    
    # 반도체 관련 키워드 (우선순위 계산용)
    SEMICONDUCTOR_KEYWORDS = [
        'semiconductor', 'chip', 'processor', 'memory', 'DRAM', 'NAND',
        '반도체', '칩', '프로세서', '메모리', '낸드',
        'AI chip', 'GPU', 'CPU', 'SoC', 'foundry', 'wafer', 'fab',
        'TSMC', 'Samsung', 'Intel', 'NVIDIA', 'AMD', 'Qualcomm',
        'Apple Silicon', 'ARM', 'RISC-V', '5nm', '3nm', '2nm'
    ]
    
    # 뉴스 소스 설정
    NEWS_SOURCES = [
        {
            'name': 'EE Times',
            'enabled': True,
            'url': 'https://www.eetimes.com/category/semiconductors/',
            'reliability_score': 1.7
        },
        {
            'name': '전자신문',
            'enabled': True, 
            'url': 'http://www.etnews.com/',
            'reliability_score': 1.6
        },
        {
            'name': 'Semiconductor Engineering',
            'enabled': True,
            'url': 'https://semiengineering.com/',
            'reliability_score': 1.7
        }
    ]

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False
    TESTING = False
    # 운영 환경에서는 보안 강화
    SECRET_KEY = os.getenv('SECRET_KEY')  # 반드시 환경변수로 설정

class TestingConfig(Config):
    """테스트 환경 설정"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'  # 메모리 내 테스트 DB

# 환경에 따른 설정 선택
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """현재 환경에 맞는 설정 반환"""
    env = os.getenv('FLASK_ENV', 'development')
    return config_dict.get(env, config_dict['default'])