# How to Share These Skills with Your Product Team

## Three Ways to Share

### ✅ Option 1: Simple Shell Scripts (Recommended for Non-Technical Users)

Your product team can run reports using simple interactive scripts:

```bash
./quick-report.sh      # Daily quick report
./analyze-report.sh    # Deep AI analysis
./audit-platforms.sh   # Platform configuration check
```

**Advantages:**
- No command-line knowledge needed
- Interactive prompts guide users
- Simple menu-based interface
- Works immediately

**Share with:**
1. Push to Git (if team has access)
2. Copy folder to shared drive
3. Give team SSH access to server

**Team runs:**
```bash
cd /path/to/meta-slack-reporting
./quick-report.sh
```

---

### Option 2: Claude Code Skills (For Technical Users)

If your team uses Claude Code CLI, they can use slash commands:

```bash
/meta-ads-quick
/meta-ads-analyze
/meta-ads-audit
```

**Advantages:**
- Native Claude integration
- Slash command interface
- Auto-discovered from skills/ directory

**Setup:**
1. Ensure Claude Code is installed
2. Open project directory in Claude Code
3. Skills are auto-discovered from `skills/` folder

---

### Option 3: Shared Server Setup (Recommended for Teams)

Set up on a shared server where team can SSH in:

```bash
# Team SSH into server
ssh user@your-server.com

# Navigate to project
cd ~/analytics/meta-slack-reporting

# Run reports
./quick-report.sh
```

**Advantages:**
- Centralized configuration
- No local setup needed
- Everyone uses same environment
- Easy to update

---

## Testing Without Slack

Before sharing, test without sending to Slack:

```bash
./test-without-slack.sh
```

This will:
- Run reports normally
- NOT send to Slack
- Show you what would be sent
- Restore configuration after

---

## Setting Up for Your Team

### 1. Git Repository (If Using Git)

```bash
# Commit your changes
git add .
git commit -m "Add Meta Ads management skills for product team"
git push

# Team members clone
git clone <your-repo-url>
cd meta-slack-reporting

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Make scripts executable
chmod +x *.sh

# Run reports
./quick-report.sh
```

---

### 2. Shared Folder (If Not Using Git)

```bash
# Copy entire folder to shared location
cp -r /path/to/meta-slack-reporting /shared/drive/meta-ads-tools/

# Team members navigate to folder
cd /shared/drive/meta-ads-tools/meta-slack-reporting

# Run reports
./quick-report.sh
```

---

### 3. Server Setup (Recommended)

```bash
# On your server
cd ~/analytics/meta-slack-reporting

# Verify everything works
./test-without-slack.sh

# Give team members SSH access
# Add their public keys to ~/.ssh/authorized_keys

# They can now SSH and run:
ssh user@server
cd ~/analytics/meta-slack-reporting
./quick-report.sh
```

---

## Documentation for Your Team

Give your team this file: **`FOR_PRODUCT_TEAM.md`**

It contains:
- Simple instructions for non-technical users
- What each report does
- When to use which report
- Troubleshooting guide
- Examples

---

## Configuration

Each account needs its own `.env` file:

```bash
# GRE account (default)
.env

# UPSC account
.env.upsc

# Test account
.env.test
```

**Important fields:**
```bash
META_ADS_ACCOUNT_ID=act_xxxxx
META_ACCESS_TOKEN=EAxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
ACCOUNT_NAME=PrepAiro GRE
PLATFORMS=instagram  # Optional: instagram-only
```

---

## Security Considerations

### ✅ Do:
- Use separate Slack webhooks for each team/channel
- Rotate access tokens regularly
- Keep `.env` files secure (don't commit to Git)
- Use `.gitignore` to exclude secrets

### ❌ Don't:
- Share access tokens publicly
- Commit `.env` files to public repos
- Give everyone admin access to Meta Ads account
- Use same webhook for test and production

---

## Access Control

### Read-Only Access (Recommended for Product Team)
- Product team can only READ data
- Meta access token has `ads_read` permission only
- They can run reports but NOT modify campaigns
- Safe for non-technical users

### Admin Access (For Technical Team Only)
- Tech team has full Meta Ads Manager access
- Can create/modify/delete campaigns
- Manages access tokens and webhooks
- Handles configuration

---

## Maintenance

### Updating Skills
```bash
# You make updates
git add .
git commit -m "Update skills"
git push

# Team members update
cd meta-slack-reporting
git pull
```

### Updating Configuration
```bash
# Edit .env files on server
nano .env

# Or team members update their local copy
nano .env.upsc
```

---

## Training Your Team

### 5-Minute Onboarding

1. **Show them the three scripts:**
   ```bash
   ls -la *.sh
   ```

2. **Run a quick test:**
   ```bash
   ./test-without-slack.sh
   ```

3. **Run a real report:**
   ```bash
   ./quick-report.sh
   ```

4. **Point them to documentation:**
   ```bash
   cat FOR_PRODUCT_TEAM.md
   ```

### Common Questions

**Q: How often should I run reports?**
A: Daily quick reports, weekly deep analysis.

**Q: What if I see an error?**
A: Check the error message - they're user-friendly. If stuck, contact tech team.

**Q: Can I run for both accounts?**
A: Yes! The script will ask which account when you run it.

**Q: Will this spam Slack?**
A: No, reports are sent to your configured channel only when you run the script.

---

## Slack Channel Setup

### Recommended Structure

```
#meta-ads-gre       → GRE daily reports
#meta-ads-upsc      → UPSC daily reports
#meta-ads-analysis  → Deep analysis reports
```

Configure each webhook in respective `.env` files.

---

## Usage Examples

### Daily Standup
```bash
# Product manager runs quick report
./quick-report.sh
# Select: GRE
# Enter: 1 (yesterday only)
# Report appears in Slack
```

### Weekly Team Meeting
```bash
# Team lead runs deep analysis
./analyze-report.sh
# Select: GRE
# Select: Full analysis
# Wait 2-3 minutes
# Report with charts appears in Slack
```

### Troubleshooting Facebook Ads
```bash
# Someone notices Facebook ads
./audit-platforms.sh
# Select: UPSC
# See which adsets have Facebook enabled
# Fix in Meta Ads Manager
```

---

## Next Steps

1. **Test everything:** Run `./test-without-slack.sh`
2. **Document access:** Who has access to what
3. **Train team:** 5-minute walkthrough
4. **Monitor usage:** Check Slack for reports
5. **Iterate:** Gather feedback, improve as needed

---

## Support

If your team has issues:
1. Check `FOR_PRODUCT_TEAM.md` for troubleshooting
2. Look at logs in `logs/` directory
3. Review error messages (they're user-friendly)
4. Contact tech team if stuck

---

## Summary

**Easiest for non-technical users:**
```bash
./quick-report.sh      # Daily
./analyze-report.sh    # Weekly
./audit-platforms.sh   # As needed
```

**Best for teams:**
- Set up on shared server
- Everyone SSH in and runs scripts
- Reports go to Slack
- No local setup needed

**Documentation to share:**
- `FOR_PRODUCT_TEAM.md` - Simple guide
- `skills/QUICK_START.md` - Quick reference
- `skills/README.md` - Detailed docs
