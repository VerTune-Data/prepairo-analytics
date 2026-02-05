# Skills Catalog

This document lists all available skills in this project.

## Available Skills

### 1. meta-ads-quick
**Fast daily Meta Ads performance snapshot**

- **Version:** 1.0.0
- **Speed:** ~30 seconds
- **Output:** Slack message
- **AI Powered:** No
- **Requirements:** Meta API, Slack webhook

**Use when:**
- Quick morning check-in
- Fast performance overview
- Daily standup metrics

**Command:**
```bash
/meta-ads-quick --account gre --days 7
```

---

### 2. meta-ads-analyze
**Deep AI-powered analysis with trends and conversions**

- **Version:** 1.0.0
- **Speed:** ~2-3 minutes
- **Output:** Multi-message Slack report with charts
- **AI Powered:** Yes (Claude)
- **Requirements:** Meta API, Slack webhook, Claude API, AWS S3, SQLite

**Use when:**
- Weekly deep-dives
- Performance optimization needed
- Preparing presentations
- Need conversion metrics (CPI, CPR, CPA)

**Command:**
```bash
/meta-ads-analyze --account gre --ai on --charts on
```

---

### 3. meta-ads-audit
**Platform configuration checker (Facebook vs Instagram)**

- **Version:** 1.0.0
- **Speed:** ~10 seconds
- **Output:** Terminal report
- **AI Powered:** No
- **Requirements:** Meta API

**Use when:**
- Facebook ads appearing unexpectedly
- Verifying Instagram-only configuration
- Troubleshooting platform issues
- Auditing ad placements

**Command:**
```bash
/meta-ads-audit --account gre
```

---

## Quick Reference

| Skill | Speed | AI | Charts | Database | Output |
|-------|-------|----|-|----------|--------|
| **meta-ads-quick** | 30s | ❌ | ❌ | ❌ | Slack |
| **meta-ads-analyze** | 2-3min | ✅ | ✅ | ✅ | Slack + Charts |
| **meta-ads-audit** | 10s | ❌ | ❌ | ❌ | Terminal |

## Skill Details

For detailed documentation on each skill, see:
- `skills/meta-ads-quick/SKILL.md`
- `skills/meta-ads-analyze/SKILL.md`
- `skills/meta-ads-audit/SKILL.md`

## Usage Patterns

### Daily Workflow
```bash
# Morning check
/meta-ads-quick

# If issues found
/meta-ads-audit
```

### Weekly Workflow
```bash
# Deep analysis
/meta-ads-analyze --range 7d

# Check configuration
/meta-ads-audit
```

### Troubleshooting Workflow
```bash
# 1. Check configuration
/meta-ads-audit

# 2. Get quick metrics
/meta-ads-quick --days 1

# 3. Deep dive if needed
/meta-ads-analyze --ai on
```

## Multi-Account Support

All skills support multiple accounts:

```bash
# GRE account (default)
/meta-ads-quick

# UPSC account
/meta-ads-quick --account upsc

# Test account
/meta-ads-quick --account test
```

## Configuration

Each account requires a `.env.{account}` file with:

```bash
META_ADS_ACCOUNT_ID=act_xxxxx
META_ACCESS_TOKEN=EAxxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
ACCOUNT_NAME=Account Name
PLATFORMS=instagram  # Optional: platform filtering
```

## Development

### Adding a New Skill

1. Create skill directory:
   ```bash
   mkdir -p skills/my-new-skill/tools
   ```

2. Create `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: my-new-skill
   description: Brief description
   version: 1.0.0
   ---
   ```

3. Create tool implementation:
   ```bash
   touch skills/my-new-skill/tools/main.py
   chmod +x skills/my-new-skill/tools/main.py
   ```

4. Update this file with new skill info

### Testing Skills

```bash
# Without Slack
./test-without-slack.sh

# With Slack
source venv/bin/activate
python3 skills/skill-name/tools/main.py --help
```

## Version History

- **1.0.0** (2026-02-05)
  - Initial release
  - Three core skills (quick, analyze, audit)
  - Multi-account support
  - Comprehensive error handling

## License

Internal use only - Analytics Team

## Support

For issues or questions:
1. Check skill-specific logs in `logs/`
2. Review skill documentation in `skills/*/SKILL.md`
3. See troubleshooting guide in `FOR_PRODUCT_TEAM.md`
4. Contact Analytics Team
