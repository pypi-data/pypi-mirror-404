# Cortex MCP Comprehensive Benchmark Test Plan

## Executive Summary

This document outlines a comprehensive testing strategy for Cortex MCP, covering all 13 core features across 4 categories. Tests are designed to provide quantifiable, reproducible, and publicly verifiable results.

---

## Test Philosophy

**"Show, Don't Tell"**
- All test scripts are public and reproducible
- Results are measured with objective metrics
- Comparison tests use identical scenarios (Cortex vs No-Cortex)
- Standard benchmarks provide industry comparison

---

## Category 1: Context Integrity (3 Features)

### 1.1 Smart Context - Token Efficiency Test

**Objective**: Measure compression ratio and recall accuracy

**Test Scenario**:
- Create 100 context entries (20KB total)
- Compress using Smart Context
- Measure: compression ratio, recall accuracy, latency

**Success Criteria**:
- Compression: ≥70%
- Recall accuracy: 100%
- Access latency: <50ms

**Test Script**: `tests/benchmark/test_smart_context.py`

```python
def test_token_efficiency():
    # Generate 100 contexts (20KB)
    contexts = generate_test_contexts(100, avg_size=200)

    # Compress
    compressed = smart_context.compress(contexts)

    # Measure
    compression_ratio = (1 - compressed.size / contexts.size) * 100

    # Recall test
    for original in contexts:
        recalled = smart_context.recall(original.id)
        assert recalled.content == original.content

    assert compression_ratio >= 70
```

**Expected Result**:
- Compression: 97.8% (current benchmark)
- Recall: 100%
- Latency: 28.98ms average

---

### 1.2 Reference History - Prediction Accuracy Test

**Objective**: Measure context recommendation accuracy

**Test Scenario**:
- 50 historical task patterns
- Each task uses 3-5 contexts
- Train on 40 tasks, test on 10 tasks
- Measure: Top-3 accuracy, Top-5 accuracy, precision@k

**Success Criteria**:
- Top-3 accuracy: ≥85%
- Top-5 accuracy: ≥95%
- Precision@3: ≥90%

**Test Script**: `tests/benchmark/test_reference_history.py`

```python
def test_reference_accuracy():
    # Historical patterns
    history = load_reference_history(50)

    # Split train/test
    train, test = split(history, 0.8)

    # Train
    ref_history.train(train)

    # Test
    correct_top3 = 0
    correct_top5 = 0

    for task in test:
        suggestions = ref_history.suggest(task.query, top_k=5)

        if task.actual_contexts[:3] in suggestions[:3]:
            correct_top3 += 1
        if task.actual_contexts in suggestions[:5]:
            correct_top5 += 1

    top3_acc = correct_top3 / len(test)
    top5_acc = correct_top5 / len(test)

    assert top3_acc >= 0.85
    assert top5_acc >= 0.95
```

**Expected Result**:
- Top-3: 95%
- Top-5: 100%

---

### 1.3 Branch Organization - Context Isolation Test

**Objective**: Verify branch isolation and switching overhead

**Test Scenario**:
- Create 5 branches with 20 contexts each
- Switch between branches 100 times
- Measure: isolation (no leakage), switch latency

**Success Criteria**:
- Isolation: 100% (no context leakage)
- Switch latency: <100ms

**Test Script**: `tests/benchmark/test_branch_isolation.py`

---

## Category 2: Truth & Verification (4 Features)

### 2.1 Hallucination Detection - False Claim Detection Rate

**Objective**: Measure hallucination detection accuracy

**Test Scenario**:
- 100 AI responses with known hallucinations
- 50 true claims, 50 false claims
- Measure: Precision, Recall, F1-score

**Success Criteria**:
- Precision: ≥90%
- Recall: ≥85%
- F1-score: ≥87%

**Test Script**: `tests/benchmark/test_hallucination_detection.py`

```python
def test_hallucination_detection():
    # Ground truth dataset
    responses = load_hallucination_dataset(100)

    tp, fp, tn, fn = 0, 0, 0, 0

    for response in responses:
        result = claim_extractor.verify(response.text, response.context)

        if result.is_hallucination and response.is_hallucination:
            tp += 1
        elif result.is_hallucination and not response.is_hallucination:
            fp += 1
        elif not result.is_hallucination and not response.is_hallucination:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * (precision * recall) / (precision + recall)

    assert precision >= 0.90
    assert recall >= 0.85
    assert f1 >= 0.87
```

---

### 2.2 Grounding Score - Correlation Test

**Objective**: Validate grounding score correlation with human judgment

**Test Scenario**:
- 100 AI responses with human-rated grounding quality
- Measure: Pearson correlation, Spearman correlation

**Success Criteria**:
- Pearson correlation: ≥0.80
- Spearman correlation: ≥0.75

**Test Script**: `tests/benchmark/test_grounding_score.py`

---

### 2.3 Claim Extraction - Extraction Accuracy

**Objective**: Measure claim extraction precision and recall

**Test Scenario**:
- 100 annotated responses with known claims
- Measure: Claim extraction precision, recall

**Success Criteria**:
- Precision: ≥85%
- Recall: ≥80%

---

### 2.4 Contradiction Detection - Detection Rate

**Objective**: Measure contradiction detection accuracy

**Test Scenario**:
- 50 responses with internal contradictions
- 50 consistent responses
- Measure: Precision, Recall

**Success Criteria**:
- Precision: ≥85%
- Recall: ≥80%

---

## Category 3: Stability & Recovery (3 Features)

### 3.1 Snapshot/Restore - Data Integrity Test

**Objective**: Verify snapshot integrity and restore accuracy

**Test Scenario**:
- Create 1000 contexts
- Take snapshot
- Modify 100 contexts
- Restore snapshot
- Measure: restore accuracy, time

**Success Criteria**:
- Restore accuracy: 100%
- Restore time: <5 seconds

**Test Script**: `tests/benchmark/test_snapshot_restore.py`

---

### 3.2 Git Integration - Sync Reliability Test

**Objective**: Measure Git branch sync reliability

**Test Scenario**:
- Create 10 Git branches
- Link to 10 Cortex branches
- Switch branches 100 times
- Measure: sync success rate, latency

**Success Criteria**:
- Sync success: 100%
- Sync latency: <200ms

---

### 3.3 Plan A/B Automation - Adaptation Test

**Objective**: Measure automation adaptation effectiveness

**Test Scenario**:
- Simulate 100 user interactions
- 70% accept, 30% reject (trigger Plan B)
- Measure: switch accuracy, false positive rate

**Success Criteria**:
- Switch trigger accuracy: ≥90%
- False positive rate: ≤5%

---

## Category 4: Scalability & Continuity (3 Features)

### 4.1 Cross-Session Memory - Persistence Test

**Objective**: Verify context persistence across sessions

**Test Scenario**:
- Session 1: Create 100 contexts
- Close session
- Session 2: Recall all contexts
- Measure: recall accuracy, latency

**Success Criteria**:
- Recall accuracy: 100%
- Session startup: <3 seconds

---

### 4.2 Cloud Sync - E2E Encryption Test

**Objective**: Verify encryption and sync integrity

**Test Scenario**:
- Encrypt 10MB of context data
- Upload to cloud
- Download on different machine
- Decrypt and verify
- Measure: encryption time, sync time, integrity

**Success Criteria**:
- Encryption: AES-256-GCM verified
- Sync time: <30 seconds for 10MB
- Data integrity: 100%

---

### 4.3 Team Context Merge - Conflict Resolution Test

**Objective**: Measure merge conflict resolution accuracy

**Test Scenario**:
- 2 users modify same context
- Merge with conflict resolution
- Measure: merge success rate, data loss rate

**Success Criteria**:
- Merge success: ≥95%
- Data loss: 0%

---

## Comparative Tests: Cortex vs No-Cortex

### CT-1: Long Session Context Retention

**Scenario**: 4-hour coding session with 200 interactions

**Setup**:
- Task: Multi-file refactoring project
- Group A: Claude + Cortex
- Group B: Claude without Cortex

**Metrics**:
- Context retention rate at 1h, 2h, 3h, 4h
- Task completion accuracy
- Number of clarification questions needed

**Expected Result**:
- Cortex: 95%+ retention at 4h
- No-Cortex: <50% retention at 4h

**Test Script**: `tests/comparative/test_long_session.py`

---

### CT-2: Cross-Session Project Continuation

**Scenario**: Resume project after 7 days

**Setup**:
- Day 1: Start complex project
- Day 8: Continue project
- Measure: recall accuracy, ramp-up time

**Expected Result**:
- Cortex: <5min ramp-up, 100% context recall
- No-Cortex: >30min ramp-up, manual context rebuilding

---

### CT-3: Multi-File Refactoring Accuracy

**Scenario**: Refactor 20-file codebase

**Setup**:
- Task: Rename function across 20 files
- Measure: accuracy, missed files, time

**Expected Result**:
- Cortex: 100% accuracy, 0 missed files
- No-Cortex: <90% accuracy, 2-3 missed files

---

## Standard Industry Benchmarks

### SB-1: Humanity's Last Exam

**Objective**: Compare against Gemini 3.0 (30.7%)

**Note**: This benchmark tests general reasoning ability, not Cortex-specific features. Cortex should help maintain context during multi-step reasoning.

**Expected Impact**:
- Cortex may improve score by 5-10% through better context retention
- Test with Claude 3.5 Sonnet + Cortex vs without

---

### SB-2: SWE-bench

**Objective**: Software engineering task completion

**Test Scenario**:
- 100 real-world GitHub issues
- Measure: resolution rate, correctness

**Expected Result**:
- Cortex: +15% resolution rate vs no-Cortex
- Better context retention for multi-file changes

---

### SB-3: HumanEval

**Objective**: Code generation accuracy

**Test Scenario**:
- 164 programming problems
- Measure: pass@1, pass@10

**Expected Result**:
- Cortex: Minimal impact (single-turn tasks)
- Real benefit shows in multi-turn conversations

---

## Real-World Scenario Tests

### RW-1: Production Bug Investigation

**Scenario**: Debug production issue across 15-file stack trace

**Metrics**:
- Time to identify root cause
- Number of context switches
- Accuracy of diagnosis

---

### RW-2: Feature Implementation

**Scenario**: Implement new feature across 8 files

**Metrics**:
- Implementation completeness
- Edge cases covered
- Test coverage

---

### RW-3: Code Review Consistency

**Scenario**: Review 20 PRs with consistent standards

**Metrics**:
- Consistency score
- False positive/negative rate
- Context retention across reviews

---

## Beta User Metrics (Closed Beta Period)

### Automatic Collection Metrics

These metrics should be collected automatically during closed beta:

1. **Usage Metrics**
   - Daily active users (DAU)
   - Average session duration
   - Number of contexts created per user
   - Number of branches per user

2. **Performance Metrics**
   - Average compression ratio achieved
   - Average search latency
   - Context recall accuracy (self-reported)
   - Token savings per user

3. **Feature Adoption**
   - % users using Smart Context
   - % users using Reference History
   - % users using Git Integration
   - % users using Cloud Sync

4. **Quality Metrics**
   - Hallucination detection rate
   - User-reported false positives
   - Grounding score distribution
   - Contradiction detection rate

5. **Automation Metrics**
   - Plan A usage time %
   - Plan B trigger frequency
   - User override rate
   - Automation satisfaction score

### User Survey Metrics

Collect via periodic surveys:

1. **NPS Score** (Net Promoter Score)
2. **Feature Usefulness Ratings** (1-5 scale)
3. **Pain Points** (open-ended)
4. **Feature Requests** (open-ended)
5. **Would-Pay Price Point** (pricing validation)

### Comparison Metrics

Ask beta users to compare with their previous workflow:

1. Time saved per day
2. Context retention improvement (subjective 1-10)
3. Error reduction (subjective 1-10)
4. Confidence in AI responses (subjective 1-10)

---

## Test Execution Plan

### Phase 1: Unit Tests (Week 1)
- All 13 feature-specific tests
- Target: 100% pass rate

### Phase 2: Comparative Tests (Week 2)
- 3 Cortex vs No-Cortex tests
- Document: video recordings, metrics

### Phase 3: Standard Benchmarks (Week 3)
- Run SWE-bench, HumanEval
- Attempt Humanity's Last Exam (if applicable)

### Phase 4: Real-World Scenarios (Week 4)
- 3 realistic coding scenarios
- Recruit 5 beta testers for user testing

### Phase 5: Beta User Metrics Collection (Ongoing)
- Instrument production code
- Weekly metric reports
- Monthly user surveys

---

## Public Verification

All test scripts will be published at:
- GitHub: `github.com/syab726/cortex/tree/main/benchmarks`
- Website: `/benchmarks/scripts`

Users can:
1. Download test scripts
2. Run on their own machines
3. Verify results independently
4. Submit their own results via PR

---

## Success Criteria Summary

| Category | Metric | Target |
|----------|--------|--------|
| Context Integrity | Compression | ≥70% |
| Context Integrity | Recall Accuracy | 100% |
| Context Integrity | Reference Accuracy | ≥95% |
| Truth & Verification | Hallucination Detection F1 | ≥87% |
| Truth & Verification | Grounding Correlation | ≥0.80 |
| Stability & Recovery | Restore Accuracy | 100% |
| Stability & Recovery | Git Sync Success | 100% |
| Scalability | Cross-session Recall | 100% |
| Scalability | Cloud Sync Time (10MB) | <30s |
| Comparative | Long Session Retention (4h) | ≥95% |
| Comparative | SWE-bench Improvement | +15% |

---

## Benchmark Results Visualization

Results will be displayed on website with:
- Interactive charts (Chart.js)
- Downloadable raw data (CSV/JSON)
- Test script links
- Reproduction instructions
- Community-submitted results

---

**Document Version**: 1.0
**Last Updated**: 2025-12-20
**Author**: Cortex MCP Team
