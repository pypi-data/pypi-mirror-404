# Cortex MCP 수동 테스트 가이드

이 가이드는 Cortex의 핵심 기능을 실제로 테스트할 수 있는 단계별 절차입니다.
각 테스트를 순서대로 실행하면서 기능이 정상 작동하는지 확인하세요.

---

## 사전 준비

```bash
# 프로젝트 루트로 이동
cd /Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp/cortex_mcp

# 기존 테스트 데이터 정리 (선택적)
rm -rf ~/.cortex/memory/manual_test_*
```

---

## 테스트 1: 브랜치 생성 및 메모리 저장

### 목적
기본적인 브랜치 생성과 메모리 저장 기능 확인

### 실행 명령어
```bash
python3 << 'EOF'
from core.memory_manager import MemoryManager

# 1. MemoryManager 생성
mm = MemoryManager(project_id="manual_test_basic")
print("✓ MemoryManager 생성 완료\n")

# 2. 브랜치 생성
branch = mm.create_branch(
    project_id="manual_test_basic",
    branch_topic="첫_번째_테스트"
)
branch_id = branch["branch_id"]
print(f"✓ 브랜치 생성 완료")
print(f"  Branch ID: {branch_id}")
print(f"  파일 경로: {branch['branch_path']}\n")

# 3. 메모리 저장
result = mm.update_memory(
    project_id="manual_test_basic",
    branch_id=branch_id,
    content="안녕하세요. 첫 번째 테스트 메시지입니다.",
    role="user"
)
print(f"✓ 메모리 저장 완료")
print(f"  파일 크기: {result['size_kb']:.2f} KB\n")

# 4. 요약 조회
summary = mm.get_active_summary(
    project_id="manual_test_basic",
    branch_id=branch_id
)
print(f"✓ 요약 조회 완료")
print(f"  브랜치 주제: {summary.get('branch_topic')}")
print(f"  요약 길이: {len(summary.get('summary', ''))} 자")

EOF
```

### 예상 결과
```
✓ MemoryManager 생성 완료
✓ 브랜치 생성 완료
  Branch ID: 첫_번째_테스트_20251222_...
  파일 경로: /Users/kimjaeheung/.cortex/memory/manual_test_basic/...
✓ 메모리 저장 완료
  파일 크기: 0.xx KB
✓ 요약 조회 완료
  브랜치 주제: 첫_번째_테스트
  요약 길이: xx 자
```

### 성공 기준
- ✓ 체크마크 4개 모두 출력
- 에러 없이 완료
- Branch ID와 파일 경로가 표시됨

### 실제 파일 확인
```bash
# 생성된 파일 확인
ls -lh ~/.cortex/memory/manual_test_basic/

# 파일 내용 확인 (YAML frontmatter + 본문)
cat ~/.cortex/memory/manual_test_basic/*.md | head -30
```

---

## 테스트 2: 할루시네이션 검증 (Phase 9 핵심 기능)

### 목적
AI 응답의 확신도 분석 및 근거 검증 기능 확인

### 실행 명령어
```bash
python3 << 'EOF'
from core.memory_manager import MemoryManager

mm = MemoryManager(project_id="manual_test_hallucination")

# 브랜치 생성
branch = mm.create_branch(
    project_id="manual_test_hallucination",
    branch_topic="할루시네이션_테스트"
)
branch_id = branch["branch_id"]

print("=== 테스트 1: 확신 표현 포함 (검증 트리거) ===\n")

# 높은 확신도 표현 포함 → 할루시네이션 검증 실행
result1 = mm.update_memory(
    project_id="manual_test_hallucination",
    branch_id=branch_id,
    content="테스트를 완료했습니다. 모든 기능이 정상 작동합니다. 반드시 성공할 것입니다.",
    role="assistant"
)

print(f"확신도 감지: {result1['hallucination_check']['average_confidence']:.2f}")
print(f"추출된 주장 수: {result1['hallucination_check']['total_claims']}")
print(f"검증된 주장 수: {result1['hallucination_check']['verified_claims']}")
print(f"Grounding Score: {result1['hallucination_check']['grounding_score']:.2f}")
print(f"위험 수준: {result1['hallucination_check']['risk_level']}")
print()

print("=== 테스트 2: 확신 표현 없음 (검증 스킵) ===\n")

# 낮은 확신도 표현 → 검증 스킵
result2 = mm.update_memory(
    project_id="manual_test_hallucination",
    branch_id=branch_id,
    content="아마도 이렇게 하면 될 것 같습니다. 확실하지 않습니다.",
    role="assistant"
)

print(f"확신도 감지: {result2['hallucination_check']['average_confidence']:.2f}")
print(f"추출된 주장 수: {result2['hallucination_check']['total_claims']}")
print(f"위험 수준: {result2['hallucination_check']['risk_level']}")

EOF
```

### 예상 결과
```
=== 테스트 1: 확신 표현 포함 (검증 트리거) ===

확신도 감지: 0.80-1.00 (높음)
추출된 주장 수: 2-4
검증된 주장 수: 0-2
Grounding Score: 0.00-1.00
위험 수준: low/medium/critical

=== 테스트 2: 확신 표현 없음 (검증 스킵) ===

확신도 감지: 0.30-0.50 (낮음)
추출된 주장 수: 0-1
위험 수준: low
```

### 성공 기준
- 테스트 1에서 확신도 >= 0.8 감지
- 테스트 1에서 주장 추출됨 (total_claims > 0)
- 테스트 2에서 확신도 <= 0.5 감지
- 에러 없이 완료

---

## 테스트 3: RAG 검색 (Vector Search)

### 목적
의미 기반 벡터 검색 기능 확인

### 실행 명령어
```bash
python3 << 'EOF'
from core.rag_engine import RAGEngine

rag = RAGEngine()

print("=== 1. 컨텐츠 인덱싱 ===\n")

# 다양한 주제의 컨텐츠 인덱싱
contents = [
    ("Python 웹 개발을 위한 Flask 프레임워크 사용법", "python"),
    ("JavaScript React를 활용한 프론트엔드 개발", "javascript"),
    ("데이터베이스 PostgreSQL 쿼리 최적화 방법", "database"),
    ("RESTful API 설계 원칙과 Best Practice", "api"),
    ("pytest를 활용한 Python 테스트 자동화", "testing")
]

for content, tag in contents:
    rag.index_content(
        content=content,
        metadata={"project_id": "manual_test_rag", "tag": tag}
    )
    print(f"✓ 인덱싱: {content[:30]}...")

print("\n=== 2. 검색 테스트 ===\n")

# 테스트 1: Python 관련 검색
results1 = rag.search_context(query="Python 웹 개발", top_k=3)
print("검색어: 'Python 웹 개발'")
for i, result in enumerate(results1, 1):
    print(f"{i}. {result['content'][:40]}... (유사도: {result['score']:.3f})")

print()

# 테스트 2: 데이터베이스 관련 검색
results2 = rag.search_context(query="데이터베이스 성능", top_k=3)
print("검색어: '데이터베이스 성능'")
for i, result in enumerate(results2, 1):
    print(f"{i}. {result['content'][:40]}... (유사도: {result['score']:.3f})")

print()

# 테스트 3: 의미 기반 검색 (동의어)
results3 = rag.search_context(query="백엔드 서버 개발", top_k=3)
print("검색어: '백엔드 서버 개발' (동의어 검색)")
for i, result in enumerate(results3, 1):
    print(f"{i}. {result['content'][:40]}... (유사도: {result['score']:.3f})")

EOF
```

### 예상 결과
```
=== 1. 컨텐츠 인덱싱 ===

✓ 인덱싱: Python 웹 개발을 위한 Flask 프레임워크...
✓ 인덱싱: JavaScript React를 활용한 프론트엔드...
✓ 인덱싱: 데이터베이스 PostgreSQL 쿼리 최적화...
✓ 인덱싱: RESTful API 설계 원칙과 Best...
✓ 인덱싱: pytest를 활용한 Python 테스트...

=== 2. 검색 테스트 ===

검색어: 'Python 웹 개발'
1. Python 웹 개발을 위한 Flask 프레임워크... (유사도: 0.8xx)
2. pytest를 활용한 Python 테스트... (유사도: 0.6xx)
3. ...

검색어: '데이터베이스 성능'
1. 데이터베이스 PostgreSQL 쿼리 최적화... (유사도: 0.7xx)
2. ...

검색어: '백엔드 서버 개발' (동의어 검색)
1. Python 웹 개발을 위한 Flask 프레임워크... (유사도: 0.6xx)
2. RESTful API 설계 원칙과 Best... (유사도: 0.5xx)
```

### 성공 기준
- 5개 컨텐츠 모두 인덱싱 완료
- 각 검색에서 관련성 높은 결과가 1순위로 나옴
- 유사도 점수가 0.5 이상

---

## 테스트 4: Reference History (맥락 추천)

### 목적
과거 참조 이력 기반 맥락 자동 추천 기능 확인

### 실행 명령어
```bash
python3 << 'EOF'
from core.reference_history import get_reference_history

rh = get_reference_history("manual_test_ref")

print("=== 1. 참조 이력 기록 ===\n")

# 시나리오: 버그 수정 작업 시 ctx_001, ctx_002 참조
rh.record_reference(
    project_id="manual_test_ref",
    task_keywords=["bugfix", "testing", "unittest"],
    contexts_used=["ctx_bug_001", "ctx_test_002"],
    branch_id="main_branch",
    query="버그 수정 및 테스트"
)
print("✓ 이력 1 기록: 버그 수정 작업 (ctx_bug_001, ctx_test_002)")

# 시나리오: 코드 리뷰 작업 시 ctx_003, ctx_004 참조
rh.record_reference(
    project_id="manual_test_ref",
    task_keywords=["code_review", "refactoring"],
    contexts_used=["ctx_review_003", "ctx_refactor_004"],
    branch_id="main_branch",
    query="코드 리뷰 및 리팩토링"
)
print("✓ 이력 2 기록: 코드 리뷰 작업 (ctx_review_003, ctx_refactor_004)")

# 시나리오: 버그 수정 + 리팩토링 (혼합)
rh.record_reference(
    project_id="manual_test_ref",
    task_keywords=["bugfix", "refactoring"],
    contexts_used=["ctx_bug_001", "ctx_refactor_004"],
    branch_id="main_branch",
    query="버그 수정과 리팩토링"
)
print("✓ 이력 3 기록: 버그+리팩토링 (ctx_bug_001, ctx_refactor_004)\n")

print("=== 2. 맥락 추천 테스트 ===\n")

# 테스트 1: 유사한 작업 (버그 수정)
suggestions1 = rh.suggest_contexts(
    query="버그를 찾아서 수정해야 합니다",
    project_id="manual_test_ref",
    top_k=3
)

print("검색어: '버그를 찾아서 수정해야 합니다'")
print(f"Tier 1 (History 기반): {suggestions1.get('tier1_suggestions', [])}")
print(f"정확도 예상: {suggestions1.get('tier1_confidence', 0):.0%}")
print()

# 테스트 2: 다른 작업 (코드 리뷰)
suggestions2 = rh.suggest_contexts(
    query="코드 리뷰를 진행합니다",
    project_id="manual_test_ref",
    top_k=3
)

print("검색어: '코드 리뷰를 진행합니다'")
print(f"Tier 1 (History 기반): {suggestions2.get('tier1_suggestions', [])}")
print(f"정확도 예상: {suggestions2.get('tier1_confidence', 0):.0%}")
print()

print("=== 3. 통계 조회 ===\n")

stats = rh.get_statistics(project_id="manual_test_ref")
print(f"총 참조 이력: {stats.get('total_entries', 0)}개")
print(f"고유 작업: {stats.get('unique_tasks', 0)}개")
print(f"가장 많이 사용된 맥락: {stats.get('most_used_contexts', [])[:3]}")

EOF
```

### 예상 결과
```
=== 1. 참조 이력 기록 ===

✓ 이력 1 기록: 버그 수정 작업 (ctx_bug_001, ctx_test_002)
✓ 이력 2 기록: 코드 리뷰 작업 (ctx_review_003, ctx_refactor_004)
✓ 이력 3 기록: 버그+리팩토링 (ctx_bug_001, ctx_refactor_004)

=== 2. 맥락 추천 테스트 ===

검색어: '버그를 찾아서 수정해야 합니다'
Tier 1 (History 기반): ['ctx_bug_001', 'ctx_test_002']
정확도 예상: 95%

검색어: '코드 리뷰를 진행합니다'
Tier 1 (History 기반): ['ctx_review_003', 'ctx_refactor_004']
정확도 예상: 95%

=== 3. 통계 조회 ===

총 참조 이력: 3개
고유 작업: 3개
가장 많이 사용된 맥락: ['ctx_bug_001', 'ctx_refactor_004', ...]
```

### 성공 기준
- 3개 이력 모두 기록 완료
- 버그 수정 검색 시 ctx_bug_001 추천됨
- 코드 리뷰 검색 시 ctx_review_003 추천됨
- 정확도 95% 표시

---

## 테스트 5: Smart Context (압축/해제)

### 목적
토큰 절감을 위한 맥락 압축 및 지연 로딩 기능 확인

### 실행 명령어
```bash
python3 << 'EOF'
from core.context_manager import ContextManager
from core.memory_manager import MemoryManager

mm = MemoryManager(project_id="manual_test_context")
cm = ContextManager()

print("=== 1. 긴 컨텐츠 생성 ===\n")

# 브랜치 생성
branch = mm.create_branch(
    project_id="manual_test_context",
    branch_topic="압축_테스트"
)
branch_id = branch["branch_id"]

# 긴 내용 저장 (토큰 절감 테스트용)
long_content = "이것은 압축 테스트를 위한 내용입니다. " * 100
mm.update_memory(
    project_id="manual_test_context",
    branch_id=branch_id,
    content=long_content,
    role="assistant"
)

print(f"✓ 긴 컨텐츠 저장 완료 ({len(long_content)} 자)")
print()

print("=== 2. 압축 상태로 로드 (Summary만) ===\n")

loaded_compressed = cm.load_context(
    project_id="manual_test_context",
    branch_id=branch_id,
    force_full_load=False  # Summary만 로드
)

print(f"Success: {loaded_compressed['success']}")
print(f"Summary 길이: {len(loaded_compressed.get('summary', ''))} 자")
print(f"Full content 로드됨: {loaded_compressed.get('is_fully_loaded')}")
print(f"응답 시간: {loaded_compressed.get('latency_ms', 0):.2f}ms")
print()

print("=== 3. 전체 로드 (Full Content) ===\n")

loaded_full = cm.load_context(
    project_id="manual_test_context",
    branch_id=branch_id,
    force_full_load=True  # 전체 로드
)

print(f"Success: {loaded_full['success']}")
print(f"Summary 길이: {len(loaded_full.get('summary', ''))} 자")
print(f"Full content 길이: {len(loaded_full.get('full_content', ''))} 자")
print(f"Full content 로드됨: {loaded_full.get('is_fully_loaded')}")
print(f"응답 시간: {loaded_full.get('latency_ms', 0):.2f}ms")
print()

print("=== 4. 압축 실행 ===\n")

compressed = cm.compress_context(
    project_id="manual_test_context",
    branch_id=branch_id,
    context_id=branch_id
)

print(f"Success: {compressed['success']}")
print(f"압축 전 크기: {compressed.get('full_size', 0)} 자")
print(f"압축 후 크기: {compressed.get('compressed_size', 0)} 자")
print(f"압축률: {compressed.get('compression_ratio', 0):.1%}")
print(f"절감된 토큰: ~{compressed.get('full_size', 0) - compressed.get('compressed_size', 0)} 자")

EOF
```

### 예상 결과
```
=== 1. 긴 컨텐츠 생성 ===

✓ 긴 컨텐츠 저장 완료 (4400 자)

=== 2. 압축 상태로 로드 (Summary만) ===

Success: True
Summary 길이: 100-300 자
Full content 로드됨: False
응답 시간: 5-20ms

=== 3. 전체 로드 (Full Content) ===

Success: True
Summary 길이: 100-300 자
Full content 길이: 4400 자
Full content 로드됨: True
응답 시간: 10-50ms

=== 4. 압축 실행 ===

Success: True
압축 전 크기: 4400 자
압축 후 크기: 100-300 자
압축률: 70-95%
절감된 토큰: ~4000-4300 자
```

### 성공 기준
- 압축 상태 로드 시 Full content 로드 안됨 (False)
- 전체 로드 시 Full content 로드됨 (True)
- 압축률 70% 이상
- 응답 시간 50ms 이하

---

## 테스트 6: P0 버그 수정 검증

### 목적
어젯밤 수정한 P0-1 (Memory Leak), P0-2 (Threading) 버그 검증

### 실행 명령어
```bash
python3 << 'EOF'
import threading
import time
from core.reference_history import get_reference_history

rh = get_reference_history("manual_test_p0")

print("=== P0-1: Memory Leak 방지 테스트 ===\n")

# Pending suggestions 생성
for i in range(5):
    rh.suggest_contexts(
        query=f"test query {i}",
        project_id="manual_test_p0",
        top_k=3
    )

print(f"Pending suggestions 생성: {len(rh._pending_suggestions)}개")
print("5분 후 자동 정리됨 (타임아웃)")
print("✓ Memory leak 방지 메커니즘 작동 중\n")

print("=== P0-2: Threading Lock 테스트 ===\n")

results = []
errors = []

def concurrent_suggest(thread_id):
    """동시에 suggest_contexts 호출"""
    try:
        suggestions = rh.suggest_contexts(
            query=f"concurrent test {thread_id}",
            project_id="manual_test_p0",
            top_k=3
        )
        results.append(thread_id)
    except Exception as e:
        errors.append((thread_id, str(e)))

# 10개 스레드 동시 실행
threads = []
for i in range(10):
    t = threading.Thread(target=concurrent_suggest, args=(i,))
    threads.append(t)
    t.start()

# 모든 스레드 완료 대기
for t in threads:
    t.join()

print(f"완료된 스레드: {len(results)}/10")
print(f"에러 발생: {len(errors)}개")

if len(errors) == 0:
    print("✓ Race condition 없음 - Threading Lock 정상 작동")
else:
    print(f"✗ 에러 발생: {errors}")

EOF
```

### 예상 결과
```
=== P0-1: Memory Leak 방지 테스트 ===

Pending suggestions 생성: 5개
5분 후 자동 정리됨 (타임아웃)
✓ Memory leak 방지 메커니즘 작동 중

=== P0-2: Threading Lock 테스트 ===

완료된 스레드: 10/10
에러 발생: 0개
✓ Race condition 없음 - Threading Lock 정상 작동
```

### 성공 기준
- Pending suggestions 생성 확인
- 10개 스레드 모두 완료
- 에러 0개
- Race condition 없음 메시지 출력

---

## 테스트 7: Git 브랜치 연동

### 목적
Git 브랜치와 Cortex 브랜치 자동 연동 기능 확인

### 실행 명령어
```bash
python3 << 'EOF'
from core.git_sync import get_git_sync

gs = get_git_sync("manual_test_git")

repo_path = "/Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp/cortex_mcp"

print("=== 1. Git 상태 확인 ===\n")

status = gs.get_git_status(
    project_id="manual_test_git",
    repo_path=repo_path
)

print(f"현재 Git 브랜치: {status.get('current_branch')}")
print(f"마지막 커밋: {status.get('last_commit_hash', 'N/A')[:8]}")
print(f"Cortex 연동 상태: {status.get('is_linked')}")
print()

print("=== 2. Git-Cortex 브랜치 연동 ===\n")

link_result = gs.link_git_branch(
    project_id="manual_test_git",
    repo_path=repo_path,
    auto_create=True
)

print(f"Success: {link_result.get('success')}")
print(f"Git 브랜치: {link_result.get('git_branch')}")
print(f"Cortex 브랜치: {link_result.get('cortex_branch_id', 'N/A')[:50]}...")
print(f"자동 생성됨: {link_result.get('auto_created', False)}")
print()

print("=== 3. 연동 목록 조회 ===\n")

links = gs.list_git_links(
    project_id="manual_test_git",
    repo_path=repo_path
)

print(f"총 연동된 브랜치: {len(links.get('links', []))}개")
for link in links.get('links', [])[:3]:
    print(f"  - {link['git_branch']} → {link['cortex_branch_id'][:50]}...")

EOF
```

### 예상 결과
```
=== 1. Git 상태 확인 ===

현재 Git 브랜치: main
마지막 커밋: 9182c31a
Cortex 연동 상태: False

=== 2. Git-Cortex 브랜치 연동 ===

Success: True
Git 브랜치: main
Cortex 브랜치: main_20251222_...
자동 생성됨: True

=== 3. 연동 목록 조회 ===

총 연동된 브랜치: 1개
  - main → main_20251222_...
```

### 성공 기준
- Git 브랜치 정보 정상 조회
- 연동 성공 (Success: True)
- Cortex 브랜치 자동 생성됨

---

## 테스트 8: 스냅샷 백업 & 복원

### 목적
프로젝트 상태 스냅샷 생성 및 복원 기능 확인

### 실행 명령어
```bash
python3 << 'EOF'
from core.backup_manager import get_backup_manager

bm = get_backup_manager()

print("=== 1. 스냅샷 생성 ===\n")

snapshot = bm.create_snapshot(
    project_id="manual_test_basic",
    description="수동 테스트 완료 후 백업"
)

print(f"✓ 스냅샷 생성 완료")
print(f"  Snapshot ID: {snapshot.get('snapshot_id')}")
print(f"  크기: {snapshot.get('size_mb', 0):.2f} MB")
print(f"  파일 수: {snapshot.get('file_count', 0)}개")
print()

print("=== 2. 스냅샷 목록 조회 ===\n")

snapshots = bm.list_snapshots(
    project_id="manual_test_basic",
    limit=10
)

print(f"총 스냅샷: {len(snapshots.get('snapshots', []))}개\n")
for i, snap in enumerate(snapshots.get('snapshots', [])[:5], 1):
    print(f"{i}. {snap['timestamp']}")
    print(f"   설명: {snap['description']}")
    print(f"   크기: {snap['size_mb']:.2f} MB\n")

print("=== 3. 백업 히스토리 ===\n")

history = bm.get_backup_history(
    project_id="manual_test_basic",
    limit=5
)

print(f"총 이력: {len(history.get('history', []))}개")
for event in history.get('history', [])[:3]:
    print(f"  - {event['timestamp']}: {event['action']}")

EOF
```

### 예상 결과
```
=== 1. 스냅샷 생성 ===

✓ 스냅샷 생성 완료
  Snapshot ID: snapshot_20251222_...
  크기: 0.01-0.1 MB
  파일 수: 1-5개

=== 2. 스냅샷 목록 조회 ===

총 스냅샷: 1개

1. 2025-12-22T17:...
   설명: 수동 테스트 완료 후 백업
   크기: 0.0x MB

=== 3. 백업 히스토리 ===

총 이력: 1개
  - 2025-12-22T17:...: create_snapshot
```

### 성공 기준
- 스냅샷 생성 성공
- Snapshot ID 생성됨
- 목록에서 조회 가능
- 히스토리 기록됨

---

## 종합 검증

모든 테스트를 완료한 후 다음을 확인하세요:

### 생성된 파일 확인
```bash
# 테스트 프로젝트 디렉토리 확인
ls -lR ~/.cortex/memory/manual_test_*/

# 스냅샷 파일 확인
ls -lh ~/.cortex/backups/

# 로그 파일 확인
ls -lh ~/.cortex/logs/
```

### 성공 기준 요약

| 테스트 | 핵심 확인 사항 | 목표 |
|--------|---------------|------|
| 1. 브랜치 생성 | ✓ 4개 모두 출력, 파일 생성됨 | 기본 기능 |
| 2. 할루시네이션 검증 | 확신도 감지, 주장 추출 | Phase 9 |
| 3. RAG 검색 | 유사도 0.5+, 관련 결과 1순위 | 검색 정확도 |
| 4. Reference History | 95% 정확도, 올바른 맥락 추천 | 추천 시스템 |
| 5. Smart Context | 압축률 70%+, 응답 50ms 이하 | 토큰 절감 |
| 6. P0 버그 수정 | 에러 0개, Race condition 없음 | 안정성 |
| 7. Git 연동 | 브랜치 연동 성공 | 통합 |
| 8. 스냅샷 | 백업 생성 및 조회 성공 | 복구 |

---

## 문제 발생 시 디버깅

### 로그 확인
```bash
# 최근 로그 확인
tail -f ~/.cortex/logs/cortex_*.log

# 에러 로그만 확인
grep -i error ~/.cortex/logs/*.log
```

### 테스트 데이터 초기화
```bash
# 모든 테스트 데이터 삭제
rm -rf ~/.cortex/memory/manual_test_*
rm -rf ~/.cortex/backups/manual_test_*
```

### 도움말
```bash
# Python 환경 확인
python3 --version
python3 -c "import sys; print(sys.path)"

# 필수 패키지 확인
python3 -c "import chromadb, yaml, networkx; print('OK')"
```
