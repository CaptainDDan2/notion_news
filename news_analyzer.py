"""
뉴스 분석 및 요약 모듈
AI를 활용한 기사 요약과 우선순위 계산
"""

import os
import re
import logging
from typing import Dict, List
from datetime import datetime, timedelta
import openai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class NewsAnalyzer:
    def __init__(self):
        """분석기 초기화"""
        # OpenAI API 키 설정
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # 중요도 평가 키워드
        self.high_priority_keywords = [
            'breakthrough', 'revolutionary', 'first time', '최초', '혁신',
            'merger', 'acquisition', '인수', '합병', 'partnership', '파트너십',
            'IPO', '상장', 'earnings', '실적', 'patent', '특허',
            'TSMC', 'Samsung', 'Intel', 'NVIDIA', 'AMD', 'Qualcomm',
            'Apple', 'Google', '삼성', '하이닉스'
        ]
        
        self.medium_priority_keywords = [
            'development', '개발', 'launch', '출시', 'announcement', '발표',
            'upgrade', '업그레이드', 'expansion', '확장', 'investment', '투자'
        ]
        
        # 반도체 기술 관련 키워드 (가중치 적용) - 반도체 공정, 소자, TSMC, 삼성, 하이닉스 최우선
        self.tech_keywords = {
            # 최상위 핵심 반도체 기업 및 공정 (최우선)
            'TSMC': 5.0, 'tsmc': 5.0,
            '삼성': 5.0, 'Samsung': 5.0, 'samsung': 4.8,
            '하이닉스': 5.0, 'SK Hynix': 5.0, 'Hynix': 4.8,
            
            # 최상위 반도체 공정 및 소자
            '반도체': 5.0, 'semiconductor': 5.0,
            '공정': 4.5, 'process': 4.3, 'manufacturing': 4.3,
            '소자': 4.8, 'device': 4.5, 'chip': 4.2,
            
            # 고급 공정 노드 (2nm, 3nm 최우선)
            '2nm': 5.0, '1nm': 5.0,
            '3nm': 4.8, '5nm': 4.2, '7nm': 3.8,
            'GAA': 4.2, 'FinFET': 3.8,
            
            # 메모리 기술
            'HBM': 4.5, 'HBM4': 5.0, 'HBM3': 4.5,
            '메모리': 4.0, 'memory': 4.0,
            'DRAM': 4.0, 'NAND': 4.0, 'Flash': 3.8,
            
            # 파운드리
            '파운드리': 4.5, 'foundry': 4.5,
            
            # AI 및 고급 기술
            'AI': 3.8, '인공지능': 3.8, '머신러닝': 3.2, 'machine learning': 3.2,
            'quantum': 3.8, '양자': 3.8, 'neuromorphic': 3.5,
            'edge computing': 3.0, '엣지 컴퓨팅': 3.0,
            'autonomous': 3.2, '자율주행': 3.2, 'IoT': 2.8, 'blockchain': 2.5
        }

    def _is_english_text(self, text: str) -> bool:
        """텍스트가 영어인지 감지 (한글 비율이 낮으면 영어)"""
        if not text:
            return False
        korean_char_count = sum(1 for c in text if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3)
        total_chars = len(text)
        korean_ratio = korean_char_count / total_chars if total_chars > 0 else 0
        return korean_ratio < 0.2  # 한글이 20% 미만이면 영어

    def _translate_text(self, text: str, is_title: bool = False) -> str:
        """텍스트를 한글로 번역"""
        if not self._is_english_text(text):
            return text
            
        try:
            if self.openai_api_key and len(text) > 10:
                max_tokens = 100 if is_title else 300
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional translator. Translate the given English text to natural Korean. Provide only the translation, nothing else."
                        },
                        {
                            "role": "user",
                            "content": text
                        }
                    ],
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                translated = response.choices[0].message.content.strip()
                return translated if translated else text
        except Exception as e:
            logger.warning(f"번역 실패: {str(e)}")
        
        return text

    def summarize_article(self, content: str, max_length: int = 400) -> str:
        """기사 상세 요약 생성 - 구체적이고 구조화된 요약"""
        try:
            if self.openai_api_key and len(content) > 100:
                return self._summarize_with_openai(content, max_length)
            else:
                return self._enhanced_simple_summarize(content, max_length)
        except Exception as e:
            logger.error(f"요약 생성 중 오류: {str(e)}")
            return self._enhanced_simple_summarize(content, max_length)

    def _summarize_with_openai(self, content: str, max_length: int) -> str:
        """OpenAI API를 사용한 구체적인 요약"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 반도체 산업 전문가이자 취업 컨설턴트입니다. 취업 준비생들이 이력서, 면접, 에세이에서 활용할 수 있도록 다음 구조로 실용적인 한국어 요약을 제공해주세요:

💼 **산업 동향 & 기술 이해**
이 뉴스가 반도체 산업에 미치는 영향과 핵심 기술을 3-4문장으로 설명해주세요. 취업 준비생이 "최신 기술 트렌드를 이해하고 있다"고 어필할 수 있는 내용으로 구성해주세요.

🏭 **주요 기업 분석 & 취업 시장**
관련 기업들의 사업 전략과 시장 포지션을 설명하고, 해당 기업들의 채용 동향이나 필요 역량과 연결해주세요. 어떤 직무에 도움이 될지도 언급해주세요.

📈 **구체적 성과 지표**
면접에서 언급할 수 있는 핵심 수치들(성능 개선률, 투자 규모, 시장 규모 등)을 정리하고, 이 수치들이 업계에서 갖는 의미를 설명해주세요.

🎯 **커리어 연관성**
이 기술/산업 변화가 향후 5-10년간 어떤 새로운 직업이나 역량 수요를 만들어낼지 분석해주세요. 취업 준비생이 어떤 방향으로 준비하면 좋을지 제시해주세요.

💡 **면접 활용 포인트**
이 내용을 면접에서 어떻게 활용할 수 있는지 구체적으로 제시해주세요. "업계 동향에 대한 이해도"나 "미래 비전"을 보여줄 수 있는 답변 소재로 구성해주세요.

각 섹션을 명확히 구분하고, 취업 준비생 관점에서 실용적으로 작성해주세요."""
                    },
                    {
                        "role": "user", 
                        "content": f"다음 반도체 기사를 위 형식으로 취업 준비생 관점에서 분석하여 실용적으로 요약해주세요 (총 {max_length*3}자 이내, 면접/이력서 활용 가능하도록):\n\n{content[:4000]}"
                    }
                ],
                max_tokens=int(max_length*2),
                temperature=0.2
            )
            summary = response.choices[0].message.content.strip()
            
            # 너무 길면 자르기
            if len(summary) > max_length * 3:
                summary = summary[:max_length * 3] + "..."
            
            return summary
        except Exception as e:
            logger.error(f"OpenAI API 요약 실패: {str(e)}")
            return self._enhanced_simple_summarize(content, max_length)

    def _enhanced_simple_summarize(self, content: str, max_length: int) -> str:
        """향상된 규칙 기반 요약 (OpenAI 실패시 대체)"""
        # 문장 분리
        sentences = re.split(r'[.!?\n]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return content[:max_length]
        
        # 중요 정보 추출
        companies = self._extract_companies(content)
        numbers = self._extract_numbers(content)
        tech_keywords = self._extract_tech_keywords(content)
        
        # 구조화된 요약 생성
        summary_parts = []
        
        # 중요 문장 추출
        important_sentences = []
        for sentence in sentences[:8]:
            score = self._sentence_importance_score(sentence)
            important_sentences.append((score, sentence))
        
        important_sentences.sort(reverse=True)
        
        # 📄 핵심 내용 - 더 구체적이고 상세하게
        if important_sentences:
            core_sentences = [s[1] for s in important_sentences[:2]]
            core_content = ". ".join(core_sentences)[:200]
            summary_parts.append(f"💼 **산업 동향 & 기술 이해**\n{core_content}. 이는 반도체 산업의 최신 기술 트렌드를 보여주는 중요한 발전입니다.\n\n")
        
        # 🏢 주요 기업/기술 - 구체적인 설명과 함께
        if companies or tech_keywords:
            entities = []
            if companies:
                entities.extend(companies[:2])
            if tech_keywords:
                entities.extend(tech_keywords[:2])
            
            entity_desc = ", ".join(entities[:4])
            if entity_desc:
                summary_parts.append(f"🏭 **주요 기업 분석 & 취업 시장**\n{entity_desc}와 관련된 기업들이 주도하는 기술 혁신으로, 관련 분야 취업 시장에 새로운 기회를 제공할 것으로 예상됩니다.\n\n")
        
        # � 구체적 성과 지표 - 수치의 의미까지 포함
        if numbers:
            number_descriptions = []
            for num in numbers[:3]:
                # 해당 수치를 포함한 문장 찾기
                for sentence in sentences:
                    if num in sentence:
                        # 수치 주변 맥락 추출
                        if '%' in num:
                            if any(keyword in sentence.lower() for keyword in ['전력', '효율', '소비', '절약', '소모']):
                                number_descriptions.append(f"전력 효율성 {num} 개선")
                            elif any(keyword in sentence.lower() for keyword in ['대역폭', '전송', '처리 속도', '빠른']):
                                number_descriptions.append(f"데이터 처리 속도 {num} 향상")
                            elif any(keyword in sentence.lower() for keyword in ['성능', '향상', '속도']):
                                number_descriptions.append(f"성능 {num} 향상")
                            elif any(keyword in sentence.lower() for keyword in ['용량', '메모리', '저장', '확장']):
                                number_descriptions.append(f"용량 {num} 확장")
                            elif any(keyword in sentence.lower() for keyword in ['시장', '점유율', '매출']):
                                number_descriptions.append(f"시장 점유율 {num} 증가")
                            else:
                                number_descriptions.append(f"{num} 성능 개선")
                        elif 'nm' in num.lower():
                            number_descriptions.append(f"{num} 미세 공정 기술")
                        elif any(unit in num.upper() for unit in ['GB', 'TB', 'MB']):
                            if any(keyword in sentence.lower() for keyword in ['메모리', '저장', '용량']):
                                number_descriptions.append(f"{num} 메모리 용량")
                            elif any(keyword in sentence.lower() for keyword in ['대역폭', '전송', '속도']):
                                number_descriptions.append(f"{num} 데이터 전송 속도")
                            else:
                                number_descriptions.append(f"{num} 용량 사양")
                        elif any(unit in num.upper() for unit in ['GHZ', 'MHZ']):
                            number_descriptions.append(f"{num} 동작 주파수")
                        else:
                            # 기타 숫자의 경우 문맥에서 키워드 추출
                            if any(keyword in sentence.lower() for keyword in ['년', '월', '분기', '양산', '출시', '예정']):
                                number_descriptions.append(f"{num} 출시/양산 일정")
                            elif any(keyword in sentence.lower() for keyword in ['억', '조', '달러', '원', '투자', '예산', '비용']):
                                number_descriptions.append(f"{num} 투자 규모")
                            elif any(keyword in sentence.lower() for keyword in ['칩', '코어', '트랜지스터']):
                                number_descriptions.append(f"{num} 하드웨어 사양")
                            else:
                                number_descriptions.append(f"{num} 핵심 수치")
                        break
            
            if number_descriptions:
                descriptions_text = ", ".join(number_descriptions)
                summary_parts.append(f"📈 **구체적 성과 지표**\n{descriptions_text} - 이러한 구체적 수치들은 면접에서 기술 트렌드와 시장 동향 이해도를 보여주는 중요한 데이터입니다.\n\n")
            else:
                # 폴백: 기존 방식
                number_desc = ", ".join(numbers[:3])
                summary_parts.append(f"📈 **구체적 성과 지표**\n{number_desc} 등 핵심 수치들이 발표되어 면접에서 활용 가능합니다.\n\n")
        
        # 🎯 커리어 연관성 - 구체적인 역량과 준비 방향 제시
        if len(important_sentences) > 2:
            insight_sentence = important_sentences[1][1] if len(important_sentences) > 1 else sentences[-1]
            
            # 기술 키워드에 따른 필요 역량 추천
            skill_recommendations = []
            if any(keyword in content.lower() for keyword in ['ai', '인공지능', 'machine learning']):
                skill_recommendations.append("AI/ML 관련 프로그래밍(Python, TensorFlow)")
            if any(keyword in content.lower() for keyword in ['반도체', 'chip', '칩']):
                skill_recommendations.append("반도체 설계 도구(Cadence, Synopsys) 경험")
            if any(keyword in content.lower() for keyword in ['클라우드', 'cloud', '데이터센터']):
                skill_recommendations.append("클라우드 플랫폼(AWS, Azure) 활용 능력")
                
            skills_text = ", ".join(skill_recommendations[:2]) if skill_recommendations else "관련 기술 스택"
            
            summary_parts.append(f"🎯 **커리어 연관성**\n{insight_sentence[:100]}. 이러한 변화로 {skills_text} 등의 역량을 갖춘 인재 수요가 증가할 것으로 예상됩니다. 관련 자격증 취득이나 프로젝트 경험을 쌓는 것이 유리합니다.\n\n")
        
        # 💡 면접 활용 포인트 - 구체적인 예시 답변 제공
        if len(sentences) > 3:
            key_point = sentences[0][:80] if sentences else "최신 기술 동향"
            
            # 기업명 추출해서 구체적인 예시 만들기
            company_for_example = companies[0] if companies else "해당 기업"
            
            example_answer = f"최근 {company_for_example}의 발표를 보면 {key_point.lower()}는 매우 중요한 의미를 가집니다"
            
            summary_parts.append(f"💡 **면접 활용 포인트**\n\"{example_answer}. 이러한 기술 발전이 업계 전반에 미치는 영향을 고려할 때, 저는...\"와 같은 방식으로 최신 동향에 대한 이해도를 어필할 수 있습니다. 기술의 파급효과와 본인의 관련 경험을 연결하여 답변하세요.\n")
        
        final_summary = "\n".join(summary_parts)
        
        # 길이 제한
        if len(final_summary) > max_length * 2.5:
            final_summary = final_summary[:int(max_length * 2.5)] + "..."
        
        return final_summary if final_summary else sentences[0][:max_length]
    
    def _extract_companies(self, text: str) -> List[str]:
        """기업명 추출"""
        companies = []
        company_patterns = [
            r'삼성전자|Samsung', r'SK하이닉스|SK Hynix', r'TSMC|대만반도체',
            r'인텔|Intel', r'AMD', r'NVIDIA|엔비디아', r'퀄컴|Qualcomm',
            r'애플|Apple', r'마이크론|Micron', r'브로드컴|Broadcom',
            r'글로벌파운드리|GlobalFoundries', r'ARM'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                companies.extend(matches[:1])  # 중복 방지
        
        return companies[:3]
    
    def _extract_numbers(self, text: str) -> List[str]:
        """중요한 수치 추출"""
        numbers = []
        number_patterns = [
            r'\d+%|\d+퍼센트',  # 퍼센트
            r'\$\d+[MB]?|\d+억 달러|\d+조 달러',  # 달러 금액
            r'\d+nm|\d+나노',  # 공정 기술
            r'\d+GB|\d+TB|\d+Gbps',  # 용량/속도
            r'\d+년|\d+월',  # 시간
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches[:2])
        
        return numbers[:3]
    
    def _extract_tech_keywords(self, text: str) -> List[str]:
        """기술 키워드 추출"""
        found_keywords = []
        tech_terms = [
            'AI', '인공지능', '머신러닝', '딥러닝', '신경망',
            '양자컴퓨팅', '양자', '엣지컴퓨팅', '클라우드',
            '자율주행', 'IoT', '5G', '6G', '블록체인',
            'HBM', 'DDR5', 'GDDR6', 'SSD', 'CPU', 'GPU'
        ]
        
        text_lower = text.lower()
        for term in tech_terms:
            if term.lower() in text_lower and term not in found_keywords:
                found_keywords.append(term)
        
        return found_keywords[:3]

    def _sentence_importance_score(self, sentence: str) -> float:
        """문장의 중요도 점수 계산"""
        score = 0.0
        sentence_lower = sentence.lower()
        
        # 키워드 기반 점수
        for keyword in self.high_priority_keywords:
            if keyword.lower() in sentence_lower:
                score += 2.0
        
        for keyword in self.medium_priority_keywords:
            if keyword.lower() in sentence_lower:
                score += 1.0
        
        # 기술 키워드 가중치 적용
        for keyword, weight in self.tech_keywords.items():
            if keyword.lower() in sentence_lower:
                score += weight
        
        # 숫자나 퍼센트가 있으면 중요도 증가
        if re.search(r'\d+%|\$\d+|\d+억|\d+조', sentence):
            score += 1.5
        
        return score

    def calculate_priority(self, article_data: Dict) -> float:
        """기사의 우선순위 점수 계산 (0-10점)"""
        try:
            title = article_data.get('title', '')
            content = article_data.get('content', '')
            source = article_data.get('source', '')
            published_date = article_data.get('published_date', datetime.now())
            
            priority_score = 0.0
            
            # 1. 제목 기반 점수 (최대 3점)
            title_score = self._calculate_text_score(title) * 1.5
            priority_score += min(title_score, 3.0)
            
            # 2. 내용 기반 점수 (최대 3점) 
            content_score = self._calculate_text_score(content) * 0.8
            priority_score += min(content_score, 3.0)
            
            # 3. 소스 신뢰도 점수 (최대 3.5점) - 기업 뉴스룸 보너스 포함
            source_score = self._calculate_source_score(source)
            priority_score += source_score
            
            # 4. 시간 기반 점수 (최대 2점)
            time_score = self._calculate_time_score(published_date)
            priority_score += time_score
            
            # 5. 기업 뉴스룸 기술 내용 추가 보너스 (0-1.5점)
            is_newsroom = any(keyword in source for keyword in ['Newsroom', 'newsroom', 'Press Release', 'press release'])
            if is_newsroom:
                priority_score += 0.5  # 뉴스룸 기본 보너스
                
                # 뉴스룸의 반도체 기술 내용 검사
                combined_text = (title + ' ' + content).lower()
                tech_keywords_found = 0
                for keyword in self.tech_keywords.keys():
                    if keyword.lower() in combined_text:
                        tech_keywords_found += 1
                
                # 반도체 기술 키워드가 많을수록 추가 보너스 (최대 +1.0)
                if tech_keywords_found > 0:
                    tech_bonus = min(tech_keywords_found * 0.25, 1.0)
                    priority_score += tech_bonus
                    logger.debug(f"기술 키워드 {tech_keywords_found}개 발견 -> +{tech_bonus:.2f} 보너스")
            
            # 최종 점수 정규화 (0-10)
            final_score = min(priority_score, 10.0)
            
            logger.debug(f"우선순위 계산: {title[:30]}... -> 점수: {final_score:.2f}")
            return final_score
            
        except Exception as e:
            logger.error(f"우선순위 계산 중 오류: {str(e)}")
            return 5.0  # 기본값

    def _calculate_text_score(self, text: str) -> float:
        """텍스트의 중요도 점수 계산"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        # 고우선순위 키워드
        for keyword in self.high_priority_keywords:
            if keyword.lower() in text_lower:
                score += 2.0
        
        # 중간우선순위 키워드
        for keyword in self.medium_priority_keywords:
            if keyword.lower() in text_lower:
                score += 1.0
        
        # 기술 키워드 가중치
        for keyword, weight in self.tech_keywords.items():
            if keyword.lower() in text_lower:
                score += weight
        
        # 특수 패턴 보너스
        patterns = [
            (r'\d+%|\d+퍼센트', 1.0),  # 퍼센트
            (r'\$\d+|\d+달러|\d+억|\d+조', 1.5),  # 금액
            (r'first|최초|first time|처음', 2.0),  # 최초/처음
            (r'record|기록|최고|highest|lowest', 1.5),  # 기록
        ]
        
        for pattern, bonus in patterns:
            if re.search(pattern, text_lower):
                score += bonus
        
        return score

    def _calculate_source_score(self, source: str) -> float:
        """뉴스 소스의 신뢰도 점수 + 기업 뉴스룸 보너스"""
        source_scores = {
            'Reuters': 2.0, '로이터': 2.0,
            'Bloomberg': 2.0, '블룸버그': 2.0, 
            'Wall Street Journal': 1.8, 'WSJ': 1.8,
            'Financial Times': 1.8, 'FT': 1.8,
            'TechCrunch': 1.5, '테크크런치': 1.5,
            'The Verge': 1.3, 'Ars Technica': 1.5,
            'EE Times': 1.7, 'Semiconductor Engineering': 1.7,
            '전자신문': 1.6, '한국경제': 1.4, '매일경제': 1.4,
            'AI Weekly': 1.2, 'TechNews': 1.0
        }
        
        score = 1.0  # 기본 점수
        
        for source_name, source_score in source_scores.items():
            if source_name.lower() in source.lower():
                score = source_score
                break
        
        # 기업 공식 뉴스룸은 우선순위 +1.5 (매우 신뢰도 높음)
        if any(keyword in source for keyword in ['Newsroom', 'newsroom', 'Press Release', 'press release', 'Official', 'official']):
            score += 1.5
        
        return min(score, 3.5)  # 최대 3.5

    def _calculate_time_score(self, published_date: datetime) -> float:
        """시간 기반 점수 (최신 기사일수록 높은 점수)"""
        if not published_date:
            return 1.0
        
        now = datetime.now()
        if published_date.tzinfo:
            now = now.replace(tzinfo=published_date.tzinfo)
        
        time_diff = now - published_date
        hours_ago = time_diff.total_seconds() / 3600
        
        # 시간에 따른 점수 감소
        if hours_ago <= 1:
            return 2.0      # 1시간 이내
        elif hours_ago <= 6:
            return 1.8      # 6시간 이내
        elif hours_ago <= 24:
            return 1.5      # 24시간 이내
        elif hours_ago <= 72:
            return 1.0      # 3일 이내
        elif hours_ago <= 168:
            return 0.5      # 1주 이내
        else:
            return 0.2      # 1주 이상

    def analyze_trends(self, articles: List[Dict]) -> Dict:
        """기사들의 트렌드 분석"""
        if not articles:
            return {}
        
        # 키워드 빈도 분석
        keyword_counts = {}
        for article in articles:
            text = (article.get('title', '') + ' ' + article.get('content', '')).lower()
            for keyword in self.tech_keywords.keys():
                if keyword.lower() in text:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # 상위 트렌드 키워드
        top_trends = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 소스별 기사 수
        source_counts = {}
        for article in articles:
            source = article.get('source', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            'top_trends': top_trends,
            'source_distribution': source_counts,
            'total_articles': len(articles),
            'avg_priority': sum(article.get('priority_score', 0) for article in articles) / len(articles)
        }

if __name__ == "__main__":
    # 테스트 실행
    analyzer = NewsAnalyzer()
    
    # 샘플 기사 테스트
    sample_article = {
        'title': 'TSMC 3nm 공정 기술로 AI 칩 성능 30% 향상',
        'content': 'TSMC가 최신 3nm 공정 기술을 통해 AI 칩의 성능을 30% 향상시켰다고 발표했습니다. 이번 혁신적인 기술은 전력 효율성도 크게 개선했습니다.',
        'source': 'TechNews',
        'published_date': datetime.now()
    }
    
    summary = analyzer.summarize_article(sample_article['content'])
    priority = analyzer.calculate_priority(sample_article)
    
    print(f"요약: {summary}")
    print(f"우선순위 점수: {priority:.2f}/10.0")