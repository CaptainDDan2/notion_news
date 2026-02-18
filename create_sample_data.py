#!/usr/bin/env python3
"""
샘플 데이터 생성 스크립트
테스트용 반도체 뉴스 데이터를 데이터베이스에 추가
"""

from database import init_db, NewsArticle, database_session
from news_analyzer import NewsAnalyzer
from datetime import datetime, timedelta
import random

def create_sample_articles():
    """샘플 기사 데이터 생성"""
    sample_articles = [
        {
            'title': 'TSMC 3nm 공정 기술로 AI 칩 성능 30% 향상 달성',
            'content': 'TSMC가 최신 3nm 공정 기술을 통해 AI 칩의 성능을 30% 향상시켰다고 발표했습니다. 이번 혁신적인 기술은 전력 효율성도 크게 개선했으며, 다음 세대 스마트폰과 서버용 프로세서에 적용될 예정입니다. 회사 관계자는 이 기술이 글로벌 반도체 시장에서 새로운 표준을 제시할 것이라고 설명했습니다.',
            'source': 'TechNews Korea',
            'url': 'https://example.com/tsmc-3nm-breakthrough'
        },
        {
            'title': '삼성전자, 차세대 HBM4 메모리 개발 성공적 완료',
            'content': '삼성전자가 차세대 고대역폭 메모리(HBM4) 개발을 성공적으로 완료했다고 발표했습니다. 새로운 HBM4는 기존 HBM3 대비 50% 향상된 속도와 40% 낮은 전력 소비를 실현했습니다. 이는 AI 데이터센터와 고성능 컴퓨팅 분야에 혁신을 가져올 것으로 전망됩니다.',
            'source': '전자신문', 
            'url': 'https://example.com/samsung-hbm4-development'
        },
        {
            'title': 'NVIDIA H200 AI 가속기, 전작 대비 2.5배 성능 향상',
            'content': 'NVIDIA가 최신 AI 가속기 H200을 발표했습니다. H200은 기존 H100 대비 2.5배 향상된 메모리 성능과 1.8배 빨라진 연산 속도를 제공합니다. 이번 제품은 대규모 언어모델 훈련과 추론에 특화되어 설계되었으며, 생성형 AI 시장의 새로운 기준점이 될 것으로 예상됩니다.',
            'source': 'AI Weekly',
            'url': 'https://example.com/nvidia-h200-announcement'
        },
        {
            'title': 'Intel 차세대 파운드리 서비스 2025년 상반기 출시 예정',
            'content': 'Intel이 차세대 파운드리 서비스를 2025년 상반기에 출시한다고 발표했습니다. Intel 18A 공정을 기반으로 하는 이 서비스는 TSMC와 경쟁할 수 있는 수준의 성능과 효율성을 제공할 예정입니다. 이는 글로벌 반도체 파운드리 시장에 새로운 경쟁자가 등장함을 의미합니다.',
            'source': 'Semiconductor Today',
            'url': 'https://example.com/intel-foundry-2025'
        },
        {
            'title': '퀄컴 스냅드래곤 8 Gen 4, 3nm 공정으로 전력효율 극대화',
            'content': '퀄컴이 스냅드래곤 8 Gen 4 모바일 프로세서를 발표했습니다. 3nm 공정으로 제조된 이 칩은 이전 세대 대비 25% 향상된 CPU 성능과 40% 개선된 GPU 성능을 제공합니다. 또한 AI 처리 성능이 70% 향상되어 온디바이스 AI 경험을 한층 끌어올릴 것으로 기대됩니다.',
            'source': 'Mobile Tech Review',
            'url': 'https://example.com/snapdragon-8-gen4'
        },
        {
            'title': 'SK하이닉스, CXL 메모리 모듈 대량 생산 개시',
            'content': 'SK하이닉스가 CXL(Compute Express Link) 메모리 모듈의 대량 생산을 개시한다고 발표했습니다. 이 제품은 데이터센터와 HPC 시스템에서 메모리 병목현상을 해결하고 전체 시스템 성능을 향상시킬 것으로 기대됩니다. 회사는 2024년 말까지 월 100만 개 생산 체제를 구축할 계획이라고 밝혔습니다.',
            'source': '반도체 뉴스',
            'url': 'https://example.com/skhynix-cxl-production'
        },
        {
            'title': 'ARM 새로운 Cortex-X5 CPU 아키텍처 발표, 성능 35% 향상',
            'content': 'ARM이 새로운 Cortex-X5 CPU 아키텍처를 발표했습니다. 이 아키텍처는 기존 Cortex-X4 대비 35% 향상된 성능과 30% 개선된 전력 효율성을 제공합니다. 특히 AI 워크로드에서의 성능 향상이 두드러지며, 차세대 스마트폰과 노트북에 적용될 예정입니다.',
            'source': 'ARM Today',
            'url': 'https://example.com/arm-cortex-x5-architecture'
        },
        {
            'title': '글로벌 반도체 시장, 2024년 8.8% 성장 전망',
            'content': '시장조사기관에 따르면 글로벌 반도체 시장이 2024년 8.8% 성장할 것으로 전망된다고 발표했습니다. AI 반도체의 급성장과 데이터센터 투자 증가가 주요 성장 동력으로 작용하고 있습니다. 메모리 반도체 가격 회복과 자동차용 반도체 수요 증가도 긍정적 요인으로 분석됩니다.',
            'source': 'Market Research',
            'url': 'https://example.com/semiconductor-market-growth'
        },
        {
            'title': 'AMD Ryzen 8000 시리즈, AI 가속화 기능 대폭 강화',
            'content': 'AMD가 Ryzen 8000 시리즈 프로세서에서 AI 가속화 기능을 대폭 강화했다고 발표했습니다. 새로운 XDNA 2 아키텍처를 채택하여 AI 추론 성능을 이전 세대 대비 3배 향상시켰습니다. 이는 로컬 AI 처리 능력을 크게 향상시켜 클라우드 의존도를 줄일 수 있을 것으로 기대됩니다.',
            'source': 'CPU World',
            'url': 'https://example.com/amd-ryzen-8000-ai'
        },
        {
            'title': '테라다인, 차세대 반도체 테스트 장비 혁신 기술 공개',
            'content': '테라다인이 차세대 반도체 테스트 장비의 혁신 기술을 공개했습니다. 새로운 시스템은 기존 대비 50% 빠른 테스트 속도와 70% 향상된 정확도를 제공합니다. 이는 AI 칩과 고성능 프로세서의 복잡한 테스트 요구사항을 효과적으로 처리할 수 있게 해줍니다.',
            'source': 'Test Equipment News',
            'url': 'https://example.com/teradyne-test-innovation'
        }
    ]
    
    return sample_articles

def insert_sample_data():
    """샘플 데이터를 데이터베이스에 삽입"""
    print("샘플 데이터 생성 중...")
    
    # 데이터베이스 초기화
    init_db()
    
    # 분석기 초기화
    analyzer = NewsAnalyzer()
    
    # 샘플 기사 데이터
    sample_articles = create_sample_articles()
    
    inserted_count = 0
    for i, article_data in enumerate(sample_articles):
        try:
            # 중복 체크
            existing = database_session.query(NewsArticle).filter_by(url=article_data['url']).first()
            if existing:
                print(f"기사 {i+1}: 이미 존재함 - {article_data['title'][:50]}...")
                continue
            
            # 분석 및 요약
            summary = analyzer.summarize_article(article_data['content'])
            priority = analyzer.calculate_priority({
                **article_data,
                'published_date': datetime.now() - timedelta(hours=random.randint(1, 48))
            })
            
            # 발행일 랜덤 설정 (최근 2일 내)
            published_date = datetime.now() - timedelta(
                hours=random.randint(1, 48),
                minutes=random.randint(0, 59)
            )
            
            # 데이터베이스에 저장
            article = NewsArticle(
                title=article_data['title'],
                content=article_data['content'],
                summary=summary,
                url=article_data['url'],
                source=article_data['source'],
                published_date=published_date,
                priority_score=priority,
                crawled_at=datetime.now()
            )
            
            database_session.add(article)
            inserted_count += 1
            
            print(f"기사 {i+1}: 추가됨 ({priority:.1f}점) - {article_data['title'][:50]}...")
            
        except Exception as e:
            print(f"기사 {i+1} 추가 오류: {str(e)}")
            continue
    
    try:
        database_session.commit()
        print(f"\n✅ 샘플 데이터 생성 완료: {inserted_count}개 기사가 추가되었습니다.")
    except Exception as e:
        database_session.rollback()
        print(f"\n❌ 데이터베이스 저장 오류: {str(e)}")

if __name__ == "__main__":
    insert_sample_data()