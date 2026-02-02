"""
PIP-BOY LLM - Vault-Tec Local AI Terminal
"""

import subprocess
import sys
import time
import requests
import os
import glob as globmod
from llm.file_expander import expand_file_references
from llm.commands import handle_command, CommandContext
from llm.config import load_config, get_config_value, get_theme_colors
from llm.history import append_to_history
from llm.hf_auth import is_logged_in, ensure_model_access, MODEL_LICENSE_URLS

# Try to import readline for tab completion (optional)
try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    try:
        import pyreadline3 as readline
        READLINE_AVAILABLE = True
    except ImportError:
        READLINE_AVAILABLE = False

API = "http://127.0.0.1:5000"
server_process = None
selected_model = "mistral-7b"

# Available models
MODELS = {
    "1": {"id": "gemma-1b", "name": "Gemma 3 1B", "desc": "Fast (HF login)", "mode": "FP16"},
    "2": {"id": "llama-1b", "name": "Llama 3.2 1B", "desc": "Fast (HF login)", "mode": "FP16"},
    "3": {"id": "mistral-7b", "name": "Mistral 7B", "desc": "Best quality", "mode": "4-BIT"},
    "4": {"id": "deepseek-1.5b", "name": "DeepSeek R1 1.5B", "desc": "Reasoning", "mode": "FP16"},
}

# Colors - Dynamic theme (loaded from config)
WHITE = "\033[97m"
GRAY = "\033[90m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"
BLACK_BG = "\033[40m"

# Theme colors (set at startup)
GREEN = "\033[92m"
DARKGREEN = "\033[32m"
LIME = "\033[38;5;118m"


def load_theme_colors():
    """Load theme colors from config."""
    global GREEN, DARKGREEN, LIME
    theme = get_theme_colors()
    GREEN = theme["primary"]
    DARKGREEN = theme["secondary"]
    LIME = theme["accent"]


def get_user_name():
    """Get user name from config."""
    return get_config_value("user_name", "VAULT DWELLER")

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_short_path(path, max_len=50):
    """Shorten path for display, keeping the end visible."""
    if len(path) <= max_len:
        return path
    return "..." + path[-(max_len - 3):]

class FileCompleter:
    """Tab completion for @filepath references."""

    def __init__(self):
        self.matches = []

    def complete(self, text, state):
        """Readline completion function."""
        if state == 0:
            # Get the full line and cursor position
            line = readline.get_line_buffer()
            cursor = readline.get_endidx()

            # Find the @ reference being completed
            self.matches = self._get_completions(line, cursor)

        if state < len(self.matches):
            return self.matches[state]
        return None

    def _get_completions(self, line, cursor):
        """Get file completions for @ references."""
        # Find the start of the current @ reference
        at_pos = line.rfind('@', 0, cursor)
        if at_pos == -1:
            return []

        # Skip if it's an escaped @@
        if at_pos > 0 and line[at_pos - 1] == '@':
            return []

        # Get the partial path after @
        partial = line[at_pos + 1:cursor]

        # Handle quoted paths
        if partial.startswith('"'):
            partial = partial[1:]
            prefix = '@"'
            suffix = '"'
        else:
            prefix = '@'
            suffix = ''

        # Get matching files
        try:
            if partial:
                pattern = partial + '*'
            else:
                pattern = '*'

            matches = []
            for path in globmod.glob(pattern):
                if os.path.isdir(path):
                    path += os.sep
                # Add quotes if path has spaces
                if ' ' in path and not suffix:
                    matches.append(f'@"{path}"')
                else:
                    matches.append(f'{prefix}{path}{suffix}')

            return sorted(matches)
        except Exception:
            return []

def setup_readline():
    """Configure readline for tab completion."""
    if not READLINE_AVAILABLE:
        return

    completer = FileCompleter()
    readline.set_completer(completer.complete)
    readline.set_completer_delims(' \t\n;')

    # Different binding for different platforms
    if 'libedit' in readline.__doc__ if readline.__doc__ else False:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

def show_hf_login_warning():
    """Show warning if not logged in to HuggingFace."""
    if not is_logged_in():
        print(f"  {GREEN}[!]{RESET} {GRAY}Not logged in to HuggingFace{RESET}")
        print(f"  {GRAY}    Some models require login. Run: pip-boy-setup{RESET}")
        print()


def model_menu():
    """Display model selection menu"""
    global selected_model

    # Show HF login warning
    show_hf_login_warning()

    print(f"{GREEN}")
    print("  ╔═══════════════════════════════════════════════╗")
    print(f"  ║  {LIME}>>>{GREEN} SELECT AI MODULE {LIME}<<<{GREEN}                      ║")
    print("  ╠═══════════════════════════════════════════════╣")
    for key, model in MODELS.items():
        print(f"  ║  {LIME}[{key}]{GREEN} {model['name']:<14} {GRAY}{model['desc']:<18}{GREEN} ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print(f"{RESET}")

    while True:
        choice = input(f"  {LIME}>{RESET} Select module {GRAY}[1-4]{RESET}: ").strip()
        if choice in MODELS:
            selected_model = MODELS[choice]["id"]

            # Check model access before proceeding
            if not verify_model_access(selected_model):
                continue

            print(f"  {GREEN}[OK]{RESET} {LIME}{MODELS[choice]['name']} loaded{RESET}")
            print()
            return
        elif choice == "":
            # Default to first option
            selected_model = MODELS["1"]["id"]

            # Check model access before proceeding
            if not verify_model_access(selected_model):
                continue

            print(f"  {GREEN}[OK]{RESET} {LIME}{MODELS['1']['name']} loaded (default){RESET}")
            print()
            return
        else:
            print(f"  {GREEN}[!]{RESET} {GRAY}Invalid selection{RESET}")


def verify_model_access(model_id: str) -> bool:
    """
    Verify user has access to the selected model.
    Returns True if access granted, False otherwise.
    """
    # Check if model requires gated access
    license_url = MODEL_LICENSE_URLS.get(model_id)

    if license_url is None:
        # Model doesn't require special access (e.g., Mistral)
        return True

    # Model requires HF access - check/prompt
    if not ensure_model_access(model_id, quiet=False):
        print(f"  {GREEN}[!]{RESET} {GRAY}Select a different model or run pip-boy-setup{RESET}")
        print()
        return False

    return True

def banner():
    # Get model display name and mode
    model_name = "UNKNOWN"
    model_mode = "FP16"
    for m in MODELS.values():
        if m["id"] == selected_model:
            model_name = m["name"].upper()
            model_mode = m.get("mode", "FP16")
            break

    print(f"""{GREEN}
    ██████╗ ██╗██████╗       ██████╗  ██████╗ ██╗   ██╗    ██╗     ██╗     ███╗   ███╗
    ██╔══██╗██║██╔══██╗      ██╔══██╗██╔═══██╗╚██╗ ██╔╝    ██║     ██║     ████╗ ████║
    ██████╔╝██║██████╔╝█████╗██████╔╝██║   ██║ ╚████╔╝     ██║     ██║     ██╔████╔██║
    ██╔═══╝ ██║██╔═══╝ ╚════╝██╔══██╗██║   ██║  ╚██╔╝      ██║     ██║     ██║╚██╔╝██║
    ██║     ██║██║           ██████╔╝╚██████╔╝   ██║       ███████╗███████╗██║ ╚═╝ ██║
    ╚═╝     ╚═╝╚═╝           ╚═════╝  ╚═════╝    ╚═╝       ╚══════╝╚══════╝╚═╝     ╚═╝
{RESET}""")
    print(f"{DARKGREEN}  ╔═══════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{DARKGREEN}  ║  {LIME}VAULT-TEC APPROVED  {DARKGREEN}│  {GREEN}{model_name}  {DARKGREEN}│  {LIME}{model_mode}  {DARKGREEN}│  {GREEN}LOCAL TERMINAL{DARKGREEN}  ║{RESET}")
    print(f"{DARKGREEN}  ╚═══════════════════════════════════════════════════════════════════════════════════════════╝{RESET}")
    print(f"{GRAY}            [/help] commands  •  [/exit] logout  •  [/clear] wipe  •  [@file] include{RESET}")
    # Show current working directory
    cwd = get_short_path(os.getcwd())
    print(f"{GRAY}  DIR: {LIME}{cwd}{RESET}")
    print()

def check_server():
    try:
        r = requests.get(f"{API}/health", timeout=2)
        return r.status_code == 200
    except:
        return False

def start_server():
    global server_process
    server_path = os.path.join(os.path.dirname(__file__), "server.py")

    # Pass selected model via environment
    env = os.environ.copy()
    env["LLM_MODEL"] = selected_model

    if os.name == 'nt':
        # CREATE_NEW_PROCESS_GROUP prevents Ctrl+C from killing the server
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        server_process = subprocess.Popen(
            [sys.executable, server_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=CREATE_NEW_PROCESS_GROUP,
            env=env
        )
    else:
        # On Unix, start in new process group
        server_process = subprocess.Popen(
            [sys.executable, server_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=env
        )

def stop_server():
    global server_process
    if server_process:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()

def wait_for_server(timeout=120):
    start = time.time()
    spinner = ['◢', '◣', '◤', '◥']
    i = 0

    while time.time() - start < timeout:
        if check_server():
            print(f"\r  {GREEN}[OK]{RESET} {LIME}AI MODULE ONLINE{RESET}                         ")
            return True

        elapsed = int(time.time() - start)
        print(f"\r  {GREEN}{spinner[i % len(spinner)]}{RESET} {DARKGREEN}Initializing system... {elapsed}s{RESET}  ", end="", flush=True)
        i += 1
        time.sleep(0.2)

    print(f"\r  {GREEN}[!!]{RESET} {DARKGREEN}INITIALIZATION FAILED{RESET}              ")
    return False

def chat_with_spinner(message):
    """Send message to API with animated spinner - Ctrl+C to cancel"""
    import threading

    result = {"response": None, "elapsed": 0, "done": False, "cancelled": False, "history": 0}

    def api_call():
        try:
            start = time.time()
            r = requests.post(
                f"{API}/chat",
                json={"message": message},
                timeout=300
            )
            result["elapsed"] = time.time() - start

            if r.status_code == 200:
                data = r.json()
                result["response"] = data.get("response", "")
                result["history"] = data.get("history_length", 0)
            else:
                result["response"] = f"Error: {r.status_code}"
        except requests.exceptions.ConnectionError:
            result["response"] = "CONNECTION LOST"
        except Exception as e:
            if not result["cancelled"]:
                result["response"] = f"SYSTEM ERROR: {e}"
        finally:
            result["done"] = True

    # Start API call in background
    thread = threading.Thread(target=api_call, daemon=True)
    thread.start()

    # Spinner animation - Fallout terminal style
    pip_frames = [
        "  [■□□□□□□□□□]",
        "  [■■□□□□□□□□]",
        "  [■■■□□□□□□□]",
        "  [■■■■□□□□□□]",
        "  [■■■■■□□□□□]",
        "  [■■■■■■□□□□]",
        "  [■■■■■■■□□□]",
        "  [■■■■■■■■□□]",
        "  [■■■■■■■■■□]",
        "  [■■■■■■■■■■]",
        "  [□■■■■■■■■■]",
        "  [□□■■■■■■■■]",
        "  [□□□■■■■■■■]",
        "  [□□□□■■■■■■]",
        "  [□□□□□■■■■■]",
        "  [□□□□□□■■■■]",
        "  [□□□□□□□■■■]",
        "  [□□□□□□□□■■]",
        "  [□□□□□□□□□■]",
        "  [□□□□□□□□□□]",
    ]

    i = 0
    start_time = time.time()

    try:
        while not result["done"]:
            elapsed = time.time() - start_time
            frame = pip_frames[i % len(pip_frames)]
            print(f"\r{GREEN}{frame} {GRAY}{elapsed:.1f}s {DIM}(Ctrl+C abort){RESET}  ", end="", flush=True)
            i += 1
            time.sleep(0.1)
    except KeyboardInterrupt:
        result["cancelled"] = True
        result["done"] = True
        print("\r" + " " * 50 + "\r", end="")
        print(f"  {GREEN}[--]{RESET} {GRAY}Operation aborted{RESET}")
        return None, 0, 0

    # Clear spinner line
    print("\r" + " " * 50 + "\r", end="")

    thread.join(timeout=0.5)
    return result["response"], result["elapsed"], result["history"]

def main():
    global selected_model

    # Load theme colors from config
    load_theme_colors()

    # Setup tab completion for @ files
    setup_readline()

    clear()

    # Check if server already running
    if check_server():
        # Get current model from running server
        try:
            r = requests.get(f"{API}/health", timeout=2)
            if r.status_code == 200:
                data = r.json()
                selected_model = data.get("model", "mistral-7b")
        except:
            pass
        banner()
        print(f"  {GREEN}[OK]{RESET} {LIME}System already online{RESET}")
    else:
        # Show model selection menu
        model_menu()
        banner()

        print(f"  {DARKGREEN}>>>{RESET} {GRAY}Booting AI subsystem...{RESET}")
        start_server()

        if not wait_for_server():
            print(f"  {GREEN}[!!]{RESET} {DARKGREEN}BOOT FAILURE. Manual override required:{RESET}")
            print(f"    {GRAY}python -m llm.server{RESET}")
            stop_server()
            sys.exit(1)

    print()

    # Get model display name for context
    model_name = "Unknown"
    for m in MODELS.values():
        if m["id"] == selected_model:
            model_name = m["name"]
            break

    # Create command context
    cmd_context = CommandContext(API, model_name)

    # Chat loop
    try:
        while True:
            try:
                user_name = get_user_name()
                user_input = input(f"{WHITE}>{RESET} {LIME}{user_name}{RESET}{DARKGREEN}:{RESET} ").strip()

                if not user_input:
                    continue

                # Check for commands (including shortcuts)
                if user_input.startswith("/") or user_input.lower() in ("exit", "quit", "q", "clear"):
                    result = handle_command(user_input, cmd_context)

                    if result == "exit":
                        break
                    elif result == "cleared":
                        # Redraw banner after clear
                        banner()
                        print(f"  {GREEN}[OK]{RESET} {GRAY}Memory wiped{RESET}\n")
                        continue
                    elif result is not None:
                        # Command was handled
                        continue

                # Expand file references
                expanded_input, file_errors = expand_file_references(user_input)

                # Show any file errors
                for error in file_errors:
                    print(f"  {GREEN}[!]{RESET} {GRAY}{error}{RESET}")

                # Skip if no valid content
                if not expanded_input.strip():
                    continue

                # Show expansion feedback
                if expanded_input != user_input:
                    print(f"  {GREEN}[+]{RESET} {GRAY}File(s) loaded{RESET}")

                # Send to LLM with spinner
                response, elapsed, history_len = chat_with_spinner(expanded_input)

                # Print response (skip if cancelled)
                if response is not None:
                    if response == "CONNECTION LOST":
                        print(f"  {GREEN}[!!]{RESET} {DARKGREEN}CONNECTION LOST - Rebooting...{RESET}")
                        stop_server()
                        start_server()
                        if wait_for_server():
                            print(f"{GRAY}  Retry your query{RESET}")
                    else:
                        print(f"{WHITE}>{RESET} {GREEN}PIP-BOY{RESET}{DARKGREEN}:{RESET} {WHITE}{response}{RESET}")
                        print(f"{GRAY}  [{elapsed:.1f}s | mem:{history_len}]{RESET}")

                        # Append to history
                        append_to_history(user_input, response)
                print()

            except KeyboardInterrupt:
                print()
                break
            except EOFError:
                break

    finally:
        print(f"\n  {DARKGREEN}>>>{RESET} {GRAY}Shutting down AI subsystem...{RESET}")
        stop_server()
        user_name = get_user_name()
        print(f"  {GREEN}[OK]{RESET} {LIME}Stay safe out there, {user_name}.{RESET}")

if __name__ == "__main__":
    main()
