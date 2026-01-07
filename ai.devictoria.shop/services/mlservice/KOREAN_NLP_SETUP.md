# 한국어 자연어 처리 (NLP) 설정 가이드

## 개요
이 프로젝트에서는 **kiwipiepy (Kiwi)** 라이브러리를 사용하여 한국어 자연어 처리 및 Bag of Words (BoW)를 구축합니다.

## 선택한 라이브러리: kiwipiepy

### 추천 이유
1. **Java 불필요**: KoNLPy와 달리 Java 설치가 필요 없어 Docker 환경에서 더 간편
2. **빠른 성능**: C++로 구현된 형태소 분석기로 매우 빠름
3. **높은 정확도**: 세종 코퍼스 기반, 한국어 형태소 분석 정확도 우수
4. **간단한 설치**: `pip install kiwipiepy`로 간단히 설치 가능
5. **지속적 관리**: 활발히 유지보수되는 프로젝트

### 다른 라이브러리와 비교

| 라이브러리 | 장점 | 단점 |
|---|---|---|
| **kiwipiepy** | ✅ Java 불필요, 빠름, 정확 | - |
| KoNLPy (Mecab) | 정확도 높음 | ❌ Java 필수, 설치 복잡 |
| KoNLPy (Okt) | 간편 | 느림, 정확도 낮음 |
| spaCy + ko_core | 다양한 기능 | 모델 크기 큼 |

## 설치

### requirements.txt에 추가
```txt
kiwipiepy==0.17.1
```

### Docker 빌드 시 자동 설치
```bash
docker-compose build mlservice
```

## 프로젝트 구조

```
ai.devictoria.shop/services/mlservice/
├── app/
│   ├── nlp/
│   │   ├── korean/                 # 한국어 NLP 패키지
│   │   │   ├── __init__.py
│   │   │   ├── korean_nlp_service.py  # 핵심 서비스 (Singleton)
│   │   │   └── korean_router.py       # FastAPI 라우터
│   │   ├── data/
│   │   │   ├── kr-Report_2018.txt     # 한국어 말뭉치 (삼성 지속가능경영보고서)
│   │   │   └── stopwords.txt          # 한국어 불용어
│   │   └── save/                       # 워드클라우드 저장 폴더
│   └── main.py                          # FastAPI 앱
└── requirements.txt
```

## 사용 전략

### 1. Singleton 패턴
`KoreanNLPService`는 Singleton 패턴으로 구현되어 한 번만 초기화됩니다.

```python
from app.nlp.korean import get_korean_nlp_service

# 어디서든 동일한 인스턴스 사용
service = get_korean_nlp_service()
```

### 2. 불용어 관리
불용어는 `app/nlp/data/stopwords.txt` 파일에서 관리됩니다.
- 처음 실행 시 기본 불용어로 파일 자동 생성
- 필요에 따라 불용어 추가/수정 가능
- 프로그래밍 방식으로도 추가 가능:
  ```python
  service.add_stopwords(['추가단어1', '추가단어2'])
  ```

### 3. 품사 태그 (POS Tags)
Kiwi는 세종 품사 태그를 사용합니다. 주요 품사:
- `NNG`: 일반명사 (예: 사람, 컴퓨터)
- `NNP`: 고유명사 (예: 삼성, 서울)
- `NNB`: 의존명사 (예: 것, 수)
- `VV`: 동사 (예: 먹다, 가다)
- `VA`: 형용사 (예: 좋다, 크다)
- `MAG`: 일반부사 (예: 매우, 너무)

기본적으로 명사만 추출 (`['NNG', 'NNP', 'NNB']`):
```python
tokens = service.tokenize(text, pos_tags=['NNG', 'NNP'])  # 일반명사 + 고유명사
```

### 4. Bag of Words (BoW) 생성
```python
# 상위 100개 단어만
bow = service.create_bow(text, top_n=100)

# 모든 단어
bow = service.create_bow(text, top_n=None)

# 동사와 형용사만
bow = service.create_bow(text, pos_tags=['VV', 'VA'])
```

## API 엔드포인트

### 기본 정보
```
GET /korean/
```

### 1. 토큰화
```
POST /korean/tokenize
Body: {
  "text": "삼성전자는 지속가능경영을 실천합니다.",
  "pos_tags": ["NNG", "NNP"],
  "min_length": 2,
  "remove_stopwords": true
}
```

### 2. BoW 생성
```
POST /korean/bow
Body: {
  "text": "...",
  "top_n": 100
}
```

### 3. 키워드 추출
```
POST /korean/keywords
Body: {
  "text": "...",
  "top_n": 20
}
```

### 4. 품사 태깅
```
POST /korean/pos?text=삼성전자는 지속가능경영을 실천합니다.
```

### 5. 워드클라우드 생성
```
POST /korean/wordcloud
Body: {
  "text": "...",
  "width": 1000,
  "height": 600,
  "background_color": "white",
  "top_n": 100
}
```

### 6. 말뭉치 분석
```
GET /korean/corpus?filename=kr-Report_2018.txt&top_n=20
```

## 사용 예시

### Python 코드
```python
from app.nlp.korean import get_korean_nlp_service

service = get_korean_nlp_service()

# 말뭉치 로드
text = service.load_corpus(Path("app/nlp/data/kr-Report_2018.txt"))

# 토큰화
tokens = service.tokenize(text, min_length=2)

# BoW 생성
bow = service.create_bow(text, top_n=100)

# 키워드 추출
keywords = service.extract_keywords(text, top_n=20)
```

### Swagger UI에서 테스트
1. 브라우저에서 `http://localhost:8080/docs` 접속
2. `korean-nlp` 태그 찾기
3. 원하는 엔드포인트 선택 → "Try it out" → 요청 전송

## 성능 최적화

### 1. Singleton 패턴으로 초기화 비용 최소화
Kiwi 형태소 분석기는 첫 초기화에 약간의 시간이 걸리지만, Singleton 패턴으로 한 번만 초기화합니다.

### 2. 불용어 캐싱
불용어는 처음 로드 후 메모리에 유지되어 매번 파일을 읽지 않습니다.

### 3. top_n 파라미터 활용
전체 단어가 아닌 상위 N개만 추출하여 메모리와 처리 시간 절약:
```python
bow = service.create_bow(text, top_n=100)  # 상위 100개만
```

## 확장 가능성

### 1. 새로운 말뭉치 추가
`app/nlp/data/` 폴더에 텍스트 파일 추가:
```bash
app/nlp/data/my_corpus.txt
```

### 2. 불용어 추가
`app/nlp/data/stopwords.txt` 파일 편집 또는:
```python
service.add_stopwords(['신규불용어1', '신규불용어2'])
```

### 3. 다른 형태소 분석기로 교체
`KoreanNLPService` 클래스 내부만 수정하면 됩니다 (인터페이스 동일 유지).

## 문제 해결

### kiwipiepy 설치 실패
```bash
pip install --upgrade pip
pip install kiwipiepy
```

### Docker 빌드 오류
```bash
docker-compose build --no-cache mlservice
```

### 한글 폰트 없음 (워드클라우드)
Docker 컨테이너에 한글 폰트 설치:
```dockerfile
RUN apt-get update && apt-get install -y fonts-nanum
```

## 참고 자료
- [Kiwi 공식 문서](https://github.com/bab2min/Kiwi)
- [kiwipiepy PyPI](https://pypi.org/project/kiwipiepy/)
- [세종 품사 태그표](https://ithub.korean.go.kr/user/guide/corpus/guide1.do)

