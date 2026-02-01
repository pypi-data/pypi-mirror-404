# Cortex MCP Beta Recruitment Plan

Internal planning document for beta tester recruitment and management.

## Recruitment Goals

### Target: 30 Beta Testers

**Breakdown by Use Case:**
- AI Developers (40%): 12 testers
- Researchers/Academics (30%): 9 testers
- Technical Writers (15%): 5 testers
- General Power Users (15%): 4 testers

**Diversity Goals:**
- 50% from non-English speaking countries
- 30% from underrepresented groups in tech
- Mix of individual developers and team leads

---

## Recruitment Channels

### Primary Channels

1. **GitHub (Main)**
   - Pin announcement in Discussions
   - README badge: "Beta Testing Open"
   - Issue template: beta_application.md

2. **Reddit** (Week 1-2)
   - r/MachineLearning
   - r/LocalLLaMA
   - r/ClaudeAI
   - r/ArtificialIntelligence

3. **Twitter/X** (Week 1-4)
   - Thread explaining Cortex value prop
   - Tag @AnthropicAI
   - Use hashtags: #LLM #AI #MCP

4. **Hacker News** (Week 2)
   - "Show HN: Cortex MCP - Making AI Accountable with Local Memory"
   - Respond to all comments within 24h

### Secondary Channels

5. **Discord Communities**
   - Anthropic Discord
   - LangChain Discord
   - AI Engineering Discord

6. **LinkedIn** (Week 3-4)
   - Post in AI/ML groups
   - Direct outreach to connections

7. **Product Hunt** (Week 4)
   - Launch as "Beta Testing"
   - Time for maximum visibility

---

## Application Process

### Step 1: Application Form

**Google Form URL**: [TBD - Create form]

**Questions:**

1. **Contact Info**
   - Name
   - Email
   - GitHub username (optional)
   - Country

2. **Experience**
   - How do you use AI tools? (open-ended)
   - Which LLM clients do you use? (Claude, ChatGPT, etc.)
   - Development experience level (1-5)

3. **Use Case**
   - What would you use Cortex for? (open-ended)
   - How often would you use it? (daily/weekly/monthly)

4. **Commitment**
   - Can you commit to 2-3 months of testing? (yes/no)
   - Can you provide monthly feedback? (yes/no)
   - Willing to enable anonymous telemetry? (yes/no)

5. **Discovery**
   - How did you hear about Cortex? (dropdown)

### Step 2: Review & Selection

**Criteria** (Scoring 1-5 each, total 25):

| Criterion | Weight | Questions |
|-----------|--------|-----------|
| Use Case Fit | 5 | Does their use case align with Cortex features? |
| Commitment | 5 | Will they actually provide feedback? |
| Diversity | 3 | Underrepresented group? Non-English? |
| Experience Level | 4 | Technical enough to test effectively? |
| Communication | 3 | Can they articulate feedback clearly? |
| Early Adopter | 2 | History of trying new tools? |
| Community Value | 3 | Likely to share/promote? |

**Selection Process:**
1. Auto-score applications (15+ points = auto-accept if slots available)
2. Manual review for borderline cases (12-14 points)
3. Reject < 12 points with kind response

**Timeline:**
- Week 1-2: Accept first 15 high-quality applicants
- Week 3-4: Fill remaining 15 slots
- Week 5+: Waitlist for dropouts

### Step 3: Onboarding

**Welcome Email Template:**

```
Subject: Welcome to Cortex MCP Beta Program!

Hi [Name],

Congratulations! You've been accepted into the Cortex MCP beta program.

Your Beta Key: BETA-XXXX-XXXX-XXXX-XXXX

Next Steps:
1. Install Cortex: https://github.com/syab726/cortex#installation
2. Activate your key: cortex-mcp --activate [YOUR-KEY]
3. Read Beta Guide: https://github.com/syab726/cortex/blob/main/BETA_TEST_GUIDE.md
4. Join Discord (optional): [INVITE-LINK]

First Task:
Complete the onboarding survey (5 min): [SURVEY-LINK]

Questions?
Reply to this email or post in GitHub Discussions.

Looking forward to your feedback!

The Cortex Team
```

**Onboarding Survey (Google Form):**
- Did installation go smoothly? (yes/no + details)
- Which feature are you most excited about?
- What's your primary use case?
- Any immediate questions or concerns?

---

## Communication Plan

### Regular Touchpoints

**Week 1 (Onboarding):**
- Welcome email with beta key
- Onboarding survey

**Week 2:**
- Check-in email: "How's it going?"
- Highlight 1-2 key features to try

**Week 4:**
- Reminder: Monthly feedback due
- Share aggregate feedback stats

**Monthly:**
- Feedback reminder (last week of month)
- Feature update announcements
- Community highlight (best feedback, interesting use cases)

### Communication Channels

1. **Email** (Primary)
   - beta@cortex-mcp.com
   - Monthly updates
   - Individual responses within 48h

2. **GitHub Discussions** (Community)
   - Q&A
   - Feature discussions
   - Use case sharing

3. **Discord** (Optional, Real-time)
   - Private #beta-testers channel
   - Weekly office hours (1h)
   - Async Q&A

---

## Retention Strategy

### Incentives

**Participation Tiers:**

| Tier | Criteria | Reward |
|------|----------|--------|
| **Gold** | 12/12 monthly reports + 5+ feature requests | Extended free access (2 years) |
| **Silver** | 9/12 monthly reports + 3+ feature requests | 50% discount on paid tier (1 year) |
| **Bronze** | 6/12 monthly reports | Mentioned in CONTRIBUTORS.md |

**Early Access:**
- Top 10 contributors get early access to Enterprise features
- Voting rights on roadmap prioritization

### Engagement Tactics

1. **Recognition**
   - Monthly "Featured Beta Tester" spotlight
   - Public thanks in release notes
   - Optional listing in CONTRIBUTORS.md

2. **Gamification**
   - Leaderboard (optional, opt-in)
   - Badges for milestones (first bug report, 100+ contexts, etc.)

3. **Exclusive Content**
   - Beta-only blog posts ("Behind the Scenes")
   - Early preview of upcoming features
   - AMA sessions with dev team

---

## Feedback Management

### Collection

**Monthly Feedback Report:**
- GitHub Issue: beta_feedback.md template
- Due: Last day of each month
- Reminder: 7 days before, 1 day before

**Surveys:**
- Onboarding (after installation)
- Mid-term (after 3 months)
- End-of-beta (after 1 year)

**Ad-hoc:**
- Bug reports (GitHub Issues)
- Feature requests (GitHub Discussions)
- Direct email (beta@cortex-mcp.com)

### Analysis

**Weekly:**
- Review new feedback
- Categorize issues (bug/feature/ux/docs)
- Assign priority

**Monthly:**
- Aggregate feedback stats
- Identify trends
- Update roadmap

**Quarterly:**
- Retention analysis (active vs. inactive testers)
- Satisfaction trends
- Feature usage metrics

### Action

**Bug Fixes:**
- Critical: Within 48h
- High: Within 1 week
- Medium: Within 2 weeks
- Low: Backlog

**Feature Requests:**
- High-demand (5+ votes): Roadmap review
- Medium-demand (2-4 votes): Consider for next phase
- Low-demand (1 vote): Backlog

**Documentation:**
- Confusing UX feedback → Documentation update within 3 days

---

## Metrics & Success Criteria

### Key Metrics

**Recruitment:**
- Applications received: Target 100+
- Acceptance rate: 30%
- Time to fill 30 slots: < 4 weeks

**Engagement:**
- Monthly feedback rate: Target 70%+
- Bug reports per month: Target 10+
- Feature requests per month: Target 5+

**Retention:**
- 3-month retention: Target 80%
- 6-month retention: Target 60%
- 1-year retention: Target 40%

**Quality:**
- Average satisfaction score: Target 8.0+/10
- Likelihood to recommend: Target 8.5+/10
- Would pay: Target 60%+ yes/maybe

### Success Criteria

**Minimum Viable Beta:**
- 20+ active testers (out of 30)
- 50+ bug reports over 3 months
- 25+ feature requests over 3 months
- Average satisfaction 7.0+/10

**Ideal Beta:**
- 25+ active testers
- 100+ bug reports over 3 months
- 50+ feature requests over 3 months
- Average satisfaction 8.5+/10
- 5+ community contributors (PRs)

---

## Timeline

### Phase 1: Preparation (Week 0)
- [ ] Create application form
- [ ] Set up beta@cortex-mcp.com email
- [ ] Prepare welcome email template
- [ ] Create onboarding survey
- [ ] Set up Discord server (optional)

### Phase 2: Recruitment (Week 1-4)
- [ ] Week 1: GitHub + Reddit announcement
- [ ] Week 2: Hacker News + Twitter
- [ ] Week 3: LinkedIn + Discord communities
- [ ] Week 4: Product Hunt

### Phase 3: Onboarding (Ongoing)
- [ ] Send welcome emails within 24h of acceptance
- [ ] Monitor onboarding survey responses
- [ ] Address installation issues promptly

### Phase 4: Active Beta (Month 1-12)
- [ ] Weekly: Review feedback, fix bugs
- [ ] Monthly: Send updates, collect feedback
- [ ] Quarterly: Analyze trends, adjust strategy

### Phase 5: Transition (Month 11-12)
- [ ] Month 11: Send transition plan to testers
- [ ] Month 12: End-of-beta survey
- [ ] Offer upgrade discounts
- [ ] Recognize top contributors

---

## Risk Mitigation

### Risk: Low Application Rate

**Mitigation:**
- Expand to more channels (dev.to, YouTube)
- Offer additional incentives (swag, extended access)
- Adjust messaging (focus on benefits)

### Risk: Low Engagement

**Mitigation:**
- Increase touchpoints (weekly emails)
- Simplify feedback process
- Offer 1-on-1 calls with highly engaged testers

### Risk: High Dropout Rate

**Mitigation:**
- Identify reasons (survey dropouts)
- Improve onboarding (better docs, videos)
- Provide more value (exclusive features, recognition)

### Risk: Negative Feedback

**Mitigation:**
- Respond quickly and empathetically
- Show action (fix bugs, add requested features)
- Transparent roadmap updates

### Risk: Data Breach / Privacy Issue

**Mitigation:**
- Zero-Trust architecture (local-first)
- Clear privacy policy
- Opt-in telemetry only
- Incident response plan ready

---

## Budget

**Estimated Costs (12 months):**

| Item | Cost |
|------|------|
| Email service (SendGrid/Mailchimp) | $50/month = $600 |
| Survey tool (Google Forms) | Free |
| Discord server (optional) | Free |
| Swag for top contributors (optional) | $500 |
| **Total** | **$1,100** |

**License Value Given Away:**
- 30 testers × $15/month × 12 months = $5,400
- Acceptable for market validation and feedback value

---

## Post-Beta Plan

### Transition Options (Month 12)

**For Beta Testers:**

1. **Upgrade to Paid** (50% off Year 1)
   - Pro: $7.50/month (normally $15)
   - Enterprise: $10/month (normally $20)

2. **Become a Contributor**
   - Contribute code/docs → Extended free access
   - Criteria: 5+ merged PRs

3. **Downgrade to Free Tier**
   - Keep using Cortex with limited features
   - No data lock-in

**For Cortex:**
- Publicly launch (with testimonials from beta testers)
- Case studies from successful beta users
- Beta tester referral program (20% commission)

---

## Contact

**Beta Program Manager**: TBD
**Email**: beta@cortex-mcp.com
**GitHub**: @syab726

---

**Last Updated**: 2026-01-02
