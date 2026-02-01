# Screenshots Guide

This directory contains screenshots for the SoulEyez documentation.

## Required Screenshots for Getting Started Guide

### 1. Main Menu (`main-menu.png`)
**How to capture:**
```bash
souleyez interactive
```
**What to show:**
- Full main menu with all options visible
- Highlight the menu choices:
  - [e] Engagement Management
  - [s] Scanning & Enumeration
  - [d] Data Management
  - [j] Job Management
  - [q] Quit

**Used in:** `docs/user-guide/getting-started.md` - Step 1

---

### 2. Engagement Creation (`engagement-create.png`)
**How to capture:**
```bash
souleyez interactive
# Press [e] → [c]
```
**What to show:**
- Engagement creation form
- Name field: "ACME Corp Assessment"
- Description field: "Internal network security assessment"
- Show the input prompts

**Used in:** `docs/user-guide/getting-started.md` - Step 2

---

### 3. Scan Configuration (`scan-config.png`)
**How to capture:**
```bash
souleyez interactive
# Press [s] → [n]
```
**What to show:**
- Nmap scan preset selection screen
- Available presets (Quick Scan, Full Scan, etc.)
- Target input field showing "192.168.1.0/24"
- Confirmation prompt

**Used in:** `docs/user-guide/getting-started.md` - Step 3

---

### 4. Job List (`job-list.png`)
**How to capture:**
```bash
souleyez interactive
# Press [j] after running a scan
```
**What to show:**
- List of jobs with various statuses:
  - 🟢 Running job
  - ✅ Completed job
  - ⏸️ Queued job (if possible)
- Job details: ID, tool name, target, status, timestamp

**Used in:** `docs/user-guide/getting-started.md` - Step 4

---

### 5. Hosts List (`hosts-list.png`)
**How to capture:**
```bash
souleyez interactive
# Press [d] → [h] after scan completes
```
**What to show:**
- List of discovered hosts
- Host IP addresses
- Hostnames (if resolved)
- Number of open ports
- Status indicators

**Used in:** `docs/user-guide/getting-started.md` - Step 5

---

## Optional Screenshots for Advanced Documentation

### 6. Credentials Management (`credentials-list.png`)
**How to capture:**
```bash
souleyez interactive
# Press [d] → [c]
```
**What to show:**
- List of discovered credentials
- Masked passwords (••••••••)
- Service types (SSH, FTP, HTTP, etc.)
- Associated hosts

---

### 7. Findings List (`findings-list.png`)
**How to capture:**
```bash
souleyez interactive
# Press [d] → [f]
```
**What to show:**
- Vulnerabilities organized by severity
- Severity color coding (Critical, High, Medium, Low)
- Finding titles and descriptions
- Associated hosts

---

### 8. Password Cracking Menu (`hashcat-menu.png`)
**How to capture:**
```bash
souleyez interactive
# Press [d] → [c] → [c]
```
**What to show:**
- Hashcat configuration screen
- Hash file selection
- Hash type presets
- Wordlist selection

---

## Screenshot Guidelines

### Format
- **File format:** PNG (preferred for terminal screenshots)
- **Resolution:** At least 1280x720
- **Terminal size:** 80x24 or larger for readability

### Capture Tools

**Linux/Kali:**
```bash
# Using gnome-screenshot
gnome-screenshot -a

# Using scrot
scrot -s screenshot.png

# Using imagemagick
import screenshot.png
```

**Terminal-specific:**
```bash
# For tmux users
tmux capture-pane -p > screenshot.txt
# Then convert to image if needed
```

### Styling Tips
- Use a clean terminal theme (dark background recommended)
- Ensure text is clearly readable
- Crop unnecessary whitespace
- Show full context (don't cut off important UI elements)
- Use realistic data (but sanitize sensitive info!)

---

## Naming Convention

- Use lowercase with hyphens: `main-menu.png`
- Be descriptive: `engagement-create.png` not `screen1.png`
- Group related screenshots: `job-list-running.png`, `job-list-completed.png`

---

## Adding Screenshots to Documentation

Once you've captured screenshots, update the getting-started.md file by uncommenting the image lines:

Change:
```markdown
<!-- TODO: Add screenshot of main menu here -->
<!-- ![SoulEyez Main Menu](../images/main-menu.png) -->
<!-- *The interactive main menu provides easy access to all features* -->
```

To:
```markdown
![SoulEyez Main Menu](../images/main-menu.png)
*The interactive main menu provides easy access to all features*
```

---

## Checklist

- [ ] main-menu.png
- [ ] engagement-create.png
- [ ] scan-config.png
- [ ] job-list.png
- [ ] hosts-list.png
- [ ] credentials-list.png (optional)
- [ ] findings-list.png (optional)
- [ ] hashcat-menu.png (optional)

---

**Last Updated:** 2025-11-03  
**Maintainer:** y0d8
