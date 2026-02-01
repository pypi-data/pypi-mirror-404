# 의존성 버전 고정 (Dependency Version Pinning)

## 배경

알파 테스트에서 PyTorch 관련 에러가 발생하여 의존성 버전을 안정적인 조합으로 고정했습니다.

## 고정된 버전 (2025-12-19)

### Core Dependencies

| 패키지 | 버전 | 이유 |
|--------|------|------|
| `numpy` | 1.26.4 | PyTorch 2.1.2와 호환성 (NumPy 2.x는 비호환) |
| `torch` | 2.1.2 | 안정적인 LTS 버전 |
| `transformers` | 4.36.2 | sentence-transformers 2.5.1과 호환 |
| `sentence-transformers` | 2.5.1 | 검증된 안정 버전 |

### 호환성 매트릭스

```
numpy 1.26.4 ←→ torch 2.1.2 ←→ transformers 4.36.2 ←→ sentence-transformers 2.5.1
```

## 검증 결과

- **Fuzzy Ontology 테스트**: 8/8 통과
- **전체 단위 테스트**: 103/103 통과
- **PyTorch 초기화 에러**: 해결됨

## 에러 이력

### 이전 문제 (NumPy 2.2.6 + PyTorch 2.1.2)
```
RuntimeError: Numpy is not available
Failed to initialize NumPy: _ARRAY_API not found
```

### 해결 방법
NumPy를 1.26.4로 다운그레이드하여 PyTorch 2.1.2와 호환되도록 수정

## 버전 업그레이드 시 주의사항

1. **NumPy 2.x로 업그레이드 시**: PyTorch도 2.2+ 버전으로 함께 업그레이드 필요
2. **sentence-transformers 업그레이드 시**: transformers 호환성 확인 필수
3. **변경 후 필수 테스트**:
   ```bash
   pytest cortex_mcp/tests/test_fuzzy_ontology.py -v
   pytest cortex_mcp/tests/unit/ -v
   ```

## 참조

- PyTorch 호환성: https://github.com/pytorch/pytorch/wiki/PyTorch-Versions
- sentence-transformers: https://www.sbert.net/
