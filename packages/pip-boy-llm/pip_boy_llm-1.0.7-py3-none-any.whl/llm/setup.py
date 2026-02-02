"""
PIP-BOY LLM Setup Wizard
Entry point: pip-boy-setup

Checks dependencies, HuggingFace login, and model access.
"""

import sys
import os

# Colors
GREEN = "\033[92m"
LIME = "\033[38;5;118m"
GRAY = "\033[90m"
RESET = "\033[0m"


def check_torch() -> bool:
    """Check if PyTorch is installed and working."""
    print(f"  Checking PyTorch...", end=" ", flush=True)
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            device = torch.cuda.get_device_name(0)
            print(f"{GREEN}[OK]{RESET} CUDA available ({device})")
        else:
            print(f"{GREEN}[OK]{RESET} CPU mode (no CUDA)")
        return True
    except ImportError:
        print(f"{GREEN}[!]{RESET} Not installed")
        return False
    except Exception as e:
        print(f"{GREEN}[!]{RESET} Error: {e}")
        return False


def check_transformers() -> bool:
    """Check if transformers is installed."""
    print(f"  Checking Transformers...", end=" ", flush=True)
    try:
        import transformers
        print(f"{GREEN}[OK]{RESET} v{transformers.__version__}")
        return True
    except ImportError:
        print(f"{GREEN}[!]{RESET} Not installed")
        return False


def check_bitsandbytes() -> bool:
    """Check if bitsandbytes is installed (optional, for quantization)."""
    print(f"  Checking bitsandbytes...", end=" ", flush=True)
    try:
        import bitsandbytes
        print(f"{GREEN}[OK]{RESET} v{bitsandbytes.__version__}")
        return True
    except ImportError:
        print(f"{GRAY}[--]{RESET} Not installed (optional, for 4-bit quantization)")
        return False
    except Exception as e:
        print(f"{GRAY}[--]{RESET} Error loading: {e}")
        return False


def check_huggingface_login() -> bool:
    """Check and setup HuggingFace login."""
    print(f"  Checking HuggingFace login...", end=" ", flush=True)
    try:
        from llm.hf_auth import is_logged_in, get_current_user, interactive_login

        if is_logged_in():
            user = get_current_user()
            name = user.get("name", "Unknown") if user else "Unknown"
            print(f"{GREEN}[OK]{RESET} Logged in as: {name}")
            return True
        else:
            print(f"{GRAY}[--]{RESET} Not logged in")
            print()
            response = input(f"  {LIME}>{RESET} Login to HuggingFace now? [y/N]: ").strip().lower()
            if response in ("y", "yes"):
                return interactive_login()
            return False

    except ImportError as e:
        print(f"{GREEN}[!]{RESET} Module error: {e}")
        return False


def check_model_access() -> dict:
    """Check access to all models."""
    from llm.hf_auth import MODEL_HF_IDS, check_model_access as check_access, MODEL_LICENSE_URLS

    results = {}
    print()
    print(f"  {LIME}Checking model access:{RESET}")

    for short_id, hf_id in MODEL_HF_IDS.items():
        print(f"    {short_id} ({hf_id})...", end=" ", flush=True)
        has_access, message = check_access(short_id)

        if has_access:
            print(f"{GREEN}[OK]{RESET}")
            results[short_id] = True
        else:
            license_url = MODEL_LICENSE_URLS.get(short_id)
            if license_url and "License" in message:
                print(f"{GRAY}[--]{RESET} Needs license agreement")
            else:
                print(f"{GRAY}[--]{RESET} {message}")
            results[short_id] = False

    return results


def create_config_dir() -> bool:
    """Create config directory if needed."""
    print(f"  Checking config directory...", end=" ", flush=True)
    try:
        from llm.config import ensure_config_dir, CONFIG_DIR
        ensure_config_dir()
        print(f"{GREEN}[OK]{RESET} {CONFIG_DIR}")
        return True
    except Exception as e:
        print(f"{GREEN}[!]{RESET} Error: {e}")
        return False


def banner():
    """Show setup wizard banner."""
    print(f"""{GREEN}
  ╔═══════════════════════════════════════════════════════════╗
  ║  {LIME}PIP-BOY LLM{GREEN} - Setup Wizard                              ║
  ╚═══════════════════════════════════════════════════════════╝
{RESET}""")


def main():
    """Run the setup wizard."""
    banner()

    print(f"  {LIME}Step 1: Checking Dependencies{RESET}")
    print()

    torch_ok = check_torch()
    transformers_ok = check_transformers()
    bnb_ok = check_bitsandbytes()

    if not torch_ok or not transformers_ok:
        print()
        print(f"  {GREEN}[!]{RESET} Missing required dependencies.")
        print(f"  {GRAY}Run: pip install pip-boy-llm[all]{RESET}")
        print()

    print()
    print(f"  {LIME}Step 2: HuggingFace Authentication{RESET}")
    print()

    hf_ok = check_huggingface_login()

    if hf_ok:
        model_access = check_model_access()
        needs_license = [k for k, v in model_access.items() if not v]

        if needs_license:
            print()
            print(f"  {GRAY}Some models require license agreement:{RESET}")
            from llm.hf_auth import MODEL_LICENSE_URLS
            for model_id in needs_license:
                url = MODEL_LICENSE_URLS.get(model_id)
                if url:
                    print(f"    - {model_id}: {url}")

    print()
    print(f"  {LIME}Step 3: Configuration{RESET}")
    print()

    create_config_dir()

    print()
    print(f"  {GREEN}═══════════════════════════════════════════════════════════{RESET}")
    print(f"  {LIME}Setup complete!{RESET}")
    print()
    print(f"  {GRAY}To start PIP-BOY LLM:{RESET}")
    print(f"    pip-boy-llm")
    print()
    print(f"  {GRAY}To check for updates:{RESET}")
    print(f"    pip-boy-update")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
