# GitHub 계정 교체 전략 가이드

## 1. Git 사용자 정보 변경

### 전역 설정 변경
```bash
git config --global user.name "본인의 이름"
git config --global user.email "본인의 이메일"
```

### 특정 저장소만 변경 (해당 저장소 디렉토리에서)
```bash
git config user.name "본인의 이름"
git config user.email "본인의 이메일"
```

## 2. Windows Credential Manager에서 GitHub 인증 정보 삭제

### 방법 1: 명령줄로 삭제
```powershell
# GitHub 관련 인증 정보 삭제
cmdkey /delete:LegacyGeneric:target=git:https://github.com

# Git Credential Manager에 저장된 정보도 확인
cmdkey /delete:git:https://github.com
```

### 방법 2: GUI로 삭제
1. Windows 검색에서 "자격 증명 관리자" 또는 "Credential Manager" 검색
2. "Windows 자격 증명" 탭 선택
3. `git:https://github.com` 항목 찾기
4. 항목을 클릭하고 "제거" 또는 "편집" 선택

## 3. SSH 키 교체 (SSH 사용 시)

### 기존 SSH 키 확인
```bash
# SSH 키 목록 확인
ls ~/.ssh/

# GitHub에 등록된 SSH 키 확인
cat ~/.ssh/id_rsa.pub  # 또는 id_ed25519.pub
```

### 새 SSH 키 생성 (필요한 경우)
```bash
# 새 SSH 키 생성
ssh-keygen -t ed25519 -C "본인의이메일@example.com"

# 또는 RSA 키 생성
ssh-keygen -t rsa -b 4096 -C "본인의이메일@example.com"
```

### GitHub에 새 SSH 키 등록
1. 생성된 공개 키 복사
```bash
cat ~/.ssh/id_ed25519.pub
# 또는 Windows에서
Get-Content ~/.ssh/id_ed25519.pub | clip
```

2. GitHub 웹사이트에서:
   - Settings → SSH and GPG keys → New SSH key
   - 공개 키 붙여넣기

## 4. Personal Access Token (PAT) 사용 (HTTPS 사용 시)

### 새 토큰 생성
1. GitHub 웹사이트 → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" 클릭
3. 필요한 권한 선택 (repo, workflow 등)
4. 토큰 생성 후 복사 (한 번만 표시됨!)

### 토큰으로 인증
```bash
# 다음 push/pull 시도 시 자격 증명 입력
# Username: 본인의 GitHub 사용자명
# Password: 생성한 Personal Access Token
```

## 5. GitHub CLI 재인증 (gh CLI 사용 시)

```bash
# 기존 인증 제거
gh auth logout

# 새 계정으로 로그인
gh auth login
```

## 6. Git Credential Manager 재설정

```bash
# 자격 증명 헬퍼 확인
git config --global credential.helper

# Windows의 경우 보통 manager-core 또는 wincred
# 자격 증명 캐시 지우기
git credential-manager-core erase
# 또는
git credential reject https://github.com
```

## 7. 기존 저장소의 원격 URL 확인 및 변경

```bash
# 현재 원격 URL 확인
git remote -v

# 원격 URL 변경 (필요한 경우)
git remote set-url origin https://github.com/본인계정/저장소명.git
# 또는 SSH 사용 시
git remote set-url origin git@github.com:본인계정/저장소명.git
```

## 8. 최종 확인

```bash
# Git 설정 확인
git config --global --list | Select-String -Pattern "user"

# 인증 테스트
git ls-remote https://github.com/본인계정/테스트저장소.git
# 또는 SSH 사용 시
ssh -T git@github.com
```

## 주의사항

1. **기존 커밋 히스토리**: 이미 커밋된 내용의 작성자 정보는 변경되지 않습니다. 
   - 필요시 `git filter-branch` 또는 `git filter-repo` 사용 (주의 필요)

2. **협업 중인 저장소**: 팀과 협의 후 변경하세요.

3. **보안**: Personal Access Token은 안전하게 보관하고 절대 공유하지 마세요.

4. **여러 계정 사용**: 특정 저장소만 다른 계정을 사용하려면 전역 설정 대신 로컬 설정을 사용하세요.

