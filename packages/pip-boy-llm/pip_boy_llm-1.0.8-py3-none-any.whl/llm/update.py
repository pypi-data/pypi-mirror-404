"""
PIP-BOY LLM Update Checker
Entry point: pip-boy-update

Checks PyPI for newer versions and offers to upgrade.
"""

import subprocess
import sys

import requests
from packaging import version

from llm import __version__, __package_name__

# Colors
GREEN = "\033[92m"
LIME = "\033[38;5;118m"
GRAY = "\033[90m"
RESET = "\033[0m"

PYPI_URL = f"https://pypi.org/pypi/{__package_name__}/json"


def get_latest_version() -> str | None:
    """Fetch latest version from PyPI."""
    try:
        response = requests.get(PYPI_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data["info"]["version"]
        elif response.status_code == 404:
            return None  # Package not published yet
        else:
            return None
    except Exception:
        return None


def compare_versions(current: str, latest: str) -> int:
    """
    Compare version strings.
    Returns:
        -1 if current < latest (update available)
         0 if current == latest
         1 if current > latest (dev version)
    """
    try:
        v_current = version.parse(current)
        v_latest = version.parse(latest)

        if v_current < v_latest:
            return -1
        elif v_current > v_latest:
            return 1
        else:
            return 0
    except Exception:
        # Fallback to string comparison
        if current == latest:
            return 0
        return -1


def run_upgrade() -> bool:
    """Run pip upgrade command."""
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", __package_name__]
        print(f"  {GRAY}Running: {' '.join(cmd)}{RESET}")
        print()

        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"  {GREEN}[!]{RESET} Upgrade failed: {e}")
        return False


def banner():
    """Show update checker banner."""
    print(f"""{GREEN}
  ╔═══════════════════════════════════════════════════════════╗
  ║  {LIME}PIP-BOY LLM{GREEN} - Update Checker                            ║
  ╚═══════════════════════════════════════════════════════════╝
{RESET}""")


def main():
    """Check for updates and optionally upgrade."""
    banner()

    print(f"  Current version: {LIME}{__version__}{RESET}")
    print(f"  Checking PyPI...", end=" ", flush=True)

    latest = get_latest_version()

    if latest is None:
        print(f"{GRAY}[--]{RESET} Package not found on PyPI")
        print()
        print(f"  {GRAY}This may be a development version or the package")
        print(f"  hasn't been published yet.{RESET}")
        print()
        return 0

    print(f"{GREEN}[OK]{RESET} Latest: {LIME}{latest}{RESET}")
    print()

    comparison = compare_versions(__version__, latest)

    if comparison == 0:
        print(f"  {GREEN}[OK]{RESET} You're running the latest version!")
        print()
        return 0

    elif comparison > 0:
        print(f"  {LIME}[*]{RESET} You're running a development version")
        print(f"  {GRAY}(newer than PyPI release){RESET}")
        print()
        return 0

    else:
        print(f"  {LIME}[*]{RESET} Update available: {__version__} -> {latest}")
        print()

        try:
            response = input(f"  {LIME}>{RESET} Upgrade now? [Y/n]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return 0

        if response in ("", "y", "yes"):
            print()
            if run_upgrade():
                print()
                print(f"  {GREEN}[OK]{RESET} Upgrade complete!")
                print(f"  {GRAY}Restart pip-boy-llm to use the new version.{RESET}")
            else:
                print()
                print(f"  {GREEN}[!]{RESET} Upgrade failed. Try manually:")
                print(f"  {GRAY}pip install --upgrade {__package_name__}{RESET}")
        else:
            print(f"  {GRAY}Upgrade skipped.{RESET}")

        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
