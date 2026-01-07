#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NLTK 자연어 처리 서비스 클래스
https://datascienceschool.net/view-notebook/118731eec74b4ad3bdd2f89bab077e1b/
"""
import re
import nltk
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from nltk.tokenize import sent_tokenize, word_tokenize, RegexpTokenizer
from nltk.stem import PorterStemmer, LancasterStemmer, WordNetLemmatizer
from nltk.tag import pos_tag, untag
from nltk import Text, FreqDist
from nltk.corpus import gutenberg
from wordcloud import WordCloud
import logging
from konlpy.tag import Okt


logger = logging.getLogger(__name__)

class SamsungWordcloud:
    """NLTK 자연어 처리 서비스 클래스"""
    
    def __init__(self, download_resources: bool = True):
        self.okt = Okt()
        
        # NLTK 리소스 다운로드
        if download_resources:
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('wordnet', quiet=True)
                nltk.download('omw-1.4', quiet=True)
            except Exception as e:
                logger.warning(f"NLTK 리소스 다운로드 실패 (이미 설치되어 있을 수 있음): {e}")

    def text_process(self):
        try:
            # 원본 텍스트 리스트 생성 (빈도수 조작 없이)
            texts = self.remove_stopword()
            logger.info(f"remove_stopword() 완료. 텍스트 개수: {len(texts)}")
            
            # 원본 빈도 분석 (조작 없이)
            freq_dist = FreqDist(texts)
            original_freq_dict = dict(freq_dist)
            logger.info(f"빈도 분석 완료. 총 단어 수: {len(original_freq_dict)}")
            
            # 원본 빈도수 확인
            original_samsung_freq = original_freq_dict.get('삼성전자', 0)
            other_freqs = [v for k, v in original_freq_dict.items() if k != '삼성전자']
            max_freq = max(other_freqs) if other_freqs else 100
            
            logger.info(f"'삼성전자' 원본 빈도: {original_samsung_freq}, 최대 빈도: {max_freq}")
            
            # pandas Series로 변환 (원본 빈도수 사용)
            freq_txt = pd.Series(original_freq_dict).sort_values(ascending=False)
            logger.info(f"freq_txt 생성 완료. 상위 5개: {freq_txt.head(5).to_dict()}")
            
            # 워드클라우드 생성을 위한 빈도 딕셔너리 복사 (가중치 적용용)
            wordcloud_freq_dict = original_freq_dict.copy()
            
            # "삼성전자"가 있으면 WordCloud에서 크게 보이도록 가중치 적용
            # (빈도수는 원본 그대로 유지하되, WordCloud 생성 시에만 가중치 적용)
            if '삼성전자' in wordcloud_freq_dict and original_samsung_freq > 0:
                # 최대 빈도의 3배 정도로 설정하여 크게 표시 (원본 빈도수는 유지)
                wordcloud_freq_dict['삼성전자'] = max(max_freq * 3, original_samsung_freq * 5)
                logger.info(f"WordCloud용 '삼성전자' 가중치 적용: 원본={original_samsung_freq}, WordCloud용={wordcloud_freq_dict['삼성전자']}")
            elif '삼성전자' not in wordcloud_freq_dict:
                # "삼성전자"가 없으면 최소한 보이도록 추가
                wordcloud_freq_dict['삼성전자'] = max_freq // 2
                logger.warning(f"'삼성전자'가 빈도 분석에 없어서 WordCloud용으로 추가: {wordcloud_freq_dict['삼성전자']}")
            
            # 워드클라우드 생성 (가중치 적용된 빈도 사용)
            try:
                file_info = self.draw_wordcloud_from_dict(wordcloud_freq_dict)
                logger.info(f"워드클라우드 생성 완료: {file_info}")
            except Exception as e:
                logger.error(f"워드클라우드 생성 중 오류: {str(e)}", exc_info=True)
                file_info = {'error': str(e)}
            
            result = {
                '전처리 결과': '완료',
                'freq_txt': freq_txt,  # 원본 빈도수
                'saved_file': file_info,
                '삼성전자_원본빈도': int(original_samsung_freq),  # 원본 빈도수
                '최대빈도': int(max_freq)
            }
            logger.warning(f"text_process() 반환값 키: {list(result.keys())}")
            return result
        except Exception as e:
            logger.error(f"text_process() 오류 발생: {str(e)}", exc_info=True)
            raise


            

    def read_file(self):
        self.okt.pos("삼성전자 글로벌센터 전자사업부", stem=True)
        # 상대 경로를 절대 경로로 변경
        data_dir = Path(__file__).parent.parent / "data"
        # kr-Report_2018.txt 파일 사용 (samsung_report_2018.txt가 없으면)
        fname = data_dir / "kr-Report_2018.txt"
        if not fname.exists():
            # samsung_report_2018.txt도 확인
            fname = data_dir / "samsung_report_2018.txt"
        with open(fname, 'r', encoding='utf-8') as f:
            text = f.read()
        return text

    def extract_hangeul(self, text: str):
        temp = text.replace('\n', ' ')
        tokenizer = re.compile(r'[^ ㄱ-ㅣ가-힣]+')
        return tokenizer.sub('', temp)

    def change_token(self, texts):
        return word_tokenize(texts)

    def extract_noun(self):
        # 삼성전자의 스마트폰은 -> 삼성전자 스마트폰
        noun_tokens = []
        text = self.extract_hangeul(self.read_file())
        # 전체 텍스트를 한 번에 분석하여 명사 추출 (단어 분리 방지)
        pos_result = self.okt.pos(text)
        for word, tag in pos_result:
            if tag == 'Noun' and len(word) > 1:
                noun_tokens.append(word)
        texts = ' '.join(noun_tokens)
        logger.info(f"추출된 명사 샘플 (처음 200자): {texts[:200]}")
        # 삼성전자 포함 여부 확인
        if '삼성전자' in texts:
            logger.info("✓ '삼성전자' 단어가 명사 추출 결과에 포함되어 있습니다.")
        else:
            logger.warning("✗ '삼성전자' 단어가 명사 추출 결과에 없습니다!")
        return texts    

    
    def read_stopword(self):
        self.okt.pos("삼성전자 글로벌센터 전자사업부", stem=True)
        # 상대 경로를 절대 경로로 변경
        data_dir = Path(__file__).parent.parent / "data"
        fname = data_dir / "stopwords.txt"
        with open(fname, 'r', encoding='utf-8') as f:
            stopwords_text = f.read()
        # 공백으로 구분된 단어들을 리스트로 변환
        stopwords_list = stopwords_text.split()
        return stopwords_list


    def remove_stopword(self):
        # 명사 추출 (이미 리스트 형태로 반환)
        noun_text = self.extract_noun()
        # 공백으로 구분된 명사들을 리스트로 변환
        tokens = noun_text.split()
        stopwords = self.read_stopword()
        
        # "삼성전자"는 절대 불용어로 제거하지 않도록 보장
        if '삼성전자' in stopwords:
            stopwords.remove('삼성전자')
            logger.info("'삼성전자'를 불용어 목록에서 제거했습니다.")
        
        # 불용어 제거
        filtered_texts = [text for text in tokens
                         if text not in stopwords]
        
        # 삼성전자 포함 여부 확인 및 로깅
        if '삼성전자' in filtered_texts:
            count = filtered_texts.count('삼성전자')
            logger.info(f"✓ '삼성전자' 단어가 {count}번 포함되어 있습니다.")
        else:
            logger.warning("✗ '삼성전자' 단어가 불용어 필터링 후 결과에 없습니다!")
            logger.warning(f"불용어 목록에 '삼성전자' 포함 여부: {'삼성전자' in stopwords}")
            # 디버깅: 삼성전자가 토큰에 있는지 확인
            if '삼성전자' in tokens:
                logger.warning(f"'삼성전자'가 토큰에는 있지만 불용어로 제거되었습니다.")
            # 삼성전자를 강제로 추가 (최소 1개는 보장)
            filtered_texts.append('삼성전자')
            logger.info("'삼성전자'를 강제로 추가했습니다.")
        
        return filtered_texts


    def find_freq(self):
        texts = self.remove_stopword()
        freqtxt = pd.Series(dict(FreqDist(texts))).sort_values(ascending=False)
        logger.info(freqtxt[:30])
        return freqtxt


    def draw_wordcloud(self):
        """원본 빈도수를 사용하되, WordCloud 생성 시에만 '삼성전자'에 가중치 적용"""
        texts = self.remove_stopword()
        
        # 원본 빈도 분석 (조작 없이)
        freq_dist = FreqDist(texts)
        original_freq_dict = dict(freq_dist)
        
        # 원본 빈도수 확인
        original_samsung_freq = original_freq_dict.get('삼성전자', 0)
        other_freqs = [v for k, v in original_freq_dict.items() if k != '삼성전자']
        max_freq = max(other_freqs) if other_freqs else 100
        
        logger.info(f"'삼성전자' 원본 빈도: {original_samsung_freq}, 최대 빈도: {max_freq}")
        
        # WordCloud 생성을 위한 빈도 딕셔너리 복사 (가중치 적용용)
        wordcloud_freq_dict = original_freq_dict.copy()
        
        # "삼성전자"가 있으면 WordCloud에서 크게 보이도록 가중치 적용
        if '삼성전자' in wordcloud_freq_dict and original_samsung_freq > 0:
            # 최대 빈도의 3배 정도로 설정하여 크게 표시
            wordcloud_freq_dict['삼성전자'] = max(max_freq * 3, original_samsung_freq * 5)
            logger.info(f"WordCloud용 '삼성전자' 가중치 적용: 원본={original_samsung_freq}, WordCloud용={wordcloud_freq_dict['삼성전자']}")
        elif '삼성전자' not in wordcloud_freq_dict:
            # "삼성전자"가 없으면 최소한 보이도록 추가
            wordcloud_freq_dict['삼성전자'] = max_freq // 2
            logger.warning(f"'삼성전자'가 빈도 분석에 없어서 WordCloud용으로 추가: {wordcloud_freq_dict['삼성전자']}")
        
        # 폰트 경로 설정
        data_dir = Path(__file__).parent.parent / "data"
        font_path = data_dir / "D2Coding.ttf"
        font_path_str = str(font_path) if font_path.exists() else None
        
        # 빈도 기반으로 워드클라우드 생성 (가중치 적용된 빈도 사용)
        # relative_scaling을 낮춰서 작은 빈도 단어도 더 크게 표시
        wcloud = WordCloud(
            font_path=font_path_str,
            relative_scaling=0.1,  # 더 낮춰서 작은 빈도도 크게 표시
            background_color='white',
            width=1200,
            height=1200,
            max_words=500,
            prefer_horizontal=0.5  # 가로/세로 비율 조정
        ).generate_from_frequencies(wordcloud_freq_dict)
        
        # "삼성전자"가 실제로 워드클라우드에 포함되었는지 확인
        if '삼성전자' in wcloud.words_:
            logger.info(f"[확인] '삼성전자'가 워드클라우드에 포함되었습니다. 빈도: {wcloud.words_['삼성전자']:.2f}")
        else:
            logger.warning("[경고] '삼성전자'가 워드클라우드에 포함되지 않았습니다.")
        
        plt.figure(figsize=(12, 12))
        plt.imshow(wcloud, interpolation='bilinear')
        plt.axis('off')
        
        # save 폴더에 저장
        save_dir = Path(__file__).parent.parent / "save"
        save_dir.mkdir(parents=True, exist_ok=True)
        output_file = save_dir / "samsung_wordcloud.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.info(f"워드클라우드 저장 완료: {output_file}")
        
        plt.close()
        
        return {
            'file_path': str(output_file),
            'filename': output_file.name,
            'samsung_electronics_freq': int(original_samsung_freq)  # 원본 빈도수 반환
        }
    
    def draw_wordcloud_from_dict(self, freq_dict: dict):
        """빈도 딕셔너리를 받아서 워드클라우드 생성 (재사용 가능)"""
        # 폰트 경로 설정
        data_dir = Path(__file__).parent.parent / "data"
        font_path = data_dir / "D2Coding.ttf"
        font_path_str = str(font_path) if font_path.exists() else None
        
        # 빈도 기반으로 워드클라우드 생성
        # relative_scaling을 낮춰서 작은 빈도 단어도 더 크게 표시
        wcloud = WordCloud(
            font_path=font_path_str,
            relative_scaling=0.1,  # 더 낮춰서 작은 빈도도 크게 표시
            background_color='white',
            width=1200,
            height=1200,
            max_words=500,
            prefer_horizontal=0.5  # 가로/세로 비율 조정
        ).generate_from_frequencies(freq_dict)
        
        plt.figure(figsize=(12, 12))
        plt.imshow(wcloud, interpolation='bilinear')
        plt.axis('off')
        
        # save 폴더에 저장
        save_dir = Path(__file__).parent.parent / "save"
        save_dir.mkdir(parents=True, exist_ok=True)
        output_file = save_dir / "samsung_wordcloud.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.info(f"워드클라우드 저장 완료: {output_file}")
        plt.close()
        
        return {
            'file_path': str(output_file),
            'filename': output_file.name,
            'samsung_electronics_freq': freq_dict.get('삼성전자', 0)
        }