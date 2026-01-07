# API Gateway Dockerfile
# 
# 빌드 방법 (루트 디렉토리에서 실행):
#   docker build -t api-gateway:latest .
# 
# 실행 방법:
#   docker run -p 8080:8080 api-gateway:latest

# 1단계: 빌드
FROM eclipse-temurin:21-jdk AS builder
WORKDIR /app

# 프로젝트 파일 복사
COPY gradle/ ./gradle/
COPY gradlew ./
COPY gradlew.bat ./
COPY build.gradle ./
COPY settings.gradle ./
COPY src/ ./src/

# 권한 설정 및 빌드
RUN chmod +x gradlew && ./gradlew clean build -x test --no-daemon

# 2단계: 실행 이미지
FROM eclipse-temurin:21-jre
WORKDIR /app

# curl 설치 (health check용)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 빌드된 JAR 파일 복사
COPY --from=builder /app/build/libs/*.jar app.jar

# 포트 노출
EXPOSE 8080

# 애플리케이션 실행
ENTRYPOINT ["java", "-jar", "app.jar"]