# Site Audit Agent (SAA)

CLI tool for automated website audits using stealthy headless Chromium and LLM-powered analysis.

## Quick Start

```bash
saa init                         # Setup config and API keys
saa audit https://example.com    # Run an audit
```

---

## Installation

### Single User (macOS/Linux) - Recommended

```bash
# Install pipx if needed
brew install pipx        # macOS
# or: sudo apt install pipx   # Ubuntu/Debian

# Install SAA from PyPI
pipx install site-audit-agent

# Setup (installs Chromium, creates config)
saa init

# Add your API keys
vi ~/.saa/.keys
```

### Multi-User Server (Ubuntu/Debian)

System-wide install with shared settings - each user provides their own API keys.

```bash
# 1. Install pipx and SAA (as root)
sudo apt install pipx
sudo PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install site-audit-agent

# 2. Initialize system config (auto-installs Playwright Chromium to /opt/playwright)
sudo saa init --system

# 3. Verify
saa --version
saa audit https://example.com --no-llm -o test.md
```

### Server Install - Quick Copy/Paste

```bash
# As root
sudo apt install pipx
sudo PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install site-audit-agent
sudo saa init --system
```

### Install from GitHub (Latest/Dev)

```bash
# Single user
pipx install git+https://github.com/iXanadu/saa.git

# Multi-user server
sudo PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install git+https://github.com/iXanadu/saa.git
```

### Server Update

```bash
# PyPI version
sudo PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx upgrade site-audit-agent

# GitHub version
sudo PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx reinstall site-audit-agent
```

### Development Install

```bash
cd /path/to/saa
pip install -e .
playwright install chromium
```

---

## Configuration

Config loads in order (later overrides earlier):

| Location | Purpose | Precedence |
|----------|---------|------------|
| `/etc/saa/` | System-wide (admin) | 1 (lowest) |
| `~/.saa/` | User config | 2 |
| `./.env`, `./.keys` | Project override | 3 |
| Environment vars | Runtime override | 4 (highest) |

### Config Files

```
~/.saa/           # or /etc/saa/ for system
├── .env          # Settings
├── .keys         # API keys (keep secret!)
├── audit-plan.md # Default audit plan
└── plans/        # Archived plan versions
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `XAI_API_KEY` | xAI API key (for Grok) |
| `ANTHROPIC_API_KEY` | Anthropic API key (for Claude) |
| `SAA_DEFAULT_LLM` | Default LLM (e.g., `xai:grok`, `anthropic:sonnet`) |
| `SAA_DEFAULT_PLAN` | Path to default audit plan |
| `SAA_OUTPUT_DIR` | Directory for auto-saved reports |
| `SAA_MAX_PAGES` | Max pages to crawl |
| `SAA_DEFAULT_DEPTH` | Max crawl depth |

---

## Usage

### Basic Examples

```bash
saa audit https://example.com              # Basic audit
saa audit https://mysite.com -o report.md  # Save to file
saa audit https://mysite.com -q            # Quiet mode (status line only)
saa audit https://mysite.com -v            # Verbose output
```

### Audit Modes

```bash
saa audit https://mysite.com -m own        # Deep audit (default)
saa audit https://competitor.com -m competitor  # Light scan
```

| Mode | Depth | Max Pages | Purpose |
|------|-------|-----------|---------|
| `own` | 10 | 200 | Deep audit of your sites |
| `competitor` | 1 | 20 | Light scan for insights |

### LLM Options

```bash
saa audit URL -l xai:grok           # Use xAI Grok
saa audit URL -l anthropic:sonnet   # Use Claude Sonnet
saa audit URL --no-llm              # Skip LLM (basic report)
```

### Custom Audit Plans

```bash
saa audit URL -p ./my-plan.md       # Use custom plan
saa audit URL --no-plan             # Skip default plan
```

### Crawl Pacing

```bash
saa audit URL --pacing off          # No delays (fast, detectable)
saa audit URL --pacing low          # 0.5-1.5s delays
saa audit URL --pacing medium       # 1-3s delays (default)
saa audit URL --pacing high         # 2-5s delays (stealthy)
```

---

## Management Commands

### Check for Updates

```bash
saa check                # Compare installed vs latest
saa update               # Update via pipx reinstall
```

### Plan Management

```bash
saa plan                 # Show current plan location
saa plan --view          # Output current plan to stdout
saa plan --edit          # Open plan in editor ($EDITOR or vi)
saa plan --update        # Update to latest bundled plan
saa plan --bundled       # Show the bundled default plan
saa plan --list          # List archived versions
saa plan --rollback      # Restore previous version
```

### View Config

```bash
saa config --list        # Show current settings
```

---

## All Options

```
saa audit [OPTIONS] URL

Options:
  -p, --plan PATH          Custom audit plan (overrides config)
  --no-plan                Skip audit plan
  -m, --mode [own|competitor]  Audit mode
  -d, --depth INTEGER      Max crawl depth
  --max-pages INTEGER      Max pages to crawl
  -l, --llm TEXT           LLM provider:model
  --no-llm                 Skip LLM analysis
  -o, --output PATH        Output file path
  -q, --quiet              Quiet mode (status line only)
  -v, --verbose            Verbose output
  --pacing [off|low|medium|high]  Crawl pacing
```

---

## Updating

```bash
# Check if update available
saa check

# Update (if installed via pipx)
saa update

# Or manually
pipx reinstall saa
```

---

## Troubleshooting

### "playwright: command not found"

Use Python module directly:
```bash
python3 -m playwright install chromium
# Or for pipx install:
~/.local/pipx/venvs/saa/bin/playwright install chromium
```

### "No module named playwright" with sudo

Install to system pipx location:
```bash
sudo PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install ...
```

---

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with assistance from [Claude](https://claude.ai) (Anthropic)
- Uses [Playwright](https://playwright.dev/) for browser automation
- Stealth capabilities via [playwright-stealth](https://github.com/nickmilo/playwright-stealth)
