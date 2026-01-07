# API Gateway 서버 실행 스크립트 (PowerShell)
# .env 파일을 로드하고 서버를 실행합니다

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  API Gateway 서버 시작" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 프로젝트 루트로 이동
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
$projectRoot = Get-Location
Write-Host "프로젝트 루트: $projectRoot"

# .env 파일 로드
$envFile = Join-Path (Split-Path -Parent $projectRoot) ".env"
if (Test-Path $envFile) {
    Write-Host ""
    Write-Host ".env 파일 로드 중: $envFile" -ForegroundColor Yellow
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        # 주석이나 빈 줄 건너뛰기
        if ($line -and -not $line.StartsWith("#")) {
            if ($line -match '^\s*([^#][^=]*?)\s*=\s*(.*?)\s*$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                if ($key -and $value) {
                    [Environment]::SetEnvironmentVariable($key, $value, "Process")
                    Write-Host "  $key = $($value.Substring(0, [Math]::Min(20, $value.Length)))..." -ForegroundColor Gray
                }
            }
        }
    }
    Write-Host ".env 파일 로드 완료" -ForegroundColor Green
    Write-Host ""
    Write-Host "로드된 DB 환경 변수 확인:" -ForegroundColor Cyan
    Write-Host "  SPRING_DATASOURCE_URL: $([Environment]::GetEnvironmentVariable('SPRING_DATASOURCE_URL', 'Process'))" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "[경고] .env 파일을 찾을 수 없습니다: $envFile" -ForegroundColor Yellow
    Write-Host "환경 변수가 설정되지 않았을 수 있습니다." -ForegroundColor Yellow
}
Write-Host ""

# Java 버전 확인
try {
    $javaVersion = java -version 2>&1 | Select-Object -First 1
    Write-Host "Java 버전: $javaVersion" -ForegroundColor Cyan
} catch {
    Write-Host "[ERROR] Java를 찾을 수 없습니다!" -ForegroundColor Red
    Write-Host "Java 21 이상이 설치되어 있고 PATH에 추가되어 있는지 확인하세요." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  서버 정보" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  URL: http://localhost:8080" -ForegroundColor Cyan
Write-Host "  Swagger UI: http://localhost:8080/swagger-ui.html" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8080/v3/api-docs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[중요] 서버 시작 완료 확인:" -ForegroundColor Yellow
Write-Host "  - 터미널에서 'Started ApiApplication' 메시지를 확인하세요" -ForegroundColor Yellow
Write-Host "  - 또는 브라우저에서 http://localhost:8080/swagger-ui.html 접속" -ForegroundColor Yellow
Write-Host ""
Write-Host "종료하려면 Ctrl+C를 누르세요" -ForegroundColor Yellow
Write-Host ""

# Gateway 서버 실행
try {
    & .\gradlew bootRun
} catch {
    Write-Host ""
    Write-Host "[ERROR] 서버 실행 중 오류가 발생했습니다." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
