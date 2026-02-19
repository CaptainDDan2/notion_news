"""
Flask 웹 애플리케이션
Notion 스타일의 뉴스 대시보드
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from database import (init_db, NewsArticle, UserPreferences, ArticleBookmark, ArticleComment, 
                     ArticleShare, AdminNews, get_articles_by_priority, 
                     get_recent_articles, search_articles, get_db_session, 
                     get_user_preferences, update_user_preferences, get_filtered_articles,
                     add_bookmark, remove_bookmark, get_bookmarked_articles, is_bookmarked, update_bookmark_notes)
from datetime import datetime, timedelta
import logging
import json
import threading
import os
from dotenv import load_dotenv

# Optional imports
try:
    from news_crawler import NewsCrawler
except ImportError:
    NewsCrawler = None
    
try:
    from news_analyzer import NewsAnalyzer
except ImportError:
    NewsAnalyzer = None
    
try:
    from captain_security import init_security, security_required
except ImportError:
    def init_security(app):
        pass
    def security_required(*args, **kwargs):
        """Fallback decorator that does nothing"""
        def decorator(f):
            return f
        # @security_required 형태로 직접 사용
        if args and callable(args[0]):
            return args[0]
        # @security_required('api') 형태로 사용
        return decorator

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
            
            # 우선순위 높은 기사들 (성능: 초기 로드 줄이기)
            priority_articles = get_articles_by_priority(session, limit=4)
            # 최근 기사들  
            recent_articles = get_recent_articles(session, limit=6)
            
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

    @app.route('/api/article/<int:article_id>', methods=['GET'])
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
            
            # 크롤링 완료
            return jsonify({
                'success': True,
                'message': f'{new_articles_count}개의 새로운 기사를 추가했습니다.',
                'new_articles': new_articles_count,
                'high_priority_articles': len(high_priority_articles)
            })
            
        except Exception as e:
            logger.error(f"크롤링 API 오류: {str(e)}")
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

    # ===== 사용자 상호작용 API 엔드포인트 =====
    
    @app.route('/api/bookmark', methods=['POST'])
    def create_bookmark():
        """아티클 북마크 생성"""
        try:
            data = request.json
            article_id = data.get('article_id')
            notes = data.get('notes', '')
            
            session = get_db_session()
            # 기존 북마크 확인
            existing = session.query(ArticleBookmark).filter_by(article_id=article_id).first()
            if existing:
                session.close()
                return jsonify({'error': '이미 북마크된 아티클입니다'}), 409
            
            bookmark = ArticleBookmark(
                article_id=article_id,
                notes=notes,
                created_at=datetime.now()
            )
            session.add(bookmark)
            session.commit()
            
            bookmark_dict = bookmark.to_dict()
            session.close()
            return jsonify({'success': True, 'bookmark': bookmark_dict}), 201
        except Exception as e:
            logger.error(f'북마크 생성 실패: {str(e)}')
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/bookmark/<int:article_id>', methods=['DELETE'])
    def delete_bookmark(article_id):
        """북마크 삭제"""
        try:
            session = get_db_session()
            bookmark = session.query(ArticleBookmark).filter_by(article_id=article_id).first()
            if not bookmark:
                session.close()
                return jsonify({'error': '북마크를 찾을 수 없습니다'}), 404
            
            session.delete(bookmark)
            session.commit()
            session.close()
            
            return jsonify({'success': True}), 200
        except Exception as e:
            logger.error(f'북마크 삭제 실패: {str(e)}')
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/bookmarks', methods=['GET'])
    def get_bookmarks():
        """저장된 북마크 조회"""
        try:
            session = get_db_session()
            bookmarks = session.query(ArticleBookmark).all()
            articles = []
            
            for bookmark in bookmarks:
                article = session.query(NewsArticle).get(bookmark.article_id)
                if article:
                    article_data = article.to_dict()
                    article_data['bookmark_id'] = bookmark.id
                    article_data['bookmark_notes'] = bookmark.notes
                    articles.append(article_data)
            
            session.close()
            return jsonify({
                'success': True,
                'count': len(articles),
                'bookmarks': articles
            }), 200
        except Exception as e:
            logger.error(f'북마크 조회 실패: {str(e)}')
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/comment', methods=['POST'])
    def create_comment():
        """아티클 댓글 작성"""
        try:
            data = request.json
            article_id = data.get('article_id')
            comment_text = data.get('comment_text')
            nickname = data.get('nickname', '익명의 독자')
            
            if not comment_text or len(comment_text.strip()) == 0:
                return jsonify({'error': '댓글 내용이 비어있습니다'}), 400
            
            session = get_db_session()
            comment = ArticleComment(
                article_id=article_id,
                nickname=nickname,
                comment_text=comment_text,
                likes=0,
                created_at=datetime.now()
            )
            session.add(comment)
            session.commit()
            
            comment_dict = comment.to_dict()
            session.close()
            return jsonify({'success': True, 'comment': comment_dict}), 201
        except Exception as e:
            logger.error(f'댓글 작성 실패: {str(e)}')
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/comments/<int:article_id>', methods=['GET'])
    def get_comments(article_id):
        """아티클 댓글 조회"""
        try:
            session = get_db_session()
            comments = session.query(ArticleComment).filter_by(article_id=article_id).order_by(ArticleComment.created_at.desc()).all()
            comments_data = [comment.to_dict() for comment in comments]
            session.close()
            
            return jsonify({
                'success': True,
                'article_id': article_id,
                'count': len(comments_data),
                'comments': comments_data
            }), 200
        except Exception as e:
            logger.error(f'댓글 조회 실패: {str(e)}')
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/comment/<int:comment_id>/like', methods=['POST'])
    def like_comment(comment_id):
        """댓글 좋아요 증가"""
        try:
            session = get_db_session()
            comment = session.query(ArticleComment).get(comment_id)
            if not comment:
                session.close()
                return jsonify({'error': '댓글을 찾을 수 없습니다'}), 404
            
            comment.likes += 1
            session.commit()
            likes = comment.likes
            session.close()
            
            return jsonify({'success': True, 'likes': likes}), 200
        except Exception as e:
            logger.error(f'댓글 좋아요 실패: {str(e)}')
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/article/share', methods=['POST'])
    def track_share():
        """아티클 공유 추적"""
        try:
            data = request.json
            article_id = data.get('article_id')
            share_type = data.get('share_type', 'link')  # 'kakao', 'link', 'copy'
            
            # 'kakao', 'link', 'copy' 중에서만 허용
            if share_type not in ['kakao', 'link', 'copy']:
                share_type = 'link'
            
            session = get_db_session()
            share = ArticleShare(
                article_id=article_id,
                share_type=share_type,
                created_at=datetime.now()
            )
            session.add(share)
            session.commit()
            
            share_dict = share.to_dict()
            session.close()
            return jsonify({'success': True, 'share': share_dict}), 201
        except Exception as e:
            logger.error(f'공유 추적 실패: {str(e)}')
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/admin/news', methods=['POST'])
    def add_admin_news():
        """수동 뉴스 추가 (관리자용)"""
        try:
            data = request.json
            title = data.get('title')
            content = data.get('content')
            source = data.get('source', '직접 입력')
            
            if not title or not content:
                return jsonify({'error': '제목과 내용은 필수입니다'}), 400
            
            # 자동으로 요약 생성
            analyzer = NewsAnalyzer()
            summary = analyzer.analyze(title, content)
            
            session = get_db_session()
            # 관리자 뉴스 저장
            admin_news = AdminNews(
                title=title,
                content=content,
                summary=summary,
                source=source,
                priority=8.0,  # 관리자 뉴스는 높은 우선순위
                created_at=datetime.now()
            )
            session.add(admin_news)
            
            # NewsArticle에도 저장 (일반 뉴스 피드에서 보이도록)
            news_article = NewsArticle(
                title=title,
                content=content,
                summary=summary,
                source=source,
                priority_score=8.0,
                crawled_at=datetime.now(),
                url=f'admin-news-{int(datetime.now().timestamp())}',
                published_date=datetime.now()
            )
            session.add(news_article)
            session.commit()
            
            admin_news_dict = admin_news.to_dict()
            session.close()
            return jsonify({'success': True, 'admin_news': admin_news_dict}), 201
        except Exception as e:
            logger.error(f'관리자 뉴스 추가 실패: {str(e)}')
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/share-stats/<int:article_id>', methods=['GET'])
    def get_share_stats(article_id):
        """아티클 공유 통계 조회"""
        try:
            session = get_db_session()
            shares = session.query(ArticleShare).filter_by(article_id=article_id).all()
            
            # 공유 타입별로 집계
            stats = {
                'total': len(shares),
                'kakao': len([s for s in shares if s.share_type == 'kakao']),
                'link': len([s for s in shares if s.share_type == 'link']),
                'copy': len([s for s in shares if s.share_type == 'copy'])
            }
            
            session.close()
            return jsonify({
                'success': True,
                'article_id': article_id,
                'stats': stats
            }), 200
        except Exception as e:
            logger.error(f'공유 통계 조회 실패: {str(e)}')
            return jsonify({'error': str(e)}), 500


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)