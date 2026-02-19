#!/usr/bin/env python3
"""
샘플 뉴스 데이터 생성 스크립트
구체적인 요약을 포함한 테스트용 데이터 생성
"""

from datetime import datetime, timedelta
import random
from database import init_db, NewsArticle, get_db_session
from news_analyzer import NewsAnalyzer

# 샘플 뉴스 데이터
sample_articles = [
    {
        "title": "삼성전자, 3nm 공정 기술로 새로운 반도체 혁신 발표",
        "content": "삼성전자가 최신 3nm 공정 기술을 활용한 차세대 반도체 제품 개발에 성공했다고 발표했습니다. 이번 기술은 기존 대비 30% 더 빠른 성능과 45% 절약된 전력 소비를 실현합니다. 삼성이 전세계에서 가장 진보된 3나노미터 제조 공정을 상용화핸으며, 특히 AI 칩과 모바일 프로세서 시장에서 경쟁 우위를 누리고자 하는 전략으로 분석됩니다.",
        "url": "https://news.samsung.com/global/",
        "source": "EE Times",
        "priority_score": 9,
        "published_date": datetime.now() - timedelta(hours=2)
    },
    {
        "title": "인텔, AI 칩 시장 공략을 위한 새로운 전략 발표",
        "content": "인텔이 AI 칩 시장에서의 경쟁력 강화를 위해 새로운 아키텍처와 제조 기술을 공개했습니다. 특히 데이터센터와 엣지 컴퓨팅 분야에 집중할 예정입니다. 인텔은 2024년 대비 AI 처리 성능이 50% 향상된 새로운 Gaudi 시리즈를 출시하며, NVIDIA와의 경쟁에서 우위를 점하고자 한다고 발표했습니다.",
        "url": "https://www.intel.com/content/www/us/en/newsroom/news/intel-news-archive.html",
        "source": "AnandTech",
        "priority_score": 8,
        "published_date": datetime.now() - timedelta(hours=4)
    },
    {
        "title": "TSMC, 2nm 공정 양산 계획 앞당겨",
        "content": "대만의 반도체 파운드리 기업 TSMC가 2nm 공정의 양산 시작을 기존 계획보다 6개월 앞당긴다고 발표했습니다. 이는 글로벌 반도체 경쟁이 더욱 치열해질 것임을 의미하며, Apple의 A-시리즈와 M-시리즈 칩에 우선 적용될 예정입니다. GAA(Gate-All-Around) 기술과 최첨단 EUV 리소그래피 기술을 결합하여, 기존 3nm 공정 대비 성능은 10-15% 향상되고 전력 소비는 25-30% 절감될 것으로 예상됩니다.",
        "url": "https://investors.tsmc.com/english/news-and-events/news",
        "source": "Semiconductor Engineering",
        "priority_score": 9,
        "published_date": datetime.now() - timedelta(hours=6)
    },
    {
        "title": "퀄컴, 차세대 스마트폰용 5G 칩셋 공개",
        "content": "퀄컴이 Snapdragon 8 Gen 3+ 브랜드로 차세대 스마트폰을 위한 새로운 5G 칩셋을 공개했습니다. 이 칩셋은 6GHz 이상의 밀리미터파 주파수 대역을 지원하여 기존 대비 40% 빠른 다운로드 속도와 25% 향상된 전력 효율성을 제공합니다. 특히 AI 연산 성능이 3배 개선되어 실시간 언어 번역과 영상 처리 기능이 대폭 강화되었습니다. 삼성, 샤오미 등 주요 제조업체들이 2024년 하반기 출시 예정인 플래그십 스마트폰에 탑재할 예정입니다.",
        "url": "https://www.qualcomm.com/news",
        "source": "Tom's Hardware",
        "priority_score": 7,
        "published_date": datetime.now() - timedelta(hours=8)
    },
    {
        "title": "SK하이닉스, HBM4 메모리 개발 성공",
        "content": "SK하이닉스가 차세대 고대역폭 메모리(HBM4) 개발에 성공했다고 발표했습니다. HBM4는 1.2TB/s의 대역폭과 32GB 단일 패키지 용량을 제공하여 기존 HBM3E 대비 50% 성능 향상을 달성했습니다. 특히 NVIDIA의 차세대 GPU와 AMD의 MI300 시리즈 등 AI 가속기에 최적화되어 있으며, ChatGPT와 같은 대규모 언어 모델 훈련 시 메모리 병목현상을 크게 해결할 것으로 기대됩니다. 2025년 1분기부터 양산을 시작하여 삼성전자와의 치열한 메모리 시장 경쟁에서 우위를 점할 계획입니다.",
        "url": "https://www.skhynix.com/eng/news/press-release.jsp",
        "source": "EE News",
        "priority_score": 8,
        "published_date": datetime.now() - timedelta(hours=10)
    },
    {
        "title": "AMD, 데이터센터용 새로운 EPYC 프로세서 발표",
        "content": "AMD가 Zen 4c 아키텍처를 기반으로 한 새로운 EPYC 9004 시리즈 데이터센터 프로세서를 발표했습니다. 최대 128코어와 256스레드를 지원하며, 기존 대비 클라우드 워크로드 성능이 35% 향상되었습니다. 특히 DDR5-5200 메모리와 PCIe 5.0을 완전 지원하여 가상화 환경과 AI 추론 작업에서 탁월한 성능을 보여줍니다. 인텔의 Xeon Scalable 대비 TCO(총 소유 비용)를 30% 절감할 수 있어 Azure, AWS 등 주요 클라우드 서비스 제공업체들이 도입을 검토 중입니다. 2024년 3분기부터 OEM 파트너사를 통해 공급될 예정입니다.",
        "url": "https://ir.amd.com/news-events/news-releases",
        "source": "Electronics Weekly",
        "priority_score": 7,
        "published_date": datetime.now() - timedelta(hours=12)
    },
    {
        "title": "마이크론, DDR5 메모리 용량 혁신 발표",
        "content": "마이크론 테크놀로지가 업계 최고 단일 모듈 용량인 128GB DDR5 DIMM을 상용화한다고 발표했습니다. DDR5-5600 속도를 지원하며, 기존 DDR4 대비 대역폭이 60% 향상되고 전력 소비는 20% 감소했습니다. 특히 인공지능 학습과 데이터 분석에 필요한 대용량 메모리에 대한 수요가 폭증하는 가운데, 기업용 서버와 고성능 워크스테이션 시장에서의 채택이 빠르게 증가할 것으로 예상됩니다. 2024년 하반기부터 본격적인 대량 생산에 들어갈 예정입니다.",
        "url": "https://investors.micron.com/news-releases",
        "source": "EDN Network",
        "priority_score": 6,
        "published_date": datetime.now() - timedelta(hours=14)
    },
    {
        "title": "ARM, 새로운 CPU 아키텍처로 성능 향상 달성",
        "content": "ARM Holdings가 Cortex-X4 아키텍처를 기반으로 이전 세대 대비 싱글 코어 성능 15%, 멀티 코어 성능 20% 향상을 달성한 새로운 CPU 아키텍처를 발표했습니다. 특히 모바일 프로세서에서는 전력 효율성이 25% 개선되었으며, AI 연산 처리를 위해 새로운 처리 파이프라인을 추가하여 온디바이스 AI 처리 성능이 40% 향상되었습니다. IoT와 엣지 컴퓨팅 영역에서는 ARM Cortex-M85 모델이 새롭게 추가되어 실시간 AI 인퍼런스를 지원합니다.",
        "url": "https://www.arm.com/newsroom",
        "source": "Electronics360",
        "priority_score": 6,
        "published_date": datetime.now() - timedelta(hours=16)
    },
    {
        "title": "NVIDIA, AI 가속을 위한 새로운 GPU 발표",
        "content": "NVIDIA가 Hopper 아키텍처의 후속 모델인 H200 GPU를 공식 발표했습니다. H200은 기존 H100 대비 AI 훈련 속도가 2배 빠르며, 특히 LLM(대규모 언어 모델) 추론에서는 2.5배 성능 향상을 보여줍니다. 141GB HBM3e 메모리를 탑재하여 메모리 대역폭이 4.8TB/s에 달하며, Transformer 모델의 self-attention 메커니즘 처리에 특화된 FlashAttention-2 엔진을 내장했습니다. 또한 FP4 정밀도를 지원하여 모델 크기를 절반으로 줄이면서도 정확도를 유지할 수 있습니다.",
        "url": "https://nvidianews.nvidia.com/",
        "source": "All About Circuits",
        "priority_score": 9,
        "published_date": datetime.now() - timedelta(hours=18)
    },
    {
        "title": "글로벌파운드리, 특수 공정 기술 확장 계획",
        "content": "글로벌파운드리가 자동차 반도체와 IoT 칩을 위한 22FDX와 12LP+ 특수 공정 기술 확장에 50억 달러를 투자한다고 발표했습니다. 이는 홀두막 성장하는 전기차 시장과 스마트 IoT 디바이스 수요에 대응하기 위한 전략입니다. 22FDX 공정은 저전력과 고성능을 동시에 요구하는 자동차 ADAS 칩과 마이크로컨트롤러에 최적화되어 있으며, 12LP+ 공정은 엣지 AI 칩과 5G RF 소자 산업에 특화되어 있습니다. 이를 통해 TSMC와 삼성의 최첫단 공정 경쟁에서는 비켜서더라도 특수 용도 시장에서의 입지를 강화하려는 목표입니다.",
        "url": "https://www.globalfoundries.com/newsroom",
        "source": "SemiMedia",
        "priority_score": 5,
        "published_date": datetime.now() - timedelta(hours=20)
    }
]

def create_sample_data():
    """샘플 뉴스 데이터를 데이터베이스에 추가"""
    print("데이터베이스 초기화 중...")
    init_db()
    
    session = get_db_session()
    analyzer = NewsAnalyzer()
    
    print("샘플 뉴스 데이터 생성 중...")
    
    for article_data in sample_articles:
        # 중복 체크
        existing = session.query(NewsArticle).filter_by(url=article_data['url']).first()
        if existing:
            continue
        
        # AI를 사용하여 동적으로 요약 생성
        print(f"  요약 생성 중: {article_data['title'][:30]}...")
        summary = analyzer.summarize_article(article_data['content'], max_length=500)
        
        # 새 기사 생성
        article = NewsArticle(
            title=article_data['title'],
            content=article_data['content'],
            summary=summary,
            url=article_data['url'],
            source=article_data['source'],
            published_date=article_data['published_date'],
            priority_score=article_data['priority_score'],
            crawled_at=datetime.now()
        )
        
        session.add(article)
        print(f"  추가됨: {article_data['title'][:50]}...")
    
    try:
        session.commit()
        print(f"샘플 데이터 추가 완료! 총 {len(sample_articles)}개의 기사가 추가되었습니다.")
        print("구체적이고 상세한 AI 요약이 포함된 기사들이 생성되었습니다.")
        print("웹 브라우저에서 http://localhost:5000에 접속하여 확인하세요.")
    except Exception as e:
        session.rollback()
        print(f"데이터 저장 중 오류 발생: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    create_sample_data()