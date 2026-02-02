# Dictionary mapping tools to their preferred wordlists
# Format: tool_name -> wordlist_category -> priority ordered list

import os
from pathlib import Path


def resolve_wordlist_path(relative_path: str) -> str:
    """
    Resolve a wordlist path to an absolute path.

    Handles paths like 'data/wordlists/foo.txt' and resolves them to actual
    filesystem paths, checking multiple locations:
    1. ~/.souleyez/data/wordlists/ (user writable, copied on first run)
    2. /usr/share/souleyez/wordlists/ (Debian package install)
    3. Development path (relative to project root)

    Args:
        relative_path: Path like 'data/wordlists/foo.txt' or just 'foo.txt'

    Returns:
        Absolute path to the wordlist file, or original path if not found
    """
    # If it's already an absolute path, return as-is
    if relative_path.startswith("/"):
        return relative_path

    # Extract just the filename if it's a data/wordlists/ path
    if "data/wordlists/" in relative_path:
        filename = relative_path.split("data/wordlists/")[-1]
    elif relative_path.startswith("wordlists/"):
        filename = relative_path.replace("wordlists/", "", 1)
    else:
        filename = relative_path

    # Locations to check in priority order
    locations = [
        Path.home() / ".souleyez" / "data" / "wordlists" / filename,
        Path("/usr/share/souleyez/wordlists") / filename,
        Path(__file__).parent / "data" / "wordlists" / filename,  # Package bundled
    ]

    for loc in locations:
        if loc.exists():
            return str(loc)

    # Not found - return original path (tools will report file not found)
    return relative_path


def resolve_args_wordlists(args: list) -> list:
    """
    Resolve all wordlist paths in a list of command arguments.

    Handles both plain paths and KEY=value format (e.g., USER_FILE=data/wordlists/foo.txt).

    Args:
        args: List of command arguments

    Returns:
        List with wordlist paths resolved to absolute paths
    """
    resolved = []
    for arg in args:
        if isinstance(arg, str) and "data/wordlists/" in arg:
            # Check if this is a KEY=value format (e.g., USER_FILE=data/wordlists/foo.txt)
            if "=" in arg:
                key, value = arg.split("=", 1)
                resolved_path = resolve_wordlist_path(value)
                resolved.append(f"{key}={resolved_path}")
            else:
                resolved.append(resolve_wordlist_path(arg))
        else:
            resolved.append(arg)
    return resolved


def ensure_user_wordlists():
    """
    Copy wordlists to user directory if not present.

    This ensures users have writable copies of wordlists in ~/.souleyez/data/wordlists/
    """
    user_wordlist_dir = Path.home() / ".souleyez" / "data" / "wordlists"

    # Only do this once
    if user_wordlist_dir.exists() and any(user_wordlist_dir.glob("*.txt")):
        return

    # Try to find source wordlists
    source_dirs = [
        Path("/usr/share/souleyez/wordlists"),
        Path(__file__).parent / "data" / "wordlists",  # Package bundled
    ]

    source_dir = None
    for d in source_dirs:
        if d.exists() and any(d.glob("*.txt")):
            source_dir = d
            break

    if not source_dir:
        return

    # Create user directory and copy files
    user_wordlist_dir.mkdir(parents=True, exist_ok=True)

    import shutil

    for src_file in source_dir.glob("*.txt"):
        dst_file = user_wordlist_dir / src_file.name
        if not dst_file.exists():
            try:
                shutil.copy2(src_file, dst_file)
            except Exception:
                pass  # Fail silently


wordlist_map = {
    # All wordlists are now self-contained in the project
    # No external dependencies on /usr/share/* paths
    "hydra": {
        "users": [
            "data/wordlists/usernames_common.txt",
            "data/wordlists/all_users.txt",
            "data/wordlists/ad_users.txt",
        ],
        "passwords": [
            "data/wordlists/passwords_brute.txt",
            "data/wordlists/top100.txt",
            "data/wordlists/top20_quick.txt",
        ],
    },
    "medusa": {
        "users": [
            "data/wordlists/usernames_common.txt",
            "data/wordlists/all_users.txt",
        ],
        "passwords": [
            "data/wordlists/passwords_brute.txt",
            "data/wordlists/top100.txt",
        ],
    },
    "gobuster": {
        "dirs": [
            "data/wordlists/web_dirs_large.txt",
            "data/wordlists/web_dirs_common.txt",
        ],
        "files": [
            "data/wordlists/web_files_common.txt",
        ],
        "dns": [
            "data/wordlists/subdomains_large.txt",
            "data/wordlists/subdomains_common.txt",
        ],
        "extensions": [
            "data/wordlists/web_extensions.txt",
        ],
    },
    "dirb": {
        "wordlist": [
            "data/wordlists/web_dirs_large.txt",
            "data/wordlists/web_dirs_common.txt",
        ]
    },
    "wfuzz": {
        "wordlist": [
            "data/wordlists/web_dirs_large.txt",
            "data/wordlists/web_dirs_common.txt",
        ]
    },
    "ffuf": {
        "dirs": [
            "data/wordlists/web_dirs_large.txt",
            "data/wordlists/web_dirs_common.txt",
        ],
        "api": [
            "data/wordlists/api_endpoints_large.txt",
            "data/wordlists/api_endpoints.txt",
        ],
        "params": [
            "data/wordlists/web_files_common.txt",
        ],
    },
    "msf_auxiliary": {
        "users": [
            "data/wordlists/usernames_common.txt",
            "data/wordlists/soul_users.txt",
        ],
        "passwords": [
            "data/wordlists/passwords_brute.txt",
            "data/wordlists/top20_quick.txt",
        ],
    },
    "ncrack": {
        "users": [
            "data/wordlists/usernames_common.txt",
            "data/wordlists/all_users.txt",
        ],
        "passwords": [
            "data/wordlists/passwords_brute.txt",
            "data/wordlists/top100.txt",
        ],
    },
    "hashcat": {
        "passwords": [
            "data/wordlists/passwords_crack.txt",
            "data/wordlists/passwords_brute.txt",
        ]
    },
    "john": {
        "passwords": [
            "data/wordlists/passwords_crack.txt",
            "data/wordlists/passwords_brute.txt",
        ]
    },
}


def get_wordlists(tool_name, category):
    """
    Get prioritized wordlist paths for a tool and category.

    Args:
        tool_name: Name of the tool (e.g., 'hydra', 'gobuster')
        category: Category of wordlist (e.g., 'users', 'passwords', 'dirs')

    Returns:
        List of wordlist paths in priority order (built-in first, then system)
    """
    tool_map = wordlist_map.get(tool_name.lower(), {})
    wordlists = tool_map.get(category, [])

    # Convert relative paths to absolute using resolver and filter to only existing files
    existing = []
    for w in wordlists:
        resolved = resolve_wordlist_path(w)
        if os.path.exists(resolved):
            existing.append(resolved)

    # Discover additional built-in wordlists not in the map
    # Check multiple locations for wordlist directory
    wordlist_dirs = [
        Path.home() / ".souleyez" / "data" / "wordlists",
        Path("/usr/share/souleyez/wordlists"),
        Path(__file__).parent / "data" / "wordlists",  # Package bundled
    ]

    for wordlist_dir in wordlist_dirs:
        if wordlist_dir.exists():
            discovered = _discover_wordlists_by_category(wordlist_dir, category)
            # Add discovered wordlists that aren't already in the list
            for wl in discovered:
                if wl not in existing:
                    existing.append(wl)
            break  # Use first found directory

    return existing


def _discover_wordlists_by_category(wordlist_dir, category):
    """
    Discover wordlists in directory matching a category.

    Args:
        wordlist_dir: Path object to wordlists directory
        category: Category name (users, passwords, dirs, etc.)

    Returns:
        List of absolute paths to matching wordlists
    """
    import os

    # Special handling for categories that should show all wordlists
    show_all_categories = {"users", "passwords"}

    # Category-specific patterns (only for non-show-all categories)
    category_patterns = {
        "dirs": ["_dirs", "directories"],
        "files": ["_files"],
        "dns": ["subdomains", "dns"],
        "wordlist": [],  # Generic - include all
    }

    matches = []

    try:
        for file in sorted(wordlist_dir.glob("*.txt")):
            filename = file.name.lower()

            # For users/passwords, show ALL wordlists
            if category in show_all_categories:
                matches.append(str(file))
            # For other categories, use pattern matching
            elif category in category_patterns:
                patterns = category_patterns[category]
                if not patterns:  # Empty list means include all
                    matches.append(str(file))
                else:
                    for pattern in patterns:
                        if pattern in filename:
                            matches.append(str(file))
                            break
            else:
                # Unknown category - include all
                matches.append(str(file))
    except Exception:
        pass

    return matches


def get_wordlist_info(wordlist_path):
    """
    Get information about a wordlist file.

    Returns:
        Dict with keys: path, line_count, size_mb, is_builtin
    """
    if not os.path.exists(wordlist_path):
        return None

    try:
        with open(wordlist_path) as f:
            line_count = sum(
                1 for line in f if line.strip() and not line.startswith("#")
            )
        size_mb = os.path.getsize(wordlist_path) / (1024 * 1024)
        # Check if it's a built-in wordlist (from any souleyez location)
        builtin_dirs = [
            str(Path.home() / ".souleyez" / "data" / "wordlists"),
            "/usr/share/souleyez/wordlists",
            "data/wordlists/",
        ]
        is_builtin = any(bd in wordlist_path for bd in builtin_dirs)

        return {
            "path": wordlist_path,
            "line_count": line_count,
            "size_mb": size_mb,
            "is_builtin": is_builtin,
        }
    except Exception:
        return None


def display_wordlist_menu(
    tool_name, category, title="Wordlist Selection", allow_single_value=None
):
    """
    Display an interactive wordlist selection browser.

    Goes directly to the full wordlist browser with recommended wordlists highlighted.

    Args:
        tool_name: Name of the tool
        category: Category of wordlist
        title: Menu title
        allow_single_value: If True, enable single value entry. If None (default),
                           auto-detect based on category (True for users/passwords)

    Returns:
        Selected wordlist path, ('single', value) tuple, or None if cancelled
    """
    import click

    from souleyez.ui.wordlist_browser import browse_wordlists

    # Get recommended wordlists for this tool/category
    wordlists = get_wordlists(tool_name, category)

    # Separate built-in wordlists (these are recommended)
    builtin_dirs = [
        str(Path.home() / ".souleyez" / "data" / "wordlists"),
        "/usr/share/souleyez/wordlists",
        str(Path(__file__).parent / "data" / "wordlists"),  # Package bundled
    ]
    recommended = [w for w in wordlists if any(bd in w for bd in builtin_dirs)]

    # Determine single value label based on category
    single_label = (
        "username"
        if category == "users"
        else "password" if category == "passwords" else "value"
    )

    # Auto-detect allow_single_value based on category if not specified
    # Single values make sense for users/passwords but not for dirs/dns wordlists
    if allow_single_value is None:
        allow_single_value = category in ("users", "passwords")

    # Launch browser directly with recommended paths highlighted
    selected = browse_wordlists(
        category_filter=category,
        title=(
            f"SELECT {category.upper()} WORDLIST"
            if title == "Wordlist Selection"
            else title.upper()
        ),
        recommended_paths=recommended,
        allow_single_value=allow_single_value,
        allow_custom_path=True,
        single_value_label=single_label,
    )

    # Show confirmation message
    if selected:
        if isinstance(selected, tuple) and selected[0] == "single":
            click.echo(
                click.style(f"✓ Single {single_label}: {selected[1]}", fg="green")
            )
        else:
            click.echo(click.style(f"✓ Selected: {selected}", fg="green"))

    return selected


def get_available_wordlists(category="users"):
    """
    Get available wordlists for a category.

    Args:
        category: 'users', 'passwords', or 'credentials'

    Returns:
        dict: {name_with_count: absolute_path}
    """
    result = {}

    if category == "users":
        files = [
            ("All Users", "all_users.txt"),
            ("Linux Users", "linux_users.txt"),
            ("Soul Users", "soul_users.txt"),
        ]
    elif category == "passwords":
        files = [
            ("Top 20 Quick", "top20_quick.txt"),
            ("Top 100", "top100.txt"),
            ("Soul Passwords", "soul_pass.txt"),
            ("Default Credentials", "default_credentials.txt"),
        ]
    elif category == "credentials":
        files = [
            ("Default Credentials (user:pass)", "default_credentials.txt"),
        ]
    else:
        return result

    for name, filename in files:
        # Use resolver to find actual path
        resolved = resolve_wordlist_path(f"data/wordlists/{filename}")
        if os.path.exists(resolved):
            # Dynamically calculate entry count (excluding comments and blank lines)
            try:
                with open(resolved) as f:
                    count = sum(
                        1 for line in f if line.strip() and not line.startswith("#")
                    )
                name_with_count = f"{name} ({count})"
            except Exception:
                name_with_count = name
            result[name_with_count] = resolved

    return result
