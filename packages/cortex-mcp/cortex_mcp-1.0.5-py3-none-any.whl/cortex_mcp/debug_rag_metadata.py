#!/usr/bin/env python3
"""
RAG 인덱스 메타데이터 디버그 스크립트

Branch Isolation 버그를 진단하기 위해 ChromaDB에 실제로 저장된
메타데이터를 확인합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.rag_engine import RAGEngine
from core.memory_manager import MemoryManager
import tempfile


def main():
    print("=" * 80)
    print("RAG 메타데이터 디버그 스크립트")
    print("=" * 80)

    # 임시 디렉토리 생성
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # MemoryManager 초기화
        test_project_id = "debug_test_project"
        memory_manager = MemoryManager(
            project_id=test_project_id, memory_dir=temp_path
        )

        # 두 개의 브랜치 생성
        branch_a = "test_branch_a"
        branch_b = "test_branch_b"

        memory_manager.create_branch(
            project_id=test_project_id, branch_topic=branch_a
        )
        memory_manager.create_branch(
            project_id=test_project_id, branch_topic=branch_b
        )

        # Branch A에 authentication 관련 맥락 저장
        print("\n[1] Branch A에 authentication 맥락 저장 중...")
        memory_manager.update_memory(
            project_id=test_project_id,
            branch_id=branch_a,
            content="User authentication system with JWT tokens",
            role="assistant",
            verified=True,
        )

        # Branch B에 payment 관련 맥락 저장
        print("[2] Branch B에 payment 맥락 저장 중...")
        memory_manager.update_memory(
            project_id=test_project_id,
            branch_id=branch_b,
            content="Payment processing with Stripe API integration",
            role="assistant",
            verified=True,
        )

        # RAG Engine 초기화
        rag_engine = RAGEngine()

        # ChromaDB에 저장된 모든 문서 조회
        print("\n[3] ChromaDB에 저장된 모든 문서 조회...")
        collection = rag_engine._init_chroma()

        try:
            all_docs = collection.get(include=["documents", "metadatas"])

            if not all_docs["ids"]:
                print("⚠️  ChromaDB에 문서가 없습니다!")
                return

            print(f"\n총 {len(all_docs['ids'])}개 문서 발견\n")

            for i, doc_id in enumerate(all_docs["ids"]):
                metadata = all_docs["metadatas"][i] if all_docs["metadatas"] else {}
                content = all_docs["documents"][i] if all_docs["documents"] else ""

                print(f"문서 #{i + 1}:")
                print(f"  ID: {doc_id}")
                print(f"  Content: {content[:60]}...")
                print(f"  Metadata:")
                for key, value in metadata.items():
                    print(f"    - {key}: {value}")
                print()

        except Exception as e:
            print(f"❌ 문서 조회 실패: {type(e).__name__}: {str(e)}")
            return

        # Branch별 검색 테스트
        print("\n[4] Branch별 검색 테스트...")

        # Branch B에서 'authentication' 검색 (결과: 0개 예상)
        print(f"\n검색 1: Branch B에서 'authentication' 검색 (예상: 0개)")
        search_b_auth = rag_engine.search_context(
            query="authentication user login",
            project_id=test_project_id,
            branch_id=branch_b,
            top_k=10,
        )
        print(f"  결과: {search_b_auth.get('total_found', 0)}개")
        if search_b_auth.get("results"):
            for result in search_b_auth["results"]:
                print(f"    - {result['content'][:60]}...")
                rel_score = result.get('relevance_score', 'N/A')
                dist = result.get('distance', 'N/A')
                rel_str = f"{rel_score:.3f}" if isinstance(rel_score, (int, float)) else str(rel_score)
                dist_str = f"{dist:.3f}" if isinstance(dist, (int, float)) else str(dist)
                print(f"      Relevance: {rel_str}")
                print(f"      Distance: {dist_str}")

        # Branch A에서 'payment' 검색 (결과: 0개 예상)
        print(f"\n검색 2: Branch A에서 'payment' 검색 (예상: 0개)")
        search_a_payment = rag_engine.search_context(
            query="payment subscription billing",
            project_id=test_project_id,
            branch_id=branch_a,
            top_k=10,
        )
        print(f"  결과: {search_a_payment.get('total_found', 0)}개")
        if search_a_payment.get("results"):
            for result in search_a_payment["results"]:
                print(f"    - {result['content'][:60]}...")
                rel_score = result.get('relevance_score', 'N/A')
                dist = result.get('distance', 'N/A')
                rel_str = f"{rel_score:.3f}" if isinstance(rel_score, (int, float)) else str(rel_score)
                dist_str = f"{dist:.3f}" if isinstance(dist, (int, float)) else str(dist)
                print(f"      Relevance: {rel_str}")
                print(f"      Distance: {dist_str}")

        # 브랜치 필터 없이 검색 (결과: 2개 예상)
        print(f"\n검색 3: 브랜치 필터 없이 'authentication' 검색 (예상: 1개)")
        search_no_filter = rag_engine.search_context(
            query="authentication user login",
            project_id=test_project_id,
            branch_id=None,
            top_k=10,
        )
        print(f"  결과: {search_no_filter.get('total_found', 0)}개")
        if search_no_filter.get("results"):
            for result in search_no_filter["results"]:
                print(f"    - {result['content'][:60]}...")
                rel_score = result.get('relevance_score', 'N/A')
                dist = result.get('distance', 'N/A')
                rel_str = f"{rel_score:.3f}" if isinstance(rel_score, (int, float)) else str(rel_score)
                dist_str = f"{dist:.3f}" if isinstance(dist, (int, float)) else str(dist)
                print(f"      Relevance: {rel_str}")
                print(f"      Distance: {dist_str}")

        # 결론
        print("\n" + "=" * 80)
        print("진단 결론:")
        print("=" * 80)

        cross_leak_b = search_b_auth.get("total_found", 0)
        cross_leak_a = search_a_payment.get("total_found", 0)

        if cross_leak_b == 0 and cross_leak_a == 0:
            print("✅ Branch Isolation이 정상 작동합니다!")
        else:
            print("❌ Branch Isolation 버그 발견:")
            if cross_leak_b > 0:
                print(
                    f"  - Branch B에서 {cross_leak_b}개의 authentication 문서 누수"
                )
            if cross_leak_a > 0:
                print(f"  - Branch A에서 {cross_leak_a}개의 payment 문서 누수")
            print(
                "\n원인: RAG 검색 시 branch_id 필터가 제대로 작동하지 않음"
            )


if __name__ == "__main__":
    main()
