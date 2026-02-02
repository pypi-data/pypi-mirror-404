"""
Command handler system for PIP-BOY LLM CLI.
Provides slash commands for file operations, navigation, and session management.
"""

import os
import sys
from datetime import datetime

# Colors - matching cli.py theme
GREEN = "\033[92m"
DARKGREEN = "\033[32m"
LIME = "\033[38;5;118m"
GRAY = "\033[90m"
WHITE = "\033[97m"
RESET = "\033[0m"


class CommandContext:
    """Context object passed to command handlers."""

    def __init__(self, api_url: str, model_name: str = "Unknown"):
        self.api_url = api_url
        self.model_name = model_name
        self.messages = []  # Current session messages

    def add_message(self, role: str, content: str):
        """Add a message to session history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })


def format_size(size_bytes: int) -> str:
    """Format file size for display."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_file_icon(path: str) -> str:
    """Get icon for file/directory."""
    if os.path.isdir(path):
        return "\U0001F4C1"  # folder icon

    ext = os.path.splitext(path)[1].lower()

    # Code files
    if ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".go", ".rs"):
        return "\U0001F4C4"  # document icon
    # Config files
    elif ext in (".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml"):
        return "\U0001F4C4"
    # Docs
    elif ext in (".md", ".txt", ".rst", ".doc", ".docx", ".pdf"):
        return "\U0001F4C4"
    # Images
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"):
        return "\U0001F5BC"  # image icon
    else:
        return "\U0001F4C4"  # default document


# ============ Command Handlers ============

def cmd_help(args: str, context: CommandContext) -> str:
    """Display all available commands."""
    help_text = f"""
  {LIME}>>> PIP-BOY COMMAND REFERENCE <<<{RESET}

  {GREEN}/help{RESET}           Show this help message
  {GREEN}/ls [path]{RESET}      List files in directory
  {GREEN}/tree [path]{RESET}    Show directory tree
  {GREEN}/cd <path>{RESET}      Change working directory
  {GREEN}/pwd{RESET}            Show current directory
  {GREEN}/clear{RESET}          Clear conversation memory
  {GREEN}/save [file]{RESET}    Save conversation to markdown
  {GREEN}/load <file>{RESET}    Load conversation from file
  {GREEN}/history{RESET}        Show conversation history
  {GREEN}/settings{RESET}       Change color theme and name
  {GREEN}/exit{RESET}           Exit PIP-BOY LLM

  {GRAY}Shortcuts: exit, quit, q, clear{RESET}
  {GRAY}File refs: @filepath to include file contents{RESET}
"""
    print(help_text)
    return "continue"


def cmd_ls(args: str, context: CommandContext) -> str:
    """List files in directory."""
    path = args.strip() if args.strip() else "."
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        print(f"  {GREEN}[!]{RESET} {GRAY}Directory not found: {path}{RESET}")
        return "continue"

    if not os.path.isdir(path):
        print(f"  {GREEN}[!]{RESET} {GRAY}Not a directory: {path}{RESET}")
        return "continue"

    try:
        entries = sorted(os.listdir(path))

        # Separate dirs and files
        dirs = []
        files = []

        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                dirs.append(entry)
            else:
                files.append(entry)

        print()

        # Print directories first
        for d in dirs:
            icon = get_file_icon(os.path.join(path, d))
            print(f"  {icon} {LIME}{d}/{RESET}")

        # Print files with sizes
        for f in files:
            full_path = os.path.join(path, f)
            icon = get_file_icon(full_path)
            try:
                size = format_size(os.path.getsize(full_path))
                print(f"  {icon} {WHITE}{f:<30}{RESET} {GRAY}({size}){RESET}")
            except OSError:
                print(f"  {icon} {WHITE}{f}{RESET}")

        if not dirs and not files:
            print(f"  {GRAY}(empty directory){RESET}")

        print()

    except PermissionError:
        print(f"  {GREEN}[!]{RESET} {GRAY}Permission denied: {path}{RESET}")
    except Exception as e:
        print(f"  {GREEN}[!]{RESET} {GRAY}Error: {e}{RESET}")

    return "continue"


def cmd_tree(args: str, context: CommandContext) -> str:
    """Show directory tree."""
    path = args.strip() if args.strip() else "."
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        print(f"  {GREEN}[!]{RESET} {GRAY}Directory not found: {path}{RESET}")
        return "continue"

    if not os.path.isdir(path):
        print(f"  {GREEN}[!]{RESET} {GRAY}Not a directory: {path}{RESET}")
        return "continue"

    print()

    def print_tree(dir_path: str, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
        if current_depth >= max_depth:
            return

        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            return

        # Filter hidden files
        entries = [e for e in entries if not e.startswith('.')]

        dirs = [e for e in entries if os.path.isdir(os.path.join(dir_path, e))]
        files = [e for e in entries if not os.path.isdir(os.path.join(dir_path, e))]

        all_entries = dirs + files

        for i, entry in enumerate(all_entries):
            is_last = (i == len(all_entries) - 1)
            connector = "\u2514\u2500\u2500 " if is_last else "\u251C\u2500\u2500 "

            full_path = os.path.join(dir_path, entry)
            icon = get_file_icon(full_path)

            if os.path.isdir(full_path):
                print(f"  {prefix}{connector}{icon} {LIME}{entry}/{RESET}")
                new_prefix = prefix + ("    " if is_last else "\u2502   ")
                print_tree(full_path, new_prefix, max_depth, current_depth + 1)
            else:
                print(f"  {prefix}{connector}{icon} {WHITE}{entry}{RESET}")

    # Print root
    root_name = os.path.basename(os.path.abspath(path)) or path
    print(f"  \U0001F4C1 {LIME}{root_name}/{RESET}")
    print_tree(path)
    print()

    return "continue"


def cmd_cd(args: str, context: CommandContext) -> str:
    """Change working directory."""
    path = args.strip()

    if not path:
        # No argument - show current directory
        print(f"  {GREEN}[DIR]{RESET} {LIME}{os.getcwd()}{RESET}\n")
        return "continue"

    # Remove quotes if present
    if (path.startswith('"') and path.endswith('"')) or \
       (path.startswith("'") and path.endswith("'")):
        path = path[1:-1]

    path = os.path.expanduser(path)

    try:
        os.chdir(path)
        print(f"  {GREEN}[OK]{RESET} {LIME}{os.getcwd()}{RESET}\n")
    except FileNotFoundError:
        print(f"  {GREEN}[!]{RESET} {GRAY}Directory not found: {path}{RESET}\n")
    except PermissionError:
        print(f"  {GREEN}[!]{RESET} {GRAY}Permission denied: {path}{RESET}\n")
    except Exception as e:
        print(f"  {GREEN}[!]{RESET} {GRAY}Error: {e}{RESET}\n")

    return "continue"


def cmd_pwd(args: str, context: CommandContext) -> str:
    """Show current working directory."""
    print(f"  {GREEN}[DIR]{RESET} {LIME}{os.getcwd()}{RESET}\n")
    return "continue"


def cmd_clear(args: str, context: CommandContext) -> str:
    """Clear conversation memory."""
    import requests

    try:
        requests.post(f"{context.api_url}/clear", timeout=5)
    except:
        pass

    # Clear local history
    context.messages.clear()

    from llm.history import clear_history
    clear_history()

    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')

    return "cleared"


def cmd_save(args: str, context: CommandContext) -> str:
    """Save conversation to markdown file."""
    from llm.history import save_conversation, get_history

    filename = args.strip() if args.strip() else f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    messages = get_history()

    if not messages:
        print(f"  {GREEN}[!]{RESET} {GRAY}No conversation to save{RESET}\n")
        return "continue"

    filepath, error = save_conversation(filename, messages, context.model_name)

    if error:
        print(f"  {GREEN}[!]{RESET} {GRAY}Save failed: {error}{RESET}\n")
    else:
        print(f"  {GREEN}[OK]{RESET} {LIME}Saved to: {filepath}{RESET}\n")

    return "continue"


def cmd_load(args: str, context: CommandContext) -> str:
    """Load conversation from file."""
    from llm.history import load_conversation

    filename = args.strip()

    if not filename:
        print(f"  {GREEN}[!]{RESET} {GRAY}Usage: /load <filename>{RESET}\n")
        return "continue"

    messages, error = load_conversation(filename)

    if error:
        print(f"  {GREEN}[!]{RESET} {GRAY}Load failed: {error}{RESET}\n")
        return "continue"

    # Display loaded conversation
    print(f"\n  {LIME}>>> Loaded conversation ({len(messages)} messages) <<<{RESET}\n")

    for msg in messages[-10:]:  # Show last 10 messages
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        # Truncate long messages
        if len(content) > 100:
            content = content[:100] + "..."

        if role == "user":
            print(f"  {LIME}VAULT DWELLER:{RESET} {GRAY}{content}{RESET}")
        else:
            print(f"  {GREEN}PIP-BOY:{RESET} {GRAY}{content}{RESET}")

    if len(messages) > 10:
        print(f"  {GRAY}... and {len(messages) - 10} more messages{RESET}")

    print()
    return "continue"


def cmd_history(args: str, context: CommandContext) -> str:
    """Show conversation history."""
    from llm.history import get_history

    messages = get_history()

    if not messages:
        print(f"  {GRAY}No conversation history{RESET}\n")
        return "continue"

    print(f"\n  {LIME}>>> Conversation History ({len(messages)} messages) <<<{RESET}\n")

    # Show last 20 messages
    for msg in messages[-20:]:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")

        # Truncate long messages
        if len(content) > 100:
            content = content[:100] + "..."

        if role == "user":
            print(f"  {LIME}VAULT DWELLER:{RESET} {WHITE}{content}{RESET}")
        else:
            print(f"  {GREEN}PIP-BOY:{RESET} {WHITE}{content}{RESET}")

    if len(messages) > 20:
        print(f"  {GRAY}... and {len(messages) - 20} more messages{RESET}")

    print()
    return "continue"


def cmd_exit(args: str, context: CommandContext) -> str:
    """Exit the application."""
    return "exit"


def cmd_settings(args: str, context: CommandContext) -> str:
    """Open settings menu."""
    from llm.config import (
        get_config_value, set_config_value,
        COLOR_THEMES, get_theme_colors
    )

    current_color = get_config_value("color_mode", "green")
    current_name = get_config_value("user_name", "VAULT DWELLER")

    # Get current theme colors for display
    theme = get_theme_colors(current_color)
    PRIMARY = theme["primary"]
    ACCENT = theme["accent"]

    print(f"""
  {ACCENT}>>> SETTINGS <<<{RESET}

  {PRIMARY}[1]{RESET} Color Theme: {ACCENT}{current_color.upper()}{RESET}
  {PRIMARY}[2]{RESET} User Name:   {ACCENT}{current_name}{RESET}
  {PRIMARY}[0]{RESET} Back

""")

    try:
        choice = input(f"  {ACCENT}>{RESET} Select option: ").strip()

        if choice == "1":
            # Color selection
            print(f"\n  {ACCENT}Select color theme:{RESET}\n")
            color_options = list(COLOR_THEMES.keys())
            for i, color in enumerate(color_options, 1):
                theme_colors = get_theme_colors(color)
                marker = " *" if color == current_color else ""
                print(f"  {theme_colors['primary']}[{i}]{RESET} {theme_colors['accent']}{color.upper()}{RESET}{GRAY}{marker}{RESET}")

            print()
            color_choice = input(f"  {ACCENT}>{RESET} Select theme [1-{len(color_options)}]: ").strip()

            try:
                idx = int(color_choice) - 1
                if 0 <= idx < len(color_options):
                    new_color = color_options[idx]
                    set_config_value("color_mode", new_color)
                    new_theme = get_theme_colors(new_color)
                    print(f"\n  {new_theme['primary']}[OK]{RESET} {new_theme['accent']}Theme set to {new_color.upper()}{RESET}")
                    print(f"  {GRAY}Restart for full effect{RESET}\n")
                else:
                    print(f"  {GREEN}[!]{RESET} {GRAY}Invalid selection{RESET}\n")
            except ValueError:
                print(f"  {GREEN}[!]{RESET} {GRAY}Invalid selection{RESET}\n")

        elif choice == "2":
            # Name input
            print()
            new_name = input(f"  {ACCENT}>{RESET} Enter your name: ").strip()
            if new_name:
                set_config_value("user_name", new_name)
                print(f"\n  {PRIMARY}[OK]{RESET} {ACCENT}Name set to: {new_name}{RESET}")
                print(f"  {GRAY}Restart for full effect{RESET}\n")
            else:
                print(f"  {GREEN}[!]{RESET} {GRAY}Name not changed{RESET}\n")

        elif choice == "0" or choice == "":
            print()

    except KeyboardInterrupt:
        print("\n")

    return "continue"


# ============ Command Registry ============

COMMANDS = {
    "/help": cmd_help,
    "/ls": cmd_ls,
    "/tree": cmd_tree,
    "/cd": cmd_cd,
    "/pwd": cmd_pwd,
    "/clear": cmd_clear,
    "/save": cmd_save,
    "/load": cmd_load,
    "/history": cmd_history,
    "/settings": cmd_settings,
    "/exit": cmd_exit,
}

# Shortcuts (backwards compatible)
SHORTCUTS = {
    "exit": "/exit",
    "quit": "/exit",
    "q": "/exit",
    "clear": "/clear",
}


def handle_command(user_input: str, context: CommandContext) -> str:
    """
    Handle a command if input matches a known command.

    Returns:
        - "continue": Command executed, continue chat loop
        - "exit": Exit the application
        - "cleared": Screen was cleared, redraw banner
        - None: Not a command
    """
    user_input = user_input.strip()

    # Check shortcuts first
    if user_input.lower() in SHORTCUTS:
        user_input = SHORTCUTS[user_input.lower()]

    # Check if it's a command
    if not user_input.startswith("/"):
        return None

    # Parse command and arguments
    parts = user_input.split(None, 1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    # Find and execute handler
    if cmd in COMMANDS:
        return COMMANDS[cmd](args, context)
    else:
        print(f"  {GREEN}[!]{RESET} {GRAY}Unknown command: {cmd}{RESET}")
        print(f"  {GRAY}Type /help for available commands{RESET}\n")
        return "continue"
