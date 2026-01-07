#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NLTK 자연어 처리 서비스 클래스
https://datascienceschool.net/view-notebook/118731eec74b4ad3bdd2f89bab077e1b/
"""
import nltk
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Optional
from nltk.tokenize import sent_tokenize, word_tokenize, RegexpTokenizer
from nltk.stem import PorterStemmer, LancasterStemmer, WordNetLemmatizer
from nltk.tag import pos_tag, untag
from nltk import Text, FreqDist
from nltk.corpus import gutenberg
from wordcloud import WordCloud


class NLTKService:
    """NLTK 자연어 처리 서비스 클래스"""
    
    def __init__(self, download_resources: bool = True):
        """
        초기화
        
        Args:
            download_resources: NLTK 리소스 다운로드 여부
        """
        if download_resources:
            try:
                nltk.download('book', quiet=True)
                nltk.download('punkt', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                nltk.download('averaged_perceptron_tagger_eng', quiet=True)
                nltk.download('wordnet', quiet=True)
            except Exception as e:
                print(f"Warning: NLTK resource download failed: {e}")
        
        self.porter_stemmer = PorterStemmer()
        self.lancaster_stemmer = LancasterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        self.regex_tokenizer = RegexpTokenizer(r"[\w]+")
    
    # *********
    # 말뭉치 관련 메서드
    # *********
    
    def get_corpus_fileids(self) -> List[str]:
        """
        Gutenberg 말뭉치의 파일 ID 목록 반환
        
        Returns:
            파일 ID 목록
        """
        return gutenberg.fileids()
    
    def load_corpus_text(self, fileid: str) -> str:
        """
        말뭉치에서 텍스트 로드
        
        Args:
            fileid: 파일 ID (예: "austen-emma.txt")
            
        Returns:
            원문 텍스트
        """
        return gutenberg.raw(fileid)
    
    def get_emma_text(self, length: int = 1302) -> str:
        """
        제인 오스틴의 엠마 텍스트 반환
        
        Args:
            length: 반환할 텍스트 길이
            
        Returns:
            엠마 텍스트 일부
        """
        emma_raw = self.load_corpus_text("austen-emma.txt")
        return emma_raw[:length]
    
    # ************
    # 토큰 생성 메서드
    # ************
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """
        문장 단위로 토큰화
        
        Args:
            text: 입력 텍스트
            
        Returns:
            문장 리스트
        """
        return sent_tokenize(text)
    
    def tokenize_words(self, text: str) -> List[str]:
        """
        단어 단위로 토큰화
        
        Args:
            text: 입력 텍스트
            
        Returns:
            단어 리스트
        """
        return word_tokenize(text)
    
    def tokenize_regex(self, text: str, pattern: str = r"[\w]+") -> List[str]:
        """
        정규식을 사용한 토큰화
        
        Args:
            text: 입력 텍스트
            pattern: 정규식 패턴 (기본값: "[\w]+")
            
        Returns:
            토큰 리스트
        """
        tokenizer = RegexpTokenizer(pattern)
        return tokenizer.tokenize(text)
    
    # ***************
    # 형태소 분석 메서드
    # ***************
    
    def stem_porter(self, words: List[str]) -> List[str]:
        """
        Porter Stemmer를 사용한 어간 추출
        
        Args:
            words: 단어 리스트
            
        Returns:
            어간 추출된 단어 리스트
        """
        return [self.porter_stemmer.stem(w) for w in words]
    
    def stem_lancaster(self, words: List[str]) -> List[str]:
        """
        Lancaster Stemmer를 사용한 어간 추출
        
        Args:
            words: 단어 리스트
            
        Returns:
            어간 추출된 단어 리스트
        """
        return [self.lancaster_stemmer.stem(w) for w in words]
    
    def lemmatize(self, words: List[str], pos: Optional[str] = None) -> List[str]:
        """
        원형 복원 (Lemmatization)
        
        Args:
            words: 단어 리스트
            pos: 품사 (예: "v", "n", "a", "r")
            
        Returns:
            원형 복원된 단어 리스트
        """
        if pos:
            return [self.lemmatizer.lemmatize(w, pos=pos) for w in words]
        return [self.lemmatizer.lemmatize(w) for w in words]
    
    # **********
    # POS tagging 메서드
    # **********
    
    def get_pos_tag_info(self, tag: str) -> str:
        """
        품사 태그 정보 조회
        
        Args:
            tag: 품사 태그 (예: "VB")
            
        Returns:
            품사 태그 설명
        """
        return nltk.help.upenn_tagset(tag)
    
    def tag_pos(self, sentence: str) -> List[Tuple[str, str]]:
        """
        품사 태깅
        
        Args:
            sentence: 입력 문장
            
        Returns:
            (단어, 품사) 튜플 리스트
        """
        tokens = word_tokenize(sentence)
        return pos_tag(tokens)
    
    def extract_nouns(self, sentence: str) -> List[str]:
        """
        명사만 추출
        
        Args:
            sentence: 입력 문장
            
        Returns:
            명사 리스트
        """
        tagged_list = self.tag_pos(sentence)
        return [t[0] for t in tagged_list if t[1] == "NN"]
    
    def untag(self, tagged_list: List[Tuple[str, str]]) -> List[str]:
        """
        태그 제거
        
        Args:
            tagged_list: (단어, 품사) 튜플 리스트
            
        Returns:
            단어 리스트
        """
        return untag(tagged_list)
    
    def create_pos_tokenizer(self, sentence: str) -> List[str]:
        """
        품사를 포함한 토큰 생성 (같은 철자, 다른 품사 구분)
        
        Args:
            sentence: 입력 문장
            
        Returns:
            "단어/품사" 형식의 토큰 리스트
        """
        tagged_list = self.tag_pos(sentence)
        return ["/".join(p) for p in tagged_list]
    
    # ***********
    # Text 클래스 관련 메서드
    # ***********
    
    def create_text_object(self, tokens: List[str], name: str = "Text") -> Text:
        """
        Text 객체 생성
        
        Args:
            tokens: 토큰 리스트
            name: 텍스트 이름
            
        Returns:
            Text 객체
        """
        return Text(tokens, name=name)
    
    def plot_word_frequency(self, text: Text, num_words: int = 20, show: bool = True):
        """
        단어 빈도 그래프 그리기
        
        Args:
            text: Text 객체
            num_words: 표시할 단어 수
            show: 그래프 표시 여부
        """
        text.plot(num_words)
        if show:
            plt.show()
    
    def plot_dispersion(self, text: Text, words: List[str], show: bool = True):
        """
        단어 분산도 그래프 그리기
        
        Args:
            text: Text 객체
            words: 분석할 단어 리스트
            show: 그래프 표시 여부
        """
        text.dispersion_plot(words)
        if show:
            plt.show()
    
    def find_concordance(self, text: Text, word: str, lines: int = 5) -> None:
        """
        단어 사용 위치 찾기
        
        Args:
            text: Text 객체
            word: 찾을 단어
            lines: 표시할 줄 수
        """
        text.concordance(word, lines=lines)
    
    def find_similar_words(self, text: Text, word: str, num: int = 10) -> List[str]:
        """
        유사한 문맥에서 사용된 단어 찾기
        
        Args:
            text: Text 객체
            word: 기준 단어
            num: 반환할 단어 수
            
        Returns:
            유사 단어 리스트
        """
        return text.similar(word, num)
    
    def find_collocations(self, text: Text, num: int = 10) -> List[str]:
        """
        연어(collocation) 찾기
        
        Args:
            text: Text 객체
            num: 반환할 연어 수
            
        Returns:
            연어 리스트
        """
        return text.collocations(num)
    
    # ***********
    # FreqDist 관련 메서드
    # ***********
    
    def create_freq_dist(self, tokens: List[str]) -> FreqDist:
        """
        빈도 분포 객체 생성
        
        Args:
            tokens: 토큰 리스트
            
        Returns:
            FreqDist 객체
        """
        return FreqDist(tokens)
    
    def get_freq_stats(self, freq_dist: FreqDist, word: str) -> Tuple[int, int, float]:
        """
        빈도 통계 조회
        
        Args:
            freq_dist: FreqDist 객체
            word: 조회할 단어
            
        Returns:
            (전체 단어 수, 단어 출현 횟수, 단어 출현 확률) 튜플
        """
        return freq_dist.N(), freq_dist[word], freq_dist.freq(word)
    
    def get_most_common(self, freq_dist: FreqDist, num: int = 10) -> List[Tuple[str, int]]:
        """
        가장 빈도가 높은 단어 조회
        
        Args:
            freq_dist: FreqDist 객체
            num: 반환할 단어 수
            
        Returns:
            (단어, 빈도) 튜플 리스트
        """
        return freq_dist.most_common(num)
    
    def extract_names_from_text(
        self, 
        text: str, 
        stopwords: Optional[List[str]] = None
    ) -> FreqDist:
        """
        텍스트에서 고유명사(NNP) 추출하여 빈도 분포 생성
        
        Args:
            text: 입력 텍스트
            stopwords: 제외할 단어 리스트
            
        Returns:
            고유명사 빈도 분포
        """
        if stopwords is None:
            stopwords = ["Mr.", "Mrs.", "Miss", "Mr", "Mrs", "Dear"]
        
        tokens = self.tokenize_regex(text)
        tagged_tokens = pos_tag(tokens)
        names_list = [
            t[0] for t in tagged_tokens 
            if t[1] == "NNP" and t[0] not in stopwords
        ]
        return self.create_freq_dist(names_list)
    
    # ***********
    # 워드클라우드 관련 메서드
    # ***********
    
    def create_wordcloud(
        self, 
        freq_dist: FreqDist,
        width: int = 1000,
        height: int = 600,
        background_color: str = "white",
        random_state: int = 0,
        show: bool = True
    ) -> WordCloud:
        """
        워드클라우드 생성
        
        Args:
            freq_dist: FreqDist 객체
            width: 이미지 너비
            height: 이미지 높이
            background_color: 배경색
            random_state: 랜덤 시드
            show: 그래프 표시 여부
            
        Returns:
            WordCloud 객체
        """
        wc = WordCloud(
            width=width,
            height=height,
            background_color=background_color,
            random_state=random_state
        )
        wc.generate_from_frequencies(freq_dist)
        
        if show:
            plt.imshow(wc)
            plt.axis("off")
            plt.show()
        
        return wc
    
    # ***********
    # 통합 분석 메서드
    # ***********
    
    def analyze_text(
        self,
        text: str,
        text_name: str = "Text",
        plot_frequency: bool = False,
        plot_dispersion_words: Optional[List[str]] = None,
        extract_names: bool = False,
        create_wordcloud: bool = False
    ) -> Dict:
        """
        텍스트 종합 분석
        
        Args:
            text: 분석할 텍스트
            text_name: 텍스트 이름
            plot_frequency: 빈도 그래프 그리기 여부
            plot_dispersion_words: 분산도 그래프에 사용할 단어 리스트
            extract_names: 고유명사 추출 여부
            create_wordcloud: 워드클라우드 생성 여부
            
        Returns:
            분석 결과 딕셔너리
        """
        # 토큰화
        tokens = self.tokenize_regex(text)
        text_obj = self.create_text_object(tokens, text_name)
        
        # 빈도 분포
        freq_dist = self.create_freq_dist(tokens)
        
        result = {
            "text_name": text_name,
            "total_tokens": len(tokens),
            "vocabulary_size": len(freq_dist),
            "most_common_words": self.get_most_common(freq_dist, 10),
            "text_object": text_obj,
            "freq_dist": freq_dist
        }
        
        # 빈도 그래프
        if plot_frequency:
            self.plot_word_frequency(text_obj, show=True)
        
        # 분산도 그래프
        if plot_dispersion_words:
            self.plot_dispersion(text_obj, plot_dispersion_words, show=True)
        
        # 고유명사 추출
        if extract_names:
            names_freq = self.extract_names_from_text(text)
            result["names_freq_dist"] = names_freq
            result["most_common_names"] = self.get_most_common(names_freq, 10)
        
        # 워드클라우드
        if create_wordcloud:
            wordcloud = self.create_wordcloud(freq_dist, show=True)
            result["wordcloud"] = wordcloud
        
        return result


# 사용 예제
if __name__ == "__main__":
    # 서비스 인스턴스 생성
    nltk_service = NLTKService()
    
    # 엠마 텍스트 로드
    emma_text = nltk_service.get_emma_text(1000)
    print("=== 엠마 텍스트 일부 ===")
    print(emma_text[:200])
    print()
    
    # 토큰화 예제
    print("=== 문장 토큰화 ===")
    sentences = nltk_service.tokenize_sentences(emma_text[:500])
    print(sentences[0] if sentences else "No sentences")
    print()
    
    # 품사 태깅 예제
    print("=== 품사 태깅 ===")
    sample_sentence = "Emma refused to permit us to obtain the refuse permit"
    tagged = nltk_service.tag_pos(sample_sentence)
    print(tagged)
    print()
    
    # 형태소 분석 예제
    print("=== 형태소 분석 ===")
    words = ['lives', 'crying', 'flies', 'dying']
    print(f"Porter Stemming: {nltk_service.stem_porter(words)}")
    print(f"Lancaster Stemming: {nltk_service.stem_lancaster(words)}")
    print(f"Lemmatization: {nltk_service.lemmatize(words)}")
    print()
    
    # 종합 분석
    print("=== 종합 분석 ===")
    analysis = nltk_service.analyze_text(
        emma_text,
        text_name="Emma",
        extract_names=True,
        create_wordcloud=False  # True로 설정하면 워드클라우드 표시
    )
    print(f"총 토큰 수: {analysis['total_tokens']}")
    print(f"어휘 크기: {analysis['vocabulary_size']}")
    print(f"가장 빈도 높은 단어: {analysis['most_common_words'][:5]}")

