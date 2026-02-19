#!/usr/bin/env python3
"""
반도체 뉴스 크롤링 및 요약 서비스
Notion 스타일의 웹 기반 뉴스 대시보드
"""

import os
import sys
import schedule
import time
from datetime import datetime
from web_app import create_app
from news_crawler import NewsCrawler
from news_analyzer import NewsAnalyzer
from database import init_db, NewsArticle, database_session
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_service.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def update_news():
    """뉴스를 크롤링하고 분석하는 주기적 작업"""
    try:
        logger.info("뉴스 업데이트 작업 시작")
        
        # 크롤링
        crawler = NewsCrawler()
        articles = crawler.crawl_semiconductor_news()
        
        # 분석 및 요약
        analyzer = NewsAnalyzer()
        
        for article_data in articles:
            # 중복 체크
            existing = database_session.query(NewsArticle).filter_by(url=article_data['url']).first()
            if existing:
                continue
            
            # 영어 제목 번역
            translated_title = analyzer._translate_text(article_data['title'], is_title=True)
            
            # 영어 내용 번역
            translated_content = analyzer._translate_text(article_data['content'], is_title=False)
            
            # 우선순위 계산 (번역된 제목 기반)
            priority = analyzer.calculate_priority({
                **article_data,
                'title': translated_title,
                'content': translated_content
            })
            
            # 분석 및 요약 (번역된 내용으로)
            summary = analyzer.summarize_article(translated_content)
            
            # DB에 저장
            article = NewsArticle(
                title=translated_title,  # 번역된 제목
                content=translated_content,  # 번역된 내용
                summary=summary,
                url=article_data['url'],
                source=article_data['source'],
                published_date=article_data['published_date'],
                priority_score=priority,
                crawled_at=datetime.now()
            )
            
            database_session.add(article)
        
        database_session.commit()
        logger.info(f"뉴스 업데이트 완료: {len(articles)}개의 새 기사 처리")
        
    except Exception as e:
        logger.error(f"뉴스 업데이트 중 오류 발생: {str(e)}")
        database_session.rollback()

def run_scheduler():
    """스케줄러 실행"""
    # 하루 2회 뉴스 업데이트
    schedule.every(12).hours.do(update_news)
    
    # 초기 실행
    update_news()
    
    logger.info("스케줄러 시작 - 12시간마다 뉴스 업데이트")
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "web":
            # 웹 서버만 실행
            app, socketio = create_app()
            
            # 환경 변수에서 설정 읽기
            host = os.getenv('HOST', '0.0.0.0')  # 외부 접속 허용
            port = int(os.getenv('PORT', 5000))
            debug = os.getenv('FLASK_ENV') == 'development'
            
            logger.info(f"웹 서버 시작: http://{host}:{port}")
            socketio.run(app, debug=debug, host=host, port=port)
        elif sys.argv[1] == "update":
            # 한 번만 뉴스 업데이트
            init_db()
            update_news()
        elif sys.argv[1] == "scheduler":
            # 스케줄러 실행
            init_db()
            run_scheduler()
    else:
        print("사용법:")
        print("  python main_run.py web       - 웹 서버 실행")
        print("  python main_run.py update    - 뉴스 한 번 업데이트")
        print("  python main_run.py scheduler - 스케줄러 실행")

if __name__ == "__main__":
    main()