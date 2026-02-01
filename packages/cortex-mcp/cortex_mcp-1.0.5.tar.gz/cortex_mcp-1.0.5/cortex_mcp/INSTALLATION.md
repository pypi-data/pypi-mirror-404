# Cortex MCP Installation Guide

Complete step-by-step installation guide for Cortex MCP.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Method 1: PyPI Installation (Recommended)](#method-1-pypi-installation-recommended)
- [Method 2: From Source](#method-2-from-source)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- **Python**: 3.10 or higher
- **Claude Desktop**: Latest version (or any MCP-compatible client)
- **Operating System**: macOS, Linux, or Windows

### Optional

- **Google Drive API**: For cloud sync feature (Enterprise tier)
- **Git**: For git integration features

### Check Python Version

```bash
python3 --version
# Should show: Python 3.10.x or higher
```

---

## Method 1: PyPI Installation (Recommended)

### Step 1: Install Cortex MCP

```bash
pip install cortex-mcp
```

### Step 2: Verify Installation

```bash
cortex-mcp --version
# Should show: cortex-mcp version x.x.x
```

### Step 3: Activate License

Choose one of the following:

#### Option A: Beta Tester (Free 1-year)

If you're a beta tester:

```bash
cortex-mcp --activate YOUR-BETA-KEY
```

#### Option B: GitHub Login (Paddle Integration)

```bash
cortex-mcp --github-login
# Follow the browser prompt to authenticate
```

#### Option C: Direct License Key

```bash
cortex-mcp --license YOUR-LICENSE-KEY
```

### Step 4: Verify License

```bash
cortex-mcp --check
# Should show: License active (Tier: Pro/Enterprise)
```

---

## Method 2: From Source

For development or contributing:

### Step 1: Clone Repository

```bash
git clone https://github.com/syab726/cortex.git
cd cortex/cortex_mcp
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -e ".[dev]"
```

### Step 4: Run Tests (Optional)

```bash
pytest tests/ -v
# Should show: 97%+ test coverage
```

### Step 5: Activate License

```bash
python -m cortex_mcp.main --activate YOUR-LICENSE-KEY
```

---

## Configuration

### Claude Desktop Configuration

Add Cortex to your Claude Desktop configuration file.

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration:**

```json
{
  "mcpServers": {
    "cortex": {
      "command": "cortex-mcp",
      "args": []
    }
  }
}
```

**With Custom Options:**

```json
{
  "mcpServers": {
    "cortex": {
      "command": "cortex-mcp",
      "args": [
        "--telemetry", "off",
        "--log-level", "info"
      ]
    }
  }
}
```

### Advanced Configuration

#### Custom Data Directory

```json
{
  "mcpServers": {
    "cortex": {
      "command": "cortex-mcp",
      "args": ["--data-dir", "/custom/path/.cortex"]
    }
  }
}
```

#### Cloud Sync Setup (Enterprise Only)

1. **Enable Google Drive API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing
   - Enable Google Drive API
   - Create credentials (OAuth 2.0 Client ID)
   - Download `credentials.json`

2. **Place Credentials**:
   ```bash
   mkdir -p ~/.cortex
   mv ~/Downloads/credentials.json ~/.cortex/
   ```

3. **Test Cloud Sync**:
   ```bash
   # In Claude, use the sync_to_cloud tool
   # First run will open browser for authentication
   ```

---

## Verification

### Test MCP Connection

1. **Restart Claude Desktop**

2. **Check MCP Status**:
   - Open Claude Desktop
   - Look for "Cortex" in the MCP server list
   - Status should show: "Connected"

3. **Test Basic Commands**:

   Ask Claude:
   ```
   Can you initialize context for this project?
   ```

   Claude should respond using the `initialize_context` tool.

### Verify Data Storage

```bash
ls -la ~/.cortex/
# Should show:
# - memory/
# - chroma_db/
# - backups/
# - licenses/
# - logs/
```

---

## Troubleshooting

### Issue: "cortex-mcp: command not found"

**Solution 1: Add to PATH**

```bash
# Add pip's binary path to your shell config (~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc  # or ~/.zshrc
```

**Solution 2: Use Full Path**

```bash
python3 -m cortex_mcp.main --version
```

**Solution 3: Reinstall in User Mode**

```bash
pip install --user cortex-mcp
```

---

### Issue: "License activation failed"

**Causes:**
- Invalid license key
- Network connection issue
- License already activated on another machine

**Solutions:**

1. **Check License Key**:
   ```bash
   cortex-mcp --check
   ```

2. **Retry Activation**:
   ```bash
   cortex-mcp --activate YOUR-LICENSE-KEY --force
   ```

3. **Use GitHub Login** (if available):
   ```bash
   cortex-mcp --github-login
   ```

4. **Contact Support**: If issue persists, email beta@cortex-mcp.com with:
   - License key (last 4 characters only)
   - Error message
   - OS and Python version

---

### Issue: "Claude Desktop doesn't show Cortex"

**Checklist:**

1. **Verify JSON Syntax**:
   ```bash
   # On macOS/Linux:
   python3 -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json

   # Should print formatted JSON without errors
   ```

2. **Check Log Files**:
   ```bash
   tail -f ~/.cortex/logs/cortex.log
   # Watch for errors during startup
   ```

3. **Restart Claude Desktop**:
   - Quit Claude completely
   - Reopen Claude Desktop
   - Check MCP server list

4. **Test Manual Start**:
   ```bash
   cortex-mcp
   # Should start MCP server and print: "Cortex MCP server started"
   ```

---

### Issue: "ImportError: No module named 'cortex_mcp'"

**Solution 1: Reinstall**

```bash
pip uninstall cortex-mcp
pip install cortex-mcp
```

**Solution 2: Check Virtual Environment**

If using venv, ensure it's activated:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install cortex-mcp
```

**Solution 3: Use Editable Install**

For development:

```bash
cd cortex/cortex_mcp
pip install -e .
```

---

### Issue: "ChromaDB persistence error"

**Cause**: Corrupted vector database

**Solution**:

```bash
# Backup existing data
cp -r ~/.cortex/chroma_db ~/.cortex/chroma_db.backup

# Remove corrupted database
rm -rf ~/.cortex/chroma_db

# Restart Cortex
# Database will be recreated automatically
```

**Note**: You'll need to re-index your contexts using `update_memory`.

---

### Issue: "High memory usage"

**Expected Behavior**:
- Initial startup: 200-300MB
- With 1000+ contexts: 500-800MB
- During RAG search: Temporary spike to 1-2GB

**Solutions**:

1. **Enable Auto-Compression**:
   ```bash
   # Add to claude_desktop_config.json:
   "args": ["--auto-compress", "30"]  # 30 minutes idle
   ```

2. **Limit Active Contexts**:
   ```bash
   # Max 3 active branches (default)
   "args": ["--max-active-branches", "3"]
   ```

3. **Reduce Embedding Cache**:
   ```bash
   # Smaller embedding cache
   "args": ["--embedding-cache-size", "100"]  # Default: 1000
   ```

---

### Issue: "Phase 9 hallucination detection not working"

**Verification**:

1. **Check License Tier**:
   ```bash
   cortex-mcp --check
   # Should show: Tier: Pro or Enterprise
   ```

   **Note**: Hallucination detection requires Pro tier or higher.

2. **Test Manually**:

   Ask Claude:
   ```
   Can you verify this response for hallucinations: "I fixed 100 bugs today"
   ```

   Claude should use the `verify_response` tool.

3. **Check Logs**:
   ```bash
   grep "HALLUCINATION" ~/.cortex/logs/cortex.log
   # Should show: [HALLUCINATION_LOG] entries
   ```

---

## Getting Help

### Documentation

- **README**: [README.md](./README.md)
- **Beta Testing**: [BETA_TEST_GUIDE.md](./BETA_TEST_GUIDE.md)
- **API Reference**: [API_REFERENCE.md](./API_REFERENCE.md)

### Support Channels

- **GitHub Issues**: [https://github.com/syab726/cortex/issues](https://github.com/syab726/cortex/issues)
- **GitHub Wiki**: [https://github.com/syab726/cortex/wiki](https://github.com/syab726/cortex/wiki)
- **Beta Tester Support**: beta@cortex-mcp.com

### Before Asking for Help

Please include:

1. **Environment**:
   ```bash
   cortex-mcp --version
   python3 --version
   uname -a  # or: ver (Windows)
   ```

2. **Error Logs**:
   ```bash
   tail -50 ~/.cortex/logs/cortex.log
   ```

3. **Configuration**:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   # Redact sensitive information
   ```

---

**Installation Complete!**

You're ready to use Cortex MCP with Claude. See [README.md](./README.md) for usage examples and [BETA_TEST_GUIDE.md](./BETA_TEST_GUIDE.md) if you're a beta tester.
