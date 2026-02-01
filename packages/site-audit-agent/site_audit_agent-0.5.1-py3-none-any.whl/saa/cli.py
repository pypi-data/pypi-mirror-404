"""CLI entry point for Site Audit Agent."""

import asyncio
import os
from pathlib import Path

import click

from saa import __version__
from saa.config import load_config
from saa.crawler import Crawler
from saa.checks import run_checks, DEFAULT_CHECKS_OWN, DEFAULT_CHECKS_COMPETITOR
from saa.report import generate_report
from saa.llm import get_llm_client
from saa.plan import load_plan


@click.group()
@click.version_option(version=__version__, prog_name="saa")
def main():
    """Site Audit Agent - Automated website audits with LLM analysis.

    \b
    Quick Start:
      saa init                         # Setup config and API keys
      saa audit https://example.com    # Run an audit

    \b
    Audit Examples:
      saa audit https://mysite.com -o report.md       # Save to file
      saa audit https://mysite.com -q                 # Quiet (status line only)
      saa audit https://mysite.com -v                 # Verbose output
      saa audit https://mysite.com -m own             # Deep audit (default)
      saa audit https://competitor.com -m competitor  # Light competitor scan
      saa audit https://mysite.com -l anthropic:sonnet  # Use Claude
      saa audit https://mysite.com --no-llm           # Skip LLM analysis
      saa audit https://mysite.com -p custom-plan.md  # Custom audit plan
      saa audit https://mysite.com --pacing high      # Slower, stealthier

    \b
    Management:
      saa check                        # Check for updates
      saa update                       # Update to latest version
      saa plan --list                  # List archived plans
      saa config --list                # Show current config
    """
    pass


@main.command()
@click.argument("url")
@click.option("--plan", "-p", type=click.Path(exists=True), help="Path to MD audit plan (overrides config)")
@click.option("--no-plan", is_flag=True, help="Skip audit plan even if configured")
@click.option("--mode", "-m", type=click.Choice(["own", "competitor"]), default="own",
              help="Audit mode: own (deep) or competitor (light)")
@click.option("--depth", "-d", type=int, default=None,
              help="Max crawl depth (default: 3 for own, 1 for competitor)")
@click.option("--max-pages", type=int, default=None,
              help="Max pages to crawl (default: 50 for own, 20 for competitor)")
@click.option("--llm", "-l", default=None, help="LLM provider:model (e.g., xai:grok, anthropic:sonnet)")
@click.option("--no-llm", is_flag=True, help="Skip LLM analysis (basic report only)")
@click.option("--output", "-o", type=click.Path(), help="Output report path (overrides config)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode (single status line)")
@click.option("--pacing", type=click.Choice(["off", "low", "medium", "high"]),
              default="medium", help="Crawl pacing level")
def audit(url: str, plan: str, no_plan: bool, mode: str, depth: int, max_pages: int,
          llm: str, no_llm: bool, output: str, verbose: bool, quiet: bool, pacing: str):
    """Run an audit on URL.

    Examples:
        saa audit https://example.com --mode own --verbose
        saa audit https://competitor.com --mode competitor --llm xai:grok
        saa audit https://mysite.com --no-llm -o report.md
    """
    from datetime import datetime
    from urllib.parse import urlparse

    config = load_config()

    # Override config with CLI options
    config.mode = mode
    config.pacing = pacing
    if llm:
        config.default_llm = llm

    # Resolve plan: CLI > config > none
    if no_plan:
        plan = None
    elif not plan and config.default_plan:
        plan_path = Path(config.default_plan)
        if plan_path.exists():
            plan = str(plan_path)
        elif verbose:
            click.echo(f"Warning: Configured plan not found: {config.default_plan}")

    # Resolve output: CLI > config (auto-generate filename) > stdout
    if not output and config.output_dir:
        output_dir = Path(config.output_dir)
        if output_dir.exists():
            domain = urlparse(url).netloc.replace(":", "_")
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            output = str(output_dir / f"{domain}_{timestamp}.md")
        elif verbose:
            click.echo(f"Warning: Output dir not found: {config.output_dir}")

    # Set depth and max_pages based on mode if not specified
    # For "own" mode: full crawl (high limits to capture entire site)
    # For "competitor" mode: light scan (limited to avoid detection/overload)
    if depth is None:
        depth = 10 if mode == "own" else 1
    if max_pages is None:
        max_pages = 200 if mode == "own" else 20

    if verbose:
        click.echo(f"Starting audit of {url}")
        click.echo(f"Mode: {mode}, Depth: {depth}, Max pages: {max_pages}, Pacing: {pacing}")
        if plan:
            click.echo(f"Using audit plan: {plan}")
        if output:
            click.echo(f"Output: {output}")
        if not no_llm:
            click.echo(f"LLM: {config.default_llm}")

    # Run the async audit
    try:
        asyncio.run(_run_audit(url, config, plan, output, verbose, quiet, mode, depth, max_pages, no_llm))
    except KeyboardInterrupt:
        click.echo("\nAudit cancelled.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


def _make_progress_callback(quiet: bool):
    """Create a progress callback for quiet mode."""
    if not quiet:
        return None

    import shutil
    term_width = shutil.get_terminal_size().columns

    def callback(current: int, total: int, url: str):
        # Truncate URL to fit terminal
        prefix = f"[{current}/{total}] "
        max_url_len = term_width - len(prefix) - 1
        if len(url) > max_url_len:
            url = url[:max_url_len-3] + "..."
        line = f"{prefix}{url}"
        # Pad to terminal width to clear previous content
        line = line.ljust(term_width - 1)
        click.echo(f"\r{line}", nl=False)

    return callback


async def _run_audit(url: str, config, plan_path: str, output_path: str,
                     verbose: bool, quiet: bool, mode: str, depth: int, max_pages: int, no_llm: bool):
    """Execute the audit asynchronously."""
    if not quiet:
        click.echo(f"Auditing: {url}")

    # Load audit plan if provided
    plan_content = None
    if plan_path:
        plan_content = load_plan(plan_path)
        if verbose:
            click.echo(f"Loaded audit plan ({len(plan_content)} chars)")

    # Create progress callback for quiet mode
    progress_callback = _make_progress_callback(quiet)

    # Crawl pages
    async with Crawler(config, verbose=verbose, progress_callback=progress_callback) as crawler:
        pages = await crawler.crawl(url, max_depth=depth, max_pages=max_pages)

    # Clear progress line and show summary in quiet mode
    if quiet:
        import shutil
        term_width = shutil.get_terminal_size().columns
        click.echo("\r" + " " * (term_width - 1) + "\r", nl=False)  # Clear line
        successful = sum(1 for p in pages if not p.error)
        click.echo(f"Crawled {len(pages)} pages ({successful} successful)")

    # Check if we got any successful pages
    successful_pages = [p for p in pages if not p.error]
    if not successful_pages:
        click.echo("Failed to fetch any pages.", err=True)
        raise SystemExit(1)

    # Run checks based on mode
    checks_to_run = DEFAULT_CHECKS_OWN if mode == "own" else DEFAULT_CHECKS_COMPETITOR
    findings = run_checks(successful_pages, checks_to_run)

    # Get LLM client if enabled
    llm_client = None
    if not no_llm:
        try:
            llm_client = get_llm_client(config.default_llm, config)
            if verbose:
                click.echo(f"Using LLM: {config.default_llm}")
        except ValueError as e:
            if verbose:
                click.echo(f"LLM not available: {e}")
                click.echo("Generating basic report without LLM analysis.")

    # Generate report
    output_text = generate_report(
        start_url=url,
        pages=pages,
        findings=findings,
        mode=mode,
        llm_client=llm_client,
        verbose=verbose,
        plan_content=plan_content,
    )

    if output_path:
        Path(output_path).write_text(output_text)
        click.echo(f"\nReport saved to: {output_path}")
    else:
        click.echo(output_text)


@main.command()
@click.option("--set", "set_key", nargs=2, metavar="KEY VALUE", help="Set config key value")
@click.option("--get", "get_key", metavar="KEY", help="Get config value")
@click.option("--list", "list_all", is_flag=True, help="List all config")
def config(set_key, get_key, list_all):
    """View or set configuration."""
    cfg = load_config()

    if list_all:
        click.echo("Current configuration:")
        click.echo(f"  chromium_path: {cfg.chromium_path}")
        click.echo(f"  default_llm: {cfg.default_llm}")
        click.echo(f"  max_pages: {cfg.max_pages}")
        click.echo(f"  default_depth: {cfg.default_depth}")
        click.echo(f"  pacing: {cfg.pacing}")
    elif get_key:
        value = getattr(cfg, get_key, None)
        if value is not None:
            click.echo(f"{get_key}: {value}")
        else:
            click.echo(f"Unknown config key: {get_key}")
    elif set_key:
        click.echo("Config setting not yet implemented - edit .env directly")
    else:
        click.echo("Use --list to see all config, --get KEY to get a value")


def _get_real_user_home() -> Path:
    """Get the real user's home directory, even when running under sudo."""
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        # Running under sudo - get the original user's home
        import pwd
        try:
            return Path(pwd.getpwnam(sudo_user).pw_dir)
        except KeyError:
            pass
    return Path.home()


def _check_chromium_installed(system: bool = False) -> bool:
    """Check if Playwright Chromium is installed."""
    import sys

    # Always check system location /opt/playwright first (works for all users)
    system_dir = Path("/opt/playwright")
    if system_dir.exists():
        chromium_dirs = list(system_dir.glob("chromium-*"))
        if chromium_dirs:
            return True

    # For system installs, only check /opt/playwright
    if system:
        return False

    # Check PLAYWRIGHT_BROWSERS_PATH env var
    browsers_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if browsers_path:
        cache_dir = Path(browsers_path)
    elif sys.platform == "darwin":
        cache_dir = Path.home() / "Library/Caches/ms-playwright"
    else:
        cache_dir = Path.home() / ".cache/ms-playwright"

    if not cache_dir.exists():
        return False

    chromium_dirs = list(cache_dir.glob("chromium-*"))
    return len(chromium_dirs) > 0


def _install_chromium(system: bool = False) -> bool:
    """Install Playwright Chromium. Returns True on success."""
    import shutil
    import subprocess

    # Find playwright executable - check pipx locations FIRST to avoid pyenv issues
    playwright_cmd = None

    # Try system pipx location first
    system_playwright = Path("/opt/pipx/venvs/site-audit-agent/bin/playwright")
    if system_playwright.exists():
        playwright_cmd = str(system_playwright)

    # Try user pipx location
    if not playwright_cmd:
        pipx_playwright = Path.home() / ".local/pipx/venvs/site-audit-agent/bin/playwright"
        if pipx_playwright.exists():
            playwright_cmd = str(pipx_playwright)

    # Fall back to PATH (may be intercepted by pyenv, but worth trying)
    if not playwright_cmd:
        playwright_cmd = shutil.which("playwright")

    if not playwright_cmd:
        return False

    if system:
        # Install to /opt/playwright system-wide
        system_dir = Path("/opt/playwright")
        system_dir.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["PLAYWRIGHT_BROWSERS_PATH"] = str(system_dir)

        # Install chromium
        result = subprocess.run([playwright_cmd, "install", "chromium"], env=env)
        if result.returncode != 0:
            return False

        # Install system dependencies
        subprocess.run([playwright_cmd, "install-deps"], env=env)

        # Make readable by all users
        subprocess.run(["chmod", "-R", "a+rX", str(system_dir)])
        return True
    else:
        result = subprocess.run([playwright_cmd, "install", "chromium"])
        return result.returncode == 0


def _check_api_keys(keys_file: Path = None) -> dict:
    """Check which API keys are configured. Returns dict of provider: bool.

    Checks both the keys file (if provided and readable) and environment variables.
    """
    keys = {"xai": False, "anthropic": False}

    # Check environment variables first
    if os.getenv("XAI_API_KEY", ""):
        keys["xai"] = True
    if os.getenv("ANTHROPIC_API_KEY", ""):
        keys["anthropic"] = True

    # Check keys file if provided
    if keys_file and keys_file.exists():
        try:
            content = keys_file.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                if line.startswith("XAI_API_KEY=") and len(line.split("=", 1)[1]) > 5:
                    keys["xai"] = True
                if line.startswith("ANTHROPIC_API_KEY=") and len(line.split("=", 1)[1]) > 5:
                    keys["anthropic"] = True
        except PermissionError:
            pass  # Can't read file, rely on env vars

    return keys


def _get_bundled_plan() -> str:
    """Get the bundled default audit plan content."""
    import importlib.resources as pkg_resources
    try:
        # Python 3.11+
        plan_source = pkg_resources.files("saa.data").joinpath("default-audit-plan.md")
        return plan_source.read_text()
    except (TypeError, AttributeError):
        # Fallback for older Python
        with pkg_resources.open_text("saa.data", "default-audit-plan.md") as f:
            return f.read()


def _get_saa_dir(system: bool) -> Path:
    """Get the SAA config directory path."""
    if system:
        return Path("/etc/saa")
    return Path.home() / ".saa"


def _archive_plan(saa_dir: Path, plan_file: Path) -> Path | None:
    """Archive existing plan to plans/ directory. Returns archive path."""
    from datetime import datetime

    if not plan_file.exists():
        return None

    plans_dir = saa_dir / "plans"
    plans_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = plans_dir / f"audit-plan_{timestamp}.md"
    archive_path.write_text(plan_file.read_text())
    return archive_path


def _plan_needs_update(saa_dir: Path) -> bool:
    """Check if installed plan differs from bundled plan."""
    plan_file = saa_dir / "audit-plan.md"
    if not plan_file.exists():
        return True

    try:
        bundled = _get_bundled_plan()
        installed = plan_file.read_text()
        return bundled.strip() != installed.strip()
    except Exception:
        return False


@main.command()
@click.option("--system", is_flag=True, help="Initialize system-wide config at /etc/saa/ (requires sudo)")
@click.option("--update-plan", is_flag=True, help="Update audit plan to latest version (archives old)")
def init(system: bool, update_plan: bool):
    """Initialize SAA and check dependencies.

    Checks Playwright/Chromium, creates config files, validates setup.

    \b
    Config loading priority (later overrides earlier):
      1. /etc/saa/    - System-wide (admin-managed, for multi-user servers)
      2. ~/.saa/      - User config (single-user or user overrides)
      3. ./.env       - Project-specific overrides

    \b
    Examples:
      saa init                    # Create ~/.saa/ for current user
      sudo saa init --system      # Create /etc/saa/ for all users
      saa init --update-plan      # Update audit plan, archive old version
    """
    import os

    # Handle --update-plan separately (quick path)
    if update_plan:
        saa_dir = _get_saa_dir(system)
        if system and os.geteuid() != 0:
            click.echo("Error: --system requires root.", err=True)
            raise SystemExit(1)

        plan_file = saa_dir / "audit-plan.md"
        if not saa_dir.exists():
            click.echo(f"Error: Config directory not found: {saa_dir}", err=True)
            click.echo("Run 'saa init' first.")
            raise SystemExit(1)

        try:
            # Archive existing plan
            if plan_file.exists():
                archive_path = _archive_plan(saa_dir, plan_file)
                click.echo(f"Archived: {archive_path}")

            # Install new plan
            plan_content = _get_bundled_plan()
            plan_file.write_text(plan_content)
            click.echo(f"Updated:  {plan_file}")
            click.echo("\nTo rollback: saa plan --rollback")
        except Exception as e:
            click.echo(f"Error updating plan: {e}", err=True)
            raise SystemExit(1)
        return

    click.echo("SAA Setup\n")

    # 1. Check Chromium
    click.echo("Checking dependencies...")
    chromium_ok = _check_chromium_installed(system=system)
    if chromium_ok:
        if system:
            click.echo("  [ok] Playwright Chromium installed in /opt/playwright")
        else:
            click.echo("  [ok] Playwright Chromium installed")
    else:
        click.echo("  [!!] Playwright Chromium not found")
        if click.confirm("       Install Chromium now?", default=True):
            if system:
                click.echo("       Installing Chromium to /opt/playwright (this may take a minute)...")
            else:
                click.echo("       Installing Chromium (this may take a minute)...")
            if _install_chromium(system=system):
                click.echo("       [ok] Chromium installed")
                chromium_ok = True
            else:
                click.echo("       [!!] Installation failed. Try manually:")
                if system:
                    click.echo("            sudo mkdir -p /opt/playwright")
                    click.echo("            sudo PLAYWRIGHT_BROWSERS_PATH=/opt/playwright playwright install chromium")
                else:
                    click.echo("            playwright install chromium")
        else:
            if system:
                click.echo("       Skipped. Install later with:")
                click.echo("            sudo mkdir -p /opt/playwright")
                click.echo("            sudo PLAYWRIGHT_BROWSERS_PATH=/opt/playwright playwright install chromium")
            else:
                click.echo("       Skipped. Install later with: playwright install chromium")

    click.echo("")

    # 2. Setup config directory
    system_dir = Path("/etc/saa")
    has_system_config = system_dir.exists() and (system_dir / ".env").exists()

    if system:
        saa_dir = system_dir
        if os.geteuid() != 0:
            click.echo("Error: --system requires root. Use: sudo saa init --system", err=True)
            raise SystemExit(1)
    else:
        saa_dir = Path.home() / ".saa"

    # For user init with existing system config, only create keys
    if not system and has_system_config:
        click.echo(f"System config: {system_dir}")
        click.echo(f"  [ok] Using system config at {system_dir}")
        click.echo(f"  [ok] System plan at {system_dir / 'audit-plan.md'}")

        # Only create user keys directory and file
        click.echo(f"\nUser config: {saa_dir}")
        saa_dir.mkdir(exist_ok=True)

        keys_file = saa_dir / ".keys"
        keys_created = False
        if not keys_file.exists():
            keys_file.write_text(
                "# API Keys for LLM providers\n"
                "# At least one key is required for LLM-powered analysis.\n"
                "# Get keys from:\n"
                "#   xAI:       https://console.x.ai/\n"
                "#   Anthropic: https://console.anthropic.com/\n"
                "#\n"
                "# Uncomment and add your key(s):\n"
                "# XAI_API_KEY=xai-your-key-here\n"
                "# ANTHROPIC_API_KEY=sk-ant-your-key-here\n"
            )
            os.chmod(keys_file, 0o600)
            click.echo(f"  [ok] Created {keys_file}")
            keys_created = True
        else:
            click.echo(f"  [ok] Exists  {keys_file}")
    else:
        # Full init (system install, or user install without system config)
        click.echo(f"Config directory: {saa_dir}")
        saa_dir.mkdir(exist_ok=True)

        # Copy default audit plan from package
        plan_file = saa_dir / "audit-plan.md"
        if not plan_file.exists():
            try:
                plan_content = _get_bundled_plan()
                plan_file.write_text(plan_content)
                click.echo(f"  [ok] Created {plan_file}")
            except Exception as e:
                click.echo(f"  [!!] Could not copy default audit plan: {e}")
        else:
            # Check if update available
            if _plan_needs_update(saa_dir):
                click.echo(f"  [ok] Exists  {plan_file}")
                click.echo(f"       [!!] Newer plan available: saa init --update-plan")
            else:
                click.echo(f"  [ok] Exists  {plan_file}")

        env_file = saa_dir / ".env"
        if not env_file.exists():
            # Different defaults for system vs user install
            if system:
                playwright_line = "PLAYWRIGHT_BROWSERS_PATH=/opt/playwright\n"
                plan_path = plan_file
            else:
                playwright_line = "# PLAYWRIGHT_BROWSERS_PATH=/opt/playwright\n"
                plan_path = plan_file

            env_file.write_text(
                "# SAA Configuration\n"
                "# Uncomment and edit the settings you want to change.\n"
                "#\n"
                "# Playwright browser location (system-wide: /opt/playwright)\n"
                f"{playwright_line}"
                "#\n"
                "# Default LLM provider:model (xai:grok, anthropic:sonnet, anthropic:opus)\n"
                "# SAA_DEFAULT_LLM=xai:grok\n"
                "#\n"
                "# Crawl limits\n"
                "# SAA_MAX_PAGES=50\n"
                "# SAA_DEFAULT_DEPTH=3\n"
                "#\n"
                f"# Default audit plan (created above)\n"
                f"SAA_DEFAULT_PLAN={plan_path}\n"
                "#\n"
                "# Output directory for reports (auto-generates filename)\n"
                "# If not set, prints to stdout\n"
                "# SAA_OUTPUT_DIR=/var/saa/reports\n"
            )
            click.echo(f"  [ok] Created {env_file}")
        else:
            click.echo(f"  [ok] Exists  {env_file}")

        # Keys file - only create for user installs (not system)
        # System installs should have users create their own ~/.saa/.keys
        real_home = _get_real_user_home()
        keys_file = saa_dir / ".keys" if not system else real_home / ".saa" / ".keys"
        keys_created = False
        if system:
            # For system install, offer to create user's personal keys
            user_dir = real_home / ".saa"
            user_keys = user_dir / ".keys"
            if user_keys.exists():
                click.echo(f"  [ok] User keys at {user_keys}")
            elif click.confirm(f"  [?] Create your personal keys file at {user_keys}?", default=True):
                user_dir.mkdir(exist_ok=True)
                user_keys.write_text(
                    "# API Keys for LLM providers\n"
                    "# At least one key is required for LLM-powered analysis.\n"
                    "# Get keys from:\n"
                    "#   xAI:       https://console.x.ai/\n"
                    "#   Anthropic: https://console.anthropic.com/\n"
                    "#\n"
                    "# Uncomment and add your key(s):\n"
                    "# XAI_API_KEY=xai-your-key-here\n"
                    "# ANTHROPIC_API_KEY=sk-ant-your-key-here\n"
                )
                os.chmod(user_keys, 0o600)
                # Fix ownership when running under sudo
                sudo_uid = os.environ.get("SUDO_UID")
                sudo_gid = os.environ.get("SUDO_GID")
                if sudo_uid and sudo_gid:
                    os.chown(user_dir, int(sudo_uid), int(sudo_gid))
                    os.chown(user_keys, int(sudo_uid), int(sudo_gid))
                click.echo(f"  [ok] Created {user_keys}")
                keys_created = True
            else:
                click.echo(f"  [!!] Skipped - run 'saa init' later to create keys")
                keys_created = True  # Triggers "setup incomplete" message
        elif not keys_file.exists():
            keys_file.write_text(
                "# API Keys for LLM providers\n"
                "# At least one key is required for LLM-powered analysis.\n"
                "# Get keys from:\n"
                "#   xAI:       https://console.x.ai/\n"
                "#   Anthropic: https://console.anthropic.com/\n"
                "#\n"
                "# Uncomment and add your key(s):\n"
                "# XAI_API_KEY=xai-your-key-here\n"
                "# ANTHROPIC_API_KEY=sk-ant-your-key-here\n"
            )
            os.chmod(keys_file, 0o600)
            click.echo(f"  [ok] Created {keys_file}")
            keys_created = True
        else:
            click.echo(f"  [ok] Exists  {keys_file}")

    # 3. Check API keys (from user's keys file or env vars)
    click.echo("")
    click.echo("API keys:")
    real_home = _get_real_user_home()
    user_keys_file = real_home / ".saa" / ".keys"
    api_keys = _check_api_keys(user_keys_file if user_keys_file.exists() else None)
    any_key = False
    if api_keys["xai"]:
        click.echo("  [ok] xAI (Grok) configured")
        any_key = True
    if api_keys["anthropic"]:
        click.echo("  [ok] Anthropic (Claude) configured")
        any_key = True
    if not any_key:
        click.echo("  [!!] No API keys configured")
        if system:
            click.echo("       Run 'saa init' to create ~/.saa/.keys")
        else:
            click.echo(f"       Edit {keys_file} to add your key(s)")

    # 4. Summary
    click.echo("")
    click.echo("=" * 40)
    all_ok = chromium_ok and any_key
    if all_ok:
        click.echo("Ready! Run: saa audit https://example.com")
    else:
        click.echo("Setup incomplete:")
        if not chromium_ok:
            click.echo("  - Install Chromium: playwright install chromium")
        if not any_key:
            if system:
                click.echo("  - Run 'saa init' (as user) to create ~/.saa/.keys")
                click.echo("  - Then edit ~/.saa/.keys to add your API key(s)")
            else:
                click.echo(f"  - Edit {keys_file} to add your API key(s)")

    # 5. Note for system installs
    if system and not any_key:
        user_keys = _get_real_user_home() / ".saa" / ".keys"
        click.echo("")
        if user_keys.exists():
            click.echo(f"Add your API keys: vi {user_keys}")
        else:
            click.echo("Each user needs their own API keys:")
            click.echo("  saa init          # Creates ~/.saa/.keys")
            click.echo("  vi ~/.saa/.keys   # Add your API key(s)")


@main.command()
def check():
    """Check if a newer version is available on GitHub.

    Fetches the latest version from GitHub and compares with installed.
    Uses SSH to access the private repository.
    """
    import shutil
    import subprocess
    import tempfile

    click.echo(f"Installed: {__version__}")

    # Check remote via git
    if not shutil.which("git"):
        click.echo("Cannot check remote: git not found")
        return

    click.echo("Checking GitHub...")
    try:
        # Shallow clone to temp dir to get remote version
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["git", "clone", "--depth=1", "--quiet",
                 "https://github.com/iXanadu/saa.git", tmpdir],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                click.echo("Could not reach GitHub (check network)")
                return

            # Read version from cloned repo
            init_file = Path(tmpdir) / "src" / "saa" / "__init__.py"
            if not init_file.exists():
                click.echo("Could not find version in repo")
                return

            remote_version = None
            for line in init_file.read_text().splitlines():
                if line.startswith("__version__"):
                    remote_version = line.split("=")[1].strip().strip('"\'')
                    break

            if not remote_version:
                click.echo("Could not parse remote version")
                return

            click.echo(f"Latest:    {remote_version}")

            # Compare versions
            if remote_version == __version__:
                click.echo("\n[ok] Code is up to date!")
            else:
                click.echo(f"\n[!!] Update available: {__version__} -> {remote_version}")
                click.echo("     Run: saa update")

            # Check config and plan status
            user_dir = Path.home() / ".saa"
            system_dir = Path("/etc/saa")

            # Find which config location is in use (if any)
            active_dir = None
            if system_dir.exists():
                active_dir = system_dir
            elif user_dir.exists():
                active_dir = user_dir

            if not active_dir:
                click.echo("\n[!!] No config found")
                click.echo("     Run: saa init (user) or sudo saa init --system")
            else:
                plan_file = active_dir / "audit-plan.md"
                if not plan_file.exists():
                    click.echo(f"\n[!!] No audit plan in {active_dir}")
                    if active_dir == system_dir:
                        click.echo("     Run: sudo saa init --system --update-plan")
                    else:
                        click.echo("     Run: saa init --update-plan")
                else:
                    # Check if plan needs update
                    remote_plan = Path(tmpdir) / "src" / "saa" / "data" / "default-audit-plan.md"
                    if remote_plan.exists():
                        if remote_plan.read_text().strip() != plan_file.read_text().strip():
                            click.echo(f"\n[!!] New audit plan available for {active_dir}")
                            if active_dir == system_dir:
                                click.echo("     Run: sudo saa init --system --update-plan")
                            else:
                                click.echo("     Run: saa init --update-plan")
    except subprocess.TimeoutExpired:
        click.echo("Timeout connecting to GitHub")
    except Exception as e:
        click.echo(f"Error checking remote: {e}")


@main.command()
def update():
    """Update saa to the latest version.

    Tries 'pipx upgrade' first (PyPI), then 'pipx reinstall' (GitHub).
    Requires pipx to be installed.
    """
    import shutil
    import subprocess

    if not shutil.which("pipx"):
        click.echo("Error: pipx not found.", err=True)
        click.echo("\nInstall pipx first:")
        click.echo("  brew install pipx")
        click.echo("\nOr update manually with pip:")
        click.echo("  pip install --upgrade site-audit-agent")
        raise SystemExit(1)

    click.echo("Updating saa...")

    # Try upgrade first (works for PyPI installs)
    result = subprocess.run(
        ["pipx", "upgrade", "site-audit-agent"],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        click.echo(result.stdout)
        click.echo("Update complete! Run 'saa check' to verify.")
        raise SystemExit(0)

    # Fall back to reinstall (works for GitHub installs)
    click.echo("Trying reinstall (GitHub install)...")
    result = subprocess.run(["pipx", "reinstall", "site-audit-agent"])

    if result.returncode == 0:
        click.echo("\nUpdate complete! Run 'saa check' to verify.")
    raise SystemExit(result.returncode)


@main.command()
@click.option("--system", is_flag=True, help="Use system config at /etc/saa/")
@click.option("--list", "list_plans", is_flag=True, help="List archived plans")
@click.option("--rollback", is_flag=True, help="Rollback to previous plan version")
@click.option("--show", is_flag=True, help="Show current plan path (default)")
@click.option("--view", is_flag=True, help="Output plan content to stdout")
@click.option("--edit", is_flag=True, help="Open plan in editor ($EDITOR or vi)")
@click.option("--update", is_flag=True, help="Update to latest bundled plan")
@click.option("--bundled", is_flag=True, help="Show bundled plan (not your current)")
def plan(system: bool, list_plans: bool, rollback: bool, show: bool,
         view: bool, edit: bool, update: bool, bundled: bool):
    """Manage audit plans.

    \b
    Examples:
      saa plan                     # Show current plan location
      saa plan --view              # Output current plan content
      saa plan --edit              # Open plan in editor
      saa plan --update            # Update to latest bundled plan
      saa plan --bundled           # Show the bundled default plan
      saa plan --list              # List archived plan versions
      saa plan --rollback          # Restore previous plan version
    """
    import os
    import subprocess

    saa_dir = _get_saa_dir(system)
    if system and os.geteuid() != 0:
        click.echo("Error: --system requires root.", err=True)
        raise SystemExit(1)

    plan_file = saa_dir / "audit-plan.md"
    plans_dir = saa_dir / "plans"

    # --bundled: show the bundled plan content
    if bundled:
        click.echo(_get_bundled_plan())
        return

    # --view: output current plan content
    if view:
        if plan_file.exists():
            click.echo(plan_file.read_text())
        else:
            click.echo("No plan configured. Run: saa init", err=True)
            raise SystemExit(1)
        return

    # --edit: open plan in editor
    if edit:
        if not plan_file.exists():
            click.echo("No plan configured. Run: saa init", err=True)
            raise SystemExit(1)
        editor = os.environ.get("EDITOR", "vi")
        subprocess.run([editor, str(plan_file)])
        return

    # --update: update to latest bundled plan
    if update:
        if plan_file.exists():
            # Check if already up to date
            if not _plan_needs_update(saa_dir):
                click.echo("Plan is already up to date.")
                return
            # Archive current plan
            archive_path = _archive_plan(saa_dir, plan_file)
            click.echo(f"Archived current: {archive_path.name}")

        # Write new plan
        plan_file.write_text(_get_bundled_plan())
        click.echo(f"Updated: {plan_file}")
        return

    # Default (--show or no flags): show current plan info
    if show or (not list_plans and not rollback):
        if plan_file.exists():
            click.echo(f"Current plan: {plan_file}")
            if _plan_needs_update(saa_dir):
                click.echo("[!!] Newer version available: saa plan --update")
        else:
            click.echo("No plan configured. Run: saa init")
        return

    if list_plans:
        if not plans_dir.exists() or not list(plans_dir.glob("*.md")):
            click.echo("No archived plans found.")
            return

        click.echo(f"Archived plans in {plans_dir}:\n")
        archives = sorted(plans_dir.glob("*.md"), reverse=True)
        for i, archive in enumerate(archives):
            click.echo(f"  {i+1}. {archive.name}")
        click.echo(f"\nTo rollback: saa plan --rollback")
        return

    if rollback:
        if not plans_dir.exists():
            click.echo("No archived plans to rollback to.")
            raise SystemExit(1)

        archives = sorted(plans_dir.glob("*.md"), reverse=True)
        if not archives:
            click.echo("No archived plans to rollback to.")
            raise SystemExit(1)

        # Get most recent archive
        latest_archive = archives[0]
        click.echo(f"Rolling back to: {latest_archive.name}")

        # Archive current plan first (so we can undo the rollback)
        if plan_file.exists():
            archive_path = _archive_plan(saa_dir, plan_file)
            click.echo(f"Archived current: {archive_path.name}")

        # Restore from archive
        plan_file.write_text(latest_archive.read_text())
        click.echo(f"Restored: {plan_file}")

        # Remove the archive we just restored from
        latest_archive.unlink()
        click.echo("Done. Run 'saa plan --list' to see remaining archives.")


if __name__ == "__main__":
    main()
