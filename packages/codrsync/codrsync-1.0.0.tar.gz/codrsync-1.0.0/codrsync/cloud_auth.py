"""
codrsync cloud authentication — Device Flow

Implements the CLI side of the device flow:
1. POST /api/auth/device-code → get user_code + device_code
2. Open browser to verification_uri with user_code
3. Poll /api/auth/device-token until authorized or expired
4. Store credentials in ~/.codrsync/credentials.json

Usage:
    codrsync auth --cloud
"""

import json
import time
import webbrowser
from pathlib import Path
from typing import Optional

import requests
from rich.console import Console
from rich.panel import Panel

from codrsync.i18n import t


console = Console()

CODRSYNC_API_URL = "https://codrsync.dev"
CREDENTIALS_FILE = Path.home() / ".codrsync" / "credentials.json"


def cloud_login(api_url: Optional[str] = None) -> bool:
    """Execute device flow login.

    Returns True if login succeeded.
    """
    base_url = api_url or CODRSYNC_API_URL

    # Step 1: Request device code
    console.print(t("cloud_auth.requesting_code"))

    try:
        resp = requests.post(
            f"{base_url}/api/auth/device-code",
            json={"client_info": {"cli_version": "1.0.0"}},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        console.print(f"{t('common.error')} {t('cloud_auth.request_failed', error=str(e))}")
        return False

    user_code = data["user_code"]
    device_code = data["device_code"]
    verification_uri = data["verification_uri"].strip()
    expires_in = data["expires_in"]
    interval = data["interval"]

    # Step 2: Show code and open browser
    console.print(Panel(
        f"{t('cloud_auth.enter_code')}\n\n"
        f"  [bold cyan]{user_code}[/bold cyan]\n\n"
        f"{t('cloud_auth.open_browser', url=verification_uri)}",
        title=t("cloud_auth.device_flow_title"),
        border_style="cyan",
    ))

    webbrowser.open(f"{verification_uri}?code={user_code}")

    # Step 3: Poll for authorization
    console.print(t("cloud_auth.waiting"))

    deadline = time.time() + expires_in
    while time.time() < deadline:
        time.sleep(interval)

        try:
            resp = requests.post(
                f"{base_url}/api/auth/device-token",
                json={"device_code": device_code},
                timeout=10,
            )

            if resp.status_code == 200:
                # Authorized!
                result = resp.json()
                _save_credentials(result)
                console.print(Panel(
                    f"{t('common.success')} {t('cloud_auth.logged_in', name=result.get('display_name', 'User'))}\n"
                    f"{t('cloud_auth.tier', tier=result.get('tier', 'free'))}",
                    title=t("cloud_auth.success_title"),
                    border_style="green",
                ))
                return True

            elif resp.status_code == 428:
                # authorization_pending — keep polling
                console.print(".", end="")
                continue
            elif resp.status_code == 410:
                console.print(f"\n{t('common.error')} {t('cloud_auth.expired')}")
                return False
            elif resp.status_code == 403:
                console.print(f"\n{t('common.error')} {t('cloud_auth.denied')}")
                return False
            else:
                console.print(f"\n{t('common.error')} HTTP {resp.status_code}")
                return False

        except requests.RequestException:
            # Network error — retry
            continue

    console.print(f"\n{t('common.error')} {t('cloud_auth.timeout')}")
    return False


def cloud_logout() -> None:
    """Remove stored credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
    console.print(t("cloud_auth.logged_out"))


def get_cloud_credentials() -> Optional[dict]:
    """Load stored cloud credentials, or None."""
    if not CREDENTIALS_FILE.exists():
        return None

    try:
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        if data.get("access_token"):
            return data
    except (json.JSONDecodeError, KeyError):
        pass

    return None


def _save_credentials(result: dict) -> None:
    """Store credentials to ~/.codrsync/credentials.json."""
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(
        json.dumps({
            "access_token": result["access_token"],
            "user_id": result["user_id"],
            "display_name": result.get("display_name", ""),
            "tier": result.get("tier", "free"),
        }, indent=2),
        encoding="utf-8",
    )
    # Restrict permissions (owner only)
    CREDENTIALS_FILE.chmod(0o600)
