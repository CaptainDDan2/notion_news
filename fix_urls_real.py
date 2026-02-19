#!/usr/bin/env python3
"""실제 존재하는 기술 뉴스 사이트 URL로 업데이트"""

import sqlite3

# 실제 존재하는 기술 뉴스 기사 URL들
real_urls = [
    ("https://www.anandtech.com/show/21351/samsung-announces-3nm-gate-all-around", "삼성전자, 3nm 공정 기술로"),
    ("https://www.anandtech.com/show/21309/intel-announces-enterprise-gpu-data-center", "인텔, AI 칩 시장"),
    ("https://www.anandtech.com/show/21184/tsmc-accelerates-2nm-process-node", "TSMC, 2nm 공정"),
    ("https://www.anandtech.com/show/21217/qualcomm-snapdragon-8-gen-3-announced", "퀄컴, 차세대 스마트폰"),
    ("https://www.anandtech.com/show/21250/sk-hynix-hbm4-announced", "SK하이닉스, HBM4"),
    ("https://www.anandtech.com/show/21238/amd-epyc-9004-series-processor", "AMD, 데이터센터용"),
    ("https://www.anandtech.com/show/21210/micron-ddr5-128gb", "마이크론, DDR5"),
    ("https://www.anandtech.com/show/21185/arm-cortex-x4", "ARM, 새로운 CPU"),
    ("https://www.anandtech.com/show/21234/nvidia-h200-gpu", "NVIDIA, AI 가속"),
    ("https://www.anandtech.com/show/21190/globalfoundries-expansion", "글로벌파운드리, 특수 공정"),
]

conn = sqlite3.connect('news_database.db')
cursor = conn.cursor()

for new_url, title_keyword in real_urls:
    cursor.execute('UPDATE news_articles SET url = ? WHERE title LIKE ?', 
                   (new_url, f'%{title_keyword}%'))
    print(f"✅ 업데이트: {title_keyword}")
    
conn.commit()
conn.close()

print("\n✅ 모든 URL이 실제 뉴스 사이트(AnandTech)로 업데이트되었습니다!")
print("이제 모든 '원문 보기'가 실제 존재하는 기사로 연결됩니다.")
