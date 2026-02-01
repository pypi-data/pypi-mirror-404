# Cortex MCP - Claude Desktop 연동 가이드

이 가이드는 Cortex MCP를 Claude Desktop과 연동하는 방법을 안내합니다.

## 목차
1. [설치 요구사항](#설치-요구사항)
2. [Cortex 설치](#cortex-설치)
3. [라이센스 활성화](#라이센스-활성화)
4. [Claude Desktop 설정](#claude-desktop-설정)
5. [동작 확인](#동작-확인)
6. [트러블슈팅](#트러블슈팅)

---

## 설치 요구사항

- **Python**: 3.11 이상
- **Claude Desktop**: 최신 버전 (MCP 지원)
- **운영체제**: macOS, Windows, Linux

### Python 버전 확인

```bash
python3 --version
# 출력: Python 3.11.x 이상이어야 함
```

---

## Cortex 설치

### 1. PyPI에서 설치

```bash
pip install cortex-mcp
```

### 2. 설치 확인

```bash
cortex-mcp --help
```

**예상 출력:**
```
[Cortex] Memory directory: /Users/your-name/.cortex/memory
[Cortex] Auto-compressor started
...
```

---

## 라이센스 활성화

Cortex는 라이센스 인증이 필요합니다.

### 베타 테스터 라이센스 발급

베타 테스터에게는 1년 무료 Pro 라이센스가 제공됩니다.

1. **라이센스 키 받기**: 베타 프로그램 가입 후 이메일로 라이센스 키 수령
2. **라이센스 활성화**:

```bash
python -m cortex_mcp.scripts.license_cli activate --key YOUR-LICENSE-KEY
```

**예상 출력:**
```
[Cortex] License activated successfully
[Cortex] License Type: Beta_1Year_Free
[Cortex] Valid Until: 2027-01-02
```

### 환경 변수 설정 (선택사항)

라이센스 키를 환경 변수로 설정할 수도 있습니다:

**macOS/Linux:**
```bash
export CORTEX_LICENSE_KEY="YOUR-LICENSE-KEY"
```

**Windows (PowerShell):**
```powershell
$env:CORTEX_LICENSE_KEY="YOUR-LICENSE-KEY"
```

---

## Claude Desktop 설정

### 1. Claude Desktop 설정 파일 찾기

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### 2. 설정 파일 편집

`claude_desktop_config.json` 파일을 열고 다음 내용을 추가합니다:

```json
{
  "mcpServers": {
    "cortex": {
      "command": "python",
      "args": ["-m", "cortex_mcp.main"],
      "env": {
        "CORTEX_LICENSE_KEY": "YOUR-LICENSE-KEY"
      }
    }
  }
}
```

**주의사항:**
- `YOUR-LICENSE-KEY`를 실제 라이센스 키로 교체하세요
- 기존에 다른 MCP 서버가 설정되어 있다면, `mcpServers` 객체 안에 `cortex` 항목을 추가하세요

**예시 (여러 MCP 서버):**
```json
{
  "mcpServers": {
    "other-server": {
      "command": "node",
      "args": ["path/to/server.js"]
    },
    "cortex": {
      "command": "python",
      "args": ["-m", "cortex_mcp.main"],
      "env": {
        "CORTEX_LICENSE_KEY": "YOUR-LICENSE-KEY"
      }
    }
  }
}
```

### 3. Claude Desktop 재시작

설정 파일을 저장한 후 Claude Desktop을 완전히 종료하고 다시 실행합니다.

---

## 동작 확인

### 1. MCP 연결 확인

Claude Desktop을 실행하고 대화창에서 다음을 확인합니다:

- 좌측 하단에 "MCP" 아이콘 또는 표시가 있는지 확인
- MCP 서버 목록에서 "cortex"가 활성화되어 있는지 확인

### 2. Cortex 도구 사용 테스트

Claude에게 다음과 같이 요청해보세요:

```
프로젝트를 초기화해줘
```

Claude가 `initialize_context` 도구를 호출하면 Cortex가 정상 작동하는 것입니다.

### 3. 기본 명령어 테스트

```
현재 활성 맥락 요약을 보여줘
```

Claude가 `get_active_summary` 도구를 호출하고 결과를 보여주면 성공입니다.

---

## 트러블슈팅

### 문제 1: "Python 3.11+ required" 에러

**원인**: Python 버전이 3.11 미만

**해결**:
1. Python 3.11 이상 설치
2. `claude_desktop_config.json`에서 `python3.11` 경로 명시:

```json
{
  "mcpServers": {
    "cortex": {
      "command": "/usr/local/bin/python3.11",
      "args": ["-m", "cortex_mcp.main"],
      "env": {
        "CORTEX_LICENSE_KEY": "YOUR-LICENSE-KEY"
      }
    }
  }
}
```

### 문제 2: "No valid license found" 에러

**원인**: 라이센스 키가 설정되지 않았거나 만료됨

**해결**:
1. 라이센스 키 확인:
   ```bash
   python -m cortex_mcp.scripts.license_cli status
   ```

2. 라이센스 재활성화:
   ```bash
   python -m cortex_mcp.scripts.license_cli activate --key YOUR-LICENSE-KEY
   ```

3. `claude_desktop_config.json`의 `CORTEX_LICENSE_KEY` 확인

### 문제 3: MCP 서버가 연결되지 않음

**원인**: Claude Desktop이 설정 파일을 읽지 못함

**해결**:
1. 설정 파일 경로가 올바른지 확인
2. JSON 문법 오류 확인 (쉼표, 중괄호 등)
3. Claude Desktop을 완전히 종료 후 재시작
4. 로그 확인:
   - macOS: `~/Library/Logs/Claude/mcp*.log`
   - Windows: `%LOCALAPPDATA%\Claude\logs\mcp*.log`

### 문제 4: "GitPython not installed" 경고

**원인**: 선택적 의존성 미설치 (Phase 9.2 기능)

**해결** (선택사항):
```bash
pip install gitpython
```

**참고**: GitPython이 없어도 Cortex의 핵심 기능은 정상 작동합니다.

### 문제 5: ChromaDB 에러

**원인**: ChromaDB 초기화 실패

**해결**:
1. ChromaDB 재설치:
   ```bash
   pip install --upgrade chromadb
   ```

2. 기존 데이터 삭제 후 재초기화:
   ```bash
   rm -rf ~/.cortex/chroma_db
   ```

---

## 로그 확인

문제 발생 시 Cortex 로그를 확인하세요:

```bash
# macOS/Linux
tail -f ~/.cortex/logs/cortex.log

# Windows
type %USERPROFILE%\.cortex\logs\cortex.log
```

---

## 추가 도움

- **GitHub Issues**: https://github.com/syab726/cortex/issues
- **이메일**: support@cortex-mcp.com
- **Discord**: https://discord.gg/cortex-mcp (베타 테스터 전용)

---

## 다음 단계

Cortex 연동이 완료되었다면:

1. **베타 테스트 가이드 읽기**: `BETA_TEST_GUIDE.md`
2. **API 레퍼런스 확인**: `API_REFERENCE.md`
3. **피드백 제출**: 문제 발견 시 GitHub Issues 또는 피드백 시스템 사용

Happy Testing!
