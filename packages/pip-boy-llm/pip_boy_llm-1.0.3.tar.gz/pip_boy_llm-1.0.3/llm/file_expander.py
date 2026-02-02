"""
File expander for @filepath syntax in user input.
Allows injecting file contents into messages before sending to LLM.
"""

import os
import re

# Try to import PDF library (optional)
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Default max file size (50KB), configurable via environment
MAX_FILE_SIZE = int(os.environ.get("AIRLLM_MAX_FILE_SIZE", 50 * 1024))

# Language detection based on file extension
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "jsx",
    ".tsx": "tsx",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".ps1": "powershell",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".less": "less",
    ".json": "json",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".md": "markdown",
    ".txt": "text",
    ".lua": "lua",
    ".r": "r",
    ".R": "r",
    ".pl": "perl",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hs": "haskell",
    ".ml": "ocaml",
    ".fs": "fsharp",
    ".clj": "clojure",
    ".vim": "vim",
    ".dockerfile": "dockerfile",
}

# Binary file extensions to reject
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv", ".flac",
    ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".pyc", ".pyo", ".class", ".o", ".obj",
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
}

# Special file types that need custom handling
SPECIAL_EXTENSIONS = {".pdf"}


def detect_language(filepath):
    """Detect programming language from file extension."""
    _, ext = os.path.splitext(filepath.lower())
    return LANGUAGE_MAP.get(ext, "")


def is_binary_extension(filepath):
    """Check if file has a known binary extension."""
    _, ext = os.path.splitext(filepath.lower())
    return ext in BINARY_EXTENSIONS


def is_binary_content(content_bytes):
    """Check if content appears to be binary (contains null bytes)."""
    return b'\x00' in content_bytes[:8192]


def is_special_extension(filepath):
    """Check if file has a special extension requiring custom handling."""
    _, ext = os.path.splitext(filepath.lower())
    return ext in SPECIAL_EXTENSIONS


def read_pdf_content(filepath):
    """
    Extract text from a PDF file.

    Returns:
        tuple: (content, error) - content is None if error occurred
    """
    if not PDF_AVAILABLE:
        return None, f"PDF support not available. Install PyPDF2: pip install PyPDF2"

    try:
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)

            # Check if encrypted
            if reader.is_encrypted:
                return None, f"PDF is encrypted: {filepath}"

            # Extract text from all pages
            text_parts = []
            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
                except Exception:
                    text_parts.append(f"--- Page {i + 1} ---\n[Could not extract text]")

            if not text_parts:
                return None, f"No text could be extracted from PDF: {filepath}"

            content = "\n\n".join(text_parts)

            # Check size after extraction
            if len(content) > MAX_FILE_SIZE:
                size_kb = len(content) / 1024
                max_kb = MAX_FILE_SIZE / 1024
                return None, f"PDF text too large ({size_kb:.1f}KB > {max_kb:.0f}KB limit): {filepath}"

            return content, None

    except PyPDF2.errors.PdfReadError as e:
        return None, f"Invalid or corrupted PDF: {filepath}"
    except Exception as e:
        return None, f"Error reading PDF: {filepath} ({e})"


def read_file_content(filepath):
    """
    Read file content with size limits and binary detection.

    Returns:
        tuple: (content, error) - content is None if error occurred
    """
    # Resolve path relative to current directory
    resolved_path = os.path.abspath(filepath)

    # Check if file exists
    if not os.path.exists(resolved_path):
        return None, f"File not found: {filepath}"

    # Check if it's a file (not directory)
    if not os.path.isfile(resolved_path):
        return None, f"Not a file: {filepath}"

    # Handle special file types (PDF, etc.)
    if is_special_extension(resolved_path):
        _, ext = os.path.splitext(resolved_path.lower())
        if ext == ".pdf":
            return read_pdf_content(resolved_path)

    # Check binary extension
    if is_binary_extension(resolved_path):
        return None, f"Binary file not supported: {filepath}"

    # Check file size
    try:
        file_size = os.path.getsize(resolved_path)
        if file_size > MAX_FILE_SIZE:
            size_kb = file_size / 1024
            max_kb = MAX_FILE_SIZE / 1024
            return None, f"File too large ({size_kb:.1f}KB > {max_kb:.0f}KB limit): {filepath}"
    except OSError as e:
        return None, f"Cannot access file: {filepath} ({e})"

    # Read file
    try:
        with open(resolved_path, "rb") as f:
            content_bytes = f.read()

        # Check for binary content
        if is_binary_content(content_bytes):
            return None, f"Binary file not supported: {filepath}"

        # Decode as text
        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = content_bytes.decode("latin-1")
            except UnicodeDecodeError:
                return None, f"Cannot decode file (unknown encoding): {filepath}"

        return content, None

    except PermissionError:
        return None, f"Permission denied: {filepath}"
    except OSError as e:
        return None, f"Cannot read file: {filepath} ({e})"


def parse_file_references(text):
    """
    Parse @filepath patterns from input text.

    Supported patterns:
        @filepath       - Simple path (no spaces)
        @"path"         - Quoted path (supports spaces)
        @@literal       - Escaped @ (produces literal @)

    Returns:
        list of tuples: [(match_string, filepath, is_escape), ...]
    """
    references = []

    # Pattern for @"quoted path" - must check first
    quoted_pattern = r'@"([^"]+)"'

    # Pattern for simple @filepath (no spaces, no quotes)
    # Stops at whitespace, quotes, or common punctuation
    simple_pattern = r'@([^\s"\'@,;:!?\[\](){}]+)'

    # Pattern for escaped @@ -> @
    escape_pattern = r'@@(\S+)'

    # Find all matches with their positions
    matches = []

    # Find escaped @@ first
    for m in re.finditer(escape_pattern, text):
        matches.append((m.start(), m.end(), m.group(0), m.group(1), True))

    # Find quoted paths
    for m in re.finditer(quoted_pattern, text):
        # Skip if overlaps with escape
        if not any(m.start() >= s and m.start() < e for s, e, _, _, _ in matches):
            matches.append((m.start(), m.end(), m.group(0), m.group(1), False))

    # Find simple paths
    for m in re.finditer(simple_pattern, text):
        # Skip if overlaps with existing match
        if not any(m.start() >= s and m.start() < e for s, e, _, _, _ in matches):
            matches.append((m.start(), m.end(), m.group(0), m.group(1), False))

    # Sort by position and convert to result format
    matches.sort(key=lambda x: x[0])

    for _, _, match_str, filepath, is_escape in matches:
        references.append((match_str, filepath, is_escape))

    return references


def expand_file_references(text):
    """
    Expand all @filepath references in text with file contents.

    Returns:
        tuple: (expanded_text, errors_list)
    """
    references = parse_file_references(text)
    errors = []
    expanded = text

    # Process in reverse order to preserve positions
    for match_str, filepath, is_escape in reversed(references):
        if is_escape:
            # @@ -> @ (literal)
            replacement = f"@{filepath}"
        else:
            # Read file and create replacement
            content, error = read_file_content(filepath)

            if error:
                errors.append(error)
                # Keep original reference on error
                continue

            # Format with language hint for syntax highlighting
            lang = detect_language(filepath)
            filename = os.path.basename(filepath)

            # Create formatted content block
            replacement = f"\n--- {filename} ---\n```{lang}\n{content}\n```\n"

        # Replace in text
        expanded = expanded.replace(match_str, replacement, 1)

    return expanded, errors
