#!/usr/bin/env python3
"""
souleyez.core.tool_chaining - Intelligent tool chaining and workflow automation

Automatically triggers follow-up scans based on discovered services and findings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

# Category constants for chain rules
CATEGORY_CTF = "ctf"  # Lab/learning scenarios - vulnerable by design
CATEGORY_ENTERPRISE = "enterprise"  # Real-world enterprise testing
CATEGORY_GENERAL = "general"  # Standard recon that applies everywhere

# Managed hosting platforms - skip CGI enumeration (pointless on these)
# These are detected from server headers/banners and product names
MANAGED_HOSTING_PLATFORMS = {
    "squarespace",
    "wix",
    "shopify",
    "webflow",
    "weebly",
    "wordpress.com",
    "ghost.io",
    "medium",
    "tumblr",
    "blogger",
    "netlify",
    "vercel",
    "github.io",
    "pages.dev",
    "cloudflare",
    "heroku",
    "railway",
    "render.com",
    "fly.io",
    "aws cloudfront",
    "akamai",
    "fastly",
    "cloudflare",
    "azure",
    "google cloud",
    "firebase",
}

# Category display icons
CATEGORY_ICONS = {
    CATEGORY_CTF: "🎯",
    CATEGORY_ENTERPRISE: "🏢",
    CATEGORY_GENERAL: "⚙️",
}

# Service groups for smarter condition matching
# When matching 'service:http', also match these services/ports
SERVICE_GROUPS = {
    "http": {
        "services": ["http", "https", "http-alt", "http-proxy", "https-alt"],
        # Port 11434 is Ollama API - runs HTTP but nmap often identifies as "unknown"
        "ports": [80, 443, 8080, 8000, 8443, 3000, 5000, 8888, 9000, 9090, 11434],
    },
    "smb": {
        "services": ["microsoft-ds", "netbios-ssn", "smb"],
        "ports": [445, 139],
    },
    "database": {
        "services": ["mysql", "postgresql", "ms-sql-s", "oracle", "mongodb"],
        "ports": [3306, 5432, 1433, 1521, 27017],
    },
    "ldap": {
        "services": ["ldap", "ldaps"],
        "ports": [389, 636],
    },
    "rdp": {
        "services": ["ms-wbt-server", "rdp"],
        "ports": [3389],
    },
    "ssh": {
        "services": ["ssh"],
        "ports": [22, 2222],
    },
    "ftp": {
        "services": ["ftp", "ftps"],
        "ports": [21, 990],
    },
    # macOS-specific services
    "afp": {
        "services": ["afp", "afpovertcp"],
        "ports": [548],
    },
    "ard": {
        "services": ["vnc", "rfb", "ard", "apple-remote-desktop"],
        "ports": [5900, 3283],
    },
    "mdns": {
        "services": ["mdns", "zeroconf", "bonjour"],
        "ports": [5353],
    },
    # Router-specific services
    "upnp": {
        "services": ["upnp", "ssdp"],
        "ports": [1900, 2869],
    },
    "tr069": {
        "services": ["tr-069", "cwmp", "acs"],
        "ports": [7547, 4567],
    },
    "telnet": {
        "services": ["telnet"],
        "ports": [23],
    },
}


def should_test_url_for_sqli(endpoint_url: str) -> bool:
    """
    Determine if a URL should be tested for SQL injection.

    This filters out URLs that are unlikely to have injectable parameters,
    while allowing URLs that might have forms or query parameters.

    Args:
        endpoint_url: The URL to evaluate

    Returns:
        True if the URL should be tested, False if it should be skipped

    Examples:
        >>> should_test_url_for_sqli("http://example.com/payroll_app.php")
        True  # Dynamic page, might have forms
        >>> should_test_url_for_sqli("http://example.com/index.php")
        False  # Common default page, rarely injectable
        >>> should_test_url_for_sqli("http://example.com/search.php?q=test")
        True  # Has query parameters
        >>> should_test_url_for_sqli("http://example.com/phpinfo.php")
        False  # phpinfo output, not injectable
        >>> should_test_url_for_sqli("http://example.com/cgi-bin/")
        False  # Directory, not a script
        >>> should_test_url_for_sqli("http://example.com/")
        False  # No path, no params
    """
    from urllib.parse import urlparse

    path_lower = endpoint_url.lower()
    has_params = "?" in endpoint_url

    # URLs with query params should generally be tested - they have injection points
    # But still skip known non-injectable apps even with params
    if has_params:
        # Even with params, skip known non-injectable applications
        hard_skip = [
            "/phpmyadmin/",  # phpMyAdmin - DB admin tool, not a target
            "/phpmyadmin?",  # phpMyAdmin with params
        ]
        if any(pattern in path_lower for pattern in hard_skip):
            return False
        # Skip static files with version/cache-busting params
        # These are not injectable: /jquery.js?v=1.2.3, /style.css?ver=5.0
        if ".js?" in path_lower or ".css?" in path_lower:
            return False
        # Has params and not in hard skip - test it
        return True

    # No query params - apply stricter filtering
    # Skip known non-injectable paths (only when no params)
    skip_patterns = [
        "/twiki/",  # TWiki wiki - not SQLi vulnerable
        "/phpmyadmin/",  # phpMyAdmin - DB admin, not SQLi target
        "/phpmyadmin.",  # phpMyAdmin CSS/JS files
        "/phpinfo",  # phpinfo() output - no injection
        "/cgi-bin/",  # Base CGI dir without script - no injection
        "/misc/",  # Drupal/CMS static assets directory
        "/modules/",  # Drupal modules directory (static files)
    ]
    if any(pattern in path_lower for pattern in skip_patterns):
        return False

    # No params - require dynamic extension that might have forms
    dynamic_extensions = (".php", ".asp", ".aspx", ".jsp", ".do", ".action", ".cgi")
    is_dynamic = any(path_lower.endswith(ext) for ext in dynamic_extensions)

    if not is_dynamic:
        # No params and not a dynamic page - skip
        return False

    # Skip common default/utility pages that rarely have injectable forms
    useless_dynamic_pages = [
        "/index.php",
        "/index.asp",
        "/index.aspx",
        "/index.jsp",
        "/default.php",
        "/default.asp",
        "/default.aspx",
        "/home.php",
        "/home.asp",
        "/info.php",
        "/test.php",
    ]
    if not has_params:
        # Only check this list for pages without params
        try:
            parsed = urlparse(endpoint_url)
            if parsed.path.lower() in useless_dynamic_pages:
                return False
        except Exception:
            pass

    return True


def classify_os_device(os_string: str, services: list) -> dict:
    """
    Classify OS and device type from nmap output.

    Args:
        os_string: OS detection string from nmap (e.g., "Linux 4.x", "Mac OS X 10.15")
        services: List of service dicts with 'port', 'service_name' keys

    Returns:
        {
            'os_family': 'macos' | 'linux' | 'windows' | 'ios' | 'router' | 'unknown',
            'device_type': 'desktop' | 'server' | 'router' | 'mobile' | 'unknown',
            'vendor': Optional vendor string (e.g., 'apple', 'cisco', 'netgear')
        }
    """
    os_lower = (os_string or "").lower()
    ports = {s.get("port") for s in services if s.get("port")}
    service_names = {s.get("service_name", "").lower() for s in services}

    # macOS detection
    if any(x in os_lower for x in ["macos", "mac os", "darwin", "os x", "apple mac"]):
        return {"os_family": "macos", "device_type": "desktop", "vendor": "apple"}

    # iOS detection
    if any(x in os_lower for x in ["ios", "iphone", "ipad", "ipod"]):
        return {"os_family": "ios", "device_type": "mobile", "vendor": "apple"}

    # Router detection - by service ports and OS strings
    router_ports = {1900, 7547, 8080, 8443}  # UPnP, TR-069, admin panels
    router_keywords = [
        "router",
        "gateway",
        "mikrotik",
        "openwrt",
        "dd-wrt",
        "tomato",
        "netgear",
        "linksys",
        "tp-link",
        "asus rt",
        "d-link",
        "zyxel",
    ]
    if any(x in os_lower for x in router_keywords):
        vendor = None
        for v in [
            "netgear",
            "linksys",
            "tp-link",
            "asus",
            "d-link",
            "zyxel",
            "cisco",
            "mikrotik",
        ]:
            if v in os_lower:
                vendor = v
                break
        return {"os_family": "linux", "device_type": "router", "vendor": vendor}

    # Check for router by typical service combination (UPnP + web + no SSH or common router services)
    if (ports & router_ports) and ("upnp" in service_names or "ssdp" in service_names):
        return {"os_family": "linux", "device_type": "router", "vendor": None}

    # Windows detection
    if any(x in os_lower for x in ["windows", "win32", "win64", "microsoft"]):
        return {"os_family": "windows", "device_type": "desktop", "vendor": "microsoft"}

    # Linux server/general detection
    if "linux" in os_lower:
        # Check if it looks like a server (common server ports)
        server_ports = {22, 80, 443, 3306, 5432, 6379, 27017}
        if ports & server_ports:
            return {"os_family": "linux", "device_type": "server", "vendor": None}
        return {"os_family": "linux", "device_type": "desktop", "vendor": None}

    return {"os_family": "unknown", "device_type": "unknown", "vendor": None}


def is_managed_hosting(
    services: List[Dict[str, Any]], http_fingerprint: Dict[str, Any] = None
) -> bool:
    """
    Detect if target is a managed hosting platform.

    These platforms don't have CGI directories, so tools like nikto
    should skip CGI enumeration to avoid long, pointless scans.

    Args:
        services: List of service dicts from nmap parser
        http_fingerprint: Optional fingerprint data from http_fingerprint plugin

    Returns:
        True if managed hosting detected, False otherwise
    """
    # Check fingerprint data first (most reliable, comes from actual HTTP headers)
    if http_fingerprint:
        managed = http_fingerprint.get("managed_hosting")
        if managed:
            return True

    # Fall back to checking services data (less reliable, from nmap banners)
    for service in services:
        # Check product field
        product = (service.get("product") or "").lower()
        raw_version = (service.get("raw_version") or "").lower()
        service_name = (service.get("service") or "").lower()

        # Combine all fields for matching
        combined = f"{product} {raw_version} {service_name}"

        # Check against known managed hosting platforms
        for platform in MANAGED_HOSTING_PLATFORMS:
            if platform in combined:
                return True

    return False


def get_managed_hosting_platform(
    services: List[Dict[str, Any]], http_fingerprint: Dict[str, Any] = None
) -> Optional[str]:
    """
    Get the name of the managed hosting platform if detected.

    Args:
        services: List of service dicts from nmap parser
        http_fingerprint: Optional fingerprint data from http_fingerprint plugin

    Returns:
        Platform name or None
    """
    # Check fingerprint data first
    if http_fingerprint:
        managed = http_fingerprint.get("managed_hosting")
        if managed:
            return managed

    # Fall back to services check
    for service in services:
        product = (service.get("product") or "").lower()
        raw_version = (service.get("raw_version") or "").lower()
        service_name = (service.get("service") or "").lower()
        combined = f"{product} {raw_version} {service_name}"

        for platform in MANAGED_HOSTING_PLATFORMS:
            if platform in combined:
                return platform.title()

    return None


# =============================================================================
# SMART SCANNING - Noise Reduction Filters
# =============================================================================
# These patterns identify URLs/paths that should be skipped for specific tools
# to reduce noise and wasted scans.

import logging
import re

logger = logging.getLogger(__name__)


class SmartFilter:
    """
    Smart filtering to reduce noise in auto-chaining.

    Identifies URLs, paths, and contexts that should be skipped for specific tools.
    """

    # Patterns to skip for SQLMap (not injectable or redundant)
    SQLMAP_SKIP_PATTERNS = [
        # Apache directory listing sort parameters (not injectable)
        re.compile(r"\?C=[DMNS];O=[AD]$", re.IGNORECASE),
        re.compile(r"\?C=[DMNS]$", re.IGNORECASE),
        # Drupal routing (internal, not injectable)
        re.compile(r"\?q=node/\d+", re.IGNORECASE),
        re.compile(r"\?q=user", re.IGNORECASE),
        re.compile(r"\?q=admin", re.IGNORECASE),
        # phpMyAdmin (already a SQL interface - redundant)
        re.compile(r"/phpmyadmin", re.IGNORECASE),
        re.compile(r"/pma/", re.IGNORECASE),
        re.compile(r"/mysql/", re.IGNORECASE),
        re.compile(r"/adminer", re.IGNORECASE),
        # Command execution params (RCE, not SQLi)
        re.compile(r"[?&](cmd|exec|command|run|system)=", re.IGNORECASE),
        # Static resource paths (not injectable)
        re.compile(
            r"\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|ttf|eot)(\?|$)", re.IGNORECASE
        ),
        # Internal framework paths
        re.compile(r"/wp-includes/", re.IGNORECASE),
        re.compile(r"/wp-content/plugins/", re.IGNORECASE),
        re.compile(r"/sites/default/files/", re.IGNORECASE),
    ]

    # Patterns to skip for Gobuster (not directories)
    GOBUSTER_SKIP_PATTERNS = [
        # Individual files - gobuster should only run on directories
        re.compile(
            r"\.(php|asp|aspx|jsp|cgi|pl|py|rb|html|htm|txt|xml|json)$", re.IGNORECASE
        ),
        # URLs with query parameters (gobuster is for directory discovery)
        re.compile(r"\?"),
    ]

    # Patterns to skip for FFUF (already fuzzing similar paths)
    FFUF_SKIP_PATTERNS = [
        # Static resources
        re.compile(r"\.(js|css|png|jpg|jpeg|gif|svg|ico)(\?|$)", re.IGNORECASE),
    ]

    # Patterns indicating internal/framework paths (low value for most scans)
    INTERNAL_PATH_PATTERNS = [
        re.compile(r"/js/", re.IGNORECASE),
        re.compile(r"/css/", re.IGNORECASE),
        re.compile(r"/images/", re.IGNORECASE),
        re.compile(r"/assets/", re.IGNORECASE),
        re.compile(r"/static/", re.IGNORECASE),
        re.compile(r"/fonts/", re.IGNORECASE),
        re.compile(r"/vendor/", re.IGNORECASE),
        re.compile(r"/node_modules/", re.IGNORECASE),
    ]

    # Technology-specific skip rules
    # Format: {detected_tech: {tool: reason}}
    TECH_SKIP_RULES = {
        "phpmyadmin": {
            "sqlmap": "phpMyAdmin is already a SQL interface",
            "nuclei": None,  # Still run nuclei for vulns
        },
        "drupal": {
            "wpscan": "WPScan only works on WordPress",
        },
        "wordpress": {
            # No skips - WordPress should get full scanning
        },
        "joomla": {
            "wpscan": "WPScan only works on WordPress",
        },
    }

    # Tools that require specific technology to be detected
    # If tech is NOT confirmed, skip the tool
    TECH_REQUIRED = {
        "wpscan": ["wordpress"],  # WPScan only makes sense on WordPress
    }

    @classmethod
    def should_skip_for_tool(
        cls, tool: str, target: str, context: Dict[str, Any] = None
    ) -> tuple:
        """
        Check if a target should be skipped for a specific tool.

        Args:
            tool: Tool name (sqlmap, gobuster, etc.)
            target: Target URL or path
            context: Optional context with technology detection

        Returns:
            (should_skip: bool, reason: str or None)
        """
        tool_lower = tool.lower()
        context = context or {}

        # Check tool-specific patterns
        if tool_lower == "sqlmap":
            for pattern in cls.SQLMAP_SKIP_PATTERNS:
                if pattern.search(target):
                    return (True, f"Matches skip pattern: {pattern.pattern}")
            # NOTE: Don't filter URLs without query params - POST injections
            # and --forms/--crawl find injection points without GET params

        elif tool_lower == "gobuster":
            for pattern in cls.GOBUSTER_SKIP_PATTERNS:
                if pattern.search(target):
                    return (True, f"Not a directory: {pattern.pattern}")

        elif tool_lower == "ffuf":
            for pattern in cls.FFUF_SKIP_PATTERNS:
                if pattern.search(target):
                    return (True, f"Static resource: {pattern.pattern}")

        # Check internal paths (skip for most offensive tools)
        if tool_lower in ["sqlmap", "nuclei", "ffuf"]:
            for pattern in cls.INTERNAL_PATH_PATTERNS:
                if pattern.search(target):
                    return (True, f"Internal/static path: {pattern.pattern}")

        # Check technology-specific skips
        detected_tech = context.get("technology", "").lower()
        if detected_tech and detected_tech in cls.TECH_SKIP_RULES:
            tech_rules = cls.TECH_SKIP_RULES[detected_tech]
            if tool_lower in tech_rules:
                reason = tech_rules[tool_lower]
                if reason:
                    return (True, reason)

        # Check if tool requires specific technology
        if tool_lower in cls.TECH_REQUIRED:
            required_techs = cls.TECH_REQUIRED[tool_lower]
            # Check if any required tech is confirmed
            is_confirmed = context.get("wordpress_confirmed", False)

            # For wpscan, check various confirmation signals
            if tool_lower == "wpscan":
                is_confirmed = (
                    context.get("wordpress_confirmed", False)
                    or context.get("is_wordpress", False)
                    or detected_tech == "wordpress"
                    or
                    # Check if any CMS detection shows WordPress
                    "wordpress" in str(context.get("cms", "")).lower()
                )

            if not is_confirmed:
                return (
                    True,
                    f"{tool} requires confirmed {'/'.join(required_techs)} detection",
                )

        return (False, None)

    @classmethod
    def filter_targets(
        cls, tool: str, targets: List[str], context: Dict[str, Any] = None
    ) -> List[str]:
        """
        Filter a list of targets, removing ones that should be skipped.

        Args:
            tool: Tool name
            targets: List of target URLs/paths
            context: Optional context

        Returns:
            Filtered list of targets
        """
        filtered = []
        for target in targets:
            should_skip, reason = cls.should_skip_for_tool(tool, target, context)
            if should_skip:
                logger.debug(f"SmartFilter: Skipping {target} for {tool}: {reason}")
            else:
                filtered.append(target)
        return filtered

    @classmethod
    def deduplicate_targets(
        cls, tool: str, targets: List[str], scanned_cache: set = None
    ) -> List[str]:
        """
        Remove duplicate targets (case-insensitive for Windows/IIS).

        Args:
            tool: Tool name
            targets: List of target URLs
            scanned_cache: Optional set of already-scanned URLs

        Returns:
            Deduplicated list
        """
        scanned_cache = scanned_cache or set()
        unique = []
        seen = set()

        for target in targets:
            # Normalize for comparison
            normalized = target.lower().rstrip("/")

            # Skip if already in this batch or previously scanned
            if normalized in seen or normalized in scanned_cache:
                logger.debug(f"SmartFilter: Dedup skipping {target} for {tool}")
                continue

            seen.add(normalized)
            unique.append(target)

        return unique


# Technology to Nuclei tags mapping
# Maps detected products/technologies to relevant nuclei template tags
TECH_TO_NUCLEI_TAGS = {
    # Web Servers
    "apache": ["apache", "cve"],
    "nginx": ["nginx", "cve"],
    "iis": ["iis", "microsoft", "cve"],
    "tomcat": ["tomcat", "apache", "cve"],
    "lighttpd": ["lighttpd", "cve"],
    "caddy": ["caddy", "cve"],
    # CMS / Frameworks
    "wordpress": ["wordpress", "wp-plugin", "cve"],
    "drupal": ["drupal", "drupalgeddon", "cve"],
    "joomla": ["joomla", "cve"],
    "magento": ["magento", "cve"],
    "typo3": ["typo3", "cve"],
    "laravel": ["laravel", "php", "cve"],
    "django": ["django", "python", "cve"],
    "flask": ["flask", "python", "cve"],
    "rails": ["rails", "ruby", "cve"],
    "express": ["express", "nodejs", "cve"],
    "spring": ["spring", "java", "cve"],
    "struts": ["struts", "java", "cve"],
    # Languages / Runtimes
    "php": ["php", "cve"],
    "node": ["nodejs", "cve"],
    "python": ["python", "cve"],
    "java": ["java", "cve"],
    "asp.net": ["aspnet", "microsoft", "cve"],
    "coldfusion": ["coldfusion", "adobe", "cve"],
    # Databases
    "mysql": ["mysql", "cve"],
    "postgresql": ["postgres", "cve"],
    "mongodb": ["mongodb", "cve"],
    "redis": ["redis", "cve"],
    "elasticsearch": ["elasticsearch", "cve"],
    "couchdb": ["couchdb", "cve"],
    # Proxies / Load Balancers
    "haproxy": ["haproxy", "cve"],
    "varnish": ["varnish", "cve"],
    "squid": ["squid", "cve"],
    "traefik": ["traefik", "cve"],
    # Admin Panels
    "phpmyadmin": ["phpmyadmin", "exposure", "cve"],
    "webmin": ["webmin", "cve"],
    "cpanel": ["cpanel", "cve"],
    "plesk": ["plesk", "cve"],
    "cockpit": ["cockpit", "cve"],
    # Mail Servers
    "postfix": ["postfix", "cve"],
    "exim": ["exim", "cve"],
    "dovecot": ["dovecot", "cve"],
    "exchange": ["exchange", "microsoft", "cve"],
    "zimbra": ["zimbra", "cve"],
    # CI/CD / DevOps
    "jenkins": ["jenkins", "cve"],
    "gitlab": ["gitlab", "cve"],
    "grafana": ["grafana", "cve"],
    "prometheus": ["prometheus", "cve"],
    "kubernetes": ["kubernetes", "k8s", "cve"],
    "docker": ["docker", "cve"],
    # Network / Router
    "cisco": ["cisco", "cve"],
    "juniper": ["juniper", "cve"],
    "mikrotik": ["mikrotik", "routeros", "cve"],
    "netgear": ["netgear", "cve"],
    "dlink": ["dlink", "cve"],
    "tplink": ["tplink", "cve"],
    "asus": ["asus", "cve"],
    "ubiquiti": ["ubiquiti", "unifi", "cve"],
    "fortinet": ["fortinet", "fortigate", "cve"],
    "pfsense": ["pfsense", "cve"],
    "openwrt": ["openwrt", "cve"],
}


def detect_nuclei_tags(services: List[Dict[str, Any]], os_info: str = "") -> str:
    """
    Detect appropriate nuclei tags based on discovered services and technologies.

    Analyzes service products, versions, and banners to determine which nuclei
    template tags would be most relevant for scanning this target.

    Args:
        services: List of service dicts from nmap parser with 'product', 'raw_version', etc.
        os_info: OS detection string from nmap (optional)

    Returns:
        Comma-separated string of nuclei tags, or empty string if no tech detected
        Example: "apache,php,cve" or "wordpress,wp-plugin,cve"
    """
    detected_tags = set()

    # Always include these base tags for web scanning
    base_tags = {"exposure", "misconfiguration"}

    for service in services:
        product = (service.get("product") or "").lower()
        raw_version = (service.get("raw_version") or "").lower()
        service_name = (service.get("service_name") or "").lower()

        # Combine all text for matching
        combined = f"{product} {raw_version} {service_name}"

        # Check each tech pattern
        for tech, tags in TECH_TO_NUCLEI_TAGS.items():
            if tech in combined:
                detected_tags.update(tags)

        # Special detection patterns
        if "wordpress" in combined or "wp-" in combined:
            detected_tags.update(["wordpress", "wp-plugin", "cve"])
        if "drupal" in combined:
            detected_tags.update(["drupal", "drupalgeddon", "cve"])
        if "joomla" in combined:
            detected_tags.update(["joomla", "cve"])

    # Check OS info for additional context
    os_lower = (os_info or "").lower()
    if "windows" in os_lower:
        detected_tags.update(["windows", "microsoft"])
    if "linux" in os_lower:
        detected_tags.add("linux")

    # If we detected specific tech, return those tags
    if detected_tags - base_tags:  # Has tags beyond base
        # Prioritize: CVE always, then limit to most relevant
        final_tags = detected_tags | {"cve"}
        return ",".join(sorted(final_tags))

    # No specific tech detected - return empty to trigger default behavior
    return ""


# Target format constants for chain rules
TARGET_FORMAT_IP = "ip"  # Just IP address (e.g., 192.168.1.1)
TARGET_FORMAT_URL = "url"  # Full URL with scheme/port (e.g., http://192.168.1.1:8080)
TARGET_FORMAT_HOST_PORT = "host:port"  # IP:port format (e.g., 192.168.1.1:445)
TARGET_FORMAT_BASE_URL = "base_url"  # Root URL only (e.g., http://192.168.1.1:8080/ from http://192.168.1.1:8080/api/foo)


@dataclass
class ChainRule:
    """Defines when and how to chain tools together."""

    trigger_tool: str  # Tool that triggers this rule (e.g., 'nmap')
    trigger_condition: (
        str  # What to look for (e.g., 'http_service', 'smb_service', 'finding:cve')
    )
    target_tool: str  # Tool to run next (e.g., 'nuclei', 'gobuster')
    priority: int = 5  # Higher = more important (1-10)
    args_template: List[str] = field(default_factory=list)  # Args for target tool
    enabled: bool = True
    description: str = ""
    category: str = CATEGORY_GENERAL  # ctf, enterprise, or general
    trigger_count: int = 0  # How many times this rule has fired
    target_format: str = TARGET_FORMAT_IP  # What format the target tool expects
    skip_scope_check: bool = (
        False  # Skip scope validation (for local tools like hashcat)
    )

    def matches(self, context: Dict[str, Any]) -> bool:
        """Check if this rule should trigger given the context."""
        # Context contains: service info, findings, host data, etc.

        # Support AND conditions (e.g., 'has:domains+port:88')
        if "&" in self.trigger_condition:
            conditions = [c.strip() for c in self.trigger_condition.split("&")]
            # All conditions must match
            return all(
                self._check_single_condition(cond, context) for cond in conditions
            )

        return self._check_single_condition(self.trigger_condition, context)

    def _check_single_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Check if a single condition matches. Supports negation with '!' prefix."""
        # Check for negation
        negated = condition.startswith("!")
        if negated:
            condition = condition[1:]  # Remove '!' prefix

        result = False

        if ":" in condition:
            # Complex condition like 'service:http', 'port:445', 'finding:cve'
            cond_type, cond_value = condition.split(":", 1)

            if cond_type == "service":
                services = context.get("services", [])

                # Check for combined services (e.g., 'mysql+http')
                if "+" in cond_value:
                    required_services = [
                        s.strip().lower() for s in cond_value.split("+")
                    ]
                    found_services = [
                        s.get("service_name", "").lower() for s in services
                    ]
                    result = all(req in found_services for req in required_services)
                else:
                    # Single service match
                    cond_lower = cond_value.lower()

                    # Check if this service has a group definition
                    if cond_lower in SERVICE_GROUPS:
                        group = SERVICE_GROUPS[cond_lower]
                        # Match by service name OR by port
                        result = any(
                            s.get("service_name", "").lower() in group["services"]
                            or s.get("port") in group["ports"]
                            for s in services
                        )
                    else:
                        # Exact match for services not in groups
                        result = any(
                            s.get("service_name", "").lower() == cond_lower
                            for s in services
                        )

            elif cond_type == "port":
                services = context.get("services", [])
                port_num = int(cond_value)
                # Only match open ports (not closed or filtered)
                result = any(
                    s.get("port") == port_num
                    and s.get("state", "").lower() in ["open", "open|filtered"]
                    for s in services
                )

            elif cond_type == "finding":
                findings = context.get("findings", [])
                if cond_value == "any":
                    result = len(findings) > 0
                else:
                    # Check for specific finding type or keyword
                    result = any(
                        cond_value.lower() in str(f.get("title", "")).lower()
                        for f in findings
                    )

            elif cond_type == "has":
                # Check if context has a specific key with data
                result = bool(context.get(cond_value))

            elif cond_type == "is":
                # Check boolean flags in context (e.g., 'is:lfi_scan')
                # Used to identify scan types for rule filtering
                if cond_value == "lfi_scan":
                    result = bool(context.get("is_lfi_scan"))
                else:
                    result = bool(context.get(f"is_{cond_value}"))

            elif cond_type == "category":
                # Check directory category (database_admin, wordpress, drupal, vulnerable_app, custom_php)
                result = (
                    context.get("directory_category", "").lower() == cond_value.lower()
                )

            elif cond_type == "os":
                # Check OS family (macos, linux, windows, ios)
                # e.g., 'os:macos', 'os:linux', 'os:windows'
                os_family = context.get("os_family", "").lower()
                result = cond_value.lower() in os_family

            elif cond_type == "device":
                # Check device type (router, desktop, server, mobile)
                # e.g., 'device:router', 'device:desktop'
                device_type = context.get("device_type", "").lower()
                result = cond_value.lower() == device_type

            elif cond_type == "vendor":
                # Check vendor (apple, cisco, netgear, etc.)
                # e.g., 'vendor:apple', 'vendor:cisco'
                vendor = context.get("vendor", "") or ""
                result = cond_value.lower() in vendor.lower()

            elif cond_type == "version":
                # Check product version (e.g., 'version:nginx:<1.19', 'version:apache:>=2.4.49,<=2.4.50')
                # cond_value format: 'product:version_conditions'
                from souleyez.core.version_utils import (
                    matches_version,
                    normalize_product_name,
                    parse_version_spec,
                )

                target_product, version_conditions = parse_version_spec(cond_value)

                if target_product and version_conditions:
                    services = context.get("services", [])
                    for service in services:
                        # Get product name from service (try multiple fields)
                        svc_product = (
                            service.get("product", "")
                            or service.get("service_product", "")
                            or ""
                        )
                        # Get version from service (try multiple fields)
                        svc_version = (
                            service.get("version", "")
                            or service.get("service_version", "")
                            or ""
                        )

                        if svc_product and svc_version:
                            # Normalize product name for comparison
                            normalized = normalize_product_name(svc_product)
                            if normalized == target_product:
                                if matches_version(svc_version, version_conditions):
                                    result = True
                                    break

            elif cond_type == "svc_version":
                # Simple version string match (e.g., 'svc_version:2.3.4')
                # Matches if any service has this exact version string
                # Useful when nmap doesn't detect product name
                services = context.get("services", [])
                for service in services:
                    svc_version = (
                        service.get("version", "")
                        or service.get("service_version", "")
                        or ""
                    )
                    if svc_version and cond_value.lower() in svc_version.lower():
                        result = True
                        break

        # Apply negation if needed
        return not result if negated else result

    def generate_command(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the command to run based on context."""
        target = context.get("target", "")
        target_url = context.get("target_url", "")  # Full URL if available
        args = self.args_template.copy()

        # For finding-based triggers, use the finding's URL if available
        # Prefer cleaner paths: exact matches over partial, directories over files
        if "finding:" in self.trigger_condition:
            findings = context.get("findings", [])
            cond_value = self.trigger_condition.split(":", 1)[1].lower()
            matching_findings = []

            for finding in findings:
                if cond_value in str(finding.get("title", "")).lower():
                    if finding.get("url"):
                        # Skip Apache/nginx config files - they're not directories
                        url = finding.get("url", "")
                        path_part = (
                            url.split("/")[-1].split("?")[0] if "/" in url else url
                        )
                        if path_part.startswith(".ht") or path_part.startswith(
                            ".nginx"
                        ):
                            continue
                        matching_findings.append(finding)

            if matching_findings:
                # Sort to prefer: 1) exact path match, 2) no file extension, 3) shorter URL
                def score_finding(f):
                    url = f.get("url", "")
                    path = url.split("?")[0]  # Remove query string
                    # Prefer paths ending with the pattern (exact match)
                    exact_match = (
                        path.rstrip("/").endswith("/" + cond_value)
                        or path.rstrip("/") == "/" + cond_value
                    )
                    # Prefer paths without file extensions
                    has_extension = "." in path.split("/")[-1]
                    # Prefer shorter paths
                    return (not exact_match, has_extension, len(url))

                matching_findings.sort(key=score_finding)
                target = matching_findings[0]["url"]

        # For domain-based triggers or AD tools, use domain as target
        domain = ""
        dc_ip = target  # Default DC IP is the target IP
        domains = context.get("domains", [])

        # Check if we have domain context (either from trigger condition or database enrichment)
        if domains and (
            "has:domains" in self.trigger_condition
            or self.target_tool in ["impacket-getnpusers"]
        ):
            # Use first discovered domain
            domain_info = domains[0]
            domain = domain_info.get("domain", "")
            dc_ip = domain_info.get("ip", target)
            # For AD tools like GetNPUsers, target should be "DOMAIN/"
            if domain and self.target_tool in ["impacket-getnpusers"]:
                target = f"{domain}/"

        # Find the relevant port for this service
        port = ""
        if "port:" in self.trigger_condition:
            port_num = self.trigger_condition.split(":")[1]
            port = port_num
        elif "service:" in self.trigger_condition:
            service_name = self.trigger_condition.split(":")[1].lower()
            # Find port for this service - check both service name AND SERVICE_GROUPS ports
            for svc in context.get("services", []):
                svc_name = svc.get("service_name", "").lower()
                svc_port = svc.get("port")

                # Direct service name match
                if svc_name == service_name:
                    port = str(svc_port)
                    break

                # Check SERVICE_GROUPS - if condition is 'service:http' and port is in http ports
                if service_name in SERVICE_GROUPS:
                    group = SERVICE_GROUPS[service_name]
                    if svc_port in group.get("ports", []):
                        port = str(svc_port)
                        break
        elif "has:services" in self.trigger_condition:
            # For has:services condition, extract port from the services array
            # Prioritize HTTP services for web tools (gobuster, nuclei, etc.)
            services = context.get("services", [])
            http_ports = {80, 443, 8080, 8443, 8000, 8888, 3000, 5000, 11434}

            # First pass: look for HTTP service by name or common HTTP ports
            for svc in services:
                svc_name = svc.get("service_name", "").lower()
                svc_port = svc.get("port")
                if svc_name == "http" or svc_name == "https" or svc_port in http_ports:
                    port = str(svc_port)
                    break

            # Second pass: if no HTTP service, use the first service's port
            if not port and services:
                port = str(services[0].get("port", ""))

        # Calculate subnet for {subnet} placeholder (e.g., 10.0.0.88 → 10.0.0.0/24)
        subnet = ""
        if "{subnet}" in str(args):
            try:
                import ipaddress

                # Use the original target (dc_ip might be modified)
                original_target = context.get("target", target)
                # Remove domain prefix if present (e.g., "DOMAIN/" → use dc_ip)
                ip_to_use = dc_ip if "/" in target else original_target
                ip_obj = ipaddress.ip_address(ip_to_use)
                # Assume /24 subnet (common for small networks)
                network = ipaddress.ip_network(f"{ip_to_use}/24", strict=False)
                subnet = str(network)
            except:
                subnet = ""

        # Get database and table from context (for SQLMap chaining)
        database = context.get("database", "")
        table = context.get("table", "")

        # Get base_dn from context (for LDAP user enumeration)
        base_dn = context.get("base_dn", "")

        # Get POST data for SQLMap POST injections
        post_data = context.get("post_data") or ""

        # Extract path from target URL for {path} placeholder (used by Hydra)
        path = ""
        if target.startswith(("http://", "https://")):
            try:
                parsed = urlparse(target)
                path = parsed.path or "/"
            except:
                path = "/"

        # Detect nuclei tags based on discovered technologies
        nuclei_tags = ""
        if self.target_tool == "nuclei" and "{nuclei_tags}" in str(args):
            services = context.get("services", [])
            os_info = context.get("os_info", "")
            nuclei_tags = detect_nuclei_tags(services, os_info)

        # Construct target_url if not provided but we have target + port
        # This ensures {target_url} placeholder always has a value for web tools
        if not target_url and port:
            scheme = context.get("scheme", "http")
            # Use standard ports without explicit port number
            if (scheme == "http" and port == "80") or (
                scheme == "https" and port == "443"
            ):
                target_url = f"{scheme}://{target}"
            else:
                target_url = f"{scheme}://{target}:{port}"
        elif not target_url:
            # Fallback to http://target if no port info
            # But only add http:// if target doesn't already have a scheme
            if target and not target.startswith(("http://", "https://")):
                target_url = f"http://{target}"
            else:
                target_url = target

        # Replace placeholders in args
        args = [
            arg.replace("{target}", target)
            .replace("{port}", port)
            .replace("{domain}", domain)
            .replace("{dc_ip}", dc_ip)
            .replace("{subnet}", subnet)
            .replace("{database}", database)
            .replace("{table}", table)
            .replace("{path}", path)
            .replace("{post_data}", post_data)
            .replace("{nuclei_tags}", nuclei_tags)
            .replace("{target_url}", target_url)
            .replace("{base_dn}", base_dn)
            for arg in args
        ]

        # For ldapsearch: skip if base_dn is empty (user enumeration needs valid base DN)
        if self.target_tool == "ldapsearch" and "-b" in args and not base_dn:
            # Check if this is a user enumeration query (has objectClass filter)
            has_object_class = any("objectClass=" in arg for arg in args)
            if has_object_class:
                # Return None to indicate this command should be skipped
                return None

        # For nuclei: if no tech-specific tags detected, remove empty -tags arg
        if self.target_tool == "nuclei" and not nuclei_tags:
            # Remove -tags and its empty value
            new_args = []
            skip_next = False
            for arg in args:
                if skip_next:
                    skip_next = False
                    continue
                if arg == "-tags":
                    skip_next = True
                    continue
                new_args.append(arg)
            args = new_args

        # For Nikto: Skip CGI enumeration on managed hosting platforms
        # This prevents long, pointless scans on Squarespace, Wix, etc.
        if self.target_tool == "nikto":
            services = context.get("services", [])
            http_fingerprint = context.get("http_fingerprint", {})
            if is_managed_hosting(services, http_fingerprint):
                # Add -C none to skip CGI dirs (pointless on managed hosting)
                if "-C" not in str(args):
                    args.extend(["-C", "none"])
                # Add -Tuning x6 to skip remote file inclusion tests
                if "-Tuning" not in str(args):
                    args.extend(["-Tuning", "x6"])
                # Log which platform was detected
                platform = get_managed_hosting_platform(services, http_fingerprint)
                if platform:
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)
                    logger.info(
                        f"[FINGERPRINT] Managed hosting detected ({platform}) - nikto using optimized scan config"
                    )

        # For SQLMap with POST injections, add --data if we have POST data
        if self.target_tool == "sqlmap" and post_data and "--data" not in str(args):
            # Insert --data after -u argument
            for i, arg in enumerate(args):
                if arg == "-u":
                    # Insert --data=POST_DATA after the URL (i.e., after args[i+1])
                    args.insert(i + 2, f"--data={post_data}")
                    break

        # Replace {subnet} in target as well if needed
        if "{subnet}" in target:
            target = subnet

        # Apply target_format to determine the final target for this rule
        # This ensures tools get the target in the format they expect
        final_target = target
        if self.target_format == TARGET_FORMAT_BASE_URL and target_url:
            # Extract root URL only (scheme://host:port/) for crawlers like katana
            # This ensures SPAs are crawled from root to render JavaScript properly
            from urllib.parse import urlparse

            parsed = urlparse(target_url)
            if parsed.port and parsed.port not in (80, 443):
                final_target = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}/"
            else:
                final_target = f"{parsed.scheme}://{parsed.hostname}/"
        elif self.target_format == TARGET_FORMAT_URL and target_url:
            # Web tools need full URLs (e.g., http://192.168.1.1:8080)
            final_target = target_url
        elif self.target_format == TARGET_FORMAT_HOST_PORT and port:
            # Some tools need host:port format (e.g., 192.168.1.1:445)
            final_target = f"{target}:{port}"
        # TARGET_FORMAT_IP is the default - just use target as-is

        return {
            "tool": self.target_tool,
            "target": final_target,
            "args": args,
            "priority": self.priority,
            "reason": f"Auto-triggered by {self.trigger_tool}: {self.description}",
        }


class ToolChaining:
    """Manages automatic tool chaining and workflow automation."""

    _instance = None  # Singleton instance

    # Cache for SQLMap injection points (for fallback)
    # Key: target host, Value: list of injection points
    _injection_points_cache = {}

    # SQLMap limits and timeouts
    MAX_DATABASES_TO_ENUMERATE = 15  # Enumerate more databases for thorough engagements

    # Phase-specific timeouts (seconds)
    SQLMAP_TIMEOUT_DBS_PHASE = 300  # 5 minutes to enumerate databases
    SQLMAP_TIMEOUT_TABLES_PHASE = 600  # 10 minutes per database for tables
    SQLMAP_TIMEOUT_DUMP_PHASE = 900  # 15 minutes per table dump

    # Row limit for dumps (already using --stop flag, this is for documentation)
    SQLMAP_MAX_ROWS_PER_TABLE = 100

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize with default chain rules."""
        # Only initialize once
        if self._initialized:
            return

        self.rules: List[ChainRule] = []
        self.enabled: bool = self._load_enabled_state()  # Load from persistent storage
        self.approval_mode: bool = (
            self._load_approval_mode()
        )  # Load approval mode state
        self._init_default_rules()
        self.load_rules_state()  # Load saved enabled/disabled states
        self._initialized = True

    def _should_skip_duplicate(
        self, tool: str, target: str, engagement_id: int, args: list = None
    ) -> bool:
        """Check if this tool+target combination should be skipped as a duplicate.

        Prevents redundant scans by checking if the same tool has already been
        queued or run for the same target in this engagement.

        This is particularly important for nuclei which gets triggered from
        multiple sqlmap jobs on the same endpoint (all confirming SQL injection).

        NOTE: sqlmap is excluded from this check because different sqlmap phases
        (--dbs, --tables, --columns, --dump) intentionally use the same target URL.
        SQLMap deduplication is handled separately via rule_id checks.

        NOTE: msf_auxiliary and hydra require args comparison because different
        modules/services should create separate jobs (e.g., ftp_anonymous vs mysql_login).

        Args:
            tool: The tool to check (e.g., 'nuclei')
            target: The target URL/host
            engagement_id: The engagement ID to check within
            args: Optional args list to compare for tools that need arg-based dedup

        Returns:
            True if this is a duplicate and should be skipped, False otherwise
        """
        # SQLMap is excluded - different phases (--dbs, --tables, --dump) use same target
        # and are already deduplicated by rule_id in the main dedup logic above
        if tool == "sqlmap":
            return False

        try:
            from souleyez.engine.background import get_all_jobs

            # Get all jobs in the system
            all_jobs = get_all_jobs()

            # Normalize target for comparison (strip trailing slashes, lowercase)
            normalized_target = target.rstrip("/").lower()

            for job in all_jobs:
                # Only check jobs in the same engagement
                if job.get("engagement_id") != engagement_id:
                    continue

                # Only check jobs with same tool
                if job.get("tool") != tool:
                    continue

                # Normalize the job's target
                job_target = (job.get("target") or "").rstrip("/").lower()

                # Check for match
                if job_target == normalized_target:
                    # For msf_auxiliary: different modules = different jobs
                    # Compare first arg (module name) to allow ftp_anonymous, mysql_login, etc.
                    if tool == "msf_auxiliary" and args:
                        existing_args = job.get("args", [])
                        if existing_args and args:
                            # Different module = not a duplicate
                            if existing_args[0] != args[0]:
                                continue

                    # For hydra: different service args = different jobs
                    if tool == "hydra" and args:
                        existing_args = job.get("args", [])
                        if existing_args != args:
                            # Different args (different service) = not a duplicate
                            continue

                    # For ldapsearch: different queries = different jobs
                    # (e.g., naming contexts query vs user enumeration query)
                    if tool == "ldapsearch" and args:
                        existing_args = job.get("args", [])
                        if existing_args != args:
                            # Different args (different query) = not a duplicate
                            continue

                    # Found a duplicate - job already exists for this tool+target
                    status = job.get("status", "unknown")
                    # Skip if queued, running, or already completed successfully
                    if status in ("queued", "running", "pending", "done", "no_results"):
                        return True

            return False

        except Exception:
            # On any error, don't skip (safer to allow potential duplicates)
            return False

    def _init_default_rules(self):
        """Set up default chaining rules."""

        # Web service discovered → run web scanners
        self.rules.extend(
            [
                # HTTP Fingerprinting - runs FIRST to detect WAF/CDN/managed hosting
                # This enables smarter tool configuration for downstream scanners
                # Excludes WinRM ports (5985/5986/47001) which are HTTP-based but not web servers
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:http & !port:5985 & !port:5986 & !port:47001",
                    target_tool="http_fingerprint",
                    priority=11,  # Highest priority - runs before all other web tools
                    args_template=[],
                    description="Web server detected, fingerprinting for WAF/CDN/platform detection",
                ),
                # Nikto triggered by http_fingerprint (uses fingerprint data for smart config)
                ChainRule(
                    trigger_tool="http_fingerprint",
                    trigger_condition="has:services",
                    target_tool="nikto",
                    priority=8,
                    args_template=["-nointeractive", "-timeout", "10"],
                    description="Fingerprinting complete, scanning for server misconfigurations with Nikto",
                    target_format=TARGET_FORMAT_URL,
                ),
                # Nuclei triggered by http_fingerprint
                ChainRule(
                    trigger_tool="http_fingerprint",
                    trigger_condition="has:services",
                    target_tool="nuclei",
                    priority=9,
                    args_template=[
                        "-tags",
                        "{nuclei_tags}",
                        "-severity",
                        "critical,high,medium",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                        "-timeout",
                        "10",
                    ],
                    description="Fingerprinting complete, scanning with Nuclei",
                    target_format=TARGET_FORMAT_URL,
                ),
                # Gobuster triggered by http_fingerprint
                ChainRule(
                    trigger_tool="http_fingerprint",
                    trigger_condition="has:services",
                    target_tool="gobuster",
                    priority=7,
                    args_template=[
                        "dir",
                        "-u",
                        "{target_url}",
                        "-w",
                        "data/wordlists/web_dirs_common.txt",
                        "-x",
                        "js,json,php,asp,aspx,html,txt,bak,old,zip",
                        "--no-error",
                        "--timeout",
                        "30s",
                        "-t",
                        "5",
                        "--delay",
                        "20ms",
                        "-k",
                    ],
                    description="Fingerprinting complete, discovering directories and files",
                    target_format=TARGET_FORMAT_URL,
                ),
                # Dalfox - XSS scanner triggered after gobuster finds pages
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="has:results",
                    target_tool="dalfox",
                    priority=6,
                    args_template=["--deep-domxss", "--format", "json", "--skip-bav"],
                    description="Web pages discovered, scanning for XSS vulnerabilities with Dalfox",
                ),
                # Dalfox - XSS scan after ffuf fuzzing
                ChainRule(
                    trigger_tool="ffuf",
                    trigger_condition="has:results",
                    target_tool="dalfox",
                    priority=6,
                    args_template=["--deep-domxss", "--format", "json", "--skip-bav"],
                    description="Fuzzing found pages, scanning for XSS vulnerabilities with Dalfox",
                ),
                # Dalfox - XSS scan after nikto finds pages
                ChainRule(
                    trigger_tool="nikto",
                    trigger_condition="has:results",
                    target_tool="dalfox",
                    priority=6,
                    args_template=["--deep-domxss", "--format", "json", "--skip-bav"],
                    description="Nikto found pages, scanning for XSS vulnerabilities with Dalfox",
                ),
                # Katana - Web crawler triggered after gobuster finds paths
                # Uses BASE_URL to crawl from root (SPAs need JS rendering from /)
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="has:paths_found",
                    target_tool="katana",
                    priority=7,
                    args_template=["-d", "5", "-jc", "-timeout", "10"],
                    description="Gobuster found paths, crawling root URL to discover parameters with Katana",
                    target_format=TARGET_FORMAT_BASE_URL,
                ),
                # Katana - Crawl API endpoints found by ffuf
                # Uses BASE_URL to crawl from root (SPAs need JS rendering from /)
                ChainRule(
                    trigger_tool="ffuf",
                    trigger_condition="has:results_found",
                    target_tool="katana",
                    priority=7,
                    args_template=["-d", "5", "-jc", "-timeout", "10"],
                    description="FFUF found endpoints, crawling root URL to discover parameters with Katana",
                    target_format=TARGET_FORMAT_BASE_URL,
                ),
                # SQLMap - Test URLs with parameters found by Katana
                ChainRule(
                    trigger_tool="katana",
                    trigger_condition="has:urls_with_params",
                    target_tool="sqlmap",
                    priority=9,
                    args_template=[
                        "-u",
                        "{target}",
                        "--batch",
                        "--level=2",
                        "--risk=2",
                        "--threads=5",
                    ],
                    description="Katana found parameterized URLs, testing for SQL injection",
                ),
                # Nuclei DAST - Scan crawled URLs from Katana
                ChainRule(
                    trigger_tool="katana",
                    trigger_condition="has:urls_found",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "dast",
                        "-severity",
                        "critical,high,medium",
                    ],
                    description="Katana crawled URLs, running DAST templates with Nuclei",
                ),
                # SQLMap - Test POST form endpoints found by Katana
                ChainRule(
                    trigger_tool="katana",
                    trigger_condition="has:forms_found",
                    target_tool="sqlmap",
                    priority=9,
                    args_template=[
                        "-u",
                        "{target}",
                        "--batch",
                        "--forms",
                        "--level=2",
                        "--risk=2",
                        "--threads=5",
                    ],
                    description="Katana found forms, testing for SQL injection",
                ),
                # SQLMap - Test CGI scripts found by nikto (often vulnerable to injection)
                ChainRule(
                    trigger_tool="nikto",
                    trigger_condition="finding:cgi",
                    target_tool="sqlmap",
                    priority=8,
                    args_template=[
                        "-u",
                        "{target}",
                        "--batch",
                        "--level=2",
                        "--risk=2",
                        "--threads=5",
                    ],
                    description="Nikto found CGI script, testing for SQL injection",
                ),
                # SQLMap - Test login pages found by nikto
                ChainRule(
                    trigger_tool="nikto",
                    trigger_condition="finding:login",
                    target_tool="sqlmap",
                    priority=8,
                    args_template=[
                        "-u",
                        "{target}",
                        "--batch",
                        "--forms",
                        "--level=2",
                        "--risk=2",
                        "--threads=5",
                    ],
                    description="Nikto found login page, testing forms for SQL injection",
                ),
                # SQLMap - Test ASP/ASPX pages found by nikto
                ChainRule(
                    trigger_tool="nikto",
                    trigger_condition="finding:aspx",
                    target_tool="sqlmap",
                    priority=7,
                    args_template=[
                        "-u",
                        "{target}",
                        "--batch",
                        "--forms",
                        "--level=2",
                        "--risk=2",
                        "--threads=5",
                    ],
                    description="Nikto found ASPX page, testing for SQL injection",
                ),
                # SQLMap - Test admin panels found by nikto
                ChainRule(
                    trigger_tool="nikto",
                    trigger_condition="finding:admin",
                    target_tool="sqlmap",
                    priority=8,
                    args_template=[
                        "-u",
                        "{target}",
                        "--batch",
                        "--forms",
                        "--level=2",
                        "--risk=2",
                        "--threads=5",
                    ],
                    description="Nikto found admin panel, testing for SQL injection",
                ),
                # === WordPress-specific chains ===
                # WordPress login page → SQLMap (forms-based injection)
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:wp-login",
                    target_tool="sqlmap",
                    priority=9,
                    args_template=[
                        "-u",
                        "{target}",
                        "--batch",
                        "--forms",
                        "--level=3",
                        "--risk=2",
                        "--threads=5",
                    ],
                    description="WordPress login found, testing for SQL injection",
                ),
                # WordPress detection → WPScan (user enum, plugin vulns)
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:wp-content",
                    target_tool="wpscan",
                    priority=8,
                    args_template=[
                        "--url",
                        "{target}",
                        "--enumerate",
                        "u,vp,vt",
                        "--plugins-detection",
                        "mixed",
                        "--random-user-agent",
                    ],
                    description="WordPress detected, scanning for vulnerabilities with WPScan",
                ),
                # phpMyAdmin → SQLMap - DISABLED
                # phpMyAdmin is a database management tool with proper authentication.
                # It doesn't have SQLi in its login form. Use nuclei/searchsploit instead.
                # ChainRule(
                #     trigger_tool="gobuster",
                #     trigger_condition="finding:phpmyadmin",
                #     target_tool="sqlmap",
                #     ...
                # ),
                # === END WordPress-specific chains ===
                # Dalfox - Deep XSS scan if nuclei hints at XSS
                ChainRule(
                    trigger_tool="nuclei",
                    trigger_condition="finding:xss",
                    target_tool="dalfox",
                    priority=7,
                    args_template=["--deep-domxss", "--format", "json"],
                    description="Nuclei detected potential XSS, deep scanning with Dalfox",
                ),
                # Nikto - Catch alternative HTTP ports
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:8080",
                    target_tool="nikto",
                    priority=7,
                    args_template=["-nointeractive", "-timeout", "10"],
                    description="HTTP on port 8080 detected, scanning with Nikto",
                ),
                # Dalfox - XSS scan WordPress pages after wpscan
                ChainRule(
                    trigger_tool="wpscan",
                    trigger_condition="has:results",
                    target_tool="dalfox",
                    priority=6,
                    args_template=["--deep-domxss", "--format", "json", "--skip-bav"],
                    description="WPScan found pages, scanning for XSS vulnerabilities with Dalfox",
                ),
            ]
        )

        # SMB service discovered → enumerate shares
        self.rules.extend(
            [
                # Modern Windows/AD tool (CrackMapExec/NetExec) - PRIORITY
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:smb",
                    target_tool="crackmapexec",
                    priority=10,
                    args_template=["smb", "--shares"],
                    description="SMB service detected, enumerating with CrackMapExec",
                ),
                # Guest credential share enumeration - common in AD environments
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:smb",
                    target_tool="nxc",
                    priority=9,
                    args_template=[
                        "smb",
                        "{target}",
                        "-u",
                        "guest",
                        "-p",
                        "",
                        "--shares",
                    ],
                    description="SMB detected - enumerating shares with guest credentials",
                ),
                # Legacy tool (enum4linux) - lower priority
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:smb",
                    target_tool="enum4linux",
                    priority=8,
                    enabled=True,
                    args_template=["-a", "{target}"],
                    description="SMB service detected, enumerating shares and users (runs after CrackMapExec)",
                ),
                # NOTE: smbmap removed - has upstream impacket pickling bug on Python 3.13+
                # Use crackmapexec/netexec --shares instead (enum4linux rule above)
            ]
        )

        # Active Directory attacks - smart chaining workflow
        self.rules.extend(
            [
                # Stage 1: Domain discovered → Verify Kerberos is running (TCP scan - no root needed)
                ChainRule(
                    trigger_tool="crackmapexec",
                    trigger_condition="has:domains",
                    target_tool="nmap",
                    priority=9,
                    args_template=["-sT", "-p", "88", "--reason"],
                    description="Domain discovered, checking for Kerberos (TCP port 88)",
                ),
                ChainRule(
                    trigger_tool="enum4linux",
                    trigger_condition="has:domains",
                    target_tool="nmap",
                    priority=9,
                    args_template=["-sT", "-p", "88", "--reason"],
                    description="Domain discovered, checking for Kerberos (TCP port 88)",
                ),
                # Stage 2: Kerberos port found → AS-REP Roasting attack
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:88",
                    target_tool="impacket-getnpusers",
                    priority=8,
                    args_template=[
                        "-no-pass",
                        "-usersfile",
                        "data/wordlists/ad_users.txt",
                        "-dc-ip",
                        "{dc_ip}",
                    ],
                    description="Kerberos detected, attempting AS-REP Roasting for accounts with pre-auth disabled",
                ),
                # Stage 2b: Kerberos port found → Kerbrute user enumeration
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:88 & has:domains",
                    target_tool="kerbrute",
                    priority=7,
                    args_template=[
                        "userenum",
                        "-d",
                        "{domain}",
                        "--dc",
                        "{dc_ip}",
                        "data/wordlists/ad_users.txt",
                    ],
                    description="Kerberos detected, enumerating valid usernames via Kerberos pre-auth",
                ),
                # Stage 3: Domain member detected (has domain but NOT a DC) → Find the actual DC
                ChainRule(
                    trigger_tool="crackmapexec",
                    trigger_condition="has:domains & !port:88",
                    target_tool="nmap",
                    priority=8,
                    args_template=[
                        "-p",
                        "88,389,636,3268,3269",
                        "-sT",
                        "-Pn",
                        "--open",
                        "{subnet}",
                    ],
                    description="Domain member detected, scanning subnet for Domain Controller",
                ),
                ChainRule(
                    trigger_tool="enum4linux",
                    trigger_condition="has:domains & !port:88",
                    target_tool="nmap",
                    priority=8,
                    args_template=[
                        "-p",
                        "88,389,636,3268,3269",
                        "-sT",
                        "-Pn",
                        "--open",
                        "{subnet}",
                    ],
                    description="Domain member detected, scanning subnet for Domain Controller",
                ),
                # Kerbrute chains - enumerate users via Kerberos when domain discovered
                # IMPORTANT: Require port 88 (Kerberos) to be open - not just "has:domains"
                # Samba workgroups report as "domains" but are NOT Active Directory
                ChainRule(
                    trigger_tool="enum4linux",
                    trigger_condition="has:domains & port:88",
                    target_tool="kerbrute",
                    priority=6,
                    args_template=[
                        "userenum",
                        "-d",
                        "{domain}",
                        "--dc",
                        "{dc_ip}",
                        "data/wordlists/ad_users.txt",
                    ],
                    description="Active Directory detected (Kerberos port 88 open) - enumerating users",
                ),
                ChainRule(
                    trigger_tool="crackmapexec",
                    trigger_condition="has:domains & port:88",
                    target_tool="kerbrute",
                    priority=6,
                    args_template=[
                        "userenum",
                        "-d",
                        "{domain}",
                        "--dc",
                        "{dc_ip}",
                        "data/wordlists/ad_users.txt",
                    ],
                    description="Active Directory detected (Kerberos port 88 open) - enumerating users",
                ),
            ]
        )

        # FTP service discovered → check for anonymous access
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:ftp",
                target_tool="msf_auxiliary",
                priority=7,
                args_template=["auxiliary/scanner/ftp/anonymous"],
                description="FTP service detected, checking anonymous access",
            )
        )

        # MySQL/PostgreSQL discovered → check default creds
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:mysql",
                    target_tool="msf_auxiliary",
                    priority=6,
                    args_template=["auxiliary/scanner/mysql/mysql_login"],
                    description="MySQL detected, checking default credentials",
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:postgresql",
                    target_tool="msf_auxiliary",
                    priority=6,
                    args_template=["auxiliary/scanner/postgres/postgres_login"],
                    description="PostgreSQL detected, checking default credentials",
                ),
            ]
        )

        # SSH service discovered → enumerate users and check default creds
        # RPORT={port} ensures non-standard SSH ports (e.g., 2222, 22222) are used
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ssh",
                    target_tool="msf_auxiliary",
                    priority=6,
                    args_template=[
                        "auxiliary/scanner/ssh/ssh_enumusers",
                        "USER_FILE=data/wordlists/soul_users.txt",
                        "RPORT={port}",
                    ],
                    description="SSH detected, enumerating users",
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ssh",
                    target_tool="msf_auxiliary",
                    priority=5,
                    # SSH_CLIENT_KEX allows legacy key exchange for old/vulnerable servers (Metasploitable, etc.)
                    # RPORT={port} ensures non-standard SSH ports are used
                    args_template=[
                        "auxiliary/scanner/ssh/ssh_login",
                        "USER_FILE=data/wordlists/soul_users.txt",
                        "STOP_ON_SUCCESS=false",
                        "BLANK_PASSWORDS=true",
                        "USER_AS_PASS=true",
                        "VERBOSE=true",
                        "SSH_CLIENT_KEX=diffie-hellman-group14-sha1,diffie-hellman-group1-sha1",
                        "RPORT={port}",
                    ],
                    description="SSH detected, checking weak credentials",
                ),
            ]
        )

        # SMB service discovered → enumerate shares and version
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:smb",
                    target_tool="msf_auxiliary",
                    priority=7,
                    args_template=["auxiliary/scanner/smb/smb_version"],
                    description="SMB detected, identifying version and OS",
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:smb",
                    target_tool="msf_auxiliary",
                    priority=6,
                    args_template=["auxiliary/scanner/smb/smb_enumshares"],
                    description="SMB detected, enumerating shares",
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:smb",
                    target_tool="enum4linux",
                    priority=5,  # Lower than MSF (6) - both run, enum4linux as backup
                    args_template=["-a"],  # Full enumeration
                    description="SMB detected, enumerating with enum4linux (works with legacy Samba)",
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:smb",
                    target_tool="msf_auxiliary",
                    priority=8,
                    args_template=["auxiliary/scanner/smb/smb_ms17_010"],
                    description="SMB detected, checking for EternalBlue (MS17-010)",
                ),
            ]
        )

        # RPC service discovered → enumerate endpoints and named pipes
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:135",
                    target_tool="msf_auxiliary",
                    priority=7,
                    args_template=["auxiliary/scanner/dcerpc/endpoint_mapper"],
                    description="RPC detected, enumerating DCERPC endpoints",
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:135",
                    target_tool="msf_auxiliary",
                    priority=6,
                    args_template=["auxiliary/scanner/smb/pipe_auditor"],
                    description="RPC detected, enumerating named pipes",
                ),
            ]
        )

        # SMTP service discovered → enumerate users
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:smtp",
                target_tool="msf_auxiliary",
                priority=5,
                args_template=["auxiliary/scanner/smtp/smtp_enum"],
                description="SMTP detected, enumerating users",
            )
        )

        # RDP service discovered → check for vulnerabilities
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ms-wbt-server",
                    target_tool="msf_auxiliary",
                    priority=8,
                    args_template=["auxiliary/scanner/rdp/cve_2019_0708_bluekeep"],
                    description="RDP detected, checking for BlueKeep (CVE-2019-0708)",
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ms-wbt-server",
                    target_tool="msf_auxiliary",
                    priority=5,
                    args_template=["auxiliary/scanner/rdp/rdp_scanner"],
                    description="RDP detected, scanning service",
                ),
            ]
        )

        # WinRM service discovered → enumerate with CrackMapExec
        # Note: Don't include {target} in args - the crackmapexec plugin adds it automatically
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:5985",
                    target_tool="crackmapexec",
                    priority=9,
                    args_template=["winrm", "--port", "5985"],
                    description="WinRM (HTTP) detected, enumerating with CrackMapExec",
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:5986",
                    target_tool="crackmapexec",
                    priority=9,
                    args_template=["winrm", "--port", "5986"],
                    description="WinRM (HTTPS) detected, enumerating with CrackMapExec",
                ),
            ]
        )

        # LDAP service discovered → enumerate Active Directory
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ldap",
                    target_tool="crackmapexec",
                    priority=7,
                    args_template=["ldap"],
                    description="LDAP/LDAPS detected, enumerating Active Directory",
                ),
            ]
        )

        # ldapsearch found domain → check Kerberos and AS-REP roasting
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="ldapsearch",
                    trigger_condition="has:domains",
                    target_tool="nmap",
                    priority=8,
                    args_template=["-sT", "-p", "88", "--reason"],
                    description="Domain discovered via LDAP, checking for Kerberos",
                ),
                ChainRule(
                    trigger_tool="ldapsearch",
                    trigger_condition="has:domains",
                    target_tool="impacket-getnpusers",
                    priority=7,
                    args_template=[
                        "{domain}/",
                        "-dc-ip",
                        "{dc_ip}",
                        "-no-pass",
                        "-usersfile",
                        "data/wordlists/ad_users.txt",
                    ],
                    description="Domain discovered via LDAP, checking for AS-REP roastable users",
                ),
                # Deep LDAP enumeration for user descriptions (may contain passwords)
                # NOTE: May fail on hardened AD but works on many CTF/vulnerable targets
                ChainRule(
                    trigger_tool="ldapsearch",
                    trigger_condition="has:domains",
                    target_tool="ldapsearch",
                    priority=6,
                    args_template=[
                        "-x",
                        "-H",
                        "ldap://{target}",
                        "-b",
                        "{base_dn}",
                        "(objectClass=user)",
                        "sAMAccountName",
                        "description",
                        "memberOf",
                    ],
                    description="Domain discovered - enumerating users and descriptions",
                ),
                # Broader LDAP enum - finds users that don't have objectClass=user set properly
                # Some AD configs have users that only show up when querying all objects
                # Include sAMAccountName and description so credentials can be detected and sprayed
                ChainRule(
                    trigger_tool="ldapsearch",
                    trigger_condition="has:domains",
                    target_tool="ldapsearch",
                    priority=5,
                    args_template=[
                        "-x",
                        "-H",
                        "ldap://{target}",
                        "-b",
                        "{base_dn}",
                        "(objectClass=*)",
                        "sAMAccountName",
                        "description",
                        "memberOf",
                    ],
                    description="Domain discovered - enumerating all objects to find hidden users",
                ),
                # Kerbrute user enumeration (works even when anonymous LDAP is blocked)
                # IMPORTANT: Require port 88 (Kerberos) - LDAP alone doesn't mean AD
                ChainRule(
                    trigger_tool="ldapsearch",
                    trigger_condition="has:domains & port:88",
                    target_tool="kerbrute",
                    priority=6,
                    args_template=[
                        "userenum",
                        "-d",
                        "{domain}",
                        "--dc",
                        "{dc_ip}",
                        "data/wordlists/ad_users.txt",
                    ],
                    description="Active Directory detected (Kerberos port 88 open) - enumerating users",
                ),
            ]
        )

        # DNS service discovered → try zone transfer
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="port:53",
                target_tool="dnsrecon",
                priority=6,
                args_template=["-d", "{domain}", "-t", "axfr", "-n", "{target}"],
                description="DNS detected, attempting zone transfer",
            )
        )

        # Domain Controller detected → Zerologon check (CVE-2020-1472)
        self.rules.append(
            ChainRule(
                trigger_tool="crackmapexec",
                trigger_condition="has:domains & port:445",
                target_tool="msf_auxiliary",
                priority=9,
                args_template=[
                    "auxiliary/admin/dcerpc/cve_2020_1472_zerologon",
                    "ACTION=CHECK",
                ],
                description="Domain Controller detected, checking for Zerologon (CVE-2020-1472)",
            )
        )

        # SMB readable share found → explore with smbclient
        self.rules.append(
            ChainRule(
                trigger_tool="crackmapexec",
                trigger_condition="has:shares",
                target_tool="smbmap",
                priority=7,
                args_template=["-H", "{target}", "-r"],
                description="SMB shares found, recursively listing contents",
            )
        )

        # Kerberos with domain → Kerberoasting (GetUserSPNs)
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="port:88 & has:domains",
                target_tool="msf_auxiliary",
                priority=7,
                args_template=[
                    "auxiliary/gather/kerberos_enumusers",
                    "DOMAIN={domain}",
                    "USER_FILE=data/wordlists/ad_users.txt",
                ],
                description="Kerberos detected, enumerating valid domain users",
            )
        )

        # Kerberoasting - check for service accounts with SPNs
        # NOTE: -no-pass only works if anonymous LDAP is allowed (rare on modern DCs)
        # Kerberoasting is triggered via smart chain when credentials are discovered
        # (see ldapsearch credential chain and password spray success chain)

        # PetitPotam check (Print Spooler pipe found)
        self.rules.append(
            ChainRule(
                trigger_tool="msf_auxiliary",
                trigger_condition="finding:spooler",
                target_tool="msf_auxiliary",
                priority=8,
                args_template=["auxiliary/scanner/dcerpc/petitpotam"],
                description="Print Spooler detected, checking for PetitPotam coercion",
            )
        )

        # Telnet service discovered → check default creds
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:telnet",
                target_tool="msf_auxiliary",
                priority=6,
                args_template=[
                    "auxiliary/scanner/telnet/telnet_login",
                    "USER_FILE=data/wordlists/soul_users.txt",
                    "STOP_ON_SUCCESS=false",
                    "BLANK_PASSWORDS=true",
                    "USER_AS_PASS=true",
                    "VERBOSE=true",
                ],
                description="Telnet detected, checking weak credentials",
            )
        )

        # MSSQL service discovered → check default creds and enumerate
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ms-sql-s",
                    target_tool="msf_auxiliary",
                    priority=6,
                    args_template=["auxiliary/scanner/mssql/mssql_login"],
                    description="MSSQL detected, checking default credentials",
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ms-sql-s",
                    target_tool="msf_auxiliary",
                    priority=5,
                    args_template=["auxiliary/scanner/mssql/mssql_ping"],
                    description="MSSQL detected, discovering instances",
                ),
            ]
        )

        # VNC service discovered → check for no-auth and weak passwords
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:vnc",
                    target_tool="msf_auxiliary",
                    priority=7,
                    args_template=["auxiliary/scanner/vnc/vnc_none_auth"],
                    description="VNC detected, checking for no authentication",
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:vnc",
                    target_tool="msf_auxiliary",
                    priority=5,
                    args_template=["auxiliary/scanner/vnc/vnc_login"],
                    description="VNC detected, checking weak passwords",
                ),
            ]
        )

        # MySQL + HTTP service discovered → test web app for SQL injection
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:mysql+http",
                target_tool="sqlmap",
                priority=8,
                enabled=False,  # This rule is not needed
                args_template=[
                    "-u",
                    "http://{target}/",
                    "--batch",
                    "--crawl=2",
                    "--risk=2",
                    "--level=3",
                    "--threads=5",
                ],
                description="MySQL + HTTP detected, testing web app for SQL injection",
            )
        )

        # Web path with parameters found → test for SQL injection
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="has:paths_with_params",
                target_tool="sqlmap",
                priority=9,
                args_template=[
                    "-u",
                    "{target}",
                    "--batch",
                    "--crawl=2",
                    "--risk=2",
                    "--level=3",
                    "--threads=5",
                ],
                description="Parametrized URL found, testing for SQL injection",
            )
        )

        # Gobuster discovered PHP files → crawl base URL - DISABLED
        # Reason: katana→sqlmap handles this better by targeting specific parametrized URLs.
        # Crawling the base URL with SQLMap is slow and often wasteful.
        # self.rules.append(
        #     ChainRule(
        #         trigger_tool="gobuster",
        #         trigger_condition="has:php_files",
        #         target_tool="sqlmap",
        #         ...
        #     )
        # )

        # Gobuster discovered ASP/ASPX files → crawl base URL - DISABLED
        # Reason: katana→sqlmap handles this better by targeting specific parametrized URLs.
        # self.rules.append(
        #     ChainRule(
        #         trigger_tool="gobuster",
        #         trigger_condition="has:asp_files",
        #         target_tool="sqlmap",
        #         ...
        #     )
        # )

        # SMART API DISCOVERY CHAIN
        # Replaced broken direct SQLMap rules with intelligent two-step approach
        # Old rules tried to test /api and /rest directories directly (no parameters)
        # New approach: ffuf discovers actual endpoints, then SQLMap tests them
        # Step 1: gobuster found /api → ffuf discovers actual endpoints
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="finding:api",
                target_tool="ffuf",
                priority=8,
                args_template=[
                    "-u",
                    "{target}/FUZZ",
                    "-w",
                    "data/wordlists/api_endpoints.txt",
                    "-t",
                    "5",
                    "-p",
                    "0.02",
                    "-mc",
                    "200,201,301,302,401,403,405",
                ],
                description="API directory found, discovering actual endpoints with parameters",
                category=CATEGORY_CTF,
            )
        )

        # Step 1b: gobuster found /rest → ffuf discovers actual endpoints
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="finding:rest",
                target_tool="ffuf",
                priority=8,
                args_template=[
                    "-u",
                    "{target}/FUZZ",
                    "-w",
                    "data/wordlists/api_endpoints.txt",
                    "-t",
                    "5",
                    "-p",
                    "0.02",
                    "-mc",
                    "200,201,301,302,401,403,405",
                ],
                description="REST directory found, discovering actual endpoints with parameters",
                category=CATEGORY_CTF,
            )
        )
        # Step 2: ffuf finds parameters → SQLMap tests (already exists at line ~1140)

        # Gobuster found interesting directories → deep fuzz with ffuf
        # Triggers only for high-value targets to avoid job explosion
        interesting_paths = [
            "admin",
            "backup",
            "api",
            "upload",
            "uploads",
            "files",
            "config",
            "panel",
            "dashboard",
            "manager",
            "console",
            "dev",
            "test",
            "staging",
            "beta",
            "private",
            "secret",
            "old",
            "tmp",
            "temp",
            "logs",
            "data",
            "db",
            "database",
            "phpmyadmin",
            "phpMyAdmin",
        ]

        for path_keyword in interesting_paths:
            # Use wordlist resolver to find the correct path
            from souleyez.wordlists import resolve_wordlist_path

            wordlist_path = resolve_wordlist_path("data/wordlists/web_files_common.txt")

            self.rules.append(
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition=f"finding:{path_keyword}",
                    target_tool="ffuf",
                    priority=6,
                    enabled=True,
                    args_template=[
                        "-u",
                        "{target}/FUZZ",
                        "-w",
                        wordlist_path,
                        "-e",
                        ".php,.html,.txt,.zip,.bak",
                        "-p",
                        "0.1",
                        "-t",
                        "10",
                    ],
                    description=f'Interesting path "{path_keyword}" found, deep fuzzing for sensitive files',
                )
            )

        # REMOVED: Gobuster redirect rule - now handled by nmap directly
        # self.rules.append(
        #     ChainRule(
        #         trigger_tool='gobuster',
        #         trigger_condition='has:redirects_with_mysql',
        #         target_tool='sqlmap',
        #         priority=9,
        #         args_template=['-u', '{target}', '--batch', '--risk=1', '--level=1'],
        #         description='Redirects found on host with MySQL, testing for SQL injection'
        #     )
        # )

        # DISABLED: smbmap has upstream pickling bug - won't produce results
        # Writable SMB shares found → check for exploitability
        # TODO: Add rule triggering from crackmapexec writable shares detection
        self.rules.append(
            ChainRule(
                trigger_tool="smbmap",
                trigger_condition="has:writable_shares",
                target_tool="msf_auxiliary",
                priority=10,
                enabled=False,  # Disabled - smbmap broken
                args_template=["auxiliary/scanner/smb/smb_version"],
                description="Writable SMB shares found, checking for vulnerabilities",
            )
        )

        # === NEW TOOL CHAINING RULES ===

        # theHarvester completed → run WHOIS on target domain
        self.rules.append(
            ChainRule(
                trigger_tool="theharvester",
                trigger_condition="has:target",
                target_tool="whois",
                priority=6,
                args_template=[],  # Plugin adds target automatically
                description="Domains discovered, gathering registration information",
            )
        )

        # theHarvester discovered URLs with parameters → test for SQL injection
        self.rules.append(
            ChainRule(
                trigger_tool="theharvester",
                trigger_condition="has:urls_with_params",
                target_tool="sqlmap",
                priority=9,
                args_template=[
                    "-u",
                    "{target}",
                    "--batch",
                    "--crawl=2",
                    "--risk=2",
                    "--level=3",
                    "--threads=5",
                ],
                description="Parametrized URLs discovered, testing for SQL injection",
            )
        )

        # DISABLED: Don't run SQLMap on base URLs without parameters (no injection points to test)
        # SQLMap should only run when we have:
        # 1. URLs with query parameters (has:urls_with_params) - handled above
        # 2. Forms discovered by Gobuster
        # 3. MySQL+HTTP combo detected by nmap
        #
        # self.rules.append(
        #     ChainRule(
        #         trigger_tool='theharvester',
        #         trigger_condition='has:base_urls',
        #         target_tool='sqlmap',
        #         priority=8,
        #         args_template=['-u', '{target}', '--batch', '--crawl=2', '--risk=2', '--level=2'],
        #         description='Base URLs discovered, crawling and testing for SQL injection'
        #     )
        # )

        # theHarvester discovered base URLs → scan with Nuclei (modern) and Gobuster (directory enum)
        # NOTE: Gobuster added for OSINT-only workflows (external assessments without nmap)
        # If nmap is used, it will also trigger Gobuster (duplicate detection prevents double-scanning)
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="theharvester",
                    trigger_condition="has:base_urls",
                    target_tool="nuclei",
                    priority=9,
                    args_template=[
                        "-tags",
                        "{nuclei_tags}",
                        "-severity",
                        "critical,high,medium",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                        "-timeout",
                        "10",
                    ],
                    description="Base URLs discovered, scanning with Nuclei",
                ),
                ChainRule(
                    trigger_tool="theharvester",
                    trigger_condition="has:base_urls",
                    target_tool="gobuster",
                    priority=8,
                    args_template=[
                        "dir",
                        "-u",
                        "{target}",
                        "-w",
                        "data/wordlists/web_dirs_common.txt",
                        "-x",
                        "js,json,php,asp,aspx,html,txt,bak,old,zip",
                        "-t",
                        "5",
                        "--delay",
                        "20ms",
                        "--no-error",
                        "-k",
                        "--timeout",
                        "30s",
                    ],
                    description="Base URLs discovered, discovering directories and files",
                ),
            ]
        )

        # === NEW: SQLMap Progressive Exploitation Rules ===

        # SQLMap Rule 1: SQL injection confirmed → enumerate databases
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:sql_injection_confirmed",
                target_tool="sqlmap",
                priority=10,
                args_template=["-u", "{target}", "--dbs", "--batch"],
                description="SQL injection confirmed, enumerating databases",
            )
        )

        # SQLMap Rule 2: Databases enumerated → enumerate tables
        # NOTE: Special handling in auto_chain() creates one job PER database
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:databases_enumerated",
                target_tool="sqlmap",
                priority=9,
                args_template=[
                    "-u",
                    "{target}",
                    "-D",
                    "{database}",
                    "--tables",
                    "--batch",
                ],
                description="Databases enumerated, enumerating tables",
            )
        )

        # SQLMap Rule 2.5: Tables enumerated → enumerate columns
        # NOTE: Special handling in auto_chain() creates one job PER table
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:tables_enumerated",
                target_tool="sqlmap",
                priority=8,
                args_template=[
                    "-u",
                    "{target}",
                    "-D",
                    "{database}",
                    "-T",
                    "{table}",
                    "--columns",
                    "--batch",
                ],
                description="Tables enumerated, enumerating columns",
            )
        )

        # SQLMap Rule 3: Columns enumerated → dump data (DISABLED by default)
        # WARNING: Can create massive data dumps - enable with caution
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:columns_enumerated",
                target_tool="sqlmap",
                priority=7,
                args_template=[
                    "-u",
                    "{target}",
                    "--batch",
                    "-D",
                    "{database}",
                    "-T",
                    "{table}",
                    "--dump",
                    "--threads=5",
                ],
                description="Columns enumerated, dumping data (DISABLED - enable manually)",
                enabled=False,  # CRITICAL: Disabled by default
            )
        )

        # === END SQLMap Progressive Exploitation ===

        # === SQLMap Post-Exploitation Rules ===

        # Rule 72: SQL injection confirmed → check privileges
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:sql_injection_confirmed",
                target_tool="sqlmap",
                priority=9,
                args_template=["-u", "{target}", "--privileges", "--batch"],
                description="SQL injection confirmed, checking database privileges",
                category=CATEGORY_CTF,
            )
        )

        # Rule 73: SQL injection confirmed → check if DBA
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:sql_injection_confirmed",
                target_tool="sqlmap",
                priority=9,
                args_template=["-u", "{target}", "--is-dba", "--batch"],
                description="SQL injection confirmed, checking DBA status",
                category=CATEGORY_CTF,
            )
        )

        # Rule 74: DBA confirmed → dump users & password hashes
        # Enabled - valuable for credential harvesting after confirming DBA access
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:is_dba",
                target_tool="sqlmap",
                priority=8,
                args_template=["-u", "{target}", "--users", "--passwords", "--batch"],
                description="DBA access confirmed, dumping database users and password hashes",
                category=CATEGORY_CTF,
            )
        )

        # Rule 75: SQL injection confirmed → read /etc/passwd and /etc/shadow (Linux)
        # DISABLED by default - aggressive file read operations
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:sql_injection_confirmed",
                target_tool="sqlmap",
                priority=7,
                args_template=[
                    "-u",
                    "{target}",
                    "--file-read=/etc/passwd,/etc/shadow",
                    "--batch",
                ],
                description="SQL injection confirmed, attempting to read /etc/passwd and /etc/shadow (DISABLED)",
                category=CATEGORY_CTF,
                enabled=False,
            )
        )

        # Rule 76: SQL injection confirmed → read win.ini (Windows)
        # DISABLED by default - aggressive file read operations
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:sql_injection_confirmed",
                target_tool="sqlmap",
                priority=7,
                args_template=[
                    "-u",
                    "{target}",
                    "--file-read=C:/Windows/win.ini",
                    "--batch",
                ],
                description="SQL injection confirmed, attempting to read win.ini (DISABLED)",
                category=CATEGORY_CTF,
                enabled=False,
            )
        )

        # Rule 77: DBA access → execute OS command
        # DISABLED by default - requires explicit user enablement
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:is_dba",
                target_tool="sqlmap",
                priority=6,
                args_template=["-u", "{target}", "--os-cmd=whoami", "--batch"],
                description="DBA access confirmed, executing OS command (DISABLED)",
                category=CATEGORY_CTF,
                enabled=False,
            )
        )

        # Rule 78: DBA access → get OS shell (DISABLED by default - dangerous)
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:is_dba",
                target_tool="sqlmap",
                priority=5,
                args_template=["-u", "{target}", "--os-shell", "--batch"],
                description="DBA access confirmed, spawning OS shell (DANGEROUS)",
                category=CATEGORY_CTF,
                enabled=False,  # CRITICAL: Disabled by default
            )
        )

        # === END SQLMap Post-Exploitation Rules ===

        # === SQLMap Cross-Tool Chain Rules ===

        # SQLi confirmed → nuclei webapp vulnerability scan
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:sql_injection_confirmed",
                target_tool="nuclei",
                priority=7,
                args_template=[
                    "-tags",
                    "sqli,injection,rce,lfi",
                    "-severity",
                    "critical,high",
                    "-rate-limit",
                    "50",
                    "-c",
                    "10",
                ],
                description="SQL injection confirmed, scanning for related webapp vulnerabilities",
            )
        )

        # Credentials dumped → hydra login testing
        # Uses credentials extracted from database dumps
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:credentials_dumped",
                target_tool="hydra",
                priority=8,
                args_template=["-C", "{credentials_file}", "-t", "4", "http-post-form"],
                description="Database credentials dumped, testing on discovered login forms",
            )
        )

        # Credentials dumped → SSH testing with dumped creds
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="has:credentials_dumped",
                target_tool="hydra",
                priority=7,
                args_template=["-C", "{credentials_file}", "-t", "4", "ssh"],
                description="Database credentials dumped, testing SSH access",
            )
        )

        # === END SQLMap Cross-Tool Chain Rules ===

        # === NEW: Windows/AD Attack Chain ===

        # Windows hosts detected → run Responder for passive credential capture
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:smb",
                target_tool="responder",
                priority=9,
                args_template=["-v"],
                description="Windows hosts detected, capturing credentials via LLMNR/NBT-NS poisoning",
                enabled=False,  # Requires manual interface selection, disabled by default
            )
        )

        # Responder captured hashes → crack with hashcat
        self.rules.append(
            ChainRule(
                trigger_tool="responder",
                trigger_condition="has:credentials_captured",
                target_tool="hashcat",
                priority=10,
                args_template=[
                    "-m",
                    "5600",
                    "-a",
                    "0",
                    "data/wordlists/passwords_crack.txt",
                ],
                description="NTLMv2 hashes captured, cracking with hashcat",
                skip_scope_check=True,  # Local file cracking, not network scan
            )
        )

        # Domain credentials discovered → run Bloodhound
        # NOTE: Special handling needed to detect domain credentials
        self.rules.append(
            ChainRule(
                trigger_tool="crackmapexec",
                trigger_condition="has:domain_credentials",
                target_tool="bloodhound",
                priority=10,
                args_template=["-c", "All"],
                description="Domain credentials obtained, mapping Active Directory",
                enabled=False,  # Requires valid domain creds and DC IP
            )
        )

        # === END Windows/AD Attack Chain ===

        # === NEW: OWASP Injection Chain Rules ===

        # Gobuster found forms/endpoints → test with Nuclei XSS templates
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="has:html_forms",
                target_tool="nuclei",
                priority=8,
                args_template=[
                    "-tags",
                    "xss,rxss",
                    "-severity",
                    "critical,high,medium",
                    "-rate-limit",
                    "50",
                    "-c",
                    "10",
                ],
                description="HTML forms found, testing for XSS vulnerabilities",
            )
        )

        # Gobuster found template endpoints → test with Nuclei SSTI
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:template",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "ssti",
                        "-severity",
                        "critical,high",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="Template engine detected, testing for SSTI",
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:render",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "ssti",
                        "-severity",
                        "critical,high",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="Render endpoint detected, testing for SSTI",
                ),
            ]
        )

        # Gobuster found file parameters → test with Nuclei LFI
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="has:file_params",
                target_tool="nuclei",
                priority=8,
                args_template=[
                    "-tags",
                    "lfi,rfi",
                    "-severity",
                    "critical,high",
                    "-rate-limit",
                    "50",
                    "-c",
                    "10",
                ],
                description="File parameters found, testing for LFI/RFI",
            )
        )

        # SQLMap failed (no SQL injection) → try command injection with Nuclei
        self.rules.append(
            ChainRule(
                trigger_tool="sqlmap",
                trigger_condition="no:sql_injection",
                target_tool="nuclei",
                priority=7,
                args_template=[
                    "-tags",
                    "rce,cmdi",
                    "-severity",
                    "critical,high",
                    "-rate-limit",
                    "50",
                    "-c",
                    "10",
                ],
                description="No SQL injection found, testing for command injection",
            )
        )

        # Gobuster found endpoints → discover parameters with ffuf, then test
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="has:endpoints",
                target_tool="ffuf",
                priority=6,
                args_template=[
                    "-u",
                    "{target}?FUZZ=test",
                    "-w",
                    "data/wordlists/web_files_common.txt",
                    "-fc",
                    "404",
                    "-p",
                    "0.1",
                    "-t",
                    "10",
                ],
                description="Endpoints found, fuzzing for hidden parameters",
            )
        )

        # ffuf found parameters → test with SQLMap (skip for LFI scans)
        # DISABLED: This rule passes {target} (original ffuf target) to sqlmap,
        # which is useless - we need actual discovered endpoints with parameters.
        # The smart chain (rule #-1) in auto_chain() handles ffuf → sqlmap properly
        # by parsing ffuf output and testing discovered endpoints.
        # self.rules.append(
        #     ChainRule(
        #         trigger_tool="ffuf",
        #         trigger_condition="has:parameters_found & !is:lfi_scan",
        #         target_tool="sqlmap",
        #         priority=9,
        #         args_template=["-u", "{target}", "--batch", "--level=2", "--risk=2"],
        #         description="Parameters discovered, testing for SQL injection",
        #     )
        # )

        # ffuf found parameters → test with Nuclei XSS (skip for LFI scans)
        # DISABLED: Same issue as above - uses {target} instead of discovered parameters.
        # Running XSS scans on bare directories like /cgi-bin/ is useless.
        # Smart chains in auto_chain() handle ffuf → nuclei properly.
        # self.rules.append(
        #     ChainRule(
        #         trigger_tool="ffuf",
        #         trigger_condition="has:parameters_found & !is:lfi_scan",
        #         target_tool="nuclei",
        #         priority=8,
        #         args_template=[
        #             "-tags",
        #             "xss,rxss",
        #             "-severity",
        #             "critical,high,medium",
        #             "-rate-limit",
        #             "50",
        #             "-c",
        #             "10",
        #         ],
        #         description="Parameters discovered, testing for XSS",
        #     )
        # )

        # Gobuster found API endpoints → parameter fuzzing with ffuf
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:api",
                    target_tool="ffuf",
                    priority=7,
                    args_template=[
                        "-u",
                        "{target}?FUZZ=test",
                        "-w",
                        "data/wordlists/web_files_common.txt",
                        "-fc",
                        "404",
                        "-p",
                        "0.1",
                        "-t",
                        "10",
                    ],
                    description="API endpoint found, fuzzing for parameters",
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:api",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "api",
                        "-severity",
                        "critical,high",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="API endpoint found, testing API security",
                ),
            ]
        )

        # === END OWASP Injection Chain Rules ===

        # === Directory Category Chain Rules ===
        # These rules trigger based on the category of discovered directories
        # Categories: database_admin, wordpress, drupal, vulnerable_app, custom_php

        # Database Admin (phpMyAdmin, Adminer) → Nuclei CVE scan
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="category:database_admin",
                target_tool="nuclei",
                priority=9,
                args_template=[
                    "-tags",
                    "phpmyadmin,exposure,cve",
                    "-severity",
                    "critical,high,medium",
                    "-rate-limit",
                    "50",
                    "-c",
                    "10",
                ],
                description="Database admin panel detected, scanning for CVEs",
            )
        )

        # Database Admin → SearchSploit for known exploits
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="category:database_admin",
                target_tool="searchsploit",
                priority=8,
                args_template=["--json", "phpMyAdmin"],
                description="Database admin panel detected, searching for exploits",
            )
        )

        # Database Admin → Hydra default credentials
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="category:database_admin",
                target_tool="hydra",
                priority=8,
                args_template=[
                    "http-post-form",
                    "{path}:pma_username=^USER^&pma_password=^PASS^:F=denied",
                    "-C",
                    "data/wordlists/default_credentials.txt",
                    "-t",
                    "1",
                ],
                description="Database admin panel detected, testing default credentials",
            )
        )

        # Database Admin → SQLMap (gentler settings for phpMyAdmin/Adminer)
        # These panels are slow and easily overwhelmed - use single thread and basic tests
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="category:database_admin",
                target_tool="sqlmap",
                priority=6,  # Lower priority than CVE/exploit scans
                args_template=[
                    "-u",
                    "{target}",
                    "--batch",
                    "--forms",
                    "--threads=1",
                    "--time-sec=10",
                    "--level=1",
                    "--risk=1",
                    "--technique=BEU",
                    "--timeout=30",
                ],
                description="Database admin panel detected, testing login form for SQL injection (low intensity)",
            )
        )

        # WordPress → WPScan enumeration
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="category:wordpress",
                target_tool="wpscan",
                priority=9,
                args_template=[
                    "--enumerate",
                    "vp,vt,u",
                    "--plugins-detection",
                    "aggressive",
                    "--random-user-agent",
                ],
                description="WordPress detected, enumerating plugins and themes",
            )
        )

        # WordPress → Nuclei CVE scan
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="category:wordpress",
                target_tool="nuclei",
                priority=8,
                args_template=[
                    "-tags",
                    "wordpress,cve",
                    "-severity",
                    "critical,high,medium",
                    "-rate-limit",
                    "50",
                    "-c",
                    "10",
                ],
                description="WordPress detected, scanning for CVEs",
            )
        )

        # Drupal → Nuclei CVE scan (Drupalgeddon, etc.)
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="category:drupal",
                target_tool="nuclei",
                priority=9,
                args_template=[
                    "-tags",
                    "drupal,drupalgeddon,cve",
                    "-severity",
                    "critical,high,medium",
                    "-rate-limit",
                    "50",
                    "-c",
                    "10",
                ],
                description="Drupal detected, scanning for CVEs",
            )
        )

        # Drupal → SearchSploit for known exploits
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="category:drupal",
                target_tool="searchsploit",
                priority=8,
                args_template=["--json", "Drupal"],
                description="Drupal detected, searching for exploits",
            )
        )

        # Vulnerable App (DVWA, Mutillidae, etc.) → SQLMap crawl
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="category:vulnerable_app",
                target_tool="sqlmap",
                priority=9,
                args_template=[
                    "-u",
                    "{target}",
                    "--batch",
                    "--crawl=2",
                    "--forms",
                    "--level=2",
                    "--risk=2",
                    "--smart",
                    "--threads=5",
                ],
                description="Vulnerable app detected, scan forms for SQL injection",
            )
        )

        # Custom PHP → SQLMap standard crawl - DISABLED
        # Reason: katana→sqlmap handles this better by targeting specific parametrized URLs.
        # The "custom_php" category is too broad (default for unrecognized paths).
        # self.rules.append(
        #     ChainRule(
        #         trigger_tool="gobuster",
        #         trigger_condition="category:custom_php",
        #         target_tool="sqlmap",
        #         ...
        #     )
        # )

        # === END Directory Category Chain Rules ===

        # === Home Directory Exposure Chain Rules ===
        # When gobuster finds .bashrc/.profile, the web root is a home directory
        # This is a critical misconfiguration - enumerate SSH keys and sensitive files

        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="has:home_directory_exposure",
                target_tool="ffuf",
                priority=10,  # High priority - critical finding
                args_template=[
                    "-u",
                    "{target}/FUZZ",
                    "-w",
                    "data/wordlists/home_dir_sensitive.txt",
                    "-mc",
                    "200",
                    "-t",
                    "5",
                    "-p",
                    "0.1",
                ],
                description="Home directory exposed - enumerating SSH keys and sensitive files",
            )
        )

        # Also trigger nuclei for file exposure checks
        self.rules.append(
            ChainRule(
                trigger_tool="gobuster",
                trigger_condition="has:home_directory_exposure",
                target_tool="nuclei",
                priority=9,
                args_template=[
                    "-tags",
                    "exposure,lfi,config",
                    "-severity",
                    "critical,high",
                    "-rate-limit",
                    "50",
                    "-c",
                    "10",
                ],
                description="Home directory exposed - checking for sensitive file disclosure",
            )
        )

        # === END Home Directory Exposure Chain Rules ===

        # theHarvester completed → discover subdomains with DNSRecon
        # NOTE: whois → dnsrecon is disabled to avoid duplicates (theHarvester already chains to dnsrecon)
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="theharvester",
                    trigger_condition="has:target",
                    target_tool="dnsrecon",
                    priority=8,
                    args_template=["-d", "{target}", "-t", "std"],
                    description="Domain identified, enumerating DNS records",
                ),
                # DISABLED: whois → dnsrecon (redundant, theHarvester already chains to dnsrecon)
                # ChainRule(
                #     trigger_tool='whois',
                #     trigger_condition='has:target',
                #     target_tool='dnsrecon',
                #     priority=7,
                #     args_template=['-d', '{target}', '-t', 'std'],
                #     description='Domain registered, enumerating DNS records'
                # ),
            ]
        )

        # DNSRecon found subdomains/hosts → scan them with nmap
        self.rules.append(
            ChainRule(
                trigger_tool="dnsrecon",
                trigger_condition="has:subdomains",
                target_tool="nmap",
                priority=9,
                args_template=["-sV", "-sC", "-T4", "{target}"],
                description="Subdomains discovered, scanning for services",
            )
        )

        # SearchSploit: Trigger on nmap service detection with product/version
        # This will be handled in special auto_chain logic below
        # (nmap → searchsploit is too complex for simple rules)

        # WordPress detected → run WPScan
        # Note: {target} is passed separately to the plugin (plugin adds --url)
        # Plugin will strip path to get base URL (e.g., http://host/wp-content → http://host/)
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:wp-admin",
                    target_tool="wpscan",
                    priority=10,
                    args_template=["--enumerate", "vp,vt,u", "--random-user-agent"],
                    description="WordPress admin panel found, scanning for vulnerabilities",
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:wp-content",
                    target_tool="wpscan",
                    priority=9,
                    args_template=["--enumerate", "vp,vt,u", "--random-user-agent"],
                    description="WordPress installation found, scanning for vulnerabilities",
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:xmlrpc",
                    target_tool="wpscan",
                    priority=9,
                    args_template=["--enumerate", "u", "--random-user-agent"],
                    description="WordPress XML-RPC found, enumerating users",
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:wp-json",
                    target_tool="wpscan",
                    priority=9,
                    args_template=["--enumerate", "u", "--random-user-agent"],
                    description="WordPress REST API found, enumerating users",
                ),
            ]
        )

        # SSH service discovered → optional brute-force (disabled by default for safety)
        # Note: {target} is passed separately to the plugin, not in args_template
        # WARNING: Hydra SSH may fail on legacy servers (OpenSSH < 6.0) with key exchange errors
        #          Use MSF ssh_login instead (has SSH_CLIENT_KEX for legacy algorithm support)
        # -s {port} ensures non-standard SSH ports (e.g., 2222, 22222) are used
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:ssh",
                target_tool="hydra",
                priority=4,
                args_template=[
                    "-L",
                    "data/wordlists/all_users.txt",
                    "-P",
                    "data/wordlists/top20_quick.txt",
                    "-t",
                    "1",
                    "-w",
                    "3",
                    "-s",
                    "{port}",
                    "-f",
                    "ssh",
                ],
                description="SSH detected, testing default credentials",
                enabled=False,  # Disabled by default - MSF ssh_login preferred for compatibility
            )
        )

        # FTP service discovered → test anonymous and brute-force
        # Note: {target} is passed separately to the plugin, not in args_template
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ftp",
                    target_tool="hydra",
                    priority=5,
                    args_template=[
                        "-l",
                        "anonymous",
                        "-p",
                        "anonymous@",
                        "-t",
                        "1",
                        "ftp",
                    ],
                    description="FTP detected, testing anonymous login",
                    enabled=False,  # Disabled by default
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ftp",
                    target_tool="hydra",
                    priority=4,
                    args_template=[
                        "-L",
                        "data/wordlists/all_users.txt",
                        "-P",
                        "data/wordlists/top20_quick.txt",
                        "-t",
                        "1",
                        "-w",
                        "3",
                        "-f",
                        "ftp",
                    ],
                    description="FTP detected, testing default credentials",
                    enabled=False,  # Disabled by default
                ),
            ]
        )

        # WPScan found users → brute-force WordPress login with enumerated usernames
        # Uses {usernames_file} placeholder - replaced in auto_chain with temp file containing enumerated users
        # Note: {target} is passed separately to the plugin, not in args_template
        self.rules.append(
            ChainRule(
                trigger_tool="wpscan",
                trigger_condition="has:users",
                target_tool="hydra",
                priority=6,
                args_template=[
                    "-L",
                    "{usernames_file}",
                    "-P",
                    "data/wordlists/soul_pass.txt",
                    "-t",
                    "2",
                    "-w",
                    "2",
                    "-vV",
                    "http-post-form",
                    "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In:F=is incorrect",
                ],
                description="WordPress users enumerated, testing credentials with enumerated usernames",
                enabled=True,  # Now uses actual enumerated users, more targeted
            )
        )

        # WordPress login found → enumerate valid usernames with Hydra
        # Triggers on wp-login, wp-admin, xmlrpc, and wp-json (all indicate WordPress)
        # Note: {target} is passed separately to the plugin, not in args_template
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:wp-login",
                    target_tool="hydra",
                    priority=7,
                    args_template=[
                        "-L",
                        "data/wordlists/soul_users.txt",
                        "-p",
                        "test",
                        "-t",
                        "2",
                        "-w",
                        "2",
                        "-vV",
                        "http-post-form",
                        "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In:F=Invalid username",
                    ],
                    description="WordPress login found, enumerating valid usernames",
                    enabled=False,  # Disabled by default - brute-force rule
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:wp-admin",
                    target_tool="hydra",
                    priority=7,
                    args_template=[
                        "-L",
                        "data/wordlists/soul_users.txt",
                        "-p",
                        "test",
                        "-t",
                        "2",
                        "-w",
                        "2",
                        "-vV",
                        "http-post-form",
                        "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In:F=Invalid username",
                    ],
                    description="WordPress admin found, enumerating valid usernames",
                    enabled=False,  # Disabled by default - brute-force rule
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:xmlrpc",
                    target_tool="hydra",
                    priority=7,
                    args_template=[
                        "-L",
                        "data/wordlists/soul_users.txt",
                        "-p",
                        "test",
                        "-t",
                        "2",
                        "-w",
                        "2",
                        "-vV",
                        "http-post-form",
                        "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In:F=Invalid username",
                    ],
                    description="WordPress XML-RPC found, enumerating valid usernames via login",
                    enabled=False,  # Disabled by default - brute-force rule
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:wp-json",
                    target_tool="hydra",
                    priority=7,
                    args_template=[
                        "-L",
                        "data/wordlists/soul_users.txt",
                        "-p",
                        "test",
                        "-t",
                        "2",
                        "-w",
                        "2",
                        "-vV",
                        "http-post-form",
                        "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In:F=Invalid username",
                    ],
                    description="WordPress REST API found, enumerating valid usernames via login",
                    enabled=False,  # Disabled by default - brute-force rule
                ),
            ]
        )

        # Hydra found valid usernames → crack passwords for those users
        # Special handling in auto_chain creates temp file from validated usernames
        # Note: {target} is passed separately, {usernames_file} is created by auto_chain
        self.rules.append(
            ChainRule(
                trigger_tool="hydra",
                trigger_condition="has:usernames",
                target_tool="hydra",
                priority=8,
                args_template=[
                    "-L",
                    "{usernames_file}",
                    "-P",
                    "data/wordlists/soul_pass.txt",
                    "-t",
                    "2",
                    "-w",
                    "2",
                    "-vV",
                    "http-post-form",
                    "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In:F=is incorrect",
                ],
                description="Valid usernames found, cracking passwords",
                enabled=False,  # Disabled by default - brute-force rule
            )
        )

        # =====================================================================
        # CREDENTIAL ACCESS & LATERAL MOVEMENT AUTO-CHAINING
        # =====================================================================

        # Kerberos (port 88) detected → GetNPUsers (AS-REP Roasting)
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="port:88",
                target_tool="impacket-getnpusers",
                priority=8,
                args_template=[],
                description="Kerberos detected, attempting AS-REP Roasting",
                enabled=True,
            )
        )

        # =====================================================================
        # LEGACY/CTF VULNERABLE SERVICES - HIGH-VALUE EXPLOIT TARGETS
        # =====================================================================
        # These rules target known vulnerable service versions commonly found
        # in CTF environments, labs, and legacy systems.

        # vsftpd 2.3.4 backdoor (CVE-2011-2523)
        # Triggers backdoor shell on port 6200 when username contains :)
        # Match FTP service with version 2.3.4 (nmap often shows just "ftp" + "2.3.4")
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:ftp & svc_version:2.3.4",
                target_tool="msf_exploit",
                priority=10,
                args_template=["exploit/unix/ftp/vsftpd_234_backdoor"],
                description="FTP 2.3.4 detected - checking for vsftpd backdoor (CVE-2011-2523)",
                category=CATEGORY_CTF,
            )
        )

        # Samba 3.0.x usermap_script RCE (CVE-2007-2447)
        # Command injection in username field
        # Match SMB service with version starting with 3 (nmap shows "3.X" or "3.0.x")
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:smb & svc_version:3.",
                target_tool="msf_exploit",
                priority=10,
                args_template=["exploit/multi/samba/usermap_script"],
                description="Samba 3.x detected - checking for usermap_script RCE (CVE-2007-2447)",
                category=CATEGORY_CTF,
            )
        )
        # Also match netbios-ssn service (common nmap detection for SMB)
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:netbios-ssn & svc_version:3.",
                target_tool="msf_exploit",
                priority=10,
                args_template=["exploit/multi/samba/usermap_script"],
                description="Samba 3.x detected (netbios-ssn) - checking for usermap_script RCE (CVE-2007-2447)",
                category=CATEGORY_CTF,
            )
        )

        # UnrealIRCd 3.2.8.1 backdoor (CVE-2010-2075)
        # DEBUG command triggers backdoor
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:irc",
                target_tool="msf_exploit",
                priority=9,
                args_template=["exploit/unix/irc/unreal_ircd_3281_backdoor"],
                description="IRC service detected - checking for UnrealIRCd backdoor (CVE-2010-2075)",
                category=CATEGORY_CTF,
            )
        )

        # distccd RCE (CVE-2004-2687)
        # Distributed compiler daemon command execution
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:distccd",
                target_tool="msf_exploit",
                priority=9,
                args_template=["exploit/unix/misc/distcc_exec"],
                description="distccd detected - command execution available (CVE-2004-2687)",
                category=CATEGORY_CTF,
            )
        )
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="port:3632",
                target_tool="msf_exploit",
                priority=8,
                args_template=["exploit/unix/misc/distcc_exec"],
                description="Port 3632 detected - checking for distccd RCE",
                category=CATEGORY_CTF,
            )
        )

        # Java RMI exploitation
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:java-rmi",
                    target_tool="msf_auxiliary",
                    priority=8,
                    args_template=["auxiliary/scanner/misc/java_rmi_server"],
                    description="Java RMI detected - enumerating registry",
                    category=CATEGORY_CTF,
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:1099",
                    target_tool="msf_auxiliary",
                    priority=7,
                    args_template=["auxiliary/scanner/misc/java_rmi_server"],
                    description="Port 1099 detected - checking for Java RMI",
                    category=CATEGORY_CTF,
                ),
            ]
        )

        # NFS enumeration
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:nfs",
                    target_tool="msf_auxiliary",
                    priority=7,
                    args_template=["auxiliary/scanner/nfs/nfsmount"],
                    description="NFS detected - enumerating exports",
                    category=CATEGORY_CTF,
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:2049",
                    target_tool="msf_auxiliary",
                    priority=6,
                    args_template=["auxiliary/scanner/nfs/nfsmount"],
                    description="Port 2049 detected - checking for NFS exports",
                    category=CATEGORY_CTF,
                ),
            ]
        )

        # Service Explorer - browse accessible services
        self.rules.extend(
            [
                # FTP anonymous access found → explore files
                # MSF parser creates findings titled "FTP Anonymous Access (READ/WRITE)"
                ChainRule(
                    trigger_tool="msf_auxiliary",
                    trigger_condition="finding:ftp anonymous",
                    target_tool="service_explorer",
                    priority=6,
                    args_template=["ftp://anonymous@{target}", "--download"],
                    description="FTP anonymous access found, exploring files",
                ),
                # Redis no-auth → explore database
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:redis",
                    target_tool="service_explorer",
                    priority=6,
                    args_template=["redis://{target}:{port}"],
                    description="Redis detected, exploring database",
                ),
                # NFS exports found → explore shares
                # MSF parser creates findings titled "NFS Export Found"
                ChainRule(
                    trigger_tool="msf_auxiliary",
                    trigger_condition="finding:nfs export",
                    target_tool="service_explorer",
                    priority=6,
                    args_template=["nfs://{target}", "--download"],
                    description="NFS exports found, exploring shares",
                ),
                # MongoDB no-auth → explore database
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:mongodb",
                    target_tool="service_explorer",
                    priority=6,
                    args_template=["mongodb://{target}:{port}"],
                    description="MongoDB detected, exploring database",
                ),
            ]
        )

        # R-services (rsh, rlogin, rexec) - legacy trust-based services
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:512",
                    target_tool="msf_auxiliary",
                    priority=7,
                    args_template=["auxiliary/scanner/rservices/rexec_login"],
                    description="rexec (512) detected - checking for trust exploitation",
                    category=CATEGORY_CTF,
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:513",
                    target_tool="msf_auxiliary",
                    priority=7,
                    args_template=["auxiliary/scanner/rservices/rlogin_login"],
                    description="rlogin (513) detected - checking for trust exploitation",
                    category=CATEGORY_CTF,
                ),
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:514",
                    target_tool="msf_auxiliary",
                    priority=7,
                    args_template=["auxiliary/scanner/rservices/rsh_login"],
                    description="rsh (514) detected - checking for trust exploitation",
                    category=CATEGORY_CTF,
                ),
            ]
        )

        # Telnet service - check for default/weak credentials
        # NOTE: Disabled - duplicates GENERAL rule at line ~585
        # self.rules.append(
        #     ChainRule(
        #         trigger_tool='nmap',
        #         trigger_condition='service:telnet',
        #         target_tool='msf_auxiliary',
        #         priority=6,
        #         args_template=['auxiliary/scanner/telnet/telnet_login', ...],
        #         description='Telnet detected - checking for default credentials',
        #         category=CATEGORY_CTF
        #     )
        # )

        # UPnP enumeration - IoT/router discovery
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:upnp",
                target_tool="msf_auxiliary",
                priority=6,
                args_template=["auxiliary/scanner/upnp/ssdp_msearch"],
                description="UPnP detected - enumerating devices",
                category=CATEGORY_CTF,
            )
        )

        # X11 open access check
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="port:6000",
                target_tool="msf_auxiliary",
                priority=6,
                args_template=["auxiliary/scanner/x11/open_x11"],
                description="X11 (6000) detected - checking for open access",
                category=CATEGORY_CTF,
            )
        )

        # Cockpit / Port 9090 - Linux admin panel
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="port:9090",
                target_tool="nuclei",
                priority=8,
                args_template=[
                    "-u",
                    "https://{target}:9090",
                    "-rate-limit",
                    "50",
                    "-c",
                    "10",
                ],
                description="Port 9090 detected (Cockpit/admin panel) - scanning with Nuclei",
                category=CATEGORY_CTF,
            )
        )

        # Bindshell detection - common backdoor port
        # Note: Port 1524 (ingreslock) is typically a bindshell on vulnerable systems
        # Connect manually with: nc <target> 1524
        # No automated scanner - this requires manual verification
        # (Commented out - no suitable plugin, requires manual connection)
        # self.rules.append(
        #     ChainRule(
        #         trigger_tool='nmap',
        #         trigger_condition='port:1524',
        #         target_tool='manual',
        #         priority=10,
        #         args_template=[],
        #         description='Port 1524 detected - POSSIBLE BINDSHELL (try: nc {target} 1524)',
        #         category=CATEGORY_CTF
        #     )
        # )

        # AJP/Tomcat Ghostcat (CVE-2020-1938)
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="port:8009",
                target_tool="msf_auxiliary",
                priority=8,
                args_template=["auxiliary/admin/http/tomcat_ghostcat"],
                description="AJP (8009) detected - checking for Ghostcat (CVE-2020-1938)",
                category=CATEGORY_CTF,
            )
        )

        # ProFTPD mod_copy (CVE-2015-3306) - file copy without auth
        # Match FTP service with version 1.3.x (common ProFTPD versions)
        self.rules.append(
            ChainRule(
                trigger_tool="nmap",
                trigger_condition="service:ftp & svc_version:1.3",
                target_tool="msf_exploit",
                priority=8,
                args_template=["exploit/unix/ftp/proftpd_modcopy_exec"],
                description="FTP 1.3.x detected - checking for ProFTPD mod_copy RCE (CVE-2015-3306)",
                category=CATEGORY_CTF,
            )
        )

        # =====================================================================
        # END LEGACY/CTF VULNERABLE SERVICES
        # =====================================================================

        # =====================================================================
        # JUICE SHOP / MODERN WEB APP DETECTION
        # =====================================================================
        # Rules for detecting and attacking OWASP Juice Shop and similar
        # modern JavaScript web applications (Node.js, Angular, React, Vue)

        # Juice Shop API endpoints indicate vulnerable app
        self.rules.extend(
            [
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:api",
                    target_tool="nuclei",
                    priority=9,
                    args_template=[
                        "-tags",
                        "exposure,misconfiguration,cve",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="API endpoint found - scanning for Juice Shop/modern app vulnerabilities",
                    category=CATEGORY_CTF,
                ),
                # REST endpoints suggest modern JS app
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:rest",
                    target_tool="nuclei",
                    priority=9,
                    args_template=[
                        "-tags",
                        "exposure,token,jwt",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="REST API found - checking for JWT/token vulnerabilities",
                    category=CATEGORY_CTF,
                ),
                # FTP directory exposure (common in Juice Shop)
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:ftp",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "exposure,lfi",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="FTP directory found - checking for file disclosure",
                    category=CATEGORY_CTF,
                ),
                # Metrics endpoint (Prometheus/monitoring exposure)
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:metrics",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "exposure,misconfiguration",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="Metrics endpoint found - checking for information disclosure",
                    category=CATEGORY_CTF,
                ),
                # Angular/React source maps
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:main.js",
                    target_tool="nuclei",
                    priority=7,
                    args_template=[
                        "-tags",
                        "exposure,js",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="JavaScript bundle found - checking for source map exposure",
                    category=CATEGORY_CTF,
                ),
            ]
        )

        # =====================================================================
        # END JUICE SHOP / MODERN WEB APP DETECTION
        # =====================================================================

        # =====================================================================
        # ACTIVE DIRECTORY ATTACK CHAINS
        # Real-world enterprise penetration testing patterns
        # =====================================================================
        self.rules.extend(
            [
                # Kerberos → Kerberoasting (AS-REP roasting)
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:88 & has:domains",
                    target_tool="impacket-getnpusers",
                    priority=9,
                    args_template=[
                        "{domain}/",
                        "-dc-ip",
                        "{dc_ip}",
                        "-no-pass",
                        "-usersfile",
                        "data/wordlists/ad_users.txt",
                    ],
                    description="Kerberos detected with domain - checking for AS-REP roastable users",
                    category=CATEGORY_ENTERPRISE,
                ),
                # LDAP → BloodHound collection
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ldap & has:domains",
                    target_tool="bloodhound-python",
                    priority=8,
                    args_template=[
                        "-c",
                        "All",
                        "-d",
                        "{domain}",
                        "-dc",
                        "{dc_ip}",
                        "-ns",
                        "{dc_ip}",
                    ],
                    enabled=False,  # Disabled by default - needs creds
                    description="LDAP detected - BloodHound collection (requires valid creds)",
                    category=CATEGORY_ENTERPRISE,
                ),
                # SMB signing disabled → Relay attack potential
                ChainRule(
                    trigger_tool="crackmapexec",
                    trigger_condition="finding:signing:False",
                    target_tool="responder",
                    priority=8,
                    args_template=["-I", "{target}", "-rdw"],
                    enabled=False,  # Manual - requires network positioning
                    description="SMB signing disabled - relay attacks possible (run Responder manually)",
                    category=CATEGORY_ENTERPRISE,
                ),
                # LDAP → Domain enumeration
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ldap",
                    target_tool="ldapsearch",
                    priority=7,
                    args_template=[
                        "-x",
                        "-H",
                        "ldap://{target}",
                        "-b",
                        "",
                        "-s",
                        "base",
                        "namingContexts",
                    ],
                    description="LDAP detected - enumerating naming contexts",
                    category=CATEGORY_ENTERPRISE,
                ),
                # WinRM → Password spray candidate
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:5985",
                    target_tool="crackmapexec",
                    priority=6,
                    args_template=["winrm", "-u", "administrator", "-p", "password"],
                    enabled=False,  # Disabled - needs valid creds
                    description="WinRM detected - potential for password spray (disabled by default)",
                    category=CATEGORY_ENTERPRISE,
                ),
                # RDP → Check for NLA
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:rdp",
                    target_tool="rdp-sec-check",
                    priority=6,
                    args_template=["{target}"],
                    description="RDP detected - checking security configuration",
                    category=CATEGORY_ENTERPRISE,
                ),
            ]
        )

        # =====================================================================
        # CLOUD MISCONFIGURATION DETECTION
        # AWS, Azure, GCP reconnaissance patterns
        # =====================================================================
        self.rules.extend(
            [
                # HTTP with cloud metadata hints → SSRF checks
                ChainRule(
                    trigger_tool="nuclei",
                    trigger_condition="finding:aws",
                    target_tool="nuclei",
                    priority=9,
                    args_template=[
                        "-tags",
                        "ssrf,aws,cloud",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="AWS indicators found - checking for SSRF/metadata access",
                    category=CATEGORY_ENTERPRISE,
                ),
                ChainRule(
                    trigger_tool="nuclei",
                    trigger_condition="finding:azure",
                    target_tool="nuclei",
                    priority=9,
                    args_template=[
                        "-tags",
                        "ssrf,azure,cloud",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="Azure indicators found - checking for SSRF/metadata access",
                    category=CATEGORY_ENTERPRISE,
                ),
                # S3 bucket enumeration
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:s3",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "s3,bucket,exposure",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="S3 reference found - checking for bucket misconfigurations",
                    category=CATEGORY_ENTERPRISE,
                ),
                # Cloud storage URLs
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:blob.core.windows.net",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "azure,storage,exposure",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="Azure Blob reference found - checking for storage misconfigurations",
                    category=CATEGORY_ENTERPRISE,
                ),
                # API Gateway detection
                ChainRule(
                    trigger_tool="nuclei",
                    trigger_condition="finding:api-gateway",
                    target_tool="nuclei",
                    priority=7,
                    args_template=[
                        "-tags",
                        "api,exposure,aws",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="API Gateway detected - checking for misconfigurations",
                    category=CATEGORY_ENTERPRISE,
                ),
            ]
        )

        # =====================================================================
        # MODERN WEB APPLICATION PATTERNS
        # GraphQL, OAuth, JWT, API security
        # =====================================================================
        self.rules.extend(
            [
                # GraphQL endpoint discovery → Introspection check
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:graphql",
                    target_tool="nuclei",
                    priority=9,
                    args_template=[
                        "-tags",
                        "graphql,introspection,exposure",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="GraphQL endpoint found - checking for introspection enabled",
                    category=CATEGORY_ENTERPRISE,
                ),
                # OAuth endpoints → Authorization bypass checks
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:oauth",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "oauth,token,misconfiguration",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="OAuth endpoint found - checking for authorization issues",
                    category=CATEGORY_ENTERPRISE,
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:authorize",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "oauth,oidc,redirect",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="Authorization endpoint found - checking for redirect issues",
                    category=CATEGORY_ENTERPRISE,
                ),
                # JWT in responses → Token analysis
                ChainRule(
                    trigger_tool="nuclei",
                    trigger_condition="finding:jwt",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "jwt,token,exposure",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="JWT token found - checking for weak algorithms/secrets",
                    category=CATEGORY_ENTERPRISE,
                ),
                # Swagger/OpenAPI exposure
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:swagger",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "swagger,openapi,exposure",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="Swagger/OpenAPI found - checking for sensitive endpoint exposure",
                    category=CATEGORY_ENTERPRISE,
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:openapi",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "swagger,openapi,api",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="OpenAPI spec found - analyzing for security issues",
                    category=CATEGORY_ENTERPRISE,
                ),
                # WebSocket endpoints
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:websocket",
                    target_tool="nuclei",
                    priority=7,
                    args_template=[
                        "-tags",
                        "websocket,exposure",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="WebSocket endpoint found - checking for security issues",
                    category=CATEGORY_ENTERPRISE,
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:socket.io",
                    target_tool="nuclei",
                    priority=7,
                    args_template=[
                        "-tags",
                        "websocket,socketio",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="Socket.io found - checking for real-time communication issues",
                    category=CATEGORY_ENTERPRISE,
                ),
                # API versioning patterns
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:v1",
                    target_tool="gobuster",
                    priority=6,
                    args_template=[
                        "dir",
                        "-u",
                        "http://{target}:{port}/v2/",
                        "-w",
                        "data/wordlists/web_dirs_common.txt",
                        "--no-error",
                        "-t",
                        "5",
                        "--delay",
                        "20ms",
                    ],
                    description="API v1 found - checking for deprecated API versions",
                    category=CATEGORY_ENTERPRISE,
                ),
                # Debug/development endpoints
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:debug",
                    target_tool="nuclei",
                    priority=9,
                    args_template=[
                        "-tags",
                        "debug,exposure,misconfiguration",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="Debug endpoint found - high priority security check",
                    category=CATEGORY_ENTERPRISE,
                ),
                ChainRule(
                    trigger_tool="gobuster",
                    trigger_condition="finding:console",
                    target_tool="nuclei",
                    priority=8,
                    args_template=[
                        "-tags",
                        "console,admin,exposure",
                        "-rate-limit",
                        "50",
                        "-c",
                        "10",
                    ],
                    description="Console endpoint found - checking for exposed admin interfaces",
                    category=CATEGORY_ENTERPRISE,
                ),
            ]
        )

        # =====================================================================
        # ROUTER TESTING CHAIN RULES
        # Home router detection → enumeration → exploitation
        # =====================================================================
        self.rules.extend(
            [
                # Router detection triggers RouterSploit scan
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="device:router",
                    target_tool="routersploit",
                    priority=9,
                    description="Router detected - scanning for vulnerabilities with RouterSploit",
                    category=CATEGORY_GENERAL,
                ),
                # UPnP service → UPnP enumeration
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:upnp",
                    target_tool="upnp",
                    priority=8,
                    description="UPnP service detected - enumerating device info",
                    category=CATEGORY_GENERAL,
                ),
                # UPnP found → UPnP abuse (port mapping)
                ChainRule(
                    trigger_tool="upnp",
                    trigger_condition="has:upnp_services",
                    target_tool="upnp_abuse",
                    priority=7,
                    args_template=["list"],
                    description="UPnP enumerated - checking port mappings",
                    category=CATEGORY_GENERAL,
                ),
                # TR-069 port → TR-069 detection
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:7547",
                    target_tool="tr069",
                    priority=8,
                    description="TR-069/CWMP port detected - ISP management check",
                    category=CATEGORY_GENERAL,
                ),
                # Router with HTTP → HTTP brute force
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="device:router & service:http",
                    target_tool="router_http_brute",
                    priority=7,
                    description="Router web admin detected - testing default credentials",
                    category=CATEGORY_GENERAL,
                ),
                # Router with SSH → SSH brute force
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="device:router & port:22",
                    target_tool="router_ssh_brute",
                    priority=6,
                    description="Router SSH detected - testing default credentials",
                    category=CATEGORY_GENERAL,
                ),
                # Router with Telnet → Telnet brute force
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="device:router & port:23",
                    target_tool="router_telnet_brute",
                    priority=7,
                    description="Router Telnet detected - testing default credentials",
                    category=CATEGORY_GENERAL,
                ),
                # RouterSploit found vulns → exploit
                ChainRule(
                    trigger_tool="routersploit",
                    trigger_condition="has:vulnerabilities",
                    target_tool="routersploit_exploit",
                    priority=10,
                    description="RouterSploit found vulnerabilities - attempting exploitation",
                    category=CATEGORY_GENERAL,
                ),
                # Router with DNS → DNS hijack check
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="device:router & port:53",
                    target_tool="dns_hijack",
                    priority=5,
                    description="Router DNS detected - checking for DNS hijacking",
                    category=CATEGORY_GENERAL,
                ),
            ]
        )

        # =====================================================================
        # macOS TESTING CHAIN RULES
        # Apple device detection → enumeration → exploitation
        # =====================================================================
        self.rules.extend(
            [
                # macOS detection → AFP enumeration
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:afp",
                    target_tool="afp",
                    priority=8,
                    description="AFP (Apple Filing) detected - enumerating shares",
                    category=CATEGORY_GENERAL,
                ),
                # macOS detection → VNC/ARD enumeration
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="os:macos & port:5900",
                    target_tool="ard",
                    priority=8,
                    description="macOS Screen Sharing detected - enumerating VNC/ARD",
                    category=CATEGORY_GENERAL,
                ),
                # VNC port without OS detection
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="service:ard",
                    target_tool="ard",
                    priority=7,
                    description="VNC/ARD service detected - enumerating",
                    category=CATEGORY_GENERAL,
                ),
                # mDNS discovery
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="port:5353",
                    target_tool="mdns",
                    priority=6,
                    description="mDNS/Bonjour detected - discovering Apple services",
                    category=CATEGORY_GENERAL,
                ),
                # AFP shares found → AFP brute force
                ChainRule(
                    trigger_tool="afp",
                    trigger_condition="has:shares",
                    target_tool="afp_brute",
                    priority=7,
                    description="AFP shares discovered - testing credentials",
                    category=CATEGORY_GENERAL,
                ),
                # VNC auth required → VNC brute force
                ChainRule(
                    trigger_tool="ard",
                    trigger_condition="has:vnc_auth_required",
                    target_tool="vnc_brute",
                    priority=7,
                    description="VNC auth required - testing passwords",
                    category=CATEGORY_GENERAL,
                ),
                # VNC brute success → VNC access
                ChainRule(
                    trigger_tool="vnc_brute",
                    trigger_condition="has:credentials",
                    target_tool="vnc_access",
                    priority=9,
                    args_template=["--screenshot"],
                    description="VNC credentials found - capturing screenshot",
                    category=CATEGORY_GENERAL,
                ),
                # macOS SSH → SSH brute force
                ChainRule(
                    trigger_tool="nmap",
                    trigger_condition="os:macos & port:22",
                    target_tool="macos_ssh",
                    priority=7,
                    description="macOS SSH detected - testing credentials",
                    category=CATEGORY_GENERAL,
                ),
            ]
        )

        # =====================================================================
        # CVE-BASED VERSION-AWARE CHAIN RULES
        # Auto-generated from CVE database for known vulnerable versions
        # =====================================================================
        self._init_cve_rules()

        # =====================================================================
        # END REAL-WORLD CHAIN RULES
        # =====================================================================

    def _init_cve_rules(self):
        """Generate ChainRules from CVE database for version-aware chaining."""
        try:
            from souleyez.core.cve_mappings import (
                generate_version_condition,
                get_all_cves,
            )
        except ImportError:
            return  # CVE mappings not available

        cve_rules = []
        for cve in get_all_cves().values():
            # Generate version condition (e.g., 'version:apache:>=2.4.49,<=2.4.50')
            condition = generate_version_condition(cve)

            # Create chain rule
            rule = ChainRule(
                trigger_tool="nmap",  # CVE checks trigger after nmap finds the service
                trigger_condition=condition,
                target_tool=cve.tool,
                priority=(
                    10
                    if cve.severity == "critical"
                    else 9 if cve.severity == "high" else 8
                ),
                args_template=cve.args.copy(),
                description=f"{cve.cve_id}: {cve.description}",
                category=CATEGORY_GENERAL,
            )
            cve_rules.append(rule)

        self.rules.extend(cve_rules)

    def add_rule(self, rule: ChainRule):
        """Add a custom chaining rule."""
        self.rules.append(rule)

    def remove_rule(self, trigger_tool: str, target_tool: str):
        """Remove a chaining rule."""
        self.rules = [
            r
            for r in self.rules
            if not (r.trigger_tool == trigger_tool and r.target_tool == target_tool)
        ]

    def toggle_chaining(self) -> bool:
        """
        Toggle auto-chaining on/off.

        Returns:
            New state (True = enabled, False = disabled)
        """
        self.enabled = not self.enabled
        self._save_enabled_state()  # Persist state to disk
        return self.enabled

    @staticmethod
    def _get_state_file() -> str:
        """Get path to auto-chain state file."""
        import os
        from pathlib import Path

        data_dir = Path.home() / ".souleyez"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / ".autochain_enabled")

    @staticmethod
    def check_enabled_status() -> bool:
        """
        Lightweight check of auto-chaining status without instantiating ToolChaining.

        This is much faster than creating a ToolChaining() instance and avoids
        potential lock contention issues.

        Returns:
            True if auto-chaining is enabled, False otherwise
        """
        import os
        from pathlib import Path

        data_dir = Path.home() / ".souleyez"
        state_file = data_dir / ".autochain_enabled"

        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    return f.read().strip().lower() == "true"
            except:
                pass
        return False  # Default: disabled (PRO feature)

    def _load_enabled_state(self) -> bool:
        """Load enabled state from file. Defaults to False if file doesn't exist."""
        import os

        state_file = self._get_state_file()
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    return f.read().strip().lower() == "true"
            except:
                pass
        return False  # Default: disabled (PRO feature)

    def _save_enabled_state(self):
        """Save enabled state to file."""
        state_file = self._get_state_file()
        try:
            with open(state_file, "w") as f:
                f.write("true" if self.enabled else "false")
        except Exception as e:
            from souleyez.log_config import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to save auto-chain state: {e}")

    def is_enabled(self) -> bool:
        """
        Check if auto-chaining is enabled.

        Verifies both:
        1. User-toggled state (re-read from file to catch UI changes)
        2. License tier (AUTO_CHAINING requires PRO)

        If user has FREE license but auto-chain was left enabled (e.g., after
        downgrade from PRO), this will auto-disable and return False.
        """
        # Re-read from file to catch changes made by other processes (UI)
        # ToolChaining is a singleton that persists, so we must refresh state
        self.enabled = self._load_enabled_state()

        if not self.enabled:
            return False

        # Verify license allows auto-chaining
        try:
            from souleyez.feature_flags.features import Feature, FeatureFlags
            from souleyez.licensing import get_active_license

            license_info = get_active_license()
            # Check tier directly - if license exists with PRO tier, allow it
            # Don't rely on is_valid which may have edge cases
            user_tier = "FREE"
            if license_info:
                if license_info.tier == "PRO":
                    user_tier = "PRO"
                elif license_info.is_valid and license_info.tier:
                    user_tier = license_info.tier

            if not FeatureFlags.is_enabled(Feature.AUTO_CHAINING, user_tier):
                # User doesn't have PRO - disable auto-chaining
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)
                logger.warning("Auto-chaining disabled: PRO license required")
                self.enabled = False
                self._save_enabled_state()
                return False

        except Exception as e:
            # If license check fails, log but allow (fail open for PRO users)
            # This prevents blocking legitimate PRO users due to import issues
            from souleyez.log_config import get_logger

            logger = get_logger(__name__)
            logger.warning(f"License check skipped for auto-chaining: {e}")
            # Don't return False - let it continue

        return True

    # ========== AI CHAIN ADVISOR METHODS ==========

    def _get_ai_chain_mode(self) -> str:
        """Get AI chain advisor mode from config. Returns 'off', 'suggest', or 'auto'."""
        try:
            from souleyez import config

            return config.get("ai.chain_mode", "off")
        except Exception:
            return "off"  # Default to off - AI advisor is opt-in

    def get_ai_recommendations(
        self,
        tool: str,
        target: str,
        parse_results: dict,
        static_commands: list,
        engagement_id: int = None,
    ) -> list:
        """
        Get AI-powered tool recommendations.

        Args:
            tool: Tool that just completed
            target: Target that was scanned
            parse_results: Parsed output from the tool
            static_commands: Commands already queued by static rules
            engagement_id: Current engagement ID

        Returns:
            List of command dicts from AI recommendations (empty if disabled/unavailable)
        """
        from souleyez.log_config import get_logger

        logger = get_logger(__name__)

        mode = self._get_ai_chain_mode()
        logger.debug(
            f"AI Chain Advisor called: tool={tool}, target={target}, mode={mode}"
        )

        if mode == "off":
            logger.debug("AI Chain Advisor is disabled (mode=off)")
            return []

        try:
            from souleyez.ai.chain_advisor import ChainAdvisor, ChainAdvisorMode

            advisor_mode = (
                ChainAdvisorMode.AUTO if mode == "auto" else ChainAdvisorMode.SUGGEST
            )
            advisor = ChainAdvisor(mode=advisor_mode)

            if not advisor.is_available():
                logger.debug("AI provider not available for chain analysis")
                return []

            logger.info(f"AI Chain Advisor analyzing: tool={tool}, target={target}")
            analysis = advisor.analyze_results(
                tool=tool,
                target=target,
                parse_results=parse_results,
                static_commands=static_commands,
                engagement_id=engagement_id,
            )

            if analysis.error:
                logger.debug(f"AI chain analysis error: {analysis.error}")
                return []

            if not analysis.recommendations:
                logger.debug("AI analysis returned no recommendations")
                return []

            logger.info(
                f"AI advisor generated {len(analysis.recommendations)} recommendations"
            )

            # Convert to command format
            commands = advisor.to_chain_commands(
                analysis.recommendations, {"target": target}
            )

            if mode == "suggest":
                # Store suggestions for UI display (don't auto-queue)
                logger.info(
                    f"Storing {len(analysis.recommendations)} AI suggestions for engagement {engagement_id}"
                )
                self._store_ai_suggestions(engagement_id, analysis)
                return []  # Don't return commands in suggest mode

            # Auto mode - return commands to be queued
            logger.info(
                f"AI advisor queuing {len(commands)} recommendations (auto mode)"
            )
            return commands

        except ImportError as ie:
            logger.debug(f"AI module not available: {ie}")
            return []
        except Exception as e:
            logger.warning(f"AI chain advisor failed: {e}")
            return []

    def _store_ai_suggestions(self, engagement_id: int, analysis) -> None:
        """Store AI suggestions for later display in UI."""
        if not engagement_id:
            return

        try:
            import json
            from pathlib import Path

            suggestions_dir = Path.home() / ".souleyez" / "ai_suggestions"
            suggestions_dir.mkdir(parents=True, exist_ok=True)

            suggestions_file = suggestions_dir / f"engagement_{engagement_id}.json"

            # Load existing suggestions
            existing = []
            if suggestions_file.exists():
                try:
                    with open(suggestions_file, "r") as f:
                        existing = json.load(f)
                except Exception:
                    existing = []

            # Add new suggestions
            import time

            for rec in analysis.recommendations:
                existing.append(
                    {
                        "timestamp": time.time(),
                        "tool": rec.tool,
                        "target": rec.target,
                        "args": rec.args,
                        "priority": rec.priority,
                        "rationale": rec.rationale,
                        "confidence": rec.confidence,
                        "expected": rec.expected_outcome,
                        "risk": rec.risk_level,
                        "provider": analysis.provider,
                        "approved": False,
                    }
                )

            # Keep only last 50 suggestions
            existing = existing[-50:]

            with open(suggestions_file, "w") as f:
                json.dump(existing, f, indent=2)

        except Exception as e:
            from souleyez.log_config import get_logger

            logger = get_logger(__name__)
            logger.debug(f"Failed to store AI suggestions: {e}")

    def get_pending_ai_suggestions(self, engagement_id: int) -> list:
        """Get pending AI suggestions for an engagement."""
        try:
            import json
            from pathlib import Path

            suggestions_file = (
                Path.home()
                / ".souleyez"
                / "ai_suggestions"
                / f"engagement_{engagement_id}.json"
            )
            if not suggestions_file.exists():
                return []

            with open(suggestions_file, "r") as f:
                suggestions = json.load(f)

            # Return only unapproved suggestions
            return [s for s in suggestions if not s.get("approved", False)]

        except Exception:
            return []

    def enable_chaining(self):
        """Enable auto-chaining."""
        self.enabled = True
        self._save_enabled_state()

    def disable_chaining(self):
        """
        Disable auto-chaining.

        Note: Does NOT clear pending chainable jobs to avoid database locks.
        The worker will respect the disabled state and skip chaining on new jobs.
        """
        self.enabled = False
        self._save_enabled_state()

    # ========== APPROVAL MODE METHODS ==========

    @staticmethod
    def _get_approval_mode_file() -> str:
        """Get path to approval mode state file."""
        import os
        from pathlib import Path

        data_dir = Path.home() / ".souleyez"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / ".approval_mode")

    def _load_approval_mode(self) -> bool:
        """Load approval mode state from file. Defaults to False (auto mode)."""
        import os

        state_file = self._get_approval_mode_file()
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    return f.read().strip().lower() == "true"
            except:
                pass
        return False  # Default: auto mode (no approval required)

    def _save_approval_mode(self):
        """Save approval mode state to file."""
        state_file = self._get_approval_mode_file()
        try:
            with open(state_file, "w") as f:
                f.write("true" if self.approval_mode else "false")
        except Exception as e:
            from souleyez.log_config import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to save approval mode state: {e}")

    def is_approval_mode(self) -> bool:
        """
        Check if approval mode is enabled (chains require approval before execution).

        Always re-reads from file to ensure we see changes made by UI while
        worker is running (since ToolChaining is a singleton that persists).
        """
        # Re-read from file to catch changes made by other processes (UI)
        self.approval_mode = self._load_approval_mode()
        return self.approval_mode

    def enable_approval_mode(self):
        """Enable approval mode - chains will queue for user approval instead of auto-executing."""
        self.approval_mode = True
        self._save_approval_mode()

    def disable_approval_mode(self):
        """Disable approval mode - chains will auto-execute (default behavior)."""
        self.approval_mode = False
        self._save_approval_mode()

    def toggle_approval_mode(self) -> bool:
        """Toggle approval mode and return new state."""
        self.approval_mode = not self.approval_mode
        self._save_approval_mode()
        return self.approval_mode

    def execute_approved_chains(self, engagement_id: int = None) -> List[int]:
        """
        Execute all approved pending chains.

        Args:
            engagement_id: Filter by engagement (None = all)

        Returns:
            List of job IDs created
        """
        from souleyez.core.pending_chains import (
            get_approved_chains,
            mark_chain_executed,
        )
        from souleyez.engine.background import enqueue_job, get_job

        job_ids = []
        approved = get_approved_chains(engagement_id)

        for chain in approved:
            try:
                # Get parent tool name for label
                parent_tool = "manual"
                parent_job_id = chain.get("parent_job_id")
                if parent_job_id:
                    try:
                        parent_job = get_job(parent_job_id)
                        if parent_job:
                            parent_tool = parent_job.get("tool", "manual")
                    except Exception:
                        pass

                job_id = enqueue_job(
                    tool=chain["tool"],
                    target=chain["target"],
                    args=chain.get("args", []),
                    label=parent_tool,
                    engagement_id=chain.get("engagement_id"),
                    parent_id=chain.get("parent_job_id"),
                    reason=chain.get("rule_description", "Approved chain"),
                    metadata=chain.get("metadata"),
                )
                mark_chain_executed(chain["id"], job_id)
                job_ids.append(job_id)
            except Exception as e:
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)
                logger.error(f"Failed to execute approved chain {chain['id']}: {e}")

        return job_ids

    def save_rules(self):
        """Save current rule states (enabled/disabled, priority, trigger_count) to disk."""
        import json
        from pathlib import Path

        rules_file = Path.home() / ".souleyez" / "chain_rules_state.json"

        # Save enabled/disabled state plus priority and trigger counts
        # NOTE: args_template is NOT saved because multiple rules can share the same key
        # but have different args. Saving would corrupt rules on reload.
        rules_state = {}
        for rule in self.rules:
            rule_key = (
                f"{rule.trigger_tool}→{rule.target_tool}:{rule.trigger_condition}"
            )
            # Store as dict to support multiple fields
            rules_state[rule_key] = {
                "enabled": rule.enabled,
                "priority": rule.priority,
                "trigger_count": rule.trigger_count,
            }

        try:
            with open(rules_file, "w") as f:
                json.dump(rules_state, f, indent=2)
        except Exception as e:
            from souleyez.log_config import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to save rule states: {e}")

    def load_rules_state(self):
        """Load saved rule states (enabled/disabled, priority, trigger_count) from disk."""
        import json
        from pathlib import Path

        rules_file = Path.home() / ".souleyez" / "chain_rules_state.json"

        if not rules_file.exists():
            return

        try:
            with open(rules_file, "r") as f:
                rules_state = json.load(f)

            # Apply saved state to matching rules
            for rule in self.rules:
                rule_key = (
                    f"{rule.trigger_tool}→{rule.target_tool}:{rule.trigger_condition}"
                )
                if rule_key in rules_state:
                    state = rules_state[rule_key]
                    # Handle both old format (boolean) and new format (dict)
                    if isinstance(state, bool):
                        # Legacy format: just enabled boolean
                        rule.enabled = state
                    elif isinstance(state, dict):
                        # New format: dict with enabled, priority, trigger_count
                        # NOTE: args_template is NOT loaded from saved state because multiple
                        # rules can share the same key but have different args. Loading saved
                        # args would corrupt all rules with the same condition.
                        if "enabled" in state:
                            rule.enabled = state["enabled"]
                        if "priority" in state:
                            rule.priority = state["priority"]
                        if "trigger_count" in state:
                            rule.trigger_count = state["trigger_count"]
        except Exception as e:
            from souleyez.log_config import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to load rule states: {e}")

    def add_custom_rule(self, rule_dict: Dict[str, Any]) -> bool:
        """
        Add a custom user-created chain rule.

        Args:
            rule_dict: Dictionary with rule definition

        Returns:
            bool: True if added successfully
        """
        try:
            # Create ChainRule from dict
            rule = ChainRule(
                trigger_tool=rule_dict["trigger_tool"],
                trigger_condition=rule_dict["condition"],
                target_tool=rule_dict["target_tool"],
                priority=rule_dict.get("priority", 5),
                args_template=rule_dict.get("args", []),
                enabled=rule_dict.get("enabled", True),
                description=rule_dict.get("description", ""),
                category=rule_dict.get("category", CATEGORY_GENERAL),
            )

            # Add to rules list
            self.rules.append(rule)

            # Save to persistent storage
            self._save_custom_rules()

            # Also save rules state
            self.save_rules()

            return True

        except Exception as e:
            from souleyez.log_config import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to add custom rule: {e}")
            return False

    def _save_custom_rules(self):
        """Save custom rules to persistent storage."""
        import json
        from pathlib import Path

        custom_rules_file = Path.home() / ".souleyez" / "custom_chain_rules.json"

        # Note: For now, we'll save ALL rules and rely on save_rules() for state
        # In the future, we could mark rules as custom vs built-in

        try:
            custom_rules_file.parent.mkdir(parents=True, exist_ok=True)
            # Just create the file for now - actual custom rules will be tracked separately
            if not custom_rules_file.exists():
                with open(custom_rules_file, "w") as f:
                    json.dump([], f)
        except Exception as e:
            from souleyez.log_config import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to save custom rules: {e}")

    def get_rules_for_tool(self, tool: str) -> List[ChainRule]:
        """Get all rules triggered by a specific tool."""
        return [r for r in self.rules if r.trigger_tool == tool and r.enabled]

    def evaluate_chains(
        self, tool: str, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate which tools should be chained given the context.

        Args:
            tool: The tool that just completed
            context: Context data (services, findings, host info, etc.)

        Returns:
            List of commands to execute, sorted by priority
        """
        # Check if auto-chaining is globally enabled
        if not self.enabled:
            return []

        commands = []
        rules = self.get_rules_for_tool(tool)

        for rule in rules:
            if rule.matches(context):
                rule.trigger_count += 1

                # For service-based triggers, create a command per matching service
                # This handles cases like SSH on multiple ports (22, 2222, 22222)
                if "service:" in rule.trigger_condition:
                    service_name = (
                        rule.trigger_condition.split(":")[1].split()[0].lower()
                    )
                    services = context.get("services", [])

                    # Find all services matching this type
                    # Skip uncertain services (nmap marks these with "?" like "ssh?")
                    matching_services = []
                    for svc in services:
                        svc_name = svc.get("service_name", "").lower()
                        svc_port = svc.get("port")

                        # Skip uncertain services - nmap couldn't confirm the protocol
                        if svc_name.endswith("?"):
                            continue

                        # Direct match or via SERVICE_GROUPS
                        if svc_name == service_name:
                            matching_services.append(svc)
                        elif service_name in SERVICE_GROUPS:
                            if svc_port in SERVICE_GROUPS[service_name].get(
                                "ports", []
                            ):
                                matching_services.append(svc)

                    # Create a command for each matching service (different ports)
                    seen_ports = set()
                    for svc in matching_services:
                        svc_port = svc.get("port")
                        if svc_port in seen_ports:
                            continue
                        seen_ports.add(svc_port)

                        # Create context copy with this specific service's port
                        svc_context = context.copy()
                        svc_context["services"] = [
                            svc
                        ]  # Single service for port extraction

                        cmd = rule.generate_command(svc_context)
                        if cmd is None:
                            continue  # Skip if generate_command returns None (e.g., missing required placeholder)
                        try:
                            rule_idx = self.rules.index(rule) + 1
                            cmd["rule_id"] = rule_idx
                        except ValueError:
                            pass
                        commands.append(cmd)
                else:
                    # Non-service triggers: single command
                    cmd = rule.generate_command(context)
                    if cmd is None:
                        continue  # Skip if generate_command returns None (e.g., missing required placeholder)
                    # Add rule_id (1-indexed position in rules list) for job tracking
                    try:
                        rule_idx = self.rules.index(rule) + 1  # 1-indexed to match UI
                        cmd["rule_id"] = rule_idx
                    except ValueError:
                        pass  # Rule not found in list (shouldn't happen)
                    commands.append(cmd)

        # Sort by priority (highest first)
        commands.sort(key=lambda x: x.get("priority", 0), reverse=True)

        # Persist updated trigger counts if any rules matched
        if commands:
            self.save_rules()

        return commands

    def _deduplicate_web_targets(
        self,
        hosts_dict: Dict[str, list],
        parse_results: Dict[str, Any],
        job: Dict[str, Any],
    ) -> list:
        """
        Deduplicate web targets to prevent redundant scanning.

        Groups IPs serving the same website and selects representative IP for scanning.
        When theHarvester discovers multiple IPs for a domain, they often serve identical
        content. This method detects such cases and reduces scan jobs by ~87%.

        Args:
            hosts_dict: {ip: [services]} from nmap results
            parse_results: Full parse results including domain context
            job: Parent job info

        Returns:
            List of deduplicated web targets:
            [
                {
                    'representative_ip': '198.185.159.144',
                    'all_ips': ['198.185.159.144', '198.185.159.145', ...],
                    'domain': 'cybersoulsecurity.com',
                    'services': [...],  # Services from representative IP
                    'scan_https_only': bool,  # True if HTTP redirects to HTTPS
                },
                ...
            ]
        """
        from souleyez.core.web_utils import check_http_redirect
        from souleyez.engine.background import get_job
        from souleyez.log_config import get_logger

        logger = get_logger(__name__)

        # Extract domain context from parent job or parse results
        def get_domain_context():
            # Check if parent job is theHarvester
            # BUG FIX: Look up the parent job from database, not current job
            # CRITICAL FIX: Use 'parent_id' not 'parent_job_id' (see background.py line 181)
            parent_job_id = job.get("parent_id")

            # ADD DEBUG LOGGING
            logger.debug(
                f"[WEB-DEDUP] Current job: id={job.get('id')}, tool={job.get('tool')}, parent_id={parent_job_id}"
            )

            if parent_job_id:
                parent_job = get_job(parent_job_id)

                # ADD DEBUG LOGGING
                if parent_job:
                    logger.debug(
                        f"[WEB-DEDUP] Parent job found: id={parent_job.get('id')}, tool={parent_job.get('tool')}, target={parent_job.get('target')}"
                    )
                else:
                    logger.warning(
                        f"[WEB-DEDUP] Parent job #{parent_job_id} not found in job queue"
                    )

                if parent_job:
                    parent_tool = parent_job.get("tool", "").lower()

                    # FIX: Check for theHarvester (case-insensitive via .lower() above)
                    if parent_tool == "theharvester":
                        domain = parent_job.get("target", "")
                        if (
                            domain
                            and not domain.replace(".", "")
                            .replace("-", "")
                            .replace("_", "")
                            .replace("/", "")
                            .isdigit()
                        ):
                            logger.info(
                                f"[WEB-DEDUP] Found parent theHarvester job (#{parent_job_id}) for domain: {domain}"
                            )
                            return domain
                        else:
                            logger.debug(
                                f"[WEB-DEDUP] Parent theHarvester target '{domain}' looks like IP, not domain"
                            )
            else:
                logger.debug("[WEB-DEDUP] No parent_id in current job")

            # Check parse results for domains
            domains = parse_results.get("domains", [])
            if domains:
                if isinstance(domains, list) and len(domains) > 0:
                    if isinstance(domains[0], dict):
                        return domains[0].get("domain")
                    elif isinstance(domains[0], str):
                        return domains[0]

            # Check subdomains
            subdomains = parse_results.get("subdomains", [])
            if subdomains and isinstance(subdomains, list) and len(subdomains) > 0:
                if isinstance(subdomains[0], dict):
                    return subdomains[0].get("subdomain")
                elif isinstance(subdomains[0], str):
                    # Extract base domain from subdomain
                    parts = subdomains[0].split(".")
                    if len(parts) >= 2:
                        return ".".join(parts[-2:])

            return None

        domain_context = get_domain_context()

        # If no domain context, return all IPs as separate targets (fallback behavior)
        if not domain_context:
            logger.debug(
                "[WEB-DEDUP] No domain context found, falling back to per-IP scanning"
            )
            return [
                {
                    "representative_ip": ip,
                    "all_ips": [ip],
                    "domain": None,
                    "services": services,
                    "scan_https_only": False,
                }
                for ip, services in hosts_dict.items()
            ]

        # Group IPs by domain and extract web services
        web_ips = []
        for ip, services in hosts_dict.items():
            # Filter for web services (http/https and common web ports)
            web_services = [
                s
                for s in services
                if (
                    s.get("service_name", "").lower()
                    in ["http", "https", "http-proxy", "ssl/http"]
                    or s.get("port") in [80, 443, 8080, 8000, 8443, 3000, 5000]
                )
            ]

            if web_services:
                web_ips.append({"ip": ip, "services": web_services})

        if not web_ips:
            logger.debug("[WEB-DEDUP] No web services found in nmap results")
            return []

        # Since all IPs came from same domain scan, group them together
        logger.info(
            f"[WEB-DEDUP] Found {len(web_ips)} IPs with web services for domain '{domain_context}'"
        )

        # Select first IP as representative
        representative = web_ips[0]
        representative_ip = representative["ip"]
        all_ips = [item["ip"] for item in web_ips]

        logger.info(
            f"[WEB-DEDUP] Selected {representative_ip} as representative for {len(all_ips)} IPs"
        )

        # Check HTTP redirect behavior to avoid duplicate HTTP+HTTPS scans
        has_http = any(
            s.get("port") == 80
            or (
                s.get("port") in [8080, 8000, 3000, 5000]
                and s.get("service_name", "").lower() == "http"
            )
            for s in representative["services"]
        )
        has_https = any(
            s.get("port") == 443
            or (
                s.get("port") in [8443]
                or s.get("service_name", "").lower() in ["https", "ssl/http"]
            )
            for s in representative["services"]
        )

        scan_https_only = False
        filtered_services = representative["services"]

        if has_http and has_https:
            logger.info(
                f"[WEB-DEDUP] Checking if HTTP→HTTPS redirect exists for {representative_ip}"
            )

            # Get the actual HTTP port (might not be 80)
            http_port = None
            for s in representative["services"]:
                if s.get("service_name", "").lower() == "http" or s.get("port") == 80:
                    http_port = s.get("port", 80)
                    break

            if http_port:
                redirect_info = check_http_redirect(
                    representative_ip, port=http_port, timeout=3
                )

                if redirect_info.get("error"):
                    logger.warning(
                        f"[WEB-DEDUP] Redirect check failed: {redirect_info['error']}, scanning both HTTP and HTTPS"
                    )
                elif redirect_info.get("redirects_to_https"):
                    logger.info(
                        f"[WEB-DEDUP] HTTP→HTTPS redirect confirmed, will scan HTTPS only"
                    )
                    scan_https_only = True
                    # Filter out HTTP services, keep only HTTPS
                    filtered_services = [
                        s
                        for s in representative["services"]
                        if not (
                            s.get("service_name", "").lower() == "http"
                            and s.get("port") in [80, 8080, 8000, 3000, 5000]
                        )
                    ]
                else:
                    logger.info(
                        f"[WEB-DEDUP] No HTTP→HTTPS redirect detected, scanning both protocols"
                    )

        web_target = {
            "representative_ip": representative_ip,
            "all_ips": all_ips,
            "domain": domain_context,
            "services": filtered_services,
            "scan_https_only": scan_https_only,
        }

        logger.info(
            f"[WEB-DEDUP] Created deduplicated target: {representative_ip} (covers {len(all_ips)} IPs)"
        )

        return [web_target]

    def auto_chain(
        self, job: Dict[str, Any], parse_results: Dict[str, Any]
    ) -> List[int]:
        """
        Automatically chain tools based on job results.

        Args:
            job: Completed job dict
            parse_results: Results from parsing (hosts, services, findings, etc.)

        Returns:
            List of new job IDs that were created
        """
        # Local import to avoid shadowing issues with urlparse
        # (Python treats urlparse as local if ANY branch imports it locally)
        from urllib.parse import urlparse

        tool = job.get("tool", "").lower()
        target = job.get("target", "")

        from souleyez.log_config import get_logger

        logger = get_logger(__name__)
        logger.info(f"auto_chain called for tool={tool}, target={target}")

        if not target:
            return []

        engagement_id = job.get("engagement_id")
        job_ids = []

        # Mark LFI scans so downstream rules can skip SQLMap/etc
        source_rule_id = job.get("rule_id")
        is_lfi_scan = source_rule_id == -4  # FFUF LFI fuzz scan
        parse_results["is_lfi_scan"] = is_lfi_scan
        parse_results["source_rule_id"] = source_rule_id

        # For scans that discover multiple hosts (like nmap), we need to chain per-host
        # Group services by host IP
        services = parse_results.get("services", [])

        hosts_dict = {}

        # IPs to skip - placeholders that shouldn't be used as scan targets
        invalid_ips = {
            "0.0.0.0",
            "127.0.0.1",
            "::1",
            "::",
        }  # nosec B104 - not binding, filtering invalid IPs

        for service in services:
            host_ip = service.get("ip", "") or service.get("host", "")
            # Skip invalid/placeholder IPs
            if host_ip and host_ip not in invalid_ips:
                if host_ip not in hosts_dict:
                    hosts_dict[host_ip] = []
                hosts_dict[host_ip].append(service)

        # If we have per-host services, create separate chain contexts for each host
        logger.info(
            f"auto_chain: hosts_dict has {len(hosts_dict)} entries, services has {len(services)} entries"
        )
        if hosts_dict:
            # === Web Target Deduplication for nmap ===
            # When nmap discovers multiple IPs (e.g., from theHarvester), deduplicate web scanning
            # to avoid redundant nuclei/gobuster jobs on identical websites
            if tool == "nmap":
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                # Get deduplicated web targets
                web_targets = self._deduplicate_web_targets(
                    hosts_dict, parse_results, job
                )

                # Separate web services from non-web services for each IP
                web_service_names = ["http", "https", "http-proxy", "ssl/http"]
                web_ports = [80, 443, 8080, 8000, 8443, 3000, 5000]

                # Track which IPs are included in web deduplication
                web_dedup_ips = set()
                for web_target in web_targets:
                    web_dedup_ips.update(web_target["all_ips"])

                # Process deduplicated web targets
                for web_target in web_targets:
                    representative_ip = web_target["representative_ip"]
                    all_ips = web_target["all_ips"]

                    context = {
                        "target": representative_ip,
                        "tool": tool,
                        "services": web_target["services"],
                        "findings": parse_results.get("findings", []),
                        "hosts": [representative_ip],
                        "writable_shares": parse_results.get("writable_shares", []),
                        "paths_with_params": parse_results.get("paths_with_params", []),
                        "domains": parse_results.get("domains", []),
                        "subdomains": parse_results.get("subdomains", []),
                        # NEW: Add deduplication metadata
                        "associated_ips": all_ips,
                        "representative_ip": representative_ip,
                        "domain_context": web_target.get("domain"),
                    }

                    # Enrich context with OS/device classification
                    os_device = classify_os_device(
                        parse_results.get("os_info", ""), web_target["services"]
                    )
                    context["os_family"] = os_device["os_family"]
                    context["device_type"] = os_device["device_type"]
                    context["vendor"] = os_device["vendor"]

                    # Enrich context with domain from database if not in parse results
                    if not context["domains"] and engagement_id:
                        try:
                            from souleyez.storage.hosts import HostManager

                            hm = HostManager()
                            host = hm.get_host_by_ip(engagement_id, representative_ip)
                            if host and host.get("domain"):
                                context["domains"] = [
                                    {"domain": host["domain"], "ip": representative_ip}
                                ]
                        except Exception as e:
                            pass

                    # Evaluate and enqueue web scanning chains
                    commands = self.evaluate_chains(tool, context)

                    # Add AI recommendations (if enabled and in auto mode)
                    ai_commands = self.get_ai_recommendations(
                        tool=tool,
                        target=representative_ip,
                        parse_results=parse_results,
                        static_commands=commands,
                        engagement_id=engagement_id,
                    )
                    commands.extend(ai_commands)

                    # Collect ALL HTTP/HTTPS ports from services
                    http_ports = []  # List of (port, is_https) tuples
                    for svc in web_target.get("services", []):
                        svc_name = svc.get("service_name", "").lower()
                        svc_port = svc.get("port")
                        if svc_name in ["https", "ssl/http"] or svc_port in [443, 8443]:
                            http_ports.append((svc_port, True))
                        elif svc_name in ["http", "http-proxy"] or svc_port in [
                            80,
                            8080,
                            8000,
                            3000,
                            5000,
                            8888,
                        ]:
                            http_ports.append((svc_port, False))

                    # Remove duplicates while preserving order
                    seen_ports = set()
                    unique_http_ports = []
                    for port_tuple in http_ports:
                        if port_tuple[0] not in seen_ports:
                            seen_ports.add(port_tuple[0])
                            unique_http_ports.append(port_tuple)

                    # Expand http_fingerprint commands for ALL HTTP ports
                    expanded_commands = []
                    for cmd in commands:
                        if (
                            cmd.get("tool") == "http_fingerprint"
                            and len(unique_http_ports) > 1
                        ):
                            # Create separate http_fingerprint job for EACH HTTP port
                            for http_port, is_https in unique_http_ports:
                                cmd_copy = cmd.copy()
                                scheme = "https" if is_https else "http"
                                if (scheme == "http" and http_port != 80) or (
                                    scheme == "https" and http_port != 443
                                ):
                                    cmd_copy["target"] = (
                                        f"{scheme}://{representative_ip}:{http_port}"
                                    )
                                else:
                                    cmd_copy["target"] = (
                                        f"{scheme}://{representative_ip}"
                                    )
                                expanded_commands.append(cmd_copy)
                        elif cmd.get("tool") == "http_fingerprint":
                            # Single HTTP port - use it directly
                            if unique_http_ports:
                                http_port, is_https = unique_http_ports[0]
                                scheme = "https" if is_https else "http"
                                if (scheme == "http" and http_port != 80) or (
                                    scheme == "https" and http_port != 443
                                ):
                                    cmd["target"] = (
                                        f"{scheme}://{representative_ip}:{http_port}"
                                    )
                                else:
                                    cmd["target"] = f"{scheme}://{representative_ip}"
                            else:
                                cmd["target"] = f"http://{representative_ip}"
                            expanded_commands.append(cmd)
                        else:
                            cmd["target"] = representative_ip
                            expanded_commands.append(cmd)

                    # Replace commands with expanded list
                    commands = expanded_commands

                    # Enrich commands with deduplication metadata
                    for cmd in commands:
                        if "metadata" not in cmd:
                            cmd["metadata"] = {}
                        cmd["metadata"]["associated_ips"] = all_ips
                        cmd["metadata"]["representative_ip"] = representative_ip
                        if web_target.get("domain"):
                            cmd["metadata"]["domain_context"] = web_target["domain"]

                    job_ids.extend(
                        self._enqueue_commands(
                            commands,
                            tool,
                            engagement_id,
                            representative_ip,
                            parent_job_id=job.get("id"),
                        )
                    )

                    logger.info(
                        f"[WEB-DEDUP] Enqueued {len(commands)} web scan jobs for {representative_ip} (covers {len(all_ips)} IPs)"
                    )

                # Process non-web services for ALL IPs (not deduplicated)
                for host_ip, host_services in hosts_dict.items():
                    # Filter out web services - only process non-web services
                    non_web_services = [
                        s
                        for s in host_services
                        if not (
                            s.get("service_name", "").lower() in web_service_names
                            or s.get("port") in web_ports
                        )
                    ]

                    if non_web_services:
                        context = {
                            "target": host_ip,
                            "tool": tool,
                            "services": non_web_services,
                            "findings": parse_results.get("findings", []),
                            "hosts": [host_ip],
                            "writable_shares": parse_results.get("writable_shares", []),
                            "paths_with_params": parse_results.get(
                                "paths_with_params", []
                            ),
                            "domains": parse_results.get("domains", []),
                            "subdomains": parse_results.get("subdomains", []),
                        }

                        # Enrich context with OS/device classification
                        os_device = classify_os_device(
                            parse_results.get("os_info", ""), non_web_services
                        )
                        context["os_family"] = os_device["os_family"]
                        context["device_type"] = os_device["device_type"]
                        context["vendor"] = os_device["vendor"]

                        # Enrich context with domain from database
                        if not context["domains"] and engagement_id:
                            try:
                                from souleyez.storage.hosts import HostManager

                                hm = HostManager()
                                host = hm.get_host_by_ip(engagement_id, host_ip)
                                if host and host.get("domain"):
                                    context["domains"] = [
                                        {"domain": host["domain"], "ip": host_ip}
                                    ]
                            except Exception as e:
                                pass

                        # Evaluate and enqueue non-web chains (SMB, SSH, RDP, etc.)
                        commands = self.evaluate_chains(tool, context)

                        # Add AI recommendations for non-web services (if enabled)
                        ai_commands = self.get_ai_recommendations(
                            tool=tool,
                            target=host_ip,
                            parse_results=parse_results,
                            static_commands=commands,
                            engagement_id=engagement_id,
                        )
                        commands.extend(ai_commands)

                        for cmd in commands:
                            cmd["target"] = host_ip
                        job_ids.extend(
                            self._enqueue_commands(
                                commands,
                                tool,
                                engagement_id,
                                host_ip,
                                parent_job_id=job.get("id"),
                            )
                        )

                return job_ids

            elif tool == "http_fingerprint":
                # http_fingerprint: pass full URL info to context so target_format can work
                # The job target is already a full URL like http://192.168.1.157:8080
                original_target = job.get("target", "")

                # Smart protocol detection: Use effective_url if fingerprint upgraded the protocol
                # This handles cases where nmap reports HTTP but server is actually HTTPS
                effective_url = parse_results.get("effective_url") or original_target
                protocol_detection = parse_results.get("protocol_detection")

                if (
                    protocol_detection in ("upgraded", "fallback")
                    and effective_url != original_target
                ):
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)
                    logger.info(
                        f"Protocol detection: using {effective_url} (was {original_target})"
                    )

                # Extract host IP and port from effective URL for context
                from urllib.parse import urlparse as parse_url

                parsed_url = parse_url(effective_url)
                host_ip = parsed_url.hostname or target
                port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)

                context = {
                    "target": host_ip,  # IP for rules that need it
                    "target_url": effective_url,  # Full URL for rules with target_format=URL (uses effective!)
                    "original_url": original_target,  # Keep original for reference
                    "tool": tool,
                    "services": parse_results.get("services", []),
                    "findings": parse_results.get("findings", []),
                    "hosts": [host_ip],
                    "port": port,
                    "scheme": parsed_url.scheme or "http",
                    "domains": parse_results.get("domains", []),
                    "protocol_detection": protocol_detection,
                    "http_fingerprint": {
                        "managed_hosting": parse_results.get("managed_hosting"),
                        "waf": parse_results.get("waf", []),
                        "cdn": parse_results.get("cdn", []),
                        "effective_url": effective_url,
                    },
                }

                # Evaluate chains - target_format in rules handles URL vs IP
                commands = self.evaluate_chains(tool, context)

                job_ids.extend(
                    self._enqueue_commands(
                        commands,
                        tool,
                        engagement_id,
                        host_ip,
                        parent_job_id=job.get("id"),
                    )
                )

                # === Process robots.txt/sitemap.xml discovered paths ===
                # These are fetched early in recon so we can trigger follow-up scans
                # even if gobuster's wordlist doesn't include these paths
                robots_paths = parse_results.get("robots_paths", [])
                sitemap_paths = parse_results.get("sitemap_paths", [])

                if robots_paths or sitemap_paths:
                    from souleyez.engine.background import enqueue_job
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)

                    all_discovered_paths = robots_paths + sitemap_paths
                    logger.info(
                        f"http_fingerprint found {len(robots_paths)} robots.txt paths, {len(sitemap_paths)} sitemap paths"
                    )

                    # Trigger gobuster on discovered directories (paths ending with /)
                    # and on paths that look like directories (no extension)
                    dirs_to_scan = []
                    for path_url in all_discovered_paths[:20]:  # Limit to 20 paths
                        parsed_path = parse_url(path_url)
                        path_part = parsed_path.path or "/"

                        # Check if it looks like a directory (ends with / or no extension)
                        is_dir = (
                            path_part.endswith("/")
                            or "." not in path_part.split("/")[-1]
                        )
                        if is_dir and path_url not in dirs_to_scan:
                            dirs_to_scan.append(path_url)

                    if dirs_to_scan:
                        logger.info(
                            f"Triggering gobuster on {len(dirs_to_scan)} discovered directories"
                        )
                        for dir_url in dirs_to_scan[:10]:  # Limit to 10 directories
                            try:
                                enqueue_job(
                                    tool="gobuster",
                                    target=dir_url,
                                    args=[
                                        "dir",
                                        "-u",
                                        dir_url,
                                        "-w",
                                        "data/wordlists/web_dirs_common.txt",
                                        "-x",
                                        "php,html,txt,js,json",
                                        "-k",
                                        "--no-error",
                                        "-t",
                                        "5",
                                        "--delay",
                                        "20ms",
                                    ],
                                    label="http_fingerprint",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by http_fingerprint: Discovered in robots.txt/sitemap (from job #{job.get('id')})",
                                )
                                job_ids.append(
                                    -1
                                )  # Placeholder, actual ID assigned by enqueue
                            except Exception as e:
                                logger.warning(
                                    f"Failed to enqueue gobuster for {dir_url}: {e}"
                                )

                    # === Download discovered wordlists ===
                    # Files like .dic, .txt with suggestive names could be wordlists
                    # Download and store them for brute-forcing
                    wordlist_extensions = [".dic", ".lst", ".wordlist"]
                    wordlist_keywords = [
                        "password",
                        "pass",
                        "user",
                        "wordlist",
                        "dict",
                        "rockyou",
                        "fsocity",
                    ]

                    for path_url in all_discovered_paths:
                        parsed_path = parse_url(path_url)
                        filename = parsed_path.path.split("/")[-1].lower()

                        # Check if it looks like a wordlist
                        is_wordlist = any(
                            filename.endswith(ext) for ext in wordlist_extensions
                        ) or any(kw in filename for kw in wordlist_keywords)

                        if is_wordlist:
                            logger.info(f"Discovered potential wordlist: {path_url}")
                            try:
                                import os as os_module
                                import ssl
                                import urllib.request

                                # Create discovered wordlists directory
                                wordlist_dir = os_module.path.join(
                                    os_module.path.expanduser("~"),
                                    ".souleyez",
                                    "data",
                                    "wordlists",
                                    "discovered",
                                )
                                os_module.makedirs(wordlist_dir, exist_ok=True)

                                # Download the wordlist
                                ctx = ssl.create_default_context()
                                ctx.check_hostname = False
                                ctx.verify_mode = ssl.CERT_NONE

                                req = urllib.request.Request(
                                    path_url,
                                    headers={
                                        "User-Agent": "Mozilla/5.0 (compatible; SoulEyez/1.0)"
                                    },
                                )

                                # Use engagement ID in filename to track source
                                safe_filename = (
                                    f"eng{engagement_id}_{filename.replace('/', '_')}"
                                )
                                local_path = os_module.path.join(
                                    wordlist_dir, safe_filename
                                )

                                with urllib.request.urlopen(
                                    req, timeout=30, context=ctx
                                ) as response:
                                    if response.getcode() == 200:
                                        content = response.read()

                                        # Basic validation - should have multiple lines
                                        if len(content) > 100 and b"\n" in content:
                                            with open(local_path, "wb") as f:
                                                f.write(content)

                                            # Deduplicate the wordlist
                                            try:
                                                with open(
                                                    local_path,
                                                    "r",
                                                    encoding="utf-8",
                                                    errors="replace",
                                                ) as f:
                                                    lines = f.readlines()
                                                unique_lines = list(
                                                    dict.fromkeys(
                                                        line.strip()
                                                        for line in lines
                                                        if line.strip()
                                                    )
                                                )
                                                with open(
                                                    local_path, "w", encoding="utf-8"
                                                ) as f:
                                                    f.write("\n".join(unique_lines))
                                                logger.info(
                                                    f"Downloaded wordlist: {local_path} ({len(unique_lines)} unique entries)"
                                                )
                                            except Exception:
                                                logger.info(
                                                    f"Downloaded wordlist: {local_path} (raw, not deduplicated)"
                                                )

                            except Exception as e:
                                logger.warning(
                                    f"Failed to download wordlist {path_url}: {e}"
                                )

                # === Process CMS detection - trigger appropriate scanner ===
                cms_detected = parse_results.get("cms_detected")
                if cms_detected:
                    from souleyez.engine.background import enqueue_job
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)

                    cms_name = cms_detected.get("name", "").lower()
                    cms_confidence = cms_detected.get("confidence", "low")
                    logger.info(
                        f"http_fingerprint detected CMS: {cms_detected.get('name')} ({cms_confidence} confidence)"
                    )

                    # Only trigger CMS scanners with high confidence detection
                    # Medium/low confidence often means false positives (e.g., SPAs returning
                    # non-404 for /wp-admin/ paths). Require 2+ paths matched for high confidence.
                    if cms_confidence != "high":
                        logger.info(
                            f"Skipping CMS scanner - {cms_confidence} confidence is insufficient (need 'high')"
                        )
                    elif "wordpress" in cms_name:
                        try:
                            enqueue_job(
                                tool="wpscan",
                                target=effective_url,
                                args=[
                                    "--url",
                                    effective_url,
                                    "--enumerate",
                                    "u,vp,vt,dbe",
                                    "--plugins-detection",
                                    "mixed",
                                    "--random-user-agent",
                                ],
                                label="http_fingerprint",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered: WordPress detected by http_fingerprint (job #{job.get('id')})",
                            )
                            logger.info(
                                f"Triggered wpscan for WordPress at {effective_url}"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to enqueue wpscan: {e}")

                    elif "joomla" in cms_name:
                        try:
                            enqueue_job(
                                tool="joomscan",
                                target=effective_url,
                                args=["-u", effective_url],
                                label="http_fingerprint",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered: Joomla detected by http_fingerprint (job #{job.get('id')})",
                            )
                            logger.info(
                                f"Triggered joomscan for Joomla at {effective_url}"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to enqueue joomscan: {e}")

                    elif "drupal" in cms_name:
                        try:
                            enqueue_job(
                                tool="droopescan",
                                target=effective_url,
                                args=["scan", "drupal", "-u", effective_url],
                                label="http_fingerprint",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered: Drupal detected by http_fingerprint (job #{job.get('id')})",
                            )
                            logger.info(
                                f"Triggered droopescan for Drupal at {effective_url}"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to enqueue droopescan: {e}")

                # === Process admin panel detection ===
                admin_panels = parse_results.get("admin_panels", [])
                if admin_panels:
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)
                    logger.info(
                        f"http_fingerprint found {len(admin_panels)} admin panels"
                    )

                    # Check for phpMyAdmin specifically - high-value target
                    for panel in admin_panels:
                        if "phpmyadmin" in panel.get("name", "").lower():
                            logger.info(
                                f"phpMyAdmin found at {panel.get('url')} - potential SQLi target"
                            )

                # === Process API endpoint detection ===
                api_endpoints = parse_results.get("api_endpoints", [])
                if api_endpoints:
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)
                    logger.info(
                        f"http_fingerprint found {len(api_endpoints)} API endpoints"
                    )

                    # Log GraphQL endpoints specifically - they often have introspection enabled
                    for api in api_endpoints:
                        if "graphql" in api.get("type", "").lower():
                            logger.info(
                                f"GraphQL endpoint found at {api.get('url')} - check for introspection"
                            )

            else:
                # Non-nmap, non-http_fingerprint tools: use original per-host processing
                for host_ip, host_services in hosts_dict.items():
                    context = {
                        "target": host_ip,
                        "tool": tool,
                        "services": host_services,
                        "findings": parse_results.get("findings", []),
                        "hosts": [host_ip],
                        "writable_shares": parse_results.get("writable_shares", []),
                        "paths_with_params": parse_results.get("paths_with_params", []),
                        "domains": parse_results.get("domains", []),
                        "subdomains": parse_results.get("subdomains", []),
                    }

                    # Enrich context with OS/device classification
                    os_device = classify_os_device(
                        parse_results.get("os_info", ""), host_services
                    )
                    context["os_family"] = os_device["os_family"]
                    context["device_type"] = os_device["device_type"]
                    context["vendor"] = os_device["vendor"]

                    # Enrich context with domain from database if not in parse results
                    if not context["domains"] and engagement_id:
                        try:
                            from souleyez.storage.hosts import HostManager

                            hm = HostManager()
                            host = hm.get_host_by_ip(engagement_id, host_ip)
                            if host and host.get("domain"):
                                context["domains"] = [
                                    {"domain": host["domain"], "ip": host_ip}
                                ]
                        except Exception as e:
                            pass

                    # Evaluate and enqueue for this specific host
                    commands = self.evaluate_chains(tool, context)

                    # Add AI recommendations (if enabled and in auto mode)
                    ai_commands = self.get_ai_recommendations(
                        tool=tool,
                        target=host_ip,
                        parse_results=parse_results,
                        static_commands=commands,
                        engagement_id=engagement_id,
                    )
                    commands.extend(ai_commands)

                    for cmd in commands:
                        cmd["target"] = host_ip
                    job_ids.extend(
                        self._enqueue_commands(
                            commands,
                            tool,
                            engagement_id,
                            host_ip,
                            parent_job_id=job.get("id"),
                        )
                    )

                # === SearchSploit: Search for exploits based on service versions ===
                if tool in ["nmap"] and host_services:
                    import re

                    seen_searches = set()  # Deduplicate search terms

                    for service in host_services:
                        product = service.get("product") or service.get(
                            "service_product"
                        )
                        version = service.get("version") or service.get(
                            "service_version"
                        )

                        # Clean nmap metadata from version
                        if version:
                            # Remove "syn-ack ttl XX" prefix
                            for prefix in ["syn-ack ttl", "ttl", "syn-ack"]:
                                if version.startswith(prefix):
                                    parts = version.split()
                                    cleaned_parts = []
                                    skip_next = False
                                    for i, part in enumerate(parts):
                                        if skip_next:
                                            skip_next = False
                                            continue
                                        if part in ["syn-ack", "ttl"]:
                                            if part == "ttl":
                                                skip_next = True
                                            continue
                                        cleaned_parts = parts[i:]
                                        break
                                    version = (
                                        " ".join(cleaned_parts)
                                        if cleaned_parts
                                        else version
                                    )
                                    break

                        # Only search if we have both product and version
                        if product and version:
                            # Parse and clean version for better Exploit-DB matching
                            version_pattern = r"\b(v?\d+\.\d+[\w\.\-]*)\b"
                            match = re.search(version_pattern, version)

                            if match:
                                parsed_version = match.group(1)

                                # Clean version - remove distro-specific suffixes
                                clean_version = parsed_version
                                clean_version = re.sub(
                                    r"-\d*ubuntu\d+$", "", clean_version
                                )
                                clean_version = re.sub(
                                    r"-\d*debian\d+$",
                                    "",
                                    clean_version,
                                    flags=re.IGNORECASE,
                                )
                                # Remove trailing letters after patch numbers (5.0.51a -> 5.0.51)
                                clean_version = re.sub(
                                    r"([0-9]+\.[0-9]+\.[0-9]+)[a-z].*$",
                                    r"\1",
                                    clean_version,
                                )
                                # Remove patch level suffixes (4.7p1 -> 4.7)
                                clean_version = re.sub(r"p\d+.*$", "", clean_version)

                                # Extract service name from version string
                                version_start = match.start()
                                service_part = version[:version_start].strip()

                                if service_part:
                                    search_term = f"{service_part} {clean_version}"
                                else:
                                    search_term = f"{product} {clean_version}"
                            else:
                                # No version pattern found, use as-is
                                search_term = f"{product} {version}"

                            # Deduplicate: Skip if we've already queued this search
                            if search_term not in seen_searches:
                                seen_searches.add(search_term)
                                commands.append(
                                    {
                                        "tool": "searchsploit",
                                        "target": search_term,
                                        "args": ["--json"],
                                        "reason": f"Auto-triggered by {tool}: Service detected - {search_term}",
                                    }
                                )

                    # Enqueue searchsploit jobs
                    searchsploit_cmds = [
                        c for c in commands if c.get("tool") == "searchsploit"
                    ]
                    if searchsploit_cmds:
                        job_ids.extend(
                            self._enqueue_commands(
                                searchsploit_cmds,
                                tool,
                                engagement_id,
                                host_ip,
                                parent_job_id=job.get("id"),
                            )
                        )
        else:
            # No per-host services, use original target (e.g., for OSINT tools)
            logger.info(
                f"auto_chain: entering else branch (no hosts_dict) for tool={tool}"
            )

            # === Special handling for SQLMap progressive exploitation ===
            if tool == "sqlmap":
                databases = parse_results.get("databases", [])
                injectable_url = parse_results.get("injectable_url", target)
                sql_injection_confirmed = parse_results.get(
                    "sql_injection_confirmed", False
                )

                # Check if this job was already in enumeration phase (avoid loops)
                job_args = job.get("args", [])
                is_dbs_phase = "--dbs" in job_args
                is_tables_phase = "--tables" in job_args or "-D" in job_args
                is_dump_phase = "--dump" in job_args

                # Get POST data - either from parse_results or from job args (if passed from previous stage)
                post_data = parse_results.get("injectable_post_data") or ""
                if not post_data:
                    # Check if --data was passed in job args
                    for arg in job_args:
                        if arg.startswith("--data="):
                            post_data = arg.split("=", 1)[1]
                            break

                # Get tables from parse results
                tables = parse_results.get("tables", {})

                # === Phase 3: Hybrid Column Enumeration → Auto-dump ===
                if is_tables_phase and not is_dump_phase and tables and len(tables) > 0:
                    # Just finished --tables phase, use hybrid approach
                    from souleyez.intelligence.sensitive_tables import (
                        is_sensitive_table_name,
                        is_system_database,
                        is_system_table,
                        prioritize_tables,
                    )
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)

                    # Filter out system databases and tables
                    filtered_tables = {}
                    skipped_tables = 0

                    for db_name, table_list in tables.items():
                        # Skip system databases entirely
                        if is_system_database(db_name):
                            skipped_tables += len(table_list)
                            continue

                        # Filter out system tables
                        app_tables = [t for t in table_list if not is_system_table(t)]
                        if app_tables:
                            filtered_tables[db_name] = app_tables

                        skipped_tables += len(table_list) - len(app_tables)

                    if skipped_tables > 0:
                        logger.info(
                            f"SQLMap: Skipped {skipped_tables} system/metadata tables"
                        )

                    if not filtered_tables:
                        logger.info(
                            "SQLMap: No application tables found after filtering"
                        )
                        return job_ids

                    # Split tables into known-sensitive vs needs-column-enum
                    sensitive_tables_dict = {}  # Dump immediately
                    unknown_tables_dict = {}  # Enumerate columns first

                    for db_name, table_list in filtered_tables.items():
                        for table_name in table_list:
                            if is_sensitive_table_name(table_name):
                                sensitive_tables_dict.setdefault(db_name, []).append(
                                    table_name
                                )
                            else:
                                unknown_tables_dict.setdefault(db_name, []).append(
                                    table_name
                                )

                    # 1. Dump known-sensitive tables immediately
                    if sensitive_tables_dict:
                        columns = parse_results.get("columns", {})
                        sensitive_tables = prioritize_tables(
                            sensitive_tables_dict, columns
                        )

                        logger.info(
                            f"SQLMap: Detected {len(sensitive_tables)} known-sensitive tables "
                            f"({', '.join(t['table'] for t in sensitive_tables[:3])}...)"
                        )

                        # Create --dump jobs for each sensitive table
                        dump_jobs = []
                        for table_info in sensitive_tables:
                            db = table_info["database"]
                            table = table_info["table"]
                            category = table_info["category"]

                            dump_args = [
                                "-u",
                                injectable_url,
                                "--batch",
                                "-D",
                                db,
                                "-T",
                                table,
                                "--dump",
                                "--stop",
                                "100",
                                "--threads",
                                "1",
                            ]
                            # Add --data for POST injections
                            if post_data:
                                dump_args.insert(2, f"--data={post_data}")

                            dump_cmd = {
                                "tool": "sqlmap",
                                "target": injectable_url,
                                "args": dump_args,
                                "label": f"Auto-chained: Dumping {category} table '{db}.{table}'",
                                "reason": f"Auto-triggered by sqlmap: Dumping {category} table '{db}.{table}'",
                            }
                            dump_jobs.append(dump_cmd)

                        job_ids.extend(
                            self._enqueue_commands(
                                dump_jobs,
                                tool,
                                engagement_id,
                                injectable_url,
                                parent_job_id=job.get("id"),
                            )
                        )

                    # 2. For unknown tables, only enumerate columns for SENSITIVE tables
                    # This reduces noise and focuses on high-value targets
                    from souleyez.intelligence.sensitive_tables import (
                        is_sensitive_table,
                        is_system_table,
                    )

                    MAX_TABLES_FOR_COLUMN_ENUM = 10  # Focused on sensitive tables only
                    tables_queued = 0
                    skipped_tables = 0

                    if unknown_tables_dict:
                        # First, filter to only sensitive tables
                        sensitive_unknown = {}
                        for db_name, table_list in unknown_tables_dict.items():
                            for table_name in table_list:
                                # Skip system tables
                                if is_system_table(table_name):
                                    skipped_tables += 1
                                    continue

                                # Check if table name suggests sensitive data
                                is_sens, category, priority = is_sensitive_table(
                                    table_name
                                )
                                if is_sens and priority >= 5:
                                    if db_name not in sensitive_unknown:
                                        sensitive_unknown[db_name] = []
                                    sensitive_unknown[db_name].append(
                                        (table_name, category, priority)
                                    )
                                else:
                                    skipped_tables += 1

                        if sensitive_unknown:
                            # Sort by priority within each database
                            for db_name in sensitive_unknown:
                                sensitive_unknown[db_name].sort(
                                    key=lambda x: -x[2]
                                )  # Sort by priority desc

                            total_sensitive = sum(
                                len(tables) for tables in sensitive_unknown.values()
                            )
                            logger.info(
                                f"SQLMap: Enumerating columns for {min(total_sensitive, MAX_TABLES_FOR_COLUMN_ENUM)} "
                                f"sensitive tables (skipped {skipped_tables} non-sensitive/system tables)"
                            )

                            for db_name, table_info_list in sensitive_unknown.items():
                                for table_name, category, priority in table_info_list:
                                    if tables_queued >= MAX_TABLES_FOR_COLUMN_ENUM:
                                        break

                                    # Create context for Rule 70 (has:tables_enumerated)
                                    context = {
                                        "target": injectable_url,
                                        "tool": tool,
                                        "tables_enumerated": True,
                                        "database": db_name,
                                        "table": table_name,
                                        "post_data": post_data,  # Preserve POST data for subsequent commands
                                    }

                                    # Let Rule 70 fire and create the --columns job
                                    commands = self.evaluate_chains(tool, context)

                                    # The rule uses {database} and {table} placeholders - already replaced by evaluate_chains
                                    if commands:
                                        job_ids.extend(
                                            self._enqueue_commands(
                                                commands,
                                                tool,
                                                engagement_id,
                                                injectable_url,
                                                parent_job_id=job.get("id"),
                                            )
                                        )
                                        tables_queued += 1
                                        logger.debug(
                                            f"  -> Queued column enum for {db_name}.{table_name} ({category}, priority={priority})"
                                        )

                                if tables_queued >= MAX_TABLES_FOR_COLUMN_ENUM:
                                    break
                        else:
                            logger.info(
                                f"SQLMap: No sensitive tables found in {len(unknown_tables_dict)} databases "
                                f"(skipped {skipped_tables} non-sensitive/system tables)"
                            )

                    # Don't return early - continue to rule evaluation below if needed

                # === Phase 4: Columns enumerated → Dump if sensitive ===
                is_columns_phase = "--columns" in job_args
                if is_columns_phase and not is_dump_phase:
                    # Just finished --columns phase, check for sensitive columns
                    from souleyez.intelligence.sensitive_tables import (
                        has_sensitive_columns,
                    )
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)

                    columns = parse_results.get("columns", {})
                    if columns:
                        dump_jobs = []

                        for table_key, column_list in columns.items():
                            if has_sensitive_columns(column_list):
                                # Parse db.table from key
                                if "." in table_key:
                                    db_name, table_name = table_key.split(".", 1)
                                else:
                                    # Fallback if no database prefix
                                    db_name = None
                                    table_name = table_key

                                logger.info(
                                    f"SQLMap: Sensitive columns detected in '{table_key}' "
                                    f"(columns: {', '.join([c if isinstance(c, str) else c.get('name', '?') for c in column_list[:3]])}...)"
                                )

                                # Create dump job for this table
                                args = [
                                    "-u",
                                    injectable_url,
                                    "--batch",
                                    "--forms",
                                    "--crawl=2",
                                ]

                                if db_name:
                                    args.extend(["-D", db_name])
                                args.extend(["-T", table_name])
                                args.extend(
                                    ["--dump", "--stop", "100", "--threads", "1"]
                                )

                                dump_cmd = {
                                    "tool": "sqlmap",
                                    "target": injectable_url,
                                    "args": args,
                                    "label": f"Auto-chained: Dumping table with sensitive columns '{table_key}'",
                                    "reason": f"Auto-triggered by sqlmap: Sensitive columns found in '{table_key}'",
                                    "rule_id": -3,  # Smart chain: sqlmap → dump (sensitive columns)
                                }
                                dump_jobs.append(dump_cmd)

                        if dump_jobs:
                            job_ids.extend(
                                self._enqueue_commands(
                                    dump_jobs,
                                    tool,
                                    engagement_id,
                                    injectable_url,
                                    parent_job_id=job.get("id"),
                                )
                            )

                    # Also trigger Rule 71 (has:columns_enumerated) for tracking
                    # Rule 71 is disabled by default, but fires for "Fired" count if enabled
                    for table_key in columns.keys():
                        if "." in table_key:
                            db_name, table_name = table_key.split(".", 1)
                        else:
                            db_name = None
                            table_name = table_key

                        context = {
                            "target": injectable_url,
                            "tool": tool,
                            "columns_enumerated": True,
                            "database": db_name or "",
                            "table": table_name,
                        }
                        # Let Rule 71 fire (if enabled)
                        commands = self.evaluate_chains(tool, context)
                        if commands:
                            job_ids.extend(
                                self._enqueue_commands(
                                    commands,
                                    tool,
                                    engagement_id,
                                    injectable_url,
                                    parent_job_id=job.get("id"),
                                )
                            )

                    return job_ids

                # For --dump phase, check for credential chaining then return
                if is_dump_phase:
                    # === Chain to Hydra for credential reuse testing ===
                    from souleyez.engine.background import enqueue_job
                    from souleyez.log_config import get_logger
                    from souleyez.storage.hosts import HostManager

                    logger = get_logger(__name__)

                    # Get credentials from parse_results
                    credentials_list = parse_results.get("credentials", [])

                    # Also extract from dumped_data if credentials list is empty
                    if not credentials_list:
                        dumped_data = parse_results.get("dumped_data", {})
                        for table_key, data_info in dumped_data.items():
                            rows = data_info.get("rows", [])
                            columns = data_info.get("columns", [])
                            col_lower = [c.lower() for c in columns]
                            if "username" in col_lower and "password" in col_lower:
                                username_col = columns[col_lower.index("username")]
                                password_col = columns[col_lower.index("password")]
                                for row in rows[:20]:
                                    username = row.get(username_col, "")
                                    password = row.get(password_col, "")
                                    if (
                                        username
                                        and password
                                        and not password.startswith("$")
                                    ):
                                        credentials_list.append(
                                            {"username": username, "password": password}
                                        )
                        if credentials_list:
                            logger.info(
                                f"Extracted {len(credentials_list)} credential(s) from dumped_data for chaining"
                            )

                    if credentials_list:
                        logger.info(
                            f"sqlmap auto-chain: {len(credentials_list)} credential(s) available for reuse testing"
                        )

                        # Find target host for credential testing
                        try:
                            parsed_url = urlparse(injectable_url)
                            target_host = parsed_url.hostname or target
                        except Exception:
                            target_host = target

                        # Get host services
                        host_manager = HostManager()
                        host = host_manager.get_host_by_ip(engagement_id, target_host)
                        services = []
                        if host:
                            services = host_manager.get_host_services(host.get("id"))

                        # Create hydra jobs for credential reuse testing
                        created_jobs = 0
                        for cred in credentials_list[:5]:  # Limit to 5 credentials
                            username = cred.get("username", "")
                            password = cred.get("password", "")

                            if not username or not password:
                                continue

                            # Test SSH if available
                            ssh_svc = next(
                                (s for s in services if s.get("port") == 22), None
                            )
                            if ssh_svc:
                                hydra_job_id = enqueue_job(
                                    tool="hydra",
                                    target=target_host,
                                    args=[
                                        "ssh",
                                        "-l",
                                        username,
                                        "-p",
                                        password,
                                        "-t",
                                        "1",
                                        "-vV",
                                        "-f",
                                    ],
                                    label="sqlmap",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by sqlmap: Testing dumped credential {username} against SSH",
                                    rule_id=-8,
                                )
                                job_ids.append(hydra_job_id)
                                created_jobs += 1
                                logger.info(
                                    f"  Chained: sqlmap → hydra SSH job #{hydra_job_id} for {username}"
                                )

                            # Test FTP if available
                            ftp_svc = next(
                                (s for s in services if s.get("port") == 21), None
                            )
                            if ftp_svc:
                                hydra_job_id = enqueue_job(
                                    tool="hydra",
                                    target=target_host,
                                    args=[
                                        "ftp",
                                        "-l",
                                        username,
                                        "-p",
                                        password,
                                        "-t",
                                        "1",
                                        "-vV",
                                        "-f",
                                    ],
                                    label="sqlmap",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by sqlmap: Testing dumped credential {username} against FTP",
                                    rule_id=-8,
                                )
                                job_ids.append(hydra_job_id)
                                created_jobs += 1
                                logger.info(
                                    f"  Chained: sqlmap → hydra FTP job #{hydra_job_id} for {username}"
                                )

                        if created_jobs > 0:
                            logger.info(
                                f"sqlmap auto-chain: Created {created_jobs} Hydra job(s) for credential reuse"
                            )
                        elif not services:
                            logger.info(
                                f"sqlmap auto-chain: No services found on {target_host} for credential testing"
                            )

                    # === Chain to Hashcat for password hash cracking ===
                    # Group credentials by hash type for efficient cracking
                    hash_groups = {}
                    for cred in credentials_list:
                        cred_type = cred.get("credential_type", "password")
                        if cred_type.startswith("hash:"):
                            hash_type = cred_type.replace("hash:", "")
                            if hash_type not in hash_groups:
                                hash_groups[hash_type] = []
                            hash_groups[hash_type].append(cred)

                    if hash_groups:
                        import os
                        import tempfile

                        # Map hash types to hashcat modes
                        hashcat_modes = {
                            "md5": "0",
                            "sha1": "100",
                            "sha256": "1400",
                            "sha512": "1800",
                            "bcrypt": "3200",
                            "md5crypt": "500",
                            "sha256crypt": "7400",
                            "sha512crypt": "1800",
                        }

                        for hash_type, creds in hash_groups.items():
                            mode = hashcat_modes.get(hash_type)
                            if not mode:
                                logger.debug(
                                    f"Skipping {hash_type} hashes - no hashcat mode mapping"
                                )
                                continue

                            logger.info(
                                f"SQLMap found {len(creds)} {hash_type} hash(es), chaining to hashcat..."
                            )

                            # Write hashes to temp file (username:hash format)
                            hash_file = tempfile.NamedTemporaryFile(
                                mode="w",
                                suffix=".txt",
                                prefix=f"sqlmap_{hash_type}_",
                                delete=False,
                            )
                            for cred in creds:
                                username = cred.get("username", "unknown")
                                password = cred.get("password", "")
                                if password:
                                    hash_file.write(f"{username}:{password}\n")
                            hash_file.close()

                            # Queue hashcat job
                            hashcat_job_id = enqueue_job(
                                tool="hashcat",
                                target=hash_file.name,
                                args=[
                                    "-m",
                                    mode,
                                    "-a",
                                    "0",
                                    "--username",
                                    "data/wordlists/passwords_crack.txt",
                                ],
                                label="sqlmap",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered by sqlmap: Cracking {len(creds)} {hash_type} hash(es) from database dump",
                                rule_id=-60,  # Smart chain: sqlmap → hashcat
                                skip_scope_check=True,  # Local file cracking
                            )
                            job_ids.append(hashcat_job_id)
                            logger.info(
                                f"  Chained: sqlmap → hashcat (mode {mode}) job #{hashcat_job_id}"
                            )

                    return job_ids

                # Check if SQL injection was just confirmed (trigger --dbs or --tables)
                # But DON'T trigger if we just ran --dbs (prevent --dbs → --dbs loop)
                if sql_injection_confirmed and not databases and not is_dbs_phase:
                    # SQL injection found but databases not yet enumerated

                    # Cache all injection points for fallback
                    all_points = parse_results.get("all_injection_points", [])
                    if all_points:
                        host = urlparse(injectable_url).netloc
                        ToolChaining._injection_points_cache[host] = all_points
                        from souleyez.log_config import get_logger

                        logger = get_logger(__name__)
                        logger.info(
                            f"SQLMap: Cached {len(all_points)} injection points for {host}"
                        )

                    # Check if DBMS is SQLite - skip --dbs, go directly to --tables
                    dbms = (parse_results.get("dbms") or "").lower()
                    is_sqlite = "sqlite" in dbms

                    post_data = parse_results.get("injectable_post_data") or ""

                    if is_sqlite:
                        # SQLite doesn't support --dbs, go directly to --tables
                        from souleyez.log_config import get_logger

                        logger = get_logger(__name__)
                        logger.info(
                            "SQLMap: SQLite detected, skipping --dbs and using --tables directly"
                        )

                        # Create --tables job directly (SQLite has implicit single database)
                        tables_args = [
                            "-u",
                            injectable_url,
                            "--tables",
                            "--batch",
                            "--threads",
                            "1",
                        ]
                        if post_data:
                            tables_args.insert(2, f"--data={post_data}")

                        tables_cmd = {
                            "tool": "sqlmap",
                            "target": injectable_url,
                            "args": tables_args,
                            "label": "Auto-chain: SQLite table enumeration",
                            "reason": "SQLite detected - skipping --dbs, enumerating tables directly",
                        }
                        job_ids.extend(
                            self._enqueue_commands(
                                [tables_cmd],
                                tool,
                                engagement_id,
                                injectable_url,
                                parent_job_id=job.get("id"),
                            )
                        )
                    else:
                        # Non-SQLite: use normal --dbs chain via evaluate_chains()
                        context = {
                            "target": injectable_url,
                            "tool": tool,
                            "sql_injection_confirmed": True,
                            "databases_enumerated": False,
                            "post_data": post_data,  # For POST injections
                        }
                        commands = self.evaluate_chains(tool, context)
                        job_ids.extend(
                            self._enqueue_commands(
                                commands,
                                tool,
                                engagement_id,
                                injectable_url,
                                parent_job_id=job.get("id"),
                            )
                        )

                # Check if databases were enumerated (trigger --tables per database)
                elif databases and len(databases) > 0:
                    # Filter out system databases (zero pentest value)
                    import re

                    from souleyez.intelligence.sensitive_tables import (
                        is_system_database,
                    )

                    def is_garbage_db_name(name: str) -> bool:
                        """Detect SQLMap marker strings or broken extraction results."""
                        if not name:
                            return True
                        # SQLMap markers are typically 40-char random alphanumeric strings
                        if len(name) >= 30 and re.match(r"^[a-zA-Z0-9]+$", name):
                            # Real DB names rarely exceed 30 chars of pure alphanumeric
                            return True
                        # Skip hex-looking strings
                        if re.match(r"^0x[0-9a-fA-F]+$", name):
                            return True
                        # Skip pure numbers (SQLMap sometimes returns counts instead of names)
                        if re.match(r"^\d+$", name):
                            return True
                        # Skip very short names (1-2 chars are rarely real DBs)
                        if len(name) <= 2:
                            return True
                        return False

                    # Track what we filtered
                    garbage_dbs = [db for db in databases if is_garbage_db_name(db)]
                    system_dbs = [
                        db
                        for db in databases
                        if is_system_database(db) and not is_garbage_db_name(db)
                    ]
                    app_databases = [
                        db
                        for db in databases
                        if not is_system_database(db) and not is_garbage_db_name(db)
                    ]

                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)

                    if garbage_dbs:
                        logger.warning(
                            f"SQLMap: Filtered {len(garbage_dbs)} garbage database names "
                            f"('{', '.join(garbage_dbs[:3])}') - extraction may have failed"
                        )

                    if not app_databases:
                        if garbage_dbs:
                            # Extraction failed - try fallback to different injection point
                            host = urlparse(injectable_url).netloc
                            all_points = ToolChaining._injection_points_cache.get(
                                host, []
                            )
                            current_url = injectable_url

                            # Find next untried injection point
                            # Check job label for previously tried URLs
                            job_label = job.get("label", "")
                            tried_urls = set()
                            if "tried:" in job_label:
                                tried_part = job_label.split("tried:")[1].split(")")[0]
                                tried_urls = set(
                                    u.strip()
                                    for u in tried_part.split(",")
                                    if u.strip()
                                )
                            tried_urls.add(current_url)

                            next_point = None
                            for point in all_points:
                                if point["url"] not in tried_urls:
                                    next_point = point
                                    break

                            if next_point:
                                logger.info(
                                    f"SQLMap: Extraction failed on {current_url}, "
                                    f"trying fallback: {next_point['url']}"
                                )

                                # Create new --dbs job with alternate injection point
                                fallback_args = [
                                    "-u",
                                    next_point["url"],
                                    "--dbs",
                                    "--batch",
                                ]

                                # Add POST data if needed
                                if next_point.get("post_data"):
                                    fallback_args.insert(
                                        2, f"--data={next_point['post_data']}"
                                    )

                                fallback_cmd = {
                                    "tool": "sqlmap",
                                    "target": next_point["url"],
                                    "args": fallback_args,
                                    "label": f"sqlmap (fallback, tried:{','.join(tried_urls)})",
                                    "reason": f"Fallback --dbs after extraction failed on {current_url}",
                                }

                                # Pass all_injection_points to the fallback job
                                # so it can continue fallback chain if needed
                                job_ids.extend(
                                    self._enqueue_commands(
                                        [fallback_cmd],
                                        tool,
                                        engagement_id,
                                        next_point["url"],
                                        parent_job_id=job.get("id"),
                                    )
                                )
                                return job_ids
                            else:
                                logger.error(
                                    f"SQLMap: All {len(all_points) or 1} injection points exhausted - "
                                    f"none support data extraction"
                                )
                        else:
                            logger.info(
                                f"SQLMap: Skipped {len(databases)} system databases "
                                f"({', '.join(databases[:3])}{'...' if len(databases) > 3 else ''})"
                            )
                        return job_ids

                    # Create one --tables job PER application database (limit to first 5)
                    db_limit = min(len(app_databases), self.MAX_DATABASES_TO_ENUMERATE)

                    for db_name in app_databases[:db_limit]:
                        # Create context with this specific database
                        context = {
                            "target": injectable_url,
                            "tool": tool,
                            "databases_enumerated": True,
                            "tables_enumerated": False,
                            "database": db_name,  # Required for {database} placeholder
                            "post_data": post_data,  # Preserve POST data for subsequent commands
                        }

                        # Evaluate chains - will match the --tables rule
                        commands = self.evaluate_chains(tool, context)

                        # Replace {database} placeholder in args with actual database name
                        for cmd in commands:
                            # Replace '-D', '{database}' with '-D', 'actual_db_name'
                            if "{database}" in cmd.get("args", []):
                                cmd["args"] = [
                                    arg if arg != "{database}" else db_name
                                    for arg in cmd["args"]
                                ]

                            # Update reason to include database name
                            cmd["reason"] = (
                                f"Auto-triggered by sqlmap: Enumerating tables in database '{db_name}'"
                            )

                        # Enqueue jobs for this database
                        job_ids.extend(
                            self._enqueue_commands(
                                commands,
                                tool,
                                engagement_id,
                                injectable_url,
                                parent_job_id=job.get("id"),
                            )
                        )

                    # Log if we hit the limit or skipped system databases
                    if len(app_databases) > db_limit or len(app_databases) < len(
                        databases
                    ):
                        from souleyez.log_config import get_logger

                        logger = get_logger(__name__)

                        skipped_count = len(databases) - len(app_databases)
                        if skipped_count > 0:
                            logger.info(
                                f"SQLMap: Skipped {skipped_count} system databases, "
                                f"enumerating {min(db_limit, len(app_databases))} application databases"
                            )

                        if len(app_databases) > db_limit:
                            logger.info(
                                f"SQLMap auto-chaining limited to first {db_limit} of {len(app_databases)} application databases"
                            )

                # === Post-exploitation chain rules (is_dba, file_read, os_cmd) ===
                # Check for post-exploitation flags and fire appropriate chain rules
                is_dba = parse_results.get("is_dba", False)
                file_read_success = parse_results.get("file_read_success", False)
                os_command_success = parse_results.get("os_command_success", False)

                if is_dba or file_read_success or os_command_success:
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)

                    # Build context with post-exploitation flags using injectable_url
                    post_exploit_context = {
                        "target": injectable_url,  # Use the correct injectable URL
                        "tool": tool,
                        "is_dba": is_dba,
                        "file_read_success": file_read_success,
                        "os_command_success": os_command_success,
                        "post_data": post_data,  # Preserve POST data for subsequent commands
                    }

                    if is_dba:
                        logger.info(
                            f"SQLMap: DBA access confirmed! Evaluating post-exploitation chains..."
                        )
                    if file_read_success:
                        logger.info(
                            f"SQLMap: File read successful! Evaluating file read chains..."
                        )
                    if os_command_success:
                        logger.info(f"SQLMap: OS command execution successful!")

                    # Evaluate chain rules - this will fire rules like has:is_dba
                    commands = self.evaluate_chains(tool, post_exploit_context)
                    if commands:
                        logger.info(
                            f"SQLMap: Matched {len(commands)} post-exploitation chain rule(s)"
                        )
                        job_ids.extend(
                            self._enqueue_commands(
                                commands,
                                tool,
                                engagement_id,
                                injectable_url,
                                parent_job_id=job.get("id"),
                            )
                        )
                # === END Post-exploitation chain rules ===

                return job_ids
            # === END SQLMap special handling ===

            # === Evaluate finding-based chain rules for all tools (including gobuster) ===
            # This enables finding:api, finding:rest, etc. to trigger SQLMap/other tools
            # SKIP for theharvester only - gobuster should always evaluate finding-based rules
            # (job deduplication handles preventing duplicate jobs)
            skip_finding_based = (
                tool
                == "theharvester"  # Skip generic evaluation, use special handling at line 1933
            )

            if (
                not hosts_dict and not skip_finding_based
            ):  # Tools without per-host services (gobuster, osint, etc.)
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                context = {
                    "target": target,
                    "tool": tool,
                    "services": [],
                    "findings": parse_results.get("findings", []),
                    "hosts": [target],
                    "php_files": parse_results.get("php_files", []),
                    "asp_files": parse_results.get("asp_files", []),
                    "high_value_dirs": parse_results.get("high_value_dirs", []),
                    "paths_with_params": parse_results.get("paths_with_params", []),
                    "domains": parse_results.get("domains", []),
                    "subdomains": parse_results.get("subdomains", []),
                    "parameters_found": parse_results.get(
                        "parameters_found", []
                    ),  # ffuf → sqlmap chain
                    "paths_found": parse_results.get(
                        "paths_found", 0
                    ),  # gobuster → katana chain
                    "results_found": parse_results.get(
                        "results_found", 0
                    ),  # ffuf → katana chain
                    "is_lfi_scan": parse_results.get(
                        "is_lfi_scan", False
                    ),  # Skip SQLMap for LFI fuzz results
                }

                # Evaluate generic chain rules (findings, etc.)
                logger.info(f"Evaluating finding-based chain rules for {tool}")
                logger.info(f"  - Findings: {len(context['findings'])}")

                commands = self.evaluate_chains(tool, context)
                if commands:
                    logger.info(
                        f"  - Matched {len(commands)} finding-based chain rule(s)"
                    )
                    job_ids.extend(
                        self._enqueue_commands(
                            commands,
                            tool,
                            engagement_id,
                            target,
                            parent_job_id=job.get("id"),
                        )
                    )
                else:
                    logger.info(f"  - No finding-based chain rules matched")
            # === END finding-based chain evaluation ===

            # === Special handling for Gobuster: PHP files → crawl once, redirects + MySQL ===
            if tool == "gobuster":
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                # === Wildcard Auto-Retry Logic ===
                # If gobuster detected wildcard responses, auto-retry with --exclude-length
                if parse_results.get("wildcard_detected") and parse_results.get(
                    "exclude_length"
                ):
                    # Check if this is already a retry attempt (prevent loops)
                    is_retry = job.get("metadata", {}).get("retry_attempt", 0) > 0

                    # Check if args already contain --exclude-length (prevent double-retry)
                    args = job.get("args", [])
                    has_exclude_length = "--exclude-length" in args

                    if not is_retry and not has_exclude_length:
                        exclude_length = parse_results["exclude_length"]
                        logger.info(
                            f"🔄 Wildcard detected (Length: {exclude_length}), creating auto-retry with --exclude-length"
                        )

                        # Create retry job with original args + --exclude-length flag
                        retry_args = args.copy()
                        retry_args.extend(["--exclude-length", exclude_length])

                        # Build retry job command
                        retry_command = {
                            "tool": "gobuster",
                            "target": target,
                            "args": retry_args,
                            "reason": f"Auto-retry: gobuster (wildcard detected, excluding length {exclude_length})",
                            "metadata": {
                                "retry_attempt": 1,
                                "retry_parent_job_id": job.get("id"),
                                "wildcard_exclude_length": exclude_length,
                            },
                        }

                        # Enqueue the retry job
                        retry_job_ids = self._enqueue_commands(
                            [retry_command],
                            tool,
                            engagement_id,
                            target,
                            parent_job_id=job.get("id"),
                        )
                        if retry_job_ids:
                            job_ids.extend(retry_job_ids)
                            logger.info(
                                f"✓ Retry job created with --exclude-length {exclude_length}"
                            )

                        # Skip further processing of this failed wildcard scan
                        # Let the retry job complete and process properly
                        return job_ids
                # === END Wildcard Auto-Retry ===

                # === Host Redirect Auto-Retry Logic ===
                # If gobuster detected a host-level redirect (e.g., non-www to www), auto-retry with corrected target
                if parse_results.get("host_redirect_detected") and parse_results.get(
                    "redirect_target"
                ):
                    # Check if this is already a retry attempt (prevent loops)
                    is_retry = job.get("metadata", {}).get("redirect_retry", False)

                    if not is_retry:
                        redirect_target = parse_results["redirect_target"]
                        original_target = target
                        logger.info(
                            f"🔄 Host redirect detected ({original_target} → {redirect_target}), creating auto-retry with corrected target"
                        )

                        # Get original args and update the -u parameter with new target
                        args = job.get("args", [])
                        retry_args = []
                        for i, arg in enumerate(args):
                            if arg == "-u" and i + 1 < len(args):
                                # Next arg is the URL, replace it
                                retry_args.append(arg)
                                retry_args.append(redirect_target)
                                # Skip the next iteration since we handled it
                            elif i > 0 and args[i - 1] == "-u":
                                # This is the URL after -u, skip it (already handled)
                                continue
                            else:
                                # Replace <target> placeholder if present
                                retry_args.append(
                                    arg.replace(original_target, redirect_target)
                                    if original_target in arg
                                    else arg
                                )

                        # Build retry job command with corrected target
                        retry_command = {
                            "tool": "gobuster",
                            "target": redirect_target,
                            "args": retry_args,
                            "reason": f"Auto-retry: gobuster (host redirect detected: {original_target} → {redirect_target})",
                            "metadata": {
                                "redirect_retry": True,
                                "retry_parent_job_id": job.get("id"),
                                "original_target": original_target,
                                "redirect_target": redirect_target,
                            },
                        }

                        # Enqueue the retry job
                        retry_job_ids = self._enqueue_commands(
                            [retry_command],
                            tool,
                            engagement_id,
                            redirect_target,
                            parent_job_id=job.get("id"),
                        )
                        if retry_job_ids:
                            job_ids.extend(retry_job_ids)
                            logger.info(
                                f"✓ Retry job created with corrected target: {redirect_target}"
                            )

                        # Skip further processing of this redirect scan
                        # Let the retry job complete and process properly
                        return job_ids
                # === END Host Redirect Auto-Retry ===

                # PHP/ASP files found → trigger SQLMap intelligently
                # High-value targets get direct testing, others get base URL crawl
                php_files = parse_results.get("php_files", [])
                asp_files = parse_results.get("asp_files", [])
                high_value_dirs = parse_results.get("high_value_dirs", [])

                logger.info(f"[DEBUG] Gobuster auto-chain analysis:")
                logger.info(f"[DEBUG]   - Found {len(php_files)} PHP file(s)")
                logger.info(f"[DEBUG]   - Found {len(asp_files)} ASP file(s)")
                logger.info(
                    f"[DEBUG]   - Found {len(high_value_dirs)} high-value director(y/ies): {high_value_dirs}"
                )

                if php_files:
                    for php_url, status_code in php_files[:5]:
                        logger.info(
                            f"[DEBUG]     PHP: {php_url} (status: {status_code})"
                        )
                    if len(php_files) > 5:
                        logger.info(
                            f"[DEBUG]     ... and {len(php_files) - 5} more PHP files"
                        )

                if asp_files:
                    for asp_url, status_code in asp_files[:5]:
                        logger.info(
                            f"[DEBUG]     ASP: {asp_url} (status: {status_code})"
                        )
                    if len(asp_files) > 5:
                        logger.info(
                            f"[DEBUG]     ... and {len(asp_files) - 5} more ASP files"
                        )

                if high_value_dirs:
                    for hvd in high_value_dirs:
                        logger.info(f"[DEBUG]     HIGH-VALUE DIR: {hvd}")

                # Extract base_url for use in all auto-chain commands
                # This must be defined before php_files or high_value_dirs processing
                base_url = None
                if parse_results.get("target_url"):
                    # Best case: parser provided target_url
                    base_url = parse_results["target_url"]
                    if not base_url.endswith("/"):
                        base_url += "/"
                elif high_value_dirs:
                    # Fallback: extract from first high-value directory
                    parsed = urlparse(high_value_dirs[0])
                    base_url = f"{parsed.scheme}://{parsed.netloc}/"
                elif php_files:
                    # Fallback: extract from first PHP file
                    # php_files is now a list of tuples (url, status_code)
                    parsed = urlparse(php_files[0][0])
                    base_url = f"{parsed.scheme}://{parsed.netloc}/"
                elif asp_files:
                    # Fallback: extract from first ASP file
                    # asp_files is now a list of tuples (url, status_code)
                    parsed = urlparse(asp_files[0][0])
                    base_url = f"{parsed.scheme}://{parsed.netloc}/"
                else:
                    # Last resort: construct from original target
                    # This handles cases where target is just an IP
                    if target.startswith("http"):
                        parsed = urlparse(target)
                        base_url = f"{parsed.scheme}://{parsed.netloc}/"
                    else:
                        # Just an IP/domain, assume HTTP
                        base_url = f"http://{target}/"

                if php_files:

                    # Define high-value keywords that indicate sensitive functionality
                    high_value_keywords = [
                        "admin",
                        "login",
                        "signin",
                        "signup",
                        "register",
                        "auth",
                        "payroll",
                        "payment",
                        "checkout",
                        "account",
                        "user",
                        "profile",
                        "dashboard",
                        "panel",
                        "console",
                        "manager",
                        "config",
                        "settings",
                        "upload",
                        "edit",
                        "delete",
                        "update",
                        "modify",
                        "search",
                        "query",
                        "sql",
                        "db",
                        "database",
                        "api",
                        "rest",
                        "password",
                        "passwd",
                        "pwd",
                        "credential",
                        "token",
                        "phpmyadmin",
                        "mutillidae",
                        "dvwa",
                        "bwapp",
                        "webgoat",  # Vulnerable web apps
                        "backup",
                        "old",
                        "dev",
                        "staging",
                        "beta",  # Development artifacts
                    ]

                    # Info-disclosure files that don't accept input (exclude from sqlmap)
                    info_disclosure_keywords = [
                        "phpinfo",
                        "info.php",
                        "test.php",
                        "debug.php",
                    ]

                    # Separate high-value targets from regular files
                    high_value_targets = []
                    regular_files = []

                    for php_file_tuple in php_files:
                        # php_files is now a list of tuples (url, status_code)
                        php_url, status_code = php_file_tuple
                        filename = php_url.lower()

                        # Skip 403 responses - access denied means we can't test for SQLi
                        if status_code == 403:
                            logger.info(f"[DEBUG] Skipping 403 Forbidden: {php_url}")
                            continue

                        # Skip Apache config files (.htaccess, .htpasswd, etc.)
                        # These match 'passwd' keyword but are not dynamic endpoints
                        path_part = (
                            php_url.split("/")[-1] if "/" in php_url else php_url
                        )
                        if path_part.startswith(".ht"):
                            logger.info(
                                f"[DEBUG] Skipping Apache config file: {php_url}"
                            )
                            continue

                        # Skip info-disclosure files (no user input = no SQL injection)
                        is_info_disclosure = any(
                            keyword in filename for keyword in info_disclosure_keywords
                        )
                        if is_info_disclosure:
                            logger.info(
                                f"[DEBUG] Skipping sqlmap for info-disclosure file: {php_url}"
                            )
                            continue

                        if any(keyword in filename for keyword in high_value_keywords):
                            high_value_targets.append(php_file_tuple)
                            logger.info(
                                f"[DEBUG] Marked as high-value target: {php_url} (status: {status_code})"
                            )
                        else:
                            regular_files.append(php_file_tuple)
                            logger.info(
                                f"[DEBUG] Marked as regular PHP file: {php_url} (status: {status_code})"
                            )

                    # Report findings
                    if high_value_targets:
                        logger.info(
                            f"[DEBUG] Found {len(high_value_targets)} high-value PHP file(s) - targeting directly"
                        )
                        for target_url, status_code in high_value_targets[
                            :5
                        ]:  # Show first 5
                            logger.info(
                                f"[DEBUG]   → {target_url} (status: {status_code})"
                            )
                        if len(high_value_targets) > 5:
                            logger.info(
                                f"[DEBUG]   ... and {len(high_value_targets) - 5} more"
                            )

                    # Show user feedback about what will be crawled
                    # Note: base_url is already extracted above at the start of gobuster handling
                    if regular_files:
                        logger.info(
                            f"[DEBUG] Found {len(regular_files)} other PHP file(s) - will crawl base URL: {base_url}"
                        )

                    # === 1. Direct targeting for high-value PHP files ===
                    # Create individual sqlmap jobs for each high-value target
                    if high_value_targets:
                        from souleyez.engine.background import enqueue_job

                        # Deduplicate: Skip PHP files that are under high-value directories
                        # (the directory crawl will discover them anyway)
                        deduplicated_targets = []
                        skipped_targets = []

                        for target_tuple in high_value_targets:
                            target_url, status_code = target_tuple
                            # Check if this file is under any high-value directory
                            is_under_dir = False
                            for dir_url in high_value_dirs:
                                # Ensure dir_url ends with / for proper prefix matching
                                normalized_dir = (
                                    dir_url if dir_url.endswith("/") else dir_url + "/"
                                )
                                if target_url.startswith(normalized_dir):
                                    is_under_dir = True
                                    skipped_targets.append(target_url)
                                    break

                            if not is_under_dir:
                                deduplicated_targets.append(target_tuple)

                        # Further deduplicate: Only scan ONE high-value target per base URL
                        # (since --crawl=2 will discover other files on same domain anyway)
                        base_url_targets = {}  # Maps base_url -> list of target tuples

                        for target_tuple in deduplicated_targets:
                            target_url, status_code = target_tuple
                            parsed = urlparse(target_url)
                            base = f"{parsed.scheme}://{parsed.netloc}/"
                            if base not in base_url_targets:
                                base_url_targets[base] = []
                            base_url_targets[base].append(target_tuple)

                        # Priority order for choosing best target per domain
                        # Higher priority = appears earlier in the list
                        priority_keywords = [
                            "login",
                            "admin",
                            "auth",
                            "signin",
                            "signup",
                            "register",
                            "payroll",
                            "payment",
                            "checkout",
                            "account",
                            "dashboard",
                            "manager",
                            "console",
                            "panel",
                            "upload",
                            "edit",
                        ]

                        final_targets = []
                        skipped_same_domain = []

                        for base, targets in base_url_targets.items():
                            if len(targets) == 1:
                                final_targets.append(targets[0])
                            else:
                                # Multiple targets on same domain - pick the best one
                                best_target = None
                                best_priority = 999

                                for target_tuple in targets:
                                    target_url, status_code = target_tuple
                                    filename = target_url.lower()
                                    # Find highest priority keyword in filename
                                    for i, keyword in enumerate(priority_keywords):
                                        if keyword in filename:
                                            if i < best_priority:
                                                best_priority = i
                                                best_target = target_tuple
                                            break

                                # If no priority keyword found, prioritize by status code
                                if best_target is None:
                                    # Status code priority: 200 > 401 > 403
                                    status_priority = {200: 1, 401: 2, 403: 3}
                                    best_target = min(
                                        targets,
                                        key=lambda t: status_priority.get(t[1], 999),
                                    )

                                final_targets.append(best_target)
                                # Mark others as skipped
                                for target_tuple in targets:
                                    if target_tuple != best_target:
                                        target_url, _ = target_tuple
                                        skipped_same_domain.append(target_url)

                        # Log same-domain deduplication
                        if skipped_same_domain:
                            logger.info(
                                f"Skipped {len(skipped_same_domain)} file(s) on same domain (crawl will discover them):"
                            )
                            for skipped in skipped_same_domain[:3]:
                                logger.info(f"  → {skipped}")
                            if len(skipped_same_domain) > 3:
                                logger.info(
                                    f"  ... and {len(skipped_same_domain) - 3} more"
                                )

                        # Log deduplication results
                        if skipped_targets:
                            logger.info(
                                f"Skipped {len(skipped_targets)} PHP file(s) already covered by directory crawls:"
                            )
                            for skipped in skipped_targets[:3]:
                                logger.info(f"  → {skipped}")
                            if len(skipped_targets) > 3:
                                logger.info(
                                    f"  ... and {len(skipped_targets) - 3} more"
                                )

                        logger.info(
                            f"Creating {len(final_targets)} direct sqlmap job(s) for high-value PHP files"
                        )

                        # Build command dictionaries for _enqueue_commands (which has duplicate detection)
                        sqlmap_commands = []
                        for target_tuple in final_targets:
                            target_url, status_code = target_tuple
                            sqlmap_commands.append(
                                {
                                    "tool": "sqlmap",
                                    "target": target_url,
                                    "args": [
                                        "--batch",
                                        "--crawl=2",
                                        "--risk=2",
                                        "--level=3",
                                        "--forms",
                                    ],
                                    "reason": f"high-value PHP file detected (status: {status_code})",
                                    "rule_id": -12,  # Smart chain: gobuster → sqlmap (high-value PHP)
                                }
                            )
                            logger.info(
                                f"  ✓ Queuing direct sqlmap test: {target_url} (status: {status_code})"
                            )

                        # Use _enqueue_commands which handles duplicate detection
                        job_ids.extend(
                            self._enqueue_commands(
                                sqlmap_commands,
                                tool,
                                engagement_id,
                                base_url,
                                parent_job_id=job.get("id"),
                            )
                        )

                # === 2. Crawl high-value directories (mutillidae, dvwa, etc.) ===
                # Check if gobuster found any high-value vulnerable app directories
                # NOTE: high_value_dirs already extracted above, no need to get again
                if high_value_dirs:
                    logger.info(
                        f"Processing {len(high_value_dirs)} high-value directory/directories via chain rules"
                    )

                    # Use chain rules to determine which tools to run for each directory
                    for dir_url in high_value_dirs:
                        category_info = self._categorize_high_value_directory(dir_url)
                        category = category_info["category"]

                        logger.info(f"  Directory: {dir_url}")
                        logger.info(f"  Category: {category}")

                        # Build context with category for chain rules to match
                        dir_context = {
                            "target": dir_url,
                            "directory_category": category,
                            "directory_url": dir_url,
                        }

                        # Evaluate chain rules - rules with category:X conditions will match
                        commands = self.evaluate_chains(tool, dir_context)

                        if commands:
                            for cmd in commands:
                                logger.info(
                                    f"    → {cmd['tool']} (rule #{cmd.get('rule_id', '?')})"
                                )

                            # Enqueue commands (already have rule_id set by evaluate_chains)
                            job_ids.extend(
                                self._enqueue_commands(
                                    commands,
                                    tool,
                                    engagement_id,
                                    base_url,
                                    parent_job_id=job.get("id"),
                                )
                            )

                # === 3. Base URL crawl for regular files ===
                # Only crawl if there are regular files AND no high-value directories AND no high-value targets
                # (Prefer crawling from specific vulnerable apps or high-value files over base URL)
                elif php_files and not high_value_dirs:
                    # Check if there are regular (non-high-value) PHP files
                    # php_files is a list of tuples (url, status_code)
                    regular_files = [
                        f
                        for f in php_files
                        if not any(kw in f[0].lower() for kw in high_value_keywords)
                    ]
                    if regular_files:
                        logger.info(
                            f"No high-value directories or targets found, creating base URL crawl for {len(regular_files)} regular file(s)"
                        )
                        logger.info(f"  Base URL: {base_url}")

                        # Create context for SQLMap crawl (only once for the base URL)
                        crawl_context = {
                            "target": base_url,
                            "tool": tool,
                            "php_files": [base_url],  # Single item to trigger rule
                        }

                        # Evaluate chains - will match our crawl rule
                        crawl_commands = self.evaluate_chains(tool, crawl_context)

                        # Filter to only SQLMap commands
                        sqlmap_only = [
                            cmd
                            for cmd in crawl_commands
                            if cmd["tool"] == "sqlmap"
                            and "--crawl" in " ".join(cmd.get("args", []))
                        ]

                        logger.info(
                            f"  Enqueueing {len(sqlmap_only)} base URL crawl job(s)"
                        )
                        # Enqueue single crawl job for base URL
                        job_ids.extend(
                            self._enqueue_commands(
                                sqlmap_only,
                                tool,
                                engagement_id,
                                base_url,
                                parent_job_id=job.get("id"),
                            )
                        )

                # === ASP/ASPX file handling (same logic as PHP) ===
                # Windows/IIS environments use ASP files which are equally vulnerable to SQLi
                if (
                    asp_files and not php_files
                ):  # Only if no PHP files (avoid duplicate base URL crawl)
                    # Use same high-value keywords as PHP
                    high_value_keywords = [
                        "admin",
                        "login",
                        "signin",
                        "signup",
                        "register",
                        "auth",
                        "payroll",
                        "payment",
                        "checkout",
                        "account",
                        "user",
                        "profile",
                        "dashboard",
                        "panel",
                        "console",
                        "manager",
                        "config",
                        "settings",
                        "upload",
                        "edit",
                        "delete",
                        "update",
                        "modify",
                        "search",
                        "query",
                        "sql",
                        "db",
                        "database",
                        "api",
                        "rest",
                        "password",
                        "passwd",
                        "pwd",
                        "credential",
                        "token",
                        "backup",
                        "old",
                        "dev",
                        "staging",
                        "beta",
                    ]

                    # Separate high-value ASP targets from regular files
                    high_value_asp_targets = []
                    regular_asp_files = []

                    for asp_file_tuple in asp_files:
                        asp_url, status_code = asp_file_tuple
                        filename = asp_url.lower()

                        # Skip 403 responses
                        if status_code == 403:
                            logger.info(
                                f"[DEBUG] Skipping 403 Forbidden ASP: {asp_url}"
                            )
                            continue

                        if any(keyword in filename for keyword in high_value_keywords):
                            high_value_asp_targets.append(asp_file_tuple)
                            logger.info(
                                f"[DEBUG] Marked as high-value ASP target: {asp_url} (status: {status_code})"
                            )
                        else:
                            regular_asp_files.append(asp_file_tuple)

                    # Create SQLMap jobs for high-value ASP targets
                    if high_value_asp_targets:
                        from souleyez.engine.background import enqueue_job

                        logger.info(
                            f"[DEBUG] Creating SQLMap jobs for {len(high_value_asp_targets)} high-value ASP file(s)"
                        )

                        for target_tuple in high_value_asp_targets[
                            :3
                        ]:  # Limit to 3 targets per scan
                            target_url, status_code = target_tuple
                            logger.info(f"  → Targeting: {target_url}")

                            job_id = enqueue_job(
                                tool="sqlmap",
                                target=target_url,
                                args=[
                                    "--batch",
                                    "--forms",
                                    "--crawl=1",
                                    "--risk=2",
                                    "--level=3",
                                    "--threads=5",
                                ],
                                label="gobuster",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered by gobuster: High-value ASP file detected",
                            )
                            if job_id:
                                job_ids.append(job_id)

                    # Base URL crawl for remaining ASP files
                    elif regular_asp_files:
                        logger.info(
                            f"Creating base URL crawl for {len(regular_asp_files)} regular ASP file(s)"
                        )
                        logger.info(f"  Base URL: {base_url}")

                        # Create context for SQLMap crawl
                        crawl_context = {
                            "target": base_url,
                            "tool": tool,
                            "asp_files": [base_url],  # Single item to trigger rule
                        }

                        # Evaluate chains
                        crawl_commands = self.evaluate_chains(tool, crawl_context)

                        # Filter to only SQLMap crawl commands
                        sqlmap_only = [
                            cmd
                            for cmd in crawl_commands
                            if cmd["tool"] == "sqlmap"
                            and "--crawl" in " ".join(cmd.get("args", []))
                        ]

                        if sqlmap_only:
                            logger.info(
                                f"  Enqueueing {len(sqlmap_only)} ASP base URL crawl job(s)"
                            )
                            job_ids.extend(
                                self._enqueue_commands(
                                    sqlmap_only,
                                    tool,
                                    engagement_id,
                                    base_url,
                                    parent_job_id=job.get("id"),
                                )
                            )

            # === Special handling for Gobuster: redirects + MySQL presence ===
            if tool == "gobuster":
                # Query database for redirects found by this job
                # parse_results doesn't include the actual paths, only summary stats
                redirects_count = parse_results.get("redirects_found", 0)
                redirects = []  # Initialize to avoid UnboundLocalError

                if redirects_count > 0:
                    # Query database for actual redirect URLs
                    from souleyez.storage.database import get_db

                    db = get_db()
                    conn = db.get_connection()

                    # Get redirects from web_paths table
                    redirects_data = conn.execute(
                        """
                        SELECT url, redirect, status_code
                        FROM web_paths
                        WHERE redirect IS NOT NULL
                        AND url LIKE ?
                        ORDER BY id DESC
                        LIMIT 10
                    """,
                        (f"%{target}%",),
                    ).fetchall()

                    conn.close()

                    redirects = [
                        {"url": r["url"], "redirect": r["redirect"]}
                        for r in redirects_data
                    ]

                if redirects:
                    # Check if host has MySQL (port 3306 or service='mysql')
                    from souleyez.storage.hosts import HostManager

                    hm = HostManager()

                    # Get host from target URL (use target_url from parse_results if available)
                    actual_target = parse_results.get("target_url", target)
                    parsed_target = urlparse(actual_target)
                    host_ip = (
                        parsed_target.netloc.split(":")[0]
                        if parsed_target.netloc
                        else actual_target.split(":")[0]
                    )

                    # Get all services for this engagement
                    services = hm.get_all_services(engagement_id)

                    # Check if MySQL exists on this host
                    mysql_found = any(
                        (
                            svc.get("ip_address") == host_ip
                            or svc.get("hostname") == host_ip
                        )
                        and (
                            svc.get("port") == 3306
                            or svc.get("service_name", "").lower() == "mysql"
                        )
                        for svc in services
                    )

                    if mysql_found:
                        print(
                            f"  🔍 MySQL detected on {host_ip} - analyzing {len(redirects)} redirect(s)"
                        )

                        # Deduplicate redirects by destination IP
                        # Only test ONE redirect per unique destination IP
                        seen_ips = set()
                        unique_redirects = {}
                        skipped_count = 0

                        # Known interesting directories worth testing even without parameters
                        interesting_dirs = [
                            "admin",
                            "phpmyadmin",
                            "mysql",
                            "database",
                            "db",
                            "api",
                            "auth",
                            "login",
                            "portal",
                            "dashboard",
                            "dav",
                            "webdav",
                            "twiki",
                            "wiki",
                            "cms",
                            "manager",
                            "console",
                            "control",
                            "panel",
                            "backup",
                            "upload",
                            "uploads",
                            "config",
                            "conf",
                            "settings",
                        ]

                        for redirect_path in redirects[:10]:
                            redirect_url = redirect_path.get("redirect")

                            if not redirect_url:
                                continue

                            # Smart filtering: Skip boring directory redirects
                            # But allow interesting directories even without parameters
                            if redirect_url.endswith("/") and "?" not in redirect_url:
                                # Check if this is an interesting directory
                                is_interesting = any(
                                    pattern in redirect_url.lower()
                                    for pattern in interesting_dirs
                                )
                                if not is_interesting:
                                    continue  # Skip boring directories only

                            # Parse redirect URL to extract destination IP
                            parsed_redirect = urlparse(redirect_url)
                            redirect_host = (
                                parsed_redirect.netloc.split(":")[0]
                                if parsed_redirect.netloc
                                else None
                            )

                            # If we can't determine the host, skip it
                            if not redirect_host:
                                continue

                            # Check if we've already queued a test for this destination IP
                            if redirect_host in seen_ips:
                                skipped_count += 1
                                continue

                            # Mark this IP as seen and add to unique redirects
                            seen_ips.add(redirect_host)
                            unique_redirects[redirect_url] = redirect_path

                        if skipped_count > 0:
                            print(
                                f"  ⏭️  Skipped {skipped_count} duplicate redirect(s) (same destination IP)"
                            )

                        if not unique_redirects:
                            print(f"  ℹ️  No suitable redirects to test")
                            return job_ids

                        print(
                            f"  🎯 Testing {len(unique_redirects)} unique redirect destination(s)"
                        )

                        # Trigger SQLMap on unique redirect URLs
                        for redirect_url, redirect_path in unique_redirects.items():
                            # Check if redirect has query parameters (high chance of SQLi)
                            has_params = "?" in redirect_url

                            # Only test redirects with parameters (like theHarvester does)
                            if not has_params:
                                continue

                            # Create context for SQLMap
                            sqlmap_context = {
                                "target": redirect_url,
                                "tool": tool,
                                "redirects_with_mysql": True,
                            }

                            # Evaluate chains - will match our new rule
                            sqlmap_commands = self.evaluate_chains(tool, sqlmap_context)

                            # Filter to only SQLMap commands
                            sqlmap_only = [
                                cmd
                                for cmd in sqlmap_commands
                                if cmd["tool"] == "sqlmap"
                            ]

                            # Update reason to be more specific
                            for cmd in sqlmap_only:
                                cmd["reason"] = (
                                    f"Auto-triggered by gobuster: Redirect with parameters found on host "
                                    f"with MySQL (port 3306)"
                                )

                            # Enqueue SQLMap jobs for this redirect
                            job_ids.extend(
                                self._enqueue_commands(
                                    sqlmap_only, tool, engagement_id, redirect_url
                                )
                            )

                # Don't return early - continue to general gobuster handling for ffuf rules
            # === END Gobuster special handling ===

            # === Special handling for Gobuster wildcard retry ===
            if tool == "gobuster" and parse_results.get("wildcard_detected"):
                # Gobuster failed due to wildcard response, auto-retry with --exclude-length
                from souleyez.engine.background import enqueue_job
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                # Check if this is already a retry (prevent loops)
                retry_attempt = job.get("metadata", {}).get("retry_attempt", 0)
                if retry_attempt >= 1:
                    logger.info(f"Gobuster wildcard: Already attempted retry, skipping")
                    return job_ids

                # Check if --exclude-length already in args (shouldn't happen, but safety check)
                job_args = job.get("args", [])
                if "--exclude-length" in job_args:
                    logger.info(
                        f"Gobuster wildcard: --exclude-length already present, skipping retry"
                    )
                    return job_ids

                # Get the exclude length
                exclude_length = parse_results.get("exclude_length")
                if not exclude_length:
                    logger.warning(
                        f"Gobuster wildcard detected but no exclude_length found"
                    )
                    return job_ids

                # Create retry job with --exclude-length
                retry_args = job_args + ["--exclude-length", exclude_length]

                logger.info(
                    f"Gobuster wildcard: Auto-retrying with --exclude-length {exclude_length}"
                )

                retry_job_id = enqueue_job(
                    tool="gobuster",
                    target=target,
                    args=retry_args,
                    label="gobuster",
                    engagement_id=engagement_id,
                    parent_id=job.get("id"),
                    reason=f"Auto-triggered by gobuster: Wildcard response detected, retrying with --exclude-length {exclude_length}",
                    metadata={"retry_attempt": 1, "retry_parent_job_id": job.get("id")},
                )

                job_ids.append(retry_job_id)
                logger.info(f"Created gobuster retry job #{retry_job_id}")

                return job_ids
            # === END Gobuster wildcard retry ===

            # === Special handling for Gobuster host redirect retry ===
            if tool == "gobuster" and parse_results.get("host_redirect_detected"):
                # Gobuster detected host-level redirect, auto-retry with corrected target
                from souleyez.engine.background import enqueue_job
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                # Check if this is already a redirect retry (prevent loops)
                is_redirect_retry = job.get("metadata", {}).get("redirect_retry", False)
                if is_redirect_retry:
                    logger.info(
                        f"Gobuster host redirect: Already attempted redirect retry, skipping"
                    )
                    return job_ids

                # Get the redirect target
                redirect_target = parse_results.get("redirect_target")
                if not redirect_target:
                    logger.warning(
                        f"Gobuster host redirect detected but no redirect_target found"
                    )
                    return job_ids

                original_target = target
                logger.info(
                    f"Gobuster host redirect: Auto-retrying with corrected target {redirect_target}"
                )

                # Get original args and update the -u parameter with new target
                job_args = job.get("args", [])
                retry_args = []
                for i, arg in enumerate(job_args):
                    if arg == "-u" and i + 1 < len(job_args):
                        retry_args.append(arg)
                        retry_args.append(redirect_target)
                    elif i > 0 and job_args[i - 1] == "-u":
                        continue
                    else:
                        retry_args.append(
                            arg.replace(original_target, redirect_target)
                            if original_target in arg
                            else arg
                        )

                retry_job_id = enqueue_job(
                    tool="gobuster",
                    target=redirect_target,
                    args=retry_args,
                    label="gobuster",
                    engagement_id=engagement_id,
                    parent_id=job.get("id"),
                    reason=f"Auto-triggered by gobuster: Host redirect detected ({original_target} → {redirect_target})",
                    metadata={
                        "redirect_retry": True,
                        "retry_parent_job_id": job.get("id"),
                        "original_target": original_target,
                    },
                    rule_id=-4,  # Smart chain: gobuster redirect retry
                )

                job_ids.append(retry_job_id)
                logger.info(f"Created gobuster redirect retry job #{retry_job_id}")

                return job_ids
            # === END Gobuster host redirect retry ===

            # === Special handling for Gobuster: extracted paths from robots.txt/sitemap.xml ===
            if tool == "gobuster" and parse_results.get("extracted_paths"):
                from souleyez.engine.background import enqueue_job
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                extracted_paths = parse_results.get("extracted_paths", [])
                extraction_sources = parse_results.get("extraction_sources", [])

                if extracted_paths:
                    source_info = ", ".join(
                        [s.get("file", "unknown") for s in extraction_sources]
                    )
                    logger.info(
                        f"Gobuster extracted paths: Found {len(extracted_paths)} paths from {source_info}"
                    )

                    # Limit to prevent explosion of jobs
                    max_extracted_scans = 10
                    created_jobs = 0

                    for extracted_url in extracted_paths[:max_extracted_scans]:
                        try:
                            # Skip if this path was already scanned by gobuster
                            # (prevents scanning the root again if it was in robots.txt)
                            original_target = job.get("target", "")
                            if extracted_url.rstrip("/") == original_target.rstrip("/"):
                                continue

                            # Create gobuster job for extracted path
                            scan_job_id = enqueue_job(
                                tool="gobuster",
                                target=extracted_url,
                                args=[
                                    "dir",
                                    "-u",
                                    extracted_url,
                                    "-w",
                                    "data/wordlists/web_dirs_common.txt",
                                    "-x",
                                    "php,html,txt,js,json",
                                    "-k",
                                    "--no-error",
                                    "-t",
                                    "5",
                                    "--delay",
                                    "20ms",
                                ],
                                label="gobuster",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered by gobuster: Extracted from {source_info} (from job #{job.get('id')})",
                                metadata={
                                    "extracted_path": True,
                                    "source": source_info,
                                },
                            )
                            job_ids.append(scan_job_id)
                            created_jobs += 1
                            logger.info(
                                f"Created gobuster job #{scan_job_id} for extracted path: {extracted_url}"
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to create job for extracted path {extracted_url}: {e}"
                            )
                            continue

                    if created_jobs > 0:
                        logger.info(
                            f"Gobuster extracted paths: Created {created_jobs} new scan jobs"
                        )

                # Don't return early - continue to other chain handling
            # === END Gobuster extracted paths ===

            # === Special handling for ffuf: Create SQLMap jobs and recursive ffuf scans ===
            if tool == "ffuf":
                from souleyez.engine.background import enqueue_job
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                # Skip SQLMap chaining for LFI fuzz scans (rule_id=-4)
                # LFI scans find file inclusion payloads, not SQLi targets
                job_rule_id = job.get("rule_id")
                is_lfi_scan = job_rule_id == -4
                if is_lfi_scan:
                    logger.info(
                        "ffuf auto-chain: Skipping SQLMap for LFI fuzz scan results"
                    )

                parameters_found = parse_results.get("parameters_found", [])
                if parameters_found:
                    logger.info(
                        f"ffuf auto-chain: Found {len(parameters_found)} endpoint(s)"
                    )

                    # Status codes that indicate testable endpoints (for SQLMap)
                    testable_statuses = {200, 201, 204, 301, 302, 401, 403}
                    # Status 500 often indicates a directory/API that needs parameters
                    # These are candidates for recursive fuzzing
                    recursive_statuses = {500}

                    created_sqlmap_jobs = 0
                    created_ffuf_jobs = 0
                    max_sqlmap_jobs = 5  # Limit to prevent overwhelming the target
                    max_recursive_ffuf = 3  # Limit recursive depth/breadth

                    # Get current recursion depth from job metadata
                    current_depth = job.get("metadata", {}).get("ffuf_depth", 0)
                    max_depth = (
                        2  # Don't go deeper than 2 levels (e.g., /rest/products/search)
                    )

                    for endpoint in parameters_found:
                        # Handle both dict and string formats
                        if isinstance(endpoint, dict):
                            endpoint_url = endpoint.get("url", "")
                            # Parser uses 'status_code', normalize both formats
                            status_code = endpoint.get("status_code") or endpoint.get(
                                "status", 0
                            )
                        else:
                            endpoint_url = str(endpoint)
                            status_code = 200  # Assume testable if no status

                        if not endpoint_url:
                            continue

                        # === Filter out non-injectable files ===
                        path_lower = endpoint_url.lower()
                        filename = (
                            path_lower.split("/")[-1]
                            if "/" in path_lower
                            else path_lower
                        )

                        # Skip Apache/nginx config files
                        if filename.startswith(".ht") or filename.startswith(".nginx"):
                            logger.debug(f"Skipping config file: {endpoint_url}")
                            continue

                        # Skip static files that can't have SQL injection
                        static_extensions = (
                            ".html",
                            ".htm",
                            ".txt",
                            ".css",
                            ".js",
                            ".json",
                            ".xml",
                            ".svg",
                            ".png",
                            ".jpg",
                            ".jpeg",
                            ".gif",
                            ".ico",
                            ".woff",
                            ".woff2",
                            ".ttf",
                            ".eot",
                            ".pdf",
                            ".doc",
                            ".docx",
                            ".xls",
                            ".xlsx",
                            ".bak",
                            ".old",
                            ".backup",
                            ".swp",
                            ".orig",
                            ".map",
                            ".md",
                            ".rst",
                            ".log",
                            ".zip",
                            ".gz",
                            ".tar",
                            ".rar",
                            ".7z",  # Archives
                        )
                        if any(filename.endswith(ext) for ext in static_extensions):
                            logger.debug(f"Skipping static file: {endpoint_url}")
                            continue

                        # Skip double extensions (fuzzing artifacts like index.php.php)
                        if filename.count(".") >= 2:
                            # Check for suspicious double extensions
                            double_ext_patterns = [".php.", ".asp.", ".jsp.", ".html."]
                            if any(pat in filename for pat in double_ext_patterns):
                                logger.debug(
                                    f"Skipping double extension artifact: {endpoint_url}"
                                )
                                continue

                        # Skip phpinfo and similar info-disclosure files (not injectable)
                        info_disclosure_files = [
                            "phpinfo.php",
                            "info.php",
                            "test.php",
                            "debug.php",
                            "pi.php",
                        ]
                        if filename in info_disclosure_files:
                            logger.debug(
                                f"Skipping info-disclosure file: {endpoint_url}"
                            )
                            continue

                        # Skip known application index pages (phpMyAdmin, etc.)
                        known_app_paths = [
                            "/phpmyadmin/",
                            "/pma/",
                            "/adminer/",
                            "/wordpress/wp-login",
                        ]
                        if any(app_path in path_lower for app_path in known_app_paths):
                            # Only skip generic index pages, not login forms
                            if (
                                filename in ["index.php", "index.html"]
                                and "?" not in endpoint_url
                            ):
                                logger.debug(
                                    f"Skipping known app index: {endpoint_url}"
                                )
                                continue

                        # Skip URLs with file extensions mid-path (e.g., /config.php/index.php)
                        # These are garbage results from fuzzing files as if they were directories
                        file_extensions_midpath = (
                            ".php",
                            ".asp",
                            ".aspx",
                            ".jsp",
                            ".do",
                            ".action",
                            ".html",
                            ".htm",
                            ".cgi",
                            ".pl",
                            ".py",
                        )
                        is_garbage_url = False
                        try:
                            from urllib.parse import urlparse as url_parse_check

                            parsed_check = url_parse_check(endpoint_url)
                            path_segments = [
                                s for s in parsed_check.path.split("/") if s
                            ]
                            # Check if any segment EXCEPT the last one has a file extension
                            if len(path_segments) > 1:
                                for segment in path_segments[:-1]:
                                    if any(
                                        segment.lower().endswith(ext)
                                        for ext in file_extensions_midpath
                                    ):
                                        logger.debug(
                                            f"Skipping garbage URL (file ext mid-path): {endpoint_url}"
                                        )
                                        is_garbage_url = True
                                        break
                        except Exception:
                            pass
                        if is_garbage_url:
                            continue

                        # === SQLMap for testable endpoints ===
                        # Skip SQLMap if this was an LFI fuzz scan - results are LFI payloads, not SQLi targets

                        # Use helper function to filter non-injectable URLs
                        if not should_test_url_for_sqli(endpoint_url):
                            continue

                        if (
                            not is_lfi_scan
                            and status_code in testable_statuses
                            and created_sqlmap_jobs < max_sqlmap_jobs
                        ):
                            # For API endpoints without parameters, add test parameters
                            # This is critical for REST APIs that don't have HTML forms
                            test_url = endpoint_url
                            if "?" not in endpoint_url:
                                path_lower = endpoint_url.lower()
                                # Search/query endpoints need a query parameter
                                if any(
                                    kw in path_lower
                                    for kw in ["/search", "/find", "/query", "/filter"]
                                ):
                                    test_url = endpoint_url + "?q=test"
                                # ID-based endpoints need an id parameter
                                elif any(
                                    kw in path_lower
                                    for kw in ["/user", "/product", "/item", "/order"]
                                ):
                                    test_url = endpoint_url + "?id=1"

                            sqlmap_args = [
                                "-u",
                                test_url,
                                "--batch",
                                "--level=2",
                                "--risk=2",
                                "--forms",
                                "--crawl=2",
                                "--threads=5",
                            ]

                            sqlmap_job_id = enqueue_job(
                                tool="sqlmap",
                                target=endpoint_url,
                                args=sqlmap_args,
                                label="ffuf",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered by ffuf: Database/dynamic endpoint detected ({status_code} response)",
                                rule_id=-1,  # Smart chain: ffuf → sqlmap (dynamic endpoint)
                            )

                            job_ids.append(sqlmap_job_id)
                            created_sqlmap_jobs += 1
                            logger.info(
                                f"  SQLMap job #{sqlmap_job_id} for {endpoint_url}"
                            )

                        # === Recursive ffuf for 500 directories ===
                        elif (
                            status_code in recursive_statuses
                            and current_depth < max_depth
                            and created_ffuf_jobs < max_recursive_ffuf
                        ):
                            # 500 often means "this is a valid path but needs sub-path/params"
                            # Fuzz one level deeper: /rest/products → /rest/products/FUZZ
                            fuzz_url = endpoint_url.rstrip("/") + "/FUZZ"

                            ffuf_args = [
                                "-u",
                                fuzz_url,
                                "-w",
                                "data/wordlists/api_endpoints.txt",
                                "-t",
                                "5",
                                "-p",
                                "0.02",
                                "-mc",
                                "200,201,301,302,401,403,500",  # Include 500 for further recursion
                            ]

                            ffuf_job_id = enqueue_job(
                                tool="ffuf",
                                target=fuzz_url,
                                args=ffuf_args,
                                label="ffuf",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered by ffuf: {status_code} response suggests deeper path, fuzzing recursively",
                                metadata={"ffuf_depth": current_depth + 1},
                                rule_id=-2,  # Smart chain: ffuf → recursive ffuf (500 response)
                            )

                            job_ids.append(ffuf_job_id)
                            created_ffuf_jobs += 1
                            logger.info(
                                f"  ffuf recursive job #{ffuf_job_id} for {endpoint_url} (depth {current_depth + 1})"
                            )

                    if created_sqlmap_jobs > 0:
                        logger.info(
                            f"ffuf auto-chain: Created {created_sqlmap_jobs} SQLMap job(s)"
                        )
                    if created_ffuf_jobs > 0:
                        logger.info(
                            f"ffuf auto-chain: Created {created_ffuf_jobs} recursive ffuf job(s)"
                        )

                # === LFI Extract chain: when ffuf LFI scan finds PHP filter URLs ===
                if is_lfi_scan and parameters_found:
                    # Look for successful PHP filter wrapper URLs
                    php_filter_urls = []
                    for endpoint in parameters_found:
                        if isinstance(endpoint, dict):
                            endpoint_url = endpoint.get("url", "")
                            status_code = endpoint.get("status_code") or endpoint.get(
                                "status", 0
                            )
                        else:
                            endpoint_url = str(endpoint)
                            status_code = 200

                        # Only extract from successful PHP filter URLs
                        if (
                            status_code == 200
                            and "php://filter" in endpoint_url
                            and "base64-encode" in endpoint_url
                        ):
                            php_filter_urls.append(endpoint_url)

                    if php_filter_urls:
                        logger.info(
                            f"ffuf auto-chain: Found {len(php_filter_urls)} PHP filter URL(s) for credential extraction"
                        )

                        # Prioritize config files
                        high_value_files = [
                            "config",
                            "database",
                            "settings",
                            "db",
                            "connect",
                            "wp-config",
                            ".env",
                        ]
                        prioritized = []
                        other = []
                        for url in php_filter_urls:
                            url_lower = url.lower()
                            if any(hv in url_lower for hv in high_value_files):
                                prioritized.append(url)
                            else:
                                other.append(url)
                        ordered_urls = prioritized + other

                        # Create lfi_extract job with the best URL(s)
                        # Use the first config file URL as target, pass others via args
                        target_url = ordered_urls[0]
                        lfi_extract_args = ["--max-urls", "10"]

                        # Write URLs to temp file for batch processing
                        import os as os_module
                        import tempfile

                        tmp_dir = os_module.path.join(
                            os_module.path.expanduser("~"), ".souleyez", "tmp"
                        )
                        os_module.makedirs(
                            tmp_dir, exist_ok=True
                        )  # Create directory BEFORE temp file
                        urls_file = tempfile.NamedTemporaryFile(
                            mode="w", suffix="_lfi_urls.txt", delete=False, dir=tmp_dir
                        )
                        for url in ordered_urls[:10]:  # Limit to 10 URLs
                            urls_file.write(url + "\n")
                        urls_file.close()

                        lfi_extract_args.extend(["--urls-file", urls_file.name])

                        lfi_job_id = enqueue_job(
                            tool="lfi_extract",
                            target=target_url,
                            args=lfi_extract_args,
                            label="ffuf",
                            engagement_id=engagement_id,
                            parent_id=job.get("id"),
                            reason=f"Auto-triggered by ffuf: {len(php_filter_urls)} PHP filter URL(s) found for credential extraction",
                            rule_id=-5,  # Smart chain: ffuf LFI → lfi_extract
                        )

                        job_ids.append(lfi_job_id)
                        logger.info(
                            f"ffuf auto-chain: Created LFI extract job #{lfi_job_id}"
                        )
            # === END ffuf special handling ===

            # === Special handling for lfi_extract: Chain Hydra for credential spraying ===
            if tool == "lfi_extract":
                from souleyez.engine.background import enqueue_job
                from souleyez.log_config import get_logger
                from souleyez.storage.hosts import HostManager

                logger = get_logger(__name__)

                credentials_found = parse_results.get("credentials", [])
                if credentials_found:
                    logger.info(
                        f"lfi_extract auto-chain: Found {len(credentials_found)} credential(s)"
                    )

                    # Get host_id from job or find by target
                    host_id = job.get("host_id")
                    target = job.get("target", "")

                    if not host_id and target:
                        # Try to find host by extracting hostname from target URL
                        try:
                            parsed_url = urlparse(target)
                            target_host = parsed_url.hostname or target
                            host_manager = HostManager()
                            host = host_manager.get_host_by_ip(
                                engagement_id, target_host
                            )
                            if host:
                                host_id = host.get("id")
                        except Exception:
                            pass

                    # Get services running on the host
                    services_to_test = []
                    if host_id:
                        try:
                            host_manager = HostManager()
                            services = host_manager.get_host_services(host_id)

                            # Map service ports to Hydra service names
                            service_map = {
                                22: "ssh",
                                21: "ftp",
                                3306: "mysql",
                                5432: "postgres",
                                1433: "mssql",
                                445: "smb",
                                139: "smb",
                                3389: "rdp",
                            }

                            for svc in services:
                                port = svc.get("port")
                                if port in service_map:
                                    services_to_test.append(
                                        {
                                            "port": port,
                                            "service": service_map[port],
                                            "state": svc.get("state", "open"),
                                        }
                                    )

                            logger.info(
                                f"  Found {len(services_to_test)} testable service(s) on host"
                            )
                        except Exception as e:
                            logger.warning(f"  Could not get host services: {e}")

                    # Create Hydra jobs for each credential + matching service
                    created_hydra_jobs = 0
                    max_hydra_jobs = 3  # Limit to avoid overwhelming

                    for cred in credentials_found:
                        if created_hydra_jobs >= max_hydra_jobs:
                            break

                        username = cred.get("username")
                        password = cred.get("password")
                        cred_type = cred.get("credential_type", "database")

                        if not username or not password:
                            continue

                        # For database credentials, prioritize MySQL/PostgreSQL
                        if cred_type == "database":
                            # Check if MySQL is available
                            mysql_svc = next(
                                (
                                    s
                                    for s in services_to_test
                                    if s["service"] == "mysql"
                                ),
                                None,
                            )
                            if mysql_svc and created_hydra_jobs < max_hydra_jobs:
                                hydra_args = [
                                    "mysql",
                                    "-l",
                                    username,
                                    "-p",
                                    password,
                                    "-t",
                                    "1",
                                    "-vV",
                                    "-f",
                                ]

                                # Extract host from target URL
                                try:
                                    parsed_url = urlparse(target)
                                    hydra_target = parsed_url.hostname or target
                                except Exception:
                                    hydra_target = target

                                hydra_job_id = enqueue_job(
                                    tool="hydra",
                                    target=f"{hydra_target}:3306",
                                    args=hydra_args,
                                    label="lfi_extract",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by lfi_extract: Testing extracted credentials ({username}) against MySQL",
                                    rule_id=-6,  # Smart chain: lfi_extract → hydra MySQL
                                )
                                job_ids.append(hydra_job_id)
                                created_hydra_jobs += 1
                                logger.info(
                                    f"  Hydra MySQL job #{hydra_job_id} for {username}"
                                )

                            # Also try SSH if available (credential reuse)
                            ssh_svc = next(
                                (s for s in services_to_test if s["service"] == "ssh"),
                                None,
                            )
                            if ssh_svc and created_hydra_jobs < max_hydra_jobs:
                                hydra_args = [
                                    "ssh",
                                    "-l",
                                    username,
                                    "-p",
                                    password,
                                    "-t",
                                    "1",
                                    "-w",
                                    "3",
                                    "-vV",
                                    "-f",
                                ]

                                try:
                                    parsed_url = urlparse(target)
                                    hydra_target = parsed_url.hostname or target
                                except Exception:
                                    hydra_target = target

                                hydra_job_id = enqueue_job(
                                    tool="hydra",
                                    target=hydra_target,
                                    args=hydra_args,
                                    label="lfi_extract",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by lfi_extract: Testing credential reuse ({username}) against SSH",
                                    rule_id=-7,  # Smart chain: lfi_extract → hydra SSH (credential reuse)
                                )
                                job_ids.append(hydra_job_id)
                                created_hydra_jobs += 1
                                logger.info(
                                    f"  Hydra SSH job #{hydra_job_id} for {username} (credential reuse test)"
                                )

                    if created_hydra_jobs > 0:
                        logger.info(
                            f"lfi_extract auto-chain: Created {created_hydra_jobs} Hydra job(s)"
                        )
            # === END lfi_extract special handling ===

            # NOTE: sqlmap credential chaining is now handled in the dump phase handler above (line ~5169)

            # === Special handling for wpscan: Chain Hydra for WordPress password spraying ===
            if tool == "wpscan":
                from souleyez.engine.background import enqueue_job
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                users_found = parse_results.get("users_found", 0)
                users_list = parse_results.get("users", [])

                if users_found > 0 and users_list:
                    logger.info(
                        f"wpscan auto-chain: {users_found} WordPress user(s) found, creating password spray job"
                    )

                    target = job.get("target", "")

                    # Extract base URL for wp-login.php
                    try:
                        parsed_url = urlparse(target)
                        # Build base URL without path
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        # Get path for subdirectory installs (e.g., /blog/)
                        path = parsed_url.path.rstrip("/") if parsed_url.path else ""
                    except Exception:
                        base_url = target
                        path = ""

                    # Create temp file with usernames
                    import os as os_module
                    import tempfile

                    tmp_dir = os_module.path.join(
                        os_module.path.expanduser("~"), ".souleyez", "tmp"
                    )
                    os_module.makedirs(tmp_dir, exist_ok=True)

                    users_file = tempfile.NamedTemporaryFile(
                        mode="w", suffix="_wp_users.txt", delete=False, dir=tmp_dir
                    )
                    for username in users_list[:20]:  # Limit to 20 users
                        users_file.write(f"{username}\n")
                    users_file.close()

                    # Build Hydra args for WordPress login spray
                    wp_login_path = f"{path}/wp-login.php" if path else "/wp-login.php"

                    # Check for discovered wordlists from this engagement
                    # These are downloaded from robots.txt hints like fsocity.dic
                    password_list = "data/wordlists/top100.txt"  # Default
                    try:
                        discovered_dir = os_module.path.join(
                            os_module.path.expanduser("~"),
                            ".souleyez",
                            "data",
                            "wordlists",
                            "discovered",
                        )
                        if os_module.path.exists(discovered_dir):
                            # Look for wordlists from this engagement
                            for filename in os_module.listdir(discovered_dir):
                                if filename.startswith(f"eng{engagement_id}_"):
                                    discovered_path = os_module.path.join(
                                        discovered_dir, filename
                                    )
                                    # Use discovered wordlist if it's not too large (< 100k lines)
                                    with open(
                                        discovered_path,
                                        "r",
                                        encoding="utf-8",
                                        errors="replace",
                                    ) as f:
                                        line_count = sum(1 for _ in f)
                                    if line_count < 100000:
                                        password_list = discovered_path
                                        logger.info(
                                            f"wpscan auto-chain: Using discovered wordlist {filename} ({line_count} entries)"
                                        )
                                    else:
                                        # Create a subset for large wordlists
                                        subset_path = os_module.path.join(
                                            discovered_dir, f"subset_{filename}"
                                        )
                                        with open(
                                            discovered_path,
                                            "r",
                                            encoding="utf-8",
                                            errors="replace",
                                        ) as f:
                                            lines = [
                                                line.strip()
                                                for line in f
                                                if line.strip()
                                            ][:10000]
                                        with open(
                                            subset_path, "w", encoding="utf-8"
                                        ) as f:
                                            f.write("\n".join(lines))
                                        password_list = subset_path
                                        logger.info(
                                            f"wpscan auto-chain: Using first 10k entries from {filename}"
                                        )
                                    break
                    except Exception as e:
                        logger.warning(f"Error checking for discovered wordlists: {e}")

                    hydra_args = [
                        "-L",
                        users_file.name,
                        "-P",
                        password_list,
                        "-t",
                        "2",  # Low threads to avoid lockout
                        "-w",
                        "3",  # 3 second delay
                        "-vV",
                        "-f",  # Stop on first success
                        "http-post-form",
                        f"{wp_login_path}:log=^USER^&pwd=^PASS^&wp-submit=Log+In:F=is incorrect",
                    ]

                    hydra_job_id = enqueue_job(
                        tool="hydra",
                        target=base_url,
                        args=hydra_args,
                        label="wpscan",
                        engagement_id=engagement_id,
                        parent_id=job.get("id"),
                        reason=f"Auto-triggered by wpscan: Spraying common passwords against {users_found} enumerated WordPress user(s)",
                        rule_id=-9,  # Smart chain: wpscan → hydra (WordPress spray)
                    )
                    job_ids.append(hydra_job_id)
                    logger.info(
                        f"wpscan auto-chain: Created Hydra WordPress spray job #{hydra_job_id}"
                    )
                else:
                    # No users found with default enumeration - try aggressive ID brute-force
                    # Only if we haven't already tried u1-50
                    original_args = job.get("args", [])
                    original_args_str = " ".join(original_args) if original_args else ""

                    already_aggressive = (
                        "u1-" in original_args_str or "u1-50" in original_args_str
                    )

                    if not already_aggressive:
                        logger.info(
                            "wpscan auto-chain: No users found, trying aggressive ID enumeration (u1-50)"
                        )

                        target = job.get("target", "")

                        # Build new args with aggressive user enumeration
                        new_args = ["--enumerate", "u1-50", "--random-user-agent"]

                        # Carry over API token if present
                        if "--api-token" in original_args_str:
                            for i, arg in enumerate(original_args):
                                if arg == "--api-token" and i + 1 < len(original_args):
                                    new_args.extend(
                                        ["--api-token", original_args[i + 1]]
                                    )
                                    break

                        fallback_job_id = enqueue_job(
                            tool="wpscan",
                            target=target,
                            args=new_args,
                            label="wpscan",
                            engagement_id=engagement_id,
                            parent_id=job.get("id"),
                            reason=f"Auto-triggered: Initial wpscan found 0 users, trying brute-force ID enumeration (from job #{job.get('id')})",
                            rule_id=-10,  # Smart chain: wpscan → wpscan (fallback user enum)
                        )
                        job_ids.append(fallback_job_id)
                        logger.info(
                            f"wpscan auto-chain: Created fallback user enumeration job #{fallback_job_id}"
                        )
            # === END wpscan special handling ===

            # === Special handling for Katana: Chain SQLMap for discovered parameters ===
            if tool == "katana":
                from souleyez.engine.background import enqueue_job
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                # Get categorized URLs from katana parser
                # sqli_candidate_urls: URLs with non-LFI params (test with SQLMap)
                # lfi_candidate_urls: URLs with LFI params like ?page=, ?file= (test with LFI tools)
                sqli_candidates = parse_results.get("sqli_candidate_urls", [])
                lfi_candidates = parse_results.get("lfi_candidate_urls", [])
                forms_found = parse_results.get("forms_found", []) or parse_results.get(
                    "post_endpoints", []
                )
                injectable_urls = parse_results.get(
                    "injectable_urls", []
                )  # Already excludes LFI-only
                lfi_params = parse_results.get("lfi_params_found", [])

                # === 1. SQLMap for SQLi candidates (excludes LFI-only URLs) ===
                # Combine SQLi candidates with forms and JS endpoints
                # BUT filter out forms that only have LFI params
                all_sqli_targets = []
                for url in sqli_candidates:
                    if url not in all_sqli_targets:
                        all_sqli_targets.append(url)
                # Filter forms: exclude if URL is in lfi_candidates and has only LFI params
                for url in forms_found:
                    if url not in all_sqli_targets:
                        # Skip forms that are LFI-only (in lfi_candidates but not sqli_candidates)
                        if url in lfi_candidates and url not in sqli_candidates:
                            logger.debug(f"  Skipping form {url} - LFI-only params")
                            continue
                        all_sqli_targets.append(url)
                for url in injectable_urls:
                    if url not in all_sqli_targets:
                        # Also skip injectable_urls that are LFI-only
                        if url in lfi_candidates and url not in sqli_candidates:
                            logger.debug(
                                f"  Skipping injectable URL {url} - LFI-only params"
                            )
                            continue
                        all_sqli_targets.append(url)

                if all_sqli_targets:
                    logger.info(
                        f"Katana auto-chain: Found {len(all_sqli_targets)} SQLi candidate URL(s)"
                    )

                    created_sqlmap_jobs = 0
                    max_sqlmap_jobs = 10  # Limit to prevent overwhelming the target

                    for url in all_sqli_targets:
                        if created_sqlmap_jobs >= max_sqlmap_jobs:
                            logger.info(
                                f"Katana auto-chain: Reached max SQLMap jobs ({max_sqlmap_jobs})"
                            )
                            break

                        # Skip static files and non-injectable endpoints
                        path_lower = url.lower()
                        static_extensions = (
                            ".html",
                            ".htm",
                            ".txt",
                            ".css",
                            ".js",
                            ".json",
                            ".xml",
                            ".svg",
                            ".png",
                            ".jpg",
                            ".jpeg",
                            ".gif",
                            ".ico",
                            ".woff",
                            ".woff2",
                            ".ttf",
                            ".eot",
                            ".pdf",
                            ".doc",
                            ".docx",
                            ".xls",
                            ".xlsx",
                        )
                        if any(path_lower.endswith(ext) for ext in static_extensions):
                            continue

                        # Skip WebSocket/socket.io endpoints - not injectable
                        if (
                            "/socket.io/" in url
                            or "/sockjs/" in url
                            or "websocket" in path_lower
                        ):
                            continue

                        # Skip external URLs - only test URLs on the original target host
                        try:
                            from urllib.parse import urlparse

                            parsed_url = urlparse(url)
                            parsed_target = urlparse(target)
                            if parsed_url.netloc and parsed_target.netloc:
                                if (
                                    parsed_url.netloc.lower()
                                    != parsed_target.netloc.lower()
                                ):
                                    logger.debug(f"  Skipping external URL: {url}")
                                    continue
                        except Exception:
                            pass

                        # Skip non-injectable paths (TWiki, phpMyAdmin, Apache dir params)
                        skip_patterns = [
                            "/twiki/",  # TWiki wiki - not SQLi vulnerable
                            "/phpmyadmin/",  # phpMyAdmin - DB admin, not SQLi
                            "/phpmyadmin.",  # phpMyAdmin CSS/JS files
                            "?c=d",
                            "?c=s",
                            "?c=m",
                            "?c=n",  # Apache dir listing sort params
                            "?o=a",
                            "?o=d",  # Apache dir listing order params
                            ";o=a",
                            ";o=d",  # Apache dir listing (semicolon variant)
                            "/misc/",  # Drupal/CMS static assets directory
                            "/modules/",  # Drupal modules directory (static files)
                        ]
                        # Also skip static files with version/cache-busting params
                        # These are not injectable: /jquery.js?v=1.2.3, /style.css?ver=5.0
                        if ".js?" in path_lower or ".css?" in path_lower:
                            logger.debug(
                                f"  Skipping static file with cache param: {url}"
                            )
                            continue
                        if any(pattern in path_lower for pattern in skip_patterns):
                            logger.debug(f"  Skipping non-injectable path: {url}")
                            continue

                        # Skip URLs without real parameters (just base URL or path)
                        if "?" not in url and url not in forms_found:
                            logger.debug(f"  Skipping URL without parameters: {url}")
                            continue

                        # Determine if this is a form (POST) or URL param (GET)
                        is_form = url in forms_found

                        sqlmap_args = [
                            "-u",
                            url,
                            "--batch",
                            "--level=2",
                            "--risk=2",
                            "--threads=5",
                        ]

                        if is_form:
                            sqlmap_args.append("--forms")

                        sqlmap_job_id = enqueue_job(
                            tool="sqlmap",
                            target=url,
                            args=sqlmap_args,
                            label="katana",
                            engagement_id=engagement_id,
                            parent_id=job.get("id"),
                            reason=f"Auto-triggered by katana: {'Form' if is_form else 'Parameterized URL'} discovered",
                            rule_id=-23,  # Smart chain: katana → sqlmap
                        )

                        job_ids.append(sqlmap_job_id)
                        created_sqlmap_jobs += 1
                        logger.info(f"  SQLMap job #{sqlmap_job_id} for {url}")

                    if created_sqlmap_jobs > 0:
                        logger.info(
                            f"Katana auto-chain: Created {created_sqlmap_jobs} SQLMap job(s)"
                        )

                # === 2. LFI scanning for LFI candidate URLs ===
                if lfi_candidates:
                    logger.info(
                        f"Katana auto-chain: Found {len(lfi_candidates)} LFI candidate URL(s)"
                    )
                    if lfi_params:
                        logger.info(f"  LFI params detected: {', '.join(lfi_params)}")

                    created_lfi_jobs = 0
                    max_lfi_jobs = 5  # Limit LFI jobs

                    for url in lfi_candidates:
                        if created_lfi_jobs >= max_lfi_jobs:
                            logger.info(
                                f"Katana auto-chain: Reached max LFI jobs ({max_lfi_jobs})"
                            )
                            break

                        # Nuclei LFI scan
                        nuclei_lfi_args = [
                            "-tags",
                            "lfi",
                            "-severity",
                            "critical,high,medium,low",
                            "-rate-limit",
                            "50",
                        ]

                        nuclei_job_id = enqueue_job(
                            tool="nuclei",
                            target=url,
                            args=nuclei_lfi_args,
                            label="katana",
                            engagement_id=engagement_id,
                            parent_id=job.get("id"),
                            reason=f"Auto-triggered by katana: LFI-suspicious parameter detected",
                            rule_id=-3,  # Smart chain: katana → nuclei LFI
                        )

                        job_ids.append(nuclei_job_id)
                        created_lfi_jobs += 1
                        logger.info(f"  Nuclei LFI job #{nuclei_job_id} for {url}")

                    if created_lfi_jobs > 0:
                        logger.info(
                            f"Katana auto-chain: Created {created_lfi_jobs} Nuclei LFI job(s)"
                        )

                    # === 2b. FFUF LFI fuzzing for deep testing ===
                    # Use LFI payloads wordlist for each LFI candidate
                    from souleyez.wordlists import resolve_wordlist_path

                    lfi_wordlist = resolve_wordlist_path(
                        "data/wordlists/lfi_payloads.txt"
                    )

                    if lfi_wordlist:
                        created_ffuf_lfi_jobs = 0
                        max_ffuf_lfi_jobs = 3  # Limit to most promising targets
                        seen_fuzz_urls = set()  # Deduplicate fuzz URLs

                        for url in lfi_candidates:
                            if created_ffuf_lfi_jobs >= max_ffuf_lfi_jobs:
                                break

                            # Extract the parameter name to fuzz
                            from urllib.parse import parse_qs

                            parsed_url = urlparse(url)  # urlparse imported globally
                            params = parse_qs(parsed_url.query)

                            # Find the LFI param in this URL
                            from souleyez.parsers.katana_parser import LFI_PARAM_NAMES

                            lfi_param = None
                            for param_name in params.keys():
                                if param_name.lower() in LFI_PARAM_NAMES:
                                    lfi_param = param_name
                                    break

                            if lfi_param:
                                # Build FFUF URL with FUZZ placeholder
                                base_path = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                                fuzz_url = f"{base_path}?{lfi_param}=FUZZ"

                                # Skip if we've already created an FFUF job for this fuzz URL
                                if fuzz_url in seen_fuzz_urls:
                                    logger.debug(
                                        f"  Skipping duplicate FFUF LFI target: {fuzz_url}"
                                    )
                                    continue
                                seen_fuzz_urls.add(fuzz_url)

                                ffuf_args = [
                                    "-u",
                                    fuzz_url,
                                    "-w",
                                    lfi_wordlist,
                                    "-mc",
                                    "200,301,302,500",  # Include 500 for error-based LFI
                                    "-fs",
                                    "0",  # Filter empty responses
                                    "-t",
                                    "5",
                                    "-p",
                                    "0.1",
                                ]

                                ffuf_job_id = enqueue_job(
                                    tool="ffuf",
                                    target=fuzz_url,
                                    args=ffuf_args,
                                    label="katana",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by katana: LFI param '{lfi_param}' detected",
                                    rule_id=-25,  # Smart chain: katana → ffuf LFI
                                )

                                job_ids.append(ffuf_job_id)
                                created_ffuf_lfi_jobs += 1
                                logger.info(
                                    f"  FFUF LFI job #{ffuf_job_id} for {lfi_param}=FUZZ"
                                )

                        if created_ffuf_lfi_jobs > 0:
                            logger.info(
                                f"Katana auto-chain: Created {created_ffuf_lfi_jobs} FFUF LFI job(s)"
                            )

                # Also trigger Nuclei DAST on all crawled URLs
                crawled_urls = parse_results.get(
                    "crawled_urls", []
                ) or parse_results.get("urls", [])
                if crawled_urls:
                    # Create a single nuclei job targeting the base URL with DAST templates
                    # (Nuclei will crawl from there)
                    base_url = target
                    nuclei_args = [
                        "-dast",  # Enable DAST mode (required for DAST templates)
                        "-severity",
                        "critical,high,medium",
                        "-rate-limit",
                        "50",
                    ]

                    nuclei_job_id = enqueue_job(
                        tool="nuclei",
                        target=base_url,
                        args=nuclei_args,
                        label="katana",
                        engagement_id=engagement_id,
                        parent_id=job.get("id"),
                        reason=f"Auto-triggered by katana: {len(crawled_urls)} URLs crawled",
                        rule_id=-24,  # Smart chain: katana → nuclei DAST
                    )

                    job_ids.append(nuclei_job_id)
                    logger.info(
                        f"Katana auto-chain: Created Nuclei DAST job #{nuclei_job_id}"
                    )
            # === END Katana special handling ===

            # Special handling for theHarvester: split into two phases
            logger.info(f"auto_chain: checking theHarvester/elif chain for tool={tool}")
            if tool == "theharvester":
                # PHASE 1: Always process the original domain for whois/dnsrecon
                # This runs REGARDLESS of whether URLs were found
                if target:  # target is the original domain (e.g., "vulnweb.com")
                    domain_context = {
                        "target": target,
                        "tool": tool,
                        "services": [],
                        "findings": [],
                        "hosts": [],
                        "domains": [target],  # Important: include original domain
                        "subdomains": parse_results.get("subdomains", []),
                    }

                    # Evaluate chains - will match whois/dnsrecon rules
                    domain_commands = self.evaluate_chains(tool, domain_context)

                    # Enqueue domain-specific tools (whois, dnsrecon)
                    job_ids.extend(
                        self._enqueue_commands(
                            domain_commands,
                            tool,
                            engagement_id,
                            target,
                            parent_job_id=job.get("id"),
                        )
                    )

                # PHASE 2: Process URLs with parameters for SQLMap
                # PHASE 3: Process base URLs for Nuclei
                urls = parse_results.get("urls", [])

                if urls:

                    def normalize_url(url):
                        """
                        Normalize URL to prevent duplicate scans:
                        - Remove www. subdomain (www.example.com → example.com)
                        - Remove trailing dots from hostname (vulnweb.com. → vulnweb.com)
                        - Normalize scheme to https for dedup (http and https are same target)
                        - Keep the base URL structure

                        Returns: normalized_url
                        """
                        parsed = urlparse(url)
                        netloc = parsed.netloc.lower()

                        # Remove www. prefix
                        if netloc.startswith("www."):
                            netloc = netloc[4:]

                        # Remove trailing dots from hostname
                        netloc = netloc.rstrip(".")

                        # Normalize scheme to https for dedup purposes
                        scheme = "https"

                        # Rebuild URL with normalized netloc and scheme
                        normalized = f"{scheme}://{netloc}{parsed.path}"
                        if parsed.query:
                            normalized += f"?{parsed.query}"

                        return normalized

                    # Normalize URLs for dedup but keep original URLs for scanning
                    # Format: {normalized_key: original_url}
                    url_map = {}

                    for url in urls:
                        normalized = normalize_url(url)
                        # Use normalized URL as key for dedup, but store ORIGINAL URL
                        if normalized not in url_map:
                            url_map[normalized] = (
                                url  # Keep original URL with original scheme
                            )

                    # Use original URLs for scanning (deduped by normalized key)
                    deduped_urls = list(url_map.values())

                    print(
                        f"  🔗 Normalized {len(urls)} URLs → {len(deduped_urls)} unique targets"
                    )
                    if len(urls) > len(deduped_urls):
                        print(
                            f"  ⏭️  Skipped {len(urls) - len(deduped_urls)} duplicate variations"
                        )

                    # Track base URLs for web scanners (avoid duplicates)
                    scanned_base_urls = set()

                    for url in deduped_urls:
                        parsed_url = urlparse(url)

                        # SQLMap: Process URLs with query parameters
                        if parsed_url.query:
                            url_context = {
                                "target": url,
                                "tool": tool,
                                "services": [],
                                "findings": [],
                                "urls": [url],
                                "urls_with_params": [url],  # Triggers SQLMap rule
                            }

                            # Evaluate chains
                            url_commands = self.evaluate_chains(tool, url_context)

                            # CRITICAL: Filter to ONLY sqlmap
                            # whois/dnsrecon expect domains, not full URLs
                            sqlmap_only = [
                                cmd for cmd in url_commands if cmd["tool"] == "sqlmap"
                            ]

                            # Enqueue SQLMap jobs for this URL
                            job_ids.extend(
                                self._enqueue_commands(
                                    sqlmap_only,
                                    tool,
                                    engagement_id,
                                    url,
                                    parent_job_id=job.get("id"),
                                )
                            )

                        # Web scanners: Process base URLs only (no path or just "/")
                        path = parsed_url.path.rstrip("/")

                        if not path or path == "":
                            # Build base URL: scheme://netloc
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

                            # Normalize for dedup check (removes trailing dots, normalizes scheme)
                            normalized_base = normalize_url(base_url)

                            # Skip if we already queued scans for this base URL
                            if normalized_base not in scanned_base_urls:
                                scanned_base_urls.add(normalized_base)

                                # Create context for web scanner chain rules
                                scan_context = {
                                    "target": base_url,
                                    "tool": tool,
                                    "base_urls": [
                                        base_url
                                    ],  # Triggers nuclei/gobuster rules
                                }

                                # Evaluate chains
                                scan_commands = self.evaluate_chains(tool, scan_context)

                                # CRITICAL: Filter to ONLY web scanners
                                # whois/dnsrecon expect domains, not full URLs
                                web_scanner_only = [
                                    cmd
                                    for cmd in scan_commands
                                    if cmd["tool"] in ["nuclei", "gobuster", "sqlmap"]
                                ]

                                # Enqueue web scanner jobs
                                job_ids.extend(
                                    self._enqueue_commands(
                                        web_scanner_only,
                                        tool,
                                        engagement_id,
                                        base_url,
                                        parent_job_id=job.get("id"),
                                    )
                                )

                # PHASE 4: Auto-chain nmap scans for discovered IPs
                ips = parse_results.get("ips", [])

                if ips:
                    nmap_commands = []
                    for ip in ips:
                        nmap_commands.append(
                            {
                                "tool": "nmap",
                                "target": ip,
                                "args": ["-F"],  # Fast scan (top 100 ports)
                                "reason": f"IP discovered by theHarvester, performing fast port scan",
                            }
                        )

                    # Enqueue all nmap jobs with parent_id
                    job_ids.extend(
                        self._enqueue_commands(
                            nmap_commands,
                            tool,
                            engagement_id,
                            expected_target=None,  # IPs can be from any target
                            parent_job_id=job.get("id"),
                        )
                    )

                return job_ids

            # === Special handling for Impacket GetNPUsers → hashcat ===
            elif tool == "impacket-getnpusers":
                asrep_hashes = parse_results.get("asrep_hashes", [])

                if asrep_hashes:
                    # Create temp file with AS-REP hashes for hashcat
                    import os
                    import tempfile

                    # Create hash file (uses secure tempdir)
                    hash_file = tempfile.NamedTemporaryFile(
                        mode="w", suffix=".txt", prefix="asrep_hashes_", delete=False
                    )

                    for hash_entry in asrep_hashes:
                        hash_file.write(f"{hash_entry.get('hash', '')}\n")

                    hash_file.close()

                    # Chain to hashcat with Kerberos 5 AS-REP mode (18200)
                    from souleyez.engine.background import enqueue_job

                    job_id = enqueue_job(
                        tool="hashcat",
                        target=hash_file.name,
                        args=[
                            "-m",
                            "18200",
                            "-a",
                            "0",
                            "data/wordlists/passwords_crack.txt",
                        ],
                        label="impacket-getnpusers",
                        engagement_id=engagement_id,
                        parent_id=job.get("id"),
                        reason="Auto-triggered by impacket-getnpusers: AS-REP hash extracted, attempting to crack",
                        skip_scope_check=True,  # Local file cracking, not network scan
                    )

                    job_ids.append(job_id)

                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)
                    logger.info(
                        f"Auto-chained: GetNPUsers → hashcat (cracking {len(asrep_hashes)} AS-REP hashes)"
                    )

                return job_ids

            # === Special handling for Impacket secretsdump → hashcat ===
            elif tool == "impacket-secretsdump":
                hashes = parse_results.get("hashes", [])

                if hashes:
                    # Create temp file with NTLM hashes for hashcat
                    import os
                    import tempfile

                    # Create hash file in format: username:hash (uses secure tempdir)
                    hash_file = tempfile.NamedTemporaryFile(
                        mode="w", suffix=".txt", prefix="ntlm_hashes_", delete=False
                    )

                    for hash_entry in hashes:
                        username = hash_entry.get("username", "unknown")
                        nt_hash = hash_entry.get("nt_hash", "")
                        if nt_hash:
                            hash_file.write(f"{username}:{nt_hash}\n")

                    hash_file.close()

                    # Chain to hashcat with NTLM mode (1000)
                    # --username flag needed because hash file format is username:hash
                    from souleyez.engine.background import enqueue_job

                    job_id = enqueue_job(
                        tool="hashcat",
                        target=hash_file.name,
                        args=[
                            "-m",
                            "1000",
                            "-a",
                            "0",
                            "--username",
                            "data/wordlists/passwords_crack.txt",
                        ],
                        label="impacket-secretsdump",
                        engagement_id=engagement_id,
                        parent_id=job.get("id"),
                        reason="Auto-triggered by impacket-secretsdump: NTLM hash extracted, attempting to crack",
                        skip_scope_check=True,  # Local file cracking, not network scan
                    )

                    job_ids.append(job_id)

                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)
                    logger.info(
                        f"Auto-chained: secretsdump → hashcat (cracking {len(hashes)} NTLM hashes)"
                    )

                return job_ids

            # === Special handling for CrackMapExec → secretsdump ===
            elif tool == "crackmapexec":
                valid_admins = parse_results.get("valid_admin_credentials", [])
                findings = parse_results.get("findings", {})
                hosts = findings.get("hosts", [])

                # Use job target directly if no hosts in findings (common case)
                target_host = hosts[0].get("ip", target) if hosts else target

                if valid_admins:
                    from souleyez.engine.background import enqueue_job, get_all_jobs

                    # Deduplicate admin credentials (same user:pass only needs one set of chains)
                    seen_creds = set()
                    unique_admins = []
                    for cred in valid_admins:
                        cred_key = f"{cred.get('domain', '')}\\{cred.get('username', '')}:{cred.get('password', '')}"
                        if cred_key not in seen_creds:
                            seen_creds.add(cred_key)
                            unique_admins.append(cred)

                    # Check for existing post-exploitation jobs to avoid duplicates
                    existing_tools = set()
                    try:
                        all_jobs = get_all_jobs()
                        for j in all_jobs:
                            if (
                                j.get("engagement_id") != engagement_id
                                or j.get("status") == "killed"
                            ):
                                continue
                            if j.get("target") == target_host and j.get("tool") in [
                                "impacket-secretsdump",
                                "impacket-psexec",
                                "impacket-wmiexec",
                                "impacket-atexec",
                            ]:
                                existing_tools.add(j.get("tool"))
                    except Exception:
                        pass

                    for cred in unique_admins:
                        domain = cred.get("domain", "")
                        username = cred.get("username", "")
                        password = cred.get("password", "")

                        # Build secretsdump args in Impacket format: domain/username:password@host
                        if domain:
                            cred_str = f"{domain}/{username}:{password}@{target_host}"
                        else:
                            cred_str = f"{username}:{password}@{target_host}"

                        # Only enqueue if not already queued/running for this target
                        if "impacket-secretsdump" not in existing_tools:
                            job_id = enqueue_job(
                                tool="impacket-secretsdump",
                                target=target_host,
                                args=[cred_str],
                                label="crackmapexec",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason="Auto-triggered by crackmapexec: Admin credentials found (Pwn3d!), extracting domain secrets",
                                rule_id=-19,  # Smart chain: crackmapexec → secretsdump
                            )
                            job_ids.append(job_id)
                            existing_tools.add("impacket-secretsdump")

                        # Also chain to psexec for shell access (run command, not interactive)
                        if "impacket-psexec" not in existing_tools:
                            psexec_job_id = enqueue_job(
                                tool="impacket-psexec",
                                target=target_host,
                                args=[cred_str, "whoami"],
                                label="crackmapexec",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered by crackmapexec: Admin credentials found (Pwn3d!), verifying shell access",
                                rule_id=-27,  # Smart chain: crackmapexec → psexec
                            )
                            job_ids.append(psexec_job_id)
                            existing_tools.add("impacket-psexec")

                        # Chain to evil-winrm for WinRM shell access
                        if "evil_winrm" not in existing_tools:
                            winrm_job_id = enqueue_job(
                                tool="evil_winrm",
                                target=target_host,
                                args=[
                                    "-u",
                                    username,
                                    "-p",
                                    password,
                                    "-P",
                                    "5985",
                                    "-c",
                                    "whoami",
                                ],
                                label="crackmapexec",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered by crackmapexec: Admin credentials found (Pwn3d!), verifying WinRM access",
                                rule_id=-28,  # Smart chain: crackmapexec → evil_winrm
                            )
                            job_ids.append(winrm_job_id)
                            existing_tools.add("evil_winrm")

                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)
                    logger.info(
                        f"Auto-chained: CrackMapExec → secretsdump + psexec + evil_winrm ({len(unique_admins)} unique admin credentials)"
                    )

                # === Readable SMB shares found → explore with smbclient ===
                readable_shares = parse_results.get("readable_shares", [])
                if readable_shares:
                    from souleyez.engine.background import enqueue_job
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)

                    # Skip default admin shares - focus on custom/interesting shares
                    skip_shares = {"ADMIN$", "C$", "IPC$"}
                    # User home shares that likely contain usernames as directories
                    home_shares = {"homes", "users", "home", "profiles", "Users"}

                    # Get stored credentials for this host to use instead of guest
                    smb_creds = None
                    try:
                        from souleyez.storage.credentials import CredentialsManager
                        from souleyez.storage.hosts import HostManager

                        cred_mgr = CredentialsManager()
                        host_mgr = HostManager()
                        host = host_mgr.get_host_by_ip(engagement_id, target)
                        if host:
                            stored_creds = cred_mgr.list_credentials(
                                engagement_id, host_id=host["id"]
                            )
                            # Find SMB/Windows credentials - prefer passwords over hashes
                            # Hashes require different auth flags and may be from later chain stages
                            for cred in stored_creds:
                                if cred.get("service") in [
                                    "smb",
                                    "winrm",
                                    "ldap",
                                    "windows",
                                ]:
                                    # Only use password-type creds, not hashes
                                    # Hashes need --hash flag and may be stale from previous runs
                                    cred_type = cred.get("credential_type", "password")
                                    if cred_type in ["password", "plaintext"]:
                                        smb_creds = cred
                                        break
                    except Exception as e:
                        logger.debug(f"Could not get stored credentials: {e}")

                    for share in readable_shares:
                        share_name = share.get("name", "")
                        if not share_name or share_name in skip_shares:
                            continue

                        # Skip if share_name looks like a domain\user (parser confusion)
                        if "\\" in share_name and not share_name.endswith("$"):
                            logger.debug(
                                f"Skipping '{share_name}' - looks like domain\\user, not share name"
                            )
                            continue

                        # Use smbmap for recursive share listing with GPP detection
                        # smbmap handles null session automatically and finds Groups.xml
                        if smb_creds:
                            username = smb_creds.get("username", "")
                            password = smb_creds.get("password", "")
                            smbmap_args = [
                                "-H",
                                target,
                                "-u",
                                username,
                                "-p",
                                password,
                                "-r",
                                share_name,
                                "--depth",
                                "10",
                            ]
                            logger.info(
                                f"Using stored credentials ({username}) for share access"
                            )
                        else:
                            # Use null session - smbmap defaults to anonymous without -u/-p
                            smbmap_args = [
                                "-H",
                                target,
                                "-r",
                                share_name,
                                "--depth",
                                "10",
                            ]

                        # Explore share with smbmap for recursive listing and GPP detection
                        job_id = enqueue_job(
                            tool="smbmap",
                            target=target,
                            args=smbmap_args,
                            label="crackmapexec",
                            engagement_id=engagement_id,
                            parent_id=job.get("id"),
                            reason=f"Auto-triggered by crackmapexec: Exploring '{share_name}' share for GPP/credentials",
                            rule_id=-11,  # Smart chain: crackmapexec → smbmap (readable shares)
                        )
                        job_ids.append(job_id)
                        logger.info(
                            f"Auto-chained: CrackMapExec → smbmap (explore {share_name} share)"
                        )

                        # If this is a homes-type share, also spider for SYSVOL login scripts
                        if share_name.lower() in [s.lower() for s in home_shares]:
                            logger.info(
                                f"  '{share_name}' appears to be a home directory share - will extract usernames for spray"
                            )

                # === STATUS_PASSWORD_MUST_CHANGE → smbpasswd password change ===
                # When crackmapexec finds users with STATUS_PASSWORD_MUST_CHANGE,
                # the password is valid but MUST be changed before login succeeds.
                # Chain to smbpasswd to change the password, then evil-winrm.
                password_must_change = parse_results.get("password_must_change", [])
                if password_must_change:
                    from souleyez.engine.background import enqueue_job
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)

                    # Deduplicate by username to avoid multiple smbpasswd jobs for same user
                    seen_users = set()

                    for entry in password_must_change:
                        domain = entry.get("domain", "")
                        username = entry.get("username", "")
                        old_password = entry.get("password", "")

                        # Skip duplicates
                        user_key = f"{domain}\\{username}".lower()
                        if user_key in seen_users:
                            logger.debug(f"Skipping duplicate smbpasswd for {username}")
                            continue
                        seen_users.add(user_key)

                        if not username or not old_password:
                            continue

                        # Generate a new password that meets complexity requirements
                        # Append "!" and increment number to create valid new password
                        if old_password.endswith("!"):
                            new_password = old_password[:-1] + "1!"
                        else:
                            new_password = old_password + "1!"

                        logger.info(
                            f"STATUS_PASSWORD_MUST_CHANGE detected for {domain}\\{username}"
                        )
                        logger.info(f"  Chaining smbpasswd to change password...")

                        # Chain to smbpasswd to change the password
                        smbpasswd_job_id = enqueue_job(
                            tool="smbpasswd",
                            target=target,
                            args=[
                                "-U",
                                username,
                                "--old-pass",
                                old_password,
                                "--new-pass",
                                new_password,
                            ],
                            label="crackmapexec",
                            engagement_id=engagement_id,
                            parent_id=job.get("id"),
                            reason=f"Auto-triggered by crackmapexec: {username} has STATUS_PASSWORD_MUST_CHANGE - changing password",
                            rule_id=-50,  # Smart chain: crackmapexec → smbpasswd (password must change)
                        )
                        job_ids.append(smbpasswd_job_id)
                        logger.info(
                            f"  Chained: crackmapexec → smbpasswd job #{smbpasswd_job_id}"
                        )

                return job_ids

            # === smbpasswd special handling: password changed → evil-winrm ===
            elif tool == "smbpasswd":
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                password_changed = parse_results.get("password_changed", False)
                username = parse_results.get("username", "")
                new_password = parse_results.get("new_password", "")

                if password_changed and username and new_password:
                    # Check for existing evil-winrm job for same user to avoid duplicates
                    from datetime import datetime, timedelta, timezone

                    from souleyez.engine.background import list_jobs

                    try:
                        all_jobs = list_jobs(limit=500)
                        cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
                        already_chained = False
                        for rj in all_jobs:
                            # Filter by tool and engagement
                            if rj.get("tool") != "evil_winrm":
                                continue
                            if rj.get("engagement_id") != engagement_id:
                                continue
                            # Check if created recently
                            created_str = rj.get("created_at", "")
                            if created_str:
                                try:
                                    created = datetime.fromisoformat(
                                        created_str.replace("Z", "+00:00")
                                    )
                                    if created < cutoff:
                                        continue
                                except Exception:
                                    pass
                            # Check if same username in args
                            rj_args = rj.get("args", [])
                            if isinstance(rj_args, str):
                                rj_args = rj_args.split()
                            if username in rj_args:
                                logger.info(
                                    f"Skipping duplicate evil-winrm chain for {username}"
                                )
                                already_chained = True
                                break
                        if already_chained:
                            return job_ids
                    except Exception as e:
                        logger.debug(f"Could not check for duplicate evil-winrm: {e}")

                    logger.info(f"Password successfully changed for {username}")
                    logger.info(f"  Chaining evil-winrm for shell access...")

                    from souleyez.engine.background import enqueue_job

                    # Chain to evil-winrm with new credentials
                    # Use -c 'whoami' to test auth (no TTY in background jobs)
                    winrm_job_id = enqueue_job(
                        tool="evil_winrm",
                        target=target,
                        args=[
                            "-u",
                            username,
                            "-p",
                            new_password,
                            "-P",
                            "5985",
                            "-c",
                            "whoami",
                        ],
                        label="smbpasswd",
                        engagement_id=engagement_id,
                        parent_id=job.get("id"),
                        reason=f"Auto-triggered by smbpasswd: Password changed for {username} - connecting via WinRM",
                        rule_id=-51,  # Smart chain: smbpasswd → evil-winrm
                    )
                    job_ids.append(winrm_job_id)
                    logger.info(
                        f"  Chained: smbpasswd → evil-winrm job #{winrm_job_id}"
                    )

                return job_ids

            # === Secretsdump special handling: NTLM hashes → hashcat ===
            elif tool == "impacket_secretsdump" or tool == "impacket-secretsdump":
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                hashes = parse_results.get("hashes", [])
                hashes_count = parse_results.get("hashes_count", 0)

                if hashes and hashes_count > 0:
                    logger.info(
                        f"Secretsdump extracted {hashes_count} NTLM hash(es), chaining to hashcat"
                    )

                    import os
                    import tempfile

                    from souleyez.engine.background import enqueue_job

                    # Create a temporary hash file for hashcat
                    # Format: username:rid:lm:nt::: (but hashcat mode 1000 just needs NT hash)
                    hash_dir = os.path.join(
                        os.path.expanduser("~"), ".souleyez", "hashes"
                    )
                    os.makedirs(hash_dir, exist_ok=True)

                    hash_file = os.path.join(
                        hash_dir, f"secretsdump_{job.get('id', 'unknown')}.txt"
                    )
                    with open(hash_file, "w") as f:
                        for h in hashes:
                            # Write in hashcat-compatible format: username:hash
                            username = h.get("username", "unknown")
                            nt_hash = h.get("nt_hash", "")
                            if nt_hash:
                                f.write(f"{username}:{nt_hash}\n")

                    # Run hashcat with NTLM mode (1000)
                    hashcat_job_id = enqueue_job(
                        tool="hashcat",
                        target=hash_file,
                        args=[
                            "-m",
                            "1000",
                            hash_file,
                            "--wordlist",
                            "passwords_crack.txt",
                            "--username",
                        ],
                        label="impacket-secretsdump",
                        engagement_id=engagement_id,
                        parent_id=job.get("id"),
                        reason=f"Auto-triggered by secretsdump: Cracking {hashes_count} NTLM hash(es)",
                        rule_id=-21,  # Smart chain: secretsdump → hashcat
                        metadata={"hash_file": hash_file, "hash_mode": "1000"},
                    )
                    job_ids.append(hashcat_job_id)
                    logger.info(
                        f"  Chained: secretsdump → hashcat job #{hashcat_job_id}"
                    )

                return job_ids

            # === GetNPUsers special handling: AS-REP hashes → hashcat ===
            elif tool == "impacket-getnpusers":
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                asrep_hashes = parse_results.get("asrep_hashes", [])
                hashes_count = parse_results.get("hashes_count", len(asrep_hashes))

                if asrep_hashes and hashes_count > 0:
                    logger.info(
                        f"GetNPUsers extracted {hashes_count} AS-REP hash(es), chaining to hashcat"
                    )

                    import os

                    from souleyez.engine.background import enqueue_job

                    # Create a hash file for hashcat
                    hash_dir = os.path.join(
                        os.path.expanduser("~"), ".souleyez", "hashes"
                    )
                    os.makedirs(hash_dir, exist_ok=True)

                    hash_file = os.path.join(
                        hash_dir, f"getnpusers_{job.get('id', 'unknown')}.txt"
                    )
                    with open(hash_file, "w") as f:
                        for h in asrep_hashes:
                            # Write the full AS-REP hash
                            hash_value = h.get("hash", "")
                            if hash_value:
                                f.write(f"{hash_value}\n")

                    # Run hashcat with AS-REP mode (18200)
                    hashcat_job_id = enqueue_job(
                        tool="hashcat",
                        target=hash_file,
                        args=[
                            "-m",
                            "18200",
                            hash_file,
                            "--wordlist",
                            "passwords_crack.txt",
                        ],
                        label="impacket-getnpusers",
                        engagement_id=engagement_id,
                        parent_id=job.get("id"),
                        reason=f"Auto-triggered by GetNPUsers: Cracking {hashes_count} AS-REP hash(es)",
                        rule_id=-22,  # Smart chain: getnpusers → hashcat
                        metadata={"hash_file": hash_file, "hash_mode": "18200"},
                    )
                    job_ids.append(hashcat_job_id)
                    logger.info(
                        f"  Chained: GetNPUsers → hashcat job #{hashcat_job_id}"
                    )

                return job_ids

            # === Special handling for smbmap: GPP file extraction ===
            if tool == "smbmap":
                gpp_files = parse_results.get("gpp_files", [])
                has_gpp = parse_results.get("has_gpp_files", False)

                if has_gpp and gpp_files:
                    from souleyez.engine.background import enqueue_job
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)

                    logger.info(
                        f"smbmap found {len(gpp_files)} GPP file(s) - triggering extraction"
                    )

                    # Build SMB path from job args
                    # Args format: ['-H', 'host', '-r', 'share', ...]
                    job_args = job.get("args", [])
                    smb_host = target

                    # Extract share name from args
                    share_name = None
                    for i, arg in enumerate(job_args):
                        if arg == "-r" and i + 1 < len(job_args):
                            share_name = job_args[i + 1]
                            break

                    if not share_name:
                        # Try to extract from GPP file paths
                        for gpp in gpp_files:
                            if gpp.get("share"):
                                share_name = gpp["share"]
                                break

                    if share_name:
                        for gpp in gpp_files[:5]:  # Limit to 5 GPP files
                            gpp_path = gpp.get("path", "")
                            gpp_file = gpp.get("file", "Groups.xml")

                            if not gpp_path:
                                continue

                            # Clean up path - remove share prefix if present
                            clean_path = gpp_path
                            if clean_path.startswith(share_name + "/"):
                                clean_path = clean_path[len(share_name) + 1 :]

                            # Create gpp_extract job
                            job_id = enqueue_job(
                                tool="gpp_extract",
                                target=smb_host,
                                args=[
                                    "--share",
                                    share_name,
                                    "--path",
                                    clean_path,
                                    "--host",
                                    smb_host,
                                ],
                                label="smbmap",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered by smbmap: GPP file '{gpp_file}' found with potential credentials",
                                rule_id=-13,  # Smart chain: smbmap → gpp_extract
                            )
                            job_ids.append(job_id)
                            logger.info(
                                f"  Created gpp_extract job #{job_id} for {gpp_path}"
                            )
                    else:
                        logger.warning(
                            "smbmap GPP chain: Could not determine share name"
                        )

                return job_ids

            # === GPP Extract → Credential-based attacks ===
            elif tool == "gpp_extract":
                credentials = parse_results.get("credentials", [])
                username = parse_results.get("username")
                password = parse_results.get("password")

                if username and password:
                    from souleyez.engine.background import enqueue_job
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)
                    logger.info(
                        f"gpp_extract found credentials: {username}, chaining attacks..."
                    )

                    # Extract domain from username if present (e.g., active.htb\SVC_TGS)
                    domain = None
                    clean_username = username
                    if "\\" in username:
                        domain, clean_username = username.split("\\", 1)
                    elif "@" in username:
                        clean_username, domain = username.split("@", 1)

                    # Chain 1: Kerberoasting with GetUserSPNs
                    # This finds service accounts that can be cracked offline
                    if domain:
                        # Build credential string for Impacket: domain/user:password
                        cred_str = f"{domain}/{clean_username}:{password}"

                        job_id = enqueue_job(
                            tool="impacket-GetUserSPNs",
                            target=target,
                            args=[cred_str, "-dc-ip", target, "-request"],
                            label="gpp_extract",
                            engagement_id=engagement_id,
                            parent_id=job.get("id"),
                            reason=f"Auto-triggered by gpp_extract: Testing GPP credentials for Kerberoastable accounts",
                            rule_id=-14,  # Smart chain: gpp_extract → GetUserSPNs
                        )
                        job_ids.append(job_id)
                        logger.info(
                            f"  Chained: gpp_extract → GetUserSPNs (Kerberoasting) job #{job_id}"
                        )

                    # Chain 2: CrackMapExec SMB to test credential access
                    cme_args = ["-u", clean_username, "-p", password]
                    if domain:
                        cme_args.extend(["-d", domain])

                    job_id = enqueue_job(
                        tool="crackmapexec",
                        target=target,
                        args=["smb", target] + cme_args,
                        label="gpp_extract",
                        engagement_id=engagement_id,
                        parent_id=job.get("id"),
                        reason=f"Auto-triggered by gpp_extract: Testing GPP credentials on SMB",
                        rule_id=-15,  # Smart chain: gpp_extract → crackmapexec
                    )
                    job_ids.append(job_id)
                    logger.info(
                        f"  Chained: gpp_extract → crackmapexec (SMB auth test) job #{job_id}"
                    )

                return job_ids

            # === GetUserSPNs → hashcat for Kerberos TGS hash cracking ===
            elif tool == "impacket-getuserspns":
                hashes = parse_results.get("hashes", [])

                if hashes:
                    import os
                    import tempfile

                    from souleyez.engine.background import enqueue_job
                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)
                    logger.info(
                        f"GetUserSPNs found {len(hashes)} Kerberos TGS hash(es), chaining to hashcat..."
                    )

                    # Write hashes to temp file
                    fd, hash_file = tempfile.mkstemp(
                        suffix=".txt", prefix="kerberos_tgs_"
                    )
                    with os.fdopen(fd, "w") as f:
                        f.write("\n".join(hashes))

                    logger.info(f"Wrote {len(hashes)} Kerberos hash(es) to {hash_file}")

                    # Chain to hashcat with Kerberos 5 TGS-REP etype 23 mode (13100)
                    # hashcat plugin expects target=hash_file (not IP)
                    # skip_scope_check=True because target is a local file, not network target
                    job_id = enqueue_job(
                        tool="hashcat",
                        target=hash_file,
                        args=[
                            "-m",
                            "13100",
                            "-a",
                            "0",
                            "data/wordlists/passwords_crack.txt",
                        ],
                        label="impacket-getuserspns",
                        engagement_id=engagement_id,
                        parent_id=job.get("id"),
                        reason=f"Auto-triggered by GetUserSPNs: Cracking {len(hashes)} Kerberos TGS hash(es)",
                        rule_id=-16,  # Smart chain: GetUserSPNs → hashcat
                        skip_scope_check=True,  # Local file cracking, not network scan
                    )
                    job_ids.append(job_id)
                    logger.info(
                        f"  Chained: GetUserSPNs → hashcat (Kerberos cracking) job #{job_id}"
                    )

                return job_ids

            # === WPScan special handling for user enumeration → hydra brute-force ===
            elif tool == "wpscan":
                users = parse_results.get("users", [])

                if users:
                    # Create temp file with enumerated WordPress usernames
                    import os
                    import re
                    import tempfile

                    fd, usernames_file = tempfile.mkstemp(
                        suffix=".txt", prefix="wpscan_users_"
                    )
                    with os.fdopen(fd, "w") as f:
                        f.write("\n".join(users))

                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)
                    logger.info(
                        f"WPScan found {len(users)} WordPress users, created temp file: {usernames_file}"
                    )

                    # Normalize target URL to WordPress root (strip wp-includes/, wp-content/, wp-admin/)
                    # This handles cases where wpscan was triggered on a WordPress subpath
                    wp_target = target
                    wp_subpaths = r"/(wp-includes|wp-content|wp-admin)(/.*)?$"
                    if re.search(wp_subpaths, wp_target):
                        wp_target = re.sub(wp_subpaths, "/", wp_target)
                        logger.info(
                            f"Normalized WordPress target: {target} -> {wp_target}"
                        )

                    # Build context with users and usernames_file for hydra chaining
                    context = {
                        "target": wp_target,
                        "tool": tool,
                        "users": users,
                        "usernames_file": usernames_file,
                        "findings": parse_results.get("findings", []),
                    }

                    # Evaluate chains - will match has:users condition
                    commands = self.evaluate_chains(tool, context)

                    # Replace {usernames_file} placeholder in args
                    for cmd in commands:
                        cmd["args"] = [
                            usernames_file if arg == "{usernames_file}" else arg
                            for arg in cmd.get("args", [])
                        ]

                    job_ids.extend(
                        self._enqueue_commands(
                            commands,
                            tool,
                            engagement_id,
                            wp_target,
                            parent_job_id=job.get("id"),
                        )
                    )

                return job_ids

            # === Hydra special handling for username enumeration → password attack ===
            elif tool == "hydra":
                usernames = parse_results.get("usernames", [])

                if usernames:
                    # Create temp file with validated usernames
                    import os
                    import tempfile

                    fd, usernames_file = tempfile.mkstemp(
                        suffix=".txt", prefix="hydra_users_"
                    )
                    with os.fdopen(fd, "w") as f:
                        f.write("\n".join(usernames))

                    from souleyez.log_config import get_logger

                    logger = get_logger(__name__)
                    logger.info(
                        f"Hydra found {len(usernames)} valid usernames, created temp file: {usernames_file}"
                    )

                    # Build context with usernames
                    context = {
                        "target": target,
                        "tool": tool,
                        "usernames": usernames,
                        "usernames_file": usernames_file,
                        "findings": parse_results.get("findings", []),
                    }

                    # Evaluate chains - will match has:usernames condition
                    commands = self.evaluate_chains(tool, context)

                    # Replace {usernames_file} placeholder in args
                    for cmd in commands:
                        cmd["args"] = [
                            usernames_file if arg == "{usernames_file}" else arg
                            for arg in cmd.get("args", [])
                        ]

                    job_ids.extend(
                        self._enqueue_commands(
                            commands,
                            tool,
                            engagement_id,
                            target,
                            parent_job_id=job.get("id"),
                        )
                    )

                # === Hydra credentials found → Evil-WinRM shell access ===
                # If Hydra found valid credentials, check if WinRM is available
                credentials = parse_results.get("credentials", [])
                if credentials:
                    from souleyez.engine.background import enqueue_job
                    from souleyez.log_config import get_logger
                    from souleyez.storage.hosts import HostManager

                    logger = get_logger(__name__)

                    try:
                        host_manager = HostManager()
                        # Extract host from target (could be host:port format)
                        target_host = target.split(":")[0] if ":" in target else target

                        # Check if WinRM port is open on this host
                        host = host_manager.get_host_by_ip(engagement_id, target_host)
                        if host:
                            services = host_manager.get_host_services(host["id"])
                            winrm_svc = next(
                                (s for s in services if s.get("port") in [5985, 5986]),
                                None,
                            )

                            if winrm_svc:
                                # WinRM is available - create Evil-WinRM job
                                for cred in credentials:  # Process all credentials
                                    username = cred.get("username")
                                    password = cred.get("password")

                                    if username and password:
                                        # Check if chains already ran for this user
                                        from souleyez.storage.database import Database

                                        try:
                                            db = Database()
                                            existing = db.execute(
                                                """SELECT id FROM jobs WHERE engagement_id = ?
                                                   AND tool = 'evil_winrm' AND args LIKE ?
                                                   AND status != 'killed' LIMIT 1""",
                                                (engagement_id, f'%-u", "{username}%'),
                                            )
                                            if existing:
                                                continue
                                        except Exception:
                                            pass

                                        winrm_port = winrm_svc.get("port", 5985)
                                        # Use -c 'whoami' to test auth (no TTY in background jobs)
                                        evil_winrm_args = [
                                            "-u",
                                            username,
                                            "-p",
                                            password,
                                            "-P",
                                            str(winrm_port),
                                            "-c",
                                            "whoami",
                                        ]

                                        if winrm_port == 5986:
                                            evil_winrm_args.append("-s")

                                        winrm_job_id = enqueue_job(
                                            tool="evil_winrm",
                                            target=target_host,
                                            args=evil_winrm_args,
                                            label="hydra",
                                            engagement_id=engagement_id,
                                            parent_id=job.get("id"),
                                            reason=f"Auto-triggered by hydra: Testing WinRM shell access with {username}",
                                            rule_id=-26,  # Smart chain: hydra → evil_winrm
                                        )
                                        job_ids.append(winrm_job_id)
                                        logger.info(
                                            f"  Evil-WinRM job #{winrm_job_id} for {username}"
                                        )
                    except Exception as e:
                        logger.debug(f"Evil-WinRM chain check failed: {e}")

                # NOTE: SSH shell chain removed - spawn shell directly from Hydra job via [s] option

                return job_ids

            # === NetExec (nxc) credential chain: valid creds → evil_winrm, Kerberoasting, secretsdump ===
            elif tool == "nxc":
                from souleyez.engine.background import enqueue_job
                from souleyez.log_config import get_logger
                from souleyez.storage.hosts import HostManager

                logger = get_logger(__name__)
                logger.info(
                    "nxc smart chain block reached - evaluating credential chains"
                )

                # Skip credential chains for auth_shares jobs (they're terminal - prevents loop)
                job_label = job.get("label", "")
                if job_label == "nxc_auth_shares":
                    logger.debug(
                        "Skipping credential chains for nxc_auth_shares job (terminal action)"
                    )
                    return job_ids

                credentials = parse_results.get("credentials", [])
                expired_credentials = parse_results.get("expired_credentials", [])
                is_pwned = parse_results.get("is_pwned", False)
                domain = parse_results.get("domain", "")

                logger.info(
                    f"nxc: found {len(credentials)} credentials, is_pwned={is_pwned}, domain={domain}"
                )

                # Log expired credentials prominently
                if expired_credentials:
                    for cred in expired_credentials:
                        logger.warning(
                            f"nxc: EXPIRED CREDENTIAL - {cred.get('domain')}\\{cred.get('username')} "
                            f"(use smbpasswd to change password)"
                        )

                # Chain on valid credentials
                if credentials:
                    try:
                        host_manager = HostManager()
                        target_host = target.split(":")[0] if ":" in target else target
                        logger.info(
                            f"nxc: looking up host {target_host} in engagement {engagement_id}"
                        )

                        host = host_manager.get_host_by_ip(engagement_id, target_host)
                        logger.info(f"nxc: host lookup result: {host}")
                        if host:
                            services = host_manager.get_host_services(host["id"])
                            winrm_svc = next(
                                (s for s in services if s.get("port") in [5985, 5986]),
                                None,
                            )
                            kerberos_svc = next(
                                (s for s in services if s.get("port") == 88), None
                            )

                            # Track processed usernames/domains to avoid duplicates within this evaluation
                            processed_users = set()
                            processed_domains = set()  # For bloodhound (one per domain)

                            # Check jobs JSON for users/domains that already have chain jobs
                            # IMPORTANT: Also check target IP to avoid cross-IP deduplication
                            try:
                                from souleyez.engine.background import get_all_jobs

                                all_jobs = get_all_jobs()
                                for j in all_jobs:
                                    if (
                                        j.get("engagement_id") != engagement_id
                                        or j.get("status") == "killed"
                                    ):
                                        continue
                                    # Only dedupe jobs for the SAME target IP
                                    job_target = j.get("target", "")
                                    if job_target != target_host:
                                        continue
                                    # Extract usernames from existing evil_winrm jobs
                                    if j.get("tool") == "evil_winrm":
                                        args = j.get("args", [])
                                        if isinstance(args, list):
                                            for i, arg in enumerate(args):
                                                if arg == "-u" and i + 1 < len(args):
                                                    processed_users.add(args[i + 1])
                                                    break
                                    # Extract domains from existing bloodhound jobs
                                    if j.get("tool") == "bloodhound":
                                        args = j.get("args", [])
                                        if isinstance(args, list):
                                            for i, arg in enumerate(args):
                                                if arg == "-d" and i + 1 < len(args):
                                                    processed_domains.add(args[i + 1])
                                                    break
                                if processed_users:
                                    logger.debug(
                                        f"Users with existing chains: {processed_users}"
                                    )
                                if processed_domains:
                                    logger.debug(
                                        f"Domains with existing bloodhound: {processed_domains}"
                                    )
                            except Exception as e:
                                logger.debug(f"Could not check existing jobs: {e}")

                            for cred in credentials:  # Process all credentials
                                username = cred.get("username")
                                password = cred.get("password")
                                cred_domain = cred.get("domain", domain)

                                if not username or not password:
                                    continue

                                # Skip if already processed (either from DB or this evaluation)
                                if username in processed_users:
                                    logger.debug(
                                        f"Credential chains already exist for {username}, skipping"
                                    )
                                    continue

                                # Mark as processed for this evaluation
                                processed_users.add(username)

                                # Chain 1: Evil-WinRM if WinRM is open
                                if winrm_svc:
                                    winrm_port = winrm_svc.get("port", 5985)
                                    # Use -c 'whoami' to test auth (no TTY in background jobs)
                                    evil_winrm_args = [
                                        "-u",
                                        username,
                                        "-p",
                                        password,
                                        "-P",
                                        str(winrm_port),
                                        "-c",
                                        "whoami",
                                    ]

                                    if winrm_port == 5986:
                                        evil_winrm_args.append("-s")

                                    winrm_job_id = enqueue_job(
                                        tool="evil_winrm",
                                        target=target_host,
                                        args=evil_winrm_args,
                                        label="nxc",
                                        engagement_id=engagement_id,
                                        parent_id=job.get("id"),
                                        reason=f"Auto-triggered by nxc: Testing WinRM shell with {cred_domain}\\{username}",
                                        rule_id=-50,  # Smart chain: nxc → evil_winrm
                                    )
                                    job_ids.append(winrm_job_id)
                                    logger.info(
                                        f"  Chained: nxc → evil_winrm job #{winrm_job_id} ({username})"
                                    )

                                # Chain 2: Kerberoasting if Kerberos is available
                                if kerberos_svc and cred_domain:
                                    kerberoast_job_id = enqueue_job(
                                        tool="impacket-GetUserSPNs",
                                        target=target_host,
                                        args=[
                                            f"{cred_domain}/{username}:{password}",
                                            "-dc-ip",
                                            target_host,
                                            "-request",
                                        ],
                                        label="nxc",
                                        engagement_id=engagement_id,
                                        parent_id=job.get("id"),
                                        reason=f"Auto-triggered by nxc: Kerberoasting with {cred_domain}\\{username}",
                                        rule_id=-51,  # Smart chain: nxc → Kerberoasting
                                    )
                                    job_ids.append(kerberoast_job_id)
                                    logger.info(
                                        f"  Chained: nxc → Kerberoasting job #{kerberoast_job_id}"
                                    )

                                # Chain 3: secretsdump if Pwn3d (admin access)
                                if is_pwned:
                                    secretsdump_job_id = enqueue_job(
                                        tool="impacket_secretsdump",
                                        target=target_host,
                                        args=[
                                            f"{cred_domain}/{username}:{password}@{target_host}"
                                        ],
                                        label="nxc",
                                        engagement_id=engagement_id,
                                        parent_id=job.get("id"),
                                        reason=f"Auto-triggered by nxc Pwn3d!: Dumping secrets with admin {username}",
                                        rule_id=-52,  # Smart chain: nxc (pwned) → secretsdump
                                    )
                                    job_ids.append(secretsdump_job_id)
                                    logger.info(
                                        f"  Chained: nxc (Pwn3d!) → secretsdump job #{secretsdump_job_id}"
                                    )

                                # Chain 4: Certipy ADCS enumeration if domain available
                                if cred_domain:
                                    certipy_job_id = enqueue_job(
                                        tool="certipy",
                                        target=target_host,
                                        args=[
                                            "find",
                                            "-u",
                                            f"{username}@{cred_domain}",
                                            "-p",
                                            password,
                                            "-dc-ip",
                                            target_host,
                                            "-vulnerable",
                                        ],
                                        label="nxc",
                                        engagement_id=engagement_id,
                                        parent_id=job.get("id"),
                                        reason=f"Auto-triggered by nxc: ADCS enumeration with {cred_domain}\\{username}",
                                        rule_id=-54,  # Smart chain: nxc → certipy (ADCS)
                                    )
                                    job_ids.append(certipy_job_id)
                                    logger.info(
                                        f"  Chained: nxc → certipy (ADCS) job #{certipy_job_id}"
                                    )

                                # Chain 5: Authenticated share enumeration
                                # Re-enumerate shares with valid creds (may find more than guest)
                                auth_shares_job_id = enqueue_job(
                                    tool="nxc",
                                    target=target_host,
                                    args=[
                                        "smb",
                                        target_host,
                                        "-u",
                                        username,
                                        "-p",
                                        password,
                                        "--shares",
                                    ],
                                    label="nxc_auth_shares",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by nxc: Authenticated share enum with {cred_domain}\\{username}",
                                    rule_id=-55,  # Smart chain: nxc → authenticated shares
                                )
                                job_ids.append(auth_shares_job_id)
                                logger.info(
                                    f"  Chained: nxc → authenticated shares job #{auth_shares_job_id}"
                                )

                                # Chain 6: BloodHound AD collection if domain available
                                # Only run once per domain per engagement (deduplication)
                                if cred_domain and cred_domain not in processed_domains:
                                    # Mark domain as processed for this evaluation
                                    processed_domains.add(cred_domain)
                                    bloodhound_job_id = enqueue_job(
                                        tool="bloodhound",
                                        target=target_host,
                                        args=[
                                            "-u",
                                            username,
                                            "-p",
                                            password,
                                            "-d",
                                            cred_domain,
                                            "-ns",
                                            target_host,
                                            "-c",
                                            "All",
                                            "--zip",
                                        ],
                                        label="nxc",
                                        engagement_id=engagement_id,
                                        parent_id=job.get("id"),
                                        reason=f"Auto-triggered by nxc: BloodHound AD collection with {cred_domain}\\{username}",
                                        rule_id=-56,  # Smart chain: nxc → bloodhound
                                    )
                                    job_ids.append(bloodhound_job_id)
                                    logger.info(
                                        f"  Chained: nxc → bloodhound job #{bloodhound_job_id}"
                                    )
                                elif cred_domain in processed_domains:
                                    logger.debug(
                                        f"BloodHound already scheduled for domain {cred_domain}, skipping"
                                    )

                    except Exception as e:
                        logger.debug(f"nxc credential chain failed: {e}")

                # Chain on readable/writable shares - spider for usernames
                # BUT skip if this is an authenticated share enum job (prevents loop)
                job_label = job.get("label", "")
                if job_label == "nxc_auth_shares":
                    logger.debug(
                        "Skipping smbclient spider for nxc_auth_shares job (prevents loop)"
                    )
                    return job_ids

                readable_shares = parse_results.get("readable_shares", [])
                writable_shares = parse_results.get("writable_shares", [])

                if readable_shares or writable_shares:
                    # Skip default admin shares - focus on custom/interesting shares
                    skip_shares = {"ADMIN$", "C$", "IPC$"}
                    # User home shares that likely contain usernames as directories
                    home_shares = {"homes", "users", "home", "profiles", "Users"}

                    # Combine readable and writable, prioritizing writable
                    all_shares = {s["name"]: s for s in readable_shares}
                    for s in writable_shares:
                        all_shares[s["name"]] = s  # Overwrite with writable version

                    for share_name, share in all_shares.items():
                        if not share_name or share_name in skip_shares:
                            continue

                        # Spider share with smbclient to list contents
                        spider_job_id = enqueue_job(
                            tool="smbclient",
                            target=target,
                            args=[
                                f"//{target}/{share_name}",
                                "-U",
                                "guest%",
                                "-c",
                                "ls",
                            ],
                            label="nxc",
                            engagement_id=engagement_id,
                            parent_id=job.get("id"),
                            reason=f"Auto-triggered by nxc: Share '{share_name}' accessible - extracting contents/usernames",
                            rule_id=-53,  # Smart chain: nxc → smbclient (share spider)
                        )
                        job_ids.append(spider_job_id)
                        logger.info(
                            f"  Chained: nxc → smbclient (spider {share_name} share) job #{spider_job_id}"
                        )

                        # Flag homes-type shares for username extraction
                        if share_name.lower() in [s.lower() for s in home_shares]:
                            logger.info(
                                f"    '{share_name}' is a home directory share - usernames will be extracted for spray"
                            )

                return job_ids

            # === Responder special handling: NTLMv2 hashes → hashcat ===
            elif tool == "responder":
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                hash_files = parse_results.get("hash_files", [])
                creds_captured = parse_results.get("credentials_captured", 0)

                if hash_files and creds_captured > 0:
                    logger.info(
                        f"Responder captured {creds_captured} NTLMv2 hash(es), chaining to hashcat"
                    )

                    from souleyez.engine.background import enqueue_job

                    # Use the first hash file (they're typically consolidated)
                    hash_file = hash_files[0]

                    # Run hashcat with NTLMv2 mode (5600)
                    hashcat_job_id = enqueue_job(
                        tool="hashcat",
                        target=hash_file,
                        args=[
                            "-m",
                            "5600",
                            hash_file,
                            "--wordlist",
                            "passwords_crack.txt",
                        ],
                        label="responder",
                        engagement_id=engagement_id,
                        parent_id=job.get("id"),
                        reason=f"Auto-triggered by Responder: Cracking {creds_captured} captured NTLMv2 hash(es)",
                        rule_id=-20,  # Smart chain: responder → hashcat
                        metadata={"hash_file": hash_file, "hash_mode": "5600"},
                    )
                    job_ids.append(hashcat_job_id)
                    logger.info(f"  Chained: Responder → hashcat job #{hashcat_job_id}")

                return job_ids

            # === Hashcat special handling: cracked password → Evil-WinRM/CME access ===
            elif tool == "hashcat":
                from souleyez.engine.background import enqueue_job
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                cracked = parse_results.get("cracked", [])
                cracked_count = parse_results.get("cracked_count", 0)
                hashcat_status = parse_results.get("hashcat_status", "unknown")

                # Trigger chain if we have cracked passwords (don't require specific status)
                # Status could be 'cracked', 'exhausted', or even 'unknown' if parsing was incomplete
                if cracked or cracked_count > 0:
                    logger.info(
                        f"Hashcat cracked {len(cracked) or cracked_count} hash(es), checking for access chains"
                    )

                    for cred in cracked:
                        username = cred.get("username", "")
                        password = cred.get("password", "")
                        hash_type = cred.get("hash_type", "unknown")

                        if not username or not password:
                            continue

                        logger.info(
                            f"  Cracked: {username}:{password} (type: {hash_type})"
                        )

                        # Try to find the original target host from parent job chain
                        # Walk up the parent chain to find a network target
                        target_host = None
                        domain = None
                        current_job = job

                        while current_job and not target_host:
                            parent_target = current_job.get("target", "")
                            # Skip file paths, look for IPs or hostnames
                            if (
                                parent_target
                                and not parent_target.startswith("/")
                                and not parent_target.startswith("file:")
                            ):
                                # Extract host from URL if needed
                                import re

                                ip_match = re.search(
                                    r"(\d+\.\d+\.\d+\.\d+)", parent_target
                                )
                                if ip_match:
                                    target_host = ip_match.group(1)
                                elif not parent_target.startswith("http"):
                                    target_host = parent_target

                            # Check for domain in job metadata
                            if not domain:
                                domain = current_job.get("metadata", {}).get("domain")

                            # Get parent job
                            parent_id = current_job.get("parent_id")
                            if parent_id:
                                try:
                                    from souleyez.engine.background import get_job

                                    current_job = get_job(parent_id)
                                except Exception:
                                    break
                            else:
                                break

                        if not target_host:
                            logger.debug(
                                f"Could not find network target from job chain for {username}"
                            )
                            continue

                        logger.info(f"  Target host for access test: {target_host}")

                        # Check for WinRM service on target
                        try:
                            from souleyez.storage.hosts import HostManager

                            hm = HostManager()
                            host = hm.get_host_by_ip(engagement_id, target_host)
                            services = []
                            if host:
                                services = hm.get_host_services(host.get("id"))

                            winrm_svc = next(
                                (s for s in services if s.get("port") in [5985, 5986]),
                                None,
                            )
                            smb_svc = next(
                                (s for s in services if s.get("port") == 445), None
                            )

                            if winrm_svc:
                                winrm_port = winrm_svc.get("port", 5985)
                                logger.info(
                                    f"  WinRM found on port {winrm_port}, chaining evil-winrm"
                                )

                                # Use -c 'whoami' to test auth (no TTY in background jobs)
                                evil_winrm_args = [
                                    "-u",
                                    username,
                                    "-p",
                                    password,
                                    "-P",
                                    str(winrm_port),
                                    "-c",
                                    "whoami",
                                ]
                                if winrm_port == 5986:
                                    evil_winrm_args.append("-s")

                                winrm_job_id = enqueue_job(
                                    tool="evil_winrm",
                                    target=target_host,
                                    args=evil_winrm_args,
                                    label="hashcat",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by hashcat: Testing WinRM access with cracked credential {username}",
                                    rule_id=-17,  # Smart chain: hashcat → evil_winrm
                                )
                                job_ids.append(winrm_job_id)
                                logger.info(
                                    f"  Chained: hashcat → evil-winrm job #{winrm_job_id}"
                                )
                            elif smb_svc:
                                # No WinRM, try CME with the cracked credential
                                logger.info(
                                    f"  SMB found, chaining crackmapexec for access test"
                                )
                                cme_job_id = enqueue_job(
                                    tool="crackmapexec",
                                    target=target_host,
                                    args=["smb", "-u", username, "-p", password],
                                    label="hashcat",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by hashcat: Testing SMB access with cracked credential {username}",
                                    rule_id=-18,  # Smart chain: hashcat → crackmapexec
                                )
                                job_ids.append(cme_job_id)
                                logger.info(
                                    f"  Chained: hashcat → crackmapexec job #{cme_job_id}"
                                )
                            elif hash_type == "kerberos":
                                # Kerberos hash means Windows/AD target - try CME anyway
                                logger.info(
                                    f"  Kerberos hash, trying crackmapexec without service check"
                                )
                                cme_job_id = enqueue_job(
                                    tool="crackmapexec",
                                    target=target_host,
                                    args=["smb", "-u", username, "-p", password],
                                    label="hashcat",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by hashcat: Testing SMB access with cracked Kerberos credential {username}",
                                    rule_id=-18,
                                )
                                job_ids.append(cme_job_id)
                                logger.info(
                                    f"  Chained: hashcat → crackmapexec job #{cme_job_id}"
                                )
                            else:
                                # Check if this came from sqlmap (web app credentials)
                                # Walk up parent chain to find sqlmap job
                                is_web_app_cred = False
                                web_target_url = None
                                check_job = job

                                while check_job:
                                    parent_id = check_job.get("parent_id")
                                    if not parent_id:
                                        break
                                    try:
                                        parent_job = get_job(parent_id)
                                        if (
                                            parent_job
                                            and parent_job.get("tool") == "sqlmap"
                                        ):
                                            is_web_app_cred = True
                                            # Get the web URL from sqlmap target
                                            web_target_url = parent_job.get(
                                                "target", ""
                                            )
                                            break
                                        check_job = parent_job
                                    except Exception:
                                        break

                                if is_web_app_cred and web_target_url:
                                    logger.info(
                                        f"  Web app credential from sqlmap, searching for login endpoints"
                                    )

                                    # Extract base URL
                                    from urllib.parse import urlparse

                                    parsed_url = urlparse(web_target_url)
                                    base_url = (
                                        f"{parsed_url.scheme}://{parsed_url.netloc}"
                                    )

                                    # Look for login endpoints in discovered paths
                                    login_paths = []
                                    try:
                                        from souleyez.storage.attack_surface import (
                                            AttackSurfaceManager,
                                        )

                                        asm = AttackSurfaceManager()
                                        paths = asm.get_discovered_paths(
                                            engagement_id, target_host
                                        )

                                        # Common login path patterns
                                        login_patterns = [
                                            r"/login",
                                            r"/signin",
                                            r"/auth",
                                            r"/api/login",
                                            r"/api/auth",
                                            r"/rest/user/login",
                                            r"/user/login",
                                            r"/account/login",
                                            r"/session",
                                        ]

                                        for path in paths:
                                            path_url = path.get("url", "").lower()
                                            for pattern in login_patterns:
                                                if pattern in path_url:
                                                    login_paths.append(path.get("url"))
                                                    break
                                    except Exception as e:
                                        logger.debug(f"Could not search paths: {e}")

                                    # If no login paths found, try common defaults
                                    # Prioritize based on sqlmap target URL patterns
                                    if not login_paths:
                                        is_rest_api = "/rest/" in web_target_url.lower()
                                        is_api = "/api/" in web_target_url.lower()

                                        if is_rest_api:
                                            # REST API detected - prioritize REST endpoints
                                            login_paths = [
                                                f"{base_url}/rest/user/login",
                                                f"{base_url}/api/login",
                                                f"{base_url}/login",
                                            ]
                                            logger.info(
                                                f"  REST API detected, trying REST endpoints first"
                                            )
                                        elif is_api:
                                            # Generic API detected
                                            login_paths = [
                                                f"{base_url}/api/login",
                                                f"{base_url}/api/auth/login",
                                                f"{base_url}/login",
                                            ]
                                            logger.info(
                                                f"  API detected, trying API endpoints first"
                                            )
                                        else:
                                            # Traditional web app
                                            login_paths = [
                                                f"{base_url}/login",
                                                f"{base_url}/api/login",
                                                f"{base_url}/rest/user/login",
                                            ]
                                            logger.info(
                                                f"  No login paths discovered, trying defaults"
                                            )

                                    # Queue hydra for the first login path found
                                    if login_paths:
                                        login_url = login_paths[0]
                                        logger.info(
                                            f"  Testing cracked credential against {login_url}"
                                        )

                                        # Use web_login_test built-in tool for credential validation
                                        # Determine if JSON API or form-based
                                        if (
                                            "/rest/" in login_url
                                            or "/api/" in login_url
                                        ):
                                            # JSON API - use web_login_test with JSON format
                                            test_args = [
                                                "--username",
                                                username,
                                                "--password",
                                                password,
                                            ]
                                        else:
                                            # Traditional form - use web_login_test with --form flag
                                            test_args = [
                                                "--username",
                                                username,
                                                "--password",
                                                password,
                                                "--form",
                                            ]

                                        test_job_id = enqueue_job(
                                            tool="web_login_test",
                                            target=login_url,
                                            args=test_args,
                                            label="hashcat",
                                            engagement_id=engagement_id,
                                            parent_id=job.get("id"),
                                            reason=f"Auto-triggered by hashcat: Testing web login with cracked credential {username}",
                                            rule_id=-61,  # Smart chain: hashcat → web login test
                                            skip_scope_check=True,
                                        )
                                        job_ids.append(test_job_id)
                                        logger.info(
                                            f"  Chained: hashcat → web_login_test job #{test_job_id}"
                                        )

                        except Exception as e:
                            logger.debug(f"Hashcat access chain check failed: {e}")

                return job_ids

            # All other tools (nmap, gobuster, nuclei, etc.)
            else:
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)

                # Enrich context with services from database for port-based chain conditions
                # This allows chains like "crackmapexec has:domains & port:445 → Zerologon"
                services_from_db = []
                host_manager = None
                credentials_manager = None
                try:
                    from souleyez.storage.credentials import CredentialsManager
                    from souleyez.storage.hosts import HostManager

                    host_manager = HostManager()
                    credentials_manager = CredentialsManager()
                    host = host_manager.get_host_by_ip(engagement_id, target)
                    if host:
                        db_services = host_manager.get_host_services(host["id"])
                        for svc in db_services:
                            services_from_db.append(
                                {
                                    "port": svc.get("port"),
                                    "service_name": svc.get("service")
                                    or svc.get("name", ""),
                                    "state": svc.get("state", "open"),
                                    "protocol": svc.get("protocol", "tcp"),
                                }
                            )
                except Exception as e:
                    logger.debug(f"Could not enrich services from DB: {e}")

                context = {
                    "target": target,
                    "tool": tool,
                    "services": services_from_db,  # Enriched from database
                    "findings": parse_results.get("findings", []),
                    "hosts": parse_results.get("hosts", []),
                    "writable_shares": parse_results.get("writable_shares", []),
                    "readable_shares": parse_results.get("readable_shares", []),
                    "paths_with_params": parse_results.get("paths_with_params", []),
                    "domains": parse_results.get("domains", []),
                    "subdomains": parse_results.get("subdomains", []),
                    "base_dn": parse_results.get(
                        "base_dn", ""
                    ),  # For LDAP user enumeration
                }

                # Debug logging for AD-related tools
                if tool in ["ldapsearch", "enum4linux", "crackmapexec"]:
                    domains = context.get("domains", [])
                    logger.info(
                        f"auto_chain({tool}): domains={domains}, "
                        f"readable_shares={len(context.get('readable_shares', []))}"
                    )

                # === ldapsearch credential-based chains ===
                # When domain discovered, use stored credentials for authenticated enumeration
                if tool == "ldapsearch":
                    base_dn = parse_results.get("base_dn", "")
                    domains = parse_results.get("domains", [])

                    # If domain discovered, try authenticated ldapsearch with stored creds
                    if (base_dn or domains) and credentials_manager and host_manager:
                        host = host_manager.get_host_by_ip(engagement_id, target)
                        if host:
                            # Get valid AD credentials from database
                            stored_creds = credentials_manager.list_credentials(
                                engagement_id, host_id=host["id"]
                            )
                            valid_ad_creds = [
                                c
                                for c in stored_creds
                                if c.get("status") == "valid"
                                and c.get("service") in ["smb", "ldap", "kerberos"]
                            ]

                            if valid_ad_creds:
                                cred = valid_ad_creds[
                                    0
                                ]  # Use first valid AD credential
                                username = cred.get("username", "")
                                password = cred.get("password", "")
                                cred_domain = (
                                    cred.get("notes", "").split("domain:")[-1].strip()
                                    if "domain:" in cred.get("notes", "")
                                    else ""
                                )

                                # Extract domain from base_dn if not in notes
                                if not cred_domain and base_dn:
                                    dc_parts = [
                                        p.split("=")[1]
                                        for p in base_dn.split(",")
                                        if p.startswith("DC=")
                                    ]
                                    cred_domain = ".".join(dc_parts) if dc_parts else ""

                                if username and password:
                                    # Construct authenticated ldapsearch for user enumeration
                                    bind_dn = (
                                        f"{username}@{cred_domain}"
                                        if cred_domain
                                        else username
                                    )
                                    ldap_base_dn = (
                                        base_dn
                                        if base_dn
                                        else ",".join(
                                            [f"DC={d}" for d in cred_domain.split(".")]
                                        )
                                    )

                                    from souleyez.engine.background import enqueue_job

                                    auth_ldap_job_id = enqueue_job(
                                        tool="ldapsearch",
                                        target=target,
                                        args=[
                                            "-x",
                                            "-H",
                                            f"ldap://{target}",
                                            "-D",
                                            bind_dn,
                                            "-w",
                                            password,
                                            "-b",
                                            ldap_base_dn,
                                            "(objectClass=user)",
                                            "sAMAccountName",
                                            "description",
                                            "memberOf",
                                        ],
                                        label="ldapsearch",
                                        engagement_id=engagement_id,
                                        parent_id=job.get("id"),
                                        reason=f"Auto-triggered by ldapsearch: Authenticated user enumeration with {username}",
                                        rule_id=-54,  # Smart chain: ldapsearch → authenticated ldapsearch
                                    )
                                    job_ids.append(auth_ldap_job_id)
                                    logger.info(
                                        f"  Chained: ldapsearch → authenticated ldapsearch job #{auth_ldap_job_id}"
                                    )

                    # When credentials are found in LDAP user descriptions, test them
                    credentials_found = parse_results.get("credentials_found", [])
                    if credentials_found:
                        logger.info(
                            f"ldapsearch found {len(credentials_found)} credential(s) in user descriptions!"
                        )

                        # Get available services from the parent nmap scan
                        from souleyez.storage.hosts import HostManager

                        host_manager = HostManager()
                        host = host_manager.get_host_by_ip(engagement_id, target)
                        services = []
                        if host:
                            services = host_manager.get_host_services(host["id"])

                        # Check for WinRM service
                        winrm_svc = next(
                            (s for s in services if s.get("port") in [5985, 5986]), None
                        )
                        smb_svc = next(
                            (s for s in services if s.get("port") == 445), None
                        )

                        for cred in credentials_found:
                            username = cred.get("username", "")
                            password = cred.get("password", "")

                            if not username or not password:
                                continue

                            # Chain 1: Test with netexec WinRM if WinRM is available
                            if winrm_svc:
                                from souleyez.engine.background import enqueue_job

                                winrm_job_id = enqueue_job(
                                    tool="nxc",
                                    target=target,
                                    args=[
                                        "winrm",
                                        target,
                                        "-u",
                                        username,
                                        "-p",
                                        password,
                                        "-x",
                                        "whoami",
                                    ],
                                    label="ldapsearch",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by ldapsearch: Testing credential from user description ({username})",
                                    rule_id=-31,  # Smart chain: ldapsearch → nxc winrm
                                )
                                job_ids.append(winrm_job_id)
                                logger.info(
                                    f"  Chained: ldapsearch → nxc winrm job #{winrm_job_id} ({username})"
                                )

                            # Chain 2: Test with CrackMapExec SMB if SMB is available
                            if smb_svc:
                                from souleyez.engine.background import enqueue_job

                                cme_job_id = enqueue_job(
                                    tool="crackmapexec",
                                    target=target,
                                    args=[
                                        "smb",
                                        target,
                                        "-u",
                                        username,
                                        "-p",
                                        password,
                                    ],
                                    label="ldapsearch",
                                    engagement_id=engagement_id,
                                    parent_id=job.get("id"),
                                    reason=f"Auto-triggered by ldapsearch: Testing credential from user description ({username})",
                                    rule_id=-32,  # Smart chain: ldapsearch → crackmapexec
                                )
                                job_ids.append(cme_job_id)
                                logger.info(
                                    f"  Chained: ldapsearch → crackmapexec job #{cme_job_id} ({username})"
                                )

                            # Chain 3: Kerberoasting with discovered credentials
                            # Now that we have valid creds, check for service accounts with SPNs
                            base_dn = parse_results.get("base_dn", "")
                            if base_dn:
                                # Extract domain from base_dn (DC=baby2,DC=vl -> baby2.vl)
                                dc_parts = [
                                    p.split("=")[1]
                                    for p in base_dn.split(",")
                                    if p.startswith("DC=")
                                ]
                                domain = ".".join(dc_parts) if dc_parts else ""
                                if domain:
                                    from souleyez.engine.background import enqueue_job

                                    spn_job_id = enqueue_job(
                                        tool="impacket-GetUserSPNs",
                                        target=target,
                                        args=[
                                            f"{domain}/{username}",
                                            "-dc-ip",
                                            target,
                                            "-p",
                                            password,
                                            "-request",
                                        ],
                                        label="ldapsearch",
                                        engagement_id=engagement_id,
                                        parent_id=job.get("id"),
                                        reason=f"Auto-triggered by ldapsearch: Kerberoasting with credential {username}",
                                        rule_id=-41,  # Smart chain: ldapsearch → Kerberoasting
                                    )
                                    job_ids.append(spn_job_id)
                                    logger.info(
                                        f"  Chained: ldapsearch → Kerberoasting job #{spn_job_id} ({username})"
                                    )

                        # Chain 4: Password spray - test found password against ALL discovered users
                        # "Initial password" scenarios often mean ALL users were given the same password
                        all_users = parse_results.get("users", [])
                        if all_users and credentials_found:
                            # Use the first found password for spraying
                            spray_password = credentials_found[0].get("password", "")
                            if spray_password and len(all_users) > 1:
                                # Create temporary user list file
                                import os
                                import tempfile

                                # Write users to temp file
                                users_file = os.path.join(
                                    tempfile.gettempdir(),
                                    f'ldap_users_{engagement_id}_{job.get("id", 0)}.txt',
                                )
                                with open(users_file, "w") as f:
                                    for user in all_users:
                                        if user:  # Skip empty usernames
                                            f.write(f"{user}\n")

                                logger.info(
                                    f"  Password spray: {len(all_users)} users with password from description"
                                )

                                # SMB password spray with crackmapexec
                                if smb_svc:
                                    from souleyez.engine.background import enqueue_job

                                    spray_job_id = enqueue_job(
                                        tool="crackmapexec",
                                        target=target,
                                        args=[
                                            "smb",
                                            target,
                                            "-u",
                                            users_file,
                                            "-p",
                                            spray_password,
                                            "--continue-on-success",
                                        ],
                                        label="ldapsearch",
                                        engagement_id=engagement_id,
                                        parent_id=job.get("id"),
                                        reason=f"Auto-triggered by ldapsearch: Spraying password across {len(all_users)} users",
                                        rule_id=-33,  # Smart chain: ldapsearch → password spray (SMB)
                                    )
                                    job_ids.append(spray_job_id)
                                    logger.info(
                                        f"  Chained: ldapsearch → SMB password spray job #{spray_job_id}"
                                    )

                                # WinRM password spray if available
                                if winrm_svc:
                                    from souleyez.engine.background import enqueue_job

                                    winrm_spray_job_id = enqueue_job(
                                        tool="crackmapexec",
                                        target=target,
                                        args=[
                                            "winrm",
                                            target,
                                            "-u",
                                            users_file,
                                            "-p",
                                            spray_password,
                                            "--continue-on-success",
                                        ],
                                        label="ldapsearch",
                                        engagement_id=engagement_id,
                                        parent_id=job.get("id"),
                                        reason=f"Auto-triggered by ldapsearch: Spraying password across {len(all_users)} users (WinRM)",
                                        rule_id=-34,  # Smart chain: ldapsearch → password spray (WinRM)
                                    )
                                    job_ids.append(winrm_spray_job_id)
                                    logger.info(
                                        f"  Chained: ldapsearch → WinRM password spray job #{winrm_spray_job_id}"
                                    )

                # === kerbrute password spray chains ===
                # When kerbrute finds valid users, spray common passwords
                if tool == "kerbrute":
                    users_found = parse_results.get("users", [])
                    if users_found and len(users_found) >= 1:
                        logger.info(
                            f"kerbrute found {len(users_found)} valid user(s) - initiating password spray"
                        )

                        # Get domain info from parse results or job metadata
                        domain = ""
                        dc_ip = target
                        job_args = job.get("args", [])
                        for i, arg in enumerate(job_args):
                            if arg == "-d" and i + 1 < len(job_args):
                                domain = job_args[i + 1]
                            elif arg == "--dc" and i + 1 < len(job_args):
                                dc_ip = job_args[i + 1]

                        if domain:
                            # Create temp file with discovered users
                            import os as os_module
                            import tempfile

                            users_file = os_module.path.join(
                                tempfile.gettempdir(),
                                f'kerbrute_users_{engagement_id}_{job.get("id", 0)}.txt',
                            )
                            with open(users_file, "w") as f:
                                for user in users_found:
                                    if user:
                                        f.write(f"{user}\n")

                            # Spray with kerbrute passwordspray using common AD passwords
                            from souleyez.engine.background import enqueue_job
                            from souleyez.wordlists import resolve_wordlist_path

                            password_wordlist = resolve_wordlist_path(
                                "data/wordlists/passwords_spray.txt"
                            )
                            spray_job_id = enqueue_job(
                                tool="kerbrute",
                                target=target,
                                args=[
                                    "passwordspray",
                                    "-d",
                                    domain,
                                    "--dc",
                                    dc_ip,
                                    users_file,
                                    password_wordlist,
                                ],
                                label="kerbrute",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered by kerbrute: Spraying passwords against {len(users_found)} valid users",
                                rule_id=-40,  # Smart chain: kerbrute → password spray
                            )
                            job_ids.append(spray_job_id)
                            logger.info(
                                f"  Chained: kerbrute → password spray job #{spray_job_id}"
                            )

                            # Username=Password check - very common in AD environments
                            # Users often set their password to match their username
                            from souleyez.engine.background import enqueue_job

                            uname_pwd_job_id = enqueue_job(
                                tool="nxc",
                                target=target,
                                args=[
                                    "smb",
                                    target,
                                    "-u",
                                    users_file,
                                    "-p",
                                    users_file,
                                    "--no-bruteforce",
                                    "--continue-on-success",
                                ],
                                label="kerbrute",
                                engagement_id=engagement_id,
                                parent_id=job.get("id"),
                                reason=f"Auto-triggered by kerbrute: Testing username=password for {len(users_found)} users",
                                rule_id=-42,  # Smart chain: kerbrute → username=password check
                            )
                            job_ids.append(uname_pwd_job_id)
                            logger.info(
                                f"  Chained: kerbrute → username=password check job #{uname_pwd_job_id}"
                            )

                # === smbclient share listing → extract usernames for spray ===
                # When smbclient lists a homes-type share, extract usernames from directories
                if tool == "smbclient":
                    import os as os_module
                    import tempfile

                    # Get extracted usernames from handler's parse_results
                    usernames = parse_results.get("extracted_usernames", [])

                    if usernames:
                        from souleyez.log_config import get_logger

                        logger = get_logger(__name__)
                        share_name = parse_results.get("share_name", "unknown")
                        logger.info(
                            f"smbclient found {len(usernames)} usernames in {share_name}: {usernames}"
                        )

                        # Create user list file
                        users_file = os_module.path.join(
                            tempfile.gettempdir(),
                            f'smb_users_{engagement_id}_{job.get("id", 0)}.txt',
                        )
                        with open(users_file, "w") as f:
                            for user in usernames:
                                f.write(f"{user}\n")

                        # Chain to username=password spray
                        from souleyez.engine.background import enqueue_job

                        spray_job_id = enqueue_job(
                            tool="nxc",
                            target=target,
                            args=[
                                "smb",
                                target,
                                "-u",
                                users_file,
                                "-p",
                                users_file,
                                "--no-bruteforce",
                                "--continue-on-success",
                            ],
                            label="smbclient",
                            engagement_id=engagement_id,
                            parent_id=job.get("id"),
                            reason=f"Auto-triggered by smbclient: Testing username=password for {len(usernames)} users from {share_name}",
                            rule_id=-43,  # Smart chain: smbclient → username=password check
                        )
                        job_ids.append(spray_job_id)
                        logger.info(
                            f"  Chained: smbclient → username=password spray job #{spray_job_id}"
                        )

                    # Check for interesting files (login scripts, GPP files, etc.)
                    interesting_files = parse_results.get("interesting_files", [])
                    if interesting_files:
                        from souleyez.log_config import get_logger

                        logger = get_logger(__name__)
                        for f in interesting_files:
                            logger.warning(
                                f"  Found interesting file: {f['name']} ({f['type']})"
                            )

                commands = self.evaluate_chains(tool, context)

                if tool in ["ldapsearch", "enum4linux", "crackmapexec"]:
                    logger.info(
                        f"auto_chain({tool}): {len(commands)} chain commands generated"
                    )

                job_ids.extend(
                    self._enqueue_commands(
                        commands,
                        tool,
                        engagement_id,
                        target,
                        parent_job_id=job.get("id"),
                    )
                )

                return job_ids

    def _categorize_high_value_directory(self, dir_url: str) -> Dict[str, Any]:
        """
        Categorize a high-value directory to determine appropriate security tools.

        Args:
            dir_url: Full URL to the directory (e.g., http://10.0.0.5/phpmyadmin)

        Returns:
            {
                'category': str,  # database_admin, wordpress, drupal, vulnerable_app, custom_php
                'description': str
            }

        Categories:
            - database_admin: phpMyAdmin, Adminer (CVE + default creds + exploits)
            - wordpress: WordPress sites (WPScan + CVE)
            - drupal: Drupal sites (CVE + exploits)
            - vulnerable_app: DVWA, Mutillidae, Juice Shop (aggressive SQLMap)
            - custom_php: Other PHP apps (standard SQLMap)
        """
        url_lower = dir_url.lower()

        # Database administration panels
        if "phpmyadmin" in url_lower or "adminer" in url_lower or "pma" in url_lower:
            return {
                "category": "database_admin",
                "description": "Database administration panel (phpMyAdmin/Adminer)",
            }

        # WordPress
        if "wordpress" in url_lower or "wp-" in url_lower or "/wp/" in url_lower:
            return {"category": "wordpress", "description": "WordPress CMS"}

        # Drupal
        if "drupal" in url_lower:
            return {"category": "drupal", "description": "Drupal CMS"}

        # Intentionally vulnerable applications (for testing/training)
        vulnerable_app_keywords = [
            "mutillidae",
            "dvwa",
            "bwapp",
            "webgoat",
            "juice",
            "juice-shop",
            "juiceshop",
            "hackazon",
            "pentesterlab",
        ]
        if any(kw in url_lower for kw in vulnerable_app_keywords):
            return {
                "category": "vulnerable_app",
                "description": "Intentionally vulnerable web application",
            }

        # Default: Custom PHP application
        return {"category": "custom_php", "description": "Custom PHP application"}

    def _enqueue_commands(
        self,
        commands: List[Dict[str, Any]],
        source_tool: str,
        engagement_id: Optional[int],
        expected_target: str = None,
        parent_job_id: int = None,
    ) -> List[int]:
        """
        Helper to enqueue commands while avoiding duplicates.

        Args:
            commands: List of command dicts to enqueue
            source_tool: Tool that triggered the chain
            engagement_id: Engagement ID to use
            expected_target: Expected target (for logging)
            parent_job_id: ID of parent job that triggered this chain

        Returns:
            List of new job IDs created
        """

        def _normalize_url(url):
            """Normalize URL for deduplication.

            - Remove trailing dots from hostname (vulnweb.com. -> vulnweb.com)
            - Normalize scheme to https (http -> https for dedup purposes)
            - Remove default ports (:80 for http, :443 for https)
            """
            if not url or "://" not in url:
                return url
            try:
                from urllib.parse import urlparse, urlunparse

                parsed = urlparse(url)

                # Remove trailing dots from hostname
                hostname = parsed.netloc.rstrip(".")

                # Remove default ports (only exact matches for default ports)
                if parsed.scheme == "http" and hostname.endswith(":80"):
                    hostname = hostname[:-3]
                elif parsed.scheme == "https" and hostname.endswith(":443"):
                    hostname = hostname[:-4]

                # Normalize scheme to https for dedup (http://x and https://x are same target)
                scheme = "https"

                return urlunparse(parsed._replace(scheme=scheme, netloc=hostname))
            except Exception:
                return url

        def _normalize_wordpress_url(url):
            """Normalize WordPress URL for deduplication.

            Strips /wp-admin/, /wp-content/, /wp-includes/ to get WordPress root.
            E.g., /blogblog/wp-admin/ -> /blogblog/
            """
            if not url or "://" not in url:
                return url
            try:
                from urllib.parse import urlparse, urlunparse

                parsed = urlparse(url)
                path = parsed.path

                # WordPress subdirectory patterns to strip
                wp_subpaths = [
                    "/wp-admin",
                    "/wp-content",
                    "/wp-includes",
                    "/wp-login.php",
                ]

                for wp_sub in wp_subpaths:
                    idx = path.lower().find(wp_sub.lower())
                    if idx != -1:
                        path = path[:idx]
                        break

                if not path.endswith("/"):
                    path = path + "/"
                if not path:
                    path = "/"

                return urlunparse(parsed._replace(path=path))
            except Exception:
                return url

        job_ids = []

        # Time window for blocking duplicate auto-chains (5 minutes)
        DUPLICATE_WINDOW_SECONDS = 300
        # SQLMap rule-based dedup window (30 minutes) - allows re-running chains after this
        SQLMAP_RULE_DEDUP_SECONDS = 1800

        # === PRE-DEDUPLICATION: Remove duplicate commands within the same batch ===
        # This prevents duplicate rules (e.g., GENERAL + CTF with same condition) from
        # creating multiple identical jobs
        seen_keys = set()
        unique_commands = []
        for cmd in commands:
            cmd_target = cmd.get("target", "")
            # Normalize target for deduplication
            normalized_target = _normalize_url(cmd_target)

            # For wpscan, also normalize WordPress paths (wp-admin, wp-content, wp-includes -> root)
            if cmd.get("tool") == "wpscan":
                normalized_target = _normalize_wordpress_url(normalized_target)

            # Normalize any URLs in args for deduplication key
            normalized_args = tuple(
                _normalize_url(arg) if isinstance(arg, str) and "://" in arg else arg
                for arg in cmd.get("args", [])
            )

            # Build unique key based on tool + target + args
            if cmd.get("tool") == "msf_auxiliary" and cmd.get("args"):
                # For msf_auxiliary, key on tool + target + module (first arg)
                key = f"{cmd['tool']}|{normalized_target}|{cmd.get('args', [''])[0]}"
            elif cmd.get("tool") == "wpscan":
                # For wpscan, key on tool + WordPress root (ignore args since same root = same scan)
                key = f"{cmd['tool']}|{normalized_target}"
            else:
                # For other tools, key on tool + target + full args (normalized)
                key = f"{cmd['tool']}|{normalized_target}|{normalized_args}"

            if key not in seen_keys:
                seen_keys.add(key)
                unique_commands.append(cmd)
            else:
                # Skip duplicate command from same batch
                print(
                    f"  ⏭️  Skipping duplicate command in batch: {cmd['tool']} for {cmd_target}"
                )

        commands = unique_commands
        # === END PRE-DEDUPLICATION ===

        try:
            from souleyez.engine.background import _lock, enqueue_job, list_jobs

            for cmd in commands:
                cmd_target = cmd.get("target", "")
                cmd_tool = cmd.get("tool", "")

                # === SMART FILTER: Skip noisy/useless targets ===
                should_skip, skip_reason = SmartFilter.should_skip_for_tool(
                    cmd_tool, cmd_target, cmd.get("context", {})
                )
                if should_skip:
                    logger.info(
                        f"SmartFilter: Skipping {cmd_tool} for {cmd_target}: {skip_reason}"
                    )
                    print(f"  🧠 SmartFilter: Skipping {cmd_tool} for {cmd_target}")
                    print(f"     Reason: {skip_reason}")
                    continue
                # === END SMART FILTER ===

                # Normalize target URL for deduplication (removes trailing dots)
                normalized_target = _normalize_url(cmd_target)

                # For wpscan, normalize WordPress paths (wp-admin, wp-content, wp-includes -> root)
                if cmd["tool"] == "wpscan":
                    normalized_target = _normalize_wordpress_url(normalized_target)

                # Create a unique key for this job (tool + target + engagement)
                # For msf_auxiliary, include the module in the key since same tool can run different modules
                if cmd["tool"] == "msf_auxiliary" and cmd.get("args"):
                    # Include first arg (the module name) in the key
                    module = cmd["args"][0] if cmd["args"] else ""
                    job_key = (
                        f"{cmd['tool']}|{normalized_target}|{engagement_id}|{module}"
                    )
                elif cmd["tool"] == "wpscan":
                    # For wpscan, key on tool + WordPress root (same root = same scan)
                    job_key = f"{cmd['tool']}|{normalized_target}|{engagement_id}"
                else:
                    job_key = f"{cmd['tool']}|{normalized_target}|{engagement_id}"

                # ATOMIC: Check and create inside lock to prevent race conditions
                with _lock:
                    # Re-read jobs INSIDE lock for latest state
                    existing_jobs = list_jobs(limit=1000)

                    # Check if similar job already exists (same tool + target + engagement, not error status)
                    # For msf_auxiliary and sqlmap, also check if the args match (different phases = different jobs)
                    # NOTE: Block if job is queued/running OR recently completed (< 5 min) with same args
                    similar_exists = False
                    for existing_job in existing_jobs:
                        # === DOMAIN-AWARE DUPLICATE DETECTION FOR WEB TOOLS ===
                        # Check for web scanning tools targeting same domain (even if different IPs)
                        # This prevents redundant scans when theHarvester creates separate nmap jobs per IP
                        if cmd["tool"] in ["nuclei", "gobuster"]:
                            # Check if both jobs target same tool and engagement
                            if (
                                existing_job.get("tool") == cmd["tool"]
                                and existing_job.get("engagement_id") == engagement_id
                            ):

                                # Check domain context from metadata
                                existing_domain = existing_job.get("metadata", {}).get(
                                    "domain_context"
                                )
                                cmd_domain = cmd.get("metadata", {}).get(
                                    "domain_context"
                                )

                                # If both have domain context and they match, this might be a duplicate
                                if (
                                    existing_domain
                                    and cmd_domain
                                    and existing_domain == cmd_domain
                                ):
                                    # Check if args match (same scan type)
                                    existing_args = existing_job.get("args", [])
                                    cmd_args = cmd.get("args", [])

                                    if existing_args == cmd_args:
                                        status = existing_job.get("status")

                                        # Block if queued or running
                                        if status in ["queued", "running"]:
                                            similar_exists = True
                                            print(
                                                f"  ⏭️  Skipping {cmd['tool']} for {cmd_target}: domain '{cmd_domain}' already being scanned by job #{existing_job['id']} on {existing_job.get('target')} ({status})"
                                            )
                                            break

                                        # Block if recently completed (< 5 min)
                                        elif status == "done":
                                            finished_at = existing_job.get(
                                                "finished_at"
                                            )
                                            if finished_at:
                                                try:
                                                    finished_time = (
                                                        datetime.fromisoformat(
                                                            finished_at.replace(
                                                                "Z", "+00:00"
                                                            )
                                                        )
                                                    )
                                                    current_time = (
                                                        datetime.now(
                                                            finished_time.tzinfo
                                                        )
                                                        if finished_time.tzinfo
                                                        else datetime.now()
                                                    )
                                                    time_delta = (
                                                        current_time - finished_time
                                                    ).total_seconds()

                                                    if (
                                                        time_delta
                                                        < DUPLICATE_WINDOW_SECONDS
                                                    ):
                                                        similar_exists = True
                                                        minutes_ago = int(
                                                            time_delta // 60
                                                        )
                                                        seconds_ago = int(
                                                            time_delta % 60
                                                        )
                                                        time_str = (
                                                            f"{minutes_ago}m {seconds_ago}s ago"
                                                            if minutes_ago > 0
                                                            else f"{seconds_ago}s ago"
                                                        )
                                                        print(
                                                            f"  ⏭️  Skipping {cmd['tool']} for {cmd_target}: domain '{cmd_domain}' scanned {time_str} by job #{existing_job['id']} (duplicate)"
                                                        )
                                                        break
                                                except Exception:
                                                    # If timestamp parsing fails, don't block (fail open)
                                                    pass
                            # Continue to next existing_job if domain doesn't match or args differ
                            continue

                        # === STANDARD TARGET-BASED DUPLICATE DETECTION (existing code) ===
                        if (
                            existing_job.get("tool") == cmd["tool"]
                            and _normalize_url(existing_job.get("target"))
                            == normalized_target
                            and existing_job.get("engagement_id") == engagement_id
                        ):

                            status = existing_job.get("status")

                            # === SQLMAP RULE-BASED DEDUP (30 min window for completed, always for active) ===
                            # For sqlmap: block if same rule applied to same URL within window
                            # This prevents loops while allowing re-runs after 30 min
                            if cmd["tool"] == "sqlmap":
                                cmd_rule_id = cmd.get("rule_id")
                                existing_rule_id = existing_job.get("rule_id")
                                if (
                                    cmd_rule_id
                                    and existing_rule_id
                                    and cmd_rule_id == existing_rule_id
                                ):
                                    # Check if -D (database) or -T (table) args differ - if so, allow
                                    # This enables --tables jobs for multiple databases with same rule_id
                                    cmd_args = cmd.get("args", [])
                                    existing_args = existing_job.get("args", [])

                                    def get_sqlmap_db_table(args):
                                        """Extract -D and -T values from sqlmap args."""
                                        db, table = None, None
                                        for i, arg in enumerate(args):
                                            if arg == "-D" and i + 1 < len(args):
                                                db = args[i + 1]
                                            elif arg == "-T" and i + 1 < len(args):
                                                table = args[i + 1]
                                        return (db, table)

                                    cmd_db_table = get_sqlmap_db_table(cmd_args)
                                    existing_db_table = get_sqlmap_db_table(
                                        existing_args
                                    )

                                    # If targeting different database or table, allow it
                                    if (
                                        cmd_db_table != existing_db_table
                                        and cmd_db_table != (None, None)
                                    ):
                                        pass  # Different DB/table, allow this job
                                    # Always block active jobs (queued/running) with same DB/table
                                    elif status in ["queued", "running"]:
                                        similar_exists = True
                                        print(
                                            f"  ⏭️  Skipping sqlmap for {cmd_target}: rule #{cmd_rule_id} already {status} (job #{existing_job['id']})"
                                        )
                                        break
                                    # For completed jobs, only block within 30 min window
                                    elif status == "done":
                                        finished_at = existing_job.get("finished_at")
                                        if finished_at:
                                            try:
                                                finished_time = datetime.fromisoformat(
                                                    finished_at.replace("Z", "+00:00")
                                                )
                                                current_time = (
                                                    datetime.now(finished_time.tzinfo)
                                                    if finished_time.tzinfo
                                                    else datetime.now()
                                                )
                                                time_delta = (
                                                    current_time - finished_time
                                                ).total_seconds()
                                                if (
                                                    time_delta
                                                    < SQLMAP_RULE_DEDUP_SECONDS
                                                ):
                                                    similar_exists = True
                                                    minutes_ago = int(time_delta // 60)
                                                    print(
                                                        f"  ⏭️  Skipping sqlmap for {cmd_target}: rule #{cmd_rule_id} ran {minutes_ago}m ago (job #{existing_job['id']})"
                                                    )
                                                    break
                                                # else: job completed > 30 min ago, allow re-run
                                            except Exception:
                                                pass  # Timestamp parse failed, don't block

                            # Check if job is active (queued/running)
                            is_active = status in ["queued", "running"]

                            # Check if job recently completed with same args (prevent immediate duplicates)
                            is_recent_duplicate = False
                            if status == "done":
                                finished_at = existing_job.get("finished_at")
                                if finished_at:
                                    try:
                                        # Parse ISO timestamp: "2025-11-11T23:34:56"
                                        finished_time = datetime.fromisoformat(
                                            finished_at.replace("Z", "+00:00")
                                        )
                                        current_time = (
                                            datetime.now(finished_time.tzinfo)
                                            if finished_time.tzinfo
                                            else datetime.now()
                                        )
                                        time_delta = (
                                            current_time - finished_time
                                        ).total_seconds()

                                        # Only block if finished < 5 min ago AND (same args OR same rule_id for sqlmap)
                                        if time_delta < DUPLICATE_WINDOW_SECONDS:
                                            existing_args = existing_job.get("args", [])
                                            cmd_args = cmd.get("args", [])

                                            # For sqlmap: also check rule_id (same rule = duplicate even with different parent)
                                            # BUT allow different databases/tables (same rule can enumerate multiple DBs)
                                            if cmd["tool"] == "sqlmap":
                                                cmd_rule_id = cmd.get("rule_id")
                                                existing_rule_id = existing_job.get(
                                                    "rule_id"
                                                )

                                                # Extract -D and -T values to compare databases/tables
                                                def _get_sqlmap_db_table(args):
                                                    db, table = None, None
                                                    for i, arg in enumerate(args):
                                                        if arg == "-D" and i + 1 < len(
                                                            args
                                                        ):
                                                            db = args[i + 1]
                                                        elif (
                                                            arg == "-T"
                                                            and i + 1 < len(args)
                                                        ):
                                                            table = args[i + 1]
                                                    return (db, table)

                                                cmd_db_table = _get_sqlmap_db_table(
                                                    cmd_args
                                                )
                                                existing_db_table = (
                                                    _get_sqlmap_db_table(existing_args)
                                                )

                                                # If targeting different database or table, allow it
                                                if (
                                                    cmd_db_table != existing_db_table
                                                    and cmd_db_table != (None, None)
                                                ):
                                                    pass  # Different DB/table, allow this job
                                                elif (
                                                    cmd_rule_id
                                                    and existing_rule_id
                                                    and cmd_rule_id == existing_rule_id
                                                ):
                                                    is_recent_duplicate = True
                                                    minutes_ago = int(time_delta // 60)
                                                    seconds_ago = int(time_delta % 60)
                                                    time_str = (
                                                        f"{minutes_ago}m {seconds_ago}s ago"
                                                        if minutes_ago > 0
                                                        else f"{seconds_ago}s ago"
                                                    )
                                                    print(
                                                        f"  ⏭️  Skipping sqlmap for {cmd_target}: rule #{cmd_rule_id} completed {time_str} (duplicate)"
                                                    )
                                                elif existing_args == cmd_args:
                                                    is_recent_duplicate = True
                                                    minutes_ago = int(time_delta // 60)
                                                    seconds_ago = int(time_delta % 60)
                                                    time_str = (
                                                        f"{minutes_ago}m {seconds_ago}s ago"
                                                        if minutes_ago > 0
                                                        else f"{seconds_ago}s ago"
                                                    )
                                                    print(
                                                        f"  ⏭️  Skipping sqlmap for {cmd_target}: job #{existing_job['id']} completed {time_str} (duplicate)"
                                                    )
                                            elif existing_args == cmd_args:
                                                is_recent_duplicate = True
                                                minutes_ago = int(time_delta // 60)
                                                seconds_ago = int(time_delta % 60)
                                                time_str = (
                                                    f"{minutes_ago}m {seconds_ago}s ago"
                                                    if minutes_ago > 0
                                                    else f"{seconds_ago}s ago"
                                                )
                                                print(
                                                    f"  ⏭️  Skipping {cmd['tool']} for {cmd_target}: job #{existing_job['id']} completed {time_str} (duplicate)"
                                                )
                                    except Exception:
                                        # If timestamp parsing fails, don't block (fail open)
                                        pass

                            # Block if active OR recent duplicate
                            if is_active or is_recent_duplicate:
                                if is_active:
                                    # For msf_auxiliary, check if module matches
                                    if cmd["tool"] == "msf_auxiliary":
                                        existing_args = existing_job.get("args", [])
                                        cmd_args = cmd.get("args", [])
                                        if (
                                            existing_args
                                            and cmd_args
                                            and existing_args[0] == cmd_args[0]
                                        ):
                                            similar_exists = True
                                            print(
                                                f"  ⏭️  Skipping {cmd['tool']} for {cmd_target}: similar job #{existing_job['id']} already exists ({existing_job['status']})"
                                            )
                                            break

                                    # For sqlmap: check by rule_id to prevent same rule firing twice on same URL
                                    # BUT allow different databases/tables (same rule can enumerate multiple DBs)
                                    elif cmd["tool"] == "sqlmap":
                                        cmd_rule_id = cmd.get("rule_id")
                                        existing_rule_id = existing_job.get("rule_id")
                                        existing_args = existing_job.get("args", [])
                                        cmd_args = cmd.get("args", [])

                                        # Extract -D and -T values to compare databases/tables
                                        def _get_db_table_active(args):
                                            db, table = None, None
                                            for i, arg in enumerate(args):
                                                if arg == "-D" and i + 1 < len(args):
                                                    db = args[i + 1]
                                                elif arg == "-T" and i + 1 < len(args):
                                                    table = args[i + 1]
                                            return (db, table)

                                        cmd_db_table = _get_db_table_active(cmd_args)
                                        existing_db_table = _get_db_table_active(
                                            existing_args
                                        )

                                        # If targeting different database or table, allow it
                                        if (
                                            cmd_db_table != existing_db_table
                                            and cmd_db_table != (None, None)
                                        ):
                                            pass  # Different DB/table, allow this job
                                        # If both have rule_id and they match (same DB/table), it's a duplicate
                                        elif (
                                            cmd_rule_id
                                            and existing_rule_id
                                            and cmd_rule_id == existing_rule_id
                                        ):
                                            similar_exists = True
                                            print(
                                                f"  ⏭️  Skipping sqlmap for {cmd_target}: rule #{cmd_rule_id} already applied (job #{existing_job['id']} {existing_job['status']})"
                                            )
                                            break
                                        # Also check if exact same args (covers manual/no-rule jobs)
                                        elif existing_args == cmd_args:
                                            similar_exists = True
                                            print(
                                                f"  ⏭️  Skipping sqlmap for {cmd_target}: similar job #{existing_job['id']} already exists ({existing_job['status']})"
                                            )
                                            break
                                        # If different rule_id and different args, allow it (different SQLMap phase)

                                    # For gobuster: check if args match
                                    elif cmd["tool"] == "gobuster":
                                        existing_args = existing_job.get("args", [])
                                        cmd_args = cmd.get("args", [])
                                        if existing_args == cmd_args:
                                            similar_exists = True
                                            print(
                                                f"  ⏭️  Skipping {cmd['tool']} for {cmd_target}: similar job #{existing_job['id']} already exists ({existing_job['status']})"
                                            )
                                            break

                                    # For hydra: check if args match (different services = different args)
                                    # SSH, FTP, Telnet, etc. have different protocol args so should all run
                                    elif cmd["tool"] == "hydra":
                                        existing_args = existing_job.get("args", [])
                                        cmd_args = cmd.get("args", [])
                                        if existing_args == cmd_args:
                                            similar_exists = True
                                            print(
                                                f"  ⏭️  Skipping {cmd['tool']} for {cmd_target}: similar job #{existing_job['id']} already exists ({existing_job['status']})"
                                            )
                                            break
                                        # Different args (different service), allow it

                                    # For ldapsearch: check if args match (different queries = different jobs)
                                    # naming contexts query vs user enumeration query
                                    elif cmd["tool"] == "ldapsearch":
                                        existing_args = existing_job.get("args", [])
                                        cmd_args = cmd.get("args", [])

                                        # Extract search filter (objectClass=...) to compare query type
                                        def _get_ldap_filter(args):
                                            for arg in args:
                                                if "objectClass=" in arg:
                                                    return arg
                                            return None

                                        cmd_filter = _get_ldap_filter(cmd_args)
                                        existing_filter = _get_ldap_filter(
                                            existing_args
                                        )

                                        # If same search filter (same query type), treat as duplicate
                                        # This prevents duplicate user enumeration queries with different base_dn
                                        if (
                                            cmd_filter
                                            and existing_filter
                                            and cmd_filter == existing_filter
                                        ):
                                            similar_exists = True
                                            print(
                                                f"  ⏭️  Skipping {cmd['tool']} for {cmd_target}: same query type already exists in job #{existing_job['id']} ({existing_job['status']})"
                                            )
                                            break
                                        elif existing_args == cmd_args:
                                            similar_exists = True
                                            print(
                                                f"  ⏭️  Skipping {cmd['tool']} for {cmd_target}: similar job #{existing_job['id']} already exists ({existing_job['status']})"
                                            )
                                            break
                                        # Different args (different query type), allow it

                                    # For quick lookup tools (whois, dnsrecon), skip 5-min duplicate check
                                    # They're fast and each theHarvester run should trigger them
                                    elif cmd["tool"] in ["whois", "dnsrecon"]:
                                        # Only block if currently running (not if just completed)
                                        pass  # Don't set similar_exists, let it run

                                    # For all other tools, consider it a duplicate
                                    else:
                                        similar_exists = True
                                        print(
                                            f"  ⏭️  Skipping {cmd['tool']} for {cmd_target}: similar job #{existing_job['id']} already exists ({existing_job['status']})"
                                        )
                                        break
                                else:
                                    # is_recent_duplicate - apply same args-based checks
                                    # For tools where different args = different job, check before blocking
                                    if cmd["tool"] in [
                                        "msf_auxiliary",
                                        "hydra",
                                        "gobuster",
                                        "ldapsearch",
                                    ]:
                                        existing_args = existing_job.get("args", [])
                                        cmd_args = cmd.get("args", [])
                                        # For msf_auxiliary, check module (first arg)
                                        if cmd["tool"] == "msf_auxiliary":
                                            if (
                                                existing_args
                                                and cmd_args
                                                and existing_args[0] == cmd_args[0]
                                            ):
                                                similar_exists = True
                                                break
                                            # Different module, allow it
                                        # For hydra/gobuster, check full args
                                        elif cmd["tool"] in ["hydra", "gobuster"]:
                                            if existing_args == cmd_args:
                                                similar_exists = True
                                                break
                                        # For ldapsearch, check query type (objectClass filter)
                                        elif cmd["tool"] == "ldapsearch":

                                            def _get_ldap_filter_recent(args):
                                                for arg in args:
                                                    if "objectClass=" in arg:
                                                        return arg
                                                return None

                                            cmd_filter = _get_ldap_filter_recent(
                                                cmd_args
                                            )
                                            existing_filter = _get_ldap_filter_recent(
                                                existing_args
                                            )
                                            if (
                                                cmd_filter
                                                and existing_filter
                                                and cmd_filter == existing_filter
                                            ):
                                                similar_exists = True
                                                break
                                            elif existing_args == cmd_args:
                                                similar_exists = True
                                                break
                                        # Different args, allow it
                                    else:
                                        # Other tools - block recent duplicates
                                        similar_exists = True
                                        break

                    # Create job if no duplicate found (still inside lock!)
                    if not similar_exists:
                        # Resolve wordlist paths in args before enqueueing
                        from souleyez.wordlists import resolve_args_wordlists

                        resolved_args = resolve_args_wordlists(cmd["args"])

                        # Check if approval mode is enabled
                        if self.is_approval_mode():
                            # Add to pending queue for user approval
                            from souleyez.core.pending_chains import add_pending_chain

                            print(
                                f"  📋 Pending approval: {cmd['tool']} for {cmd_target}"
                            )
                            chain_id = add_pending_chain(
                                parent_job_id=parent_job_id,
                                rule_description=cmd.get(
                                    "reason", f"Auto-chain from {source_tool}"
                                ),
                                tool=cmd["tool"],
                                target=cmd_target,
                                args=resolved_args,
                                priority=cmd.get("priority", 5),
                                engagement_id=engagement_id,
                                metadata=cmd.get("metadata"),
                            )
                            # Return chain ID as negative to indicate pending (not executed)
                            job_ids.append(-chain_id)
                        else:
                            # Auto mode: enqueue immediately
                            # Check for duplicate jobs to prevent redundant scans
                            # Pass args for tools that need arg-based dedup (msf_auxiliary, hydra)
                            if self._should_skip_duplicate(
                                cmd["tool"], cmd_target, engagement_id, cmd.get("args")
                            ):
                                print(
                                    f"  ⏭️  Skipped duplicate {cmd['tool']} for {cmd_target}"
                                )
                                continue

                            print(
                                f"  🔗 Chaining {cmd['tool']} for {cmd_target}: {cmd['reason']}"
                            )
                            # enqueue_job will acquire _lock again (nested lock is safe - same thread)
                            try:
                                job_id = enqueue_job(
                                    tool=cmd["tool"],
                                    target=cmd_target,
                                    args=resolved_args,
                                    label=source_tool,
                                    engagement_id=engagement_id,
                                    parent_id=parent_job_id,
                                    reason=cmd.get(
                                        "reason", f"Auto-chain from {source_tool}"
                                    ),
                                    metadata=cmd.get(
                                        "metadata"
                                    ),  # Pass through deduplication metadata
                                    rule_id=cmd.get(
                                        "rule_id"
                                    ),  # Pass rule ID for tracking
                                )
                                job_ids.append(job_id)
                            except Exception as scope_err:
                                # Handle scope violations gracefully - skip out-of-scope targets
                                if (
                                    "ScopeViolationError" in type(scope_err).__name__
                                    or "out of scope" in str(scope_err).lower()
                                ):
                                    print(f"  ⚠️  Skipped (out of scope): {cmd_target}")
                                else:
                                    raise  # Re-raise unexpected errors

                # Lock released here - next iteration gets fresh lock

        except Exception as e:
            print(f"  ⚠️  Failed to enqueue chained jobs: {e}")

        return job_ids

    def get_chain_summary(self) -> str:
        """Get a summary of all configured chain rules."""
        summary = "Tool Chaining Rules:\n"
        summary += "=" * 60 + "\n\n"

        # Group by trigger tool
        by_trigger = {}
        for rule in self.rules:
            if rule.trigger_tool not in by_trigger:
                by_trigger[rule.trigger_tool] = []
            by_trigger[rule.trigger_tool].append(rule)

        for trigger, rules in sorted(by_trigger.items()):
            summary += f"{trigger.upper()}:\n"
            for rule in sorted(rules, key=lambda r: r.priority, reverse=True):
                status = "✓" if rule.enabled else "✗"
                summary += f"  [{status}] Priority {rule.priority}: {rule.trigger_condition} → {rule.target_tool}\n"
                summary += f"      {rule.description}\n"
            summary += "\n"

        return summary


# Global instance
_chaining = None


def get_tool_chaining() -> ToolChaining:
    """Get the global tool chaining instance."""
    global _chaining
    if _chaining is None:
        _chaining = ToolChaining()
    return _chaining
