# 📮 Postman 사용 가이드

KoELECTRA 감성 분석 API를 Postman에서 테스트하는 방법입니다.

## 🚀 서버 실행

```bash
# 서버 실행
cd ai.devictoria.shop/services/transformer
python -m app.main

# 또는 uvicorn 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 9006
```

서버가 실행되면: http://localhost:9006

## 📝 API 엔드포인트

### 1. 감성 분석 (POST)

**URL:** `http://localhost:9006/api/v1/sentiment/analyze`

**Method:** `POST`

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "text": "이 영화 정말 재미있어요! 강력 추천합니다.",
    "return_probabilities": true
}
```

**예상 응답:**
```json
{
    "status": "success",
    "data": {
        "text": "이 영화 정말 재미있어요! 강력 추천합니다.",
        "sentiment": "긍정",
        "score": 0.9234,
        "label_id": 1,
        "probabilities": {
            "부정": 0.0766,
            "긍정": 0.9234
        },
        "processing_time_ms": 45.2
    },
    "timestamp": "2024-12-15T10:30:00Z"
}
```

### 2. 헬스 체크 (GET)

**URL:** `http://localhost:9006/api/v1/sentiment/health`

**Method:** `GET`

**예상 응답:**
```json
{
    "status": "healthy",
    "model_loaded": true,
    "tokenizer_loaded": true,
    "device": "cpu",
    "timestamp": "2024-12-15T10:30:00Z"
}
```

### 3. 모델 정보 (GET)

**URL:** `http://localhost:9006/api/v1/sentiment/model-info`

**Method:** `GET`

**예상 응답:**
```json
{
    "model_path": "/path/to/koelectra_model",
    "device": "cpu",
    "max_length": 512,
    "model_loaded": true,
    "tokenizer_loaded": true,
    "timestamp": "2024-12-15T10:30:00Z"
}
```

## 🧪 테스트 예시

### 긍정 감성 텍스트
```json
{
    "text": "이 영화 정말 재미있어요!",
    "return_probabilities": true
}
```

### 부정 감성 텍스트
```json
{
    "text": "최악의 영화였습니다. 시간 낭비예요.",
    "return_probabilities": true
}
```

### 중립적 텍스트
```json
{
    "text": "그냥 그래요. 특별한 건 없어요.",
    "return_probabilities": true
}
```

## 📊 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `status` | string | 응답 상태 ("success" 또는 "error") |
| `data.text` | string | 입력된 원본 텍스트 |
| `data.sentiment` | string | 감성 레이블 ("긍정" 또는 "부정") |
| `data.score` | float | 신뢰도 점수 (0.0 ~ 1.0) |
| `data.label_id` | int | 레이블 ID (0: 부정, 1: 긍정) |
| `data.probabilities` | object | 각 감성별 확률값 (return_probabilities=true일 때) |
| `data.processing_time_ms` | float | 처리 시간 (밀리초) |
| `timestamp` | string | 응답 시각 (ISO 8601 형식) |

## 🌐 Swagger UI 사용

브라우저에서 다음 주소로 접속하면 대화형 API 문서를 사용할 수 있습니다:

**Swagger UI:** http://localhost:9006/docs

여기서 직접 API를 테스트할 수 있습니다!

## ⚠️ 주의사항

1. **첫 실행 시**: 모델을 로드하는데 시간이 걸릴 수 있습니다 (10-30초)
2. **텍스트 길이**: 최대 5000자까지 입력 가능
3. **한국어 텍스트**: 모델은 한국어에 최적화되어 있습니다

## 🐛 문제 해결

### 모델 로드 실패
- 모델 파일이 `app/koelectra/koelectra_model/` 경로에 있는지 확인
- 필요한 파일: `config.json`, `pytorch_model.bin`, `vocab.txt`, `tokenizer_config.json`

### 서버 연결 실패
- 서버가 실행 중인지 확인: `curl http://localhost:9006/ping`
- 포트가 사용 중인지 확인: `netstat -an | grep 9006`

