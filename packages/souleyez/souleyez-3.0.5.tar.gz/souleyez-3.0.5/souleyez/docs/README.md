# SoulEyez Documentation

**Version:** 3.0.5
**Last Updated:** January 31, 2026
**Organization:** CyberSoul Security

Welcome to the SoulEyez documentation! This documentation covers architecture, development, user guides, and operational information for the SoulEyez penetration testing platform.

---

## 📚 Documentation Structure

### 🏗️ Architecture

Technical architecture and design decisions.

- [**Architecture Overview**](architecture/overview.md) - Complete system architecture
  - System overview and design philosophy
  - Core components and data flow
  - Engagement data model with ERD
  - Credential encryption architecture
  - Parser architecture
  - Job execution engine
  - Technology stack

- [**Architecture Decision Records (ADRs)**](architecture/decisions/)
  - [ADR-001: Local LLM Over Cloud AI](architecture/decisions/001-local-llm-over-cloud.md)
  - [ADR-002: Master Password Approach](architecture/decisions/002-master-password-approach.md)
  - [ADR-003: SQLite Database Design](architecture/decisions/003-database-schema-design.md)
  - [ADR Template](architecture/decisions/000-template.md)

---

### 👨‍💻 Developer Guide

Information for contributors and developers.

- [**Epic 3: Repository Migration**](developer-guide/EPIC3_REPOSITORY_MIGRATION.md)
  - Move from personal repo to @cybersoul-security
  - 4 stories, 6 story points, 1 week

- [**Epic 4: Code Rebrand**](developer-guide/EPIC4_CODE_REBRAND.md)
  - Rename souleyez → souleyez
  - 8 stories, 32 story points, 1 week

- [**Phase 1 Foundation**](developer-guide/PHASE1_FOUNDATION.md)
  - Detailed 2-week work breakdown
  - 5 work streams, 80 hours total

- [**Phase 1 User Stories**](developer-guide/PHASE1_USER_STORIES.md)
  - 18 user stories ready for import
  - Sprint planning for 2 weeks

- [**Epics Overview**](developer-guide/EPICS_OVERVIEW.md)
  - Master reference for all 10 project epics
  - Timeline and status tracking

- [**Test Coverage Plan**](developer-guide/test_coverage_plan.md)
  - Testing strategy and coverage goals

- [**Deliverables Summary**](developer-guide/DELIVERABLES_SUMMARY.md)
  - Phase 1 planning deliverables summary

- [**Documentation Structure Guide**](doc_structure_guide.md)
  - This guide defines the complete documentation structure

---

### 📖 User Guide

End-user documentation for penetration testers.

- [**Getting Started**](user-guide/getting-started.md) - First engagement in 10 minutes
- [**Installation Guide**](user-guide/installation.md) - Setup and dependencies
- [**Worker Management**](user-guide/worker-management.md) - Background job system
- [**Tools Reference**](user-guide/tools-reference.md) - All supported security tools
- [**Workflows**](user-guide/workflows.md) - Common pentesting workflows
- [**Troubleshooting**](user-guide/troubleshooting.md) - Common issues and fixes

---

### 📡 API Reference

*(Coming in Epic 5)*

API documentation and reference.

- CLI Commands
- Engagement API
- Parser API
- Credential API
- AI API (Internal)

---

### ⚙️ Operations

*(Coming in Epic 7)*

Deployment and operational guides.

- Deployment
- Configuration
- Backup & Recovery
- Monitoring
- Performance Tuning
- Upgrade Guide

---

### 🔐 Security

Security documentation and best practices.

- [**Credential Encryption**](security/credential-encryption.md) - Master password and encryption
- Threat Model *(planned)*
- Key Management *(planned)*
- Security Best Practices *(planned)*

### ⚡ Feature Documentation

Advanced features and integrations.

- [**Auto-Chaining**](user-guide/auto-chaining.md) - Automatic follow-up scans
- [**Metasploit Integration**](user-guide/metasploit-integration.md) - MSF data sync and exploit tracking
- [**SIEM Integration**](user-guide/siem-integration.md) - Wazuh, Splunk, and detection validation
  - Detection validation (verify attacks triggered alerts)
  - Vulnerability management views
  - Gap analysis (passive vs active CVE comparison)
  - MITRE ATT&CK coverage reports
  - Real-time alert monitoring
- [**Configuration Guide**](user-guide/configuration.md) - All configuration options
- [**Database Migrations**](database/MIGRATIONS.md) - Schema migration system

---

### 🎓 Tutorials

*(Coming in Epic 6)*

Step-by-step tutorials.

- Your First Engagement
- Importing Nmap Scans
- Metasploit Integration
- Using AI Attack Paths
- Report Generation

---

### ⚖️ Compliance

*(Coming in Epic 7)*

Legal and compliance documentation.

- Licenses
- Third-Party Notices
- Privacy Policy
- Export Compliance

---

## 🚀 Quick Links

### For Users
- [Getting Started Guide](user-guide/getting-started.md) - First engagement in 10 minutes
- [Installation Guide](user-guide/installation.md) - Setup instructions
- [Troubleshooting](user-guide/troubleshooting.md) - Common issues

### For Developers
- [Architecture Overview](architecture/overview.md)
- [Database Schema](database/SCHEMA.md)
- [Database Migrations](database/MIGRATIONS.md)

### Feature Documentation
- [Auto-Chaining](user-guide/auto-chaining.md) - Automatic follow-up scans
- [Metasploit Integration](user-guide/metasploit-integration.md) - MSF data sync
- [SIEM Integration](user-guide/siem-integration.md) - Wazuh and Splunk
- [Configuration](user-guide/configuration.md) - All settings

---

## 📊 Documentation Status

| Section | Status | Last Updated |
|---------|--------|--------------|
| Architecture | ✅ Complete | Oct 2025 |
| ADRs | ✅ Complete | Oct 2025 |
| User Guide | ✅ Complete | Dec 2025 |
| Auto-Chaining | ✅ Complete | Nov 2025 |
| Metasploit Integration | ✅ Complete | Jan 2026 |
| SIEM Integration | ✅ Complete | Jan 2026 |
| Configuration | ✅ Complete | Nov 2025 |
| Security (Encryption) | ✅ Complete | Nov 2025 |
| Database Docs | ✅ Complete | Nov 2025 |
| API Reference | 🔄 In Progress | - |
| Tutorials | 🔄 Planned | - |

---

## 🛠️ Documentation Standards

### Writing Style
- Clear, concise language
- Present tense, active voice
- Include code examples
- Short paragraphs (3-5 sentences)

### Formatting
- GitHub-flavored Markdown
- Table of contents for long documents
- Code blocks with language specification
- Hierarchical headings (H1 → H2 → H3)

### Maintenance
- Review quarterly
- Mark deprecated features clearly
- Update version numbers
- Keep CHANGELOG.md current

---

## 👥 Documentation Ownership

| Section | Primary Owner | Reviewer |
|---------|---------------|----------|
| Architecture | Robert (CTO) | Jr (CISO) |
| User Guide | Magz (COO) | Arman (CMO) |
| Developer Guide | Jr (CISO) | Robert (CTO) |
| API Reference | Robert (CTO) | - |
| Operations | Magz (COO) | Robert (CTO) |
| Security | Jr (CISO) | Robert (CTO) |
| Tutorials | Arman (CMO) | Magz (COO) |
| Compliance | Jr (CISO) | Aliyeh (CEO) |

---

## 📞 Need Help?

- **Issues**: https://github.com/cyber-soul-security/SoulEyez/issues
- **Discussions**: https://github.com/cyber-soul-security/SoulEyez/discussions
- **Security**: cysoul.secit@gmail.com
- **General**: cysoul.secit@gmail.com

---

**Maintained by**: CyberSoul Security
**License**: See [LICENSE](../LICENSE)
**Last Review**: December 1, 2025
**Next Review**: January 1, 2026
