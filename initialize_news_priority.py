#!/usr/bin/env python3
"""
뉴스 우선순위 초기화 스크립트
Render 배포 시 자동으로 실행되어 특정 출처(TheElec, 전자신문, 서울경제)의 기사들의 우선순위를 높입니다.
"""

import sqlite3
from datetime import datetime
import os
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_news_priority():
    """뉴스 우선순위 초기화 - 특정 출처의 기사들을 최신으로 업데이트"""
    
    db_file = 'news_database.db'
    
    # 데이터베이스 파일 확인
    if not os.path.exists(db_file):
        logger.info("데이터베이스가 아직 생성되지 않았습니다. 초기 실행 시 자동 생성됩니다.")
        return
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 현재 시간
        now = datetime.now()
        
        # 우선순위를 높일 출처들
        high_priority_sources = ['TheElec', '전자신문', '서울경제']
        
        print("=" * 70)
        print("뉴스 우선순위 초기화")
        print("=" * 70)
        
        for source in high_priority_sources:
            # 기사 개수 확인
            cursor.execute("SELECT COUNT(*) FROM news_articles WHERE source = ?", (source,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                # 타임스탐프 업데이트 (최신으로 만들기)
                cursor.execute(
                    "UPDATE news_articles SET crawled_at = ? WHERE source = ?",
                    (now, source)
                )
                conn.commit()
                logger.info(f"✓ {source}: {count}개 기사 우선순위 업데이트")
                print(f"  {source}: {count}개 기사 우선순위 상향")
            else:
                logger.info(f"- {source}: 기사 없음")
        
        conn.close()
        logger.info("우선순위 초기화 완료!")
        print("\n뉴스 우선순위 초기화 완료!")
        
    except sqlite3.OperationalError as e:
        logger.error(f"데이터베이스 접근 오류: {str(e)}")
        # 테이블이 없는 경우 무시 (초기 실행)
        pass
    except Exception as e:
        logger.error(f"우선순위 초기화 중 오류: {str(e)}")
        raise

if __name__ == "__main__":
    initialize_news_priority()
