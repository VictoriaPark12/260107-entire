"""
한국어 자연어 처리 서비스
KoNLPy 없이 kiwipiepy를 사용한 형태소 분석
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from collections import Counter
import re


class KoreanNLPService:
    """
    한국어 자연어 처리 서비스 (Singleton 패턴)
    
    kiwipiepy를 사용하여 형태소 분석 및 BoW 생성
    """
    
    _instance = None
    _kiwi = None
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super(KoreanNLPService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """초기화 (한 번만 실행)"""
        if self._initialized:
            return
            
        try:
            from kiwipiepy import Kiwi
            self._kiwi = Kiwi()
            print("[Korean NLP] Kiwi 형태소 분석기 초기화 완료")
        except ImportError:
            print("[Korean NLP] kiwipiepy가 설치되지 않았습니다. pip install kiwipiepy")
            self._kiwi = None
        
        # 불용어 로드
        self.stopwords = self._load_stopwords()
        self._initialized = True
    
    def _load_stopwords(self) -> set:
        """불용어 로드"""
        stopwords_file = Path(__file__).parent.parent / "data" / "stopwords.txt"
        
        # 기본 한국어 불용어
        default_stopwords = {
            '의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를', '으로', '자',
            '에', '와', '한', '하다', '있다', '되다', '하는', '있는', '되는', '수', '등', '및',
            '그', '저', '것', '때', '더', '매우', '너무', '정말', '아주', '조금', '전혀',
            '또', '또한', '그리고', '하지만', '그러나', '그래서', '왜냐하면', '때문에'
        }
        
        if stopwords_file.exists():
            try:
                with open(stopwords_file, 'r', encoding='utf-8') as f:
                    # 파일에서 불용어 로드 (한 줄에 하나씩 또는 공백으로 구분)
                    content = f.read()
                    file_stopwords = set(re.split(r'[\s,]+', content.strip()))
                    default_stopwords.update(file_stopwords)
                    print(f"[Korean NLP] 불용어 {len(file_stopwords)}개 로드 완료")
            except Exception as e:
                print(f"[Korean NLP] 불용어 파일 로드 실패: {e}")
        else:
            # 불용어 파일 생성
            try:
                stopwords_file.parent.mkdir(parents=True, exist_ok=True)
                with open(stopwords_file, 'w', encoding='utf-8') as f:
                    f.write(' '.join(sorted(default_stopwords)))
                print(f"[Korean NLP] 불용어 파일 생성 완료: {stopwords_file}")
            except Exception as e:
                print(f"[Korean NLP] 불용어 파일 생성 실패: {e}")
        
        return default_stopwords
    
    def tokenize(
        self, 
        text: str, 
        pos_tags: Optional[List[str]] = None,
        min_length: int = 2,
        remove_stopwords: bool = True
    ) -> List[str]:
        """
        한국어 텍스트 토큰화
        
        Args:
            text: 입력 텍스트
            pos_tags: 추출할 품사 태그 (None이면 모든 명사: NNG, NNP, NNB)
                     - NNG: 일반명사
                     - NNP: 고유명사
                     - NNB: 의존명사
                     - VV: 동사
                     - VA: 형용사
                     - MAG: 일반부사
            min_length: 최소 토큰 길이
            remove_stopwords: 불용어 제거 여부
        
        Returns:
            토큰 리스트
        """
        if not self._kiwi:
            raise RuntimeError("Kiwi 형태소 분석기가 초기화되지 않았습니다.")
        
        # 기본값: 명사만 추출
        if pos_tags is None:
            pos_tags = ['NNG', 'NNP', 'NNB']
        
        # 형태소 분석
        result = self._kiwi.tokenize(text)
        
        # 토큰 추출
        tokens = []
        for token in result:
            # 품사 태그 필터링
            if token.tag in pos_tags:
                word = token.form
                
                # 길이 필터링
                if len(word) < min_length:
                    continue
                
                # 불용어 제거
                if remove_stopwords and word in self.stopwords:
                    continue
                
                tokens.append(word)
        
        return tokens
    
    def create_bow(
        self,
        text: str,
        pos_tags: Optional[List[str]] = None,
        min_length: int = 2,
        remove_stopwords: bool = True,
        top_n: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Bag of Words (BoW) 생성
        
        Args:
            text: 입력 텍스트
            pos_tags: 추출할 품사 태그
            min_length: 최소 토큰 길이
            remove_stopwords: 불용어 제거 여부
            top_n: 상위 N개만 반환 (None이면 전체)
        
        Returns:
            단어별 빈도수 딕셔너리
        """
        # 토큰화
        tokens = self.tokenize(
            text=text,
            pos_tags=pos_tags,
            min_length=min_length,
            remove_stopwords=remove_stopwords
        )
        
        # 빈도수 계산
        bow = Counter(tokens)
        
        # 상위 N개만 반환
        if top_n:
            bow = dict(bow.most_common(top_n))
        else:
            bow = dict(bow)
        
        return bow
    
    def extract_keywords(
        self,
        text: str,
        top_n: int = 20,
        pos_tags: Optional[List[str]] = None
    ) -> List[Tuple[str, int]]:
        """
        키워드 추출 (빈도수 기반)
        
        Args:
            text: 입력 텍스트
            top_n: 상위 N개 키워드
            pos_tags: 추출할 품사 태그
        
        Returns:
            (키워드, 빈도수) 튜플 리스트
        """
        bow = self.create_bow(text=text, pos_tags=pos_tags, top_n=top_n)
        return list(bow.items())
    
    def analyze_pos(self, text: str) -> List[Dict[str, str]]:
        """
        품사 태깅 분석
        
        Args:
            text: 입력 텍스트
        
        Returns:
            형태소 분석 결과 리스트
        """
        if not self._kiwi:
            raise RuntimeError("Kiwi 형태소 분석기가 초기화되지 않았습니다.")
        
        result = self._kiwi.tokenize(text)
        
        return [
            {
                "form": token.form,      # 원형
                "tag": token.tag,         # 품사 태그
                "start": token.start,     # 시작 위치
                "len": token.len          # 길이
            }
            for token in result
        ]
    
    def load_corpus(self, filepath: Path) -> str:
        """
        말뭉치 파일 로드
        
        Args:
            filepath: 파일 경로
        
        Returns:
            텍스트 내용
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"[Korean NLP] 파일 로드 실패: {e}")
            return ""
    
    def add_stopwords(self, words: List[str]):
        """불용어 추가"""
        self.stopwords.update(words)
    
    def remove_stopwords_from_list(self, words: List[str]) -> List[str]:
        """리스트에서 불용어 제거"""
        return [word for word in words if word not in self.stopwords]


# 싱글톤 인스턴스 접근 함수
_korean_nlp_service: Optional[KoreanNLPService] = None


def get_korean_nlp_service() -> KoreanNLPService:
    """한국어 NLP 서비스 인스턴스 가져오기 (싱글톤)"""
    global _korean_nlp_service
    if _korean_nlp_service is None:
        _korean_nlp_service = KoreanNLPService()
    return _korean_nlp_service

