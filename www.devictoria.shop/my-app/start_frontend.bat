@echo off
chcp 65001 >nul
title Next.js Frontend Server
color 0B

echo ========================================
echo   Next.js 프론트엔드 서버 시작
echo ========================================
echo.

REM 배치 파일이 있는 디렉토리로 이동
cd /d "%~dp0"
set PROJECT_ROOT=%CD%
echo [1/3] 프로젝트 루트: %PROJECT_ROOT%
echo.

echo [2/3] Node.js 및 패키지 매니저 확인 중...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js를 찾을 수 없습니다!
    echo Node.js가 설치되어 있고 PATH에 추가되어 있는지 확인하세요.
    pause
    exit /b 1
)
node --version

REM pnpm이 설치되어 있는지 확인, 없으면 npm 사용
pnpm --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] pnpm을 찾을 수 없습니다. npm을 사용합니다.
    set PACKAGE_MANAGER=npm
) else (
    echo [INFO] pnpm을 사용합니다.
    set PACKAGE_MANAGER=pnpm
)
echo.

echo [3/3] 서버 시작 중...
echo.
echo ========================================
echo   서버 정보
echo ========================================
echo   URL: http://localhost:3000
echo   Diffusion 페이지: http://localhost:3000/diffusion
echo ========================================
echo.
echo 종료하려면 Ctrl+C를 누르세요
echo.

REM node_modules가 없으면 의존성 설치
if not exist "node_modules" (
    echo [INFO] node_modules를 찾을 수 없습니다. 의존성을 설치합니다...
    %PACKAGE_MANAGER% install
    if errorlevel 1 (
        echo [ERROR] 의존성 설치 중 오류가 발생했습니다.
        pause
        exit /b 1
    )
    echo.
)

REM 개발 서버 시작
%PACKAGE_MANAGER% run dev

if errorlevel 1 (
    echo.
    echo [ERROR] 서버 실행 중 오류가 발생했습니다.
    pause
)

