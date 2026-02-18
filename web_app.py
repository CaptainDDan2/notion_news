"""
Flask 웹 애플리케이션
Notion 스타일의 뉴스 대시보드
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from database import (init_db, NewsArticle, UserPreferences, ArticleBookmark, get_articles_by_priority, 
                     get_recent_articles, search_articles, get_db_session, 
                     get_user_preferences, update_user_preferences, get_filtered_articles,
                     add_bookmark, remove_bookmark, get_bookmarked_articles, is_bookmarked, update_bookmark_notes)
from news_crawler import NewsCrawler
from news_analyzer import NewsAnalyzer
from datetime import datetime, timedelta
import logging
import json
import threading
import os
from dotenv import load_dotenv
from captain_security import init_security, security_required

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

def create_app():
    """Flask 앱 생성 및 설정"""
    app = Flask(__name__)
    
    # 보안 설정
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('HTTPS_ONLY', 'false').lower() == 'true'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # CORS 설정 (보안 강화)
    allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5000').split(',')
    CORS(app, origins=allowed_origins)
    
    # WebSocket 설정 (threading 모드 사용으로 SSL 호환성 문제 방지)
    socketio = SocketIO(app, cors_allowed_origins=allowed_origins, async_mode='threading')
    
    # 데이터베이스 초기화
    init_db()
    
    # Captain DDandDan 최고 보안 시스템 적용
    init_security(app)
    
    # 보안 헤더 추가
    @app.after_request
    def set_security_headers(response):
        """보안 헤더 설정"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HTTPS 강제 설정 (프로덕션 환경)
        if os.getenv('HTTPS_ONLY', 'false').lower() == 'true':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    # 허용된 호스트 확인
    @app.before_request
    def check_host():
        """허용된 호스트인지 확인"""
        allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
        if request.host.split(':')[0] not in allowed_hosts:
            logger.warning(f'허용되지 않은 호스트 접근 시도: {request.host}')
            # 프로덕션에서는 403을 반환할 수 있음
            # return 'Forbidden', 403
    
    @app.route('/')
    def index():
        """메인 페이지"""
        try:
            session = get_db_session()
            
            # 우선순위 높은 기사들
            priority_articles = get_articles_by_priority(session, limit=8)
            # 최근 기사들  
            recent_articles = get_recent_articles(session, limit=12)
            
            # 통계 정보
            total_articles = session.query(NewsArticle).count()
            today_articles = session.query(NewsArticle).filter(
                NewsArticle.crawled_at >= datetime.now() - timedelta(days=1)
            ).count()
            
            session.close()
            
            return render_template('index.html',
                                 priority_articles=priority_articles,
                                 recent_articles=recent_articles,
                                 total_articles=total_articles,
                                 today_articles=today_articles)
        except Exception as e:
            logger.error(f"메인 페이지 로딩 오류: {str(e)}")
            return render_template('index.html',
                                 priority_articles=[],
                                 recent_articles=[],
                                 total_articles=0,
                                 today_articles=0)

    @app.route('/health')
    def health_check():
        """Docker 헬스 체크 엔드포인트"""
        try:
            # 데이터베이스 연결 테스트
            session = get_db_session()
            session.query(NewsArticle).first()
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected'
            }), 200
        except Exception as e:
            logger.error(f'헬스 체크 실패: {str(e)}')
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500

    @app.route('/api/articles')
    @security_required('api')
    def api_articles():
        """기사 목록 API"""
        try:
            session = get_db_session()
            
            # 쿼리 파라미터
            page = int(request.args.get('page', 1))
            limit = min(int(request.args.get('limit', 20)), 100)
            sort_by = request.args.get('sort', 'priority')  # priority, recent, title
            search_query = request.args.get('search', '').strip()
            
            # 검색 또는 일반 조회
            if search_query:
                articles = search_articles(search_query, session, limit=limit)
            else:
                if sort_by == 'recent':
                    articles = session.query(NewsArticle).order_by(NewsArticle.crawled_at.desc())
                elif sort_by == 'title':
                    articles = session.query(NewsArticle).order_by(NewsArticle.title)
                else:  # priority
                    articles = session.query(NewsArticle).order_by(NewsArticle.priority_score.desc())
                
                # 페이징 적용
                offset = (page - 1) * limit
                articles = articles.offset(offset).limit(limit).all()
            
            # JSON 응답 준비
            articles_data = [article.to_dict() for article in articles]
            
            session.close()
            
            return jsonify({
                'success': True,
                'articles': articles_data,
                'page': page,
                'limit': limit,
                'total': len(articles_data)
            })
            
        except Exception as e:
            logger.error(f"기사 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/article/<int:article_id>')
    def api_article_detail(article_id):
        """기사 상세 정보 API"""
        try:
            session = get_db_session()
            article = session.query(NewsArticle).filter_by(id=article_id).first()
            
            if not article:
                session.close()
                return jsonify({'success': False, 'error': '기사를 찾을 수 없습니다'}), 404
            
            article_data = article.to_dict()
            session.close()
            
            return jsonify({
                'success': True,
                'article': article_data
            })
            
        except Exception as e:
            logger.error(f"기사 상세 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crawl', methods=['POST'])
    def api_crawl_news():
        """수동 뉴스 크롤링 API"""
        try:
            # 크롤링 시작 알림
            app.send_notification('뉴스 크롤링을 시작합니다...', 'info')
            
            # 크롤링 실행
            crawler = NewsCrawler()
            articles = crawler.crawl_semiconductor_news()
            
            # 분석 및 저장
            analyzer = NewsAnalyzer()
            session = get_db_session()
            
            new_articles_count = 0
            high_priority_articles = []
            
            for article_data in articles:
                # 중복 체크
                existing = session.query(NewsArticle).filter_by(url=article_data['url']).first()
                if existing:
                    continue
                
                # 분석
                summary = analyzer.summarize_article(article_data['content'])
                priority = analyzer.calculate_priority(article_data)
                
                # 저장
                article = NewsArticle(
                    title=article_data['title'],
                    content=article_data['content'],
                    summary=summary,
                    url=article_data['url'],
                    source=article_data['source'],
                    published_date=article_data['published_date'],
                    priority_score=priority,
                    crawled_at=datetime.now()
                )
                
                session.add(article)
                new_articles_count += 1
                
                # 높은 우선순위 기사 체크
                if priority >= 8.0:
                    high_priority_articles.append({
                        'id': None,  # DB 저장 후 설정
                        'title': article_data['title'],
                        'priority_score': priority,
                        'source': article_data['source']
                    })
            
            session.commit()
            
            # 새 기사들의 ID 업데이트
            for i, high_priority in enumerate(high_priority_articles):
                article = session.query(NewsArticle).filter_by(
                    title=high_priority['title']
                ).first()
                if article:
                    high_priority_articles[i]['id'] = article.id
            
            session.close()
            
            # 완료 알림
            app.send_notification(
                f'{new_articles_count}개의 새로운 기사를 추가했습니다.',
                'success'
            )
            
            # 높은 우선순위 기사 알림
            for article in high_priority_articles:
                app.socketio.emit('new_article', {'article': article}, room='news_updates')
            
            # 크롤링 완료 이벤트
            app.socketio.emit('crawl_complete', {'count': new_articles_count}, room='news_updates')
            
            return jsonify({
                'success': True,
                'message': f'{new_articles_count}개의 새로운 기사를 추가했습니다.',
                'new_articles': new_articles_count,
                'high_priority_articles': len(high_priority_articles)
            })
            
        except Exception as e:
            logger.error(f"크롤링 API 오류: {str(e)}")
            app.send_notification('뉴스 크롤링 중 오류가 발생했습니다.', 'error')
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/stats')
    @security_required('api')
    def api_statistics():
        """통계 정보 API"""
        try:
            session = get_db_session()
            
            # 기본 통계
            total_articles = session.query(NewsArticle).count()
            today_articles = session.query(NewsArticle).filter(
                NewsArticle.crawled_at >= datetime.now() - timedelta(days=1)
            ).count()
            
            # 소스별 통계
            from sqlalchemy import func
            sources = session.query(NewsArticle.source, func.count(NewsArticle.id)).group_by(NewsArticle.source).all()
            
            # 최근 7일간 기사 수
            daily_stats = []
            for i in range(7):
                date = datetime.now() - timedelta(days=i)
                start_date = date.replace(hour=0, minute=0, second=0)
                end_date = date.replace(hour=23, minute=59, second=59)
                
                count = session.query(NewsArticle).filter(
                    NewsArticle.crawled_at >= start_date,
                    NewsArticle.crawled_at <= end_date
                ).count()
                
                daily_stats.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
            
            session.close()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_articles': total_articles,
                    'today_articles': today_articles,
                    'daily_stats': daily_stats[::-1],  # 오래된 것부터
                    'source_stats': [{'source': s[0], 'count': s[1]} for s in sources]
                }
            })
            
        except Exception as e:
            logger.error(f"통계 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/trends')
    def api_trends():
        """트렌드 분석 API"""
        try:
            session = get_db_session()
            
            # 최근 3일간의 기사들
            recent_articles = session.query(NewsArticle).filter(
                NewsArticle.crawled_at >= datetime.now() - timedelta(days=3)
            ).all()
            
            # 트렌드 분석
            analyzer = NewsAnalyzer()
            articles_data = [article.to_dict() for article in recent_articles]
            trends = analyzer.analyze_trends(articles_data)
            
            session.close()
            
            return jsonify({
                'success': True,
                'trends': trends
            })
            
        except Exception as e:
            logger.error(f"트렌드 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/preferences')
    def api_get_preferences():
        """사용자 설정 조회 API"""
        try:
            user_id = request.args.get('user_id', 'default')
            session = get_db_session()
            
            prefs = get_user_preferences(user_id, session)
            prefs_data = prefs.to_dict()
            
            session.close()
            
            return jsonify({
                'success': True,
                'preferences': prefs_data
            })
            
        except Exception as e:
            logger.error(f"설정 조회 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/preferences', methods=['POST'])
    def api_update_preferences():
        """사용자 설정 업데이트 API"""
        try:
            user_id = request.json.get('user_id', 'default')
            preferences_data = request.json.get('preferences')
            
            if not preferences_data:
                return jsonify({'success': False, 'error': '설정 데이터가 없습니다'}), 400
            
            session = get_db_session()
            
            prefs = update_user_preferences(user_id, preferences_data, session)
            if prefs:
                prefs_data = prefs.to_dict()
                session.close()
                
                return jsonify({
                    'success': True,
                    'message': '설정이 저장되었습니다.',
                    'preferences': prefs_data
                })
            else:
                session.close()
                return jsonify({'success': False, 'error': '설정 저장에 실패했습니다'}), 500
                
        except Exception as e:
            logger.error(f"설정 업데이트 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/articles/personalized')
    def api_personalized_articles():
        """개인화된 기사 목록 API"""
        try:
            user_id = request.args.get('user_id', 'default')
            page = int(request.args.get('page', 1))
            limit = min(int(request.args.get('limit', 20)), 100)
            sort_by = request.args.get('sort', 'priority')
            
            session = get_db_session()
            
            articles = get_filtered_articles(user_id, session, limit, sort_by)
            articles_data = [article.to_dict() for article in articles]
            
            session.close()
            
            return jsonify({
                'success': True,
                'articles': articles_data,
                'page': page,
                'limit': limit,
                'total': len(articles_data)
            })
            
        except Exception as e:
            logger.error(f"개인화 기사 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/preferences')
    def preferences_page():
        """설정 페이지"""
        return render_template('preferences.html')

    # 북마크 관련 API
    @app.route('/api/bookmarks')
    def api_get_bookmarks():
        """북마크된 기사 목록 조회 API"""
        try:
            user_id = request.args.get('user_id', 'default')
            limit = min(int(request.args.get('limit', 50)), 100)
            
            session = get_db_session()
            
            bookmarked_articles = get_bookmarked_articles(user_id, session, limit)
            
            session.close()
            
            return jsonify({
                'success': True,
                'bookmarks': bookmarked_articles,
                'total': len(bookmarked_articles)
            })
            
        except Exception as e:
            logger.error(f"북마크 조회 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/bookmarks', methods=['POST'])
    def api_add_bookmark():
        """기사 북마크 추가 API"""
        try:
            user_id = request.json.get('user_id', 'default')
            article_id = request.json.get('article_id')
            notes = request.json.get('notes', '')
            
            if not article_id:
                return jsonify({'success': False, 'error': '기사 ID가 필요합니다'}), 400
            
            session = get_db_session()
            
            bookmark = add_bookmark(user_id, article_id, notes, session)
            
            if bookmark:
                bookmark_data = bookmark.to_dict()
                session.close()
                
                return jsonify({
                    'success': True,
                    'message': '북마크에 추가되었습니다.',
                    'bookmark': bookmark_data
                })
            else:
                session.close()
                return jsonify({'success': False, 'error': '북마크 추가에 실패했습니다'}), 500
                
        except Exception as e:
            logger.error(f"북마크 추가 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/bookmarks/<int:article_id>', methods=['DELETE'])
    def api_remove_bookmark(article_id):
        """기사 북마크 제거 API"""
        try:
            user_id = request.args.get('user_id', 'default')
            
            session = get_db_session()
            
            success = remove_bookmark(user_id, article_id, session)
            
            session.close()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '북마크에서 제거되었습니다.'
                })
            else:
                return jsonify({'success': False, 'error': '북마크를 찾을 수 없습니다'}), 404
                
        except Exception as e:
            logger.error(f"북마크 제거 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/bookmarks/<int:article_id>/check')
    def api_check_bookmark(article_id):
        """기사 북마크 여부 확인 API"""
        try:
            user_id = request.args.get('user_id', 'default')
            
            session = get_db_session()
            
            bookmarked = is_bookmarked(user_id, article_id, session)
            
            session.close()
            
            return jsonify({
                'success': True,
                'bookmarked': bookmarked
            })
            
        except Exception as e:
            logger.error(f"북마크 확인 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/bookmarks/<int:article_id>/notes', methods=['PUT'])
    def api_update_bookmark_notes(article_id):
        """북마크 메모 업데이트 API"""
        try:
            user_id = request.json.get('user_id', 'default')
            notes = request.json.get('notes', '')
            
            session = get_db_session()
            
            bookmark = update_bookmark_notes(user_id, article_id, notes, session)
            
            if bookmark:
                bookmark_data = bookmark.to_dict()
                session.close()
                
                return jsonify({
                    'success': True,
                    'message': '메모가 업데이트되었습니다.',
                    'bookmark': bookmark_data
                })
            else:
                session.close()
                return jsonify({'success': False, 'error': '북마크를 찾을 수 없습니다'}), 404
                
        except Exception as e:
            logger.error(f"북마크 메모 업데이트 API 오류: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/bookmarks')
    def bookmarks_page():
        """북마크 페이지"""
        return render_template('bookmarks.html')

    @app.errorhandler(404)
    def not_found(error):
        """404 에러 처리"""
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """500 에러 처리"""
        logger.error(f"서버 내부 오류: {str(error)}")
        return render_template('500.html'), 500

    # WebSocket 이벤트 핸들러
    @socketio.on('connect')
    def handle_connect():
        """클라이언트 연결"""
        join_room('news_updates')
        emit('connected', {'status': 'connected'})
        logger.info('클라이언트가 연결되었습니다')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """클라이언트 연결 해제"""
        leave_room('news_updates')
        logger.info('클라이언트 연결이 해제되었습니다')
    
    # 실시간 알림 전송 함수
    def send_notification(message, type='info', data=None):
        """모든 연결된 클라이언트에게 알림 전송"""
        try:
            socketio.emit('notification', {
                'message': message,
                'type': type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }, room='news_updates')
            logger.info(f'알림 전송: {message}')
        except Exception as e:
            logger.error(f'알림 전송 실패: {str(e)}')
    
    # Flask 앱에 SocketIO 인스턴스와 알림 함수 등록
    app.socketio = socketio
    app.send_notification = send_notification

    return app, socketio

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)