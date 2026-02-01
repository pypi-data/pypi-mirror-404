# ADR-XXX: [Short Title of Decision]

**Status**: [Proposed | Accepted | Deprecated | Superseded]
**Date**: YYYY-MM-DD
**Deciders**: [List of people involved]
**Supersedes**: [ADR-XXX if applicable] or None

---

## Context

[Describe the problem or challenge that requires a decision. Include:]
- What situation are we facing?
- What constraints exist (technical, business, regulatory)?
- What triggered this decision?
- What are the key requirements?

**Example**:
> souleyez needs to store discovered credentials securely. We must balance security (encryption at rest) with usability (no complex key management). The tool is used by individual penetration testers on their own workstations.

---

## Decision

[State the decision clearly and concisely. Use bold text for emphasis.]

**Example**:
> **souleyez will use master password-based encryption with PBKDF2 + Fernet symmetric encryption.**

### Key Design Choices

[List the main components of the decision]

1. **Component 1**: Description
2. **Component 2**: Description
3. **Component 3**: Description

---

## Rationale

[Explain WHY this decision was made. This is the most important section.]

### Why This Approach?

[Explain the reasoning, benefits, and how it solves the problem]

#### Compared to Alternative 1

**Pros**:
- ✅ Benefit 1
- ✅ Benefit 2

**Cons**:
- ❌ Drawback 1
- ❌ Drawback 2

**Decision**: [Accept/Reject] - [Brief reasoning]

#### Compared to Alternative 2

[Same structure as above]

---

## Consequences

[Document the expected outcomes, both positive and negative]

### Positive

[What benefits does this decision bring?]

1. **Benefit 1**: Description
2. **Benefit 2**: Description
3. **Benefit 3**: Description

### Negative

[What drawbacks or limitations exist?]

1. **Limitation 1**: Description
2. **Limitation 2**: Description

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| **Risk 1** | How we address it |
| **Risk 2** | How we address it |

---

## Alternatives Considered

[Document alternatives that were evaluated but rejected]

### 1. Alternative Name

**Idea**: Brief description

**Pros**:
- Advantage 1
- Advantage 2

**Cons**:
- Disadvantage 1
- Disadvantage 2

**Verdict**: **Rejected** - Reasoning

### 2. Another Alternative

[Same structure as above]

---

## Future Considerations

[What might change this decision in the future?]

**Possible Future Changes**:
- If X happens, we should reconsider Y
- When user base grows to Z, reevaluate this approach

**Decision Point**: When to revisit (e.g., "Revisit if users request X in 3+ GitHub issues")

---

## Related Decisions

[Link to related ADRs]

- [ADR-XXX: Related Decision](xxx-related-decision.md) - How they relate

---

## References

[External resources, documentation, standards]

- Link 1: Description
- Link 2: Description
- Research paper / RFC / Standard

---

## Notes

[Optional section for additional context, discussions, or historical notes]

**Implementation Details**:
- File locations
- Key functions/classes
- Configuration options

**Discussion Summary**:
- Date: Key points from team discussion
- Date: Follow-up decisions

---

**Authors**: [Names]
**Last Updated**: YYYY-MM-DD
**Reviewers**: [Names if applicable]

---

## Template Usage Instructions

1. **Copy this template**: `cp 000-template.md 00X-your-decision.md`
2. **Replace XXX with next number**: Check existing ADRs for numbering
3. **Fill in all sections**: Don't leave placeholders
4. **Use consistent formatting**: Match style of existing ADRs
5. **Link from docs/README.md**: Add entry to ADR index
6. **Commit with descriptive message**: `git add docs/adr/00X-*.md && git commit -m "docs: Add ADR-00X [title]"`

### ADR Numbering Scheme

- `001-099`: Core architecture decisions
- `100-199`: Feature-specific decisions
- `200-299`: Infrastructure and tooling
- `300-399`: Security and compliance
- `400-499`: Integration decisions

### Status Meanings

- **Proposed**: Under discussion, not yet accepted
- **Accepted**: Approved and implemented
- **Deprecated**: No longer recommended but still in use
- **Superseded**: Replaced by a newer ADR (link to new one)

### Writing Tips

- **Be specific**: Avoid vague statements like "improve performance"
- **Use examples**: Show concrete code or scenarios
- **Explain tradeoffs**: Every decision has pros and cons
- **Think long-term**: How will this age? What might change?
- **Link liberally**: Connect to related docs and ADRs
