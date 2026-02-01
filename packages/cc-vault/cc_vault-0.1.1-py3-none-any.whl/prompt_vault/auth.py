"""Device flow authentication for Prompt Vault CLI."""

import time
import webbrowser
import requests
from typing import Optional

from prompt_vault.config import Config, DEFAULT_API_URL

# Bypass proxy for localhost
NO_PROXY = {"http": None, "https": None}


def device_flow_auth(api_url: Optional[str] = None) -> bool:
    """
    Authenticate using device flow.

    1. Request device code from server
    2. Open browser for user to approve
    3. Poll for approval
    4. Save tokens to config
    """
    config = Config.load()
    base_url = api_url or config.api_base_url or DEFAULT_API_URL

    print("Starting authentication...")
    print()

    # Step 1: Request device code
    # Bypass proxy for localhost
    proxies = NO_PROXY if "localhost" in base_url or "127.0.0.1" in base_url else None

    try:
        resp = requests.post(f"{base_url}/api/device/start", timeout=10, proxies=proxies)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"Failed to connect to server: {e}")
        return False

    device_code = data["device_code"]
    user_code = data["user_code"]
    verification_url = data["verification_url"]
    expires_in = data.get("expires_in", 600)

    # Step 2: Show user code and open browser
    print(f"Your verification code: {user_code}")
    print()
    print(f"Opening browser to: {verification_url}")
    print()
    print("If the browser doesn't open, visit the URL manually.")
    print()

    try:
        webbrowser.open(verification_url)
    except Exception:
        pass  # Browser open failed, user can open manually

    # Step 3: Poll for approval
    print("Waiting for approval...")

    poll_interval = 2
    max_attempts = expires_in // poll_interval

    for attempt in range(max_attempts):
        time.sleep(poll_interval)

        try:
            resp = requests.post(
                f"{base_url}/api/device/poll",
                json={"device_code": device_code},
                timeout=10,
                proxies=proxies,
            )

            if resp.status_code == 200:
                # Success!
                data = resp.json()
                config.user_id = data["user_id"]
                config.refresh_token = data["refresh_token"]
                config.api_base_url = base_url
                config.save()

                print()
                print(f"Authenticated as: {config.user_id}")
                print("You can now use 'cv sync' or 'cv install' for auto-sync.")
                return True

            elif resp.status_code == 428:
                # Still pending
                if attempt % 5 == 0:
                    print(".", end="", flush=True)
                continue

            elif resp.status_code == 410:
                # Expired
                print()
                print("Verification code expired. Please try again.")
                return False

            else:
                print()
                print(f"Unexpected response: {resp.status_code}")
                return False

        except requests.RequestException:
            continue

    print()
    print("Timeout waiting for approval. Please try again.")
    return False


def get_access_token() -> Optional[str]:
    """Get a valid access token, refreshing if needed."""
    config = Config.load()

    if not config.is_authenticated:
        return None

    # Bypass proxy for localhost
    proxies = NO_PROXY if "localhost" in config.api_base_url or "127.0.0.1" in config.api_base_url else None

    try:
        resp = requests.post(
            f"{config.api_base_url}/api/token/refresh",
            json={"refresh_token": config.refresh_token},
            timeout=10,
            proxies=proxies,
        )

        if resp.status_code == 200:
            data = resp.json()
            return data["access_token"]
        else:
            return None

    except requests.RequestException:
        return None
