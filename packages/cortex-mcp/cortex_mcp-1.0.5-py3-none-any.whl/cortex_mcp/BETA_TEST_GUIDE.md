# Cortex MCP Beta Testing Guide

Welcome to the Cortex MCP beta program! This guide will help you get started and make the most of your beta testing experience.

## Table of Contents

- [Program Overview](#program-overview)
- [Beta Tester Benefits](#beta-tester-benefits)
- [Getting Started](#getting-started)
- [What to Test](#what-to-test)
- [Providing Feedback](#providing-feedback)
- [Community](#community)
- [FAQ](#faq)

---

## Program Overview

### Goals

Cortex MCP beta testing aims to:

1. **Validate Core Features** in real-world AI development workflows
2. **Identify Edge Cases** that unit tests can't catch
3. **Gather User Feedback** on UX and feature prioritization
4. **Build Community** of early adopters and contributors

### Timeline

- **Beta Duration**: 1 year (renewable based on participation)
- **Commitment**: Minimum 2-3 months active testing
- **Feedback Frequency**: At least 1 report per month

### Slots Available

- **Total**: 30 beta testers
- **Current**: Check [GitHub Discussions](https://github.com/syab726/cortex/discussions) for availability

---

## Beta Tester Benefits

### What You Get

1. **Free Pro Tier Access** (1 year, normally $15/month = $180 value)
   - Reference History (95% recommendation accuracy)
   - Smart Context (70% token savings)
   - Hallucination Detection (Phase 9)
   - Plan A/B automatic mode switching

2. **Direct Communication Channel**
   - Private Discord channel (optional)
   - Direct email support (beta@cortex-mcp.com)
   - Monthly Q&A sessions with the dev team

3. **Feature Request Priority**
   - Your feedback shapes the roadmap
   - Vote on upcoming features
   - Early access to experimental features

4. **Recognition**
   - Listed in CONTRIBUTORS.md (optional)
   - Beta tester badge in community forums
   - Special mention in blog posts/releases

### What We Need from You

1. **Active Usage**
   - Use Cortex MCP in your daily AI workflow
   - Test at least 3 core features per month
   - Report any bugs or issues

2. **Feedback**
   - Monthly feedback report (template provided)
   - Participate in surveys (5-10 minutes each)
   - Share use cases and workflows

3. **Telemetry**
   - Keep anonymous telemetry enabled (opt-out available)
   - Allows us to track feature usage and performance
   - No personal data or code is collected

---

## Getting Started

### Step 1: Apply for Beta Access

**Application Form**: [Google Form Link](https://forms.gle/YOUR_FORM_ID)

**Required Information**:
- Name and email
- GitHub username (optional)
- AI development experience (brief description)
- Primary use case for Cortex MCP
- Commitment to provide feedback (yes/no)

**What We're Looking For**:
- Active AI developers (LLM app builders, researchers, etc.)
- Diverse use cases (coding, writing, research, etc.)
- Willingness to provide constructive feedback

### Step 2: Receive Beta Key

Once accepted:
- You'll receive a beta license key via email (within 3 business days)
- Key format: `BETA-XXXX-XXXX-XXXX-XXXX`
- Valid for 1 year from activation date

### Step 3: Install and Activate

Follow [INSTALLATION.md](./INSTALLATION.md) with your beta key:

```bash
# Install
pip install cortex-mcp

# Activate beta key
cortex-mcp --activate BETA-XXXX-XXXX-XXXX-XXXX

# Verify
cortex-mcp --check
# Should show: License active (Tier: Pro, Type: Beta)
```

### Step 4: Join the Community

- **GitHub Discussions**: [https://github.com/syab726/cortex/discussions](https://github.com/syab726/cortex/discussions)
- **Discord** (optional): Invite link in welcome email
- **Mailing List**: beta@cortex-mcp.com (announcements only)

### Step 5: Complete Onboarding Survey

A short survey (5 minutes) to help us understand your workflow:
- What AI tools do you currently use?
- What problems are you trying to solve?
- What features are you most excited about?

---

## What to Test

### Priority 1: Core Features (Must Test)

Test at least one from each category:

#### 1. Memory Management
- **initialize_context**: Scan your project (FULL/LIGHT/NONE modes)
- **create_branch**: Create context branches for different tasks
- **update_memory**: Save conversations and context

**Test Scenario**:
```
1. Ask Claude to initialize context for your project
2. Start a new task and create a branch
3. Have a 5+ message conversation
4. Close and reopen Claude
5. Verify context is preserved
```

#### 2. Search & Retrieval
- **search_context**: Find past conversations
- **suggest_contexts**: Get AI-powered recommendations
- **accept_suggestions / reject_suggestions**: Provide feedback

**Test Scenario**:
```
1. Build up 10+ contexts over different topics
2. Start a new task similar to a past one
3. Check if Cortex recommends relevant contexts
4. Accept or reject recommendations
5. Verify recommendation quality improves over time
```

#### 3. Hallucination Detection (Phase 9)
- **verify_response**: Check AI responses for grounding

**Test Scenario**:
```
1. Ask Claude to implement a feature
2. Ask Claude to verify its response for hallucinations
3. Check the grounding score (should be >= 0.7 for ACCEPT)
4. Try responses with false claims and verify detection
```

### Priority 2: Advanced Features (Encouraged)

#### 4. Smart Context
- **load_context**: Lazy loading of compressed contexts
- **Auto-compression**: Test 30-minute idle auto-compression

**Test Scenario**:
```
1. Create a large context (100+ messages)
2. Wait 30 minutes without using that context
3. Verify it gets auto-compressed (check logs)
4. Load it again and verify content is intact
```

#### 5. Git Integration
- **link_git_branch**: Link Cortex branches to git branches

**Test Scenario**:
```
1. Work on a git branch (e.g., feature/new-ui)
2. Create a Cortex branch for the same topic
3. Switch git branches
4. Verify Cortex auto-switches branches
```

#### 6. Backup & Snapshots
- **create_snapshot**: Create backups
- **restore_snapshot**: Restore from backups
- **list_snapshots**: View snapshot history

**Test Scenario**:
```
1. Build up some contexts
2. Create a snapshot
3. Make changes to contexts
4. Restore from snapshot
5. Verify contexts are reverted
```

### Priority 3: Edge Cases (Nice to Have)

Try to break things! Examples:
- Very large contexts (1000+ messages)
- Rapid branch switching (10+ times)
- Offline usage (disconnect network)
- Concurrent Claude windows
- Special characters in context content

---

## Providing Feedback

### Monthly Feedback Report (Required)

**Due**: Last day of each month

**Template**: [GitHub Issue Template](https://github.com/syab726/cortex/issues/new?template=beta_feedback.md)

**Sections**:

1. **Usage Summary**
   - Features tested this month
   - Approximate usage frequency (daily/weekly/monthly)
   - Primary use cases

2. **What Worked Well**
   - Features you loved
   - Positive experiences
   - Productivity improvements

3. **Issues Encountered**
   - Bugs (with reproduction steps)
   - Performance problems
   - Confusing UX

4. **Feature Requests**
   - Missing features
   - Improvement ideas
   - Priority ranking

5. **Overall Rating**
   - Satisfaction: 1-10
   - Likelihood to recommend: 1-10
   - Would you pay for this? (yes/no/maybe)

### Bug Reports (As Needed)

**GitHub Issues**: [https://github.com/syab726/cortex/issues/new?template=bug_report.md](https://github.com/syab726/cortex/issues/new?template=bug_report.md)

**Include**:
- Clear description of the bug
- Steps to reproduce
- Expected vs. actual behavior
- Environment (OS, Python version, Claude version)
- Logs (from `~/.cortex/logs/cortex.log`)

**Priority Bugs**:
- Data loss or corruption
- Security vulnerabilities
- Crash or freeze
- Hallucination detection false negatives

### Feature Requests

**GitHub Discussions**: [https://github.com/syab726/cortex/discussions/categories/feature-requests](https://github.com/syab726/cortex/discussions/categories/feature-requests)

**Template**:
```markdown
## Problem
Describe the problem you're trying to solve.

## Proposed Solution
How would you solve it?

## Alternatives Considered
Any other approaches?

## Use Case
Real-world example of how you'd use this.

## Priority
Low / Medium / High / Critical
```

### Surveys (Occasional)

We'll send 2-3 short surveys during the beta period:
- Onboarding survey (after installation)
- Mid-term survey (after 3 months)
- End-of-beta survey (after 1 year)

**Time**: 5-10 minutes each
**Incentive**: Early access to new features for participants

---

## Community

### Communication Channels

1. **GitHub Discussions** (Primary)
   - General questions
   - Feature discussions
   - Use case sharing

2. **Discord** (Optional, invite-only)
   - Real-time chat with other beta testers
   - Q&A with dev team
   - Weekly office hours

3. **Email** (Support only)
   - beta@cortex-mcp.com
   - Response time: 24-48 hours

### Community Guidelines

- **Be Respectful**: Constructive criticism only
- **Be Specific**: Vague feedback is hard to act on
- **Be Honest**: We value candid opinions
- **Be Patient**: We're a small team

### Recognition

Top contributors (most helpful feedback) will get:
- Extended free access (beyond 1 year)
- Early access to Enterprise features
- Mentioned in release notes

---

## FAQ

### Q: What happens after the 1-year beta period?

**A**: You'll have several options:
1. **Upgrade to Paid**: Get a 50% discount on the first year ($7.50/month for Pro)
2. **Become a Contributor**: Continue free access by contributing code/docs
3. **Downgrade to Free**: Keep using Cortex with limited features

We'll never lock you out of your data.

### Q: Can I use Cortex MCP for commercial projects?

**A**: Yes! Beta license allows commercial use. We only ask that you provide feedback based on your experience.

### Q: Is my data secure during beta testing?

**A**: Yes. All data is stored locally by default. Telemetry is anonymous and opt-in. See [Privacy Policy](./PRIVACY.md).

### Q: What if I find a critical security issue?

**A**: Email security@cortex-mcp.com immediately. Do not post publicly. We have a responsible disclosure policy.

### Q: Can I share my beta key with others?

**A**: No. Beta keys are non-transferable and tied to your email. Sharing may result in key revocation.

### Q: What if I can't provide feedback every month?

**A**: That's okay! We understand life gets busy. Just let us know if you need to take a break. Minimum commitment is 3 months total, not consecutive.

### Q: Can I test Cortex MCP with models other than Claude?

**A**: Cortex MCP is designed for Claude (Anthropic's MCP protocol), but technically works with any MCP-compatible client. Let us know if you try others!

### Q: How do I report a bug without exposing my project's code?

**A**: Great question! You can:
1. Create a minimal reproduction case with dummy data
2. Redact sensitive parts from logs before submitting
3. Email us directly if you can't share publicly

### Q: What's the difference between Beta Free and Pro tier?

**A**: Beta Free = Pro tier. You get all Pro features for free during the beta period.

### Q: Can I extend my beta access beyond 1 year?

**A**: Possibly! Top contributors (most helpful feedback) may receive extensions. We'll evaluate case-by-case.

---

## Getting Help

### Documentation

- **README**: [README.md](./README.md)
- **Installation**: [INSTALLATION.md](./INSTALLATION.md)
- **API Reference**: [API_REFERENCE.md](./API_REFERENCE.md)

### Support

- **GitHub Issues**: Bug reports
- **GitHub Discussions**: General questions
- **Email**: beta@cortex-mcp.com (beta testers only)

### Tips for Better Support

1. **Search First**: Check existing issues/discussions
2. **Be Specific**: Include error messages, logs, steps to reproduce
3. **One Issue per Report**: Don't bundle multiple problems
4. **Follow Up**: Let us know if our solution worked

---

## Thank You!

Thank you for being part of the Cortex MCP beta program. Your feedback is invaluable in building a tool that truly helps AI developers work more effectively.

**Let's build the future of AI accountability together!**

---

**Questions?** Email beta@cortex-mcp.com or post in [GitHub Discussions](https://github.com/syab726/cortex/discussions).
