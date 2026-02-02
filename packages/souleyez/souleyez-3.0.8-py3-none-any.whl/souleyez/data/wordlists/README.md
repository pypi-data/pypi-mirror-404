# 🔑 SoulEyez Wordlists

Custom curated wordlists for efficient penetration testing.

## Username Lists

### `all_users.txt` (78 users)
**Complete list combining Linux system users + Star Wars theme users**
- Standard Linux accounts (root, daemon, www-data, etc.)
- Star Wars character accounts (luke_skywalker, darth_vader, etc.)
- Service accounts (mysql, postgres, sshd, etc.)

**Use for:** Comprehensive username enumeration

### `linux_users.txt` (48 users)
**Standard Linux/Unix system and service accounts**
- System accounts (root, daemon, bin, sys)
- Service accounts (www-data, mysql, postgres, ftp)
- Common defaults (admin, user, guest, vagrant)

**Use for:** Standard Linux/Unix targets

### `starwars_users.txt` (30 users)
**Star Wars character-themed usernames**
- Original trilogy (luke_skywalker, darth_vader, leia_organa)
- Prequels (anakin_skywalker, obi_wan, padme)
- Sequels (rey, kylo_ren, finn)

**Use for:** CTF challenges, themed labs, creative admins

## Password Lists

### `top20_quick.txt` (20 passwords)
**Ultra-fast password spray - most common weak passwords**
- Runtime: ~20 seconds with 78 users
- Hit rate: Catches obvious weak passwords

**Use for:** Quick wins, initial reconnaissance

### `top100.txt` (100 passwords)  
**Balanced speed/coverage - realistic passwords**
- Runtime: ~2 minutes with 78 users
- Includes seasonal variants (Summer2024, Winter2024)
- Common patterns (Password1, P@ssw0rd, Admin123)

**Use for:** Standard penetration tests

### `default_credentials.txt` (34 pairs)
**Vendor default username:password combinations**
- Format: `username:password`
- Use with Hydra's `-C` flag

**Use for:** Testing default credentials

## Usage Examples

### Quick Password Spray (Fastest)
Try top 20 passwords against all users:
```bash
souleyez jobs enqueue hydra <target> --args "ssh -L data/wordlists/all_users.txt -P data/wordlists/top20_quick.txt -t 1 -w 3"
```

### Standard Brute-Force
Comprehensive scan with top 100:
```bash
souleyez jobs enqueue hydra <target> --args "ssh -L data/wordlists/all_users.txt -P data/wordlists/top100.txt -t 1 -w 3"
```

### Default Credentials Check
Test vendor defaults:
```bash
souleyez jobs enqueue hydra <target> --args "ssh -C data/wordlists/default_credentials.txt -t 1"
```

### Single User Brute-Force
Focus on root account:
```bash
souleyez jobs enqueue hydra <target> --args "ssh -l root -P data/wordlists/top100.txt -t 1 -w 3"
```

### Star Wars Themed Target
For CTF/lab with Star Wars usernames:
```bash
souleyez jobs enqueue hydra <target> --args "ssh -L data/wordlists/starwars_users.txt -P data/wordlists/top100.txt -t 1 -w 3"
```

## Attack Statistics

| Users | Passwords | Total Attempts | Time (t=1, w=3) | Time (t=4, w=0) |
|-------|-----------|----------------|-----------------|-----------------|
| 78    | 20        | 1,560          | ~1.5 minutes    | ~15 seconds     |
| 78    | 100       | 7,800          | ~6.5 minutes    | ~1 minute       |
| 48    | 100       | 4,800          | ~4 minutes      | ~40 seconds     |
| 30    | 100       | 3,000          | ~2.5 minutes    | ~25 seconds     |

*Times assume successful SSH connections. Add 50% for connection issues.*

## Maintenance

### Update Seasonal Passwords
Before each engagement, update seasonal references:
```bash
# Example: Replace 2024 with 2025
sed -i 's/2024/2025/g' data/wordlists/top100.txt
sed -i 's/Winter/Spring/g' data/wordlists/top100.txt
```

### Add Client-Specific Passwords
Create custom list for engagement:
```bash
cat > data/wordlists/client_acme.txt << EOF
Acme2024!
Acme@2024
AcmePassword
CompanyName123
EOF
```

### Merge with External Lists
Combine with SecLists or other sources:
```bash
# Add top 1000 from rockyou.txt
head -1000 /usr/share/wordlists/rockyou.txt > data/wordlists/common1000.txt
```

## Best Practices

### Start Small, Escalate
1. **Quick spray** (top20) - 2 minutes
2. **Standard scan** (top100) - 7 minutes  
3. **External wordlist** (rockyou) - hours

### Password Spraying > Brute Force
- **Spraying**: Try 1-2 passwords against ALL users (less noisy)
- **Brute-force**: Try ALL passwords against 1 user (loud, risky)

### Always Use Rate Limiting
- Production: `-t 1 -w 3` (1 thread, 3 second delay)
- Lab: `-t 4 -w 0` (4 threads, no delay)
- Never use `-t 16` on production without authorization

## Sources

These wordlists are derived from:
- **SecLists** by Daniel Miessler
- **HIBP** (Have I Been Pwned) breach data
- **Real-world pentest findings** (anonymized)
- **Vendor documentation** (default credentials)
- **OWASP** password research

## License

Free to use for **authorized security testing only**.

⚠️ **WARNING**: Unauthorized use against systems you don't own is illegal.

---

## Quick Reference Card

```bash
# Ultra-fast (20 passwords, 1.5 min)
hydra -L data/wordlists/all_users.txt -P data/wordlists/top20_quick.txt -t 1 -w 3 ssh://TARGET

# Standard (100 passwords, 6.5 min)
hydra -L data/wordlists/all_users.txt -P data/wordlists/top100.txt -t 1 -w 3 ssh://TARGET

# Password spray (stealthy)
hydra -L data/wordlists/all_users.txt -p "Password123" -t 1 -w 5 ssh://TARGET

# Defaults only
hydra -C data/wordlists/default_credentials.txt -t 1 ssh://TARGET
```

💡 **Pro Tip**: Check `/etc/passwd` if you have file read access to see all usernames!
