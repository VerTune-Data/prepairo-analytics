# Skills System - Complete Explanation

## What Are Skills?

**Skills** are specialized capabilities you can give to Claude to perform specific tasks. Think of them as "plugins" or "extensions" that teach Claude how to do something new.

### Real-World Analogy
- **Claude without skills** = A smart assistant who can think and talk
- **Claude with skills** = Same assistant, but now knows how to run your Meta Ads reports, check your database, etc.

---

## How Skills Work

### The Basic Structure

Every skill has two parts:

```
skills/meta-ads-quick/           # Skill folder
├── prompt.md                    # Instructions for Claude
└── tools/                       # Actual programs to run
    └── quick_report.py          # Python script that does the work
```

### 1. **prompt.md** - The Instructions

This tells Claude:
- What the skill does
- When to use it
- What arguments it accepts
- What output to expect

Example:
```markdown
# Meta Ads Quick Report

Get a fast daily performance snapshot.

## Usage
/meta-ads-quick [--account gre|upsc] [--days 7]

## What it does
Fetches Meta Ads data and sends to Slack
```

### 2. **tools/** - The Implementation

The actual Python script that:
- Connects to Meta Ads API
- Fetches data
- Formats reports
- Sends to Slack

---

## How Skills Are Discovered

### Automatic Discovery

When Claude starts, it looks for skills in specific locations:

```
Current Project:
  ./skills/                      # ← Skills in your project

Global Skills:
  ~/.claude/skills/              # ← Skills available everywhere
```

### Discovery Process

1. **Claude scans** these directories
2. **Finds folders** with `prompt.md` files
3. **Reads prompt.md** to understand what the skill does
4. **Registers** the skill as available
5. **Shows** in slash command autocomplete

---

## How Skills Execute

### Execution Flow

```
User types: /meta-ads-quick --account gre
                    ↓
1. Claude reads the skill's prompt.md
                    ↓
2. Claude understands: "This fetches Meta Ads data"
                    ↓
3. Claude runs: python3 skills/meta-ads-quick/tools/quick_report.py --account gre
                    ↓
4. Script executes (connects to API, fetches data, sends to Slack)
                    ↓
5. Script returns: "✅ Report sent successfully"
                    ↓
6. Claude shows result to user
```

### What Happens Behind the Scenes

```python
# When you use /meta-ads-quick --account gre

# Step 1: Claude identifies the skill
skill = find_skill("meta-ads-quick")

# Step 2: Claude reads prompt.md to understand arguments
arguments = parse_arguments("--account gre")

# Step 3: Claude executes the tool
result = execute(
    command="python3",
    script="skills/meta-ads-quick/tools/quick_report.py",
    args=["--account", "gre"]
)

# Step 4: Claude processes the output
output = result.stdout  # "✅ Report sent successfully to Slack"

# Step 5: Claude shows it to you
display(output)
```

---

## Platform Compatibility

### Where Skills Work

| Platform | Skills Support | How It Works |
|----------|---------------|--------------|
| **Claude Desktop** | ✅ Full | Auto-discovers from project folder |
| **Claude Code CLI** | ✅ Full | Auto-discovers from project folder |
| **Claude.ai Web** | ❌ No | Web version doesn't support skills |
| **API** | ⚠️ Partial | Can implement similar via function calling |

---

## Claude Desktop (The App)

### How It Works

```
1. Open Folder in Claude Desktop
   File → Open Folder → select "meta-slack-reporting"
                    ↓
2. Claude Desktop scans ./skills/ directory
                    ↓
3. Discovers three skills:
   - /meta-ads-quick
   - /meta-ads-analyze
   - /meta-ads-audit
                    ↓
4. Skills appear in slash command menu
                    ↓
5. User types: /meta-ads-quick
                    ↓
6. Claude Desktop executes the skill
                    ↓
7. Shows result in chat
```

### User Experience

**For your product team using Claude Desktop:**

```
User: "Get me yesterday's Meta Ads report for GRE"

Claude: "I'll run the quick report for you using /meta-ads-quick"
        [Executes skill]

        ✅ Report sent successfully to Slack!

        The report shows:
        - Total spend: ₹15,234
        - Impressions: 1.2M
        - Top campaign: GRE Core Conversions

        Check your Slack channel for the full report.

User: "Now analyze with AI insights"

Claude: "I'll run the deep analysis using /meta-ads-analyze"
        [Executes skill with AI enabled]

        ✅ Analysis complete! Report with charts sent to Slack.
```

**Natural conversation** - they don't need to know the commands!

---

## Claude Code CLI

### How It Works

```bash
# In terminal
$ claude

> /meta-ads-quick --account gre --days 7
[Executes skill]
✅ Report sent successfully to Slack

> /meta-ads-analyze --account upsc --ai on
[Executes skill]
✅ Analysis complete - report sent to Slack
```

### Direct Command Mode

```bash
# One-shot execution
$ claude /meta-ads-quick --account gre

# Or via chat
$ claude
> I need a Meta Ads report for yesterday
Claude: [Suggests /meta-ads-quick]
> Yes, run it
Claude: [Executes skill]
```

---

## Skills vs. MCP Servers vs. Shell Scripts

### Comparison

| Feature | Skills | MCP Servers | Shell Scripts |
|---------|--------|-------------|---------------|
| **Discovery** | Auto from `skills/` | Configured in settings | Manual execution |
| **Claude Integration** | Native | Native | External |
| **Slash Commands** | ✅ Yes | ✅ Yes | ❌ No |
| **Cross-Platform** | Desktop + CLI | Desktop + CLI | Terminal only |
| **Setup** | Drop in `skills/` folder | Add to config file | Make executable |
| **Best For** | Project-specific tools | System-wide tools | Simple scripts |

### When to Use What

**Skills** (What we built):
- Project-specific tools
- Tools your team uses in this project only
- Want natural language + slash commands
- Example: Meta Ads reporting for this project

**MCP Servers**:
- System-wide tools (work across all projects)
- Integrations with external services
- Tools shared across many projects
- Example: Database connector, Slack integration, etc.

**Shell Scripts** (Also provided):
- Simple automation
- Users without Claude Desktop
- Quick one-off tasks
- Example: Cron jobs, manual execution

---

## How Your Product Team Uses Skills

### Scenario 1: Non-Technical User with Claude Desktop

**Sarah (Product Manager) needs daily reports:**

```
1. Opens Claude Desktop
2. Opens "meta-slack-reporting" folder
3. Types in chat: "I need yesterday's Meta Ads performance"
4. Claude suggests: /meta-ads-quick
5. Claude runs it automatically
6. Report appears in Slack
7. Sarah sees: "✅ Done! Check Slack"
```

**Sarah never:**
- Touched a terminal
- Ran a Python script
- Knew what an API is
- Understood the technical implementation

---

### Scenario 2: Technical User with Claude Code CLI

**Alex (Data Analyst) needs detailed analysis:**

```bash
$ claude

Alex: /meta-ads-analyze --account gre --range 7d --ai on

[Claude executes skill]
- Fetching 7 days of data...
- Generating AI insights...
- Creating charts...
- Uploading to S3...
- Sending to Slack...

✅ Analysis complete!

Alex: Now show me platform configuration

Claude: [Runs /meta-ads-audit automatically]
[Shows terminal output]

Summary:
- Instagram-only: 1 adset
- Active Facebook: 0 adsets
✅ Configuration looks good
```

---

### Scenario 3: Mixed Team

**Different team members, same tools:**

| Person | Platform | How They Use It |
|--------|----------|-----------------|
| Sarah (PM) | Claude Desktop | Natural language: "Get me a report" |
| Alex (Analyst) | Claude Code CLI | Direct: `/meta-ads-analyze --ai on` |
| Mike (Ops) | SSH + Scripts | Shell: `./quick-report.sh` |

**Same backend, different interfaces!**

---

## Skill Execution Environment

### What Happens When Skill Runs

```
User: /meta-ads-quick --account gre
                    ↓
┌─────────────────────────────────────┐
│   Claude (Desktop or CLI)           │
│                                     │
│  1. Finds skill in skills/ folder   │
│  2. Reads prompt.md                 │
│  3. Validates arguments             │
│  4. Prepares execution              │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│   Subprocess Execution              │
│                                     │
│  python3 skills/.../quick_report.py │
│           --account gre             │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│   Your Python Script                │
│                                     │
│  1. Loads config from .env          │
│  2. Connects to Meta Ads API        │
│  3. Fetches data                    │
│  4. Formats report                  │
│  5. Sends to Slack                  │
│  6. Returns: "✅ Success"           │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│   Claude Displays Result            │
│                                     │
│  Shows: "✅ Report sent to Slack"   │
└─────────────────────────────────────┘
```

### Environment Details

**Working Directory**: Project root
```bash
/Users/anigam/analytics/meta-slack-reporting/
```

**Virtual Environment**: Activated automatically
```bash
source venv/bin/activate
```

**Environment Variables**: Loaded from .env
```bash
META_ADS_ACCOUNT_ID=act_xxx
META_ACCESS_TOKEN=xxx
SLACK_WEBHOOK_URL=xxx
```

**Standard Output**: Captured and shown to user
```bash
Loading configuration...
Connecting to API...
✅ Report sent successfully
```

**Logs**: Written to logs/ directory
```bash
logs/meta_ads_quick_20260205.log
```

---

## Advanced: How Skills Are Structured

### Complete Skill Anatomy

```
skills/meta-ads-quick/
│
├── prompt.md                    # Required: Claude's instructions
│   ├── Title
│   ├── Description
│   ├── Usage examples
│   ├── Arguments
│   └── Output description
│
└── tools/                       # Required: Implementation
    ├── quick_report.py          # Main script
    ├── helpers.py               # Optional: Helper functions
    └── config.json              # Optional: Skill-specific config
```

### prompt.md Structure

```markdown
# Skill Title

Brief description of what it does.

## Usage
/skill-name [arguments]

## Arguments
- --arg1: Description
- --arg2: Description

## What You Get
- Output 1
- Output 2

## Examples
/skill-name --arg1 value
```

### Why This Structure?

1. **prompt.md** = Claude's understanding
   - Claude reads this to know what the skill does
   - Used for natural language matching
   - Helps Claude suggest when to use the skill

2. **tools/** = Actual implementation
   - Can be any language (Python, Bash, Node.js, etc.)
   - Must be executable
   - Returns output to stdout

---

## Skill Discovery in Detail

### Discovery Algorithm

```python
# Simplified version of how Claude discovers skills

def discover_skills(directories):
    skills = []

    for directory in directories:
        # Find all subdirectories
        for folder in directory.subdirectories():
            # Check if it has prompt.md
            if folder.has_file("prompt.md"):
                # Read the prompt
                prompt = read_file(folder / "prompt.md")

                # Parse skill metadata
                skill = {
                    "name": folder.name,
                    "prompt": prompt,
                    "tools_dir": folder / "tools",
                    "slash_command": f"/{folder.name}"
                }

                skills.append(skill)

    return skills

# When Claude starts:
skills = discover_skills([
    "./skills",              # Project skills
    "~/.claude/skills"       # Global skills
])

# Register them
for skill in skills:
    register_slash_command(skill["slash_command"], skill)
```

---

## Cross-Platform Execution

### How Skills Work Everywhere

```
Same Skill Files:
skills/meta-ads-quick/
├── prompt.md
└── tools/quick_report.py

Used In Different Platforms:

┌──────────────────┐
│ Claude Desktop   │──┐
│ (Mac/Windows)    │  │
└──────────────────┘  │
                      ├──→ Same skill files
┌──────────────────┐  │
│ Claude Code CLI  │──┤
│ (Terminal)       │  │
└──────────────────┘  │
                      │
┌──────────────────┐  │
│ SSH Server       │──┘
│ (Remote)         │
└──────────────────┘
```

### Platform-Specific Behavior

**Claude Desktop:**
- GUI interface
- Natural language interaction
- Slash command autocomplete
- Pretty output formatting

**Claude Code CLI:**
- Terminal interface
- Direct slash commands
- Raw output
- Scriptable

**Shell Scripts (Fallback):**
- No Claude needed
- Works anywhere
- Simple menu interface
- Direct execution

---

## Security & Permissions

### What Skills Can Access

**Skills run with YOUR permissions:**
```
├── File System: ✅ Full access to project directory
├── Environment Variables: ✅ Can read .env files
├── Network: ✅ Can make API calls
├── System Commands: ✅ Can run any command
└── User Data: ✅ Full access
```

**Important:** Only use skills you trust!

### Safe Practices

✅ **Do:**
- Review skill code before using
- Keep skills in version control
- Use environment variables for secrets
- Limit network access in production

❌ **Don't:**
- Run unknown skills from internet
- Store secrets in skill code
- Give skills root/admin access
- Share sensitive .env files

---

## Debugging Skills

### When Skills Don't Work

**Check these in order:**

1. **Is skill discovered?**
   ```bash
   # In Claude Desktop/CLI
   Type: /met[tab]
   # Should autocomplete to /meta-ads-quick
   ```

2. **Is prompt.md valid?**
   ```bash
   cat skills/meta-ads-quick/prompt.md
   # Should have proper markdown formatting
   ```

3. **Is tool executable?**
   ```bash
   ls -la skills/meta-ads-quick/tools/quick_report.py
   # Should show: -rwxr-xr-x (executable bit)
   ```

4. **Does tool run manually?**
   ```bash
   python3 skills/meta-ads-quick/tools/quick_report.py --help
   # Should show help text
   ```

5. **Check logs:**
   ```bash
   tail -f logs/meta_ads_quick_*.log
   # Watch for errors
   ```

---

## Summary: The Complete Picture

### What We Built

```
Project Skills System:

skills/
├── meta-ads-quick/          # Fast daily reports
│   ├── prompt.md           # Claude understands this
│   └── tools/
│       └── quick_report.py  # Does the actual work
│
├── meta-ads-analyze/        # Deep AI analysis
│   ├── prompt.md
│   └── tools/
│       └── analyze_report.py
│
└── meta-ads-audit/          # Platform checker
    ├── prompt.md
    └── tools/
        └── audit_platforms.py
```

### How It Works Across Platforms

```
┌─────────────────────────────────────────────┐
│          Your Product Team                  │
│                                             │
│  Sarah uses      Alex uses       Mike uses  │
│  Claude Desktop  Claude CLI      Shell      │
└──────┬──────────────┬─────────────┬─────────┘
       │              │             │
       ├──────────────┼─────────────┤
       │              │             │
       ↓              ↓             ↓
┌──────────────────────────────────────────────┐
│          Same Backend Skills                 │
│                                              │
│  /meta-ads-quick                             │
│  /meta-ads-analyze                           │
│  /meta-ads-audit                             │
└──────────────────────────────────────────────┘
       │              │             │
       ├──────────────┼─────────────┤
       │              │             │
       ↓              ↓             ↓
┌──────────────────────────────────────────────┐
│          Python Scripts                      │
│                                              │
│  • Load config from .env                     │
│  • Connect to Meta Ads API                   │
│  • Generate reports                          │
│  • Send to Slack                             │
└──────────────────────────────────────────────┘
```

### Key Takeaways

1. **Skills = Instructions (prompt.md) + Tools (Python scripts)**
2. **Auto-discovered** from `skills/` folder
3. **Work in Claude Desktop** (GUI) and **Claude Code CLI** (terminal)
4. **Natural language** or **slash commands**
5. **Your team** doesn't need to know technical details
6. **Same skills** work across all platforms
7. **Secure** - runs with your permissions in your environment

---

## For Your Product Team

**What they need to know:**

1. Open project in Claude Desktop
2. Type: `/meta-ads-quick`
3. Or just ask: "Get me a Meta Ads report"
4. That's it!

**What they don't need to know:**

- How skills work
- Python programming
- API integration
- Technical implementation
- File structure

The skills system handles everything automatically!

---

**Questions?** Check the other documentation:
- `FOR_PRODUCT_TEAM.md` - Simple usage guide
- `HOW_TO_SHARE.md` - Sharing strategies
- `skills/README.md` - Technical details
