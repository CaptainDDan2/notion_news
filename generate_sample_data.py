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
        "title": "삼성, 업계 최초 상용 HBM4 출하로 AI 컴퓨팅 성능 강화",
        "content": "삼성전자가 업계 최초로 상용 HBM4를 출하하며 AI 데이터센터용 메모리 성능을 끌어올렸습니다. HBM4는 11.7Gbps 전송 속도와 스택당 최대 3.3TB/s 대역폭을 제공하며, 24~36GB 용량 구성과 전력 효율 개선을 강조했습니다. 회사는 HBM4 이후 로드맵과 생산 역량도 함께 소개했습니다.",
        "url": "https://news.samsung.com/global/samsung-ships-industry-first-commercial-hbm4-with-ultimate-performance-for-ai-computing",
        "source": "Samsung Newsroom",
        "priority_score": 9,
        "published_date": datetime.now() - timedelta(hours=2)
    },
    {
        "title": "삼성, Galaxy A07 5G 출시…AI 기능과 6,000mAh 배터리 강조",
        "content": "삼성전자가 Galaxy A07 5G를 공개하며 보급형 라인업에 AI 기능을 확대했습니다. Gemini, Circle to Search 지원과 함께 6,000mAh 배터리, 6.7인치 120Hz 디스플레이, IP54 등급 등 주요 사양이 소개됐습니다. 제품은 일부 지역부터 순차 출시됩니다.",
        "url": "https://news.samsung.com/global/samsung-launches-galaxy-a07-5g-bringing-intelligence-and-reliable-performance-to-more-galaxy-a-series-devices",
        "source": "Samsung Newsroom",
        "priority_score": 7,
        "published_date": datetime.now() - timedelta(hours=4)
    },
    {
        "title": "삼성 연구원, 3GPP Excellence Award 수상…MIMO 표준화 기여",
        "content": "삼성 리서치 아메리카의 연구원이 3GPP Excellence Award를 수상했습니다. 수상자는 RAN1에서 MIMO 표준화와 차세대 이동통신 핵심 기술에 기여한 점을 인정받았습니다. 삼성은 6G 표준화 참여와 이동통신 기술 리더십을 강조했습니다.",
        "url": "https://news.samsung.com/global/samsung-researcher-receives-3gpp-excellence-award",
        "source": "Samsung Newsroom",
        "priority_score": 6,
        "published_date": datetime.now() - timedelta(hours=6)
    },
    {
        "title": "Samsung TV Plus, 월간 이용자 1억 명 돌파",
        "content": "Samsung TV Plus가 월간 활성 사용자 1억 명을 돌파했다고 발표했습니다. FAST 기반 무료 스트리밍 서비스로 채널과 VOD를 확대하고 AI 기반 콘텐츠 개선을 추진 중이라고 설명했습니다. 글로벌 미디어 플랫폼으로의 전환 전략도 소개했습니다.",
        "url": "https://news.samsung.com/global/from-hardware-roots-to-global-media-platform-how-samsung-tv-plus-reached-100-million-users",
        "source": "Samsung Newsroom",
        "priority_score": 5,
        "published_date": datetime.now() - timedelta(hours=8)
    },
    {
        "title": "퀄컴, AI200·AI250 공개…데이터센터 추론 성능 강화",
        "content": "퀄컴이 데이터센터용 AI 추론 가속기 AI200과 AI250을 공개했습니다. 랙 스케일 추론 성능과 메모리 대역폭 향상, TCO 개선을 강조했으며, AI250은 새로운 메모리 아키텍처로 효율을 높였습니다. 상용화는 2026~2027년을 목표로 합니다.",
        "url": "https://www.qualcomm.com/news/releases/2025/10/qualcomm-unveils-ai200-and-ai250-redefining-rack-scale-data-cent",
        "source": "Qualcomm Press Release",
        "priority_score": 8,
        "published_date": datetime.now() - timedelta(hours=10)
    },
    {
        "title": "퀄컴, Alphawave Semi 인수 완료…고속 연결성 강화",
        "content": "퀄컴이 Alphawave Semi 인수 완료를 발표했습니다. 고속 유선 연결 기술을 확보해 데이터센터와 AI 컴퓨팅 확장에 활용한다는 계획입니다. 인수로 Oryon CPU와 Hexagon NPU 생태계와의 시너지도 강조했습니다.",
        "url": "https://www.qualcomm.com/news/releases/2025/12/qualcomm-completes-acquisition-of-alphawave-semi",
        "source": "Qualcomm Press Release",
        "priority_score": 7,
        "published_date": datetime.now() - timedelta(hours=12)
    },
    {
        "title": "퀄컴, 로보틱스 전용 플랫폼 공개…Physical AI 확대",
        "content": "퀄컴이 로봇용 종합 기술 스택과 Dragonwing IQ10 시리즈를 공개했습니다. 휴머노이드부터 산업용 AMR까지 다양한 로봇 폼팩터를 지원하며, 안전 등급 SoC와 파트너 생태계를 강화한다고 밝혔습니다. CES에서 데모도 진행됐습니다.",
        "url": "https://www.qualcomm.com/news/releases/2026/01/qualcomm-introduces-a-full-suite-of-robotics-technologies-power",
        "source": "Qualcomm Press Release",
        "priority_score": 7,
        "published_date": datetime.now() - timedelta(hours=14)
    },
    {
        "title": "NVIDIA-메타, AI 인프라 협력 확대…Blackwell·Rubin 대규모 도입",
        "content": "NVIDIA가 메타와의 파트너십을 확대해 대규모 AI 인프라 구축을 지원한다고 발표했습니다. Grace CPU, Blackwell·Rubin GPU, Spectrum-X 네트워킹과 Confidential Computing 도입을 통해 학습·추론 효율을 높인다는 내용입니다.",
        "url": "https://nvidianews.nvidia.com/news/meta-builds-ai-infrastructure-with-nvidia",
        "source": "NVIDIA Newsroom",
        "priority_score": 9,
        "published_date": datetime.now() - timedelta(hours=16)
    },
    {
        "title": "NVIDIA Blackwell 기반 오픈소스 모델로 추론 비용 최대 10배 절감",
        "content": "NVIDIA 블로그는 Blackwell 플랫폼과 오픈소스 모델 조합으로 추론 비용을 크게 줄인 사례를 소개했습니다. Baseten, DeepInfra, Fireworks AI, Together AI 등이 토큰 비용과 지연 시간을 개선한 사례를 공유했습니다.",
        "url": "https://blogs.nvidia.com/blog/inference-open-source-models-blackwell-reduce-cost-per-token/",
        "source": "NVIDIA Blog",
        "priority_score": 8,
        "published_date": datetime.now() - timedelta(hours=18)
    },
    {
        "title": "NVIDIA DGX Spark, 대학 연구 현장에 데스크톱급 AI 슈퍼컴퓨터 확산",
        "content": "NVIDIA 블로그는 DGX Spark가 대학 연구 현장에 확산되고 있다고 소개했습니다. IceCube, NYU, Harvard 등에서 로컬 AI 실험과 민감 데이터 처리에 활용 중이며, 데스크톱급 시스템으로도 대형 모델을 다루는 사례가 포함됐습니다.",
        "url": "https://blogs.nvidia.com/blog/dgx-spark-higher-education/",
        "source": "NVIDIA Blog",
        "priority_score": 6,
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