# SoulEyez UI Design System

**Version:** 1.0
**Status:** Proposed
**Last Updated:** 2025-11-05

---

## Purpose

This document defines the visual design system for SoulEyez's CLI interface. Following these standards ensures:
- **Professional appearance** - Consistent, clean UI across all views
- **Maintainability** - Centralized styling reduces code duplication
- **Accessibility** - Predictable layout helps users navigate efficiently
- **Terminal compatibility** - Works across 80-120+ column terminals

---

## Problem Statement

### Current Issues (As of Nov 5, 2025)

1. **Mixed Box-Drawing Styles** - Three different styles across the UI:
   - `┌─┐` (thin single) - Manual ASCII tables in dashboard.py
   - `╭─╮` (rounded) - Rich Tables in interactive.py
   - `┏━┓` (bold single) - Controls bar in dashboard.py

2. **Inconsistent Widths** - Sections vary between 80-120 characters

3. **Duplicate Table Code** - Manual ASCII tables scattered across files

4. **Spacing Chaos** - Variable blank lines and indentation

### Impact

Users report the interface looks "unprofessional" and "chaotic." The mixed styles create visual noise that distracts from the actual penetration testing data.

---

## Design Principles

### 1. **One Table Style, Everywhere**

**Decision:** Use Rich library with `box.SIMPLE` for ALL tables.

```
────────────────────────────────────────
 Column 1    Column 2    Column 3
────────────────────────────────────────
 Value 1     Value 2     Value 3
────────────────────────────────────────
```

**Rationale:**
- ✅ Clean, modern appearance
- ✅ No corner characters (less visual clutter)
- ✅ Consistent with tools like k9s, lazygit
- ✅ Rich library handles column sizing automatically
- ✅ Eliminates 500+ lines of manual ASCII table code

**Alternative Considered:** `box.MINIMAL` (even cleaner, no side borders)

---

### 2. **Visual Hierarchy**

```
╔══════════════════════════════════════════════════════════════╗
║ SOULEYEZ DASHBOARD │ Engagement: test      2025-11-05 01:32  ║  ← Level 0: App Header
╚══════════════════════════════════════════════════════════════╝

📊 SECTION TITLE                                                ← Level 1: Section
────────────────────────────────────────────────────────────    ← Level 1 separator

 Column 1    Column 2    Column 3                               ← Level 2: Content
────────────────────────────────────────────────────────────
 Value 1     Value 2     Value 3
────────────────────────────────────────────────────────────


🎯 NEXT SECTION                                                 ← 2 blank lines between
────────────────────────────────────────────────────────────
```

**Level Definitions:**

| Level | Purpose | Style | Usage |
|-------|---------|-------|-------|
| **0** | App header | `╔═╗` (double line, bold) | Dashboard header ONLY |
| **1** | Section title | Emoji + TITLE (bold) + `─` separator | Major sections |
| **2** | Content | Rich Tables (`box.SIMPLE`) | Data display |
| **3** | Sub-content | Plain text, 2-space indent | Details, notes |

---

### 3. **Consistent Width System**

**Rule:** All elements share the same width.

```python
# Get terminal width dynamically
width = DesignSystem.get_terminal_width()

# All elements use this width:
# - Headers
# - Separators
# - Tables (expand=True)
# - Controls bars
```

**Default:** 100 characters (safe for most terminals)
**Min:** 80 characters
**Max:** Terminal width (responsive)

---

### 4. **Spacing Rules**

```
[Section Title + Emoji]           ← Bold text
[Separator line]                  ← ─ repeated to width
[Blank line]                      ← 1 blank line after separator
[Content - Table or Text]         ← Rich Table or plain text
[Blank line]                      ← 1 blank line after content
[Blank line]                      ← 2 total blank lines between sections
[Next Section Title]
```

**Summary:**
- **After separator:** 1 blank line
- **After content:** 1 blank line
- **Between sections:** 2 blank lines total
- **Table rows:** No extra spacing (Rich handles this)

---

### 5. **Color & Emoji System**

#### Section Emojis (Visual Anchors)

| Emoji | Section | Purpose |
|-------|---------|---------|
| 📊 | Metrics/Stats | Tool metrics, data summaries |
| 🎯 | Targets/Hosts | Host lists, services |
| 🔍 | Findings | Vulnerabilities, discoveries |
| ⚡ | Jobs | Active scans, queue status |
| 🌐 | Web/Network | Endpoints, paths, DNS |
| 🔐 | Credentials | User accounts, passwords |
| 🔑 | Keys/Tokens | API keys, session tokens |

#### Status Colors (Rich Syntax)

```python
from rich.console import Console

# Severity levels
"[red]Critical[/red]"           # 🔴 Critical
"[yellow]High[/yellow]"         # 🟡 High
"[blue]Medium[/blue]"           # 🔵 Medium
"[green]Low[/green]"            # 🟢 Low
"[dim]Info[/dim]"               # ⚪ Info

# Job status
"[green]✓ done[/green]"         # Success
"[red]✗ error[/red]"            # Error
"[yellow]⟳ running[/yellow]"    # In progress
"[dim]○ pending[/dim]"          # Queued
```

---

## Implementation

### Architecture

**New Module:** `souleyez/ui/design_system.py`

This module provides:
- Centralized styling constants
- Helper functions for tables, separators, headers
- Terminal width detection
- Consistent Rich configuration

### DesignSystem Class

```python
from rich.table import Table
from rich import box
import os


class DesignSystem:
    """Centralized design system for SoulEyez UI."""

    # Box Styles
    HEADER_BOX = box.DOUBLE        # ╔═╗ - App header only
    TABLE_BOX = box.SIMPLE         # ─── - All tables

    # Widths
    DEFAULT_WIDTH = 100            # Default terminal width
    MIN_WIDTH = 80                 # Minimum supported width

    # Separators
    SECTION_SEP = "─"              # Section separator character

    # Spacing
    SECTION_SPACING = 2            # Blank lines between sections
    CONTENT_SPACING = 1            # Blank lines after separator

    @staticmethod
    def get_terminal_width():
        """Get current terminal width, fallback to DEFAULT_WIDTH."""
        try:
            width = os.get_terminal_size().columns
            return max(width, DesignSystem.MIN_WIDTH)
        except:
            return DesignSystem.DEFAULT_WIDTH

    @staticmethod
    def separator(width: int = None):
        """Generate section separator line."""
        w = width or DesignSystem.get_terminal_width()
        return DesignSystem.SECTION_SEP * w

    @staticmethod
    def create_table(expand=True, **kwargs):
        """
        Create a Rich Table with consistent styling.

        Args:
            expand: Fill terminal width (default: True)
            **kwargs: Additional Table() arguments

        Returns:
            Configured Rich Table instance
        """
        return Table(
            box=DesignSystem.TABLE_BOX,
            expand=expand,
            padding=(0, 1),
            show_header=True,
            header_style="bold",
            **kwargs
        )

    @staticmethod
    def section_header(emoji: str, title: str, width: int = None):
        """
        Render a section header with emoji and separator.

        Args:
            emoji: Section emoji (📊, 🎯, etc.)
            title: Section title (e.g., "TOOL METRICS")
            width: Terminal width (auto-detected if None)

        Returns:
            List of formatted lines
        """
        w = width or DesignSystem.get_terminal_width()
        lines = [
            f"{emoji} {title}",
            DesignSystem.SECTION_SEP * w,
            ""  # Blank line after separator
        ]
        return lines

    @staticmethod
    def blank_lines(count: int = 1):
        """Generate blank lines for spacing."""
        return [""] * count
```

---

### Migration Plan

#### Phase 1: Create DesignSystem Module ✅

1. Create `souleyez/ui/design_system.py`
2. Implement `DesignSystem` class
3. Write unit tests for helpers

#### Phase 2: Update Dashboard (dashboard.py) 🔄

**Functions to refactor:**

1. **`render_header()`** (lines ~81-136)
   - Replace `┌─┐` / `┏━┓` with Rich Panel using `box.DOUBLE`
   - Use `DesignSystem.get_terminal_width()`

2. **`render_new_tool_metrics()`** (lines ~144-285)
   - DELETE manual ASCII table (lines 248-281)
   - Replace with `DesignSystem.create_table()`
   - Use `DesignSystem.section_header()` for title

3. **`render_recent_hosts()`** (lines ~342-415)
   - DELETE manual ASCII table
   - Replace with Rich Table

4. **`render_critical_findings()`** (lines ~555-658)
   - DELETE manual ASCII table
   - Replace with Rich Table

5. **`render_top_ports()`** (lines ~659-729)
   - DELETE manual ASCII table
   - Replace with Rich Table

6. **`render_endpoints_and_redirects()`** (lines ~767-923)
   - Update to use `DesignSystem.TABLE_BOX`

**Global replacements:**
```bash
# Search for hardcoded separators
"─" * 102  → DesignSystem.separator()
"─" * 120  → DesignSystem.separator()
"──────..." → DesignSystem.separator()
```

#### Phase 3: Update Interactive Menu (interactive.py) 🔄

**Search for:** `box=box.ROUNDED` or `box.ROUNDED`

Replace with:
```python
from souleyez.ui.design_system import DesignSystem

# Before
table = Table(box=box.ROUNDED, ...)

# After
table = DesignSystem.create_table()
```

**Files to update:**
- Line ~1872: Jobs view
- Line ~3932: Findings view
- Line ~4519: Credentials view

#### Phase 4: Update Command Views 🔄

Check all CLI commands that render tables:
```bash
grep -r "from rich" souleyez/commands/
```

Standardize:
- `souleyez jobs list` - Use DesignSystem
- `souleyez findings list` - Use DesignSystem
- `souleyez creds list` - Use DesignSystem
- `souleyez hosts list` - Use DesignSystem

#### Phase 5: Testing ✅

Test every view:
- [ ] `souleyez dashboard` - Main dashboard
- [ ] `souleyez interactive` - Interactive menu
- [ ] `souleyez jobs list` - Jobs view
- [ ] `souleyez findings list` - Findings view
- [ ] `souleyez creds list` - Credentials view
- [ ] `souleyez hosts list` - Hosts view

**Visual checks:**
- [ ] All tables use same box style (no mixed `┌─┐` / `╭─╮`)
- [ ] All separators same width
- [ ] Consistent spacing between sections
- [ ] Terminal width responsive (test at 80, 100, 120 cols)
- [ ] No visual regressions

---

## Rich Box Style Reference

If `box.SIMPLE` doesn't meet requirements, here are alternatives:

### box.SIMPLE (Recommended)
```
────────────────────────────────────────
 Header
────────────────────────────────────────
 Row 1
 Row 2
────────────────────────────────────────
```
**Pros:** Clean, professional, no corners
**Cons:** None

---

### box.MINIMAL (Ultra-Clean)
```
 Header
────────────────────────────────────────
 Row 1
 Row 2
```
**Pros:** Minimalist, maximum content space
**Cons:** No top border (might look incomplete)

---

### box.MINIMAL_HEAVY_HEAD (Bold Header)
```
 Header
════════════════════════════════════════
 Row 1
 Row 2
```
**Pros:** Emphasizes headers
**Cons:** Mixed line weights (heavy + light)

---

### box.HORIZONTALS (Rows Only)
```
 Header
────────────────────────────────────────
 Row 1
────────────────────────────────────────
 Row 2
────────────────────────────────────────
```
**Pros:** Clear row separation
**Cons:** Verbose, lots of lines

---

### box.ROUNDED (Current - AVOID)
```
╭────────────────────────────────────────╮
│ Header                                 │
├────────────────────────────────────────┤
│ Row 1                                  │
│ Row 2                                  │
╰────────────────────────────────────────╯
```
**Pros:** Soft appearance
**Cons:** Too casual, inconsistent with rest of UI

---

### box.ASCII (Old Style - AVOID)
```
┌────────────────────────────────────────┐
│ Header                                 │
├────────────────────────────────────────┤
│ Row 1                                  │
│ Row 2                                  │
└────────────────────────────────────────┘
```
**Pros:** Terminal compatible
**Cons:** Manual maintenance nightmare, Rich handles this better

---

## Before → After Examples

### Dashboard Header

**BEFORE (Inconsistent):**
```
┌────────────────────────────────────────────────────────┐
│ SOULEYEZ DASHBOARD │ Engagement: test    2025-11-05    │
└────────────────────────────────────────────────────────┘
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ [m] Menu [j] Jobs [q] Quit                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

**AFTER (Consistent):**
```
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║ SOULEYEZ DASHBOARD │ Engagement: test                                          2025-11-05 01:32  ║
║ 📊 Hosts: 3 │ Services: 2 │ Findings: 0 │ [m] Menu [j] Jobs [q] Quit                           ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

### Tool Metrics Section

**BEFORE (Manual ASCII + Mixed Styles):**
```
📊 TOOL METRICS
──────────────────────────────────────────────────────────────  (102 chars)
  ┌──────────────────────────────┬────────────────┐
  │ Tool                         │ Count          │
  ├──────────────────────────────┼────────────────┤
  │ Nmap                         │ 3              │
  │ Gobuster                     │ 0              │
  └──────────────────────────────┴────────────────┘
```

**AFTER (Rich Table + Consistent):**
```
📊 TOOL METRICS
──────────────────────────────────────────────────────────────────────────────────────────────────

 Tool                          Data Type                Count
────────────────────────────────────────────────────────────────────────────────────────────────
 Nmap                          Hosts                        3
 Gobuster                      Web Paths                    0
────────────────────────────────────────────────────────────────────────────────────────────────
```

---

### Jobs Queue

**BEFORE (Rounded + Inconsistent Width):**
```
╭──────────────────┬─────────────────────────┬──────────────╮
│               ID │ Status                  │ Tool         │
├──────────────────┼─────────────────────────┼──────────────┤
│                5 │ ✓ done                  │ nmap         │
╰──────────────────┴─────────────────────────┴──────────────╯
```

**AFTER (Simple + Full Width):**
```
⚡ ACTIVE JOBS
──────────────────────────────────────────────────────────────────────────────────────────────────

 ID     Status     Tool        Target         Label         Created
──────────────────────────────────────────────────────────────────────────────────────────────────
 5      ✓ done     nmap        10.0.0.28      FULL          2025-11-05T05:43
──────────────────────────────────────────────────────────────────────────────────────────────────
```

---

## Benefits

### Developer Experience
- **Less code:** Eliminate 500+ lines of manual ASCII table logic
- **Faster development:** `DesignSystem.create_table()` vs manual borders
- **Easier maintenance:** Change ONE constant to update entire UI

### User Experience
- **Professional appearance:** Consistent, clean interface
- **Predictable layout:** Users know what to expect
- **Better focus:** Less visual noise, more attention on data

### Performance
- **No impact:** Rich tables are fast (used by millions)
- **Terminal-friendly:** Works on all modern terminals

---

## Migration Checklist

- [ ] Create `souleyez/ui/design_system.py`
- [ ] Write unit tests for DesignSystem helpers
- [ ] Update `dashboard.py` (6 functions)
- [ ] Update `interactive.py` (4 instances)
- [ ] Update command views (`jobs`, `findings`, `creds`, `hosts`)
- [ ] Test all views (8 views × 3 terminal widths = 24 tests)
- [ ] Visual QA pass (no regressions)
- [ ] Update screenshots in docs (if any)
- [ ] Delete old ASCII table helper code

---

## FAQ

**Q: Why not keep rounded corners (`box.ROUNDED`)?**
A: Rounded corners look "soft" but aren't professional for security tools. `box.SIMPLE` is cleaner and more consistent with industry-standard CLI tools (kubectl, gh, etc).

**Q: What if users prefer the old style?**
A: Consistency > personal preference. A unified design system is a core requirement for professional software. Users will adapt quickly.

**Q: Can we make box style configurable?**
A: Not recommended. Configuration options create maintenance burden and defeat the purpose of a design system. ONE style for ALL views.

**Q: What about terminals that don't support UTF-8?**
A: Rich automatically falls back to ASCII mode on incompatible terminals. This is handled transparently.

**Q: How do we handle wide data (long URLs, file paths)?**
A: Rich Tables support:
- Truncation with ellipsis (`overflow="ellipsis"`)
- Word wrapping (`overflow="fold"`)
- Horizontal scrolling (future enhancement)

---

## References

- [Rich Library Docs](https://rich.readthedocs.io/)
- [Rich Box Styles](https://rich.readthedocs.io/en/latest/appendix/box.html)
- [Terminal UI Best Practices](https://clig.dev/)

---

**Status:** Ready for implementation
**Owner:** Gambino (implementation), Doc (architecture)
**Approval Required:** y0d8 (product owner)
