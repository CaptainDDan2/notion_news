#!/usr/bin/env python3
"""
Render 데이터베이스에 한국 뉴스 기사를 직접 로드하는 스크립트
전자신문, TheElec, 서울경제에서 크롤링한 데이터 추가
"""

import os
import sys
from datetime import datetime
from database import init_db, NewsArticle, get_db_session
from news_analyzer import NewsAnalyzer

# 한국 반도체 뉴스 샘플 데이터 (실제 크롤링된 기사들)
korean_articles = [
    {
        "title": "테스, 화합물 반도체 'AIN 에피 공정' 혁신…글로벌 선두 노린다",
        "content": "국내 반도체 장비기업 테스가 화합물 반도체 장비 '에피 시스템(Epi System)' 시장에 승부수를 던졌다. 고구조적 안정성과 열 방출 특성이 뛰어난 질화알루미늄(AlN) 에피 공정의 기술적 검증을 완료, 양산 준비를 완료했다. 화합물반도체는 두 가지 이상의 원소를 혼합해서 만드는 반도체로, 고온·고전압에 강해 전기차, 통신장비에 활용 도가 높다.",
        "url": "https://www.etnews.com/20260219000264",
        "source": "전자신문",
        "published_date": datetime(2026, 2, 19, 17, 0, 0)
    },
    {
        "title": "엔비디아보다 2배 빠른 AI 반도체 등장",
        "content": "엔비디아보다 추천 속도는 2.1배 빠르며 지연은 줄이고, 전력 소모까지 낮춘 인공지능(AI) 반도체 기술이 개발됐다. 대규모 데이터를 다루는 지능형 서비스의 속도와 에너지 효율을 동시에 높일 수 있는 기반이 마련됐다는 평가는 반도체 산업의 미래를 보여준다.",
        "url": "https://www.etnews.com/20260218000040",
        "source": "전자신문",
        "published_date": datetime(2026, 2, 18, 21, 0, 0)
    },
    {
        "title": "ICTK, MWC서 양자보안 비전 제시…보안칩으로 PQC 취약점 해결",
        "content": "ICTK가 스페인 바르셀로나에서 열리는 MWC 2026에 참가해 양자보안 비즈니스 로드맵을 공개한다. 양자내성암호(PQC)와 물리적 복제 불가 기능(PUF)을 결합한 보안 아키텍처를 선보일 예정이다. ICTK는 자사 VIA PUF 기술을 PQC와 결합해 하드웨어 단에서부터 보안 신뢰점을 구축한다.",
        "url": "https://www.etnews.com/20260219000041",
        "source": "전자신문",
        "published_date": datetime(2026, 2, 19, 9, 32, 0)
    },
    {
        "title": "Samsung ships HBM4, first among memory makers",
        "content": "Multiple memory makers are working to ship HBM (high bandwidth memory), but Samsung Electronics is first to mass-produce and ship a commercial HBM4. The introduction of HBM4 represents a milestone in AI data center memory performance, offering 11.7Gbps speed and maximum bandwidth of 3.3TB/s per stack.",
        "url": "https://www.thelec.net/news/articleView.html?idxno=5584",
        "source": "TheElec",
        "published_date": datetime(2026, 2, 19, 19, 39, 0)
    },
    {
        "title": "Samsung to develop custom HBM with computing core",
        "content": "Samsung is developing a custom HBM with a computing core integrated. This represents major innovation in memory technology, combining HBM with computational abilities. The development effort signals Samsung's commitment to lead in advanced semiconductor packaging and integration.",
        "url": "https://www.thelec.net/news/articleView.html?idxno=5581",
        "source": "TheElec",
        "published_date": datetime(2026, 2, 19, 19, 39, 0)
    },
    {
        "title": "SK Hynix to supply HBM3E for Microsoft Maia 200 AI chip",
        "content": "SK Hynix has secured a major deal to supply HBM3E (High Bandwidth Memory 3E) for Microsoft's Maia 200 AI processor. HBM3E represents the latest advancement in high-speed memory technology, crucial for AI inference workloads. This supply agreement reinforces SK Hynix's position in the AI semiconductor ecosystem.",
        "url": "https://www.thelec.net/news/articleView.html?idxno=5562",
        "source": "TheElec",
        "published_date": datetime(2026, 2, 19, 19, 39, 0)
    }
]

def load_korean_articles():
    """한국 반도체 뉴스 기사 로드"""
    try:
        init_db()
        
        session = get_db_session()
        analyzer = NewsAnalyzer()
        
        loaded_count = 0
        
        for article_data in korean_articles:
            try:
                # 중복 체크
                existing = session.query(NewsArticle).filter_by(url=article_data['url']).first()
                if existing:
                    print(f"⊘ 이미 존재: {article_data['title'][:50]}")
                    continue
                
                # 우선순위 계산
                priority = analyzer.calculate_priority(article_data)
                
                # 기사 생성
                article = NewsArticle(
                    title=article_data['title'],
                    content=article_data['content'],
                    summary=f"반도체 산업 관련 기사: {article_data['source']}",
                    url=article_data['url'],
                    source=article_data['source'],
                    published_date=article_data['published_date'],
                    priority_score=priority,
                    crawled_at=datetime.now(),
                    category='semiconductor'
                )
                
                session.add(article)
                session.commit()
                
                print(f"✓ {priority:.1f}점 - [{article_data['source']}] {article_data['title'][:50]}")
                loaded_count += 1
                
            except Exception as e:
                print(f"✗ 에러: {str(e)[:50]}")
                session.rollback()
        
        session.close()
        print(f"\n✅ 완료: {loaded_count}개 기사 로드")
        return loaded_count > 0
        
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        return False

if __name__ == "__main__":
    success = load_korean_articles()
    sys.exit(0 if success else 1)
