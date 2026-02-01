#!/usr/bin/env python3
"""
SessionStart Hook - 세션 시작 시 자동 프로젝트 초기화

Claude Code 세션이 시작될 때 호출되어:
1. 프로젝트 초기화 여부 확인
2. 미초기화 시 initialize_context 호출 제안
3. 기초기화 시 활성 브랜치 요약 로드
"""

import sys
import uuid
from datetime import datetime

# 상위 모듈 import를 위한 경로 설정
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cortex_mcp.hooks.runner import (
    HookContext,
    generate_mcp_tool_call,
    log_hook_activity,
    output_system_message,
    output_tool_suggestion,
)

# Memory Manager import (자동 맥락 로드용)
from cortex_mcp.core.memory_manager import MemoryManager

# Phase 9.2: AI 자기검증 프로토콜 상수
CORTEX_VERIFICATION_PROTOCOL_V2 = """[CORTEX_VERIFICATION_PROTOCOL v2.0 - AI 자기검증 시스템]

## 핵심 원칙 (MANDATORY - 절대 위반 금지)

**AI 자기검증 방식:**
- AI가 자신이 출력한 문장을 다시 읽고 모순 확인
- 정규식/패턴 매칭 없이 순수 의미 기반 판단
- 모든 언어, 모든 표현 방식 지원
- 토큰 비용: 응답당 ~$0.0015 (Sonnet 기준, 500 tokens)

## 1. update_memory 호출 시 자동 흐름 (MANDATORY)

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
      "verification_prompt": "다음 응답에 모순이 있나요?\\n\\n{응답 전체}\\n\\n확인 사항:\\n1. 시간 순서 모순 (먼저 A 후 B ↔ 먼저 B 후 A)\\n2. 내용 모순 (성공 ↔ 실패, 7개 ↔ 6개)\\n3. 근거 없는 주장\\n\\n모순이 있으면 '있음: [이유]', 없으면 '없음'으로 답변."
   }
```

**[Case C] 모순 발견 시**
```
AI: 자기검증 중 모순 발견
→ AI: 사용자에게 알림: "검증 중 모순 발견, 수정합니다."
→ AI: 응답 수정
→ AI: update_memory(수정된_응답, verified=True)
```

## 2. 확신 표현 감지 (간단한 키워드 포함 여부)

**한국어:**
- "확실", "완료", "성공", "구현했", "수정했", "추가했"
- "생성했", "완성했", "해결했", "통과", "정상", "마쳤"
- "반드시", "절대", "명확히", "확인했", "검증했"

**영어:**
- "completed", "successfully", "implemented", "fixed"
- "added", "created", "finished", "resolved", "passed"
- "working", "done", "achieved", "verified"

**Note:** 단순 키워드 포함 여부만 확인 (정규식 아님)

## 3. 자기검증 프로세스 (MANDATORY)

1. **응답 생성 후 update_memory 호출**
   - 모든 응답 완료 후 즉시 호출 (필수)

2. **verification_required 반환 시**
   - verification_prompt를 읽고 자기검증 수행
   - 모순 있으면: 사용자에게 알림 + 수정 + update_memory(verified=True)
   - 모순 없으면: update_memory(verified=True)

3. **verified=True 플래그**
   - 무한 루프 방지
   - 검증 완료 후 저장 시 반드시 포함

## 4. 예외 사항

**검증 건너뛰기 조건:**
- 확신 표현이 없는 일반 대화
- 이미 verified=True로 호출한 경우
- role="user"인 경우 (사용자 메시지)

---

이 프로토콜을 준수하여 모든 응답의 정확도를 100%로 유지하세요.
"""


def main():
    """SessionStart Hook 메인 로직"""
    ctx = HookContext()

    # 세션 ID 생성
    session_id = str(uuid.uuid4())[:8]
    ctx.state["session_id"] = session_id
    ctx.state["project_id"] = ctx.project_id
    ctx.state["last_activity"] = datetime.utcnow().isoformat()

    ctx.log(
        "SessionStart",
        "session_started",
        {"session_id": session_id, "project_id": ctx.project_id, "project_path": ctx.project_path},
    )

    # Phase 9.2: AI 자기검증 프로토콜은 이제 cortex_protocols.md에서 관리
    # output_system_message(CORTEX_VERIFICATION_PROTOCOL_V2) - REMOVED
    ctx.log(
        "SessionStart",
        "verification_protocol_delegated",
        {"managed_by": "cortex_protocols.md", "injection_time": datetime.utcnow().isoformat()},
    )

    if not ctx.is_initialized:
        # 프로젝트 미초기화 - 초기화 제안
        ctx.state["initialized"] = False
        ctx.save()

        # System Prompt에 초기화 안내 주입
        init_message = f"""[CORTEX_INIT_REQUIRED]

Cortex 장기 기억 시스템이 이 프로젝트에 처음 연결되었습니다.

프로젝트: {ctx.project_path}
프로젝트 ID: {ctx.project_id}

초기 맥락 스캔 모드를 선택해주세요:

1. [FULL] 전체 심층 분석
   - 모든 소스 코드 분석
   - 토큰 소모 높음 (대규모 프로젝트 시 비용 발생 가능)

2. [LIGHT] 핵심 파일만 스캔 (권장)
   - README, 설정 파일, 진입점만 분석
   - 빠른 시작 가능

3. [NONE] 스캔 건너뛰기
   - 단순 작업 시 선택

사용자에게 위 옵션을 안내하고 선택을 받은 후 initialize_context를 호출하세요."""

        output_system_message(init_message)

        # 초기화 도구 호출 제안
        tool_call = generate_mcp_tool_call(
            "initialize_context",
            {
                "project_id": ctx.project_id,
                "project_path": ctx.project_path,
                "scan_mode": "LIGHT",  # 기본값
            },
        )
        output_tool_suggestion([tool_call])

    else:
        # 이미 초기화됨 - 활성 브랜치 요약 자동 로드
        ctx.state["initialized"] = True
        active_branch = ctx.active_branch

        if active_branch:
            ctx.state["active_branch"] = active_branch

            # Memory Manager를 사용하여 직접 요약 로드 (자동 실행)
            try:
                mem_mgr = MemoryManager()
                result = mem_mgr.get_active_summary(ctx.project_id)

                if result.get("success"):
                    summary = result.get("summary", "")
                    branch_topic = result.get("branch_topic", "")

                    ctx.save()

                    # 요약 정보는 이제 cortex_prompt.md에서 관리
                    # output_system_message(context_message) - REMOVED (cortex_prompt.md가 대신 처리)

                    ctx.log(
                        "SessionStart",
                        "context_auto_loaded",
                        {
                            "branch_id": active_branch,
                            "branch_topic": branch_topic,
                            "summary_length": len(summary),
                            "auto_loaded": True,
                        },
                    )
                else:
                    # 요약 로드 실패
                    ctx.save()
                    error_msg = result.get("error", "Unknown error")
                    output_system_message(
                        f"[CORTEX_WARNING] 맥락 자동 로드 실패: {error_msg}\n"
                        f"수동으로 get_active_summary를 호출하세요."
                    )
                    ctx.log(
                        "SessionStart",
                        "context_load_failed",
                        {"error": error_msg, "branch_id": active_branch},
                    )
            except Exception as e:
                # 예외 처리
                ctx.save()
                error_str = str(e)
                output_system_message(
                    f"[CORTEX_ERROR] 맥락 자동 로드 중 오류 발생: {error_str}\n"
                    f"수동으로 get_active_summary를 호출하세요."
                )
                ctx.log(
                    "SessionStart",
                    "context_load_exception",
                    {"exception": error_str, "branch_id": active_branch},
                )
        else:
            ctx.save()
            # 활성 브랜치 없음 - 브랜치 생성 제안
            context_message = f"""[CORTEX_NO_ACTIVE_BRANCH]

프로젝트가 초기화되어 있지만 활성 브랜치가 없습니다.
새 작업을 시작하려면 브랜치를 생성하세요.

프로젝트: {ctx.project_path}
프로젝트 ID: {ctx.project_id}"""

            output_system_message(context_message)

            tool_call = generate_mcp_tool_call(
                "create_branch", {"project_id": ctx.project_id, "branch_topic": "main"}
            )
            output_tool_suggestion([tool_call])


if __name__ == "__main__":
    main()
