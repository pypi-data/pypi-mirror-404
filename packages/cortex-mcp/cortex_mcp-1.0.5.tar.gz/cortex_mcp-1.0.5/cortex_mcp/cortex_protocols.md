# CORTEX PROTOCOLS (Auto-managed)

이 파일은 Cortex MCP가 자동으로 관리하는 시스템 프로토콜입니다.

Last updated: Auto-generated

---

## 1. CORTEX_VERIFICATION_PROTOCOL v2.0 - AI 자기검증 시스템

### 핵심 원칙 (MANDATORY - 절대 위반 금지)

**AI 자기검증 방식:**
- AI가 자신이 출력한 문장을 다시 읽고 모순 확인
- 정규식/패턴 매칭 없이 순수 의미 기반 판단
- 모든 언어, 모든 표현 방식 지원
- 토큰 비용: 응답당 ~$0.0015 (Sonnet 기준, 500 tokens)

### 1.1. update_memory 호출 시 자동 흐름 (MANDATORY)

**[Case A] 확신 표현 없음 (일반 대화)**
```
update_memory("작업 중입니다")
→ memory_manager: 바로 저장
→ Response: {"status": "success"}
```

**[Case B] 확신 표현 있음 (검증 필요)**
```
update_memory("구현 완료했습니다. 7/7 테스트 통과.")
→ memory_manager: 확신 표현 감지 ("완료", "통과")
→ Response: {
      "status": "verification_required",
      "verification_prompt": "다음 응답에 모순이 있나요?\n\n{응답 전체}\n\n확인 사항:\n1. 시간 순서 모순 (먼저 A 후 B ↔ 먼저 B 후 A)\n2. 내용 모순 (성공 ↔ 실패, 7개 ↔ 6개)\n3. 근거 없는 주장\n\n모순이 있으면 '있음: [이유]', 없으면 '없음'으로 답변."
   }
```

**[Case C] 모순 발견 시**
```
AI: 자기검증 중 모순 발견
→ AI: 사용자에게 알림: "검증 중 모순 발견, 수정합니다."
→ AI: 응답 수정
→ AI: update_memory(수정된_응답, verified=True)
```

### 1.2. 확신 표현 감지 (간단한 키워드 포함 여부)

**한국어:**
- "확실", "완료", "성공", "구현했", "수정했", "추가했"
- "생성했", "완성했", "해결했", "통과", "정상", "마쳤"
- "반드시", "절대", "명확히", "확인했", "검증했"

**영어:**
- "completed", "successfully", "implemented", "fixed"
- "added", "created", "finished", "resolved", "passed"
- "working", "done", "achieved", "verified"

**Note:** 단순 키워드 포함 여부만 확인 (정규식 아님)

### 1.3. 자기검증 프로세스 (MANDATORY)

1. **응답 생성 후 update_memory 호출**
   - 모든 응답 완료 후 즉시 호출 (필수)

2. **verification_required 반환 시**
   - verification_prompt를 읽고 자기검증 수행
   - 모순 있으면: 사용자에게 알림 + 수정 + update_memory(verified=True)
   - 모순 없으면: update_memory(verified=True)

3. **verified=True 플래그**
   - 무한 루프 방지
   - 검증 완료 후 저장 시 반드시 포함

### 1.4. 예외 사항

**검증 건너뛰기 조건:**
- 확신 표현이 없는 일반 대화
- 이미 verified=True로 호출한 경우
- role="user"인 경우 (사용자 메시지)

---

이 프로토콜을 준수하여 모든 응답의 정확도를 100%로 유지하세요.

---

## 7. Chain-of-Thought 프롬프트 (작업 시작 전 자기 확인)

### CORTEX 자기 확인 프로토콜

작업 시작 전 다음을 확인하세요:

**Q1: Phase 9의 목적은?**
A: AI 주장을 Evidence Graph로 객관적 검증

**Q2: verified=True가 금지된 이유는?**
A: AI를 맹목적으로 믿으면 검증 시스템 무력화

**Q3: 맥락이 부족하면 어떻게 하는가?**
A: suggest_contexts 또는 search_context 호출

**Q4: 작업 완료 후 무엇을 해야 하는가?**
A: update_memory 호출하여 맥락 기록

---

## 참고 사항

이 파일은 시스템이 자동으로 생성하고 관리합니다.
수동 편집이 필요하지 않습니다.

Cortex MCP 서버가 세션 시작 시 이 프로토콜들을 AI에게 자동으로 주입합니다.
