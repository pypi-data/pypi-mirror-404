# Cortex MCP API Reference

Complete reference for all Cortex MCP tools and their parameters.

## Table of Contents

- [Core Memory Tools](#core-memory-tools)
- [Search & Retrieval Tools](#search--retrieval-tools)
- [Verification & Quality Tools](#verification--quality-tools)
- [Backup & Sync Tools](#backup--sync-tools)
- [Git Integration Tools](#git-integration-tools)
- [Automation Tools](#automation-tools)
- [Common Response Format](#common-response-format)
- [Error Handling](#error-handling)

---

## Core Memory Tools

### initialize_context

Initialize context scanning for a project.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_path` | string | Yes | Absolute path to project directory |
| `mode` | enum | No | Scan mode: `full`, `light`, or `none` (default: `light`) |

**Modes:**

- **full**: Deep scan of entire codebase (high token usage, best accuracy)
- **light**: Scan README, entry points, and config files only (recommended)
- **none**: Skip scanning (fastest, minimal context)

**Returns:**

```json
{
  "success": true,
  "project_id": "abc123def456",
  "mode": "light",
  "files_scanned": 15,
  "contexts_created": 3,
  "message": "Project initialized successfully"
}
```

**Example Usage:**

```python
# In Claude, you would say:
"Can you initialize context for this project in light mode?"

# Claude calls:
initialize_context(
    project_path="/Users/username/myproject",
    mode="light"
)
```

---

### create_branch

Create a new context branch.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID from `initialize_context` |
| `branch_topic` | string | Yes | Topic/name for this branch |
| `parent_branch` | string | No | Parent branch ID (for child branches) |

**Returns:**

```json
{
  "success": true,
  "branch_id": "feature_authentication_20260102_123456",
  "branch_path": "~/.cortex/memory/abc123/feature_authentication_20260102_123456.md",
  "message": "Branch 'feature_authentication' created and verified",
  "verified": true
}
```

**Verification:**

Cortex automatically verifies branch creation by:
1. Checking file exists at `branch_path`
2. Validating YAML frontmatter
3. Confirming branch is indexed

**Example Usage:**

```python
# User says: "Let's start working on user authentication"
# Claude detects topic change and calls:
create_branch(
    project_id="abc123def456",
    branch_topic="User Authentication Implementation"
)
```

---

### update_memory

Save context to memory with automatic indexing and hallucination detection (Pro+).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `branch_id` | string | Yes | Branch ID |
| `content` | string | Yes | Content to save |
| `role` | enum | Yes | `user` or `assistant` |

**Returns:**

```json
{
  "success": true,
  "task_id": "task_20260102_123456_abc",
  "grounding_score": 0.87,
  "hallucination_status": "ACCEPT",
  "risk_level": "low",
  "ontology_category": "development",
  "indexed": true,
  "message": "Memory updated and verified"
}
```

**Background Processing:**

After saving, Cortex asynchronously:
1. **Hallucination Detection** (Pro+): Extracts claims and calculates grounding score
2. **Ontology Classification** (Pro+): Categorizes content (development/bug_fix/feature/etc.)
3. **RAG Indexing**: Updates vector database for search
4. **Auto-Compression**: Compresses old messages if threshold exceeded

**Grounding Score Thresholds:**

| Score | Status | Meaning |
|-------|--------|---------|
| >= 0.7 | ACCEPT | Well-grounded, sufficient evidence |
| 0.3-0.7 | WARN | Manual review recommended |
| < 0.3 | REJECT | Insufficient evidence, likely hallucination |

**Example Usage:**

```python
# After AI responds to user
update_memory(
    project_id="abc123def456",
    branch_id="feature_auth_20260102_123456",
    content="Implemented JWT authentication with refresh tokens",
    role="assistant"
)
```

---

### get_active_summary

Get current branch summary for injection into System Prompt.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `branch_id` | string | Yes | Branch ID |

**Returns:**

```json
{
  "success": true,
  "summary": "Working on user authentication feature. Implemented JWT tokens with refresh mechanism. Next: Add role-based access control.",
  "content": "Full context content (if needed)",
  "branch_topic": "User Authentication Implementation",
  "last_updated": "2026-01-02T12:34:56Z",
  "message_count": 15,
  "status": "active"
}
```

**System Prompt Injection:**

Claude automatically injects this summary into its System Prompt to maintain long-term context across sessions.

**Example Usage:**

```python
# At start of new session
get_active_summary(
    project_id="abc123def456",
    branch_id="feature_auth_20260102_123456"
)
# Returns summary for context restoration
```

---

## Search & Retrieval Tools

### search_context

Search through stored contexts using hybrid RAG (semantic + keyword).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `query` | string | Yes | Search query |
| `top_k` | integer | No | Number of results (default: 10) |
| `filter_category` | string | No | Ontology category filter (Pro+) |
| `min_score` | float | No | Minimum relevance score (0.0-1.0, default: 0.3) |

**Returns:**

```json
{
  "success": true,
  "results": [
    {
      "context_id": "context_abc123",
      "branch_id": "feature_auth_20260102_123456",
      "branch_topic": "User Authentication",
      "content": "Implemented JWT authentication...",
      "score": 0.92,
      "metadata": {
        "ontology_category": "development",
        "created_at": "2026-01-02T10:00:00Z"
      }
    }
  ],
  "total_results": 15,
  "search_time_ms": 45
}
```

**Search Algorithm:**

1. **Semantic Search**: Uses sentence-transformers embeddings
2. **Keyword Search**: Falls back to keyword matching if semantic fails
3. **Hybrid Scoring**: Combines both scores for ranking
4. **Category Filtering** (Pro+): Narrows results by ontology category

**Example Usage:**

```python
# User asks: "How did we implement authentication?"
search_context(
    project_id="abc123def456",
    query="authentication implementation",
    top_k=5,
    filter_category="development"
)
```

---

### load_context

Load specific context (lazy loading, decompression if needed).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `branch_id` | string | Yes | Branch ID |
| `context_id` | string | Yes | Context ID |

**Returns:**

```json
{
  "success": true,
  "context_id": "context_abc123",
  "content": "Full context content...",
  "metadata": {
    "compressed": false,
    "size_bytes": 5120,
    "created_at": "2026-01-02T10:00:00Z"
  },
  "message": "Context loaded successfully"
}
```

**Lazy Loading:**

- **Compressed contexts** are stored with only `metadata + summary`
- **`load_context`** decompresses and loads full content on demand
- **30-minute idle rule**: Contexts auto-compress after 30 minutes of inactivity

**Example Usage:**

```python
load_context(
    project_id="abc123def456",
    branch_id="feature_auth_20260102_123456",
    context_id="context_abc123"
)
```

---

### suggest_contexts

Get AI-powered context recommendations based on Reference History (Pro+).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `current_context` | string | Yes | Current task/topic description |
| `top_k` | integer | No | Number of suggestions (default: 5) |

**Returns:**

```json
{
  "success": true,
  "session_id": "suggestion_session_abc123",
  "suggestions": [
    {
      "context_id": "context_xyz789",
      "branch_id": "feature_auth_20260102_123456",
      "branch_topic": "User Authentication",
      "reason": "Historically referenced together with current task",
      "confidence": 0.95,
      "source": "reference_history"
    }
  ],
  "total_suggestions": 3,
  "message": "3 relevant contexts suggested"
}
```

**Recommendation Sources:**

| Source | Confidence | Description |
|--------|-----------|-------------|
| `reference_history` | 95% | Based on past co-references |
| `ai_analysis` | 70% | AI semantic analysis |
| `user_selected` | 100% | User explicitly selected before |

**Next Steps:**

After receiving suggestions, you MUST call either:
- `accept_suggestions(session_id, context_ids)`
- `reject_suggestions(session_id, reason)`

**Example Usage:**

```python
suggest_contexts(
    project_id="abc123def456",
    current_context="Adding role-based access control",
    top_k=5
)
```

---

### accept_suggestions

Accept context recommendations (provides feedback to Reference History).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `session_id` | string | Yes | Session ID from `suggest_contexts` |
| `context_ids` | array[string] | Yes | IDs of accepted contexts |

**Returns:**

```json
{
  "success": true,
  "accepted_count": 2,
  "message": "Feedback recorded, recommendations will improve"
}
```

**Feedback Loop:**

Accepting suggestions:
1. Records co-reference in Reference History
2. Increases confidence for future recommendations
3. Improves AI's understanding of your workflow

**Example Usage:**

```python
accept_suggestions(
    project_id="abc123def456",
    session_id="suggestion_session_abc123",
    context_ids=["context_xyz789", "context_def456"]
)
```

---

### reject_suggestions

Reject context recommendations (with reason for improvement).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `session_id` | string | Yes | Session ID from `suggest_contexts` |
| `reason` | string | Yes | Why suggestions were rejected |

**Returns:**

```json
{
  "success": true,
  "message": "Feedback recorded, will avoid similar suggestions"
}
```

**Improvement:**

Rejection feedback helps Cortex:
- Avoid irrelevant recommendations
- Learn your preferences
- Adjust recommendation algorithms

**Example Usage:**

```python
reject_suggestions(
    project_id="abc123def456",
    session_id="suggestion_session_abc123",
    reason="Suggested contexts are from a different project phase"
)
```

---

## Verification & Quality Tools

### verify_response

Hallucination detection with grounding score (Pro+).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `response_text` | string | Yes | AI response to verify |
| `evidence_sources` | array[string] | No | Expected evidence sources |

**Returns:**

```json
{
  "success": true,
  "grounding_score": 0.87,
  "status": "ACCEPT",
  "risk_level": "low",
  "claims_extracted": 5,
  "claims_verified": 5,
  "evidence_items": [
    {
      "claim": "Implemented JWT authentication",
      "evidence": "File: auth.py line 45",
      "grounding": 1.0,
      "verified": true
    }
  ],
  "fuzzy_confidence": 0.85,
  "contradictions": [],
  "message": "Response is well-grounded with sufficient evidence"
}
```

**Verification Process:**

1. **Claim Extraction**: Identifies verifiable claims
2. **Evidence Matching**: Matches claims against project files, git history, etc.
3. **Grounding Scoring**: Calculates evidence quality score
4. **Contradiction Detection**: Checks for internal contradictions
5. **Fuzzy Analysis**: Analyzes confidence levels in language

**Thresholds:**

| Grounding Score | Status | Recommendation |
|----------------|--------|----------------|
| >= 0.7 | ACCEPT | Sufficient evidence |
| 0.3-0.7 | WARN | Manual review needed |
| < 0.3 | REJECT | Likely hallucination |

**Example Usage:**

```python
verify_response(
    project_id="abc123def456",
    response_text="I implemented JWT authentication with refresh tokens in auth.py",
    evidence_sources=["auth.py", "git log"]
)
```

---

### get_context_graph_info

Retrieve context relationship graph (Enterprise feature preview).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `branch_id` | string | No | Specific branch (optional, returns all if omitted) |

**Returns:**

```json
{
  "success": true,
  "nodes": [
    {
      "id": "context_abc123",
      "type": "context",
      "label": "JWT Implementation",
      "branch_id": "feature_auth_20260102_123456"
    }
  ],
  "edges": [
    {
      "from": "context_abc123",
      "to": "context_def456",
      "type": "references",
      "weight": 0.8
    }
  ],
  "total_nodes": 15,
  "total_edges": 23
}
```

**Use Cases:**

- Visualize context dependencies
- Identify knowledge clusters
- Find orphaned contexts

**Example Usage:**

```python
get_context_graph_info(
    project_id="abc123def456"
)
```

---

## Backup & Sync Tools

### create_snapshot

Create verified backup snapshot.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `description` | string | No | Snapshot description |

**Returns:**

```json
{
  "success": true,
  "snapshot_id": "snapshot_20260102_123456",
  "snapshot_path": "~/.cortex/backups/abc123/snapshot_20260102_123456.tar.gz",
  "size_bytes": 1048576,
  "verified": true,
  "message": "Snapshot created and verified"
}
```

**Verification:**

Snapshots are verified by:
1. Creating tarball of all project contexts
2. Computing SHA-256 checksum
3. Testing extraction
4. Confirming file integrity

**Example Usage:**

```python
create_snapshot(
    project_id="abc123def456",
    description="Before major refactor"
)
```

---

### restore_snapshot

Restore from a snapshot with integrity verification.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `snapshot_id` | string | Yes | Snapshot ID to restore |

**Returns:**

```json
{
  "success": true,
  "restored_contexts": 15,
  "restored_branches": 3,
  "verified": true,
  "message": "Snapshot restored and verified successfully"
}
```

**Safety:**

- Current data is backed up before restore
- Integrity check before applying
- Rollback on verification failure

**Example Usage:**

```python
restore_snapshot(
    project_id="abc123def456",
    snapshot_id="snapshot_20260102_123456"
)
```

---

### list_snapshots

List available snapshots.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |

**Returns:**

```json
{
  "success": true,
  "snapshots": [
    {
      "snapshot_id": "snapshot_20260102_123456",
      "created_at": "2026-01-02T12:34:56Z",
      "description": "Before major refactor",
      "size_bytes": 1048576,
      "verified": true
    }
  ],
  "total_snapshots": 5
}
```

**Example Usage:**

```python
list_snapshots(project_id="abc123def456")
```

---

### sync_to_cloud

E2E encrypted cloud backup (Enterprise only).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |

**Returns:**

```json
{
  "success": true,
  "uploaded_bytes": 2097152,
  "encrypted": true,
  "cloud_path": "cortex-backups/abc123def456_20260102.enc",
  "message": "Backup uploaded successfully"
}
```

**Encryption:**

- **Algorithm**: AES-256-GCM
- **Key**: Derived from license key
- **Security**: End-to-end, zero-knowledge

**Example Usage:**

```python
sync_to_cloud(project_id="abc123def456")
```

---

### sync_from_cloud

Restore from cloud backup (Enterprise only).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |

**Returns:**

```json
{
  "success": true,
  "downloaded_bytes": 2097152,
  "decrypted": true,
  "restored_contexts": 20,
  "message": "Backup restored from cloud"
}
```

**Example Usage:**

```python
sync_from_cloud(project_id="abc123def456")
```

---

## Git Integration Tools

### link_git_branch

Link Cortex branch to git branch.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |
| `cortex_branch_id` | string | Yes | Cortex branch ID |
| `git_branch_name` | string | Yes | Git branch name |

**Returns:**

```json
{
  "success": true,
  "linked": true,
  "auto_switch": true,
  "message": "Cortex will auto-switch when you checkout this git branch"
}
```

**Auto-Switching:**

Once linked:
- `git checkout feature-branch` → Cortex auto-loads corresponding context
- Seamless context switching across git workflows

**Example Usage:**

```python
link_git_branch(
    project_id="abc123def456",
    cortex_branch_id="feature_auth_20260102_123456",
    git_branch_name="feature/authentication"
)
```

---

## Automation Tools

### get_automation_status

Get Plan A/B automation status.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |

**Returns:**

```json
{
  "success": true,
  "current_plan": "A",
  "acceptance_rate": 0.85,
  "rejection_rate": 0.15,
  "feedback_count": 100,
  "message": "Plan A active (high acceptance rate)"
}
```

**Plans:**

- **Plan A**: Automatic mode (acceptance rate >= 70%)
- **Plan B**: Confirmation mode (acceptance rate < 70%)

**Example Usage:**

```python
get_automation_status(project_id="abc123def456")
```

---

## Common Response Format

All tools return responses in this format:

```json
{
  "success": boolean,
  "message": string,
  // ... tool-specific fields
}
```

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": "Detailed error information"
}
```

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `PROJECT_NOT_FOUND` | Project ID doesn't exist | Call `initialize_context` first |
| `BRANCH_NOT_FOUND` | Branch ID doesn't exist | Call `create_branch` first |
| `LICENSE_REQUIRED` | Feature requires license | Upgrade to Pro/Enterprise |
| `INVALID_PARAMS` | Missing/invalid parameters | Check parameter types and requirements |
| `STORAGE_ERROR` | Disk I/O error | Check `~/.cortex/` permissions |
| `NETWORK_ERROR` | Cloud sync failed | Check internet connection |

---

## Best Practices

### 1. Context Lifecycle

```
initialize_context → create_branch → update_memory (continuous)
→ search_context (as needed) → create_snapshot (periodic)
```

### 2. Suggestion Workflow

```
suggest_contexts → review suggestions → accept_suggestions OR reject_suggestions
```

### 3. Verification Workflow

```
update_memory → automatic hallucination detection → manual verify_response (if WARN)
```

### 4. Backup Strategy

- **Snapshots**: Before major changes
- **Cloud Sync**: Daily (Enterprise)
- **Local Backups**: Automated by Cortex

---

## Rate Limits

No rate limits for local operations. Cloud sync (Enterprise):
- **sync_to_cloud**: 100 requests/day
- **sync_from_cloud**: 20 requests/day

---

## Support

Questions about the API? See:
- **README**: [README.md](./README.md)
- **Installation**: [INSTALLATION.md](./INSTALLATION.md)
- **Beta Testing**: [BETA_TEST_GUIDE.md](./BETA_TEST_GUIDE.md)
- **GitHub Issues**: [https://github.com/syab726/cortex/issues](https://github.com/syab726/cortex/issues)
