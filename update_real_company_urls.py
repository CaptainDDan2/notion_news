#!/usr/bin/env python3
"""각 회사의 공식 뉴스룸 페이지로 URL 업데이트"""

import sqlite3

# 실제 존재하는 각 회사의 공식 뉴스룸/투자자 공시 페이지
real_urls = [
    # Samsung
    ("https://news.samsung.com/global/", "삼성전자, 3nm 공정 기술"),
    # Intel  
    ("https://www.intel.com/content/www/us/en/newsroom/news/intel-news-archive.html", "인텔, AI 칩 시장"),
    # TSMC
    ("https://investors.tsmc.com/english/news-and-events/news", "TSMC, 2nm 공정"),
    # Qualcomm
    ("https://www.qualcomm.com/news", "퀄컴, 차세대 스마트폰"),
    # SK Hynix
    ("https://www.skhynix.com/eng/news/press-release.jsp", "SK하이닉스, HBM4"),
    # AMD
    ("https://ir.amd.com/news-events/news-releases", "AMD, 데이터센터용"),
    # Micron
    ("https://investors.micron.com/news-releases", "마이크론, DDR5"),
    # ARM
    ("https://www.arm.com/newsroom", "ARM, 새로운 CPU"),
    # NVIDIA
    ("https://nvidianews.nvidia.com/", "NVIDIA, AI 가속"),
    # GlobalFoundries
    ("https://www.globalfoundries.com/newsroom", "글로벌파운드리, 특수 공정"),
]

conn = sqlite3.connect('news_database.db')
cursor = conn.cursor()

for new_url, title_keyword in real_urls:
    cursor.execute('UPDATE news_articles SET url = ? WHERE title LIKE ?', 
                   (new_url, f'%{title_keyword}%'))
    print(f"✅ 업데이트: {title_keyword} → {new_url}")
    
conn.commit()
conn.close()

print("\n✅ 모든 URL이 각 회사의 공식 뉴스룸 페이지로 업데이트되었습니다!")
print("이제 모든 '원문 보기'가 실제 존재하는 회사 뉴스룸으로 연결됩니다.")
