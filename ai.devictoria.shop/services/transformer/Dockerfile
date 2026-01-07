FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치 (필요한 최소 패키지만)
RUN apt-get update && apt-get install -y \
    g++ \
    curl \
    wget \
    gnupg \
    unzip \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치 (selenium을 위한)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# NLTK 리소스 미리 다운로드
RUN python -m nltk.downloader punkt wordnet omw-1.4 || true

# app 디렉토리 복사
COPY app/ ./app/

EXPOSE 9007

# uvicorn으로 실행 (app.main:app으로 모듈 경로 지정)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9007"]
