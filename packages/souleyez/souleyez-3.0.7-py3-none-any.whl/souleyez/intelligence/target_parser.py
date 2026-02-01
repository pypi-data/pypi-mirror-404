#!/usr/bin/env python3
"""
Target parser for job correlation.
Parses job targets to extract host, port, and service information.
"""

import re
from typing import Dict, List, Optional
from urllib.parse import urlparse


class TargetParser:
    """Parse job targets to extract host and port information."""

    # Common service-to-port mappings
    SERVICE_PORTS = {
        "ftp": 21,
        "ssh": 22,
        "telnet": 23,
        "smtp": 25,
        "dns": 53,
        "http": 80,
        "pop3": 110,
        "imap": 143,
        "snmp": 161,
        "ldap": 389,
        "https": 443,
        "smb": 445,
        "smbold": 139,
        "mssql": 1433,
        "mysql": 3306,
        "rdp": 3389,
        "postgres": 5432,
        "postgresql": 5432,
        "vnc": 5900,
        "redis": 6379,
        "mongodb": 27017,
    }

    # Reverse mapping: port to service
    PORT_SERVICES = {v: k for k, v in SERVICE_PORTS.items()}
    # Handle duplicates manually
    PORT_SERVICES[139] = "smb"
    PORT_SERVICES[445] = "smb"

    # Add common non-standard web ports for vulnerable web apps
    PORT_SERVICES[3000] = "http"  # Node.js/Express default, OWASP Juice Shop
    PORT_SERVICES[8080] = "http"  # Tomcat/alternative HTTP
    PORT_SERVICES[8000] = "http"  # Django/Python dev servers
    PORT_SERVICES[8888] = "http"  # Jupyter/alternative web servers
    PORT_SERVICES[9090] = "http"  # Cockpit/monitoring interfaces

    # MSF module patterns
    MSF_PATTERNS = {
        "ftp": 21,
        "ssh": 22,
        "telnet": 23,
        "smtp": 25,
        "http": 80,
        "pop3": 110,
        "imap": 143,
        "snmp": 161,
        "smb": 445,
        "mssql": 1433,
        "mysql": 3306,
        "rdp": 3389,
        "postgres": 5432,
        "vnc": 5900,
        "redis": 6379,
    }

    def parse_target(self, tool: str, target: str, args: Optional[List] = None) -> Dict:
        """
        Parse job target to extract host and port.

        Args:
            tool: Tool name (nmap, nuclei, hydra, etc.)
            target: Target string (IP, URL, domain, etc.)
            args: Additional arguments (list or dict)

        Returns:
            {
                'host': str,
                'port': int (optional),
                'ports': List[int] (optional),
                'service': str (optional),
                'protocol': str (optional)
            }

        Examples:
            parse_target('nmap', '10.0.0.5', ['-p', '22,80'])
            → {'host': '10.0.0.5', 'ports': [22, 80]}

            parse_target('nuclei', 'http://10.0.0.5:443')
            → {'host': '10.0.0.5', 'port': 443, 'protocol': 'https'}

            parse_target('hydra', '10.0.0.5', ['ssh'])
            → {'host': '10.0.0.5', 'port': 22, 'service': 'ssh'}
        """
        result = {}

        # Check if target is a URL
        if target.startswith(("http://", "https://", "ftp://", "ftps://")):
            url_info = self.extract_from_url(target)
            result.update(url_info)
            return result

        # Extract host and port from various formats
        host, port = self._extract_host_port(target)
        result["host"] = host

        if port:
            result["port"] = port

        # Tool-specific parsing
        if tool == "nmap":
            result.update(self._parse_nmap_args(args))
        elif tool in ["nuclei", "gobuster", "wpscan"]:
            result.update(self._parse_web_tool_target(target))
        elif tool == "hydra":
            result.update(self._parse_hydra_args(target, args))
        elif tool == "msf_auxiliary":
            result.update(self._parse_msf_args(args))
        elif tool == "enum4linux":
            result["port"] = 445
            result["service"] = "smb"
        elif tool == "smbmap":
            result["port"] = 445
            result["service"] = "smb"
        elif tool == "sqlmap":
            result.update(self._parse_sqlmap_target(target))
        elif tool == "whois":
            # Whois is domain-level, no port
            pass
        elif tool == "dnsrecon":
            result["port"] = 53
            result["service"] = "dns"
        elif tool == "theharvester":
            # OSINT, no specific port
            pass

        # If we have a port but no service, infer service
        if result.get("port") and not result.get("service"):
            result["service"] = self.infer_service_from_port(result["port"])

        # If we have a service but no port, infer port
        if result.get("service") and not result.get("port"):
            result["port"] = self.infer_port_from_service(result["service"])

        return result

    def _extract_host_port(self, target: str) -> tuple:
        """
        Extract host and port from target string.

        Handles:
            - 10.0.0.5
            - 10.0.0.5:3306
            - example.com
            - example.com:8080

        Returns:
            (host, port) tuple
        """
        # Check for IP:port or domain:port
        match = re.match(r"^([a-zA-Z0-9\.\-]+):(\d+)$", target)
        if match:
            return match.group(1), int(match.group(2))

        # Just host
        return target, None

    def extract_from_url(self, url: str) -> Dict:
        """
        Parse URL to extract host, port, protocol.

        Examples:
            'http://10.0.0.5' → {'host': '10.0.0.5', 'port': 80, 'protocol': 'http'}
            'https://10.0.0.5:8443' → {'host': '10.0.0.5', 'port': 8443, 'protocol': 'https'}
            'ftp://10.0.0.5:21' → {'host': '10.0.0.5', 'port': 21, 'protocol': 'ftp'}
        """
        parsed = urlparse(url)

        result = {"host": parsed.hostname or parsed.netloc, "protocol": parsed.scheme}

        # Determine port
        if parsed.port:
            result["port"] = parsed.port
        else:
            # Use default port for protocol
            if parsed.scheme == "http":
                result["port"] = 80
            elif parsed.scheme == "https":
                result["port"] = 443
            elif parsed.scheme == "ftp":
                result["port"] = 21
            elif parsed.scheme == "ftps":
                result["port"] = 990

        # Infer service from protocol
        if parsed.scheme in ["http", "https"]:
            result["service"] = "http"
        elif parsed.scheme in ["ftp", "ftps"]:
            result["service"] = "ftp"

        return result

    def _parse_nmap_args(self, args: Optional[List]) -> Dict:
        """
        Parse Nmap arguments to extract port info.

        Examples:
            ['-p', '22,80,443'] → {'ports': [22, 80, 443]}
            ['-p', '1-1000'] → {'ports': range(1, 1001)}
            ['-sV', '-p-'] → {}  # Full port scan
        """
        result = {}

        if not args:
            return result

        # Look for -p flag
        try:
            p_idx = args.index("-p")
            if p_idx + 1 < len(args):
                port_spec = args[p_idx + 1]

                # Handle full port scan
                if port_spec == "-":
                    return result

                # Handle comma-separated ports
                if "," in port_spec:
                    ports = []
                    for p in port_spec.split(","):
                        if "-" in p:
                            # Range like 20-25
                            start, end = map(int, p.split("-"))
                            ports.extend(range(start, end + 1))
                        else:
                            ports.append(int(p))
                    result["ports"] = ports

                # Handle port range
                elif "-" in port_spec:
                    start, end = map(int, port_spec.split("-"))
                    result["ports"] = list(range(start, end + 1))

                # Single port
                else:
                    result["ports"] = [int(port_spec)]

        except (ValueError, IndexError):
            pass

        return result

    def _parse_web_tool_target(self, target: str) -> Dict:
        """Parse web tool targets (nuclei, gobuster, wpscan)."""
        if target.startswith(("http://", "https://")):
            return self.extract_from_url(target)
        return {}

    def _parse_hydra_args(self, target: str, args: Optional[List]) -> Dict:
        """
        Parse Hydra arguments.

        Examples:
            target='10.0.0.5', args=['ssh'] → {'port': 22, 'service': 'ssh'}
            target='10.0.0.5', args=['mysql'] → {'port': 3306, 'service': 'mysql'}
        """
        result = {}

        if args and len(args) > 0:
            # First arg is usually the service
            service = args[0].lower()
            result["service"] = service
            result["port"] = self.infer_port_from_service(service)

        return result

    def _parse_msf_args(self, args: Optional[List]) -> Dict:
        """
        Parse Metasploit auxiliary module args.

        Args can be:
            - List: ['scanner/mysql/mysql_login']
            - Dict: {'module': 'scanner/mysql/mysql_login'}

        Examples:
            {'module': 'scanner/mysql/mysql_login'} → {'service': 'mysql', 'port': 3306}
            {'module': 'scanner/ssh/ssh_login'} → {'service': 'ssh', 'port': 22}
        """
        result = {}

        if not args:
            return result

        # Extract module name
        module = None
        if isinstance(args, dict):
            module = args.get("module")
        elif isinstance(args, list) and len(args) > 0:
            module = args[0]

        if module:
            msf_info = self.parse_msf_module(module)
            result.update(msf_info)

        return result

    def _parse_sqlmap_target(self, target: str) -> Dict:
        """
        Parse SQLMap target (usually a URL).

        Examples:
            'http://10.0.0.5/page.php?id=1' → {'host': '10.0.0.5', 'port': 80, 'service': 'http'}
        """
        if target.startswith(("http://", "https://")):
            return self.extract_from_url(target)
        return {}

    def parse_msf_module(self, module: str) -> Dict:
        """
        Extract service info from MSF module name.

        Examples:
            'scanner/mysql/mysql_login' → {'service': 'mysql', 'port': 3306}
            'scanner/ssh/ssh_login' → {'service': 'ssh', 'port': 22}
            'exploit/unix/ftp/vsftpd_234_backdoor' → {'service': 'ftp', 'port': 21}
        """
        result = {}

        # Extract service name from module path
        parts = module.split("/")

        for part in parts:
            part_lower = part.lower()
            if part_lower in self.MSF_PATTERNS:
                result["service"] = part_lower
                result["port"] = self.MSF_PATTERNS[part_lower]
                break

        return result

    def infer_port_from_service(self, service: str) -> Optional[int]:
        """
        Infer default port from service name.

        Examples:
            'ssh' → 22
            'mysql' → 3306
            'http' → 80
            'https' → 443
        """
        service_lower = service.lower()
        return self.SERVICE_PORTS.get(service_lower)

    def infer_service_from_port(self, port: int) -> Optional[str]:
        """
        Infer service from common port.

        Examples:
            22 → 'ssh'
            3306 → 'mysql'
            443 → 'https'
        """
        return self.PORT_SERVICES.get(port)
