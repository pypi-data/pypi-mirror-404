# Deliverable Templates

This directory contains built-in compliance and security framework templates for SoulEyez.

## Available Templates

### Compliance Frameworks

- **pci_dss_4.0.json** - PCI-DSS 4.0 (12 deliverables)
- **hipaa_security.json** - HIPAA Security Rule (8 deliverables)

### Security Standards

- **owasp_top10_2021.json** - OWASP Top 10 2021 (10 deliverables)
- **nist_csf.json** - NIST Cybersecurity Framework (5 deliverables)

## Template Format

```json
{
  "name": "Template Name",
  "description": "Description of the template",
  "framework": "framework-id",
  "engagement_type": "webapp|network|redteam|cloud|wireless|mobile|api",
  "deliverables": [
    {
      "category": "reconnaissance|enumeration|exploitation|post_exploitation|techniques",
      "title": "Deliverable title",
      "description": "What needs to be tested",
      "target_type": "count|boolean|manual",
      "target_value": 1,
      "auto_validate": true|false,
      "validation_query": "SQL query to auto-check progress",
      "priority": "critical|high|medium|low"
    }
  ]
}
```

## Auto-Validation

Deliverables with `auto_validate: true` can automatically check progress by querying:
- `findings` table - for discovered vulnerabilities
- `hosts` table - for discovered systems
- `services` table - for open ports/services
- `credentials` table - for compromised accounts

## Creating Custom Templates

1. Copy an existing template as a starting point
2. Modify the deliverables array
3. Save with a descriptive filename
4. Import via the UI: `[T] > [I] Import Template`

## Best Practices

- Use clear, actionable titles
- Include requirement IDs for compliance frameworks
- Set appropriate priorities (critical/high for security controls)
- Enable auto-validation where possible to track progress automatically
- Group related tests by category (PTES methodology)
