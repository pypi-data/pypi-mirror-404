# AI Integration Guide

SoulEyez integrates with AI providers to enable **intelligent attack recommendations**, **autonomous execution**, and **AI-enhanced reports**. Choose between local privacy-first AI (Ollama) or cloud-based quality AI (Claude).

## Table of Contents

1. [Overview](#overview)
2. [AI Providers](#ai-providers)
3. [Configuration](#configuration)
4. [AI-Driven Execution](#ai-driven-execution)
5. [AI-Enhanced Reports](#ai-enhanced-reports)
6. [Privacy Considerations](#privacy-considerations)
7. [Keyboard Shortcuts](#keyboard-shortcuts)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What Can AI Do in SoulEyez?

| Feature | Description |
|---------|-------------|
| **Attack Recommendations** | AI analyzes your engagement and suggests next steps |
| **Autonomous Execution** | AI executes recommended scans with safety controls |
| **Enhanced Reports** | AI generates executive summaries and remediation plans |
| **Finding Enhancement** | AI adds business context to technical findings |

### Provider Comparison

| Feature | Ollama (Local) | Claude (Cloud) |
|---------|----------------|----------------|
| **Privacy** | Data stays on your machine | Data sent to Anthropic API |
| **Quality** | Good (depends on model) | Excellent |
| **Speed** | Depends on hardware | Fast |
| **Cost** | Free | API costs apply |
| **Offline** | Works offline | Requires internet |

---

## AI Providers

### Ollama (Local AI)

Ollama runs AI models locally on your machine. **No data leaves your system**.

**Recommended for:**
- Client engagements with strict data handling requirements
- Offline environments
- Cost-sensitive usage

**Supported Models:**
- `llama3.1:8b` - Recommended, balanced performance
- `llama3.2:1b` - Lightweight, faster
- `mistral` - Fast, general purpose
- `codellama` - Code-focused tasks

### Claude (Cloud AI)

Claude is Anthropic's cloud AI service, offering superior quality for complex analysis.

**Recommended for:**
- Executive summaries requiring polish
- Complex remediation planning
- When quality matters more than privacy

**Models:**
- `claude-sonnet-4-20250514` - Default, balanced
- `claude-opus-4-5-20251101` - Highest quality

---

## Configuration

### Quick Setup

1. Go to **Settings & Security** → **AI Settings**
2. Choose your provider:
   - **[1] Switch Provider** - Toggle between Ollama and Claude
   - **[2] Ollama Settings** - Configure local model
   - **[3] Claude Settings** - Set up API key

### Ollama Setup

1. Install Ollama: https://ollama.ai
2. Start the service:
   ```bash
   ollama serve
   ```
3. Pull a model:
   ```bash
   ollama pull llama3.1:8b
   ```
4. In SoulEyez: **Settings → AI Settings → Ollama Settings**

### Local Network Ollama Setup

Run Ollama on another machine on your local network (e.g., a Mac with Apple Silicon GPU):

**On the Ollama host machine:**
```bash
# Start Ollama listening on all interfaces
OLLAMA_HOST=0.0.0.0 ollama serve
```

**In SoulEyez (CLI):**
```bash
souleyez config set ai.ollama_url http://10.0.0.28:11434
```

**In SoulEyez (Menu):**
1. Go to **Settings → AI Settings → Ollama Settings**
2. Press **[u]** for Network Settings
3. Enter the machine's IP (e.g., `10.0.0.28:11434`)

**Verify connection:**
```bash
curl http://10.0.0.28:11434/api/tags
```

**Security:** Only private network IPs are allowed (10.x.x.x, 192.168.x.x, 172.16-31.x.x). Public internet IPs are blocked to prevent accidental data exfiltration.

### Claude Setup

1. Get API key from: https://console.anthropic.com
2. In SoulEyez: **Settings → AI Settings → Claude Settings**
3. Enter your API key (stored encrypted)
4. Test connection

### Quick Toggle

From the Command Center dashboard, press **`a`** to quickly toggle between providers:

```
AI Providers:          Ollama (llama3.1:8b) ◀, Claude ✓ Ready
                       [Press 'a' to toggle provider, 'x' for AI Execute]
```

---

## AI-Driven Execution

### What is AI Execute?

AI Execute analyzes your current engagement and:
1. Reviews discovered hosts, services, and findings
2. Identifies gaps in your testing coverage
3. Recommends specific tools and commands
4. Executes approved recommendations automatically

### How to Use

1. From Command Center, press **`x`** for AI Execute
2. Select your AI provider (or use default)
3. Choose approval mode:
   - **Auto-approve** - AI executes without confirmation
   - **Confirm each** - Approve each action individually
4. AI analyzes and executes recommendations

### Safety Controls

| Control | Description |
|---------|-------------|
| **Approval Mode** | Choose auto or manual approval |
| **Scope Limits** | AI only targets engagement hosts |
| **Tool Whitelist** | Only approved pentesting tools |
| **Rate Limiting** | Prevents overwhelming targets |

---

## AI-Enhanced Reports

### Features

| Feature | Description |
|---------|-------------|
| **Executive Summary** | Business-focused overview of findings |
| **Finding Enhancement** | Adds business impact to technical findings |
| **Remediation Plan** | Prioritized action items |
| **Risk Rating** | Overall engagement risk assessment |

### Generating AI Reports

1. Go to **Reports** menu
2. Select report type
3. Enable **AI Enhancement** option
4. Choose AI provider
5. Generate report

### Report Sections

**Executive Summary:**
- High-level risk overview
- Key findings summary
- Business impact assessment
- Recommended priorities

**Enhanced Findings:**
- Technical details + business context
- Attack scenarios
- Risk implications

**Remediation Plan:**
- Prioritized by severity and impact
- Estimated effort levels
- Quick wins vs long-term fixes

---

## Privacy Considerations

### Data Handling by Provider

| Provider | What's Sent | Storage |
|----------|-------------|---------|
| **Ollama** | Nothing leaves your machine | Local only |
| **Claude** | Engagement data, findings, host info | Anthropic servers |

### When to Use Each Provider

**Use Ollama when:**
- Client has strict data handling requirements
- Working with classified/sensitive targets
- No internet access available
- Cost is a concern

**Use Claude when:**
- Need highest quality output
- Generating client-facing reports
- Complex analysis required
- Data sharing is acceptable

### Privacy Warning

When switching to Claude, SoulEyez displays:
```
⚠️  Data will be sent to Anthropic's API
```

---

## Keyboard Shortcuts

### Command Center

| Key | Action |
|-----|--------|
| `a` | Toggle AI provider (Ollama ↔ Claude) |
| `x` | AI-Driven Execution |
| `r` | Reports menu (includes AI options) |

### During AI Execution

| Key | Action |
|-----|--------|
| `y` | Approve recommendation |
| `n` | Skip recommendation |
| `q` | Quit AI execution |

---

## Troubleshooting

### Ollama Issues

**"Ollama not running"**
```bash
# Start Ollama service
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

**"Model not found"**
```bash
# List available models
ollama list

# Pull required model
ollama pull llama3.1:8b
```

**Slow performance**
- Use smaller model: `llama3.2:1b` or `mistral`
- Check system resources (RAM, CPU)
- Close other applications

### Claude Issues

**"API key not configured"**
1. Go to Settings → AI Settings → Claude Settings
2. Unlock vault (if locked)
3. Enter API key

**"Connection failed"**
- Check internet connection
- Verify API key is valid
- Check Anthropic service status

**"Rate limited"**
- Wait a few minutes
- Check API usage limits at console.anthropic.com

### General Issues

**"No AI providers available"**
- Ensure Ollama is running, OR
- Configure Claude API key

**AI recommendations seem off**
- Update to latest Ollama model
- Try Claude for better quality
- Ensure engagement has sufficient data

---

## Best Practices

1. **Start with Ollama** for initial testing, switch to Claude for reports
2. **Review AI recommendations** before auto-approving
3. **Use Claude for client-facing** executive summaries
4. **Keep Ollama as fallback** for offline/sensitive work
5. **Monitor API costs** if using Claude extensively

---

## CLI Commands

```bash
# Check AI status
souleyez ai status

# Initialize AI (pull model)
souleyez ai init

# Get recommendations
souleyez ai recommend

# Execute with AI
souleyez ai execute

# Generate AI report
souleyez reports generate --ai-enhanced

# Configure AI settings (local network Ollama)
souleyez config set ai.ollama_url http://10.0.0.28:11434
souleyez config set ai.ollama_model llama3.1:8b
souleyez config set ai.provider ollama

# View AI settings
souleyez config get ai.ollama_url
souleyez config list
```

---

## Related Documentation

- [Auto-Chaining Guide](auto-chaining.md) - Automated tool workflows
- [Configuration Guide](configuration.md) - All settings options
- [Keyboard Shortcuts Reference](shortcuts.md) - All hotkeys
