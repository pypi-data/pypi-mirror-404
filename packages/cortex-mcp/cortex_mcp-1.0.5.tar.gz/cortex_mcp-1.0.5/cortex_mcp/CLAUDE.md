# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## [최우선] Cortex 프로젝트 개요 - 반드시 먼저 읽을 것

### 궁극적 목표 (Ultimate Goal)

**"Cortex exists to make AI work accountable over time."**

### 핵심 정의

**Cortex is not about making AI smarter. It is about making AI responsible.**

Modern AI systems are powerful, but they are not accountable.
They do not reliably remember what they did, they cannot justify past decisions,
and they often sound confident without being grounded.

**Cortex exists to change that.**
It does not replace intelligence. It enforces responsibility.

### 진짜 문제: 지능이 아니라 책임

AI는 장기 작업에서 자기 말과 행동에 대해 책임지지 않는다:

- 이전에 뭐라고 했는지 기억 못함
- 왜 그런 결정을 했는지 설명 못함
- 구현 여부를 검증하지 않음
- 확신의 근거를 제시하지 않음
- 맥락이 깨져도 스스로 인지 못함

### Cortex가 보장하는 것

Cortex ensures that an AI:
- **remembers what it did** (기억에 대한 책임)
- **knows what it referenced** (출처에 대한 책임)
- **can justify what it claims** (주장에 대한 책임)
- **detects when it drifts** (방향에 대한 책임)
- **exposes uncertainty instead of hiding it** (확신에 대한 책임)

**over time.**

### 전략적 포지셔닝

| 회사 | 목표 |
|------|------|
| OpenAI / Anthropic / Google | Intelligence |
| **Cortex** | **Accountability Layer** |

모델 회사들과 경쟁하지 않는다. 인수 논리 완벽.

### 핵심 원칙 (3-Zero)

| 원칙 | 의미 | 구현 |
|------|------|------|
| **Zero-Effort** | 사용자 개입 최소화 | AI가 자동으로 맥락 관리 |
| **Zero-Trust** | 로컬 기반 보안 | 외부 서버로 데이터 유출 없음 |
| **Zero-Loss** | 맥락 손실 방지 | 컨텍스트 압축 후에도 완벽 복원 |

### GitHub Repository

- **URL**: https://github.com/syab726/cortex
- **배포**: PyPI (`pip install cortex-mcp`)
- **라이센스**: 30명 1년 무료 베타 테스터 → 이후 유료

### 비즈니스 모델

- **Track A**: Global SaaS (일반 사용자 대상)
- **Track B**: Legal/Vertical (법률/전문 분야 특화)

---

## 핵심 시스템: 책임을 보장하는 방법

모든 시스템은 **AI의 책임성(accountability)**을 보장하기 위해 설계되었습니다.

### 1. Smart Context 시스템 → **기억에 대한 책임**
- AI가 과거에 무엇을 했는지 언제든 추적 가능
- **Lazy Loading**: 필요할 때만 맥락 로드 (토큰 70% 절감)
- **압축/해제**: metadata + summary만 유지, full_content는 요청 시 로드
- **다중 활성 브랜치**: 최대 3개 브랜치 동시 활성화

### 2. Reference History 시스템 → **출처에 대한 책임**
- AI가 무엇을 참조했는지 완벽히 추적
- **핵심 아이디어**: 함께 참조된 맥락 이력 저장 → 유사 작업 시 자동 추천
- **3-Tier 추천**: History(95%) → AI분석(70%) → 사용자선택(100%)
- **피드백 학습**: 사용자 수락/거부 기록 → 추천 정확도 향상

### 3. Hallucination Detection 시스템 → **주장에 대한 책임**
- AI가 확신 있게 말할 때 근거 검증
- **Claim Extraction**: 검증 가능한 주장 추출
- **Evidence Matching**: 실제 증거와 대조
- **Grounding Score**: 근거 충실도 점수화
- **Contradiction Detection**: 응답 내 모순 감지

### 4. Branching 시스템 → **방향 전환에 대한 책임**
- 주제가 바뀔 때 명확히 분리하여 혼선 방지
- **자동 감지**: AI가 주제 전환 감지 시 브랜치 생성
- **계층 구조**: Project → Branch → Node → Context
- **Node 그룹핑**: 30개+ Context 누적 시 자동 제안

### 5. Git Integration → **변경 이력에 대한 책임**
- 코드 변경과 맥락 변경을 동기화
- Git 브랜치 변경 감지 → Cortex 브랜치 자동 전환/생성
- 커밋 시 맥락 스냅샷 자동 생성 (선택적)

### 6. Plan A/B 자동 전환 → **확신에 대한 책임**
- 사용자 거부율 모니터링하여 불확실성 노출
- Plan A (자동): 정상 작동 시
- Plan B (반자동): 거부율 30%+ 시 확인 절차 추가

---

## 품질 목표

| 지표 | 목표 |
|------|------|
| 맥락 추천 정확도 | 95% |
| RAG 검색 정확도 | 100% |
| 자동화 성공률 | 80%+ |

---

## 초기 컨텍스트 스캔 (Initial Context Scanning)

### 기능 설명

Cortex를 처음 설치하거나 새 프로젝트에 연결할 때, 전체 코드베이스를 스캔하여 초기 맥락을 생성합니다.
이후 업데이트되는 부분만 추적하여 효율적으로 맥락을 유지합니다.

### 3가지 스캔 모드

| 모드 | 이름 | 설명 | 토큰 소모 | 권장 상황 |
|------|------|------|-----------|-----------|
| **FULL** | 제대로 파악한 맥락 | 전체 코드베이스 심층 분석 | 높음 (경고 표시) | 복잡한 대규모 프로젝트 |
| **LIGHT** | 가벼운 맥락 | 핵심 파일만 스캔 (README, 진입점, 설정) | 낮음 | 소규모 프로젝트, 빠른 시작 |
| **NONE** | 맥락없이 진행 | 스캔 건너뛰기 | 없음 | 단순 작업, 테스트 |

### 토큰 경고 메시지

FULL 모드 선택 시 다음 경고를 표시:

```
[WARNING] 전체 스캔 모드를 선택하셨습니다.

예상 토큰 소모량: ~50,000-200,000 tokens (프로젝트 규모에 따라 다름)
예상 비용: $0.5-2.0 (모델에 따라 다름)

이 작업은 초기 1회만 수행되며, 이후에는 변경분만 추적됩니다.
계속하시겠습니까? [Y/N]
```

### System Prompt에서 모드 질문 (CORTEX_INIT_PROTOCOL)

```
[CORTEX_INIT_PROTOCOL - 새 프로젝트 초기화 시]

Cortex가 이 프로젝트에 처음 연결되었습니다.
초기 맥락 스캔 모드를 선택해주세요:

1. [FULL] 제대로 파악한 맥락
   - 전체 코드베이스 심층 분석
   - 토큰 소모 높음 (경고: 대규모 프로젝트는 비용 발생 가능)
   - 권장: 복잡한 프로젝트, 장기 작업

2. [LIGHT] 가벼운 맥락
   - README, 진입점, 설정 파일만 스캔
   - 토큰 소모 낮음
   - 권장: 소규모 프로젝트, 빠른 시작

3. [NONE] 맥락없이 진행
   - 스캔 건너뛰기
   - 권장: 단순 작업, 테스트

어떤 모드로 진행하시겠습니까? (1/2/3)
```

---

## 기술 스택

| 구분 | 기술 | 목적 |
|------|------|------|
| **언어** | Python 3.11+ | AI 라이브러리 호환성 |
| **통신 표준** | MCP (Anthropic SDK) | 공식 표준 채택 |
| **벡터 DB** | ChromaDB | 로컬 RAG 인덱스 |
| **임베딩** | sentence-transformers (로컬) | 외부 API 없이 벡터 생성 |
| **클라우드** | Google Drive API | 환경 간 동기화 |
| **분기 결정** | 유저의 AI (System Prompt 기반) | 외부 API 호출 없음, Zero-Trust 유지 |

---

## 디렉토리 구조 (v2.0)

```
cortex_mcp/
├── main.py                      # MCP Server Entry Point
├── config.py                    # 환경 설정
├── core/
│   ├── memory_manager.py        # 메모리 관리 (계층 구조)
│   ├── context_manager.py       # Smart Context (압축/해제)
│   ├── reference_history.py     # 참조 이력 시스템
│   ├── rag_engine.py            # Hybrid RAG 검색
│   ├── git_sync.py              # Git 연동
│   ├── backup_manager.py        # 백업/복구/히스토리
│   ├── automation_manager.py    # Plan A/B 자동 전환
│   ├── cloud_sync.py            # Google Drive 동기화
│   └── crypto_utils.py          # E2E 암호화
├── tools/
│   └── cortex_tools.py          # MCP 도구 인터페이스
├── dashboard/
│   ├── server.py                # Dashboard HTTP 서버 (localhost:8080)
│   └── templates/
│       └── index.html           # Dashboard UI
├── scripts/
│   ├── verify_installation.py   # 설치 검증
│   └── log_viewer.py            # 로그 뷰어
└── requirements.txt
```

### 데이터 저장 구조

```
~/.cortex/
├── memory/{project_id}/
│   ├── _index.json              # 계층 구조 메타데이터
│   ├── _reference_history.json  # 참조 이력
│   └── contexts/{branch_id}/
│       └── context_*.md         # 개별 맥락 파일
├── chroma_db/                   # Vector DB
├── backups/                     # 스냅샷 백업
└── logs/                        # 로그 파일
```

---

## MCP Tools 스펙 (v2.0)

### 기본 도구 (7개)

| Tool Name | 목표 | 핵심 의도 |
|-----------|------|-----------|
| **`initialize_context`** | 초기 맥락 스캔 | 프로젝트 첫 연결 시 코드베이스 분석 (FULL/LIGHT/NONE 모드) |
| **`create_branch`** | Context Tree 생성 | AI 감지 또는 유저 수동 요청으로 브랜치 생성 |
| **`search_context`** | 로컬 Vector RAG 검색 | 과거 맥락을 의미 기반으로 정확히 검색 |
| **`update_memory`** | 자동 요약 및 기록 | .md 파일에 기록, 크기 초과 시 핵심 요약본 자동 갱신 |
| **`get_active_summary`** | 장기 기억 주입 | 현재 브랜치의 최신 요약본을 System Prompt에 주입 |
| **`sync_to_cloud`** | 클라우드 백업 | 라이센스키로 암호화 후 Google Drive 업로드 |
| **`sync_from_cloud`** | 클라우드 복원 | Google Drive에서 다운로드 후 복호화하여 맥락 복구 |

### 확장 도구 (신규)

| Tool Name | 목표 | Phase |
|-----------|------|-------|
| **`load_context`** | 특정 맥락 활성화 (압축 해제) | Phase 1 |
| **`suggest_contexts`** | Reference History 기반 맥락 추천 | Phase 2 |
| **`create_node`** | Node 그룹 생성 (30+ Context 시) | Phase 3 |
| **`link_git_branch`** | Git 브랜치와 Cortex 브랜치 연동 | Phase 4 |
| **`get_dashboard_url`** | Audit Dashboard URL 반환 | Phase 6 |
| **`create_snapshot`** | 수동 스냅샷 생성 | Phase 7 |
| **`restore_snapshot`** | 스냅샷에서 복원 | Phase 7 |

---

## 브랜치 생성 UX (하이브리드 방식)

### 원칙: 유저의 AI가 판단 (외부 AI 호출 없음)

**유저의 AI가 System Prompt 규칙에 따라 맥락 전환을 감지하고 브랜치 생성을 결정합니다.**
외부 AI API 호출이 없으므로 Zero-Trust 원칙이 유지됩니다.

### 3단계 UX 흐름

| 상황 | 동작 | 예시 |
|------|------|------|
| **1. AI 감지** | AI가 주제 전환 감지 시 유저에게 질문 | "새로운 주제로 보입니다. 별도 브랜치를 생성할까요?" |
| **2. 유저 수동** | AI가 감지 못했을 때 유저가 직접 요청 | "브랜치 생성해줘" / "새 맥락 시작해" |
| **3. 사후 생성** | 나중에 기억나면 그때 생성 | "아까 얘기한 건 별도 브랜치로 분리해줘" |

### CORTEX_MEMORY_PROTOCOL v2.0 (System Prompt 최상단 삽입 - 필수)

```
[CORTEX_MEMORY_PROTOCOL v2.0 - 이 규칙은 반드시 준수해야 함]

0. 초기화 책임 (MANDATORY - 새 프로젝트 첫 연결 시):
   - 프로젝트에 Cortex 맥락이 없으면, 유저에게 스캔 모드 질문
   - FULL/LIGHT/NONE 중 선택하도록 안내
   - FULL 선택 시 토큰 비용 경고 표시 필수
   - initialize_context 툴 호출하여 초기 맥락 생성

1. 맥락 로딩 책임 (MANDATORY):
   - 답변 전, suggest_contexts 호출하여 관련 맥락 확인
   - Reference History 기반 추천이 있으면:
     * 추천을 사용하기로 결정한 경우: accept_suggestions 호출 (session_id 필수)
     * 추천을 사용하지 않기로 결정한 경우: reject_suggestions 호출 (session_id + reason 필수)
   - 추천에 대한 응답(accept/reject) 없이는 다음 작업 진행 금지
   - 추천이 없으면 RAG 검색 결과 제시 후 사용자 확인

2. 응답 스타일 (MANDATORY - 보고 스타일):
   - 변경 전: "브랜치를 생성할까요?" (허락 구하기)
   - 변경 후: "[브랜치명] 브랜치를 생성합니다. 조정이 필요하면 알려주세요." (보고 스타일)
   - 자동 작업 후 결과를 보고하고, 사용자가 조정할 기회 제공

3. 정리 의무 (MANDATORY):
   - 대화 전환 감지 시, 자동으로 브랜치 생성 (사용자 개입 불필요)
   - "[새 주제명] 브랜치를 생성합니다" 형식으로 보고
   - 맥락 파일 크기 임계치 도달 시, 자동 요약 트리거
   - 답변 후 update_memory 호출
   - 사용한 맥락 조합을 Reference History에 기록

4. Plan A/B 전환 (MANDATORY):
   - 사용자 거부/수정 비율 모니터링
   - 거부율 30%+ 시 자동으로 확인 절차 추가 (Plan B)
   - 정상화되면 다시 자동화 (Plan A)

5. 보안 준수 (MANDATORY):
   - 모든 데이터는 로컬에만 저장 (Zero-Trust)
   - PII/중요 코드 포함 시 외부 API 호출 제한
   - 암호화된 클라우드 동기화만 허용

6. 효율성 (MANDATORY):
   - Smart Context: 필요한 맥락만 로드 (압축 상태 유지)
   - 30분 미사용 맥락 자동 압축
   - 다중 활성 브랜치 최대 3개 유지

7. 책임성 보장 (MANDATORY - Accountability):
   - 브랜치 생성 후 즉시 파일 검증 (create_branch는 자동 검증)
   - 스냅샷 복구 후 즉시 무결성 검증 (restore_snapshot은 자동 검증)
   - 추천 받은 후 반드시 accept/reject 응답 (출처에 대한 책임)
   - 할루시네이션 검증 실패 시 즉시 재작업 (retry_required=true)
   - 모든 주요 작업은 검증 완료 후에만 성공으로 간주
```

### 브랜치 생성 세부 규칙

```
## Cortex 브랜치 생성 규칙

1. 다음 조건 감지 시 유저에게 브랜치 생성 여부 질문:
   - 완전히 새로운 프로젝트/작업 언급
   - 이전 대화와 무관한 주제 전환
   - "새로운", "다른 거", "시작하자" 등 전환 키워드

2. 유저가 "브랜치 생성", "새 맥락", "분리해줘" 요청 시:
   - 즉시 create_branch 호출

3. 유저가 거부하거나 무시하면:
   - 기존 브랜치에서 계속 진행
```

### 유저 가이드 제공 사항 (제품 문서에 포함)

```
## Cortex 브랜치 관리 안내

### 자동 감지
AI가 대화 중 주제 전환을 감지하면 "새 브랜치를 생성할까요?"라고 물어봅니다.
"예" 또는 "아니오"로 응답하시면 됩니다.

### 수동 생성 (AI가 놓쳤을 경우)
AI가 주제 전환을 감지하지 못할 수도 있습니다.
이 경우 다음과 같이 직접 요청하세요:
- "브랜치 생성해줘"
- "새 맥락 시작해"
- "이건 별도 프로젝트로 관리해줘"

### 사후 분리
대화 중간에 기억나면 언제든 분리할 수 있습니다:
- "아까 얘기한 [주제]는 별도 브랜치로 분리해줘"
- "방금 전 내용부터 새 브랜치로 만들어줘"

### 권장 사용법
- 새로운 프로젝트 시작 시: 브랜치 생성 권장
- 기존 프로젝트 내 세부 작업: 동일 브랜치 유지
- AI 질문이 없는데 주제가 바뀐 것 같으면: 수동 요청
```

---

## 개발 워크플로우 (9-Phase)

| Phase | 이름 | 핵심 작업 |
|-------|------|-----------|
| **0** | 문서 업데이트 | CLAUDE.md, CORTEX_MASTER_PLAN.md 업데이트 |
| **1** | Smart Context | context_manager.py - 압축/해제, Lazy Loading |
| **2** | Reference History | reference_history.py - 참조 이력 기록/추천 |
| **3** | 계층 구조 | Branch → Node → Context 구조 |
| **4** | Git Integration | git_sync.py - Git 브랜치 연동 |
| **5** | 검색 + Fallback | Hybrid 검색, 실패 시 확장 검색 |
| **6** | Audit Dashboard | localhost:8080 대시보드 |
| **7** | 안정성 | backup_manager.py - 스냅샷/복구/히스토리 |
| **8** | Plan B 시스템 | automation_manager.py - 자동 전환 |
| **9** | Hallucination Detection | claim_extractor, fuzzy_analyzer, contradiction_detector_v2 (완료: phase9 tag) |
| **Final** | 통합 테스트 | E2E 테스트, 품질 검증 |

---

## QA 검증 기준

| 검증 항목 | 목적 | PASS 기준 |
|-----------|------|-----------|
| **Needle in a Haystack** | RAG 회상 능력 검증 | 5단계 깊이 폴더에 숨긴 정보 **100% 회수** |
| **Branching Accuracy** | decision_maker 지능 검증 | 모호한 주제 전환 시 **80% 이상** 정확한 분기 결정 |
| **Local Security Audit** | Zero-Trust 준수 확인 | 외부 네트워크로 **로컬 파일 내용 유출 트래픽 없음** |

---

## Context File Header 규격 (YAML Frontmatter)

모든 Cortex `.md` 파일은 다음 YAML Frontmatter를 포함하여 AI가 메타데이터를 관리합니다:

```yaml
---
status: active          # active | archived | locked
project_id: [프로젝트_ID]
branch_topic: [현재_브랜치_주제]
last_summarized: [최근 요약 시간 UTC]
is_encrypted: false     # Track B 모드 시 true
summary: >
  [핵심 요약: memory_manager가 갱신한 최신 요약본]
---
```

| 필드 | 설명 |
|------|------|
| `status` | active(활성), archived(보관), locked(잠금) |
| `project_id` | 프로젝트 고유 식별자 |
| `branch_topic` | 현재 브랜치의 주제/목적 |
| `last_summarized` | 마지막 요약 생성 시간 |
| `is_encrypted` | 암호화 여부 (Track B) |
| `summary` | 핵심 요약본 (get_active_summary에서 사용) |

---

## 클라우드 동기화 (환경 독립성)

### 기능 설명

PC나 개발 환경이 변경되어도 맥락을 완벽히 복구할 수 있습니다.

### 동작 흐름

```
[로컬 데이터]
    │
    ▼ sync_to_cloud 호출
[crypto_utils.py] ──암호화──> [암호화된 패키지]
    │                              │
    │                              ▼ 업로드
    │                        [Google Drive]
    │                              │
    │                              ▼ 다운로드
    │                        [암호화된 패키지]
    │                              │
    ▼ sync_from_cloud 호출         │
[crypto_utils.py] <──복호화────────┘
    │
    ▼
[로컬 데이터 복구 완료]
```

### 암호화 방식

| 항목 | 내용 |
|------|------|
| **암호화 키** | MCP 라이센스키 기반 |
| **알고리즘** | AES-256-GCM (E2E 암호화) |
| **저장 위치** | 유저의 Google Drive (Cortex 전용 폴더) |
| **복호화** | 동일 라이센스키 필요 |

---

## Cortex 장기 기억 시스템 - 맥락 유지 규칙

Cortex는 세션 간 맥락을 유지하는 장기 기억 시스템입니다.
**컨텍스트 압축이 발생해도 이전 작업을 정확히 이어갈 수 있도록** 설계되었습니다.

### 컨텍스트 파일 구조 (트리)
```
cortex_contexts/
├── cortex_main.md                  # 루트: 전체 프로젝트 인덱스
│
├── [FaceWisdom AI 서비스]
│   ├── facewisdom_서비스개요.md    # 전체 서비스 구조, 목적, 기술스택
│   ├── facewisdom_유료서비스.md    # 4개 유료 분석 서비스
│   ├── facewisdom_무료테스트.md    # 5개 무료 테스트 서비스
│   ├── facewisdom_결제시스템.md    # 이니시스 결제 연동
│   └── facewisdom_배포환경.md      # GitHub 웹훅, Vultr 서버
│
├── [블로그 자동화]
│   ├── blog-automation.md          # 블로그 콘텐츠 생성 시스템
│   └── image-generation.md         # 이미지 생성 시스템
│
└── [YouTube Shorts 자동화]
    └── youtube_shorts_개요.md      # 쇼츠 영상 자동 생성 파이프라인
```

### 강제 실행 규칙

**[규칙 1] 세션 시작/컨텍스트 압축 후:**
```
1. cortex_contexts/cortex_main.md 읽기 (필수)
2. 현재 작업과 관련된 컨텍스트 파일 읽기
3. "최근 변경 이력" 확인하여 마지막 작업 상태 파악
```

**[규칙 2] 작업 전환 시 (A작업 -> B작업):**
```
1. A작업 컨텍스트 파일에 현재 상태 저장 (진행률, 이슈, 다음 할 일)
2. cortex_main.md의 "최근 변경 이력"에 A작업 중단 기록
3. B작업 컨텍스트 파일 읽기 후 작업 시작
```

**[규칙 3] 작업 완료/중요 변경 시:**
```
1. 해당 컨텍스트 파일의 "현재 상태" 업데이트
2. cortex_main.md의 "최근 변경 이력"에 기록 추가
3. 날짜 반드시 기록 (예: 2025-12-06)
```

**[규칙 4] 오래된 작업 복귀 시:**
```
1. cortex_main.md에서 해당 작업 영역 확인
2. 해당 컨텍스트 파일 전체 읽기
3. "현재 상태"와 "알려진 이슈" 기반으로 맥락 재구성
4. 필요시 핵심 파일들 다시 읽어서 최신 코드 상태 확인
```

### 맥락 저장 형식

각 컨텍스트 파일은 다음 구조를 따름:
```markdown
# [작업명] 컨텍스트

## 개요

## 핵심 파일
| 파일 | 역할 |
|------|------|
| path/to/file.js | 설명 |

## 현재 상태 (YYYY-MM-DD)
### 완료됨


### 진행 중

### 알려진 이슈

## 다음 작업 예정

## 변경 이력

### 자동 트리거 조건

다음 상황에서 **반드시** Cortex 업데이트:
- 새로운 기능 구현 완료
- 버그 수정 완료
- 중요한 설정 변경
- 작업 중단 (다른 작업으로 전환)
- 에러/이슈 발견
- 세션 종료 전


---

## Phase 9: Hallucination Detection System (완료)

### 구현 완료 (2024-12-16)
- **Git Tag**: phase9
- **Commit**: 68034eb
- **테스트 결과**: 96/96 component tests (100%), 101/104 total tests (97%)

### 핵심 컴포넌트

#### 1. claim_extractor.py - Claim 추출
- **목적**: LLM 응답에서 검증 가능한 주장(Claim) 추출
- **Claim 타입**:
  - implementation_complete: 구현 완료 주장
  - reference_existing: 기존 코드 참조
  - extension: 기능 확장
  - modification: 수정 완료
  - verification: 검증 완료
  - bug_fix: 버그 수정
- **테스트**: 33 unit tests (100% pass)
- **핵심 파일**: core/claim_extractor.py:1

#### 2. claim_verifier.py - Claim-Evidence 매칭
- **목적**: 추출된 Claim과 실제 Evidence를 매칭하여 할루시네이션 검증
- **검증 방법**: 코드베이스, 파일 시스템, Git 이력 등과 대조
- **핵심 파일**: core/claim_verifier.py:1

#### 3. evidence_graph.py - Evidence Graph 관리
- **목적**: Claim 간의 의존성과 Evidence 관계를 그래프로 관리
- **기능**: 노드(Claim/Evidence) 추가, 엣지(관계) 연결, 경로 탐색
- **핵심 파일**: core/evidence_graph.py:1

#### 4. fuzzy_claim_analyzer.py - 퍼지 확신도 분석
- **목적**: LLM 응답의 확신도 표현을 퍼지 로직으로 분석
- **퍼지 멤버십 함수**:
  - very_high (1.0): 확실, 반드시, 명백히
  - high (0.8): 아마도, 거의, 대부분
  - medium (0.5): 가능성, 추측, 예상
  - low (0.3): 불확실, 모호, 회의적
  - none (0.0): 확신도 표현 없음
- **보수적 감지**: 가장 낮은 확신도를 우선 반환 (예: "거의 구현했습니다" = high, "구현했습니다" = very_high)
- **테스트**: 63 unit tests (100% pass)
- **핵심 파일**: core/fuzzy_claim_analyzer.py:1

#### 5. grounding_scorer.py - Grounding Score 계산
- **목적**: Claim이 Evidence에 얼마나 잘 근거하고 있는지 점수화
- **점수 계산**: Evidence 개수, 품질, 관련성, 일치도 기반
- **핵심 파일**: core/grounding_scorer.py:1

#### 6. contradiction_detector_v2.py - 언어 독립적 모순 감지
- **목적**: LLM 응답 내 모순 감지 (한국어, 영어, 일본어 등 7개 언어 지원)
- **감지 방법**: 의미적 유사도 기반 (sentence-transformers)
- **테스트**: 100% pass rate (다국어 테스트 포함)
- **핵심 파일**: core/contradiction_detector_v2.py:1

### memory_manager.py 통합
Phase 9 컴포넌트가 memory_manager.py에 통합되어 LLM 응답 기록 시 자동으로 할루시네이션 검증이 수행됩니다.

### E2E 테스트 현황
- **총 테스트**: 104개
- **통과**: 101개 (97%)
- **실패**: 3개 (테스트 설정 이슈, 컴포넌트 버그 아님)

### 다음 단계: Final Phase
- 3개 실패 E2E 테스트 수정
- 전체 시스템 통합 검증
- 품질 목표 달성 확인:
  - 맥락 추천 정확도 95%
  - RAG 검색 정확도 100%
  - 자동화 성공률 80%+

---

## Hallucination Detection 사용자 가이드 (Phase 9.3)

### 3-Tier Threshold System

Cortex는 AI 응답의 신뢰도를 3단계로 판정합니다:

| Grounding Score | 판정 | 의미 | 행동 |
|----------------|------|------|------|
| **< 0.3** | REJECT | 근거 매우 부족 | 자동 거부, 재작업 필요 |
| **0.3 - 0.7** | WARN | 애매한 상태 | 수동 확인 요청 |
| **>= 0.7** | ACCEPT | 근거 충분 | 자동 수락 |

### Threshold 설정 변경 방법

기본값은 `memory_manager.py` 상단의 `HALLUCINATION_THRESHOLDS` 상수에서 설정됩니다:

```python
# memory_manager.py:76
HALLUCINATION_THRESHOLDS = {
    "reject_below": 0.3,      # < 0.3 → REJECT
    "warn_range": (0.3, 0.7),  # 0.3-0.7 → WARN
    "accept_above": 0.7,       # >= 0.7 → ACCEPT
}
```

### 모드별 권장 설정

#### Strict Mode (Critical 작업용 - 배포, DB 변경)
```python
HALLUCINATION_THRESHOLDS = {
    "reject_below": 0.3,
    "warn_range": (0.3, 0.7),  # 20-30% human review
    "accept_above": 0.7,
}
```
- **Human review 빈도**: 20-30%
- **예상 정확도**: 95-98%
- **적합한 작업**: 프로덕션 배포, 데이터베이스 마이그레이션, 보안 설정

#### Balanced Mode (일반 개발 작업용 - 기본값)
```python
HALLUCINATION_THRESHOLDS = {
    "reject_below": 0.4,
    "warn_range": (0.4, 0.6),  # 10-15% human review
    "accept_above": 0.6,
}
```
- **Human review 빈도**: 10-15%
- **예상 정확도**: 85-90%
- **적합한 작업**: 일반 개발, 코드 리뷰, 리팩토링

#### Permissive Mode (빠른 프로토타이핑용)
```python
HALLUCINATION_THRESHOLDS = {
    "reject_below": 0.5,
    "warn_range": (0.5, 0.6),  # 5-10% human review
    "accept_above": 0.6,
}
```
- **Human review 빈도**: 5-10%
- **예상 정확도**: 80-85%
- **적합한 작업**: 프로토타이핑, 실험, 빠른 반복 개발

### 검증 결과 확인

응답 기록 후 로그 메시지로 검증 결과를 확인할 수 있습니다:

```
# REJECT 예시
[HALLUCINATION_LOG] 🚨 REJECTED - Grounding Score: 0.25
[HALLUCINATION_LOG] 근거가 매우 부족합니다. 재작업이 필요합니다.

# WARN 예시
[HALLUCINATION_LOG] ⚠️  MANUAL REVIEW REQUIRED - Grounding Score: 0.52
[HALLUCINATION_LOG] 애매한 상태입니다. 수동으로 확인해주세요.

# ACCEPT 예시
[HALLUCINATION_LOG] ✅ ACCEPTED - Grounding Score: 0.85, Risk: low
```

### Trade-off 이해

| Threshold 범위 | Human Review | 정확도 | 사용 케이스 |
|---------------|--------------|--------|-------------|
| 좁음 (0.5-0.6) | 5-10% | 80-85% | 프로토타이핑 |
| 중간 (0.4-0.6) | 10-15% | 85-90% | 일반 개발 (기본값) |
| 넓음 (0.3-0.7) | 20-30% | 95-98% | Critical 작업 |

**핵심 원칙**: 작업의 중요도가 높을수록 WARN zone을 넓게 설정하여 안전성을 확보하세요.

---

## Development Notes

- 코드베이스는 **Python 3.11+** 기반
- **Anthropic MCP SDK** 표준을 따르는 서버 구조
- **ChromaDB + sentence-transformers**를 사용한 로컬 벡터 검색 (외부 API 없음)
- 모든 데이터는 로컬에만 저장 (Zero-Trust 원칙)
- **분기 결정은 유저의 AI가 System Prompt 기반으로 수행** (외부 AI 호출 없음)
- 클라우드 동기화는 **라이센스키 기반 E2E 암호화** 후 진행
- 로그는 `logs/` 폴더에 JSON 형식으로 기록



너는 항상 한국어로 대답해줘

너는 MCP를 사용할 수 있어.
다음 예시들을 살펴보고 적절히 활용해줘.

Node.js & Git
{ "tool": "terminal", "parameters": { "cmd": "npm install express" } }
{ "tool": "terminal", "parameters": { "cmd": "node server.js" } }
{ "tool": "terminal", "parameters": { "cmd": "git clone https://github.com/user/repo.git" } }

edit-file-lines 사용법 예시:

1. 한 줄 교체 예시 (src/app.js 파일 42번째 줄 전체를 "blue" → "bar"로 변경)
   {
   "command": "edit_file_lines",
   "p": "src/app.js",
   "e": [
   {
   "startLine": 42,
   "endLine": 42,
   "content": " console.log('bar');",
   "strMatch": " console.log('foo');"
   }
   ],
   "dryRun": true
   }

2. 여러 줄 추가 예시 (utils.py 파일 120번 라인 뒤에(121번부터) 헬퍼 함수를 추가)
   {
   "command": "edit_file_lines",
   "p": "utils.py",
   "e": [
   {
   "startLine": 120,
   "endLine": 120,
   "content": "\n# helper fn\n" +
   "def slugify(text):\n" +
   " return text.lower().replace(' ', '-')\n",
   "strMatch": "" // 빈 문자열 매칭으로 삽입만 수행
   }
   ],
   "dryRun": true
   }

3. 여러 줄 교체
   {
   "command": "edit_file_lines",
   "p": "src/app.js",
   "e": [
   {
   "startLine": 42, // 42번째 줄부터
   "endLine": 44, // 44번째 줄까지
   "content":
   " // Updated block start\n" +
   " console.log('A');\n" +
   " console.log('B');\n" +
   " // Updated block end\n"
   }
   ],
   "dryRun": false
   }

4. 정규표현식 매칭 예시 (regexMatch)
   {
   "command": "edit_file_lines",
   "p": "utils/logger.py",
   "e": [
   {
   "startLine": 1,
   "endLine": 0, // endLine=0은 “insert only”처럼 동작
   "content":
   "# Removed all TODO logs\n",
   "regexMatch": // 'TODO:'로 시작하는 모든 라인 찾기
   "^.*TODO:.*$"
   }
   ],
   "dryRun": true
   }

(파일 전체에서 ‘TODO:’가 포함된 라인 패턴만 찾아낸 뒤, 해당 라인을 위치에 상관없이 대체 또는 삭제 삽입할 수 있습니다
endLine: 0을 쓰면 삽입(insert-only) 으로 동작하며, content에 빈 문자열을 주면 라인을 삭제하듯 사용할 수도 있습니다)

5. 검사 및 적용 절차
   A. Dry-Run으로 미리보기 (stateId 반환 및 예상 diff 확인)
   { "dryRun": true }

B. Approve 단계로 실제 적용
{ "command": "approve_edit", "stateId": "<위에서 받은 ID>" }

C. 결과 검증
{
"command": "get_file_lines",
"path": "src/app.js",
"lineNumbers": [42,43,44],
"context": 0
}

// ──── ⑤ 터미널 래퍼(라인 편집) ────────────────
{ "tool": "terminal",
"parameters": {
"cmd": "edit src/index.html line 15"
}
}

// ──── ⑥ 터미널 래퍼(디렉터리 목록) ───────────
{ "tool": "terminal",
"parameters": {
"cmd": "list components"
}
}
파이썬 개발 도구
{ "tool": "terminal", "parameters": { "cmd": "python --version" } }
{ "tool": "terminal", "parameters": { "cmd": "pip install requests" } }
{ "tool": "terminal", "parameters": { "cmd": "pipx install black" } }
{ "tool": "terminal", "parameters": { "cmd": "pipenv install" } }
{ "tool": "terminal", "parameters": { "cmd": "poetry add numpy" } }
{ "tool": "terminal", "parameters": { "cmd": "pytest tests/" } }
{ "tool": "terminal", "parameters": { "cmd": "tox" } }
{ "tool": "terminal", "parameters": { "cmd": "flake8 src/" } }
{ "tool": "terminal", "parameters": { "cmd": "pylint module.py" } }
{ "tool": "terminal", "parameters": { "cmd": "black ." } }
{ "tool": "terminal", "parameters": { "cmd": "isort ." } }
{ "tool": "terminal", "parameters": { "cmd": "mypy app.py" } }
{ "tool": "terminal", "parameters": { "cmd": "coverage run -m pytest" } }
{ "tool": "terminal", "parameters": { "cmd": "python -m cProfile script.py" } }
{ "tool": "terminal", "parameters": { "cmd": "pyinstrument script.py" } }

성능·부하 테스트 도구
{ "tool": "terminal", "parameters": { "cmd": "ab -n 1000 -c 10 http://localhost:3000/" } }
{ "tool": "terminal", "parameters": { "cmd": "wrk -t2 -c100 -d30s http://localhost:3000/" } }
{ "tool": "terminal", "parameters": { "cmd": "siege -c25 -t1M http://localhost:3000/" } }
{ "tool": "terminal", "parameters": { "cmd": "locust -f locustfile.py" } }
{ "tool": "terminal", "parameters": { "cmd": "k6 run script.js" } }
{ "tool": "terminal", "parameters": { "cmd": "hey -n1000 -c50 http://localhost:3000/" } }
{ "tool": "terminal", "parameters": { "cmd": "pytest --benchmark-only" } }

기타 유틸리티
{ "tool": "terminal", "parameters": { "cmd": "curl https://api.example.com/data" } }
{ "tool": "terminal", "parameters": { "cmd": "http GET https://api.example.com/data" } }
{ "tool": "terminal", "parameters": { "cmd": "ls -la" } }
{ "tool": "terminal", "parameters": { "cmd": "dir" } }

// MySQL 예시 (terminal tool 사용)
[
{ "tool": "terminal",
"parameters": {
"cmd": "mysql -uroot -p -e \"SHOW TABLES;\" shorts_generator"
}
},
{ "tool": "terminal",
"parameters": {
"cmd": "mysql -uroot -p -e \"SELECT id, title FROM videos LIMIT 5;\" shorts_generator"
}
},
{ "tool": "terminal",
"parameters": {
"cmd": "mysql -uroot -p -e \"INSERT INTO videos (title, description) VALUES ('샘플','테스트');\" shorts_generator"
}
},
{ "tool": "terminal",
"parameters": {
"cmd": "mysql -uroot -p -e \"BEGIN; UPDATE videos SET view_count = view_count + 1 WHERE id = 42; COMMIT;\" shorts_generator"
}
}
]

Youtube MPC Server 사용 예시
{ "tool": "terminal", "parameters": { "cmd": "youtube-data-mcp-server --transport stdio --tool getVideoDetails --params '{\"videoIds\":[\"dQw4w9WgXcQ\",\"kJQP7kiw5Fk\"]}'" } }

{ "tool": "terminal", "parameters": { "cmd": "youtube-data-mcp-server --transport stdio --tool searchVideos --params '{\"query\":\"ChatGPT tutorial\",\"maxResults\":5}'" } }

{ "tool": "terminal", "parameters": { "cmd": "youtube-data-mcp-server --transport stdio --tool getTranscripts --params '{\"videoIds\":[\"dQw4w9WgXcQ\"],\"lang\":\"ko\"}'" } }

{ "tool": "terminal", "parameters": { "cmd": "youtube-data-mcp-server --transport stdio --tool getRelatedVideos --params '{\"videoId\":\"dQw4w9WgXcQ\",\"maxResults\":5}'" } }

{ "tool": "terminal", "parameters": { "cmd": "youtube-data-mcp-server --transport stdio --tool getChannelStatistics --params '{\"channelIds\":[\"UC_x5XG1OV2P6uZZ5FSM9Ttw\"]}'" } }

{ "tool": "terminal", "parameters": { "cmd": "youtube-data-mcp-server --transport stdio --tool getChannelTopVideos --params '{\"channelId\":\"UC_x5XG1OV2P6uZZ5FSM9Ttw\",\"maxResults\":3}'" } }

{ "tool": "terminal", "parameters": { "cmd": "youtube-data-mcp-server --transport stdio --tool getVideoEngagementRatio --params '{\"videoIds\":[\"dQw4w9WgXcQ\",\"kJQP7kiw5Fk\"]}'" } }

{ "tool": "terminal", "parameters": { "cmd": "youtube-data-mcp-server --transport stdio --tool getTrendingVideos --params '{\"regionCode\":\"KR\",\"categoryId\":\"10\",\"maxResults\":5}'" } }

{ "tool": "terminal", "parameters": { "cmd": "youtube-data-mcp-server --transport stdio --tool compareVideos --params '{\"videoIds\":[\"dQw4w9WgXcQ\",\"kJQP7kiw5Fk\"]}'" } }

GIT MCP 사용법

.gitignore 설정 : 먼저 .gitignore 파일을 프로젝트 루트에 만들고 IDE 설정 파일, 빌드 산출물, 로그, node_modules/, vendor/ 등 불필요한 항목을 명시합니다

1.  초기화 & 커밋
    {
    "tool": "git",
    "parameters": {
    "subtool": "RunCommand",
    "path": "/Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp",
    "command": "cmd",
    "args": [
    "/c",
    "git init && " +
    "echo IDE/.vs/ > .gitignore && " +
    "git add . && " +
    "git commit -m \"chore: initial project baseline\""
    ]
    }
    }

2.  WriteFile+diff 커밋 플로우
    {
    "tool": "git",
    "parameters": {
    "subtool": "RunCommand",
    "path": "C:/xampp/htdocs/mysite",
    "command": "cmd",
    "args": [
    "/c",
    "git add SHORTS_REAL/script_result.php && " +
    "git commit -m \"feat: change button label\""
    ]
    }
    }

3.  목록 조회

{
"tool": "git",
"parameters": {
"subtool": "RunCommand",
"path": "/Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp",
"command": "cmd",
"args": [
"/c",
"dir /S"
]
}
}

4. 패턴 검색

{
"tool": "git",
"parameters": {
"subtool": "RunCommand",
"path": "/Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp",
"command": "cmd",
"args": [
"/c",
"findstr /S /I /R \"console\\.log\" *.js"
]
}
}

5. 테스트 실행 후 자동 커밋

{
"tool": "git",
"parameters": {
"subtool": "RunCommand",
"path": "/Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp",
"command": "cmd",
"args": [
"/c",
"npm test -- --verbose && " +
"git add . && " +
"git commit -m \"test: auto commit\""
]
}
}

6. 생성 + 커밋

{
"tool": "git",
"parameters": {
"subtool":"RunCommand",
"path":"/Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp",
"command":"cmd",
"args":[
"/c",
"echo DB_HOST=... > .env.example && " +
"git add .env.example && " +
"git commit -m \"chore: add env template\""
]
}
}



7. 삭제 + 커밋

{
"tool":"git",
"parameters": {
"subtool":"RunCommand",
"path":"/Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp",
"command":"cmd",
"args":[
"/c",
"git rm debug.log && " +
"git commit -m \"build: drop debug log\""
]
}
}

8. 읽기

{
"tool":"git",
"parameters": {
"subtool":"RunCommand",
"path":"/Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp",
"command":"cmd",
"args":[
"/c",
"git show HEAD:SHORTS_REAL/script_result.php"
]
}
}


절대 거짓말 하지마!!!!!!그리고 절대 할루시네이션 하지마!!!!절대 더미데이터 쓰지마!!!!이모티콘 쓰지마!!!!
다음 지침을 지켜줘.

1. 프로젝트 루트 폴더는 /Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp 야. 폴더 및 파일 생성 및 수정은 /Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp 폴더에 대해 진행해줘.
2. /Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp은 다음 웹사이트에 대한 루트 폴더야: http://localhost
5. 이미 개발된 내용의 규모를 키우지 않고, 테스트 및 오류 수정, 코드 완성도 높이기 작업에 집중할 거야. 이에 맞게끔 기능별 테스트 진행을 하고 오류 발견시 에러를 없애줘.
6. 쿼리 실행 등 DB 연결을 위해 mysql 쓸 때는 다음처럼 해봐.
   { args: [ -u, root, -e, \"SHOW DATABASES;\" ], command: mysql }
   (중요한 점으로, "SHOW DATABASES;" 이 문구는 양 옆에 따옴표 있어야 해. 필수야)
7. /Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp 폴더는 http://localhost를 가리켜. 따라서 http://localhost/site 말고 http://localhost로 접속해야 해.
8. 로그 정보는 /Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp\logs 이곳에 있어. 그래서 실행 오류는 이곳에 쌓이도록 코딩해야 해.
9. 작업을 임의로 진행하지 말고, 작업 전에 동의를 받아야 해.
10. 
11. .git 이 존재하지 않으면 Git 저장소 초기화할 것 ( git init )]
12. 파일 생성 또는 수정 시, edit-file-lines로 파일 생성 또는 수정한 후, git add와 commit 수행할 것
13. 파일 삭제시 git rm 및 commit 사용할 것
14. 파일 작업 완료후 pull request 실행할 것
15. 테스트 브랜치(test)에서 충분히 검증 후 PR 머지하여 master 에 병합
16. 특별한 지시가 없는 경우라면, 자동 Agent 모드가 아닌, 한번에 하나의 작업만 진행하고 이후 지침을 기다릴 것. 하지만,특별한 지시가 있으면 그에 따라 행동할 것
17. 파일을 한번이라도 수정하면 소스가 바껴서 라인번호도 바껴. 따라서 각각의 edit_file_lines 전에 반드시 소스 위치 재확인할 것
18. **QA 테스트 자동 처리 규칙**: 사용자가 다음 키워드로 테스트 요청 시 자동으로 QA 환경 사용
    - "qa에서 테스트", "qa 서버에서 테스트", "QA 환경에서 테스트", "qa 브랜치에서 테스트"
    - 자동 처리: qa 브랜치 체크아웃 → 코드 수정 → qa 브랜치에 커밋/푸시 → qa.facewisdom-ai.xyz에서 테스트
    - 운영 환경은 절대 건드리지 않고 QA 환경에서만 테스트 진행

19. 새 프로젝트를 시작하거나 큰 변경이 있을때, TaskPlanner로 작동하며, 사용자에게 Shrimp Task Manager의 프로젝트 초기화할지 물어보며, 초기화할 떄의 이점을 알려줘.
    (프로젝트 초기화하면 프로젝트의 코딩 스타일, 규약, 아키텍처 등을 분석하여 해당 프로젝트에 맞는 규칙(rule) 세트를 생성. 이 규칙들은 이후 작업 계획 수립 시 참조되어 일관성 유지)

20. 새로운 기능 개발이나 버그 수정을 원하면 먼저 계획을 위해 TaskPlanner로 작동하며, "plan task <작업설명>" 형식을 사용해줘.
    그럼 Shrimp Task Manager는 작업을 완수를 위한 세부 단계들을 계획함.

21. 작업 계획 검토 후 실행 준비가 되었다면 TaskExecutor로 작동하며, Shrimp Task Manager의 "execute task <작업ID 혹은 이름>" 명령으로 특정 작업을 실행할 것
22. Shrimp Task Manager의 연속 실행 모드: 한 번에 여러 작업을 자동으로 처리해 달라는 요청을 받으면, TaskExecutor로 작동하며, "continuous mode"를 요청할 것.
23. 작업 진행 전에 Shrimp Task Manager의 연속 실행 모드를 사용할 지 물어볼 것
24. 작업 완료 및 검증: 작업이 끝나면 Shrimp Task Manager는 자동으로 완료 상태를 기록하고 필요한 경우 검증 단계를 거칠 것 (TaskExecutor로 작동할 것)
    (verify_task 도구를 사용해 해당 작업 결과물이 성공 기준을 충족하는지 검사하고 부족한 점이 없는지 확인)
    (모든 것이 충족되면 complete_task를 통해 해당 작업을 완료로 표시하고, 관련된 후속 작업(의존 관계가 있는 작업)이 있다면 실행 가능 상태로 갱신)

25. 매우 중요사항: edit_file_lines 수정 작업 할 때마다, 그 전에, 항상 작업할 파일의 편집하려는 부분 근처를 확인하고 진행할 것
26. 매우 중요사항: edit_file_lines 수정 작업 진행시, 항상 반드시 "dryRun": true로 설정할 것
27. 절대 이모티콘 사용하지마
28. 코딩 시 들여쓰기 항상 조심하고, 여러번 수정하지 않도록 항상 유의해
29. 중요 : 크롤러 개발시에는 무조건 실제 데이터를 크롤링 하도록 해라. 하드코딩, 더미데이터 크롤링은 아무런 의미가 없다. 쓰레기에 불과하다. 무조건 현시점 실제 데이터를 수집할 수 있도록 개발해야한다.
30. 절대 지켜야할 사항 : 절대로 더미데이터 쓰지마

---

## [MEMORY REFRESH - 2025-12-11] v2.1 업데이트

### 완료된 작업

1. **온톨로지 엔진 memory_manager 통합 완료**
   - `memory_manager.py`에 자동 분류 기능 추가
   - `update_memory()` 호출 시 자동으로 온톨로지 분류
   - YAML frontmatter에 `ontology_category`, `ontology_path`, `ontology_confidence` 저장
   - confidence >= 0.50 시 분류 적용

2. **Reference History 벤치마크 수정**
   - 테스트 시나리오 5개 → 10개로 확장
   - 키워드 매칭 로직 개선
   - 정확도: 80% → 100%

3. **마스터플랜 v2.1 업데이트**
   - Section 23: 학문적 기법 접목 계획 (엔트로피, 그래프, 시맨틱 웹)
   - Section 24: Feature Flags (티어별 기능 분리)
   - Section 25: 온톨로지 엔진 통합 상태

### 핵심 정책 결정

| 항목 | 정책 |
|------|------|
| **엔트로피/그래프 기법** | 베타테스트 결과 보고 추가 여부 결정 (Pro+ 티어) |
| **시맨틱 웹 추론** | Enterprise 전용, **사전 구현 필수** |
| **온톨로지 엔진** | Pro 이상에서 활성화 (구현 완료) |

### 시맨틱 웹 엔진 정책 (Enterprise 전용)

```
Enterprise 고객 생기면 바로 제공해야 함 → 사전 구현 필수

기능:
- 전이적 관계 추론 (A→B, B→C ⇒ A→C)
- 충돌 감지 (정책 충돌, 버전 충돌)
- N-hop 관계 탐색

구현 파일: core/semantic_web.py (예정)
```

### Feature Flags 티어별 매핑

| 기능 | Free | Pro | Enterprise |
|------|------|-----|------------|
| 온톨로지 | X | O | O |
| Reference History | X | O | O |
| Smart Context | X | O | O |
| **시맨틱 웹** | X | X | **O** |
| Multi-PC 동기화 | X | X | O |

### 구현 대기 항목

1. **시맨틱 웹 엔진** (`core/semantic_web.py`)
   - Enterprise 전용
   - OWL/RDF 스타일 관계 추론
   - memory_manager 통합 필요

2. **Feature Flags 런타임 체크**
   - `config.py` 또는 `license_manager.py`에 구현
   - 티어별 기능 활성화/비활성화

---

## [MEMORY REFRESH - 2025-12-09] 이전 업데이트

### 마스터 플랜 업데이트 완료

`CORTEX_MASTER_PLAN.md` 파일이 대폭 업데이트되었습니다.

**반드시 확인해야 할 변경 사항:**

1. **온톨로지 엔진 (구현 완료)**: Section 9
   - 핵심 차별화 기능
   - Tier 1/2에서만 활성화
   - `ontology_engine.py` 구현 완료
   - `memory_manager.py` 통합 완료

2. **3-Tier 가격 모델 (변경)**: Section 10
   - 기존: 30명 베타 1년 무료
   - 변경: Free / $15 Pro / $20 Premium
   - Trial: 30일 (Tier 2 기능)

3. **하이브리드 아키텍처 (변경)**: Section 11
   - 기존: 완전 로컬
   - 변경: 로컬 MCP + 중앙 라이센스 서버
   - 라이센스 캐싱 72시간 (오프라인 작동)

4. **Paddle Affiliate (신규)**: Section 18
   - 추천인: 첫 결제 20% 커미션 (일회성)
   - 피추천인: Trial 30일 + 가입 시 15일 무료

5. **알파 테스트 로그 시스템 (신규)**: Section 20
   - 기능별 로그 수집
   - `~/.cortex/logs/alpha_test/` 디렉토리

6. **Phase 2 개발 로드맵**: Section 21
   - Phase 1: 완료 (tag: phase1)
   - Phase 2: 온톨로지, 중앙 서버, Paddle 연동

### 기존 기능 업데이트 필요

| 모듈 | 변경 필요 사항 | 상태 |
|------|---------------|------|
| `ontology_engine.py` | 기본 분류 엔진 | 완료 |
| `memory_manager.py` | 온톨로지 통합 | 완료 |
| `semantic_web.py` | Enterprise 추론 엔진 | 대기 |
| `license_manager.py` | Tier 파라미터, 캐싱 로직, Trial 처리 | 대기 |
| `rag_engine.py` | Ontology 필터 연동 | 대기 |
| `automation_manager.py` | Tier별 "클릭 세금" 로직 | 대기 |

### 참조 문서

- `CORTEX_MASTER_PLAN.md` - 전체 기획 (Section 9-26)
- `launching.md` - 런칭 전 체크리스트
- `rival.md` - 경쟁사 분석

### Git Checkpoint

```
Phase 1 복원 필요 시:
git checkout phase1
```

---

*Last Memory Refresh: 2025-12-11*




Read and follow ./cortex_prompt.md
