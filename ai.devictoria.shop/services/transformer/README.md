# KoELECTRA 영화 리뷰 감성 분석 서비스

한국어 영화 리뷰를 분석하여 긍정/부정 감성을 판단하는 RESTful API 서비스입니다.

## 🎯 주요 기능

- **감성 분석**: 영화 리뷰의 긍정/부정 판단
- **신뢰도 점수**: 예측 신뢰도 제공 (0-1)
- **배치 처리**: 여러 리뷰 동시 분석
- **캐싱**: Redis 기반 결과 캐싱
- **고성능**: KoELECTRA 기반 빠른 추론

## 🛠️ 기술 스택

- **모델**: KoELECTRA (monologg/koelectra-base-v3-discriminator)
- **Framework**: FastAPI + PyTorch + Transformers
- **Cache**: Redis
- **Container**: Docker

## 📦 설치 및 실행

### 1. 로컬 환경 (Python)

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 서버 실행
python -m app.main

# 또는 uvicorn 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 9006
```

### 2. Docker 환경

```bash
# Docker 이미지 빌드
docker build -t sentiment-api .

# 컨테이너 실행
docker run -p 9006:9006 \
  -e DEVICE=cpu \
  -e REDIS_HOST=host.docker.internal \
  sentiment-api
```

### 3. Docker Compose

```bash
# 서비스 시작 (API + Redis)
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

## 📖 API 사용 예시

### 1. 단일 리뷰 분석

```bash
curl -X POST "http://localhost:9006/api/v1/sentiment/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "이 영화 정말 재미있어요! 강력 추천합니다.",
    "return_probabilities": true
  }'
```

**응답:**
```json
{
  "status": "success",
  "data": {
    "text": "이 영화 정말 재미있어요! 강력 추천합니다.",
    "sentiment": "긍정",
    "score": 0.9823,
    "probabilities": {
      "부정": 0.0177,
      "긍정": 0.9823
    }
  },
  "processing_time_ms": 45.2,
  "timestamp": "2024-12-15T10:30:00Z"
}
```

### 2. 배치 리뷰 분석

```bash
curl -X POST "http://localhost:9006/api/v1/sentiment/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "정말 최고의 영화였어요!",
      "시간 낭비였습니다.",
      "그냥 그래요."
    ]
  }'
```

### 3. 헬스 체크

```bash
curl http://localhost:9006/api/v1/sentiment/health
```

### 4. 모델 정보

```bash
curl http://localhost:9006/api/v1/sentiment/model-info
```

## 📊 API 문서

서버 실행 후 다음 URL에서 대화형 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:9006/docs
- **ReDoc**: http://localhost:9006/redoc

## ⚙️ 설정

`.env` 파일에서 다음 설정을 변경할 수 있습니다:

| 설정 | 기본값 | 설명 |
|------|--------|------|
| `MODEL_NAME` | monologg/koelectra-base-v3-discriminator | 사용할 모델 |
| `DEVICE` | cpu | 실행 장치 (cpu/cuda) |
| `MAX_LENGTH` | 512 | 최대 토큰 길이 |
| `REDIS_HOST` | localhost | Redis 호스트 |
| `REDIS_PORT` | 6379 | Redis 포트 |
| `CACHE_TTL` | 3600 | 캐시 유지 시간(초) |
| `ENABLE_CACHE` | true | 캐싱 활성화 여부 |

## 🚀 성능 최적화

### CPU 최적화
```bash
# Dynamic Quantization 활성화
USE_QUANTIZATION=true

# 배치 크기 조정
BATCH_SIZE=16
```

### GPU 사용
```bash
# CUDA 장치 사용
DEVICE=cuda

# Docker에서 GPU 사용
docker run --gpus all -p 9006:9006 sentiment-api
```

## 📝 아키텍처

자세한 아키텍처 문서는 [ARCHITECTURE.md](./ARCHITECTURE.md)를 참고하세요.

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/

# 커버리지 리포트
pytest --cov=app tests/
```

## 📄 라이선스

MIT License

## 👥 기여

이슈와 PR은 언제나 환영합니다!

