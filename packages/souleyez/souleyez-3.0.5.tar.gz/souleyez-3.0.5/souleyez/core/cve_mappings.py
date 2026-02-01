#!/usr/bin/env python3
"""
souleyez.core.cve_mappings

CVE-to-version database for version-aware tool chaining.
Maps known CVEs to affected product versions and recommended exploit tools.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from souleyez.core.version_utils import (
    matches_version,
    normalize_product_name,
    parse_version_spec,
)

logger = logging.getLogger(__name__)


@dataclass
class CVEMapping:
    """Maps a CVE to affected product versions and exploit tool."""

    cve_id: str
    product: str  # Normalized product name (e.g., 'apache')
    affected_versions: str  # Version spec (e.g., '>=2.4.49,<=2.4.50')
    tool: str  # Tool to run (e.g., 'nuclei')
    args: List[str] = field(default_factory=list)  # Tool arguments
    severity: str = "high"  # critical, high, medium, low
    description: str = ""  # Human-readable description
    references: List[str] = field(default_factory=list)  # URLs

    def matches_service(self, product: str, version: str) -> bool:
        """Check if a service product/version is affected by this CVE."""
        if not product or not version:
            return False

        normalized = normalize_product_name(product)
        if normalized != self.product:
            return False

        _, conditions = parse_version_spec(f"{self.product}:{self.affected_versions}")
        return matches_version(version, conditions)


# Curated list of high-impact CVEs
# These are well-known vulnerabilities with reliable detection
CURATED_CVES: Dict[str, CVEMapping] = {
    # Apache HTTP Server
    "CVE-2021-41773": CVEMapping(
        cve_id="CVE-2021-41773",
        product="apache",
        affected_versions=">=2.4.49,<=2.4.49",
        tool="nuclei",
        args=["-t", "http/cves/2021/CVE-2021-41773.yaml"],
        severity="critical",
        description="Apache 2.4.49 path traversal and RCE",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2021-41773"],
    ),
    "CVE-2021-42013": CVEMapping(
        cve_id="CVE-2021-42013",
        product="apache",
        affected_versions=">=2.4.49,<=2.4.50",
        tool="nuclei",
        args=["-t", "http/cves/2021/CVE-2021-42013.yaml"],
        severity="critical",
        description="Apache 2.4.49-2.4.50 path traversal bypass (incomplete fix for CVE-2021-41773)",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2021-42013"],
    ),
    # nginx
    "CVE-2021-23017": CVEMapping(
        cve_id="CVE-2021-23017",
        product="nginx",
        affected_versions=">=0.6.18,<=1.20.0",
        tool="nuclei",
        args=["-t", "http/cves/2021/CVE-2021-23017.yaml"],
        severity="high",
        description="nginx DNS resolver off-by-one heap write",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2021-23017"],
    ),
    # PHP
    "CVE-2019-11043": CVEMapping(
        cve_id="CVE-2019-11043",
        product="php",
        affected_versions=">=7.1.0,<7.1.33",
        tool="nuclei",
        args=["-t", "http/cves/2019/CVE-2019-11043.yaml"],
        severity="critical",
        description="PHP-FPM RCE via nginx misconfiguration",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2019-11043"],
    ),
    "CVE-2012-1823": CVEMapping(
        cve_id="CVE-2012-1823",
        product="php",
        affected_versions=">=5.3.0,<5.3.12",
        tool="nuclei",
        args=["-t", "http/cves/2012/CVE-2012-1823.yaml"],
        severity="critical",
        description="PHP CGI argument injection RCE",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2012-1823"],
    ),
    # OpenSSH
    "CVE-2018-15473": CVEMapping(
        cve_id="CVE-2018-15473",
        product="ssh",
        affected_versions=">=2.0,<7.7",
        tool="nmap",
        args=["--script", "ssh-auth-methods", "-p", "22"],
        severity="medium",
        description="OpenSSH user enumeration",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2018-15473"],
    ),
    # vsftpd
    "CVE-2011-2523": CVEMapping(
        cve_id="CVE-2011-2523",
        product="vsftpd",
        affected_versions="=2.3.4",
        tool="nmap",
        args=["--script", "ftp-vsftpd-backdoor", "-p", "21"],
        severity="critical",
        description="vsftpd 2.3.4 backdoor (smiley face)",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2011-2523"],
    ),
    # ProFTPD
    "CVE-2015-3306": CVEMapping(
        cve_id="CVE-2015-3306",
        product="proftpd",
        affected_versions=">=1.3.5,<1.3.5a",
        tool="nmap",
        args=["--script", "ftp-proftpd-backdoor", "-p", "21"],
        severity="critical",
        description="ProFTPD mod_copy arbitrary file read/write",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2015-3306"],
    ),
    # Samba
    "CVE-2017-7494": CVEMapping(
        cve_id="CVE-2017-7494",
        product="samba",
        affected_versions=">=3.5.0,<4.6.4",
        tool="nmap",
        args=["--script", "smb-vuln-cve-2017-7494", "-p", "445"],
        severity="critical",
        description="Samba RCE via writable share (SambaCry)",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2017-7494"],
    ),
    # Apache Tomcat
    "CVE-2020-1938": CVEMapping(
        cve_id="CVE-2020-1938",
        product="tomcat",
        affected_versions=">=6.0.0,<9.0.31",
        tool="nmap",
        args=["--script", "ajp-brute,ajp-headers,ajp-methods", "-p", "8009"],
        severity="critical",
        description="Apache Tomcat AJP Ghostcat file read/include",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2020-1938"],
    ),
    # WordPress
    "CVE-2022-21661": CVEMapping(
        cve_id="CVE-2022-21661",
        product="wordpress",
        affected_versions=">=5.8.0,<5.8.3",
        tool="wpscan",
        args=["--enumerate", "vp,vt,u"],
        severity="high",
        description="WordPress SQL injection via WP_Query",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2022-21661"],
    ),
    # Drupal
    "CVE-2018-7600": CVEMapping(
        cve_id="CVE-2018-7600",
        product="drupal",
        affected_versions=">=7.0,<7.58",
        tool="nuclei",
        args=["-t", "http/cves/2018/CVE-2018-7600.yaml"],
        severity="critical",
        description="Drupal RCE (Drupalgeddon2)",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2018-7600"],
    ),
    "CVE-2018-7602": CVEMapping(
        cve_id="CVE-2018-7602",
        product="drupal",
        affected_versions=">=7.0,<7.59",
        tool="nuclei",
        args=["-t", "http/cves/2018/CVE-2018-7602.yaml"],
        severity="critical",
        description="Drupal RCE (Drupalgeddon3)",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2018-7602"],
    ),
    # Microsoft IIS
    "CVE-2017-7269": CVEMapping(
        cve_id="CVE-2017-7269",
        product="iis",
        affected_versions=">=6.0,<=6.0",
        tool="nmap",
        args=["--script", "http-vuln-cve2017-7269", "-p", "80"],
        severity="critical",
        description="IIS 6.0 WebDAV buffer overflow RCE",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2017-7269"],
    ),
    # Redis
    "CVE-2022-0543": CVEMapping(
        cve_id="CVE-2022-0543",
        product="redis",
        affected_versions=">=2.2,<6.2.7",
        tool="nuclei",
        args=["-t", "network/cves/2022/CVE-2022-0543.yaml"],
        severity="critical",
        description="Redis Lua sandbox escape RCE (Debian/Ubuntu)",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2022-0543"],
    ),
    # Elasticsearch
    "CVE-2015-1427": CVEMapping(
        cve_id="CVE-2015-1427",
        product="elasticsearch",
        affected_versions=">=1.3.0,<1.4.3",
        tool="nuclei",
        args=["-t", "http/cves/2015/CVE-2015-1427.yaml"],
        severity="critical",
        description="Elasticsearch Groovy sandbox bypass RCE",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2015-1427"],
    ),
    # Apache Struts
    "CVE-2017-5638": CVEMapping(
        cve_id="CVE-2017-5638",
        product="struts",
        affected_versions=">=2.3.5,<2.3.32",
        tool="nuclei",
        args=["-t", "http/cves/2017/CVE-2017-5638.yaml"],
        severity="critical",
        description="Apache Struts2 RCE via Content-Type header",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2017-5638"],
    ),
    # Log4j
    "CVE-2021-44228": CVEMapping(
        cve_id="CVE-2021-44228",
        product="log4j",
        affected_versions=">=2.0,<2.15.0",
        tool="nuclei",
        args=["-t", "http/cves/2021/CVE-2021-44228.yaml"],
        severity="critical",
        description="Log4j RCE (Log4Shell)",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2021-44228"],
    ),
}


def get_cves_for_service(product: str, version: str) -> List[CVEMapping]:
    """
    Find all CVEs that apply to a given product/version.

    Args:
        product: Product name from scan (e.g., "Apache httpd", "nginx")
        version: Version string from scan (e.g., "2.4.49", "1.19.0")

    Returns:
        List of applicable CVEMapping objects, sorted by severity.
    """
    applicable = []
    for cve in CURATED_CVES.values():
        if cve.matches_service(product, version):
            applicable.append(cve)

    # Sort by severity (critical > high > medium > low)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    applicable.sort(key=lambda c: severity_order.get(c.severity, 4))

    return applicable


def get_cve_by_id(cve_id: str) -> Optional[CVEMapping]:
    """Get a specific CVE by ID."""
    return CURATED_CVES.get(cve_id.upper())


def load_cve_database(path: Optional[str] = None) -> Dict[str, CVEMapping]:
    """
    Load CVE database from JSON file.

    Args:
        path: Path to JSON file. If None, uses default location.

    Returns:
        Dictionary of CVE ID -> CVEMapping
    """
    if path is None:
        # Check user config directory first
        user_path = Path.home() / ".souleyez" / "cve_database.json"
        if user_path.exists():
            path = str(user_path)
        else:
            # Fall back to package data
            pkg_path = Path(__file__).parent.parent / "data" / "cve_database.json"
            if pkg_path.exists():
                path = str(pkg_path)
            else:
                logger.debug("No CVE database file found, using curated list")
                return CURATED_CVES

    try:
        with open(path, "r") as f:
            data = json.load(f)

        cves = {}
        for cve_id, entry in data.items():
            cves[cve_id] = CVEMapping(
                cve_id=cve_id,
                product=entry.get("product", ""),
                affected_versions=entry.get("affected", ""),
                tool=entry.get("tool", "nuclei"),
                args=entry.get("args", []),
                severity=entry.get("severity", "high"),
                description=entry.get("description", ""),
                references=entry.get("references", []),
            )

        logger.info(f"Loaded {len(cves)} CVEs from {path}")
        return cves

    except (IOError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load CVE database from {path}: {e}")
        return CURATED_CVES


def get_all_cves() -> Dict[str, CVEMapping]:
    """Get all available CVEs (curated + loaded from file)."""
    # Start with curated list
    all_cves = CURATED_CVES.copy()

    # Try to load additional CVEs from file
    loaded = load_cve_database()
    all_cves.update(loaded)

    return all_cves


def generate_version_condition(cve: CVEMapping) -> str:
    """
    Generate a version condition string for a CVE.

    Returns condition like: 'version:apache:>=2.4.49,<=2.4.50'
    """
    return f"version:{cve.product}:{cve.affected_versions}"
