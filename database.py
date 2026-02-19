"""
데이터베이스 모델 정의
SQLAlchemy를 사용한 뉴스 기사 데이터 모델
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 데이터베이스 설정
DATABASE_URL = "sqlite:///./news_database.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
database_session = SessionLocal()

Base = declarative_base()

class ArticleComment(Base):
    """기사 댓글 테이블"""
    __tablename__ = "article_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, index=True, nullable=False)
    nickname = Column(String, nullable=False)  # 익명 닉네임
    comment_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)  # 좋아요 수
    
    def to_dict(self):
        return {
            'id': self.id,
            'article_id': self.article_id,
            'nickname': self.nickname,
            'comment_text': self.comment_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'likes': self.likes
        }

class ArticleShare(Base):
    """기사 공유 기록 테이블"""
    __tablename__ = "article_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, index=True, nullable=False)
    share_type = Column(String)  # 'kakao', 'link', 'copy' 등
    shared_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'article_id': self.article_id,
            'share_type': self.share_type,
            'shared_at': self.shared_at.isoformat() if self.shared_at else None
        }

class AdminNews(Base):
    """관리자가 수동으로 추가한 뉴스"""
    __tablename__ = "admin_news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    url = Column(String, unique=True, index=True, nullable=False)
    source = Column(String, default="관리자 등록")
    published_date = Column(DateTime, default=datetime.utcnow)
    added_at = Column(DateTime, default=datetime.utcnow)
    priority_score = Column(Float, default=8.0)  # 수동 등록은 높은 우선순위
    category = Column(String, default="semiconductor")
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'url': self.url,
            'source': self.source,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'priority_score': self.priority_score,
            'category': self.category,
            'is_admin': True
        }

class ArticleBookmark(Base):
    """기사 북마크 테이블"""
    __tablename__ = "article_bookmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, default="default")
    article_id = Column(Integer, index=True, nullable=False)
    bookmarked_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)  # 사용자 메모
    
    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'article_id': self.article_id,
            'bookmarked_at': self.bookmarked_at.isoformat() if self.bookmarked_at else None,
            'notes': self.notes
        }

class UserPreferences(Base):
    """사용자 설정 테이블"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, default="default")  # 단순화를 위해 기본 사용자
    interested_keywords = Column(Text)  # JSON 형태로 저장
    blocked_keywords = Column(Text)     # JSON 형태로 저장  
    preferred_sources = Column(Text)    # JSON 형태로 저장
    min_priority_score = Column(Float, default=0.0)
    max_articles_per_page = Column(Integer, default=20)
    notification_enabled = Column(Integer, default=1)  # Boolean 대체
    notification_priority_threshold = Column(Float, default=7.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'interested_keywords': json.loads(self.interested_keywords) if self.interested_keywords else [],
            'blocked_keywords': json.loads(self.blocked_keywords) if self.blocked_keywords else [],
            'preferred_sources': json.loads(self.preferred_sources) if self.preferred_sources else [],
            'min_priority_score': self.min_priority_score,
            'max_articles_per_page': self.max_articles_per_page,
            'notification_enabled': bool(self.notification_enabled),
            'notification_priority_threshold': self.notification_priority_threshold,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class NewsArticle(Base):
    """뉴스 기사 테이블"""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    url = Column(String, unique=True, index=True, nullable=False)
    source = Column(String, index=True, nullable=False)
    published_date = Column(DateTime)
    crawled_at = Column(DateTime, default=datetime.utcnow, index=True)  # 성능 개선용 인덱스
    priority_score = Column(Float, default=0.0, index=True)  # 성능 개선용 인덱스
    category = Column(String, default="semiconductor")
    
    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'url': self.url,
            'source': self.source,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'crawled_at': self.crawled_at.isoformat() if self.crawled_at else None,
            'priority_score': self.priority_score,
            'category': self.category
        }
    
    def __repr__(self):
        return f"<NewsArticle(title='{self.title[:50]}...', source='{self.source}')>"

def init_db():
    """데이터베이스 초기화"""
    print("데이터베이스를 초기화합니다...")
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 초기화 완료!")

def get_db_session():
    """데이터베이스 세션 생성"""
    return SessionLocal()

# 유틸리티 함수들
def get_articles_by_priority(session=None, limit=10):
    """우선순위 순으로 기사 조회 (중복 제거)"""
    if not session:
        session = database_session
    articles = session.query(NewsArticle).order_by(NewsArticle.priority_score.desc()).limit(limit * 2).all()
    # URL 기반 중복 제거
    seen_urls = set()
    unique_articles = []
    for article in articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique_articles.append(article)
            if len(unique_articles) >= limit:
                break
    return unique_articles

def get_recent_articles(session=None, limit=20):
    """최근 기사 조회 (중복 제거)"""
    if not session:
        session = database_session
    articles = session.query(NewsArticle).order_by(
        NewsArticle.crawled_at.desc(),
        NewsArticle.id.desc()
    ).limit(limit * 2).all()
    # URL 기반 중복 제거
    seen_urls = set()
    unique_articles = []
    for article in articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique_articles.append(article)
            if len(unique_articles) >= limit:
                break
    return unique_articles

def search_articles(query, session=None, limit=20):
    """기사 검색 (중복 제거)"""
    if not session:
        session = database_session
    articles = session.query(NewsArticle).filter(
        NewsArticle.title.contains(query) | 
        NewsArticle.content.contains(query) |
        NewsArticle.summary.contains(query)
    ).order_by(NewsArticle.priority_score.desc()).limit(limit * 2).all()
    # URL 기반 중복 제거
    seen_urls = set()
    unique_articles = []
    for article in articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique_articles.append(article)
            if len(unique_articles) >= limit:
                break
    return unique_articles

# 사용자 설정 관련 함수들
def get_user_preferences(user_id="default", session=None):
    """사용자 설정 조회"""
    if not session:
        session = database_session
    
    prefs = session.query(UserPreferences).filter_by(user_id=user_id).first()
    if not prefs:
        # 기본 설정 생성
        prefs = create_default_preferences(user_id, session)
    
    return prefs

def create_default_preferences(user_id="default", session=None):
    """기본 사용자 설정 생성"""
    if not session:
        session = database_session
    
    import json
    
    default_keywords = [
        "AI", "인공지능", "머신러닝", "deep learning",
        "5nm", "3nm", "2nm", "process technology",
        "TSMC", "Samsung", "Intel", "NVIDIA", "AMD",
        "memory", "DRAM", "NAND", "SSD", "HBM"
    ]
    
    default_sources = [
        "EE Times", "전자신문", "Semiconductor Engineering", 
        "AnandTech", "Tom's Hardware"
    ]
    
    prefs = UserPreferences(
        user_id=user_id,
        interested_keywords=json.dumps(default_keywords, ensure_ascii=False),
        blocked_keywords=json.dumps([], ensure_ascii=False),
        preferred_sources=json.dumps(default_sources, ensure_ascii=False),
        min_priority_score=0.0,
        max_articles_per_page=20,
        notification_enabled=1,
        notification_priority_threshold=7.0
    )
    
    session.add(prefs)
    session.commit()
    
    return prefs

def update_user_preferences(user_id="default", preferences_data=None, session=None):
    """사용자 설정 업데이트"""
    if not session:
        session = database_session
    
    if not preferences_data:
        return None
    
    import json
    
    prefs = session.query(UserPreferences).filter_by(user_id=user_id).first()
    if not prefs:
        prefs = create_default_preferences(user_id, session)
    
    # 설정 업데이트
    if 'interested_keywords' in preferences_data:
        prefs.interested_keywords = json.dumps(preferences_data['interested_keywords'], ensure_ascii=False)
    
    if 'blocked_keywords' in preferences_data:
        prefs.blocked_keywords = json.dumps(preferences_data['blocked_keywords'], ensure_ascii=False)
    
    if 'preferred_sources' in preferences_data:
        prefs.preferred_sources = json.dumps(preferences_data['preferred_sources'], ensure_ascii=False)
    
    if 'min_priority_score' in preferences_data:
        prefs.min_priority_score = preferences_data['min_priority_score']
    
    if 'max_articles_per_page' in preferences_data:
        prefs.max_articles_per_page = preferences_data['max_articles_per_page']
    
    if 'notification_enabled' in preferences_data:
        prefs.notification_enabled = int(preferences_data['notification_enabled'])
    
    if 'notification_priority_threshold' in preferences_data:
        prefs.notification_priority_threshold = preferences_data['notification_priority_threshold']
    
    prefs.updated_at = datetime.utcnow()
    session.commit()
    
    return prefs

def get_filtered_articles(user_id="default", session=None, limit=20, sort_by='priority'):
    """사용자 설정에 따라 필터링된 기사 조회"""
    if not session:
        session = database_session
    
    # 사용자 설정 조회
    prefs = get_user_preferences(user_id, session)
    prefs_dict = prefs.to_dict()
    
    # 기본 쿼리
    query = session.query(NewsArticle)
    
    # 최소 우선순위 점수 필터
    if prefs_dict['min_priority_score'] > 0:
        query = query.filter(NewsArticle.priority_score >= prefs_dict['min_priority_score'])
    
    # 선호 소스 필터
    if prefs_dict['preferred_sources']:
        query = query.filter(NewsArticle.source.in_(prefs_dict['preferred_sources']))
    
    # 차단 키워드 필터
    if prefs_dict['blocked_keywords']:
        for keyword in prefs_dict['blocked_keywords']:
            query = query.filter(
                ~(NewsArticle.title.contains(keyword) | 
                  NewsArticle.content.contains(keyword) |
                  NewsArticle.summary.contains(keyword))
            )
    
    # 관심 키워드가 있는 경우 우선순위 부스트 (간단한 구현)
    if prefs_dict['interested_keywords']:
        # 실제로는 더 복잡한 스코어링 로직이 필요
        pass
    
    # 정렬
    if sort_by == 'recent':
        query = query.order_by(NewsArticle.crawled_at.desc())
    else:  # priority
        query = query.order_by(NewsArticle.priority_score.desc())
    
    # 제한
    limit = min(limit, prefs_dict['max_articles_per_page'])
    query = query.limit(limit)
    
    return query.all()

# 북마크 관련 함수들
def add_bookmark(user_id="default", article_id=None, notes="", session=None):
    """기사 북마크 추가"""
    if not session:
        session = database_session
    
    if not article_id:
        return None
    
    # 이미 북마크된 기사인지 확인
    existing = session.query(ArticleBookmark).filter_by(
        user_id=user_id, article_id=article_id
    ).first()
    
    if existing:
        return existing  # 이미 북마크됨
    
    bookmark = ArticleBookmark(
        user_id=user_id,
        article_id=article_id,
        notes=notes
    )
    
    session.add(bookmark)
    session.commit()
    
    return bookmark

def remove_bookmark(user_id="default", article_id=None, session=None):
    """기사 북마크 제거"""
    if not session:
        session = database_session
    
    if not article_id:
        return False
    
    bookmark = session.query(ArticleBookmark).filter_by(
        user_id=user_id, article_id=article_id
    ).first()
    
    if bookmark:
        session.delete(bookmark)
        session.commit()
        return True
    
    return False

def get_bookmarked_articles(user_id="default", session=None, limit=50):
    """북마크된 기사 목록 조회"""
    if not session:
        session = database_session
    
    # 북마크와 기사 정보를 조인하여 조회
    query = session.query(NewsArticle, ArticleBookmark).join(
        ArticleBookmark, NewsArticle.id == ArticleBookmark.article_id
    ).filter(
        ArticleBookmark.user_id == user_id
    ).order_by(
        ArticleBookmark.bookmarked_at.desc()
    ).limit(limit)
    
    results = query.all()
    
    # 결과 포맷팅
    bookmarked_articles = []
    for article, bookmark in results:
        article_dict = article.to_dict()
        article_dict['bookmark_info'] = bookmark.to_dict()
        bookmarked_articles.append(article_dict)
    
    return bookmarked_articles

def is_bookmarked(user_id="default", article_id=None, session=None):
    """특정 기사가 북마크되어 있는지 확인"""
    if not session:
        session = database_session
    
    if not article_id:
        return False
    
    bookmark = session.query(ArticleBookmark).filter_by(
        user_id=user_id, article_id=article_id
    ).first()
    
    return bookmark is not None

def update_bookmark_notes(user_id="default", article_id=None, notes="", session=None):
    """북마크 메모 업데이트"""
    if not session:
        session = database_session
    
    bookmark = session.query(ArticleBookmark).filter_by(
        user_id=user_id, article_id=article_id
    ).first()
    
    if bookmark:
        bookmark.notes = notes
        session.commit()
        return bookmark
    
    return None

def get_related_articles(article_id, session=None, limit=5):
    """관련 기사 검색 (같은 카테고리 또는 유사 키워드)"""
    if not session:
        session = database_session
    
    # 원본 기사 정보 가져오기
    article = session.query(NewsArticle).filter_by(id=article_id).first()
    if not article:
        return []
    
    # 같은 카테고리 또는 유사 제목의 기사 찾기
    related = session.query(NewsArticle).filter(
        NewsArticle.id != article_id,  # 자기 자신 제외
        (NewsArticle.category == article.category) |  # 같은 카테고리
        (NewsArticle.source == article.source)  # 같은 출처
    ).order_by(
        NewsArticle.priority_score.desc(),
        NewsArticle.crawled_at.desc()
    ).limit(limit).all()
    
    return related
