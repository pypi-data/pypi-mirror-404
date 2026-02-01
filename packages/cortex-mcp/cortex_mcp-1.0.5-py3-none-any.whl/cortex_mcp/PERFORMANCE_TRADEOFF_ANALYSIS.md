# 성능 vs 책임성 Trade-off 분석
## "무거워지는 툴" 우려에 대한 객관적 검토

**질문**: 검증 레이어 추가가 툴을 너무 무겁게 만드는가?
**우려**: 토큰 소모 증가, 응답 지연 → 사용자 이탈

---

## 1. 현재 제안된 개선의 실제 비용

### CRITICAL: 할루시네이션 검증 강제

**현재 방식**
```python
# 사용자 요청 → AI 응답 (1회 LLM 호출)
# update_memory() 저장
# 끝
```

**제안 방식 (Option 1: 전체 자동 검증)**
```python
# 사용자 요청 → AI 응답 (1회 LLM 호출)
# update_memory() 저장
# auto_verify() 자동 실행 (1회 LLM 호출)  ← 추가
# 끝
```

**비용 계산**
```
입력 토큰: 기존 응답 (평균 500 tokens)
출력 토큰: 검증 결과 (평균 200 tokens)

비용 증가:
- Sonnet 4.5 기준: $0.003/1K input + $0.015/1K output
- 응답당 추가 비용: $0.0045
- 100회 사용 시: $0.45 추가

시간 증가:
- 검증 LLM 호출: +2-3초
- 총 응답 시간: 5초 → 7-8초 (60% 증가)
```

**문제점**
- ❌ 모든 응답마다 검증 → **과도함**
- ❌ 간단한 질문("안녕?")도 검증 → **낭비**
- ❌ 응답 시간 60% 증가 → **사용자 체감 나쁨**

### HIGH: Reference History 강제

**비용**
```
추가 비용: 없음 (기록만 추가)
시간 증가: 거의 없음 (<100ms)
```

**문제점**
- ✅ 비용 거의 없음
- ✅ 강제할 만한 가치 있음

### HIGH: 브랜치 생성 검증

**비용**
```
추가 비용: 없음 (파일 시스템 체크만)
시간 증가: <50ms
```

**문제점**
- ✅ 비용 거의 없음
- ✅ 중요한 작업이므로 검증 가치 있음

### HIGH: Backup 복구 검증

**비용**
```
추가 비용: 없음 (해시 계산만)
시간 증가: <200ms (파일 많으면 더 걸림)
```

**문제점**
- ✅ 비용 적음
- ✅ 복구는 드물게 발생 → 허용 가능

### MEDIUM: Plan B 암묵적 거부 감지

**비용**
```
추가 비용: git log 파싱 비용 (무시 가능)
시간 증가: <100ms
```

**문제점**
- ✅ 비용 매우 적음
- ⚠️ 복잡도 증가 (Git 의존성)

---

## 2. 실제 문제: 할루시네이션 검증만 무겁다

### 비용 비교표

| 개선 항목 | 토큰 증가 | 시간 증가 | 비용 증가 | 영향 |
|----------|----------|----------|----------|------|
| **할루시네이션 검증 (전체)** | **+700** | **+2-3초** | **$0.0045/회** | **🔴 HIGH** |
| Reference History 강제 | +0 | +50ms | $0 | 🟢 NONE |
| 브랜치 생성 검증 | +0 | +50ms | $0 | 🟢 NONE |
| Backup 복구 검증 | +0 | +200ms | $0 | 🟢 LOW |
| Plan B 개선 | +0 | +100ms | $0 | 🟢 LOW |

**결론**: 할루시네이션 검증만 무겁다. 나머지는 거의 영향 없음.

---

## 3. 할루시네이션 검증 대안

### Option 1: 전체 자동 검증 (현재 제안)
```
장점: 완벽한 책임성
단점: 비용 2배, 시간 60% 증가
판단: ❌ 너무 무거움
```

### Option 2: 선택적 검증 (추천)
```python
# 중요한 작업만 검증
VERIFY_TRIGGERS = [
    "file_modified",      # 파일 수정
    "git_commit",         # Git 커밋
    "branch_created",     # 브랜치 생성
    "implementation_complete"  # 구현 완료 주장
]

def update_memory(project_id, branch_id, content, role="assistant"):
    # 1. 저장
    memory_manager.update_memory(...)

    # 2. 중요한 작업인지 판단
    if should_verify(content):
        # 검증 수행
        verify_response(content)
    else:
        # 검증 스킵
        pass
```

**비용**
```
검증 비율: 20% (간단한 질문 80%, 중요 작업 20%)
비용 증가: $0.0045 × 0.2 = $0.0009/회
시간 증가: 평균 +0.6초 (20%만 검증)
```

**판단**: ✅ 합리적

### Option 3: 백그라운드 검증
```python
# 응답 후 비동기로 검증
def update_memory(project_id, branch_id, content):
    # 1. 즉시 저장 (사용자는 바로 다음 작업)
    memory_manager.update_memory(...)

    # 2. 백그라운드에서 검증
    asyncio.create_task(verify_response_async(content))
```

**장점**: 사용자는 지연 느끼지 않음
**단점**: 검증 결과를 나중에 봐야 함

**판단**: ✅ 좋은 대안

### Option 4: 사용자 설정
```python
# 사용자가 검증 레벨 선택
VERIFICATION_LEVELS = {
    "none": 0,      # 검증 안 함
    "light": 0.2,   # 중요한 것만
    "medium": 0.5,  # 절반
    "strict": 1.0   # 모든 응답
}
```

**판단**: ✅ 최선의 선택 (사용자가 결정)

---

## 4. 경쟁사 비교

### Cursor (AI Code Editor)
- **검증**: 없음
- **속도**: 매우 빠름
- **정확도**: 낮음 (사용자 불만 많음)

### GitHub Copilot
- **검증**: 없음
- **속도**: 빠름
- **정확도**: 중간

### Replit Agent
- **검증**: 없음
- **속도**: 빠름
- **정확도**: 낮음

### **Cortex가 차별화될 수 있는 지점**
- 경쟁사들은 모두 "빠르지만 부정확"
- Cortex는 "조금 느리지만 책임있음"
- **하지만**: 너무 느리면 사용자 이탈

**균형점**: 선택적 검증 + 사용자 설정

---

## 5. 실제 사용 시나리오 분석

### 시나리오 1: 간단한 질문
```
User: "이 함수 뭐 하는 거야?"
AI: "이 함수는 X를 합니다."
```

**검증 필요?**: ❌ 아니오
**이유**: 코드 읽기만 함, 변경 없음

### 시나리오 2: 파일 수정
```
User: "auth.py에 로그인 기능 추가해줘"
AI: "auth.py에 login() 함수를 추가했습니다."
```

**검증 필요?**: ✅ 예
**이유**: 파일 변경, 구현 완료 주장

### 시나리오 3: 버그 수정
```
User: "이 버그 수정해줘"
AI: "버그를 수정했습니다. line 42를 변경했습니다."
```

**검증 필요?**: ✅ 예
**이유**: 파일 변경, 버그 수정 주장

### 시나리오 4: 일반 대화
```
User: "고마워"
AI: "천만에요! 더 도와드릴 게 있나요?"
```

**검증 필요?**: ❌ 아니오
**이유**: 대화만 함, 작업 없음

### 결론
```
검증 필요한 비율: 20-30%
검증 불필요한 비율: 70-80%

→ 선택적 검증으로 비용 80% 절감 가능
```

---

## 6. 최종 권장사항

### ✅ 꼭 해야 하는 것 (비용 거의 없음)

1. **Reference History 강제** (HIGH)
   - 비용: 0
   - 시간: +50ms
   - 가치: 높음 (출처 추적)

2. **브랜치 생성 검증** (HIGH)
   - 비용: 0
   - 시간: +50ms
   - 가치: 높음 (맥락 분리 보장)

3. **Backup 복구 검증** (HIGH)
   - 비용: 0
   - 시간: +200ms
   - 가치: 높음 (복구는 드물게 발생)

### ⚠️ 신중하게 해야 하는 것

4. **할루시네이션 검증 강제** (CRITICAL)
   - **Option A: 전체 검증** ❌ 너무 무거움
   - **Option B: 선택적 검증** ✅ 추천
   - **Option C: 백그라운드 검증** ✅ 대안
   - **Option D: 사용자 설정** ✅ 최선

**권장**: Option D (사용자 설정) + Option B (기본값: 선택적)

### ❓ 나중에 해도 되는 것 (MEDIUM)

5. **Plan B 암묵적 거부 감지**
   - 비용: 거의 없음
   - 하지만 복잡도 증가
   - 판단: Phase 3+ (나중에)

6. **파일 잠금 메커니즘**
   - 비용: 없음
   - 하지만 필요성 낮음 (극단적 케이스)
   - 판단: Phase 3+ (나중에)

7. **압축 알림**
   - 비용: 없음
   - 하지만 중요도 낮음
   - 판단: Phase 3+ (나중에)

---

## 7. 구체적 구현 제안

### 할루시네이션 검증 (수정안)

```python
class VerificationConfig:
    """사용자 설정 가능한 검증 레벨"""
    LEVELS = {
        "off": {
            "enabled": False,
            "description": "검증 안 함 (가장 빠름)"
        },
        "smart": {  # 기본값
            "enabled": True,
            "triggers": [
                "file_modified",
                "git_commit",
                "branch_created",
                "implementation_complete"
            ],
            "description": "중요한 작업만 검증 (추천)"
        },
        "strict": {
            "enabled": True,
            "triggers": "*",  # 모든 응답
            "description": "모든 응답 검증 (느림, 정확함)"
        }
    }

def should_verify(content: str, level: str = "smart") -> bool:
    """검증 필요 여부 판단"""
    config = VerificationConfig.LEVELS[level]

    if not config["enabled"]:
        return False

    if config["triggers"] == "*":
        return True

    # 중요한 작업인지 판단
    for trigger in config["triggers"]:
        if trigger in content.lower():
            return True

    return False

def update_memory(project_id, branch_id, content, role="assistant"):
    """개선된 update_memory"""
    # 1. 저장
    memory_manager.update_memory(project_id, branch_id, content, role)

    # 2. 사용자 설정 확인
    user_level = get_user_verification_level(project_id)  # 기본: "smart"

    # 3. 검증 필요 여부 판단
    if should_verify(content, user_level):
        # 중요한 작업 → 검증
        result = auto_verifier.verify_response(content)

        if result["grounding_score"] < 0.7:
            # 할루시네이션 감지
            return {
                "status": "hallucination_detected",
                "message": "⚠️ 검증 실패. 재시도를 권장합니다.",
                "details": result
            }

    return {"status": "success"}
```

### 사용자 설정 UI (MCP Tool)

```python
@server.call_tool()
async def set_verification_level(
    project_id: str,
    level: Literal["off", "smart", "strict"]
) -> str:
    """검증 레벨 설정

    Args:
        level:
            - off: 검증 안 함 (가장 빠름)
            - smart: 중요한 작업만 검증 (추천, 기본값)
            - strict: 모든 응답 검증 (느림, 정확함)
    """
    set_user_verification_level(project_id, level)

    config = VerificationConfig.LEVELS[level]
    return f"검증 레벨: {level}\n{config['description']}"
```

---

## 8. 비용 비교 (최종)

### 기존 (검증 없음)
```
100회 사용 시:
- 토큰 비용: $1.50
- 평균 응답 시간: 5초
```

### 전체 검증 (Option 1)
```
100회 사용 시:
- 토큰 비용: $1.50 + $0.45 = $1.95 (30% 증가)
- 평균 응답 시간: 8초 (60% 증가)
```

### 선택적 검증 (Option 2, 추천)
```
100회 사용 시 (20%만 검증):
- 토큰 비용: $1.50 + $0.09 = $1.59 (6% 증가)
- 평균 응답 시간: 5.6초 (12% 증가)
```

### 판단
```
선택적 검증:
- 비용 증가: 6% ✅ 허용 가능
- 시간 증가: 12% ✅ 체감 낮음
- 정확도 향상: 중요 작업만 검증 ✅ 효율적
```

---

## 9. 최종 결론

### Phase 3 (MEDIUM) 작업 필요성

**해야 하는가?**
- Plan B 개선: ❓ 나중에 (복잡도 증가)
- 파일 잠금: ❓ 나중에 (극단적 케이스)
- 압축 알림: ❓ 나중에 (중요도 낮음)

**판단**: 지금 당장은 불필요. Phase Final 전에 재검토.

### HIGH 작업 필요성

**꼭 해야 하는가?**
- Reference History 강제: ✅ 예 (비용 0)
- 브랜치 생성 검증: ✅ 예 (비용 0)
- Backup 복구 검증: ✅ 예 (비용 거의 0)

**판단**: 반드시 해야 함. 무겁지 않음.

### CRITICAL 작업 (할루시네이션 검증)

**전체 검증?**: ❌ 너무 무거움
**선택적 검증?**: ✅ 추천 (비용 6% 증가, 시간 12% 증가)
**사용자 설정?**: ✅ 최선 (사용자가 선택)

### 무거워지는가?

**객관적 답변**:
- HIGH 작업들: ✅ 거의 영향 없음 (시간 +50-200ms)
- CRITICAL (선택적 검증): ✅ 허용 가능 (비용 +6%, 시간 +12%)
- CRITICAL (전체 검증): ❌ 너무 무거움 (비용 +30%, 시간 +60%)

### 최종 권장

1. **즉시 적용** (HIGH 3개)
   - Reference History 강제
   - 브랜치 생성 검증
   - Backup 복구 검증
   - **영향**: 거의 없음 ✅

2. **선택적 적용** (CRITICAL)
   - 할루시네이션 검증: 선택적 + 사용자 설정
   - 기본값: "smart" (중요한 것만)
   - **영향**: 비용 +6%, 시간 +12% ✅

3. **보류** (MEDIUM)
   - Plan B 개선, 파일 잠금, 압축 알림
   - Phase Final 전에 재검토

### 사용자 이탈 위험?

**분석**:
- 비용 +6%: ✅ 무시 가능
- 시간 +12% (0.6초): ✅ 체감 낮음
- 정확도 향상: ✅ 가치 큼

**판단**: 이탈 위험 낮음. 오히려 정확도 향상으로 만족도 증가 예상.

---

*분석 완료: 2025-12-23*
