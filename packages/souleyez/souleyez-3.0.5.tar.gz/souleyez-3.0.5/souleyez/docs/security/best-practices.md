# Security Best Practices for Users

## Overview

This guide provides practical security advice for souleyez users, from individual pentesters to enterprise teams.

---

## Quick Security Wins (5 Minutes)

These simple steps dramatically improve security:

### 1. Enable Credential Encryption

```bash
python3 migrate_credentials.py
```

**Impact:** Protects all stored credentials with encryption  
**Effort:** 1 minute  
**Requirement:** Strong master password

---

### 2. Use Strong Master Password

```
❌ Bad:  password123
❌ Bad:  souleyez
✅ Good: Tr0ut-F1sh!ng-B0at$42
✅ Good: MyD0g'sN@me&B1rthY3ar!99
```

**Impact:** Prevents brute-force attacks  
**Effort:** 30 seconds  
**Tool:** Password manager (LastPass, 1Password, Bitwarden)

---

### 3. Check File Permissions

```bash
ls -la data/souleyez.db
ls -la ~/.souleyez/crypto.json

# Should see: -rw-------
# If not, fix:
chmod 600 data/souleyez.db
chmod 600 ~/.souleyez/crypto.json
```

**Impact:** Prevents other users reading your data  
**Effort:** 30 seconds  
**Requirement:** Basic shell knowledge

---

### 4. Enable Screen Lock

```bash
# Set auto-lock timeout
# GNOME: Settings > Privacy > Screen Lock > 5 minutes
# macOS: System Preferences > Security > Require password after 5 minutes
```

**Impact:** Protects unattended system  
**Effort:** 1 minute  
**Requirement:** None

---

### 5. Regular Backups

```bash
# Quick backup
tar czf ~/souleyez_backup_$(date +%Y%m%d).tar.gz \
    ~/.souleyez/crypto.json \
    data/souleyez.db

# Store backup securely (encrypted USB, cloud with encryption)
```

**Impact:** Recover from data loss  
**Effort:** 2 minutes  
**Requirement:** Backup destination

---

## General Security Principles

### Defense in Depth

**Don't rely on a single security control.** Layer multiple protections:

```
┌─────────────────────────────────────┐
│ Physical Security (locked room)     │
│  ├─ Disk Encryption (LUKS/FileVault)│
│  │  ├─ User Authentication (password)│
│  │  │  ├─ File Permissions (600)    │
│  │  │  │  ├─ Credential Encryption  │
│  │  │  │  │  └─ Strong Password     │
└─────────────────────────────────────┘
```

**Example:** Even if attacker steals your laptop:
1. Need to bypass disk encryption
2. Need to log in as your user
3. Need to access database file
4. Need to decrypt credentials

---

### Least Privilege

**Only grant necessary permissions.**

**DO:**
- Run souleyez as regular user
- Use sudo only when tool requires it (e.g., `sudo nmap -sS`)
- Create dedicated user for souleyez (enterprises)

**DON'T:**
- Run souleyez as root
- Grant unnecessary file permissions
- Share accounts between users

---

### Zero Trust

**Trust nothing, verify everything.**

**DO:**
- Verify tool installations (`which nmap`, check hash)
- Review findings before acting
- Validate target authorization
- Audit access logs

**DON'T:**
- Assume tools are safe
- Trust network connections
- Skip verification steps

---

## Before You Scan

### 1. Obtain Authorization

**Legal Requirements:**

✅ **Required:**
- Written authorization from asset owner
- Scope document (what you can/cannot test)
- Rules of engagement
- Emergency contact information

❌ **Never:**
- Scan without authorization
- Exceed authorized scope
- Test production systems without approval
- Share findings publicly before disclosure

**Example Authorization Email:**

```
From: client@example.com
To: pentester@company.com
Subject: Authorization for Security Assessment

I, [Name], authorize [Company] to perform security testing on:
- IP Range: 192.168.1.0/24
- Domains: *.example.com
- Dates: October 15-29, 2025
- Restrictions: No DoS attacks, no social engineering

Contact for issues: [Phone/Email]
Emergency stop: [Phone]

Signed: [Signature]
```

---

### 2. Create Engagement

**Always use engagements for organization:**

```bash
souleyez engagement create "ACME Corp Q4 2025" \
    -d "Internal network assessment per SOW-2025-10"
souleyez engagement use "ACME Corp Q4 2025"
```

**Why:**
- Separate client data
- Audit trail
- Clear scope boundaries
- Easy reporting

---

### 3. Test Connectivity

**Verify you can reach targets before scanning:**

```bash
# Basic connectivity
ping 192.168.1.100

# Check network path
traceroute 192.168.1.100

# Verify routing
ip route get 192.168.1.100
```

**Common Issues:**
- VPN not connected
- Wrong network segment
- Firewall blocking
- Target offline

---

## During Scanning

### 1. Monitor Your Scans

**Use the dashboard to watch progress:**

```bash
souleyez dashboard
```

**Watch for:**
- Jobs taking too long (may be stuck)
- High CPU/memory usage
- Network saturation
- Unexpected findings (could indicate issues)

---

### 2. Be Stealthy (When Appropriate)

**Adjust scan intensity based on rules of engagement:**

```bash
# Stealthy (slow, less likely to trigger IDS)
souleyez jobs enqueue nmap 192.168.1.0/24 -a "-T2 -sT"

# Normal (default)
souleyez jobs enqueue nmap 192.168.1.0/24 -a "-T3"

# Aggressive (fast, noisy)
souleyez jobs enqueue nmap 192.168.1.0/24 -a "-T4 -sS"
```

**Stealth Options:**
- `-T2` or `-T1` timing templates
- `-sT` (TCP connect instead of SYN)
- Longer delays between requests
- Smaller scan windows

---

### 3. Respect Rate Limits

**Don't DOS the target:**

```bash
# Limit parallel connections
souleyez jobs enqueue gobuster http://example.com \
    -a "dir -w wordlist.txt -t 5"  # Only 5 threads

# Slower scans
souleyez jobs enqueue nmap 192.168.1.100 \
    -a "--max-rate 100"  # Max 100 packets/sec
```

**Signs you're going too fast:**
- Target becomes unresponsive
- Services crash
- Legitimate users complain
- IDS/IPS alerts

---

### 4. Secure Your Connection

**Protect scanning traffic:**

```bash
# Use VPN for remote targets
sudo openvpn --config client.ovpn

# Or SSH tunnel
ssh -D 1080 user@jumphost

# Configure tools to use SOCKS proxy (if needed)
```

**Why:**
- Encrypt traffic (coffee shop WiFi)
- Hide source IP
- Access internal networks
- Bypass geo-restrictions (authorized only)

---

## After Scanning

### 1. Review Findings Carefully

**Don't blindly trust tool output:**

```bash
souleyez findings list
```

**Verification Steps:**
1. Manually verify each finding
2. Check for false positives
3. Assess actual risk (not just CVSS score)
4. Document reproduction steps

**Example:**

```bash
# Tool says: "SQL Injection found"
# Verify: Test payload manually in browser
# Result: False positive (input validation works)
# Action: Mark as false positive in notes
```

---

### 2. Secure Your Results

**Findings are sensitive:**

```bash
# Generate report
souleyez report generate "ACME Corp Findings"

# Encrypt report
gpg --encrypt --recipient client@example.com \
    reports/acme_corp_findings.html

# Send via secure channel (not email)
# Use: SFTP, secure file sharing, encrypted email
```

**DON'T:**
- Email unencrypted findings
- Store on public cloud (Dropbox, Google Drive)
- Share via Slack/Teams (unless encrypted)
- Print and leave on desk

---

### 3. Clean Up Artifacts

**Remove evidence of testing:**

```bash
# Example: Remove uploaded shells
ssh target "rm /var/www/html/test_shell.php"

# Example: Clear logs (if authorized)
ssh target "echo > /var/log/nginx/access.log"

# Archive engagement
souleyez engagement list
# Archive in secure storage, then delete
```

**Why:**
- Prevent real attackers finding your tools
- Clean up test accounts/files
- Respect client's environment

---

### 4. Secure Delete Sensitive Data

**When engagement is complete:**

```bash
# Export findings first
souleyez report generate "Final Report"

# Secure delete (overwrite before removal)
shred -vfz -n 7 data/souleyez.db
shred -vfz -n 7 ~/.souleyez/crypto.json
shred -vfz -n 7 data/jobs/*.log

# Or use secure delete tool
sudo apt install secure-delete
srm -vz data/souleyez.db
```

**When to secure delete:**
- End of engagement
- Client requests data destruction
- Leaving company
- Decommissioning hardware

---

## Password Management

### Master Password Best Practices

**DO:**
- ✅ Use 12+ characters
- ✅ Mix uppercase, lowercase, numbers, symbols
- ✅ Make it memorable but unique
- ✅ Store in password manager
- ✅ Use different password per system

**DON'T:**
- ❌ Reuse passwords from other services
- ❌ Use personal information (birthday, pet name)
- ❌ Write on sticky note (unless locked in safe)
- ❌ Store in plaintext file
- ❌ Share with colleagues

---

### Password Manager Setup

**Recommended Tools:**
- **LastPass** (freemium, cross-platform)
- **1Password** (paid, best UX)
- **Bitwarden** (open-source, free)
- **KeePassXC** (offline, free)

**Setup:**

```bash
# Example: Bitwarden CLI
sudo apt install bitwarden-cli

# Login
bw login

# Store souleyez password
bw create item \
    --name "SoulEyez Master Password" \
    --username "souleyez" \
    --password "Tr0ut-F1sh!ng-B0at$42" \
    --notes "For ~/souleyez_app installation"

# Retrieve password
bw get password "SoulEyez Master Password"
```

---

## Physical Security

### Laptop Security

**DO:**
- ✅ Enable full-disk encryption (LUKS/FileVault/BitLocker)
- ✅ Strong password/PIN (not fingerprint as primary)
- ✅ Screen lock after 5 minutes
- ✅ BIOS/UEFI password
- ✅ Disable USB boot (BIOS setting)

**DON'T:**
- ❌ Leave laptop unattended in public
- ❌ Store passwords on sticky notes
- ❌ Use same password for disk encryption and login
- ❌ Disable security features for convenience

---

### Workspace Security

**DO:**
- ✅ Lock screen when leaving desk
- ✅ Shred printed findings
- ✅ Use privacy screen (prevent shoulder surfing)
- ✅ Store backups in locked drawer/safe

**DON'T:**
- ❌ Discuss findings in public (coffee shop, airplane)
- ❌ Display sensitive data on external monitors (visible to others)
- ❌ Store USB drives with data unsecured

---

## Network Security

### Home Network

**Basic Hardening:**

```bash
# Change default router password
# Router admin: http://192.168.1.1
# Change admin password immediately

# Use WPA3 WiFi encryption (or WPA2 if WPA3 unavailable)
# Router > Wireless > Security > WPA3-Personal

# Disable WPS (WiFi Protected Setup)
# Router > Wireless > WPS > Disable

# Enable firewall
# Router > Security > Firewall > Enable

# Separate scanning VLAN (advanced)
# Router > VLAN > Create > ID 100 "Scanning"
```

---

### Public WiFi

**Risks:**
- Man-in-the-middle attacks
- Traffic sniffing
- Malicious hotspots

**Protections:**

```bash
# Always use VPN on public WiFi
sudo openvpn --config client.ovpn

# Or SSH tunnel
ssh -D 1080 -C user@your_server

# Verify SSL certificates
# Check HTTPS indicator in browser

# Disable file sharing
# Network settings > File Sharing > Off
```

**Rules:**
- ❌ Never access client data on public WiFi
- ❌ Never enter credentials on HTTP sites
- ✅ Use VPN for all activity
- ✅ Verify network name with staff (avoid "Free WiFi" spoofs)

---

## Social Engineering Defense

### Protecting Yourself

**DO:**
- ✅ Verify caller identity before discussing engagement
- ✅ Use code words with clients (pre-arranged)
- ✅ Be suspicious of urgent requests
- ✅ Verify email addresses carefully (look for typos)

**DON'T:**
- ❌ Share findings over phone without verification
- ❌ Click links in unexpected emails
- ❌ Download attachments from unknown senders
- ❌ Discuss client names in public

---

### Red Flags

**Suspicious Requests:**

```
From: ceo@clientt.com  # Typo in domain
Subject: URGENT: Send pentesting results NOW

Need findings report immediately for board meeting.
Send to: attacker@suspicious.com

- CEO
```

**What's wrong:**
- Unexpected urgency
- Spelling error in domain (clientt vs client)
- Unusual request (CEO wouldn't ask directly)
- External email address
- Pressure tactics

**Response:**
1. Don't reply to email
2. Call client contact directly (known number)
3. Verify request legitimacy
4. Report phishing attempt

---

## Incident Response

### If You Suspect Compromise

**Immediate Actions:**

1. **Disconnect from network**
   ```bash
   sudo ip link set eth0 down
   sudo ip link set wlan0 down
   ```

2. **Document everything**
   - What you were doing
   - What you observed
   - Time of incident
   - Screenshot if possible

3. **Don't destroy evidence**
   - Don't shut down (live memory)
   - Don't delete files
   - Don't "fix" things

4. **Notify stakeholders**
   - Your security team
   - Client (if their data at risk)
   - Legal (if required)

5. **Preserve system**
   - Take memory dump (`sudo dd if=/dev/mem of=memory.dump`)
   - Clone disk (`sudo dd if=/dev/sda of=disk.img`)
   - Or: Power off and secure system

---

### If Credentials Compromised

**Master Password Leaked:**

1. **Change immediately**
   ```bash
   python3 change_password.py  # See credential-encryption.md
   ```

2. **Rotate all target credentials**
   - Change passwords on all systems you've tested
   - Notify client of potential breach

3. **Audit access logs**
   - Check for unauthorized access
   - Review recent activity

4. **Document incident**
   - When/how compromise occurred
   - What data was accessed
   - Mitigation actions taken

---

### If Database Stolen

**Assume worst case:**

1. **If encrypted:**
   - Assess master password strength
   - If weak: Rotate all credentials immediately
   - If strong: Monitor for unusual activity

2. **If plaintext:**
   - Assume all credentials compromised
   - Rotate everything immediately
   - Notify affected clients

3. **Investigate:**
   - How was database accessed?
   - What other data was stolen?
   - Was it targeted or opportunistic?

4. **Legal obligations:**
   - Data breach notification laws
   - Client contracts (may require disclosure)
   - Professional standards

---

## Operational Security (OPSEC)

### Communication Security

**DO:**
- ✅ Use encrypted messaging (Signal, Wire)
- ✅ PGP-encrypt sensitive emails
- ✅ Verify recipient before sending
- ✅ Use secure file sharing (encrypted)

**DON'T:**
- ❌ Discuss findings in public places
- ❌ Use SMS for sensitive info
- ❌ Email plaintext credentials
- ❌ Post about clients on social media

---

### Travel Security

**Before Travel:**
- Backup critical data
- Encrypt all devices
- Use travel laptop (not primary)
- Remove sensitive data

**During Travel:**
- Use VPN at all times
- Avoid public charging stations (juice jacking)
- Keep devices with you (don't check bags)
- Use privacy screen on airplane

**After Travel:**
- Check devices for tampering
- Scan for malware
- Review recent file access
- Change passwords if device was out of sight

---

## Compliance Considerations

### GDPR (EU)

**Requirements for pentesters:**
- Obtain consent for data collection
- Document legal basis for processing
- Enable data deletion (right to erasure)
- Notify breaches within 72 hours

**Implementation:**

```bash
# Document consent
echo "Authorization: [PDF link]" > engagement_notes.txt

# Enable deletion
souleyez engagement delete "Client XYZ"

# Breach notification procedure
# Have client contact info ready
# Prepare incident report template
```

---

### HIPAA (US Healthcare)

**Requirements:**
- Encrypt all PHI (Protected Health Information)
- Access controls and logging
- Business Associate Agreement (BAA)
- Breach notification procedures

**Implementation:**

```bash
# Enable all encryption
python3 migrate_credentials.py

# Audit logging
# See secure-defaults.md for implementation

# Secure disposal
shred -vfz -n 7 data/souleyez.db
```

---

## Team Best Practices

### For Managers

**DO:**
- ✅ Provide security training
- ✅ Enforce encryption policies
- ✅ Regular security audits
- ✅ Incident response plan
- ✅ Client data handling procedures

**DON'T:**
- ❌ Share databases between team members
- ❌ Store findings on shared drives (unless encrypted)
- ❌ Reuse passwords across projects
- ❌ Skip authorization verification

---

### For Team Members

**DO:**
- ✅ Use unique master password per system
- ✅ Report security concerns immediately
- ✅ Follow documented procedures
- ✅ Keep software updated

**DON'T:**
- ❌ Share credentials with teammates
- ❌ Work on personal devices (BYOD risks)
- ❌ Skip backup procedures
- ❌ Take shortcuts on security

---

## Security Checklist

### Daily

- [ ] Lock screen when away from desk
- [ ] Verify target authorization before scanning
- [ ] Review findings as they come in
- [ ] Log out of souleyez when done

### Weekly

- [ ] Review audit logs (if enabled)
- [ ] Backup database and crypto config
- [ ] Check for security updates
- [ ] Test backup recovery

### Monthly

- [ ] Rotate target credentials (in coordination with client)
- [ ] Archive old engagements
- [ ] Review security configuration
- [ ] Update threat model

### Quarterly

- [ ] Security audit of souleyez installation
- [ ] Penetration test of scanning infrastructure
- [ ] Review and update procedures
- [ ] Team security training

---

## Resources

### Tools

- **Password Managers**: Bitwarden, 1Password, KeePassXC
- **VPNs**: WireGuard, OpenVPN, Tailscale
- **Encrypted Messaging**: Signal, Wire, Threema
- **File Encryption**: GPG, VeraCrypt, Cryptomator

### Reading

- **OWASP Testing Guide**: https://owasp.org/www-project-web-security-testing-guide/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework
- **PTES Technical Guidelines**: http://www.pentest-standard.org/

### Training

- **OSCP** (Offensive Security Certified Professional)
- **CEH** (Certified Ethical Hacker)
- **GPEN** (GIAC Penetration Tester)
- **Security+ ** (CompTIA)

---

## Getting Help

**Security Questions:**
- GitHub Discussions: https://github.com/y0d8/souleyez_app/discussions
- Email: security@souleyez.dev (TODO)

**Security Vulnerabilities:**
- **DO NOT** report publicly
- Email: security@souleyez.dev (TODO)
- PGP Key: [TODO]

---

## See Also

- [Threat Model](threat-model.md)
- [Credential Encryption](credential-encryption.md)
- [Secure Defaults](secure-defaults.md)
- [SECURITY.md](../../SECURITY.md)
