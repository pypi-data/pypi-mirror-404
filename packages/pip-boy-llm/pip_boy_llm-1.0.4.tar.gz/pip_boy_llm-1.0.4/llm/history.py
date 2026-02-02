"""
Conversation history management for PIP-BOY LLM.
Handles saving and loading conversations.
"""

import os
import yaml
from datetime import datetime
from llm.config import ensure_config_dir, get_config_value

# In-memory history for current session
_session_history = []


def get_history() -> list:
    """Get current session history."""
    return _session_history.copy()


def clear_history():
    """Clear current session history."""
    global _session_history
    _session_history = []


def append_to_history(user_msg: str, assistant_msg: str):
    """Add a message pair to session history."""
    _session_history.append({
        "role": "user",
        "content": user_msg,
        "timestamp": datetime.now().isoformat()
    })
    _session_history.append({
        "role": "assistant",
        "content": assistant_msg,
        "timestamp": datetime.now().isoformat()
    })


def save_conversation(filepath: str, messages: list, model_name: str = "Unknown"):
    """
    Save conversation to a markdown file.

    Args:
        filepath: Path to save file (markdown format)
        messages: List of message dicts with 'role' and 'content'
        model_name: Name of the model used
    """
    # Expand user path
    filepath = os.path.expanduser(filepath)

    # Ensure .md extension
    if not filepath.endswith(".md"):
        filepath += ".md"

    # Build markdown content
    lines = [
        "# PIP-BOY LLM Conversation",
        f"*Saved: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*Model: {model_name}*",
        "",
        "---",
        ""
    ]

    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "user":
            lines.append(f"**VAULT DWELLER:** {content}")
        else:
            lines.append(f"**PIP-BOY:** {content}")

        lines.append("")
        lines.append("---")
        lines.append("")

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return filepath, None
    except Exception as e:
        return None, str(e)


def load_conversation(filepath: str) -> tuple:
    """
    Load conversation from a markdown file.

    Returns:
        tuple: (messages_list, error) - messages_list is None if error
    """
    # Expand user path
    filepath = os.path.expanduser(filepath)

    # Try with and without .md extension
    if not os.path.exists(filepath) and not filepath.endswith(".md"):
        filepath += ".md"

    if not os.path.exists(filepath):
        return None, f"File not found: {filepath}"

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        messages = []

        # Parse markdown format
        lines = content.split("\n")
        for line in lines:
            line = line.strip()

            if line.startswith("**VAULT DWELLER:**"):
                msg = line.replace("**VAULT DWELLER:**", "").strip()
                messages.append({"role": "user", "content": msg})
            elif line.startswith("**PIP-BOY:**"):
                msg = line.replace("**PIP-BOY:**", "").strip()
                messages.append({"role": "assistant", "content": msg})

        return messages, None

    except Exception as e:
        return None, str(e)


def save_to_history_file(messages: list):
    """Append messages to persistent history file (YAML)."""
    ensure_config_dir()
    history_file = get_config_value("history_file")

    if not history_file:
        return

    history_file = os.path.expanduser(history_file)

    # Load existing history
    existing = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or []
        except Exception:
            existing = []

    # Append new messages
    existing.extend(messages)

    # Keep only last 100 message pairs
    if len(existing) > 200:
        existing = existing[-200:]

    try:
        with open(history_file, "w", encoding="utf-8") as f:
            yaml.dump(existing, f, default_flow_style=False, allow_unicode=True)
    except Exception:
        pass  # Silently fail


def load_from_history_file() -> list:
    """Load messages from persistent history file."""
    history_file = get_config_value("history_file")

    if not history_file:
        return []

    history_file = os.path.expanduser(history_file)

    if not os.path.exists(history_file):
        return []

    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    except Exception:
        return []
