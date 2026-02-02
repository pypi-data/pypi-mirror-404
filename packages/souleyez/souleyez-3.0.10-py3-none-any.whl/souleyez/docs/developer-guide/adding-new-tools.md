# Adding New Tools to SoulEyez

This guide covers the complete process for integrating a new external tool into SoulEyez. Follow ALL steps to ensure proper integration.

## Quick Checklist

Use this checklist when adding a new tool:

- [ ] 1. Create plugin file (`souleyez/plugins/<tool>.py`)
- [ ] 2. Create handler file (`souleyez/handlers/<tool>_handler.py`)
- [ ] 3. Register handler in registry (`souleyez/handlers/registry.py`)
- [ ] 4. Add to tool checker (`souleyez/utils/tool_checker.py`)
- [ ] 5. Add to interactive UI menu (`souleyez/ui/interactive.py`)
- [ ] 6. Add chain rules if applicable (`souleyez/core/tool_chaining.py`)
- [ ] 7. Test the integration
- [ ] 8. Commit and push

---

## Step 1: Create the Plugin

**File:** `souleyez/plugins/<tool_name>.py`

The plugin defines how to build and execute the tool command.

```python
#!/usr/bin/env python3
"""
souleyez.plugins.<tool_name> - Brief description
"""
import subprocess
import time
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "Tool Display Name",
    "description": (
        "Multi-line description of what the tool does.\n\n"
        "When to use this tool:\n"
        "- Use case 1\n"
        "- Use case 2\n"
    ),
    "usage": "souleyez jobs enqueue <tool> <target> --args \"<arguments>\"",
    "examples": [
        "souleyez jobs enqueue <tool> 10.0.0.1 --args \"arg1 arg2\"",
    ],
    "flags": [
        ["--flag1", "Description of flag1"],
        ["--flag2", "Description of flag2"],
    ],
    "preset_categories": {
        "category_name": [
            {
                "name": "Preset Name",
                "args": ["arg1", "arg2", "<target>"],
                "desc": "What this preset does"
            },
        ]
    },
    "presets": []  # Auto-populated from preset_categories
}

# Flatten presets
for category_presets in HELP['preset_categories'].values():
    HELP['presets'].extend(category_presets)


class ToolNamePlugin(PluginBase):
    name = "Tool Display Name"
    tool = "tool_command"  # The actual CLI command
    category = "category_name"  # reconnaissance, scanning, exploitation, etc.
    HELP = HELP

    def build_command(self, target: str, args: List[str] = None, label: str = "", log_path: str = None):
        """Build command for background execution."""
        args = args or []
        args = [arg.replace("<target>", target) for arg in args]

        cmd = ["tool_command"]
        cmd.extend(args)

        return {
            'cmd': cmd,
            'timeout': 1800  # 30 minutes default
        }

    def run(self, target: str, args: List[str] = None, label: str = "", log_path: str = None) -> int:
        """Execute tool and write output to log_path."""
        args = args or []
        args = [arg.replace("<target>", target) for arg in args]

        cmd = ["tool_command"]
        cmd.extend(args)

        if not log_path:
            try:
                proc = subprocess.run(cmd, capture_output=True, timeout=600, check=False)
                return proc.returncode
            except Exception:
                return 1

        try:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(f"=== Plugin: ToolName ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {args}\n")
                fh.write(f"Command: {' '.join(cmd)}\n\n")

            proc = subprocess.run(cmd, capture_output=True, timeout=600, check=False, text=True)

            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                if proc.stdout:
                    fh.write(proc.stdout)
                if proc.stderr:
                    fh.write(f"\n{proc.stderr}")
                fh.write(f"\n\nExit Code: {proc.returncode}\n")

            return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a") as fh:
                fh.write("\n\nERROR: Command timed out\n")
            return 124
        except FileNotFoundError:
            with open(log_path, "w") as fh:
                fh.write(f"ERROR: {cmd[0]} not found in PATH\n")
            return 127
        except Exception as e:
            with open(log_path, "a") as fh:
                fh.write(f"\n\nERROR: {e}\n")
            return 1


plugin = ToolNamePlugin()
```

**Key Points:**
- Plugin is auto-discovered by `souleyez/engine/loader.py` via `pkgutil.iter_modules()`
- Must have a `plugin` attribute at module level
- The `tool` attribute should match the CLI command name

---

## Step 2: Create the Handler

**File:** `souleyez/handlers/<tool_name>_handler.py`

The handler parses tool output and displays results.

```python
#!/usr/bin/env python3
"""
Handler for <tool_name>.
"""
import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)

STATUS_DONE = 'done'
STATUS_ERROR = 'error'
STATUS_WARNING = 'warning'
STATUS_NO_RESULTS = 'no_results'


class ToolNameHandler(BaseToolHandler):
    """Handler for tool_name."""

    tool_name = "tool_name"  # Must match plugin's tool attribute
    display_name = "Tool Display Name"

    # Enable the handlers you implement
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Regex patterns for parsing output
    RESULT_PATTERN = r'RESULT:\s*(\S+)'
    ERROR_PATTERNS = [
        (r'connection refused', 'Connection refused'),
        (r'timeout', 'Connection timed out'),
    ]

    def parse_job(
        self,
        engagement_id: int,
        log_path: str,
        job: Dict[str, Any],
        host_manager: Optional[Any] = None,
        findings_manager: Optional[Any] = None,
        credentials_manager: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Parse tool results from log file."""
        try:
            target = job.get('target', '')

            if not log_path or not os.path.exists(log_path):
                return {
                    'tool': self.tool_name,
                    'status': STATUS_ERROR,
                    'error': 'Log file not found'
                }

            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                log_content = f.read()

            # Check for errors first
            for pattern, error_msg in self.ERROR_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    return {
                        'tool': self.tool_name,
                        'status': STATUS_ERROR,
                        'target': target,
                        'error': error_msg
                    }

            # Parse results
            results = re.findall(self.RESULT_PATTERN, log_content)

            if results:
                # Store findings/credentials if applicable
                # Example: Store credentials
                # if credentials_manager and host_manager:
                #     host = host_manager.get_host_by_ip(engagement_id, target)
                #     if host:
                #         credentials_manager.add_credential(...)

                return {
                    'tool': self.tool_name,
                    'status': STATUS_DONE,
                    'target': target,
                    'results': results,
                    'results_found': len(results),
                    # Add counts for job summary display:
                    # 'users_found': len(users),
                    # 'credentials_added': len(credentials),
                    # 'hosts_added': len(hosts),
                    # 'findings_added': len(findings),
                }

            return {
                'tool': self.tool_name,
                'status': STATUS_NO_RESULTS,
                'target': target
            }

        except Exception as e:
            logger.error(f"Error parsing {self.tool_name} job: {e}")
            return {'tool': self.tool_name, 'status': STATUS_ERROR, 'error': str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful results."""
        click.echo()
        click.echo(click.style("=" * 70, fg='green'))
        click.echo(click.style(f"{self.display_name.upper()} SUCCESSFUL", fg='green', bold=True))
        click.echo(click.style("=" * 70, fg='green'))
        click.echo()

        # Parse and display results from log
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                log_content = f.read()

            results = re.findall(self.RESULT_PATTERN, log_content)
            if results:
                click.echo(click.style(f"  RESULTS ({len(results)})", bold=True, fg='cyan'))
                for result in results:
                    click.echo(f"    {click.style(result, fg='green')}")
        except Exception as e:
            click.echo(f"  Error reading log: {e}")

        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display error results."""
        click.echo()
        click.echo(click.style("=" * 70, fg='red'))
        click.echo(click.style(f"{self.display_name.upper()} FAILED", fg='red', bold=True))
        click.echo(click.style("=" * 70, fg='red'))
        click.echo()

        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                log_content = f.read()

            for pattern, error_msg in self.ERROR_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    click.echo(f"  Error: {error_msg}")
                    break
            else:
                click.echo(f"  {self.display_name} failed - check log for details")
        except Exception:
            click.echo("  Could not read error details")

        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display warning results."""
        click.echo()
        click.echo(click.style("=" * 70, fg='yellow'))
        click.echo(click.style(f"{self.display_name.upper()} - PARTIAL RESULTS", fg='yellow', bold=True))
        click.echo(click.style("=" * 70, fg='yellow'))
        click.echo()
        click.echo("  Completed with warnings")
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display no results message."""
        click.echo()
        click.echo(click.style("=" * 70, fg='yellow'))
        click.echo(click.style(f"{self.display_name.upper()} - NO RESULTS", fg='yellow', bold=True))
        click.echo(click.style("=" * 70, fg='yellow'))
        click.echo()
        click.echo("  No results found.")
        click.echo()
```

**Key Points:**
- `tool_name` must match the plugin's `tool` attribute
- Return dict must include standard fields for job summary display:
  - `users_found`, `credentials_added`, `hosts_added`, `findings_added`, `shares_found`
- The `display_*` methods are called when viewing job details

---

## Step 3: Register Handler in Registry

**File:** `souleyez/handlers/registry.py`

Add import in the `_discover_handlers()` method:

```python
try:
    from souleyez.handlers import tool_name_handler  # noqa: F401
except ImportError as e:
    logger.warning(f"Failed to import tool_name_handler: {e}")
```

---

## Step 4: Add to Tool Checker

**File:** `souleyez/utils/tool_checker.py`

Add to the appropriate category in `EXTERNAL_TOOLS`:

```python
EXTERNAL_TOOLS = {
    # ... existing categories ...
    'category_name': {
        # ... existing tools ...
        'tool_name': {
            'command': 'tool_command',  # CLI command to check
            'install_kali': 'sudo apt install tool-package',
            'install_ubuntu': 'go install github.com/author/tool@latest',
            'install_method': 'apt',  # apt, go, pipx, gem, manual
            'description': 'Brief description for setup wizard'
        },
    },
}
```

**Categories:**
- `prerequisites` - Required system tools
- `reconnaissance` - OSINT and info gathering
- `web_scanning` - Web vulnerability scanning
- `exploitation` - Active exploitation
- `credential_attacks` - Password attacks
- `windows_ad` - Windows/Active Directory
- `router_iot` - Router and IoT testing
- `remote_access` - Remote access tools

---

## Step 5: Add to Interactive UI Menu

**File:** `souleyez/ui/interactive.py`

### 5.1 Add to Phase Subsection

Find the appropriate phase and add to its subsection tools list:

```python
PHASES = [
    # ...
    {
        "name": "PHASE 5: POST-EXPLOITATION",
        # ...
        "subsections": [
            {
                "title": "Credential Harvesting",
                "tools": [
                    "tool_name",  # Add here
                    "existing_tool",
                ],
            },
        ],
    },
]
```

### 5.2 Add Description

Add to `desc_map`:

```python
desc_map = {
    # ...
    "tool_name": "Brief description shown in menu",
}
```

### 5.3 Add Display Name

Add to `name_map` inside `get_display_name()`:

```python
name_map = {
    # ...
    "tool_name": "DisplayName",
}
```

---

## Step 6: Add Chain Rules (Optional)

**File:** `souleyez/core/tool_chaining.py`

If the tool should be triggered automatically based on other scan results:

```python
CHAIN_RULES = [
    # ...
    {
        'id': NEXT_ID,
        'name': 'Descriptive Chain Name',
        'trigger_tool': 'previous_tool',
        'trigger_status': 'done',
        'condition': lambda job, parse: (
            parse.get('some_condition') and
            other_condition
        ),
        'action_tool': 'tool_name',
        'action_args': ['arg1', '{placeholder}', '<target>'],
        'description': 'When to trigger this chain',
        'category': 'category_name',
    },
]
```

**Placeholders:**
- `<target>` - Target IP/hostname
- `{domain}` - Discovered domain name
- `{base_dn}` - LDAP base DN
- `{username}` - Username from credentials
- `{password}` - Password from credentials

---

## Step 7: Test the Integration

```bash
# Test plugin discovery
python3 -c "
from souleyez.engine.loader import discover_plugins
plugins = discover_plugins()
print('tool_name' in plugins)
print(plugins.get('tool_name'))
"

# Test handler registration
python3 -c "
from souleyez.handlers.registry import get_handler
handler = get_handler('tool_name')
print(handler)
print(handler.has_done_handler if handler else 'NOT REGISTERED')
"

# Test tool checker
python3 -c "
from souleyez.utils.tool_checker import EXTERNAL_TOOLS
for cat, tools in EXTERNAL_TOOLS.items():
    if 'tool_name' in tools:
        print(f'Found in {cat}')
        print(tools['tool_name'])
"

# Run the tool manually
souleyez jobs enqueue tool_name <target> --args "test args"
souleyez jobs list
```

---

## Step 8: Commit and Push

```bash
git add souleyez/plugins/tool_name.py
git add souleyez/handlers/tool_name_handler.py
git add souleyez/handlers/registry.py
git add souleyez/utils/tool_checker.py
git add souleyez/ui/interactive.py
git add souleyez/core/tool_chaining.py  # If chain rules added

git commit -m "feat: add tool_name plugin for <purpose>"
git push
```

---

## Common Mistakes to Avoid

1. **Forgetting to register handler** - Tool works but results aren't parsed
2. **Missing from tool_checker** - Won't appear in `souleyez setup` wizard
3. **Missing from UI menu** - Users can't find the tool
4. **Wrong tool_name in handler** - Handler won't be matched to jobs
5. **Missing count fields in parse_job return** - Job summary won't show results
6. **Not testing chain rules** - Automation won't trigger

---

## Files Modified When Adding a Tool

| File | Purpose |
|------|---------|
| `souleyez/plugins/<tool>.py` | Plugin (command building, execution) |
| `souleyez/handlers/<tool>_handler.py` | Handler (parsing, display) |
| `souleyez/handlers/registry.py` | Handler registration |
| `souleyez/utils/tool_checker.py` | Installation instructions |
| `souleyez/ui/interactive.py` | UI menu entry |
| `souleyez/core/tool_chaining.py` | Auto-chain rules (optional) |
