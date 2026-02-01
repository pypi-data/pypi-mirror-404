#!/usr/bin/env python3
"""
souleyez.plugins.http_fingerprint - Lightweight HTTP fingerprinting

Detects:
- Server software (Apache, nginx, IIS, etc.)
- WAFs (Cloudflare, Akamai, AWS WAF, etc.)
- CDNs (Cloudflare, Fastly, CloudFront, etc.)
- Managed hosting platforms (Squarespace, Wix, Shopify, etc.)
- Technologies (via headers and cookies)

This runs BEFORE web vulnerability scanners to enable smarter tool configuration.
"""

import json
import socket
import ssl
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .plugin_base import PluginBase

HELP = {
    "name": "HTTP Fingerprint - Lightweight Web Reconnaissance",
    "description": (
        "Performs lightweight HTTP fingerprinting to detect server software, "
        "WAFs, CDNs, and managed hosting platforms.\n\n"
        "This runs automatically before web vulnerability scanners to enable "
        "smarter tool configuration. For example, if Squarespace is detected, "
        "nikto will skip CGI enumeration (pointless on managed platforms).\n\n"
        "Detection categories:\n"
        "- Server software (Apache, nginx, IIS, etc.)\n"
        "- WAFs (Cloudflare, Akamai, AWS WAF, Imperva, etc.)\n"
        "- CDNs (Cloudflare, Fastly, CloudFront, Akamai, etc.)\n"
        "- Managed hosting (Squarespace, Wix, Shopify, Netlify, etc.)\n"
    ),
    "usage": "souleyez jobs enqueue http_fingerprint <target>",
    "examples": [
        "souleyez jobs enqueue http_fingerprint http://example.com",
        "souleyez jobs enqueue http_fingerprint https://example.com",
    ],
    "flags": [
        ["--timeout <sec>", "Request timeout (default: 10)"],
    ],
    "presets": [
        {"name": "Quick Fingerprint", "args": [], "desc": "Fast fingerprint scan"},
    ],
    "help_sections": [
        {
            "title": "What is HTTP Fingerprinting?",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "Lightweight reconnaissance that identifies web infrastructure",
                        "Runs automatically before vulnerability scanners",
                        "Enables smarter tool configuration based on detected technology",
                    ],
                ),
                (
                    "What It Detects",
                    [
                        "Server software - Apache, nginx, IIS, LiteSpeed",
                        "WAFs - Cloudflare, Akamai, AWS WAF, Imperva, Sucuri",
                        "CDNs - Cloudflare, Fastly, CloudFront, Akamai",
                        "Managed hosting - Squarespace, Wix, Shopify, Netlify",
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
                        "souleyez jobs enqueue http_fingerprint http://example.com",
                        "souleyez jobs enqueue http_fingerprint https://example.com",
                        "  → Detects server, WAF, CDN, and hosting platform",
                    ],
                ),
            ],
        },
        {
            "title": "Why This Matters",
            "color": "yellow",
            "content": [
                (
                    "Smart Tool Configuration",
                    [
                        "If Squarespace detected → skip CGI enumeration (pointless)",
                        "If Cloudflare WAF detected → adjust scan rate to avoid blocks",
                        "If nginx detected → test nginx-specific vulnerabilities",
                    ],
                ),
                (
                    "Attack Surface Mapping",
                    [
                        "Managed platforms have limited attack surface",
                        "WAFs require evasion techniques or finding bypasses",
                        "CDNs may hide the real origin server IP",
                    ],
                ),
            ],
        },
    ],
}

# WAF detection signatures
# Format: {header_name: {value_pattern: waf_name}}
WAF_SIGNATURES = {
    # Header-based detection
    "headers": {
        "server": {
            "cloudflare": "Cloudflare",
            "akamaighost": "Akamai",
            "akamainetworkstorage": "Akamai",
            "awselb": "AWS ELB",
            "bigip": "F5 BIG-IP",
            "barracuda": "Barracuda",
            "denyall": "DenyAll",
            "fortigate": "Fortinet FortiGate",
            "imperva": "Imperva",
            "incapsula": "Imperva Incapsula",
            "netscaler": "Citrix NetScaler",
            "sucuri": "Sucuri",
            "wallarm": "Wallarm",
        },
        "x-powered-by": {
            "aws lambda": "AWS Lambda",
            "express": "Express.js",
            "php": "PHP",
            "asp.net": "ASP.NET",
        },
        "x-sucuri-id": {"": "Sucuri"},
        "x-sucuri-cache": {"": "Sucuri"},
        "cf-ray": {"": "Cloudflare"},
        "cf-cache-status": {"": "Cloudflare"},
        "x-amz-cf-id": {"": "AWS CloudFront"},
        "x-amz-cf-pop": {"": "AWS CloudFront"},
        "x-akamai-transformed": {"": "Akamai"},
        "x-cache": {
            "cloudfront": "AWS CloudFront",
            "varnish": "Varnish",
        },
        "x-fastly-request-id": {"": "Fastly"},
        "x-served-by": {
            "cache-": "Fastly",
        },
        "x-cdn": {
            "incapsula": "Imperva Incapsula",
            "cloudflare": "Cloudflare",
        },
        "x-iinfo": {"": "Imperva Incapsula"},
        "x-proxy-id": {"": "Imperva"},
        "x-request-id": {},  # Generic, but useful context
        "x-fw-protection": {"": "Unknown WAF"},
        "x-protected-by": {"": "Unknown WAF"},
        "x-waf-status": {"": "Unknown WAF"},
        "x-denied-reason": {"": "Unknown WAF"},
    },
    # Cookie-based detection
    "cookies": {
        "__cfduid": "Cloudflare",
        "cf_clearance": "Cloudflare",
        "__cf_bm": "Cloudflare Bot Management",
        "incap_ses": "Imperva Incapsula",
        "visid_incap": "Imperva Incapsula",
        "nlbi_": "Imperva Incapsula",
        "ak_bmsc": "Akamai Bot Manager",
        "bm_sz": "Akamai Bot Manager",
        "_abck": "Akamai Bot Manager",
        "awsalb": "AWS ALB",
        "awsalbcors": "AWS ALB",
        "ts": "F5 BIG-IP",
        "bigipserver": "F5 BIG-IP",
        "citrix_ns_id": "Citrix NetScaler",
        "sucuri_cloudproxy": "Sucuri",
    },
}

# CDN detection signatures
CDN_SIGNATURES = {
    "headers": {
        "cf-ray": "Cloudflare",
        "cf-cache-status": "Cloudflare",
        "x-amz-cf-id": "AWS CloudFront",
        "x-amz-cf-pop": "AWS CloudFront",
        "x-cache": {
            "cloudfront": "AWS CloudFront",
            "hit from cloudfront": "AWS CloudFront",
        },
        "x-fastly-request-id": "Fastly",
        "x-served-by": "Fastly",
        "x-akamai-transformed": "Akamai",
        "x-akamai-request-id": "Akamai",
        "x-edge-location": "Generic CDN",
        "x-cdn": "Generic CDN",
        "x-cache-status": "Generic CDN",
        "x-varnish": "Varnish",
        "via": {
            "cloudfront": "AWS CloudFront",
            "varnish": "Varnish",
            "akamai": "Akamai",
        },
        "x-azure-ref": "Azure CDN",
        "x-msedge-ref": "Azure CDN",
        "x-goog-": "Google Cloud CDN",
        "x-bunny-": "Bunny CDN",
        "x-hw": "Huawei CDN",
    },
    "server": {
        "cloudflare": "Cloudflare",
        "akamaighost": "Akamai",
        "cloudfront": "AWS CloudFront",
        "fastly": "Fastly",
        "varnish": "Varnish",
        "keycdn": "KeyCDN",
        "bunnycdn": "Bunny CDN",
        "cdn77": "CDN77",
        "stackpath": "StackPath",
        "limelight": "Limelight",
        "azure": "Azure CDN",
    },
}

# Managed hosting platform signatures
MANAGED_HOSTING_SIGNATURES = {
    "server": {
        "squarespace": "Squarespace",
        "wix": "Wix",
        "shopify": "Shopify",
        "weebly": "Weebly",
        "webflow": "Webflow",
        "ghost": "Ghost",
        "medium": "Medium",
        "tumblr": "Tumblr",
        "blogger": "Blogger/Blogspot",
        "wordpress.com": "WordPress.com",
        "netlify": "Netlify",
        "vercel": "Vercel",
        "heroku": "Heroku",
        "github": "GitHub Pages",
        "gitlab": "GitLab Pages",
        "firebase": "Firebase Hosting",
        "render": "Render",
        "railway": "Railway",
        "fly": "Fly.io",
        "deno": "Deno Deploy",
    },
    "headers": {
        "x-shopify-stage": "Shopify",
        "x-shopify-request-id": "Shopify",
        "x-wix-request-id": "Wix",
        "x-wix-renderer-server": "Wix",
        "x-sqsp-edge": "Squarespace",
        "x-squarespace-": "Squarespace",
        "x-ghost-": "Ghost",
        "x-medium-content": "Medium",
        "x-tumblr-": "Tumblr",
        "x-blogger-": "Blogger/Blogspot",
        "x-netlify-": "Netlify",
        "x-nf-request-id": "Netlify",
        "x-vercel-": "Vercel",
        "x-vercel-id": "Vercel",
        "x-heroku-": "Heroku",
        "x-github-request-id": "GitHub Pages",
        "x-firebase-": "Firebase Hosting",
        "x-render-origin-server": "Render",
        "fly-request-id": "Fly.io",
    },
    "cookies": {
        "wordpress_": "WordPress",
        "wp-settings": "WordPress",
        "_shopify_": "Shopify",
        "wixSession": "Wix",
    },
}

# Server software signatures
SERVER_SIGNATURES = {
    "apache": "Apache",
    "nginx": "nginx",
    "microsoft-iis": "Microsoft IIS",
    "iis": "Microsoft IIS",
    "lighttpd": "lighttpd",
    "litespeed": "LiteSpeed",
    "openresty": "OpenResty",
    "caddy": "Caddy",
    "tomcat": "Apache Tomcat",
    "jetty": "Eclipse Jetty",
    "gunicorn": "Gunicorn",
    "uvicorn": "Uvicorn",
    "werkzeug": "Werkzeug (Flask)",
    "waitress": "Waitress",
    "cowboy": "Cowboy (Erlang)",
    "kestrel": "Kestrel (ASP.NET)",
    "express": "Express.js",
}


class HttpFingerprintPlugin(PluginBase):
    name = "HTTP Fingerprint"
    tool = "http_fingerprint"
    category = "scanning"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """
        HTTP fingerprinting is done in Python, not via external command.
        Return None to use run() method instead.
        """
        return None

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute HTTP fingerprint scan with smart protocol detection."""
        args = args or []
        timeout = 10

        # Parse timeout from args
        for i, arg in enumerate(args):
            if arg == "--timeout" and i + 1 < len(args):
                try:
                    timeout = int(args[i + 1])
                except ValueError:
                    pass

        # Ensure target has scheme
        if not target.startswith(("http://", "https://")):
            target = f"http://{target}"

        try:
            # Use thread-based hard timeout to prevent indefinite hangs
            # urllib timeouts don't always work if server accepts connection but stalls
            from concurrent.futures import ThreadPoolExecutor
            from concurrent.futures import TimeoutError as FuturesTimeout

            hard_timeout = timeout * 3  # 30 seconds max for entire probe operation

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._smart_probe, target, timeout)
                try:
                    result, effective_url = future.result(timeout=hard_timeout)
                except FuturesTimeout:
                    # Hard timeout hit - server is unresponsive
                    result = {
                        "error": f"Timeout: server did not respond within {hard_timeout}s",
                        "status_code": None,
                        "server": None,
                        "waf": [],
                        "cdn": [],
                        "managed_hosting": None,
                        "technologies": [],
                        "headers": {},
                        "cookies": [],
                        "tls": None,
                        "redirect_url": None,
                    }
                    effective_url = target

            output = self._format_output(effective_url, result, label)

            if log_path:
                with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                    fh.write(output)

                    # Skip additional probing if initial fingerprint failed
                    if not result.get("error"):
                        # Fetch robots.txt and sitemap.xml for path discovery
                        robots_paths, sitemap_paths = self._fetch_robots_sitemap(
                            effective_url, timeout
                        )
                        result["robots_paths"] = robots_paths
                        result["sitemap_paths"] = sitemap_paths

                        # Quick path probing for CMS, admin panels, API endpoints
                        quick_probe = self._quick_path_probe(effective_url, timeout)
                        result["cms_detected"] = quick_probe.get("cms")
                        result["admin_panels"] = quick_probe.get("admin_panels", [])
                        result["api_endpoints"] = quick_probe.get("api_endpoints", [])

                        # Write additional detections to log
                        if quick_probe.get("cms"):
                            cms = quick_probe["cms"]
                            fh.write(f"\n{'=' * 40}\n")
                            fh.write(
                                f"CMS DETECTED: {cms['name']} ({cms['confidence']} confidence)\n"
                            )
                            for p in cms["paths"]:
                                fh.write(f"  - {p['path']} (HTTP {p['status']})\n")
                            fh.write(f"{'=' * 40}\n")

                        if quick_probe.get("admin_panels"):
                            fh.write(f"\nADMIN PANELS FOUND:\n")
                            for panel in quick_probe["admin_panels"]:
                                fh.write(
                                    f"  - {panel['name']}: {panel['url']} (HTTP {panel['status']})\n"
                                )

                        if quick_probe.get("api_endpoints"):
                            fh.write(f"\nAPI ENDPOINTS FOUND:\n")
                            for api in quick_probe["api_endpoints"]:
                                fh.write(
                                    f"  - {api['type']}: {api['url']} (HTTP {api['status']})\n"
                                )

                    # Write JSON result for parsing
                    fh.write("\n\n=== JSON_RESULT ===\n")
                    fh.write(json.dumps(result, indent=2))
                    fh.write("\n=== END_JSON_RESULT ===\n")

            return 0

        except Exception as e:
            error_output = f"=== Plugin: HTTP Fingerprint ===\n"
            error_output += f"Target: {target}\n"
            error_output += f"Error: {type(e).__name__}: {e}\n"

            if log_path:
                with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                    fh.write(error_output)

            return 1

    def _smart_probe(self, target: str, timeout: int = 10) -> tuple:
        """
        Smart protocol detection: probe both HTTP and HTTPS, return the better result.

        This handles cases where:
        - nmap reports HTTP but server is actually HTTPS
        - Server serves different content on HTTP vs HTTPS
        - HTTP redirects to HTTPS (or vice versa)

        Returns:
            tuple: (result_dict, effective_url)
        """
        parsed = urlparse(target)

        # Quick connectivity check - fail fast if port isn't responding
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        try:
            with socket.create_connection(
                (host, port), timeout=min(timeout, 5)
            ) as sock:
                pass  # Just checking if we can connect
        except (socket.timeout, socket.error, OSError) as e:
            # Port not responding - return error result immediately
            return {
                "error": f"Connection failed: {e}",
                "status_code": None,
                "server": None,
                "waf": [],
                "cdn": [],
                "managed_hosting": None,
                "technologies": [],
                "headers": {},
                "cookies": [],
                "tls": None,
                "redirect_url": None,
                "protocol_detection": "failed",
                "effective_url": target,
            }, target

        # Build both URL variants
        http_url = (
            f"http://{host}:{port}"
            if port not in (80, 443)
            else f"http://{host}" if port == 80 else f"http://{host}:{port}"
        )
        https_url = (
            f"https://{host}:{port}"
            if port not in (80, 443)
            else f"https://{host}" if port == 443 else f"https://{host}:{port}"
        )

        # Handle standard ports correctly
        if port == 80:
            http_url = f"http://{host}"
            https_url = f"https://{host}:80"  # Non-standard HTTPS on port 80
        elif port == 443:
            http_url = f"http://{host}:443"  # Non-standard HTTP on port 443
            https_url = f"https://{host}"
        else:
            http_url = f"http://{host}:{port}"
            https_url = f"https://{host}:{port}"

        # Probe the original protocol first
        original_is_https = parsed.scheme == "https"
        primary_url = target
        alternate_url = https_url if not original_is_https else http_url

        # Probe primary (original) URL
        primary_result = self._fingerprint(primary_url, timeout)

        # Calculate "richness" score for primary result
        primary_score = self._calculate_result_richness(primary_result)
        primary_status = primary_result.get("status_code") or 0

        # Check if primary result is "good enough" to skip alternate probe
        # Must have: successful status (2xx/3xx), decent score, no errors
        # 4xx/5xx status means we MUST try alternate protocol (could be wrong protocol)
        primary_is_successful = 200 <= primary_status < 400

        if (
            primary_is_successful
            and primary_score >= 3
            and not primary_result.get("error")
        ):
            primary_result["protocol_detection"] = "primary"
            primary_result["effective_url"] = primary_url
            return primary_result, primary_url

        # Otherwise, probe alternate protocol (primary failed, errored, or got 4xx/5xx)
        alternate_result = self._fingerprint(alternate_url, timeout)
        alternate_score = self._calculate_result_richness(alternate_result)

        # Compare and choose the better result
        if alternate_score > primary_score and not alternate_result.get("error"):
            # Alternate protocol is better
            alternate_result["protocol_detection"] = "upgraded"
            alternate_result["protocol_note"] = (
                f"Switched from {parsed.scheme.upper()} to {'HTTPS' if not original_is_https else 'HTTP'} (richer response)"
            )
            alternate_result["original_url"] = primary_url
            alternate_result["effective_url"] = alternate_url
            return alternate_result, alternate_url
        elif not primary_result.get("error"):
            # Primary is fine or equal
            primary_result["protocol_detection"] = "primary"
            primary_result["effective_url"] = primary_url
            return primary_result, primary_url
        elif not alternate_result.get("error"):
            # Primary failed, alternate works
            alternate_result["protocol_detection"] = "fallback"
            alternate_result["protocol_note"] = (
                f"Primary ({parsed.scheme.upper()}) failed, using {'HTTPS' if not original_is_https else 'HTTP'}"
            )
            alternate_result["original_url"] = primary_url
            alternate_result["effective_url"] = alternate_url
            return alternate_result, alternate_url
        else:
            # Both failed, return primary with error
            primary_result["protocol_detection"] = "failed"
            primary_result["effective_url"] = primary_url
            return primary_result, primary_url

    def _calculate_result_richness(self, result: Dict[str, Any]) -> int:
        """
        Calculate a "richness" score for fingerprint results.
        Higher score = more useful/valid response.
        """
        score = 0

        # Error = bad
        if result.get("error"):
            return 0

        # Status code scoring
        status = result.get("status_code")
        if status == 200:
            score += 3
        elif status in (301, 302, 303, 307, 308):
            score += 2  # Redirects are informative
        elif status in (401, 403):
            score += 2  # Auth required = real service
        elif status in (404, 500, 502, 503):
            score += 1  # At least it responded

        # Has server header
        if result.get("server"):
            score += 1

        # Has technologies detected
        if result.get("technologies"):
            score += len(result["technologies"])

        # Has TLS info (means HTTPS worked)
        if result.get("tls"):
            score += 2

        # Has WAF/CDN detection
        if result.get("waf"):
            score += 1
        if result.get("cdn"):
            score += 1

        # Has headers (more headers = richer response)
        headers = result.get("headers", {})
        if len(headers) > 5:
            score += 2
        elif len(headers) > 0:
            score += 1

        return score

    def _fingerprint(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Perform HTTP fingerprinting on target URL.

        Returns dict with:
        - server: Server software detected
        - waf: WAF/protection detected (if any)
        - cdn: CDN detected (if any)
        - managed_hosting: Managed platform detected (if any)
        - headers: Raw response headers
        - technologies: List of detected technologies
        - tls: TLS/SSL information (for HTTPS)
        """
        import urllib.error
        import urllib.request

        # Set global socket timeout to prevent hanging on slow/unresponsive servers
        # This is a safety net - individual requests also have timeouts
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout + 5)  # Slightly longer than request timeout

        result = {
            "server": None,
            "server_version": None,
            "waf": [],
            "cdn": [],
            "managed_hosting": None,
            "technologies": [],
            "headers": {},
            "cookies": [],
            "tls": None,
            "status_code": None,
            "redirect_url": None,
        }

        parsed = urlparse(url)

        # Security: Only allow http/https schemes (B310 - prevent file:// or custom schemes)
        if parsed.scheme not in ("http", "https"):
            result["error"] = (
                f"Invalid URL scheme: {parsed.scheme}. Only http/https allowed."
            )
            return result

        is_https = parsed.scheme == "https"

        # Check if target is an IP address (for special handling)
        import re

        is_ip_target = bool(re.match(r"^(\d{1,3}\.){3}\d{1,3}$", parsed.hostname or ""))

        # Create request with common browser headers
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
        )

        # Always create SSL context with verification disabled
        # This handles: 1) HTTPS targets, 2) HTTP->HTTPS redirects, 3) IP targets with invalid certs
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            # Get TLS info for HTTPS targets
            if is_https:
                try:
                    with socket.create_connection(
                        (parsed.hostname, parsed.port or 443), timeout=timeout
                    ) as sock:
                        with ctx.wrap_socket(
                            sock, server_hostname=parsed.hostname
                        ) as ssock:
                            cert = ssock.getpeercert(binary_form=True)
                            cipher = ssock.cipher()
                            version = ssock.version()
                            result["tls"] = {
                                "version": version,
                                "cipher": cipher[0] if cipher else None,
                                "bits": cipher[2] if cipher else None,
                            }
                except Exception:
                    pass  # TLS info is optional

            # Always pass SSL context (handles HTTP->HTTPS redirects)
            response = urllib.request.urlopen(
                req, timeout=timeout, context=ctx
            )  # nosec B310 - scheme validated above

            result["status_code"] = response.getcode()

            # Get headers
            headers = {k.lower(): v for k, v in response.headers.items()}
            result["headers"] = dict(response.headers)

            # Check for redirect
            if response.geturl() != url:
                result["redirect_url"] = response.geturl()

            # Parse cookies
            if "set-cookie" in headers:
                cookies = headers.get("set-cookie", "")
                result["cookies"] = [c.strip() for c in cookies.split(",")]

            # Detect server
            server_header = headers.get("server", "").lower()
            result["server"] = headers.get("server")

            for sig, name in SERVER_SIGNATURES.items():
                if sig in server_header:
                    result["server_version"] = name
                    result["technologies"].append(name)
                    break

            # Detect WAF
            result["waf"] = self._detect_waf(headers, result["cookies"])

            # Detect CDN
            result["cdn"] = self._detect_cdn(headers, server_header)

            # Detect managed hosting
            result["managed_hosting"] = self._detect_managed_hosting(
                headers, server_header, result["cookies"]
            )

            # Detect technologies from headers
            self._detect_technologies(headers, result)

        except urllib.error.HTTPError as e:
            # Even errors give us useful headers
            result["status_code"] = e.code
            headers = {k.lower(): v for k, v in e.headers.items()}
            result["headers"] = dict(e.headers)
            result["server"] = headers.get("server")

            server_header = headers.get("server", "").lower()
            result["waf"] = self._detect_waf(headers, [])
            result["cdn"] = self._detect_cdn(headers, server_header)
            result["managed_hosting"] = self._detect_managed_hosting(
                headers, server_header, []
            )

        except urllib.error.URLError as e:
            result["error"] = str(e.reason)

        except socket.timeout:
            result["error"] = "Connection timed out"

        except Exception as e:
            result["error"] = f"{type(e).__name__}: {e}"

        finally:
            # Restore original socket timeout
            socket.setdefaulttimeout(old_timeout)

        return result

    def _detect_waf(self, headers: Dict[str, str], cookies: List[str]) -> List[str]:
        """Detect WAF from headers and cookies."""
        detected = []

        # Check headers
        for header, signatures in WAF_SIGNATURES["headers"].items():
            header_val = headers.get(header, "").lower()
            if header_val:
                if isinstance(signatures, dict):
                    for sig, waf_name in signatures.items():
                        if sig == "" or sig in header_val:
                            if waf_name and waf_name not in detected:
                                detected.append(waf_name)
                elif isinstance(signatures, str) and signatures not in detected:
                    detected.append(signatures)

        # Check cookies
        cookie_str = " ".join(cookies).lower()
        for cookie_sig, waf_name in WAF_SIGNATURES["cookies"].items():
            if cookie_sig.lower() in cookie_str:
                if waf_name not in detected:
                    detected.append(waf_name)

        return detected

    def _detect_cdn(self, headers: Dict[str, str], server_header: str) -> List[str]:
        """Detect CDN from headers."""
        detected = []

        # Check specific headers
        for header, cdn_info in CDN_SIGNATURES["headers"].items():
            header_val = headers.get(header, "").lower()
            if header_val:
                if isinstance(cdn_info, dict):
                    for sig, cdn_name in cdn_info.items():
                        if sig in header_val and cdn_name not in detected:
                            detected.append(cdn_name)
                elif isinstance(cdn_info, str) and cdn_info not in detected:
                    detected.append(cdn_info)

        # Check server header
        for sig, cdn_name in CDN_SIGNATURES["server"].items():
            if sig in server_header and cdn_name not in detected:
                detected.append(cdn_name)

        return detected

    def _detect_managed_hosting(
        self, headers: Dict[str, str], server_header: str, cookies: List[str]
    ) -> Optional[str]:
        """Detect managed hosting platform."""
        # Check server header first (most reliable)
        for sig, platform in MANAGED_HOSTING_SIGNATURES["server"].items():
            if sig in server_header:
                return platform

        # Check specific headers
        for header_prefix, platform in MANAGED_HOSTING_SIGNATURES["headers"].items():
            for header in headers:
                if header.lower().startswith(header_prefix.lower()):
                    return platform

        # Check cookies
        cookie_str = " ".join(cookies).lower()
        for cookie_sig, platform in MANAGED_HOSTING_SIGNATURES["cookies"].items():
            if cookie_sig.lower() in cookie_str:
                return platform

        return None

    def _detect_technologies(self, headers: Dict[str, str], result: Dict[str, Any]):
        """Detect additional technologies from headers."""
        techs = result["technologies"]

        # X-Powered-By
        powered_by = headers.get("x-powered-by", "")
        if powered_by:
            if "php" in powered_by.lower():
                techs.append(f"PHP ({powered_by})")
            elif "asp.net" in powered_by.lower():
                techs.append(f"ASP.NET ({powered_by})")
            elif "express" in powered_by.lower():
                techs.append("Express.js")
            elif powered_by not in techs:
                techs.append(powered_by)

        # X-AspNet-Version
        aspnet_ver = headers.get("x-aspnet-version", "")
        if aspnet_ver:
            techs.append(f"ASP.NET {aspnet_ver}")

        # X-Generator
        generator = headers.get("x-generator", "")
        if generator:
            techs.append(generator)

        result["technologies"] = list(set(techs))

    def _fetch_robots_sitemap(self, base_url: str, timeout: int = 10) -> tuple:
        """
        Fetch robots.txt and sitemap.xml to extract paths for discovery.

        This runs early in the recon chain so discovered paths can trigger
        follow-up scans even if gobuster's wordlist doesn't include them.

        Returns:
            tuple: (robots_paths, sitemap_paths) - lists of discovered URLs
        """
        import re
        import urllib.error
        import urllib.request
        from urllib.parse import urljoin

        try:
            import defusedxml.ElementTree as ElementTree
        except ImportError:
            import xml.etree.ElementTree as ElementTree

        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        robots_paths = []
        sitemap_paths = []

        # Create SSL context for self-signed certs
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # === Fetch robots.txt ===
        try:
            robots_url = urljoin(base + "/", "robots.txt")
            req = urllib.request.Request(
                robots_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SoulEyez/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
                if response.getcode() == 200:
                    content = response.read().decode("utf-8", errors="replace")

                    # Known directives to skip
                    known_directives = [
                        "user-agent:",
                        "disallow:",
                        "allow:",
                        "sitemap:",
                        "crawl-delay:",
                        "host:",
                        "request-rate:",
                    ]

                    for line in content.split("\n"):
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue

                        line_lower = line.lower()

                        # Extract Disallow/Allow paths
                        if line_lower.startswith("disallow:") or line_lower.startswith(
                            "allow:"
                        ):
                            _, _, path = line.partition(":")
                            path = path.strip()
                            if (
                                path
                                and path != "/"
                                and "*" not in path
                                and "?" not in path
                            ):
                                full_url = urljoin(base + "/", path.lstrip("/"))
                                if full_url not in robots_paths:
                                    robots_paths.append(full_url)

                        # Extract Sitemap URLs
                        elif line_lower.startswith("sitemap:"):
                            _, _, sitemap_url = line.partition(":")
                            sitemap_url = sitemap_url.strip()
                            # Handle "Sitemap: http://..." format
                            if sitemap_url.startswith("//"):
                                sitemap_url = parsed.scheme + ":" + sitemap_url
                            elif not sitemap_url.startswith("http"):
                                sitemap_url = urljoin(
                                    base + "/", sitemap_url.lstrip("/")
                                )
                            if sitemap_url not in sitemap_paths:
                                sitemap_paths.append(sitemap_url)

                        # Extract bare file paths (CTF-style hints like "key-1-of-3.txt")
                        elif not any(
                            line_lower.startswith(d) for d in known_directives
                        ):
                            path = line.strip()
                            # Must look like a file with extension
                            if path and re.match(r"^[\w\-./]+\.\w{1,5}$", path):
                                full_url = urljoin(base + "/", path.lstrip("/"))
                                if full_url not in robots_paths:
                                    robots_paths.append(full_url)

        except Exception:
            pass  # robots.txt fetch is optional

        # === Fetch sitemap.xml (if not found in robots.txt) ===
        if not sitemap_paths:
            sitemap_paths.append(urljoin(base + "/", "sitemap.xml"))

        # Try to parse each sitemap
        all_sitemap_urls = []
        for sitemap_url in sitemap_paths[:3]:  # Limit to first 3 sitemaps
            try:
                req = urllib.request.Request(
                    sitemap_url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; SoulEyez/1.0)"},
                )
                with urllib.request.urlopen(
                    req, timeout=timeout, context=ctx
                ) as response:
                    if response.getcode() == 200:
                        content = response.read().decode("utf-8", errors="replace")
                        try:
                            root = ElementTree.fromstring(content)
                            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                            # Try with namespace
                            for loc in root.findall(".//sm:loc", ns):
                                if loc.text and loc.text not in all_sitemap_urls:
                                    all_sitemap_urls.append(loc.text.strip())

                            # Try without namespace
                            if not all_sitemap_urls:
                                for loc in root.findall(".//loc"):
                                    if loc.text and loc.text not in all_sitemap_urls:
                                        all_sitemap_urls.append(loc.text.strip())

                        except ElementTree.ParseError:
                            # Fallback to regex
                            loc_matches = re.findall(r"<loc>([^<]+)</loc>", content)
                            for url in loc_matches:
                                if url not in all_sitemap_urls:
                                    all_sitemap_urls.append(url)

            except Exception:
                pass  # sitemap fetch is optional

        # Replace sitemap_paths with actual URLs from sitemaps (limit to 50)
        if all_sitemap_urls:
            sitemap_paths = all_sitemap_urls[:50]
        else:
            sitemap_paths = []  # Clear if sitemap didn't exist

        return robots_paths, sitemap_paths

    def _quick_path_probe(self, base_url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Quick path probing for CMS detection, admin panels, and API indicators.

        Uses HEAD requests to minimize bandwidth and noise. Only checks paths
        that return 2xx/3xx/401/403 status codes (indicates existence).

        Returns:
            dict: {
                'cms': {'name': str, 'paths': list} or None,
                'admin_panels': [{'path': str, 'status': int}],
                'api_endpoints': [{'path': str, 'status': int, 'type': str}]
            }
        """
        import urllib.error
        import urllib.request

        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        # Create SSL context for self-signed certs
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        result = {"cms": None, "admin_panels": [], "api_endpoints": []}

        # Define paths to check
        # Format: (path, category, subcategory/type)
        paths_to_check = [
            # CMS Detection
            ("/wp-admin/", "cms", "WordPress"),
            ("/wp-login.php", "cms", "WordPress"),
            ("/wp-includes/", "cms", "WordPress"),
            ("/administrator/", "cms", "Joomla"),
            ("/components/com_content/", "cms", "Joomla"),
            ("/user/login", "cms", "Drupal"),
            ("/core/misc/drupal.js", "cms", "Drupal"),
            ("/typo3/", "cms", "TYPO3"),
            ("/sitecore/", "cms", "Sitecore"),
            # Admin Panels
            ("/phpmyadmin/", "admin", "phpMyAdmin"),
            ("/pma/", "admin", "phpMyAdmin"),
            ("/admin/", "admin", "Admin Panel"),
            ("/admin/login", "admin", "Admin Login"),
            ("/login/", "admin", "Login Page"),
            ("/login.php", "admin", "Login Page"),
            ("/manager/", "admin", "Manager"),
            ("/cpanel/", "admin", "cPanel"),
            ("/webmail/", "admin", "Webmail"),
            # API Indicators
            ("/api/", "api", "REST API"),
            ("/api/v1/", "api", "REST API v1"),
            ("/api/v2/", "api", "REST API v2"),
            ("/graphql", "api", "GraphQL"),
            ("/graphql/", "api", "GraphQL"),
            ("/swagger.json", "api", "Swagger/OpenAPI"),
            ("/swagger/", "api", "Swagger UI"),
            ("/openapi.json", "api", "OpenAPI"),
            ("/api-docs/", "api", "API Docs"),
            ("/v1/", "api", "API v1"),
            ("/rest/", "api", "REST API"),
        ]

        # Track CMS detections to avoid duplicates
        cms_detected = {}

        # CMS-specific content markers to verify detection (prevents SPA false positives)
        cms_content_markers = {
            "WordPress": [
                b"wp-login",
                b"wp-includes",
                b"wp-content",
                b"wordpress",
                b"wlwmanifest",
                b"xmlrpc.php",
            ],
            "Joomla": [b"joomla", b"com_content", b"/administrator/"],
            "Drupal": [b"drupal", b"sites/default", b"sites/all"],
            "TYPO3": [b"typo3", b"typo3conf"],
            "Sitecore": [b"sitecore"],
        }

        for path, category, subtype in paths_to_check:
            try:
                url = base.rstrip("/") + path

                # For CMS detection, use GET to verify content (prevents SPA false positives)
                # SPAs return 200 for all routes but with same content
                if category == "cms":
                    req = urllib.request.Request(
                        url,
                        method="GET",
                        headers={
                            "User-Agent": "Mozilla/5.0 (compatible; SoulEyez/1.0)"
                        },
                    )
                    try:
                        with urllib.request.urlopen(
                            req, timeout=timeout, context=ctx
                        ) as response:
                            status = response.getcode()
                            # Read first 4KB to check for CMS markers
                            content = response.read(4096).lower()
                    except urllib.error.HTTPError as e:
                        status = e.code
                        content = b""

                    # Verify response contains CMS-specific content
                    if status in (200, 301, 302, 401, 403):
                        markers = cms_content_markers.get(subtype, [])
                        has_cms_content = any(marker in content for marker in markers)
                        if has_cms_content:
                            if subtype not in cms_detected:
                                cms_detected[subtype] = []
                            cms_detected[subtype].append(
                                {"path": path, "status": status}
                            )
                    continue

                # For admin/API detection, HEAD is fine (just checking existence)
                req = urllib.request.Request(
                    url,
                    method="HEAD",
                    headers={"User-Agent": "Mozilla/5.0 (compatible; SoulEyez/1.0)"},
                )

                try:
                    with urllib.request.urlopen(
                        req, timeout=timeout, context=ctx
                    ) as response:
                        status = response.getcode()
                except urllib.error.HTTPError as e:
                    status = e.code

                # Consider 2xx, 3xx, 401, 403 as "exists"
                if status in (200, 201, 204, 301, 302, 303, 307, 308, 401, 403):
                    if category == "admin":
                        result["admin_panels"].append(
                            {
                                "path": path,
                                "name": subtype,
                                "status": status,
                                "url": url,
                            }
                        )
                    elif category == "api":
                        result["api_endpoints"].append(
                            {
                                "path": path,
                                "type": subtype,
                                "status": status,
                                "url": url,
                            }
                        )

            except Exception:
                # Timeout or connection error - skip this path
                continue

        # Determine primary CMS (most path matches)
        if cms_detected:
            best_cms = max(cms_detected.items(), key=lambda x: len(x[1]))
            result["cms"] = {
                "name": best_cms[0],
                "paths": best_cms[1],
                "confidence": "high" if len(best_cms[1]) >= 2 else "medium",
            }

        return result

    def _format_output(self, target: str, result: Dict[str, Any], label: str) -> str:
        """Format fingerprint results for log output."""
        lines = []
        lines.append("=== Plugin: HTTP Fingerprint ===")
        lines.append(f"Target: {target}")
        if label:
            lines.append(f"Label: {label}")
        lines.append(
            f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
        )
        lines.append("=" * 60)
        lines.append("")

        if result.get("error"):
            lines.append(f"ERROR: {result['error']}")
            return "\n".join(lines)

        # Protocol detection info (smart probe results)
        protocol_detection = result.get("protocol_detection")
        if protocol_detection in ("upgraded", "fallback"):
            lines.append("-" * 40)
            lines.append(f"PROTOCOL DETECTION: {protocol_detection.upper()}")
            if result.get("protocol_note"):
                lines.append(f"  {result['protocol_note']}")
            if result.get("original_url"):
                lines.append(f"  Original URL: {result['original_url']}")
            lines.append(f"  Effective URL: {result.get('effective_url', target)}")
            lines.append("-" * 40)
            lines.append("")

        # Status
        lines.append(f"HTTP Status: {result.get('status_code', 'N/A')}")

        if result.get("redirect_url"):
            lines.append(f"Redirected to: {result['redirect_url']}")

        # Server
        if result.get("server"):
            lines.append(f"Server: {result['server']}")

        # TLS
        if result.get("tls"):
            tls = result["tls"]
            lines.append(
                f"TLS: {tls.get('version', 'Unknown')} ({tls.get('cipher', 'Unknown')})"
            )

        lines.append("")

        # Managed Hosting (most important for tool decisions)
        if result.get("managed_hosting"):
            lines.append("-" * 40)
            lines.append(f"MANAGED HOSTING DETECTED: {result['managed_hosting']}")
            lines.append("  -> CGI enumeration will be skipped")
            lines.append("  -> Limited vulnerability surface expected")
            lines.append("-" * 40)
            lines.append("")

        # WAF
        if result.get("waf"):
            lines.append(f"WAF/Protection Detected:")
            for waf in result["waf"]:
                lines.append(f"  - {waf}")
            lines.append("")

        # CDN
        if result.get("cdn"):
            lines.append(f"CDN Detected:")
            for cdn in result["cdn"]:
                lines.append(f"  - {cdn}")
            lines.append("")

        # Technologies
        if result.get("technologies"):
            lines.append(f"Technologies:")
            for tech in result["technologies"]:
                lines.append(f"  - {tech}")
            lines.append("")

        # Robots.txt paths (discovered files/directories)
        robots_paths = result.get("robots_paths", [])
        if robots_paths:
            lines.append("-" * 40)
            lines.append(f"ROBOTS.TXT PATHS ({len(robots_paths)} found):")
            for path in robots_paths[:20]:
                lines.append(f"  - {path}")
            if len(robots_paths) > 20:
                lines.append(f"  ... and {len(robots_paths) - 20} more")
            lines.append("-" * 40)
            lines.append("")

        # Sitemap URLs
        sitemap_paths = result.get("sitemap_paths", [])
        if sitemap_paths:
            lines.append(f"SITEMAP URLS ({len(sitemap_paths)} found):")
            for url in sitemap_paths[:10]:
                lines.append(f"  - {url}")
            if len(sitemap_paths) > 10:
                lines.append(f"  ... and {len(sitemap_paths) - 10} more")
            lines.append("")

        lines.append(
            f"\n=== Completed: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} ==="
        )

        return "\n".join(lines)


plugin = HttpFingerprintPlugin()
