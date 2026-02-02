# ADR-001: Local LLM (Ollama) Over Cloud AI Services

**Status**: Accepted
**Date**: 2025-10-29
**Deciders**: Aliyeh (CEO), Jr (CISO/Lead Engineer), CyberSoul Security Leadership
**Project**: SoulEyez Platform

---

## Context

SoulEyez's core value proposition includes **AI-powered attack path intelligence** to help penetration testers visualize next steps and understand complex engagement data. This is a key differentiator in the Pro tier ($79/month) and Enterprise tier ($299/month).

The critical decision: **Where does the AI run?**

Options:
1. **Cloud AI** (OpenAI GPT-4, Anthropic Claude, Google Gemini)
2. **Local LLM** (Ollama + Llama 3.1, run on user's machine)
3. **Hybrid** (Cloud for Pro, Local for Enterprise)

This decision impacts:
- **Privacy/Compliance**: Pentesting data is highly sensitive
- **Cost Structure**: Cloud API costs vs. compute requirements
- **User Experience**: Response time, reliability, offline capability
- **Competitive Position**: Privacy-first positioning vs. bleeding-edge AI

---

## Decision

**SoulEyez will use LOCAL LLM (Ollama + Llama 3.1 8B) for all AI features.**

### Implementation Details

**Technology Stack**:
- **Model**: Llama 3.1 8B (Meta's open-source model)
- **Runtime**: Ollama (local LLM server)
- **Minimum Requirements**: 8GB RAM, CPU inference (GPU optional)
- **Deployment**: User installs Ollama locally, SoulEyez connects via API

**Architecture**:
```
SoulEyez CLI/Dashboard
       ↓
   Local API call (localhost:11434)
       ↓
   Ollama Server (user's machine)
       ↓
   Llama 3.1 8B Model
       ↓
   Attack path suggestions, finding summaries
```

---

## Rationale

### Why Local LLM Over Cloud AI?

#### 1. Privacy & Compliance (CRITICAL FOR PENTESTING)

**Pentesting data is HIGHLY sensitive**:
- Client IP addresses, network topology
- Discovered credentials (even if encrypted at rest)
- Vulnerability details and exploitation paths
- Business-critical systems exposure

**Cloud AI Risk**:
❌ Sending this data to OpenAI/Anthropic violates:
- Most client NDAs (explicit "no third-party sharing" clauses)
- Compliance frameworks (PCI-DSS 3.4, HIPAA, SOC 2)
- Government/DoD contracts (FedRAMP, NIST 800-171)

**Example Scenario**:
```
Pentester discovers:
- admin:P@ssw0rd123 on client's production database
- Sends to Cloud AI: "Analyze this credential strength"
- Cloud provider logs request (per their TOS)
- Client's admin password now in third-party logs
→ NDA violation, potential data breach notification required
```

**Local LLM Win**:
✅ **Zero data exfiltration** - Everything stays on pentester's laptop
✅ **Compliance-friendly** - Meets strictest client requirements
✅ **Competitive advantage** - "Privacy-first AI" positioning

#### 2. Cost Structure (SUSTAINABLE ECONOMICS)

**Cloud AI Costs**:
- OpenAI GPT-4: $0.03 per 1K input tokens, $0.06 per 1K output tokens
- Anthropic Claude: $0.015 per 1K input tokens, $0.075 per 1K output tokens

**Per-User Analysis**:
```
Typical engagement (1 week):
- 500 API calls for attack path suggestions
- Average 1K tokens input + 500 tokens output per call
- Cost per user per engagement: $30-50

With 50 Pro users ($79/mo):
- Monthly API costs: $1,500 - $2,500
- 32-50% of revenue consumed by AI costs
```

**Local LLM Costs**:
- One-time development: ~40 hours integration
- Per-user cost: $0 (user's compute)
- Scales to 1000+ users with zero marginal cost

**Economic Impact**:
```
Year 1 with 50 Pro users:
- Cloud AI: $18,000 - $30,000 in API costs
- Local LLM: $0 ongoing costs
- Savings: $18,000 - $30,000 (46% margin improvement)
```

#### 3. Offline Operation (FIELD WORK COMPATIBILITY)

Pentesters often work in:
- Air-gapped environments (client networks with no internet)
- Remote locations (poor connectivity)
- Secure facilities (no external API access allowed)

**Cloud AI**: ❌ Requires internet connection, fails in these scenarios

**Local LLM**: ✅ Fully functional offline

**Real-World Use Case**:
> "I'm testing a client's internal network. No external internet access. I still need AI guidance on which lateral movement paths to explore."

#### 4. Response Time & Reliability

**Cloud AI**:
- Network latency: 200-500ms
- API rate limits (requests per minute)
- Downtime risk (OpenAI outages happen)
- Dependent on user's internet quality

**Local LLM**:
- Latency: 50-100ms (localhost call)
- No rate limits
- 100% uptime (if user's machine is on)
- Consistent performance

**User Experience**:
- Cloud: "Waiting for AI response... (spinning)"
- Local: "Instant suggestions appear as you work"

#### 5. Brand Differentiation

**Market Positioning**:

SoulEyez's tagline: *"See through the soul's eyes — perceive what others cannot."*

**Competitive Analysis**:

| Competitor | AI Strategy | Privacy |
|------------|-------------|---------|
| BurpSuite Pro | No AI features | N/A |
| Intruder.io | Cloud AI (scanning intel) | Data sent to cloud |
| ProjectDiscovery Nuclei | No AI | N/A |
| **SoulEyez** | **Local AI** | **100% private** |

**Messaging Opportunity**:
> "SoulEyez AI never sends your data to the cloud. Your engagement stays between you and your client — always."

This positions CyberSoul as **security-first, privacy-respecting** — aligned with SoulEyez brand values.

---

## Alternatives Considered

### Alternative 1: Cloud AI (OpenAI GPT-4 / Anthropic Claude)

**Pros**:
- ✅ Best-in-class AI quality (most accurate suggestions)
- ✅ No local compute requirements
- ✅ Regular model improvements (automatic)
- ✅ Fastest time-to-market (API integration easy)

**Cons**:
- ❌ **Privacy violation** (client data sent externally)
- ❌ 32-50% revenue consumed by API costs
- ❌ Requires internet (fails in air-gapped environments)
- ❌ Rate limits and downtime risk
- ❌ Vendor lock-in (OpenAI changes pricing, TOS)
- ❌ Compliance violations (PCI-DSS, HIPAA, FedRAMP)

**Verdict**: **Rejected** - Privacy concerns are disqualifying for pentesting use case.

---

### Alternative 2: Hybrid Approach (Cloud for Pro, Local for Enterprise)

**Idea**:
- Pro tier ($79/mo): Cloud AI (user accepts privacy risk)
- Enterprise tier ($299/mo): Local AI (privacy guaranteed)

**Pros**:
- ✅ Lower compute requirements for Pro users
- ✅ Best AI quality for majority of users
- ✅ Privacy option for enterprise customers

**Cons**:
- ❌ **Splits codebase** (two AI integrations to maintain)
- ❌ **Confusing messaging** ("Pro is less private?")
- ❌ **Support burden** (troubleshoot both systems)
- ❌ **Ethics concern** (encouraging users to violate client NDAs)
- ❌ Still incurs cloud costs for majority of users

**Verdict**: **Rejected** - Undermines "privacy-first" positioning, creates operational complexity.

---

### Alternative 3: No AI Features

**Idea**: Focus on deterministic tool orchestration, skip AI entirely.

**Pros**:
- ✅ Simplest implementation
- ✅ No privacy concerns
- ✅ No compute requirements
- ✅ Fully deterministic results

**Cons**:
- ❌ **Removes core differentiator** (project plan's "AI attack path intelligence")
- ❌ **Pricing justification weakens** (why pay $79/mo without AI?)
- ❌ **Competitive disadvantage** (competitors will add AI)
- ❌ **Misses market trend** (AI-augmented tools are the future)

**Verdict**: **Rejected** - AI features are central to SoulEyez's value proposition and Pro tier pricing.

---

### Alternative 4: Privacy-Preserving Cloud AI (Anonymized Data)

**Idea**: Strip sensitive data before sending to cloud AI.

**Example**:
```
Original: "admin:password123 on 10.0.0.5 port 3306 MySQL"
Sanitized: "[USER]:[PASS] on [IP] port 3306 MySQL"
```

**Pros**:
- ✅ Reduces (but doesn't eliminate) privacy risk
- ✅ Allows cloud AI quality
- ✅ Lower compute requirements

**Cons**:
- ❌ **AI quality degrades** (context loss from anonymization)
- ❌ **Not fully compliant** (metadata leakage: "client has MySQL on port 3306")
- ❌ **Complex to implement correctly** (easy to miss sensitive data)
- ❌ **Still costs money** (API fees)
- ❌ **User trust issue** ("How do I know it's really anonymized?")

**Verdict**: **Rejected** - Partial privacy is not sufficient for pentesting data. Complexity outweighs benefits.

---

## Consequences

### Positive

1. **Privacy & Compliance**
   - ✅ Zero data exfiltration
   - ✅ Meets strictest client NDA requirements
   - ✅ Passes compliance audits (PCI-DSS, HIPAA, FedRAMP)
   - ✅ Competitive advantage ("Only privacy-first AI pentesting platform")

2. **Economics**
   - ✅ $0 marginal cost per user
   - ✅ 46% margin improvement vs. cloud AI
   - ✅ Pricing power (can charge for AI features without paying OpenAI)

3. **User Experience**
   - ✅ Works offline (air-gapped environments)
   - ✅ Low latency (localhost calls)
   - ✅ No rate limits
   - ✅ Predictable performance

4. **Brand**
   - ✅ Reinforces "SoulEyez" identity (ethical, privacy-respecting)
   - ✅ Differentiation in crowded market
   - ✅ Thought leadership opportunity (blog: "Why We Built Privacy-First AI")

### Negative

1. **Compute Requirements**
   - ❌ Users need 8GB+ RAM (minimum)
   - ❌ GPU recommended for speed (but not required)
   - ❌ Installation complexity (user must install Ollama)
   - ❌ May not run on low-end laptops

2. **AI Quality**
   - ❌ Llama 3.1 8B is good, but not GPT-4 quality
   - ❌ No automatic model improvements (we control updates)
   - ❌ Domain-specific training required (pentesting knowledge)

3. **Development Effort**
   - ❌ More complex than cloud API integration
   - ❌ Need to handle Ollama installation/configuration
   - ❌ Model prompt engineering required
   - ❌ Testing across different hardware configurations

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **User's machine too slow** | Document minimum requirements; offer CPU-optimized models; show loading states |
| **Ollama installation failure** | Provide step-by-step guides; offer Docker alternative; one-click installers |
| **AI suggestions inaccurate** | Clearly label as "suggestions" not "facts"; allow user feedback to improve prompts |
| **Model security concerns** | Use official Llama models only; verify checksums; sandboxed execution |
| **Competitors use better AI** | Differentiates on privacy, not raw AI quality; iterate on prompt engineering |

---

## Implementation Plan

### Phase 3: AI Intelligence (Nov 4 - Jan 31, 2026)

**Week 1-2: Ollama Integration**
- [ ] Install and test Ollama locally
- [ ] Create Python client for Ollama API
- [ ] Design prompt templates for attack path suggestions

**Week 3-4: Core AI Features**
- [ ] Finding summarization ("What's important here?")
- [ ] Next-step recommendations ("What should I try next?")
- [ ] Credential strength analysis

**Week 5-6: Prompt Engineering**
- [ ] Test with real engagement data
- [ ] Refine prompts for accuracy
- [ ] Implement context window management (8K token limit)

**Week 7-8: UX Integration**
- [ ] Add AI panel to dashboard
- [ ] CLI command: `souleyez suggest`
- [ ] Loading states and error handling

**Week 9-10: Documentation & Testing**
- [ ] User guide: Installing Ollama
- [ ] Model selection guidance (8B vs 70B)
- [ ] Performance benchmarks

**Week 11-12: Pro Tier Gating**
- [ ] Stripe billing integration
- [ ] Feature flag for AI capabilities
- [ ] "Upgrade to Pro" prompts

---

## Technical Specifications

### Model Selection

**Primary Model**: Llama 3.1 8B Instruct
- Parameters: 8 billion
- Context window: 8,192 tokens
- RAM requirement: 8GB minimum
- Inference speed: 5-10 tokens/sec (CPU), 30-50 tokens/sec (GPU)
- License: Meta's Llama Community License (commercial use allowed)

**Optional Upgrade**: Llama 3.1 70B Instruct (for users with 64GB+ RAM)

### Prompt Template Example

```python
ATTACK_PATH_PROMPT = """
You are an expert penetration tester assistant. Given the following engagement data, suggest the next logical step.

Discovered Services:
{services_json}

Credentials Found:
{credentials_json}

Findings So Far:
{findings_json}

Provide:
1. Top 3 attack paths to explore
2. Reasoning for each path
3. Specific commands to run

Be concise and actionable.
"""
```

### API Integration

```python
import ollama

def get_attack_suggestions(engagement_data):
    prompt = format_prompt(engagement_data)

    response = ollama.chat(
        model='llama3.1:8b',
        messages=[
            {'role': 'system', 'content': 'You are a penetration testing assistant.'},
            {'role': 'user', 'content': prompt}
        ],
        options={
            'temperature': 0.3,  # Lower = more deterministic
            'top_p': 0.9
        }
    )

    return response['message']['content']
```

---

## Success Metrics (Phase 3 Completion)

| Metric | Target |
|--------|--------|
| **AI Response Time** | < 5 seconds (95th percentile) |
| **AI Error Rate** | < 2% (hallucinations, crashes) |
| **User Satisfaction (AI)** | NPS ≥ 8 for AI features |
| **Installation Success** | ≥ 90% install Ollama successfully |
| **Pro Conversion** | 10% of free users upgrade for AI |

---

## Future Considerations

### Fine-Tuning on Pentesting Data

**When**: Q2 2026 (after initial launch)

**Approach**:
- Collect anonymized engagement data (opt-in)
- Fine-tune Llama 3.1 on CVE descriptions, MITRE ATT&CK, exploit-db
- Create "SoulEyez-tuned" model for better pentesting suggestions

### GPU Acceleration

**When**: Q3 2026 (if user feedback indicates slowness)

**Options**:
- Offer pre-configured Docker images with GPU support
- Cloud GPU rental for Pro users (hybrid approach)
- Optimize prompts to reduce token count (faster inference)

### Multi-Model Support

**When**: Q4 2026 (if users request it)

**Allow users to choose**:
- Llama 3.1 (default)
- Mistral 7B (faster, less accurate)
- Mixtral 8x7B (higher quality, more RAM)
- User's own custom model

---

## Related Decisions

- [ADR-002: Master Password Approach](002-master-password-approach.md) - Privacy-first security
- [ADR-003: SQLite Database Choice](003-database-schema-design.md) - Local-first architecture

---

## References

- Llama 3.1 Model Card: https://ai.meta.com/blog/meta-llama-3-1/
- Ollama Documentation: https://ollama.ai/docs
- OWASP LLM Security: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- PCI-DSS 3.4 (Credential Encryption): https://www.pcisecuritystandards.org/

---

**Authors**: Aliyeh (CEO), Jr (CISO/Lead Engineer), CyberSoul Security
**Last Updated**: 2025-10-29
**Review Date**: March 2026 (post-Phase 3 completion)
