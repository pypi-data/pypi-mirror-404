#!/usr/bin/env python3
"""
souleyez.importers.smart_importer - Intelligent data import with type detection
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

import defusedxml.ElementTree as ET


class SmartImporter:
    """Smart importer that detects and categorizes data types."""

    def __init__(self):
        self.detected_types = {
            "hosts": 0,
            "services": 0,
            "vulnerabilities": 0,
            "credentials": 0,
            "web_paths": 0,
            "notes": 0,
        }

    def analyze_msf_xml(self, xml_path: str) -> Dict[str, Any]:
        """
        Analyze MSF XML file and detect what data types it contains.

        Returns:
            Dict with counts of each data type and preview data
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            analysis = {
                "file_type": "msf_xml",
                "hosts": {"count": 0, "preview": []},
                "services": {"count": 0, "preview": []},
                "vulnerabilities": {"count": 0, "preview": []},
                "credentials": {"count": 0, "preview": []},
                "web_paths": {"count": 0, "preview": []},
                "notes": {"count": 0, "preview": []},
            }

            # Analyze hosts
            hosts = root.findall(".//host")
            analysis["hosts"]["count"] = len(hosts)
            for host in hosts[:3]:  # Preview first 3
                address = host.find("address")
                name = host.find("name")
                os_name = host.find("os-name")
                analysis["hosts"]["preview"].append(
                    {
                        "address": address.text if address is not None else "",
                        "name": name.text if name is not None else "",
                        "os": os_name.text if os_name is not None else "",
                    }
                )

            # Analyze services
            services = root.findall(".//service")
            analysis["services"]["count"] = len(services)
            for svc in services[:3]:
                port = svc.find("port")
                proto = svc.find("proto")
                name = svc.find("name")
                info = svc.find("info")
                analysis["services"]["preview"].append(
                    {
                        "port": port.text if port is not None else "",
                        "proto": proto.text if proto is not None else "",
                        "name": name.text if name is not None else "",
                        "info": info.text if info is not None else "",
                    }
                )

            # Analyze vulnerabilities (notes with vuln refs)
            notes = root.findall(".//note")
            for note in notes:
                ntype = note.find("ntype")
                data = note.find("data")

                if ntype is not None and data is not None:
                    # Check if it's a vulnerability
                    if "vuln" in ntype.text.lower() or self._looks_like_vuln(data.text):
                        analysis["vulnerabilities"]["count"] += 1
                        if len(analysis["vulnerabilities"]["preview"]) < 3:
                            analysis["vulnerabilities"]["preview"].append(
                                {
                                    "type": ntype.text,
                                    "data": (
                                        data.text[:100] + "..."
                                        if len(data.text) > 100
                                        else data.text
                                    ),
                                }
                            )
                    else:
                        analysis["notes"]["count"] += 1
                        if len(analysis["notes"]["preview"]) < 3:
                            analysis["notes"]["preview"].append(
                                {
                                    "type": ntype.text,
                                    "data": (
                                        data.text[:100] + "..."
                                        if len(data.text) > 100
                                        else data.text
                                    ),
                                }
                            )

            # Analyze credentials
            creds = root.findall(".//cred")
            analysis["credentials"]["count"] = len(creds)
            for cred in creds[:3]:
                user = cred.find("user")
                pass_elem = cred.find("pass")
                service = cred.find("service")
                analysis["credentials"]["preview"].append(
                    {
                        "username": user.text if user is not None else "",
                        "password": (
                            pass_elem.text[:20] + "..."
                            if pass_elem is not None and len(pass_elem.text) > 20
                            else (pass_elem.text if pass_elem is not None else "")
                        ),
                        "service": service.text if service is not None else "",
                    }
                )

            # Analyze web paths/findings
            web_vulns = root.findall(".//web_vuln")
            analysis["web_paths"]["count"] = len(web_vulns)
            for wv in web_vulns[:3]:
                path = wv.find("path")
                method = wv.find("method")
                pname = wv.find("pname")
                analysis["web_paths"]["preview"].append(
                    {
                        "path": path.text if path is not None else "",
                        "method": method.text if method is not None else "",
                        "param": pname.text if pname is not None else "",
                    }
                )

            return analysis

        except Exception as e:
            return {"error": str(e)}

    def _looks_like_vuln(self, text: str) -> bool:
        """Check if text looks like vulnerability data."""
        vuln_keywords = [
            "cve-",
            "exploit",
            "vulnerable",
            "vulnerability",
            "attack",
            "injection",
            "xss",
            "sqli",
            "rce",
            "buffer overflow",
            "authentication bypass",
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in vuln_keywords)

    def preview_import(self, xml_path: str) -> Dict[str, Any]:
        """
        Preview what will be imported from the file.

        Returns detailed breakdown of importable data.
        """
        return self.analyze_msf_xml(xml_path)

    def selective_import(
        self, xml_path: str, engagement_id: int, import_types: List[str]
    ) -> Dict[str, int]:
        """
        Import only selected data types.

        Args:
            xml_path: Path to MSF XML file
            engagement_id: Target engagement ID
            import_types: List of types to import
                         ['hosts', 'services', 'vulnerabilities', 'credentials', etc]

        Returns:
            Dict with counts of imported items per type
        """
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        results = {
            "hosts": 0,
            "services": 0,
            "vulnerabilities": 0,
            "credentials": 0,
            "web_paths": 0,
            "notes": 0,
        }

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            hm = HostManager()
            fm = FindingsManager()
            cm = CredentialsManager()

            # Import hosts
            if "hosts" in import_types:
                hosts = root.findall(".//host")
                for host_elem in hosts:
                    address = host_elem.find("address")
                    if address is not None and address.text:
                        host_data = {"ip": address.text}

                        name = host_elem.find("name")
                        if name is not None and name.text:
                            host_data["hostname"] = name.text

                        os_name = host_elem.find("os-name")
                        if os_name is not None and os_name.text:
                            host_data["os"] = os_name.text

                        host_data["status"] = "up"
                        host_id = hm.add_or_update_host(engagement_id, host_data)
                        results["hosts"] += 1

                        # Import services for this host
                        if "services" in import_types:
                            for svc in host_elem.findall(".//service"):
                                port = svc.find("port")
                                proto = svc.find("proto")
                                name = svc.find("name")
                                info = svc.find("info")
                                state = svc.find("state")

                                if port is not None:
                                    hm.add_service(
                                        host_id=host_id,
                                        port=int(port.text),
                                        protocol=(
                                            proto.text if proto is not None else "tcp"
                                        ),
                                        state=(
                                            state.text if state is not None else "open"
                                        ),
                                        service_name=(
                                            name.text if name is not None else None
                                        ),
                                        service_version=(
                                            info.text if info is not None else None
                                        ),
                                    )
                                    results["services"] += 1

            # Import credentials
            if "credentials" in import_types:
                creds = root.findall(".//cred")
                for cred in creds:
                    user = cred.find("user")
                    pass_elem = cred.find("pass")
                    service_name = cred.find("service")

                    if user is not None:
                        # Try to find associated host
                        host_elem = cred.find(".//host")
                        target_host = None
                        if host_elem is not None:
                            addr = host_elem.find("address")
                            if addr is not None:
                                target_host = addr.text

                        cm.add_credential(
                            engagement_id=engagement_id,
                            username=user.text,
                            password=pass_elem.text if pass_elem is not None else None,
                            host=target_host,
                            service=(
                                service_name.text if service_name is not None else None
                            ),
                            source="msf_import",
                        )
                        results["credentials"] += 1

            # Import vulnerabilities as findings
            if "vulnerabilities" in import_types:
                notes = root.findall(".//note")
                for note in notes:
                    ntype = note.find("ntype")
                    data = note.find("data")

                    if ntype is not None and data is not None:
                        if "vuln" in ntype.text.lower() or self._looks_like_vuln(
                            data.text
                        ):
                            # Extract host if available
                            host_elem = note.find(".//host")
                            host_ip = None
                            host_id = None

                            if host_elem is not None:
                                addr = host_elem.find("address")
                                if addr is not None:
                                    host_ip = addr.text
                                    host_obj = hm.get_host_by_ip(engagement_id, host_ip)
                                    if host_obj:
                                        host_id = host_obj["id"]

                            fm.add_finding(
                                engagement_id=engagement_id,
                                host_id=host_id,
                                title=ntype.text,
                                finding_type="vulnerability",
                                severity="medium",
                                description=data.text,
                                tool="msf_import",
                            )
                            results["vulnerabilities"] += 1

            # Import web vulnerabilities
            if "web_paths" in import_types:
                web_vulns = root.findall(".//web_vuln")
                for wv in web_vulns:
                    path = wv.find("path")
                    method = wv.find("method")
                    pname = wv.find("pname")
                    proof = wv.find("proof")

                    if path is not None:
                        title = f"Web vulnerability in {path.text}"
                        if pname is not None:
                            title += f" (parameter: {pname.text})"

                        description = (
                            f"Method: {method.text if method is not None else 'N/A'}\n"
                        )
                        description += f"Path: {path.text}\n"
                        if proof is not None:
                            description += f"Proof: {proof.text}\n"

                        fm.add_finding(
                            engagement_id=engagement_id,
                            host_id=None,
                            title=title,
                            finding_type="web_vulnerability",
                            severity="medium",
                            description=description,
                            tool="msf_import",
                            path=path.text if path is not None else None,
                        )
                        results["web_paths"] += 1

            return results

        except Exception as e:
            return {"error": str(e)}


def format_preview_summary(analysis: Dict[str, Any]) -> str:
    """Format analysis results into readable summary."""
    if "error" in analysis:
        return f"Error analyzing file: {analysis['error']}"

    lines = []
    lines.append("\n" + "=" * 70)
    lines.append("IMPORT PREVIEW")
    lines.append("=" * 70 + "\n")

    total_items = sum(
        analysis[key]["count"]
        for key in [
            "hosts",
            "services",
            "vulnerabilities",
            "credentials",
            "web_paths",
            "notes",
        ]
        if key in analysis
    )

    lines.append(f"Total items detected: {total_items}\n")

    for data_type in [
        "hosts",
        "services",
        "vulnerabilities",
        "credentials",
        "web_paths",
        "notes",
    ]:
        if data_type in analysis and analysis[data_type]["count"] > 0:
            count = analysis[data_type]["count"]
            preview = analysis[data_type]["preview"]

            lines.append(f"  ✓ {data_type.upper()}: {count}")

            if preview:
                for item in preview[:2]:  # Show max 2 examples
                    lines.append(f"    - {str(item)[:60]}...")
                lines.append("")

    return "\n".join(lines)
