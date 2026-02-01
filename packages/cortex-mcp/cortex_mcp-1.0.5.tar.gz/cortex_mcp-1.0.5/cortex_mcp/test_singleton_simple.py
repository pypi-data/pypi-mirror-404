"""
RAGEngine SentenceTransformer 싱글톤 간단 테스트
multiprocessing 없이 직접 테스트
"""

import sys
import time
from pathlib import Path

# 직접 import
sys.path.insert(0, str(Path(__file__).parent))

from core.rag_engine import RAGEngine


def main():
    print("[테스트] SentenceTransformer 싱글톤 캐싱\n")

    # 첫 번째 인스턴스
    print("=" * 60)
    print("[1차] 첫 번째 RAGEngine 생성 + 모델 로딩")
    start = time.time()
    rag1 = RAGEngine()
    # 모델 초기화 트리거
    model1 = rag1._init_embedding_model()
    duration1 = time.time() - start
    print(f"소요 시간: {duration1:.3f}초")
    print(f"모델 객체 ID: {id(model1)}")

    # 두 번째 인스턴스
    print("\n" + "=" * 60)
    print("[2차] 두 번째 RAGEngine 생성 + 캐시된 모델 사용")
    start = time.time()
    rag2 = RAGEngine()
    # 캐시된 모델 사용
    model2 = rag2._init_embedding_model()
    duration2 = time.time() - start
    print(f"소요 시간: {duration2:.3f}초")
    print(f"모델 객체 ID: {id(model2)}")

    # 검증
    print("\n" + "=" * 60)
    print("[검증]")
    print(f"모델 객체 동일성: {model1 is model2}")
    print(f"1차 소요: {duration1:.3f}초")
    print(f"2차 소요: {duration2:.3f}초")
    print(f"절약 시간: {duration1 - duration2:.3f}초")

    if duration1 > 0:
        improvement = ((duration1 - duration2) / duration1) * 100
        print(f"개선율: {improvement:.1f}%")

    if model1 is model2:
        print("\n✅ PASS: 싱글톤 캐싱 정상 작동")
    else:
        print("\n❌ FAIL: 모델이 캐싱되지 않음")


if __name__ == "__main__":
    main()
