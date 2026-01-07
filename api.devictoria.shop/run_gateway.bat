@echo off
chcp 65001 >nul
title API Gateway Server
color 0A

echo ========================================
echo   API Gateway 서버 시작
echo ========================================
echo.

REM 배치 파일이 있는 디렉토리로 이동
cd /d "%~dp0"
set PROJECT_ROOT=%CD%
echo 프로젝트 루트: %PROJECT_ROOT%
echo.

REM .env 파일을 PowerShell 스크립트로 로드 (더 안정적)
set ENV_FILE=%PROJECT_ROOT%\..\.env
if exist "%ENV_FILE%" (
    echo .env 파일 로드 중: %ENV_FILE%
    REM PowerShell을 사용하여 .env 파일 로드 및 환경 변수 설정
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content '%ENV_FILE%' | ForEach-Object { if ($_ -match '^\s*([^#][^=]*?)\s*=\s*(.*?)\s*$') { $key = $matches[1].Trim(); $value = $matches[2].Trim(); if ($key -and $value) { [Environment]::SetEnvironmentVariable($key, $value, 'Process') } } }"
    echo .env 파일 로드 완료
    echo.
) else (
    echo [경고] .env 파일을 찾을 수 없습니다: %ENV_FILE%
    echo 환경 변수가 설정되지 않았을 수 있습니다.
    echo.
)

REM Docker 확인
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker를 찾을 수 없습니다. Gradle로 실행합니다.
    echo.
    goto :gradle_run
)

REM Docker가 실행 중인지 확인 (간단한 ping으로)
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker가 실행되지 않았습니다. Gradle로 실행합니다.
    echo.
    goto :gradle_run
)

REM Docker로 실행
echo Docker를 사용하여 실행합니다.
echo.

REM 기존 컨테이너가 있으면 제거
docker ps -a --filter "name=api-gateway" --format "{{.Names}}" | findstr /C:"api-gateway" >nul 2>&1
if not errorlevel 1 (
    echo 기존 컨테이너 제거 중...
    docker stop api-gateway >nul 2>&1
    docker rm api-gateway >nul 2>&1
)

REM Docker 이미지 빌드
echo Docker 이미지 빌드 중...
docker build -t api-gateway:latest .
if errorlevel 1 (
    echo [ERROR] Docker 이미지 빌드 실패. Gradle로 실행합니다.
    echo.
    goto :gradle_run
)

echo.
echo ========================================
echo   서버 정보
echo ========================================
echo   URL: http://localhost:8080
echo   Swagger UI: http://localhost:8080/swagger-ui.html
echo   API Docs: http://localhost:8080/v3/api-docs
echo ========================================
echo.
echo 종료하려면 Ctrl+C를 누르세요
echo.

REM Docker 컨테이너 실행
docker run --name api-gateway -p 8080:8080 api-gateway:latest
goto :end

:gradle_run
REM Java 버전 확인
java -version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Java를 찾을 수 없습니다!
    echo Java 21 이상이 설치되어 있고 PATH에 추가되어 있는지 확인하세요.
    pause
    exit /b 1
)

echo ========================================
echo   서버 정보
echo ========================================
echo   URL: http://localhost:8080
echo   Swagger UI: http://localhost:8080/swagger-ui.html
echo   API Docs: http://localhost:8080/v3/api-docs
echo ========================================
echo.
echo [중요] 서버 시작 완료 확인:
echo   - 터미널에서 "Started ApiApplication" 메시지를 확인하세요
echo   - 또는 브라우저에서 http://localhost:8080/swagger-ui.html 접속
echo.
echo 종료하려면 Ctrl+C를 누르세요
echo.

REM Gateway 서버 실행 (Gradle)
call gradlew bootRun

:end
if errorlevel 1 (
    echo.
    echo [ERROR] 서버 실행 중 오류가 발생했습니다.
    pause
)
