#!/usr/bin/env python3
"""
souleyez.plugins.dns_hijack

DNS hijacking detection plugin.
Checks if a router is performing DNS hijacking/redirection.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "DNS Hijack — DNS Manipulation Detection",
    "description": (
        "Detect DNS hijacking or manipulation by a router.\n\n"
        "Compromised routers often modify DNS settings to:\n"
        "- Redirect users to phishing sites\n"
        "- Inject ads into web pages\n"
        "- Monitor browsing activity\n"
        "- Block security updates\n\n"
        "This plugin compares DNS responses from the router to known-good servers.\n\n"
        "Quick tips:\n"
        "- Compare router DNS to 8.8.8.8 (Google) or 1.1.1.1 (Cloudflare)\n"
        "- Test with known domains (google.com, microsoft.com)\n"
        "- NXDOMAIN hijacking is common (typos redirect to ads)\n"
        "- Check multiple domains to confirm\n"
    ),
    "usage": "souleyez jobs enqueue dns_hijack <router_ip>",
    "examples": [
        "souleyez jobs enqueue dns_hijack 192.168.1.1",
        'souleyez jobs enqueue dns_hijack 192.168.1.1 --args "--domains google.com,microsoft.com"',
    ],
    "flags": [
        ["--domains DOMAINS", "Comma-separated test domains"],
    ],
    "presets": [
        {"name": "Quick Check", "args": [], "desc": "Test with common domains"},
        {
            "name": "Extended",
            "args": [
                "--domains",
                "google.com,microsoft.com,apple.com,facebook.com,amazon.com",
            ],
            "desc": "Test multiple major sites",
        },
    ],
    "help_sections": [
        {
            "title": "What is DNS Hijacking?",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "DNS hijacking redirects DNS queries to attacker-controlled servers",
                        "Compromised routers may modify DNS to redirect traffic",
                        "This tool compares router DNS responses to known-good DNS (8.8.8.8)",
                    ],
                ),
                (
                    "Common Attack Goals",
                    [
                        "Redirect users to phishing sites (fake banking, email)",
                        "Inject ads into web pages for profit",
                        "Monitor browsing activity and steal credentials",
                        "Block security updates to maintain access",
                    ],
                ),
            ],
        },
        {
            "title": "Usage & Examples",
            "color": "green",
            "content": [
                (
                    "Basic Usage",
                    [
                        "souleyez jobs enqueue dns_hijack 192.168.1.1",
                        "  → Tests router DNS against Google DNS (8.8.8.8)",
                    ],
                ),
                (
                    "Custom Domains",
                    [
                        'souleyez jobs enqueue dns_hijack 192.168.1.1 --args "--domains google.com,bank.com"',
                        "  → Tests specific domains you're concerned about",
                    ],
                ),
            ],
        },
        {
            "title": "Understanding Results",
            "color": "yellow",
            "content": [
                (
                    "Result Indicators",
                    [
                        "[OK] - DNS responses match the reference server",
                        "[WARN] - Partial match, some IPs differ (investigate)",
                        "[ALERT] - No matching IPs, likely hijacked!",
                    ],
                ),
                (
                    "NXDOMAIN Test",
                    [
                        "Tests if router returns IPs for fake domains",
                        "If yes: Router hijacks typos to show ads/search pages",
                        "Common ISP 'feature' but can mask real hijacking",
                    ],
                ),
                (
                    "Next Steps if Hijacked",
                    [
                        "Change router DNS to 8.8.8.8 or 1.1.1.1 manually",
                        "Check router for firmware compromise",
                        "Look for unauthorized admin accounts",
                        "Consider factory reset if malware suspected",
                    ],
                ),
            ],
        },
    ],
}


class DNSHijackPlugin(PluginBase):
    name = "DNS Hijack"
    tool = "dig"
    category = "vulnerability_analysis"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build dig commands for DNS hijack detection."""
        args = args or []

        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        # Parse domains to test
        domains = ["google.com", "microsoft.com", "example.com"]
        i = 0
        while i < len(args):
            if args[i] == "--domains" and i + 1 < len(args):
                domains = [d.strip() for d in args[i + 1].split(",")]
                i += 2
            else:
                i += 1

        # We'll build a shell script that compares responses
        # This is stored and executed
        return {"domains": domains, "target": target, "timeout": 120}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute DNS hijack detection."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        domains = cmd_spec["domains"]
        reference_dns = "8.8.8.8"  # Google DNS as reference

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# DNS Hijack Detection on {target}\n")
                f.write(f"# Reference DNS: {reference_dns}\n")
                f.write(f"# Test domains: {', '.join(domains)}\n")
                f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        hijack_detected = False

        try:
            for domain in domains:
                with open(log_path, "a") as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Testing: {domain}\n")
                    f.write(f"{'='*60}\n\n")

                # Query target router
                try:
                    router_result = subprocess.run(
                        ["dig", "+short", f"@{target}", domain, "A"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    router_ips = (
                        set(router_result.stdout.strip().split("\n"))
                        if router_result.stdout.strip()
                        else set()
                    )
                except subprocess.TimeoutExpired:
                    router_ips = set()
                    with open(log_path, "a") as f:
                        f.write(f"  Router DNS (@{target}): TIMEOUT\n")

                # Query reference DNS
                try:
                    ref_result = subprocess.run(
                        ["dig", "+short", f"@{reference_dns}", domain, "A"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    ref_ips = (
                        set(ref_result.stdout.strip().split("\n"))
                        if ref_result.stdout.strip()
                        else set()
                    )
                except subprocess.TimeoutExpired:
                    ref_ips = set()
                    with open(log_path, "a") as f:
                        f.write(f"  Reference DNS (@{reference_dns}): TIMEOUT\n")

                with open(log_path, "a") as f:
                    f.write(f"  Router DNS (@{target}):\n")
                    for ip in sorted(router_ips):
                        f.write(f"    {ip}\n")
                    f.write(f"\n  Reference DNS (@{reference_dns}):\n")
                    for ip in sorted(ref_ips):
                        f.write(f"    {ip}\n")

                    # Compare
                    if router_ips and ref_ips:
                        if router_ips == ref_ips:
                            f.write(f"\n  [OK] Responses match\n")
                        elif router_ips & ref_ips:
                            f.write(f"\n  [WARN] Partial match - some IPs differ\n")
                            f.write(f"    Router only: {router_ips - ref_ips}\n")
                            f.write(f"    Reference only: {ref_ips - router_ips}\n")
                        else:
                            f.write(
                                f"\n  [ALERT] No matching IPs - possible DNS hijack!\n"
                            )
                            hijack_detected = True
                    elif router_ips and not ref_ips:
                        f.write(
                            f"\n  [WARN] Router returned IPs but reference didn't\n"
                        )
                    elif ref_ips and not router_ips:
                        f.write(
                            f"\n  [WARN] Reference returned IPs but router didn't\n"
                        )

            # Test NXDOMAIN hijacking
            with open(log_path, "a") as f:
                f.write(f"\n{'='*60}\n")
                f.write("Testing NXDOMAIN hijacking (nonexistent domain):\n")
                f.write(f"{'='*60}\n\n")

            fake_domain = "thisisafakedomainthatdoesnotexist12345.com"

            try:
                nxdomain_result = subprocess.run(
                    ["dig", "+short", f"@{target}", fake_domain, "A"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                nxdomain_ips = nxdomain_result.stdout.strip()

                with open(log_path, "a") as f:
                    if nxdomain_ips:
                        f.write(
                            f"  [ALERT] Router returns IPs for nonexistent domain!\n"
                        )
                        f.write(
                            f"  This indicates NXDOMAIN hijacking (likely ads/search redirect)\n"
                        )
                        f.write(f"  Returned IPs: {nxdomain_ips}\n")
                        hijack_detected = True
                    else:
                        f.write(
                            f"  [OK] Router correctly returns no IPs for nonexistent domain\n"
                        )
            except subprocess.TimeoutExpired:
                with open(log_path, "a") as f:
                    f.write(f"  [WARN] NXDOMAIN test timed out\n")

            # Summary
            with open(log_path, "a") as f:
                f.write(f"\n{'='*60}\n")
                f.write("SUMMARY\n")
                f.write(f"{'='*60}\n\n")
                if hijack_detected:
                    f.write("  [!] POTENTIAL DNS HIJACKING DETECTED\n")
                    f.write(
                        "  Investigate the router for malware or misconfiguration.\n"
                    )
                else:
                    f.write("  [OK] No obvious DNS hijacking detected\n")

            return 1 if hijack_detected else 0

        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {e}\n")
            return 1


plugin = DNSHijackPlugin()
