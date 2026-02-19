"""
API 엔드포인트 테스트
"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:5000'

def test_api_endpoints():
    """모든 새로운 API 엔드포인트 테스트"""
    
    print("=" * 60)
    print("API 엔드포인트 테스트 시작")
    print("=" * 60)
    
    # 1. 북마크 생성
    print("\n1. 북마크 생성 테스트")
    print("-" * 40)
    try:
        response = requests.post(f"{BASE_URL}/api/bookmark", json={
            "article_id": 1,
            "notes": "중요한 반도체 뉴스"
        })
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")
    except Exception as e:
        print(f"오류: {e}")
    
    # 2. 북마크 조회
    print("\n2. 북마크 조회 테스트")
    print("-" * 40)
    try:
        response = requests.get(f"{BASE_URL}/api/bookmarks")
        print(f"상태 코드: {response.status_code}")
        data = response.json()
        print(f"저장된 북마크 수: {data.get('count', 0)}")
    except Exception as e:
        print(f"오류: {e}")
    
    # 3. 댓글 작성
    print("\n3. 댓글 작성 테스트")
    print("-" * 40)
    try:
        response = requests.post(f"{BASE_URL}/api/comment", json={
            "article_id": 1,
            "comment_text": "매우 유용한 정보입니다!",
            "nickname": "반도체 전문가"
        })
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")
    except Exception as e:
        print(f"오류: {e}")
    
    # 4. 댓글 조회
    print("\n4. 댓글 조회 테스트")
    print("-" * 40)
    try:
        response = requests.get(f"{BASE_URL}/api/comments/1")
        print(f"상태 코드: {response.status_code}")
        data = response.json()
        print(f"댓글 수: {data.get('count', 0)}")
        if data.get('comments'):
            print(f"첫 번째 댓글: {data['comments'][0]['comment_text']}")
    except Exception as e:
        print(f"오류: {e}")
    
    # 5. 댓글 좋아요
    print("\n5. 댓글 좋아요 테스트")
    print("-" * 40)
    try:
        response = requests.post(f"{BASE_URL}/api/comment/1/like")
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")
    except Exception as e:
        print(f"오류: {e}")
    
    # 6. 공유 추적
    print("\n6. 공유 추적 테스트")
    print("-" * 40)
    try:
        for share_type in ['kakao', 'link', 'copy']:
            response = requests.post(f"{BASE_URL}/api/article/share", json={
                "article_id": 1,
                "share_type": share_type
            })
            print(f"{share_type}: {response.status_code}")
    except Exception as e:
        print(f"오류: {e}")
    
    # 7. 공유 통계 조회
    print("\n7. 공유 통계 조회 테스트")
    print("-" * 40)
    try:
        response = requests.get(f"{BASE_URL}/api/share-stats/1")
        print(f"상태 코드: {response.status_code}")
        data = response.json()
        if data.get('stats'):
            stats = data['stats']
            print(f"총 공유: {stats.get('total')}")
            print(f"카톡: {stats.get('kakao')}, 링크: {stats.get('link')}, 복사: {stats.get('copy')}")
    except Exception as e:
        print(f"오류: {e}")
    
    # 8. 관리자 뉴스 추가
    print("\n8. 관리자 뉴스 추가 테스트")
    print("-" * 40)
    try:
        response = requests.post(f"{BASE_URL}/api/admin/news", json={
            "title": "삼성전자, 새로운 AI 반도체 공개",
            "content": "삼성전자가 최신 AI 가속기를 발표했습니다. 이는 차세대 인공지능 애플리케이션을 위해 설계되었습니다.",
            "source": "삼성전자 (관리자 입력)"
        })
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")
    except Exception as e:
        print(f"오류: {e}")
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

if __name__ == '__main__':
    print("주의: 테스트를 실행하려면 먼저 main_run.py 또는 web_app.py를 실행하세요")
    print("명령어: python main_run.py")
    print()
    
    try:
        test_api_endpoints()
    except requests.exceptions.ConnectionError:
        print("오류: 서버에 연결할 수 없습니다.")
        print("먼저 서버를 시작하세요: python main_run.py")
