#!/usr/bin/env python3
"""
Attack chain analysis and visualization.
Builds attack graphs from evidence timeline and generates Mermaid.js diagrams.
"""

from datetime import datetime
from typing import Dict, List, Set, Tuple


class AttackChainAnalyzer:
    """Analyze and visualize attack chains from evidence."""

    def __init__(self):
        self.phase_colors = {
            "reconnaissance": "#17a2b8",
            "enumeration": "#28a745",
            "exploitation": "#ffc107",
            "post_exploitation": "#dc3545",
        }

    def build_attack_chain(
        self, evidence: Dict, findings: List[Dict], credentials: List[Dict]
    ) -> Dict:
        """
        Build attack chain from evidence timeline.

        Returns dict with nodes and edges for graph visualization.
        """
        nodes = []
        edges = []
        node_id = 0

        # Track hosts and services
        hosts_seen = set()

        # Phase 1: Reconnaissance nodes
        recon_items = evidence.get("reconnaissance", [])
        if recon_items:
            recon_node = {
                "id": f"node{node_id}",
                "label": f"Reconnaissance\\n{len(recon_items)} items",
                "type": "reconnaissance",
                "count": len(recon_items),
            }
            nodes.append(recon_node)
            recon_id = recon_node["id"]
            node_id += 1
        else:
            recon_id = None

        # Phase 2: Enumeration nodes (per host)
        enum_items = evidence.get("enumeration", [])
        enum_nodes = {}

        for item in enum_items:
            host = item.get("host", "unknown")
            hosts_seen.add(host)

            if host not in enum_nodes:
                enum_node = {
                    "id": f"node{node_id}",
                    "label": f"Enumeration\\n{host}",
                    "type": "enumeration",
                    "host": host,
                }
                nodes.append(enum_node)
                enum_nodes[host] = enum_node["id"]
                node_id += 1

                # Link from reconnaissance
                if recon_id:
                    edges.append(
                        {"from": recon_id, "to": enum_node["id"], "label": "discovered"}
                    )

        # Phase 3: Exploitation nodes
        exploit_items = evidence.get("exploitation", [])
        exploit_nodes = {}

        for item in exploit_items:
            host = item.get("host", "unknown")
            service = item.get("service", "service")
            hosts_seen.add(host)

            key = f"{host}:{service}"
            if key not in exploit_nodes:
                exploit_node = {
                    "id": f"node{node_id}",
                    "label": f"Exploit\\n{host}\\n{service}",
                    "type": "exploitation",
                    "host": host,
                    "service": service,
                }
                nodes.append(exploit_node)
                exploit_nodes[key] = exploit_node["id"]
                node_id += 1

                # Link from enumeration
                if host in enum_nodes:
                    edges.append(
                        {
                            "from": enum_nodes[host],
                            "to": exploit_node["id"],
                            "label": "exploited",
                        }
                    )

        # Add credential nodes
        cred_nodes = {}
        for cred in credentials:
            host = cred.get("host", "unknown")
            service = cred.get("service", "service")
            username = cred.get("username", "user")
            hosts_seen.add(host)

            key = f"{host}:{service}:{username}"
            if key not in cred_nodes:
                cred_node = {
                    "id": f"node{node_id}",
                    "label": f"Credential\\n{username}@{host}",
                    "type": "credential",
                    "host": host,
                }
                nodes.append(cred_node)
                cred_nodes[key] = cred_node["id"]
                node_id += 1

                # Link from exploitation
                exploit_key = f"{host}:{service}"
                if exploit_key in exploit_nodes:
                    edges.append(
                        {
                            "from": exploit_nodes[exploit_key],
                            "to": cred_node["id"],
                            "label": "obtained",
                        }
                    )

        # Phase 4: Post-exploitation nodes
        post_items = evidence.get("post_exploitation", [])
        if post_items:
            # Group by host
            post_by_host = {}
            for item in post_items:
                host = item.get("host", "unknown")
                hosts_seen.add(host)
                if host not in post_by_host:
                    post_by_host[host] = []
                post_by_host[host].append(item)

            for host, items in post_by_host.items():
                post_node = {
                    "id": f"node{node_id}",
                    "label": f"Post-Exploit\\n{host}\\n{len(items)} items",
                    "type": "post_exploitation",
                    "host": host,
                }
                nodes.append(post_node)
                node_id += 1

                # Link from credentials or exploits
                linked = False
                for cred_key, cred_id in cred_nodes.items():
                    if host in cred_key:
                        edges.append(
                            {"from": cred_id, "to": post_node["id"], "label": "access"}
                        )
                        linked = True
                        break

                if not linked:
                    for exploit_key, exploit_id in exploit_nodes.items():
                        if host in exploit_key:
                            edges.append(
                                {
                                    "from": exploit_id,
                                    "to": post_node["id"],
                                    "label": "access",
                                }
                            )
                            break

        return {
            "nodes": nodes,
            "edges": edges,
            "hosts": list(hosts_seen),
            "phases": {
                "reconnaissance": len(recon_items),
                "enumeration": len(enum_items),
                "exploitation": len(exploit_items),
                "post_exploitation": len(post_items),
            },
        }

    def generate_mermaid_diagram(self, chain: Dict) -> str:
        """Generate Mermaid.js flowchart from attack chain."""
        if not chain["nodes"]:
            return ""

        mermaid = "graph TD\n"

        # Define node styles
        mermaid += "    classDef recon fill:#17a2b8,stroke:#0c5460,color:#fff\n"
        mermaid += "    classDef enum fill:#28a745,stroke:#155724,color:#fff\n"
        mermaid += "    classDef exploit fill:#ffc107,stroke:#856404,color:#000\n"
        mermaid += "    classDef post fill:#dc3545,stroke:#721c24,color:#fff\n"
        mermaid += "    classDef cred fill:#6f42c1,stroke:#3d1f66,color:#fff\n\n"

        # Add nodes
        for node in chain["nodes"]:
            node_id = node["id"]
            label = node["label"].replace("\n", "<br/>")
            node_type = node["type"]

            # Shape based on type
            if node_type == "reconnaissance":
                mermaid += f"    {node_id}[{label}]:::recon\n"
            elif node_type == "enumeration":
                mermaid += f"    {node_id}[{label}]:::enum\n"
            elif node_type == "exploitation":
                mermaid += f"    {node_id}[{label}]:::exploit\n"
            elif node_type == "post_exploitation":
                mermaid += f"    {node_id}[{label}]:::post\n"
            elif node_type == "credential":
                mermaid += f"    {node_id}[{label}]:::cred\n"

        # Add edges
        mermaid += "\n"
        for edge in chain["edges"]:
            label = edge.get("label", "")
            mermaid += f"    {edge['from']} -->|{label}| {edge['to']}\n"

        return mermaid

    def get_attack_summary(self, chain: Dict) -> Dict:
        """Generate summary statistics for attack chain."""
        return {
            "total_nodes": len(chain["nodes"]),
            "total_edges": len(chain["edges"]),
            "hosts_compromised": len(chain["hosts"]),
            "phases_active": sum(1 for count in chain["phases"].values() if count > 0),
            "longest_path": self._calculate_longest_path(chain),
            "critical_nodes": self._identify_critical_nodes(chain),
        }

    def _calculate_longest_path(self, chain: Dict) -> int:
        """Calculate longest path in attack graph (simplified)."""
        if not chain["edges"]:
            return len(chain["nodes"])

        # Build adjacency list
        adj = {}
        for edge in chain["edges"]:
            if edge["from"] not in adj:
                adj[edge["from"]] = []
            adj[edge["from"]].append(edge["to"])

        # Find nodes with no incoming edges (starting points)
        has_incoming = set(edge["to"] for edge in chain["edges"])
        start_nodes = [
            node["id"] for node in chain["nodes"] if node["id"] not in has_incoming
        ]

        if not start_nodes:
            return 1

        # DFS to find longest path
        def dfs(node, visited):
            if node not in adj:
                return 1

            max_depth = 1
            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    depth = 1 + dfs(neighbor, visited)
                    max_depth = max(max_depth, depth)
                    visited.remove(neighbor)

            return max_depth

        longest = max(dfs(start, {start}) for start in start_nodes)
        return longest

    def _identify_critical_nodes(self, chain: Dict) -> List[str]:
        """Identify critical nodes (high connectivity)."""
        # Count edges per node
        node_degree = {}
        for edge in chain["edges"]:
            node_degree[edge["from"]] = node_degree.get(edge["from"], 0) + 1
            node_degree[edge["to"]] = node_degree.get(edge["to"], 0) + 1

        # Critical if degree > 2
        critical = [node_id for node_id, degree in node_degree.items() if degree > 2]
        return critical

    def build_host_centric_chain(
        self,
        evidence: Dict,
        findings: List[Dict],
        credentials: List[Dict],
        attack_surface: Dict = None,
    ) -> Dict:
        """
        Build host-centric attack chain showing per-host attack journey
        and lateral movement between hosts.

        SMART INFERENCE: Creates nodes based on available data, not just explicit evidence.
        - If we have findings → we discovered and enumerated the host
        - If we have services → we enumerated them
        - If we have credentials → we exploited something
        - If findings indicate exploitation → show exploitation phase

        Returns:
            {
                'hosts': [{host, hostname, nodes, internal_edges}, ...],
                'lateral_edges': [...],
                'summary': {...}
            }
        """
        host_chains = {}
        lateral_edges = []
        node_counter = [0]

        def next_node_id():
            node_counter[0] += 1
            return f"n{node_counter[0]}"

        # Build host info from attack_surface (primary source)
        host_info = {}
        if attack_surface and attack_surface.get("hosts"):
            for h in attack_surface["hosts"]:
                host_ip = h.get("host")
                if host_ip:
                    host_info[host_ip] = {
                        "hostname": h.get("hostname"),
                        "score": h.get("score", 0),
                        "services": h.get("services", []),
                        "findings_count": h.get("findings", 0),
                        "critical_findings": h.get("critical_findings", 0),
                        "open_ports": h.get("open_ports", 0),
                    }

        # Collect findings by host
        findings_by_host = {}
        for f in findings:
            host = f.get("ip_address")
            if host:
                if host not in findings_by_host:
                    findings_by_host[host] = []
                findings_by_host[host].append(f)

        # Collect credentials by host
        creds_by_host = {}
        for c in credentials:
            host = c.get("ip_address") or c.get("host")
            if host:
                if host not in creds_by_host:
                    creds_by_host[host] = []
                creds_by_host[host].append(c)

        # Collect evidence by host and phase
        evidence_by_host = {}
        for phase in [
            "reconnaissance",
            "enumeration",
            "exploitation",
            "post_exploitation",
        ]:
            for item in evidence.get(phase, []):
                host = item.get("host") or item.get("ip_address")
                if host:
                    if host not in evidence_by_host:
                        evidence_by_host[host] = {
                            "recon": [],
                            "enum": [],
                            "exploit": [],
                            "post": [],
                        }
                    if phase == "reconnaissance":
                        evidence_by_host[host]["recon"].append(item)
                    elif phase == "enumeration":
                        evidence_by_host[host]["enum"].append(item)
                    elif phase == "exploitation":
                        evidence_by_host[host]["exploit"].append(item)
                    else:
                        evidence_by_host[host]["post"].append(item)

        # Get all hosts (union of all sources)
        all_hosts = (
            set(host_info.keys())
            | set(findings_by_host.keys())
            | set(creds_by_host.keys())
            | set(evidence_by_host.keys())
        )

        # Build chain for each host
        for host in all_hosts:
            info = host_info.get(host, {})
            host_findings = findings_by_host.get(host, [])
            host_creds = creds_by_host.get(host, [])
            host_evidence = evidence_by_host.get(
                host, {"recon": [], "enum": [], "exploit": [], "post": []}
            )

            # Get services from attack_surface
            services = info.get("services", [])
            service_count = len(services) if isinstance(services, list) else services

            # Categorize findings
            critical_findings = [
                f for f in host_findings if f.get("severity") == "critical"
            ]
            high_findings = [f for f in host_findings if f.get("severity") == "high"]

            # Determine what phases to show (SMART INFERENCE)
            has_any_data = bool(
                host_findings or host_creds or services or any(host_evidence.values())
            )
            has_services = service_count > 0 or host_evidence["enum"]
            has_vulns = bool(critical_findings or high_findings)
            has_exploitation = bool(
                host_creds
                or host_evidence["exploit"]
                or any(
                    f.get("title", "").lower().find("exploit") >= 0
                    for f in host_findings
                )
                or any(
                    f.get("finding_type") in ["exploitation", "data_breach"]
                    for f in host_findings
                )
            )
            has_creds = bool(host_creds)
            has_post = bool(host_evidence["post"])

            # Check for exploited services in attack_surface
            exploited_services = []
            if isinstance(services, list):
                exploited_services = [
                    s for s in services if s.get("status") == "exploited"
                ]
                if exploited_services:
                    has_exploitation = True

            host_data = {
                "host": host,
                "hostname": info.get("hostname"),
                "nodes": [],
                "internal_edges": [],
                "score": info.get("score", 0),
            }

            prev_node_id = None

            # Phase 1: Discovery (INFERRED if we have any data about this host)
            if has_any_data:
                node_id = next_node_id()
                recon_count = len(host_evidence["recon"])
                if recon_count > 0:
                    detail = f"{recon_count} scans"
                elif info.get("open_ports"):
                    detail = f"{info['open_ports']} ports found"
                else:
                    detail = "Host identified"
                host_data["nodes"].append(
                    {
                        "id": node_id,
                        "label": "Discovery",
                        "detail": detail,
                        "type": "discovery",
                        "phase": 1,
                    }
                )
                prev_node_id = node_id

            # Phase 2: Enumeration (INFERRED if we have services or findings)
            if has_services or host_findings:
                node_id = next_node_id()
                enum_count = len(host_evidence["enum"])
                if enum_count > 0:
                    # Get service names from evidence
                    svc_names = set()
                    for item in host_evidence["enum"]:
                        svc = item.get("service") or item.get("tool", "")
                        if svc:
                            svc_names.add(svc)
                    detail = (
                        ", ".join(list(svc_names)[:3])
                        if svc_names
                        else f"{enum_count} items"
                    )
                elif service_count > 0:
                    detail = f"{service_count} services"
                else:
                    detail = "Services scanned"
                host_data["nodes"].append(
                    {
                        "id": node_id,
                        "label": "Enumeration",
                        "detail": detail,
                        "type": "enumeration",
                        "phase": 2,
                    }
                )
                if prev_node_id:
                    host_data["internal_edges"].append(
                        {"from": prev_node_id, "to": node_id, "label": "scanned"}
                    )
                prev_node_id = node_id

            # Phase 3: Vulnerabilities (if we have critical/high findings)
            if has_vulns:
                node_id = next_node_id()
                # Get top vulnerability title
                top_vuln = (critical_findings + high_findings)[0]
                top_title = top_vuln.get("title", "Vulnerability")[:25]
                vuln_detail = []
                if critical_findings:
                    vuln_detail.append(f"{len(critical_findings)} critical")
                if high_findings:
                    vuln_detail.append(f"{len(high_findings)} high")
                host_data["nodes"].append(
                    {
                        "id": node_id,
                        "label": top_title,
                        "detail": ", ".join(vuln_detail),
                        "type": "vulnerability",
                        "phase": 3,
                    }
                )
                if prev_node_id:
                    host_data["internal_edges"].append(
                        {"from": prev_node_id, "to": node_id, "label": "found"}
                    )
                prev_node_id = node_id

            # Phase 4: Exploitation (if we have creds, exploit evidence, or exploited services)
            if has_exploitation:
                node_id = next_node_id()
                exploit_count = len(host_evidence["exploit"])
                if exploited_services:
                    svc_names = [
                        s.get("service", "service") for s in exploited_services[:2]
                    ]
                    detail = ", ".join(svc_names)
                elif exploit_count > 0:
                    detail = f"{exploit_count} exploits"
                elif has_creds:
                    detail = "Access gained"
                else:
                    detail = "Exploited"
                host_data["nodes"].append(
                    {
                        "id": node_id,
                        "label": "Exploited",
                        "detail": detail,
                        "type": "exploitation",
                        "phase": 4,
                    }
                )
                if prev_node_id:
                    host_data["internal_edges"].append(
                        {"from": prev_node_id, "to": node_id, "label": "exploited"}
                    )
                prev_node_id = node_id

            # Phase 5: Credentials (if we have creds)
            if has_creds:
                node_id = next_node_id()
                usernames = set(c.get("username", "user") for c in host_creds)
                host_data["nodes"].append(
                    {
                        "id": node_id,
                        "label": "Credentials",
                        "detail": ", ".join(list(usernames)[:3]),
                        "type": "credential",
                        "phase": 5,
                        "creds": host_creds,
                    }
                )
                if prev_node_id:
                    host_data["internal_edges"].append(
                        {"from": prev_node_id, "to": node_id, "label": "dumped"}
                    )
                prev_node_id = node_id

            # Phase 6: Post-Exploitation (if we have post evidence)
            if has_post:
                node_id = next_node_id()
                host_data["nodes"].append(
                    {
                        "id": node_id,
                        "label": "Post-Exploit",
                        "detail": f"{len(host_evidence['post'])} actions",
                        "type": "post_exploitation",
                        "phase": 6,
                    }
                )
                if prev_node_id:
                    host_data["internal_edges"].append(
                        {"from": prev_node_id, "to": node_id, "label": "accessed"}
                    )

            # Only add host if it has nodes
            if host_data["nodes"]:
                host_chains[host] = host_data

        # Detect lateral movement (credentials from host A used on host B)
        for source_host, source_data in host_chains.items():
            for node in source_data["nodes"]:
                if node["type"] == "credential" and node.get("creds"):
                    for target_host, target_data in host_chains.items():
                        if target_host == source_host:
                            continue
                        # If target was exploited and source has creds, potential lateral
                        target_exploited = any(
                            n["type"] in ["exploitation", "post_exploitation"]
                            for n in target_data["nodes"]
                        )
                        if target_exploited:
                            # Find target's first exploitation node
                            for target_node in target_data["nodes"]:
                                if target_node["type"] == "exploitation":
                                    cred_username = node["creds"][0].get("username", "")
                                    lateral_edges.append(
                                        {
                                            "from_host": source_host,
                                            "from_node": node["id"],
                                            "to_host": target_host,
                                            "to_node": target_node["id"],
                                            "label": "lateral",
                                            "credential": cred_username,
                                        }
                                    )
                                    break
                            break  # Only one lateral edge per source-target pair

        # Sort hosts by score (highest first)
        sorted_hosts = sorted(
            host_chains.values(), key=lambda x: x.get("score", 0), reverse=True
        )

        # Calculate summary
        total_nodes = sum(len(h["nodes"]) for h in sorted_hosts)
        total_internal_edges = sum(len(h["internal_edges"]) for h in sorted_hosts)
        hosts_with_exploitation = sum(
            1
            for h in sorted_hosts
            if any(
                n["type"] in ["exploitation", "credential", "post_exploitation"]
                for n in h["nodes"]
            )
        )

        return {
            "hosts": sorted_hosts,
            "lateral_edges": lateral_edges,
            "summary": {
                "total_hosts": len(sorted_hosts),
                "hosts_exploited": hosts_with_exploitation,
                "total_nodes": total_nodes,
                "total_internal_edges": total_internal_edges,
                "lateral_movements": len(lateral_edges),
            },
        }

    def _sanitize_mermaid_label(self, text: str) -> str:
        """Sanitize text for use in Mermaid labels."""
        if not text:
            return ""
        # Replace characters that break Mermaid syntax
        text = str(text)
        text = text.replace('"', "'")  # Double quotes to single
        text = text.replace("[", "(")  # Brackets to parens
        text = text.replace("]", ")")
        text = text.replace("{", "(")
        text = text.replace("}", ")")
        text = text.replace("<", "")  # Remove angle brackets (except our <br/>)
        text = text.replace(">", "")
        text = text.replace("|", "-")  # Pipe breaks edge labels
        text = text.replace("#", "")  # Hash can cause issues
        text = text.replace("&", "and")
        text = text.replace("\n", " ")
        text = text.replace("\r", "")
        # Limit length
        if len(text) > 40:
            text = text[:37] + "..."
        return text

    def generate_host_centric_mermaid(self, chain: Dict) -> str:
        """
        Generate Mermaid.js diagram with subgraphs per host.
        Shows internal attack progression and lateral movement.
        """
        hosts = chain.get("hosts", [])
        lateral_edges = chain.get("lateral_edges", [])

        if not hosts:
            return ""

        # Limit to top 6 hosts for readability
        display_hosts = hosts[:6]

        mermaid = "graph TD\n\n"

        # Define node styles
        mermaid += "    %% Node styles\n"
        mermaid += "    classDef discovery fill:#17a2b8,stroke:#0c5460,color:#fff\n"
        mermaid += "    classDef enumeration fill:#28a745,stroke:#155724,color:#fff\n"
        mermaid += "    classDef vulnerability fill:#ffc107,stroke:#856404,color:#000\n"
        mermaid += "    classDef exploitation fill:#fd7e14,stroke:#c45d00,color:#fff\n"
        mermaid += "    classDef credential fill:#6f42c1,stroke:#3d1f66,color:#fff\n"
        mermaid += (
            "    classDef post_exploitation fill:#dc3545,stroke:#721c24,color:#fff\n\n"
        )

        # Generate subgraph for each host
        for idx, host_data in enumerate(display_hosts):
            host_ip = host_data["host"]
            hostname = host_data.get("hostname", "")

            # Sanitize host IP for Mermaid ID
            safe_host = host_ip.replace(".", "_").replace("-", "_").replace(":", "_")
            # Ensure ID starts with letter
            if safe_host[0].isdigit():
                safe_host = "h" + safe_host

            # Sanitize subgraph title
            subgraph_title = self._sanitize_mermaid_label(host_ip)
            if hostname:
                safe_hostname = self._sanitize_mermaid_label(hostname[:15])
                subgraph_title = f"{subgraph_title} - {safe_hostname}"

            mermaid += f'    subgraph {safe_host}["{subgraph_title}"]\n'
            mermaid += f"        direction TB\n"

            # Add nodes for this host
            for node in host_data["nodes"]:
                node_id = node["id"]
                label = self._sanitize_mermaid_label(node["label"])
                detail = self._sanitize_mermaid_label(node.get("detail", ""))
                node_type = node["type"]

                # Format label - use line break for detail
                if detail:
                    full_label = f"{label}<br/>{detail}"
                else:
                    full_label = label

                mermaid += f'        {node_id}["{full_label}"]:::{node_type}\n'

            # Add internal edges
            for edge in host_data["internal_edges"]:
                edge_label = self._sanitize_mermaid_label(edge.get("label", ""))
                mermaid += f"        {edge['from']} -->|{edge_label}| {edge['to']}\n"

            mermaid += "    end\n\n"

        # Add lateral movement edges between subgraphs (only for displayed hosts)
        displayed_host_ips = {h["host"] for h in display_hosts}
        if lateral_edges:
            mermaid += "    %% Lateral movement\n"
            for edge in lateral_edges:
                # Only show lateral edges between displayed hosts
                if edge["from_host"] not in displayed_host_ips:
                    continue
                if edge["to_host"] not in displayed_host_ips:
                    continue

                from_node = edge["from_node"]
                to_node = edge["to_node"]
                cred = self._sanitize_mermaid_label(edge.get("credential", ""))
                label = f"lateral: {cred}" if cred else "lateral"

                mermaid += f"    {from_node} -.->|{label}| {to_node}\n"

        return mermaid

    def get_host_centric_summary(self, chain: Dict) -> Dict:
        """Generate summary statistics for host-centric attack chain."""
        summary = chain.get("summary", {})
        hosts = chain.get("hosts", [])
        lateral_edges = chain.get("lateral_edges", [])

        # Find the host with deepest attack progression
        max_depth = 0
        deepest_host = None
        for host_data in hosts:
            depth = len(host_data["nodes"])
            if depth > max_depth:
                max_depth = depth
                deepest_host = host_data["host"]

        # Count hosts at each phase
        phase_counts = {
            "discovery": 0,
            "enumeration": 0,
            "vulnerability": 0,
            "exploitation": 0,
            "credential": 0,
            "post_exploitation": 0,
        }
        for host_data in hosts:
            for node in host_data["nodes"]:
                node_type = node["type"]
                if node_type in phase_counts:
                    phase_counts[node_type] += 1

        return {
            "total_hosts": summary.get("total_hosts", len(hosts)),
            "hosts_exploited": summary.get("hosts_exploited", 0),
            "total_nodes": summary.get("total_nodes", 0),
            "lateral_movements": len(lateral_edges),
            "deepest_attack": max_depth,
            "deepest_host": deepest_host,
            "phase_counts": phase_counts,
        }
