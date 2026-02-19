"""
뉴스 크롤링 모듈
반도체 관련 뉴스 사이트에서 기사를 수집
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict
from html import unescape
import xml.etree.ElementTree as ET
import random

logger = logging.getLogger(__name__)

class NewsCrawler:
    def __init__(self):
        """크롤러 초기화"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.max_per_source = 20
        
        # 반도체 관련 뉴스 사이트 목록
        self.news_sources = [
            {
                'name': 'EE Times',
                'url': 'https://www.eetimes.com/category/semiconductors/',
                'selector': {
                    'articles': 'article',
                    'title': 'h2 a, h3 a',
                    'link': 'h2 a, h3 a',
                    'content': 'div.entry-content, div.excerpt'
                }
            },
            {
                'name': '전자신문',
                'list_urls': [
                    'https://www.etnews.com/news/section.html?id1=06',
                    'https://www.etnews.com/news/section.html?id1=03',
                    'https://www.etnews.com/news/section.html?id1=04'
                ],
                'link_pattern': 'https://www.etnews.com/',
                'link_regex': r'https://www\.etnews\.com/\d{11,}'
            },
            {
                'name': 'TheElec',
                'list_urls': [
                    'https://www.thelec.net/news/articleList.html?sc_section_code=S1N3&view_type=sm',
                    'https://www.thelec.net/news/articleList.html?sc_section_code=S1N1&view_type=sm'
                ],
                'link_pattern': 'https://www.thelec.net/news/articleView.html?idxno='
            },
            {
                'name': '서울경제',
                'list_urls': [
                    'https://www.sedaily.com/business/it',
                    'https://www.sedaily.com/business/corporation'
                ],
                'link_pattern': 'https://www.sedaily.com/article/',
                'link_regex': r'https://www\.sedaily\.com/article/\d+'
            },
            {
                'name': 'ZDNet Korea',
                'list_urls': [
                    'https://zdnet.co.kr/news/?lstcode=0100&page=1',
                    'https://zdnet.co.kr/news/?lstcode=0120&page=1'
                ],
                'link_pattern': 'https://zdnet.co.kr/view/?no='
            },
            {
                'name': '머니투데이',
                'list_urls': [
                    'https://www.mt.co.kr/tech',
                    'https://www.mt.co.kr/industry'
                ],
                'link_pattern': 'https://www.mt.co.kr/',
                'link_regex': r'https://www\.mt\.co\.kr/(tech|industry)/\d{4}/\d{2}/\d{2}/\d+'
            },
            {
                'name': '블로터',
                'list_urls': [
                    'https://www.bloter.net/news/articleList.html?sc_section_code=S1N4&view_type=sm',
                    'https://www.bloter.net/news/articleList.html?sc_section_code=S1N20&view_type=sm'
                ],
                'link_pattern': 'https://www.bloter.net/news/articleView.html?idxno='
            },
            {
                'name': 'Semiconductor Engineering',
                'url': 'https://semiengineering.com/',
                'selector': {
                    'articles': '.post-item',
                    'title': '.post-title a',
                    'link': '.post-title a',
                    'content': '.post-excerpt'
                }
            },
            {
                'name': 'AnandTech',
                'url': 'https://www.anandtech.com/tag/semiconductors',
                'selector': {
                    'articles': '.article',
                    'title': 'h2 a',
                    'link': 'h2 a',
                    'content': '.description'
                }
            },
            {
                'name': 'Tom\'s Hardware',
                'url': 'https://www.tomshardware.com/news/tag/semiconductors',
                'selector': {
                    'articles': '.article-item',
                    'title': '.article-name a',
                    'link': '.article-name a',
                    'content': '.synopsis'
                }
            },
            {
                'name': '디지털타임스',
                'url': 'http://www.dt.co.kr/contents.html?article_no=2021020302109976601002',
                'selector': {
                    'articles': '.article_list div',
                    'title': 'a',
                    'link': 'a',
                    'content': '.summary'
                }
            },
            {
                'name': 'TechCrunch',
                'url': 'https://techcrunch.com/category/hardware/',
                'selector': {
                    'articles': '.post-block',
                    'title': '.post-block__title a',
                    'link': '.post-block__title a',
                    'content': '.post-block__content'
                }
            },
            {
                'name': 'IEEE Spectrum',
                'url': 'https://spectrum.ieee.org/topic/semiconductors/',
                'selector': {
                    'articles': '.article',
                    'title': 'h3 a',
                    'link': 'h3 a',
                    'content': '.deck'
                }
            },
            {
                'name': 'The Register',
                'url': 'https://www.theregister.com/hardware/semiconductors/',
                'selector': {
                    'articles': '.story_link',
                    'title': 'h4',
                    'link': '',
                    'content': '.standfirst'
                }
            },
            {
                'name': 'Nikkei Asia',
                'url': 'https://asia.nikkei.com/Business/Tech/Semiconductors',
                'selector': {
                    'articles': '.article',
                    'title': '.article__title a',
                    'link': '.article__title a',
                    'content': '.article__excerpt'
                }
            }
        ]
        
        # 반도체 관련 키워드
        self.semiconductor_keywords = [
            'semiconductor', 'chip', 'processor', 'memory', 'DRAM', 'NAND',
            '반도체', '칩', '프로세서', '메모리', '낸드', 'AI chip', 'GPU',
            'CPU', 'SoC', 'foundry', 'wafer', 'fab', 'TSMC', 'Samsung',
            'Intel', 'NVIDIA', 'ARM', 'RISC-V', '5nm', '3nm', '2nm'
        ]

    def is_relevant_article(self, title: str, content: str = "") -> bool:
        """반도체 관련 기사인지 판단"""
        text = (title + " " + content).lower()
        return any(keyword.lower() in text for keyword in self.semiconductor_keywords)

    def extract_article_content(self, url: str) -> str:
        """기사의 전체 내용 추출"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 일반적인 기사 내용 선택자들
            content_selectors = [
                '.entry-content',
                '.article-content', 
                '.post-content',
                '.content',
                '.article-body',
                'main article',
                '[class*="content"]'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text(strip=True) for elem in elements])
                    break
            
            if not content:
                # 백업: 모든 p 태그에서 텍스트 추출
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            return content[:5000]  # 최대 5000자로 제한
            
        except Exception as e:
            logger.error(f"기사 내용 추출 실패 {url}: {str(e)}")
            return ""

    def parse_date(self, date_str: str) -> datetime:
        """날짜 문자열을 datetime 객체로 변환"""
        if not date_str:
            return datetime.now()
        
        # 간단한 날짜 파싱 (실제로는 더 정교한 파싱이 필요)
        try:
            # 몇 가지 일반적인 날짜 형식 시도
            date_formats = [
                '%Y-%m-%d',
                '%Y.%m.%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%B %d, %Y',
                '%d %B %Y'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
            
            # 파싱 실패시 현재 시간 반환
            return datetime.now()
        except:
            return datetime.now()

    def _fetch_rss_content(self, rss_urls: List[str]) -> str:
        """RSS URL 목록에서 첫 번째로 성공하는 RSS 내용을 가져오기"""
        for rss_url in rss_urls:
            try:
                response = self.session.get(rss_url, timeout=15)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.warning(f"RSS 요청 실패: {rss_url} ({str(e)})")
                continue
        return ""

    def _extract_rss_items(self, xml_text: str) -> List[Dict]:
        """RSS/Atom XML에서 기사 목록 추출"""
        items = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"RSS XML 파싱 실패: {str(e)}")
            return items

        # RSS 2.0 형태
        channel = root.find('channel')
        if channel is not None:
            for item in channel.findall('item'):
                title = item.findtext('title', '').strip()
                link = item.findtext('link', '').strip()
                description = item.findtext('description', '').strip()
                pub_date = item.findtext('pubDate', '').strip()

                if not title or not link:
                    continue

                items.append({
                    'title': unescape(title),
                    'link': link,
                    'description': description,
                    'pub_date': pub_date
                })
            return items

        # Atom 형태
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('atom:entry', ns):
            title = entry.findtext('atom:title', default='', namespaces=ns).strip()
            link_elem = entry.find('atom:link', ns)
            link = link_elem.get('href', '').strip() if link_elem is not None else ''
            summary = entry.findtext('atom:summary', default='', namespaces=ns).strip()
            updated = entry.findtext('atom:updated', default='', namespaces=ns).strip()

            if not title or not link:
                continue

            items.append({
                'title': unescape(title),
                'link': link,
                'description': summary,
                'pub_date': updated
            })

        return items

    def crawl_rss_source(self, source: Dict) -> List[Dict]:
        """RSS 기반 크롤링"""
        articles = []
        rss_urls = source.get('rss_urls', [])
        if not rss_urls:
            return articles

        logger.info(f"{source['name']} RSS에서 뉴스 수집 중...")
        xml_text = self._fetch_rss_content(rss_urls)
        if not xml_text:
            logger.error(f"{source['name']} RSS 수집 실패: 유효한 RSS 응답 없음")
            return articles

        items = self._extract_rss_items(xml_text)
        for item in items[:10]:
            title = item['title']
            link = item['link']

            if not self.is_relevant_article(title, item.get('description', '')):
                continue

            description = item.get('description', '')
            content_text = ''
            if description:
                content_text = BeautifulSoup(description, 'html.parser').get_text(" ", strip=True)

            if not content_text:
                content_text = self.extract_article_content(link)

            if not content_text:
                content_text = title

            articles.append({
                'title': title,
                'content': content_text,
                'url': link,
                'source': source['name'],
                'published_date': self.parse_date(item.get('pub_date', ''))
            })

        logger.info(f"{source['name']} RSS에서 {len(articles)}개 기사 수집 완료")
        return articles

    def crawl_list_source(self, source: Dict) -> List[Dict]:
        """목록 페이지 기반 크롤링"""
        articles = []
        list_urls = source.get('list_urls', [])
        if not list_urls:
            return articles

        link_pattern = source.get('link_pattern')
        link_regex = source.get('link_regex')
        seen_urls = set()

        logger.info(f"{source['name']} 목록 페이지에서 뉴스 수집 중...")

        for list_url in list_urls:
            try:
                response = self.session.get(list_url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                for anchor in soup.select('a[href]'):
                    href = anchor.get('href', '').strip()
                    if not href:
                        continue

                    if href.startswith('/'):
                        href = urljoin(list_url, href)

                    if link_pattern and link_pattern not in href:
                        continue

                    if link_regex and not re.search(link_regex, href):
                        continue

                    if href in seen_urls:
                        continue

                    title = anchor.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue

                    if not self.is_relevant_article(title):
                        continue

                    seen_urls.add(href)

                    content = self.extract_article_content(href)
                    if not content:
                        content = title

                    articles.append({
                        'title': title,
                        'content': content,
                        'url': href,
                        'source': source['name'],
                        'published_date': datetime.now()
                    })

                    if len(articles) >= self.max_per_source:
                        break

                if len(articles) >= self.max_per_source:
                    break

                time.sleep(random.uniform(1, 2))

            except Exception as e:
                logger.error(f"{source['name']} 목록 크롤링 실패: {str(e)}")
                continue

        logger.info(f"{source['name']} 목록에서 {len(articles)}개 기사 수집 완료")
        return articles

    def crawl_source(self, source: Dict) -> List[Dict]:
        """특정 소스에서 뉴스 크롤링"""
        if source.get('list_urls'):
            return self.crawl_list_source(source)

        if source.get('rss_urls'):
            return self.crawl_rss_source(source)

        articles = []
        try:
            logger.info(f"{source['name']}에서 뉴스 수집 중...")
            
            response = self.session.get(source['url'], timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            article_elements = soup.select(source['selector']['articles'])
            
            for element in article_elements[:self.max_per_source]:  # 최대 기사 수 제한
                try:
                    # 제목 추출
                    title_elem = element.select_one(source['selector']['title'])
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    
                    # 링크 추출
                    link_elem = element.select_one(source['selector']['link'])
                    if not link_elem:
                        continue
                    
                    link = link_elem.get('href', '')
                    if link.startswith('/'):
                        link = urljoin(source['url'], link)
                    
                    # 반도체 관련성 체크
                    if not self.is_relevant_article(title):
                        continue
                    
                    # 기사 내용 추출
                    content = self.extract_article_content(link)
                    if not content:
                        content = title  # 내용을 가져올 수 없으면 제목만 사용
                    
                    article_data = {
                        'title': title,
                        'content': content,
                        'url': link,
                        'source': source['name'],
                        'published_date': datetime.now(),  # 실제로는 각 사이트별로 날짜 파싱 필요
                    }
                    
                    articles.append(article_data)
                    logger.debug(f"수집된 기사: {title[:50]}...")
                    
                    # 요청 간 지연
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.error(f"기사 파싱 오류: {str(e)}")
                    continue
            
            logger.info(f"{source['name']}에서 {len(articles)}개 기사 수집 완료")
            
        except Exception as e:
            logger.error(f"{source['name']} 크롤링 실패: {str(e)}")
        
        return articles

    def crawl_semiconductor_news(self) -> List[Dict]:
        """모든 소스에서 반도체 뉴스 크롤링"""
        logger.info("반도체 뉴스 크롤링 시작...")
        all_articles = []
        
        for source in self.news_sources:
            try:
                articles = self.crawl_source(source)
                all_articles.extend(articles)
                time.sleep(2)  # 소스 간 지연
            except Exception as e:
                logger.error(f"소스 {source['name']} 크롤링 실패: {str(e)}")
                continue
        
        # 중복 제거 (URL 기준)
        unique_articles = []
        seen_urls = set()
        
        for article in all_articles:
            if article['url'] not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(article['url'])
        
        logger.info(f"총 {len(unique_articles)}개의 고유 기사 수집 완료")
        return unique_articles

    def get_sample_news(self) -> List[Dict]:
        """테스트용 샘플 뉴스 데이터"""
        return [
            {
                'title': 'TSMC 3nm 공정 기술 발전으로 AI 칩 성능 향상',
                'content': 'TSMC가 최신 3nm 공정 기술을 통해 AI 칩의 성능을 크게 향상시켰다고 발표했습니다. 이는 전력 효율성을 30% 개선하고 성능을 15% 향상시키는 결과를 보여줍니다.',
                'url': 'https://example.com/tsmc-3nm-ai-chip',
                'source': 'TechNews',
                'published_date': datetime.now() - timedelta(hours=2)
            },
            {
                'title': '삼성전자, 차세대 DRAM 개발 성공',
                'content': '삼성전자가 차세대 DDR5 DRAM 개발에 성공했다고 발표했습니다. 기존 대비 50% 빠른 속도와 낮은 전력 소비를 실현했습니다.',
                'url': 'https://example.com/samsung-dram-development',
                'source': 'ElectronicsDaily',
                'published_date': datetime.now() - timedelta(hours=5)
            },
            {
                'title': 'NVIDIA, 새로운 AI 가속기 H200 발표',
                'content': 'NVIDIA가 최신 AI 가속기 H200을 발표했습니다. 기존 H100 대비 2.5배 향상된 메모리 성능을 제공합니다.',
                'url': 'https://example.com/nvidia-h200-announcement',
                'source': 'AI Weekly',
                'published_date': datetime.now() - timedelta(hours=8)
            }
        ]

if __name__ == "__main__":
    # 테스트 실행
    crawler = NewsCrawler()
    articles = crawler.get_sample_news()  # 실제로는 crawl_semiconductor_news() 사용
    for article in articles:
        print(f"제목: {article['title']}")
        print(f"소스: {article['source']}")
        print(f"URL: {article['url']}")
        print("---")