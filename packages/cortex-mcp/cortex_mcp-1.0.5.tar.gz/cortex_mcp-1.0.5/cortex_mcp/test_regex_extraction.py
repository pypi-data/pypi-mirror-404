"""
파일 참조 추출 Regex 패턴 테스트
"""

import re

# 현재 ClaimVerifier의 패턴
current_pattern = r'(?:[\w./]+/)?[\w.]+\.(?:py|js|ts|tsx|jsx|java|cpp|c|h|go|rs|md|yaml|yml|json|xml|toml|ini|cfg|conf|txt)'

# 테스트 케이스
test_cases = [
    ('단일 파일 (조사 포함)', 'memory_manager.py 파일을 수정했습니다'),
    ('2개 파일 (조사 포함)', 'memory_manager.py를 수정하고 claim_verifier.py도 수정했습니다'),
    ('경로 포함', 'core/memory_manager.py와 core/claim_verifier.py를 수정'),
    ('쉼표 구분', 'test.py, foo.py, bar.py 세 파일 수정'),
    ('영어 문장', 'I modified memory_manager.py and claim_verifier.py files'),
]

print('=' * 80)
print('파일 참조 추출 Regex 테스트')
print('=' * 80)
print()

for label, text in test_cases:
    matches = re.findall(current_pattern, text, re.IGNORECASE)

    print(f'[{label}]')
    print(f'입력: {text}')
    print(f'추출: {matches}')
    print(f'개수: {len(matches)}개')
    print()

print('=' * 80)
print('문제 분석')
print('=' * 80)
print()

# 가장 중요한 실패 케이스 분석
text = 'memory_manager.py를 수정하고 claim_verifier.py도 수정했습니다'
matches = re.findall(current_pattern, text, re.IGNORECASE)

expected = ['memory_manager.py', 'claim_verifier.py']
print(f'입력: {text}')
print(f'기대값: {expected} ({len(expected)}개)')
print(f'실제값: {matches} ({len(matches)}개)')
print()

if len(matches) < len(expected):
    print(f'FAIL: {len(expected) - len(matches)}개의 파일 참조를 놓쳤습니다!')
    print()

    # 개선된 패턴 제안
    print('개선 방안 테스트:')

    # 방안 1: 한글 조사 앞에서도 매칭되도록 경계 조건 추가
    improved_pattern_1 = r'[\w./]+\.(?:py|js|ts|tsx|jsx|java|cpp|c|h|go|rs|md|yaml|yml|json|xml|toml|ini|cfg|conf|txt)'

    matches_improved = re.findall(improved_pattern_1, text, re.IGNORECASE)
    print(f'  패턴 1 (단순화): {matches_improved} ({len(matches_improved)}개)')
else:
    print('PASS: 모든 파일 참조를 정확히 추출했습니다!')
