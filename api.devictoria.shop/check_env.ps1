# 환경 변수 확인 스크립트
Write-Host "환경 변수 확인" -ForegroundColor Green
Write-Host ""

$envFile = Join-Path (Split-Path -Parent $PSScriptRoot) ".env"
Write-Host ".env 파일 경로: $envFile" -ForegroundColor Yellow
Write-Host ""

if (Test-Path $envFile) {
    Write-Host ".env 파일 내용:" -ForegroundColor Cyan
    Get-Content $envFile | Select-String -Pattern "SPRING_DATASOURCE|DB_" | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
    Write-Host ""
    
    # 환경 변수 로드
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            if ($line -match '^\s*([^#][^=]*?)\s*=\s*(.*?)\s*$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                if ($key -and $value) {
                    [Environment]::SetEnvironmentVariable($key, $value, "Process")
                }
            }
        }
    }
    
    Write-Host "로드된 환경 변수:" -ForegroundColor Cyan
    Write-Host "  SPRING_DATASOURCE_URL: $([Environment]::GetEnvironmentVariable('SPRING_DATASOURCE_URL', 'Process'))" -ForegroundColor White
    Write-Host "  SPRING_DATASOURCE_USERNAME: $([Environment]::GetEnvironmentVariable('SPRING_DATASOURCE_USERNAME', 'Process'))" -ForegroundColor White
    Write-Host "  SPRING_DATASOURCE_PASSWORD: $([Environment]::GetEnvironmentVariable('SPRING_DATASOURCE_PASSWORD', 'Process'))" -ForegroundColor White
} else {
    Write-Host "[오류] .env 파일을 찾을 수 없습니다!" -ForegroundColor Red
}

