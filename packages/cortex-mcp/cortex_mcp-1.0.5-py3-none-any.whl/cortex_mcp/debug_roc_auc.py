"""
ROC-AUC 테스트 디버깅 스크립트

각 케이스의 grounding score 분포를 확인하여 문제점을 파악합니다.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cortex_mcp.core.memory_manager import MemoryManager
from sklearn.metrics import roc_auc_score
import json

def create_labeled_dataset():
    """레이블된 데이터셋 생성 (테스트 코드와 동일)"""
    labeled_responses = []

    # 1. Grounded 응답 (60개)
    for i in range(60):
        labeled_responses.append({
            "text": f"파일 grounded_file_{i}.py를 수정했습니다. 버그를 수정하고 기능을 구현했습니다.",
            "is_hallucination": False
        })

    # 2. Hallucination 응답 (40개)
    for i in range(40):
        labeled_responses.append({
            "text": f"환상파일_{i}.py를 구현했습니다. 모든 테스트가 통과했습니다.",
            "is_hallucination": True
        })

    return labeled_responses

def main():
    print("=" * 80)
    print("ROC-AUC 디버깅 분석")
    print("=" * 80)

    # 1. MemoryManager 초기화
    project_id = "test_hallucination_roc"
    memory_manager = MemoryManager(project_id=project_id)

    # 2. 브랜치 생성
    branch_result = memory_manager.create_branch(
        project_id=project_id,
        branch_topic="ROC-AUC 디버깅"
    )
    branch_id = branch_result.get("branch_id")

    # 3. 데이터셋 생성
    labeled_responses = create_labeled_dataset()

    # 4. 각 케이스 처리 및 점수 수집
    scores = []
    labels = []

    grounded_scores = []  # is_hallucination=False인 경우
    hallucination_scores = []  # is_hallucination=True인 경우

    print(f"\n총 {len(labeled_responses)}개 케이스 처리 중...\n")

    for idx, response in enumerate(labeled_responses):
        # Context 설정
        if not response["is_hallucination"]:
            file_name = f"grounded_file_{idx}.py"
            context = {
                "files_modified": {
                    file_name: {
                        "diff": f"+def fixed_function():\n+    return 'fixed'\n",
                        "status": "modified",
                        "lines_added": 2,
                        "lines_removed": 0
                    }
                }
            }
        else:
            context = {"files_modified": {}}  # Empty for hallucination

        # update_memory 호출
        result = memory_manager.update_memory(
            project_id=project_id,
            branch_id=branch_id,
            content=response["text"],
            role="assistant",
            context=context
        )

        grounding_score = result.get("grounding_score", 0.0)
        scores.append(grounding_score)
        labels.append(1 if not response["is_hallucination"] else 0)

        # 분류별 점수 저장
        if not response["is_hallucination"]:
            grounded_scores.append(grounding_score)
        else:
            hallucination_scores.append(grounding_score)

        # 진행 상황 출력
        if (idx + 1) % 20 == 0:
            print(f"  처리 완료: {idx + 1}/{len(labeled_responses)}")

    # 5. ROC-AUC 계산
    auc = roc_auc_score(labels, scores)

    # 6. 통계 분석
    print(f"\n" + "=" * 80)
    print("분석 결과")
    print("=" * 80)

    print(f"\n[전체 통계]")
    print(f"  - ROC-AUC: {auc:.3f}")
    print(f"  - 평균 Grounding Score: {sum(scores)/len(scores):.3f}")
    print(f"  - 최소: {min(scores):.3f}, 최대: {max(scores):.3f}")

    print(f"\n[Grounded 응답 (60개) - 높은 점수 기대]")
    print(f"  - 평균: {sum(grounded_scores)/len(grounded_scores):.3f}")
    print(f"  - 최소: {min(grounded_scores):.3f}, 최대: {max(grounded_scores):.3f}")
    print(f"  - 0.7 이상 비율: {sum(1 for s in grounded_scores if s >= 0.7)/len(grounded_scores)*100:.1f}%")
    print(f"  - 0.3 미만 비율: {sum(1 for s in grounded_scores if s < 0.3)/len(grounded_scores)*100:.1f}%")

    print(f"\n[Hallucination 응답 (40개) - 낮은 점수 기대]")
    print(f"  - 평균: {sum(hallucination_scores)/len(hallucination_scores):.3f}")
    print(f"  - 최소: {min(hallucination_scores):.3f}, 최대: {max(hallucination_scores):.3f}")
    print(f"  - 0.7 이상 비율: {sum(1 for s in hallucination_scores if s >= 0.7)/len(hallucination_scores)*100:.1f}%")
    print(f"  - 0.3 미만 비율: {sum(1 for s in hallucination_scores if s < 0.3)/len(hallucination_scores)*100:.1f}%")

    # 7. 문제 케이스 출력
    print(f"\n[문제 케이스 분석]")

    # Grounded인데 점수가 낮은 경우 (False Negative)
    false_negatives = [(idx, s) for idx, s in enumerate(grounded_scores) if s < 0.3]
    if false_negatives:
        print(f"\n  False Negative (Grounded인데 낮은 점수): {len(false_negatives)}개")
        for idx, score in false_negatives[:5]:  # 최대 5개만 출력
            print(f"    - Case {idx}: score={score:.3f}")

    # Hallucination인데 점수가 높은 경우 (False Positive)
    false_positives = [(idx, s) for idx, s in enumerate(hallucination_scores) if s >= 0.7]
    if false_positives:
        print(f"\n  False Positive (Hallucination인데 높은 점수): {len(false_positives)}개")
        for idx, score in false_positives[:5]:  # 최대 5개만 출력
            print(f"    - Case {idx + 60}: score={score:.3f}")

    print(f"\n" + "=" * 80)

    # 8. 결론
    if auc >= 0.75:
        print("결론: 목표 달성")
    else:
        print(f"결론: 목표 미달 (현재 {auc:.3f}, 목표 0.75)")

        if len(false_positives) > len(false_negatives):
            print("주요 문제: Hallucination 케이스의 점수가 너무 높음")
            print("  → claim_verifier가 코드베이스를 스캔하여 false evidence를 반환하고 있을 가능성")
        elif len(false_negatives) > len(false_positives):
            print("주요 문제: Grounded 케이스의 점수가 너무 낮음")
            print("  → claim_evidence_map이 제대로 채워지지 않고 있을 가능성")
        else:
            print("주요 문제: 두 그룹의 점수 분포가 겹침")

    print("=" * 80)

if __name__ == "__main__":
    main()
