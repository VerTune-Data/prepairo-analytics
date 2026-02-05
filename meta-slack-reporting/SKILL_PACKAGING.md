# How Skills Are Packaged

## Basic Structure

Skills are simply **folders with files**. No special packaging required!

```
skills/meta-ads-quick/
├── prompt.md              # Required: Instructions for Claude
└── tools/                 # Required: Implementation
    └── quick_report.py    # Your script
```

That's it! Drop this folder in `skills/` and it works.

---

## Packaging Methods

### Method 1: Git Repository (Most Common)

**Structure:**
```
your-repo/
├── skills/
│   ├── meta-ads-quick/
│   ├── meta-ads-analyze/
│   └── meta-ads-audit/
├── modules/               # Shared code
├── .env.example           # Config template
├── requirements.txt       # Python dependencies
└── README.md
```

**Install:**
```bash
git clone https://github.com/your-org/meta-ads-tools
cd meta-ads-tools
# Skills automatically available in ./skills/
```

**Update:**
```bash
git pull
```

---

### Method 2: NPM Package (For Node.js Skills)

**package.json:**
```json
{
  "name": "@your-org/meta-ads-skills",
  "version": "1.0.0",
  "description": "Meta Ads reporting skills for Claude",
  "main": "index.js",
  "files": [
    "skills/"
  ],
  "keywords": ["claude", "skills", "meta-ads"],
  "claudeSkills": {
    "directory": "skills/"
  }
}
```

**Install:**
```bash
npm install @your-org/meta-ads-skills
# Skills available in node_modules/@your-org/meta-ads-skills/skills/
```

---

### Method 3: PyPI Package (For Python Skills)

**setup.py:**
```python
from setuptools import setup, find_packages

setup(
    name='meta-ads-skills',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'meta_ads_skills': [
            'skills/*/prompt.md',
            'skills/*/tools/*'
        ]
    },
    install_requires=[
        'facebook-business>=19.0.0',
        'anthropic',
        'boto3',
    ],
    entry_points={
        'claude_skills': [
            'meta-ads-quick = meta_ads_skills.skills.meta-ads-quick',
            'meta-ads-analyze = meta_ads_skills.skills.meta-ads-analyze',
            'meta-ads-audit = meta_ads_skills.skills.meta-ads-audit',
        ]
    }
)
```

**Install:**
```bash
pip install meta-ads-skills
```

---

### Method 4: Zip Archive (Simple Distribution)

**Create:**
```bash
cd meta-slack-reporting
zip -r meta-ads-skills.zip skills/ modules/ requirements.txt README.md
```

**Install:**
```bash
unzip meta-ads-skills.zip
cd meta-ads-skills
# Skills in ./skills/
```

---

### Method 5: Docker Image (Isolated Environment)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy skills and dependencies
COPY skills/ ./skills/
COPY modules/ ./modules/
COPY requirements.txt .
COPY .env.example .env

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make scripts executable
RUN chmod +x skills/*/tools/*.py

# Default command
CMD ["bash"]
```

**Build & Share:**
```bash
docker build -t meta-ads-skills:1.0.0 .
docker push your-registry/meta-ads-skills:1.0.0
```

**Use:**
```bash
docker run -it --env-file .env meta-ads-skills:1.0.0
# Skills available in /app/skills/
```

---

## Distribution Platforms

### 1. GitHub/GitLab (Open Source)

```
https://github.com/your-org/meta-ads-skills
```

**Advantages:**
- Version control
- Issue tracking
- Pull requests
- Free hosting
- Easy updates via `git pull`

**Installation:**
```bash
git clone https://github.com/your-org/meta-ads-skills
cd meta-ads-skills
```

---

### 2. Private Git Server (Enterprise)

```
https://git.company.com/analytics/meta-ads-skills
```

**Advantages:**
- Private and secure
- Company control
- Internal access only

**Installation:**
```bash
git clone git@git.company.com:analytics/meta-ads-skills.git
cd meta-ads-skills
```

---

### 3. Shared Network Drive

```
/mnt/shared/claude-skills/meta-ads/
```

**Advantages:**
- No Git knowledge required
- Direct file access
- Works offline

**Installation:**
```bash
cp -r /mnt/shared/claude-skills/meta-ads/ ~/my-skills/
```

---

### 4. Skills Registry (Future)

*Hypothetical - not yet available:*

```bash
claude-cli skills install meta-ads-reporting
```

Similar to npm/pip registries for skills.

---

## Skill Metadata

### skill.json (Optional)

Add metadata to your skill:

```json
{
  "name": "meta-ads-quick",
  "version": "1.0.0",
  "description": "Fast Meta Ads performance snapshot",
  "author": "Your Team",
  "license": "MIT",
  "claude": {
    "minVersion": "0.1.0"
  },
  "keywords": ["meta-ads", "reporting", "analytics"],
  "dependencies": {
    "python": ">=3.8",
    "packages": [
      "facebook-business>=19.0.0",
      "requests"
    ]
  },
  "configuration": {
    "required": [
      "META_ADS_ACCOUNT_ID",
      "META_ACCESS_TOKEN",
      "SLACK_WEBHOOK_URL"
    ],
    "optional": [
      "PLATFORMS",
      "REPORT_DAYS"
    ]
  }
}
```

---

## Version Management

### Semantic Versioning

```
1.0.0 → Major.Minor.Patch

1.0.0 - Initial release
1.1.0 - Add new feature
1.1.1 - Bug fix
2.0.0 - Breaking change
```

### Git Tags

```bash
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```

### Changelog

```markdown
# Changelog

## [1.1.0] - 2026-02-05
### Added
- AI-powered insights in analyze skill
- Platform filtering support

### Fixed
- Slack webhook timeout issue

## [1.0.0] - 2026-02-01
### Added
- Initial release with three skills
```

---

## Dependencies Management

### Python (requirements.txt)

```txt
facebook-business==19.0.0
anthropic>=0.18.0
boto3>=1.26.0
matplotlib>=3.5.0
requests>=2.28.0
python-dotenv>=0.19.0
pytz>=2021.3
```

**Install:**
```bash
pip install -r requirements.txt
```

---

### Node.js (package.json)

```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
```

**Install:**
```bash
npm install
```

---

### Docker (All-in-One)

```dockerfile
# All dependencies packaged in image
FROM python:3.11-slim
RUN pip install facebook-business anthropic boto3
# Skills bundled in image
```

**Install:**
```bash
docker pull your-registry/meta-ads-skills:latest
# Everything included, no separate install
```

---

## Configuration Files

### .env.example (Template)

```bash
# Meta Ads Configuration
META_ADS_ACCOUNT_ID=act_xxxxx
META_ACCESS_TOKEN=EAxxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx

# Optional Settings
PLATFORMS=instagram
REPORT_DAYS=7
ACCOUNT_NAME=PrepAiro GRE
```

**User copies and fills in:**
```bash
cp .env.example .env
nano .env  # Fill in actual values
```

---

## Installation Scripts

### install.sh (Automated Setup)

```bash
#!/bin/bash
# Meta Ads Skills Installation Script

echo "Installing Meta Ads Skills..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x skills/*/tools/*.py

# Copy config template
cp .env.example .env

echo "✅ Installation complete!"
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Run: source venv/bin/activate"
echo "3. Test: python3 skills/meta-ads-quick/tools/quick_report.py --help"
```

**Use:**
```bash
./install.sh
```

---

## Sharing Within Teams

### Option 1: Git Submodules

```bash
# Main project
git submodule add https://github.com/your-org/meta-ads-skills skills/

# Team members
git clone --recursive https://github.com/your-org/main-project
```

---

### Option 2: Monorepo

```
company-analytics/
├── skills/
│   ├── meta-ads/
│   ├── google-ads/
│   └── database-tools/
├── shared/
└── docs/
```

**Everyone clones once:**
```bash
git clone https://github.com/company/analytics
# All skills available in skills/
```

---

### Option 3: Symlinks (Development)

```bash
# Shared location
/opt/company-skills/meta-ads/

# Developer's project
cd ~/my-project
ln -s /opt/company-skills/meta-ads skills/meta-ads

# Skills appear in project but stored centrally
```

---

## Publishing Skills

### GitHub Release

```bash
# Tag version
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Create release on GitHub
gh release create v1.0.0 \
  --title "Meta Ads Skills v1.0.0" \
  --notes "Initial release with three skills"
```

**Users install:**
```bash
curl -L https://github.com/your-org/meta-ads-skills/archive/v1.0.0.tar.gz | tar xz
```

---

### NPM Package

```bash
npm publish
```

**Users install:**
```bash
npm install -g @your-org/meta-ads-skills
```

---

### PyPI Package

```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```

**Users install:**
```bash
pip install meta-ads-skills
```

---

## Skill Discovery by Claude

### How Claude Finds Skills

```python
# Simplified version

def discover_skills():
    skill_directories = [
        "./skills",              # Project skills
        "~/.claude/skills",      # Global skills
        "node_modules/*/skills", # NPM installed
        "venv/lib/python*/site-packages/*/skills", # PyPI installed
    ]

    skills = []
    for directory in skill_directories:
        for folder in scan_directories(directory):
            if has_file(folder, "prompt.md"):
                skills.append(register_skill(folder))

    return skills
```

### Where to Install

**Project-specific (current approach):**
```
./skills/meta-ads-quick/
```
Only available in this project.

**Global (all projects):**
```
~/.claude/skills/meta-ads-quick/
```
Available in all Claude sessions.

**Package manager:**
```
node_modules/@your-org/skills/meta-ads-quick/
```
Managed via npm/pip.

---

## Example: Complete Packaging

### Your Current Setup

```
meta-slack-reporting/
├── skills/
│   ├── meta-ads-quick/
│   │   ├── prompt.md
│   │   └── tools/quick_report.py
│   ├── meta-ads-analyze/
│   │   ├── prompt.md
│   │   └── tools/analyze_report.py
│   └── meta-ads-audit/
│       ├── prompt.md
│       └── tools/audit_platforms.py
├── modules/
│   ├── config_loader.py
│   ├── error_handler.py
│   └── ...
├── .env.example
├── requirements.txt
├── README.md
└── LICENSE
```

### Packaging Options

**1. Keep as Git repo (Recommended):**
```bash
# Share repo URL
git clone https://github.com/your-org/meta-slack-reporting
```

**2. Create Python package:**
```bash
pip install meta-ads-reporting
# Skills installed to site-packages
```

**3. Docker image:**
```bash
docker run your-org/meta-ads-reporting
# Everything included
```

**4. Zip for distribution:**
```bash
wget https://releases.company.com/meta-ads-skills-v1.0.0.zip
unzip meta-ads-skills-v1.0.0.zip
```

---

## Best Practices

### ✅ Do:
- Include `README.md` with clear instructions
- Provide `.env.example` template
- Version your releases (semantic versioning)
- Document dependencies in `requirements.txt`
- Include installation script
- Add LICENSE file
- Write clear prompt.md files
- Test on clean systems before releasing

### ❌ Don't:
- Include secrets in repository
- Hard-code configuration
- Forget to document dependencies
- Skip version tags
- Distribute without testing
- Include unnecessary files (use `.gitignore`)

---

## Summary

**Skills are just folders** - no special packaging needed!

**Distribution options:**
1. **Git** (easiest) - Just share repo URL
2. **NPM/PyPI** (for wider distribution)
3. **Docker** (for isolated environments)
4. **Zip** (for simple file sharing)

**Your current setup is already packaged:**
```bash
git clone your-repo
cd meta-slack-reporting
# Skills ready to use in ./skills/
```

**To share with team:**
1. Push to Git
2. Team clones
3. They open folder in Claude Desktop
4. Skills auto-discovered
5. Done!

No complex packaging required!
