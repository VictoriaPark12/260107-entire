# KoELECTRA 영화 리뷰 감성 분석 서비스 아키텍처

## 📋 목차
1. [개요](#개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [모델 아키텍처](#모델-아키텍처)
4. [프로젝트 구조](#프로젝트-구조)
5. [API 설계](#api-설계)
6. [데이터 플로우](#데이터-플로우)
7. [성능 최적화 전략](#성능-최적화-전략)
8. [배포 전략](#배포-전략)

---

## 개요

### 서비스 목적
- **입력**: 한국어 영화 리뷰 텍스트
- **출력**: 감성 분석 결과 (긍정/부정) + 신뢰도 점수
- **모델**: KoELECTRA (Korean ELECTRA) - 허깅페이스 사전학습 모델

### 기술 스택
- **Deep Learning Framework**: PyTorch
- **Transformer Library**: Hugging Face Transformers
- **Web Framework**: FastAPI
- **Model Serving**: ONNX Runtime (선택적 최적화)
- **Caching**: Redis
- **Containerization**: Docker

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (Web Browser / Mobile App / External API Consumer)         │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                         │
│            FastAPI (Uvicorn ASGI Server)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Router: /api/v1/sentiment                             │ │
│  │  - POST /analyze    : 단일 리뷰 분석                    │ │
│  │  - POST /batch      : 배치 리뷰 분석                    │ │
│  │  - GET  /health     : 헬스 체크                         │ │
│  │  - GET  /model-info : 모델 정보 조회                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SentimentService                                    │   │
│  │  - 입력 전처리 (텍스트 정제)                          │   │
│  │  - 토큰화 및 임베딩                                   │   │
│  │  - 모델 추론                                          │   │
│  │  - 결과 후처리                                        │   │
│  │  - 캐싱 관리                                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
        ▼                            ▼
┌──────────────────┐       ┌──────────────────┐
│  Model Layer     │       │  Cache Layer     │
│                  │       │                  │
│  KoELECTRA       │       │  Redis           │
│  - Tokenizer     │       │  - 쿼리 캐싱     │
│  - Model         │       │  - 결과 캐싱     │
│  - Config        │       │  - TTL: 1시간    │
└──────────────────┘       └──────────────────┘
```

---

## 모델 아키텍처

### KoELECTRA 구조

```
입력 텍스트: "이 영화 정말 재미있어요!"
    │
    ▼
┌────────────────────────────────────────────────────────┐
│  1. Tokenization (토큰화)                               │
│  WordPiece Tokenizer                                   │
│  Output: [CLS] 이 영화 정말 재미 ##있어요 ! [SEP]      │
└────────────┬───────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────┐
│  2. Embedding Layer (임베딩 레이어)                     │
│  - Token Embeddings   (토큰 임베딩)                     │
│  - Position Embeddings (위치 임베딩)                    │
│  - Token Type Embeddings (세그먼트 임베딩)              │
│  Dimension: 768                                        │
└────────────┬───────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────┐
│  3. ELECTRA Encoder (인코더)                           │
│  - 12 Transformer Layers                               │
│  - 12 Attention Heads per Layer                        │
│  - Hidden Size: 768                                    │
│  - Intermediate Size: 3072                             │
│  - Dropout: 0.1                                        │
│                                                         │
│  각 레이어:                                             │
│  ┌────────────────────────────────────────────────┐   │
│  │ Multi-Head Self-Attention                      │   │
│  │  - Q, K, V 행렬 계산                           │   │
│  │  - Attention Score 계산                        │   │
│  │  - Layer Normalization                         │   │
│  └────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────┐   │
│  │ Feed-Forward Network                           │   │
│  │  - Dense(768 → 3072) + GELU                   │   │
│  │  - Dense(3072 → 768)                          │   │
│  │  - Layer Normalization                         │   │
│  └────────────────────────────────────────────────┘   │
└────────────┬───────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────┐
│  4. Pooling Layer ([CLS] 토큰 추출)                    │
│  Output: [CLS] 벡터 (768 차원)                         │
└────────────┬───────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────┐
│  5. Classification Head (분류 헤드)                     │
│  - Dropout (0.1)                                       │
│  - Dense Layer (768 → 2)                              │
│  - Softmax Activation                                  │
│                                                         │
│  Output: [부정 확률, 긍정 확률]                         │
│  Example: [0.15, 0.85]                                 │
└────────────┬───────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────┐
│  6. Post-Processing (후처리)                           │
│  - 최대 확률값의 인덱스 선택: argmax([0.15, 0.85]) = 1 │
│  - 레이블 매핑: {0: "부정", 1: "긍정"}                  │
│  - 신뢰도 점수: max([0.15, 0.85]) = 0.85               │
│                                                         │
│  최종 출력:                                             │
│  {                                                      │
│    "label": "긍정",                                     │
│    "score": 0.85,                                      │
│    "probabilities": {                                  │
│      "부정": 0.15,                                      │
│      "긍정": 0.85                                       │
│    }                                                    │
│  }                                                      │
└────────────────────────────────────────────────────────┘
```

### 모델 하이퍼파라미터

| 파라미터 | 값 | 설명 |
|---------|-----|------|
| `vocab_size` | 30000 | 한국어 WordPiece 어휘 크기 |
| `hidden_size` | 768 | 은닉층 차원 |
| `num_hidden_layers` | 12 | Transformer 레이어 수 |
| `num_attention_heads` | 12 | 어텐션 헤드 수 |
| `intermediate_size` | 3072 | FFN 중간층 차원 |
| `max_position_embeddings` | 512 | 최대 시퀀스 길이 |
| `type_vocab_size` | 2 | 세그먼트 타입 수 |
| `layer_norm_eps` | 1e-12 | Layer Norm epsilon |
| `dropout` | 0.1 | 드롭아웃 비율 |

---

## 프로젝트 구조

```
transformer/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI 애플리케이션 엔트리포인트
│   │
│   ├── sentiment/                       # 감성 분석 모듈
│   │   ├── __init__.py
│   │   ├── config.py                    # 설정 관리
│   │   ├── model.py                     # Pydantic 모델 (요청/응답)
│   │   ├── service.py                   # 비즈니스 로직
│   │   ├── router.py                    # API 라우터
│   │   └── utils.py                     # 유틸리티 함수
│   │
│   ├── models/                          # ML 모델 관리
│   │   ├── __init__.py
│   │   ├── model_loader.py              # 모델 로드 및 초기화
│   │   ├── inference.py                 # 추론 엔진
│   │   └── cache/                       # 다운로드된 모델 캐시
│   │       └── koelectra-base-v3/       # 허깅페이스 모델 캐시
│   │
│   ├── preprocessing/                   # 전처리 모듈
│   │   ├── __init__.py
│   │   ├── text_cleaner.py              # 텍스트 정제
│   │   └── tokenizer.py                 # 토큰화
│   │
│   └── common/                          # 공통 유틸리티
│       ├── __init__.py
│       ├── logger.py                    # 로깅 설정
│       ├── exceptions.py                # 커스텀 예외
│       └── redis_client.py              # Redis 클라이언트
│
├── tests/                               # 테스트 코드
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_service.py
│   └── test_model.py
│
├── requirements.txt                     # Python 의존성
├── Dockerfile                           # Docker 이미지 빌드
├── docker-compose.yml                   # Docker Compose 설정
├── .env.example                         # 환경 변수 예시
└── ARCHITECTURE.md                      # 이 문서
```

---

## API 설계

### 1. 단일 리뷰 감성 분석
```http
POST /api/v1/sentiment/analyze
Content-Type: application/json

Request Body:
{
  "text": "이 영화 정말 재미있어요! 강력 추천합니다.",
  "return_probabilities": true
}

Response (200 OK):
{
  "status": "success",
  "data": {
    "text": "이 영화 정말 재미있어요! 강력 추천합니다.",
    "sentiment": "긍정",
    "score": 0.9823,
    "probabilities": {
      "부정": 0.0177,
      "긍정": 0.9823
    },
    "processing_time_ms": 45.2
  }
}
```

### 2. 배치 리뷰 분석
```http
POST /api/v1/sentiment/batch
Content-Type: application/json

Request Body:
{
  "texts": [
    "정말 최고의 영화였어요!",
    "시간 낭비였습니다.",
    "그냥 그래요."
  ]
}

Response (200 OK):
{
  "status": "success",
  "data": {
    "results": [
      {
        "text": "정말 최고의 영화였어요!",
        "sentiment": "긍정",
        "score": 0.9756
      },
      {
        "text": "시간 낭비였습니다.",
        "sentiment": "부정",
        "score": 0.9234
      },
      {
        "text": "그냥 그래요.",
        "sentiment": "중립",
        "score": 0.5123
      }
    ],
    "total_count": 3,
    "processing_time_ms": 123.5
  }
}
```

### 3. 헬스 체크
```http
GET /api/v1/sentiment/health

Response (200 OK):
{
  "status": "healthy",
  "model_loaded": true,
  "redis_connected": true,
  "timestamp": "2024-12-15T10:30:00Z"
}
```

### 4. 모델 정보 조회
```http
GET /api/v1/sentiment/model-info

Response (200 OK):
{
  "model_name": "monologg/koelectra-base-v3-discriminator",
  "model_type": "ELECTRA",
  "language": "Korean",
  "num_labels": 2,
  "max_length": 512,
  "version": "1.0.0"
}
```

---

## 데이터 플로우

### 순방향 추론 플로우

```
1. 요청 수신
   └─> FastAPI Router (router.py)

2. 입력 검증
   └─> Pydantic Model (model.py)
   └─> 텍스트 길이 체크 (최대 512 토큰)

3. 캐시 확인
   └─> Redis 조회 (hash of text)
   └─> 캐시 히트 → 바로 반환
   └─> 캐시 미스 → 다음 단계

4. 전처리
   └─> 텍스트 정제 (text_cleaner.py)
       - HTML 태그 제거
       - 특수문자 정제
       - 공백 정규화
   └─> 토큰화 (tokenizer.py)
       - KoELECTRA Tokenizer
       - Padding & Truncation

5. 모델 추론
   └─> 추론 엔진 (inference.py)
       - 모델 forward pass
       - GPU/CPU 자동 선택
       - 배치 처리 최적화

6. 후처리
   └─> Softmax 적용
   └─> 레이블 매핑
   └─> 신뢰도 계산

7. 캐싱
   └─> Redis 저장 (TTL: 1시간)

8. 응답 반환
   └─> JSON 직렬화
   └─> HTTP Response
```

---

## 성능 최적화 전략

### 1. 모델 최적화
```python
# 전략 1: 모델 양자화 (INT8)
- 모델 크기: 400MB → 100MB (75% 감소)
- 추론 속도: 2배 향상
- 정확도 손실: < 1%

# 전략 2: ONNX 변환
- 추론 속도: 1.5-2배 향상
- 크로스 플랫폼 호환성
- 배포 간소화

# 전략 3: Dynamic Quantization
torch.quantization.quantize_dynamic(
    model, {torch.nn.Linear}, dtype=torch.qint8
)
```

### 2. 캐싱 전략
```python
# Redis 캐싱
- Key: SHA256(text_hash)
- Value: JSON(결과)
- TTL: 3600초 (1시간)
- 예상 히트율: 40-60%

# LRU 캐시 (메모리)
from functools import lru_cache
@lru_cache(maxsize=1000)
def predict(text_hash):
    ...
```

### 3. 배치 처리
```python
# 동적 배치 생성
- 최소 배치 크기: 4
- 최대 배치 크기: 32
- 대기 시간: 100ms

# GPU 메모리 최적화
- Gradient 비활성화: torch.no_grad()
- Mixed Precision: torch.cuda.amp
```

### 4. 비동기 처리
```python
# FastAPI 비동기 핸들러
@router.post("/analyze")
async def analyze_sentiment(request: SentimentRequest):
    result = await service.analyze_async(request.text)
    return result

# 백그라운드 태스크
from fastapi import BackgroundTasks
```

---

## 배포 전략

### 1. Docker 컨테이너화
```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 오케스트레이션
```yaml
# docker-compose.yml
version: '3.8'
services:
  transformer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MODEL_NAME=monologg/koelectra-base-v3-discriminator
      - REDIS_HOST=redis
      - DEVICE=cuda
    depends_on:
      - redis
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### 3. 스케일링 전략
```
# 수평 스케일링
- Load Balancer (Nginx/Traefik)
- Multiple Container Replicas (3-5개)
- Redis 공유 캐시

# 수직 스케일링
- GPU 인스턴스 (T4/V100)
- CPU: 4-8 코어
- RAM: 16-32GB
```

### 4. 모니터링
```python
# 메트릭 수집
- Prometheus + Grafana
- 지연시간 (Latency)
- 처리량 (Throughput)
- 에러율 (Error Rate)
- 캐시 히트율

# 로깅
- Structured Logging (JSON)
- Log Level: INFO/DEBUG/ERROR
- ELK Stack (선택적)
```

---

## 추가 고려사항

### 1. 보안
- API Key 인증
- Rate Limiting (요청 제한)
- CORS 설정
- Input Sanitization

### 2. 에러 처리
- 타임아웃 설정 (10초)
- Retry 전략 (3회)
- Graceful Degradation
- 상세한 에러 메시지

### 3. 모델 업데이트
- Blue-Green 배포
- A/B 테스팅
- 모델 버전 관리
- Rollback 전략

### 4. 비용 최적화
- Spot Instance 활용
- Auto-scaling 설정
- Cold Start 최소화
- 효율적인 캐싱

---

## 참고 자료

- [KoELECTRA 논문](https://arxiv.org/abs/2010.02840)
- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [PyTorch 최적화 가이드](https://pytorch.org/tutorials/recipes/recipes/tuning_guide.html)

