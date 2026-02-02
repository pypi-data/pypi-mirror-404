"""
HuggingFace authentication utilities for PIP-BOY LLM.
Handles login, token management, and model access verification.
"""

from huggingface_hub import HfApi, login, whoami
from huggingface_hub.utils import HfHubHTTPError

# Model IDs mapping
MODEL_HF_IDS = {
    "gemma-1b": "google/gemma-3-1b-it",
    "llama-1b": "meta-llama/Llama-3.2-1B-Instruct",
    "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.3",
}

# License agreement URLs
MODEL_LICENSE_URLS = {
    "gemma-1b": "https://huggingface.co/google/gemma-3-1b-it",
    "llama-1b": "https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct",
    "mistral-7b": None,  # Mistral doesn't require agreement
}


def is_logged_in() -> bool:
    """Check if user is logged in to HuggingFace."""
    try:
        whoami()
        return True
    except Exception:
        return False


def get_current_user() -> dict | None:
    """
    Get current logged in user info.
    Returns dict with 'name', 'fullname', 'email' or None if not logged in.
    """
    try:
        return whoami()
    except Exception:
        return None


def check_model_access(model_id: str) -> tuple[bool, str]:
    """
    Check if user has access to a model.

    Args:
        model_id: Short model ID (e.g., "gemma-1b") or full HF ID

    Returns:
        (has_access, message) tuple
    """
    # Map short ID to full HF ID
    hf_id = MODEL_HF_IDS.get(model_id, model_id)

    try:
        api = HfApi()
        api.model_info(hf_id)
        return True, "Access granted"
    except HfHubHTTPError as e:
        if e.response.status_code == 401:
            return False, "Not logged in to HuggingFace"
        elif e.response.status_code == 403:
            license_url = MODEL_LICENSE_URLS.get(model_id)
            if license_url:
                return False, f"License agreement required: {license_url}"
            return False, "Access denied - model may require special permissions"
        else:
            return False, f"Error checking access: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def interactive_login() -> bool:
    """
    Guide user through HuggingFace login process.
    Returns True if login successful.
    """
    print("\n  [HuggingFace Login Required]")
    print("  Some models require authentication to download.")
    print()
    print("  Steps:")
    print("    1. Go to: https://huggingface.co/settings/tokens")
    print("    2. Create a token with 'read' access")
    print("    3. Enter the token below")
    print()

    try:
        token = input("  Enter HuggingFace token (or press Enter to skip): ").strip()
        if not token:
            print("  [Skipped] Login cancelled")
            return False

        login(token=token, add_to_git_credential=False)

        user = get_current_user()
        if user:
            print(f"  [OK] Logged in as: {user.get('name', 'Unknown')}")
            return True
        else:
            print("  [!] Login failed")
            return False

    except KeyboardInterrupt:
        print("\n  [Cancelled]")
        return False
    except Exception as e:
        print(f"  [!] Login error: {e}")
        return False


def ensure_model_access(model_id: str, quiet: bool = False) -> bool:
    """
    Ensure user has access to a model, prompting for login if needed.

    Args:
        model_id: Short model ID (e.g., "gemma-1b")
        quiet: If True, don't print status messages

    Returns:
        True if access granted, False otherwise
    """
    hf_id = MODEL_HF_IDS.get(model_id, model_id)

    # Check if model requires gated access
    license_url = MODEL_LICENSE_URLS.get(model_id)

    # First, check current access
    has_access, message = check_model_access(model_id)

    if has_access:
        if not quiet:
            print(f"  [OK] Model access verified: {hf_id}")
        return True

    # Not logged in - prompt for login
    if "Not logged in" in message:
        if not quiet:
            print(f"\n  [!] {message}")

        if interactive_login():
            # Re-check after login
            has_access, message = check_model_access(model_id)
            if has_access:
                return True

    # Check if license agreement needed
    if "License agreement" in message:
        if not quiet:
            print(f"\n  [!] {message}")
            print("  Please accept the license agreement at the URL above,")
            print("  then run this command again.")
        return False

    if not quiet:
        print(f"\n  [!] Cannot access model: {message}")

    return False


def get_model_hf_id(model_id: str) -> str:
    """Get full HuggingFace model ID from short ID."""
    return MODEL_HF_IDS.get(model_id, model_id)
