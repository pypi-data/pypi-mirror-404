#!/usr/bin/env python3
"""
Chart generation for pentest reports.
Creates interactive Chart.js charts for HTML reports.
"""

import json
from typing import Dict, List


class ChartGenerator:
    """Generate Chart.js chart configurations."""

    def __init__(self):
        self.colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745",
            "info": "#17a2b8",
        }

    def severity_distribution_chart(self, findings_by_severity: Dict) -> str:
        """Generate pie chart showing finding distribution by severity."""
        data = {
            "Critical": len(findings_by_severity.get("critical", [])),
            "High": len(findings_by_severity.get("high", [])),
            "Medium": len(findings_by_severity.get("medium", [])),
            "Low": len(findings_by_severity.get("low", [])),
            "Info": len(findings_by_severity.get("info", [])),
        }

        # Filter out zero values
        filtered_data = {k: v for k, v in data.items() if v > 0}

        if not filtered_data:
            return ""

        labels = list(filtered_data.keys())
        values = list(filtered_data.values())
        colors = [self.colors[k.lower()] for k in labels]

        config = {
            "type": "doughnut",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "data": values,
                        "backgroundColor": colors,
                        "borderWidth": 2,
                        "borderColor": "#fff",
                    }
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": True,
                "plugins": {
                    "legend": {"position": "right", "labels": {"font": {"size": 14}}},
                    "title": {
                        "display": True,
                        "text": "Findings by Severity",
                        "font": {"size": 16, "weight": "bold"},
                    },
                },
            },
        }

        return json.dumps(config)

    def host_impact_chart(self, attack_surface: Dict) -> str:
        """Generate bar chart showing findings per host."""
        hosts = attack_surface.get("hosts", [])

        # Sort by findings count (descending) and take top 10
        sorted_hosts = sorted(hosts, key=lambda h: h.get("findings", 0), reverse=True)[
            :10
        ]

        if not sorted_hosts:
            return ""

        labels = []
        critical_data = []
        high_data = []
        other_data = []

        for host in sorted_hosts:
            # Use hostname or IP
            label = host.get("hostname") or host.get("host", "Unknown")
            labels.append(label)

            critical_data.append(host.get("critical_findings", 0))
            high_findings = host.get("findings", 0) - host.get("critical_findings", 0)
            # Assume 30% of non-critical are high, rest are medium/low (simplified)
            high_count = int(high_findings * 0.3)
            other_count = high_findings - high_count

            high_data.append(high_count)
            other_data.append(other_count)

        config = {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Critical",
                        "data": critical_data,
                        "backgroundColor": self.colors["critical"],
                        "stack": "stack0",
                    },
                    {
                        "label": "High",
                        "data": high_data,
                        "backgroundColor": self.colors["high"],
                        "stack": "stack0",
                    },
                    {
                        "label": "Medium/Low",
                        "data": other_data,
                        "backgroundColor": self.colors["medium"],
                        "stack": "stack0",
                    },
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": True,
                "indexAxis": "y",
                "plugins": {
                    "legend": {"display": True, "position": "top"},
                    "title": {
                        "display": True,
                        "text": "Top 10 Hosts by Finding Count",
                        "font": {"size": 16, "weight": "bold"},
                    },
                },
                "scales": {
                    "x": {
                        "stacked": True,
                        "title": {"display": True, "text": "Number of Findings"},
                    },
                    "y": {"stacked": True},
                },
            },
        }

        return json.dumps(config)

    def exploitation_progress_chart(self, attack_surface: Dict) -> str:
        """Generate gauge/progress chart for exploitation rate."""
        overview = attack_surface.get("overview", {})
        total_services = overview.get("total_services", 0)
        exploited = overview.get("exploited_services", 0)

        if total_services == 0:
            return ""

        exploitation_rate = round((exploited / total_services) * 100, 1)
        remaining = 100 - exploitation_rate

        # Determine color based on rate
        if exploitation_rate >= 50:
            color = self.colors["critical"]
        elif exploitation_rate >= 25:
            color = self.colors["high"]
        elif exploitation_rate >= 10:
            color = self.colors["medium"]
        else:
            color = self.colors["low"]

        config = {
            "type": "doughnut",
            "data": {
                "labels": ["Exploited", "Not Exploited"],
                "datasets": [
                    {
                        "data": [exploitation_rate, remaining],
                        "backgroundColor": [color, "#e9ecef"],
                        "borderWidth": 0,
                        "circumference": 180,
                        "rotation": 270,
                    }
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": True,
                "plugins": {
                    "legend": {"display": False},
                    "title": {
                        "display": True,
                        "text": f"Exploitation Rate: {exploitation_rate}%",
                        "font": {"size": 16, "weight": "bold"},
                    },
                    "tooltip": {"enabled": True},
                },
            },
        }

        return json.dumps(config)

    def timeline_chart(self, evidence: Dict) -> str:
        """Generate timeline chart showing findings discovered over time."""
        from datetime import datetime

        # Group evidence by date
        timeline_data = {}

        for phase, items in evidence.items():
            if isinstance(items, list):
                for item in items:
                    timestamp = item.get("timestamp", "")
                    if timestamp:
                        # Extract date (YYYY-MM-DD)
                        date = timestamp[:10] if len(timestamp) >= 10 else timestamp
                        if date not in timeline_data:
                            timeline_data[date] = 0
                        timeline_data[date] += 1

        if not timeline_data:
            return ""

        # Sort by date
        sorted_dates = sorted(timeline_data.keys())
        counts = [timeline_data[date] for date in sorted_dates]

        config = {
            "type": "line",
            "data": {
                "labels": sorted_dates,
                "datasets": [
                    {
                        "label": "Evidence Items Collected",
                        "data": counts,
                        "borderColor": self.colors["info"],
                        "backgroundColor": "rgba(23, 162, 184, 0.1)",
                        "fill": True,
                        "tension": 0.3,
                        "pointRadius": 5,
                        "pointHoverRadius": 7,
                    }
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": True,
                "plugins": {
                    "legend": {"display": True, "position": "top"},
                    "title": {
                        "display": True,
                        "text": "Evidence Collection Timeline",
                        "font": {"size": 16, "weight": "bold"},
                    },
                },
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "title": {"display": True, "text": "Items Collected"},
                    },
                    "x": {"title": {"display": True, "text": "Date"}},
                },
            },
        }

        return json.dumps(config)

    def evidence_by_phase_chart(self, evidence_counts: Dict) -> str:
        """Generate stacked bar chart for evidence by phase."""
        if not evidence_counts:
            return ""

        phases = ["Reconnaissance", "Enumeration", "Exploitation", "Post-Exploitation"]
        counts = [
            evidence_counts.get("reconnaissance", 0),
            evidence_counts.get("enumeration", 0),
            evidence_counts.get("exploitation", 0),
            evidence_counts.get("post_exploitation", 0),
        ]

        if sum(counts) == 0:
            return ""

        config = {
            "type": "bar",
            "data": {
                "labels": phases,
                "datasets": [
                    {
                        "label": "Evidence Count",
                        "data": counts,
                        "backgroundColor": [
                            self.colors["info"],
                            self.colors["low"],
                            self.colors["medium"],
                            self.colors["high"],
                        ],
                        "borderWidth": 1,
                    }
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": True,
                "plugins": {
                    "legend": {"display": False},
                    "title": {
                        "display": True,
                        "text": "Evidence by Testing Phase",
                        "font": {"size": 16, "weight": "bold"},
                    },
                },
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "title": {"display": True, "text": "Evidence Items"},
                    }
                },
            },
        }

        return json.dumps(config)

    def service_exposure_chart(self, attack_surface: Dict) -> str:
        """Generate chart showing service exposure distribution."""
        hosts = attack_surface.get("hosts", [])

        if not hosts:
            return ""

        # Count services across all hosts
        service_counts = {}
        for host in hosts:
            services_data = host.get("services", [])
            if isinstance(services_data, list):
                for service in services_data:
                    service_name = service.get("service", "unknown")
                    service_counts[service_name] = (
                        service_counts.get(service_name, 0) + 1
                    )

        if not service_counts:
            return ""

        # Take top 10 services
        sorted_services = sorted(
            service_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]
        labels = [s[0] for s in sorted_services]
        counts = [s[1] for s in sorted_services]

        config = {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Occurrences",
                        "data": counts,
                        "backgroundColor": self.colors["info"],
                        "borderWidth": 1,
                    }
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": True,
                "indexAxis": "y",
                "plugins": {
                    "legend": {"display": False},
                    "title": {
                        "display": True,
                        "text": "Top 10 Exposed Services",
                        "font": {"size": 16, "weight": "bold"},
                    },
                },
                "scales": {
                    "x": {
                        "beginAtZero": True,
                        "title": {"display": True, "text": "Number of Instances"},
                    }
                },
            },
        }

        return json.dumps(config)

    def credentials_by_service_chart(self, credentials: List[Dict]) -> str:
        """Generate chart showing credentials found by service type."""
        if not credentials:
            return ""

        service_counts = {}
        for cred in credentials:
            service = cred.get("service", "unknown")
            service_counts[service] = service_counts.get(service, 0) + 1

        if not service_counts:
            return ""

        labels = list(service_counts.keys())
        counts = list(service_counts.values())

        config = {
            "type": "pie",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "data": counts,
                        "backgroundColor": [
                            self.colors["critical"],
                            self.colors["high"],
                            self.colors["medium"],
                            self.colors["low"],
                            self.colors["info"],
                            "#6c757d",
                            "#17a2b8",
                            "#28a745",
                        ],
                        "borderWidth": 2,
                        "borderColor": "#fff",
                    }
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": True,
                "plugins": {
                    "legend": {"position": "right"},
                    "title": {
                        "display": True,
                        "text": "Credentials by Service",
                        "font": {"size": 16, "weight": "bold"},
                    },
                },
            },
        }

        return json.dumps(config)

    def generate_all_charts(self, data: Dict) -> Dict:
        """Generate all chart configurations."""
        charts = {}

        # Phase 1 charts
        severity_chart = self.severity_distribution_chart(data["findings_by_severity"])
        if severity_chart:
            charts["severity_distribution"] = severity_chart

        host_chart = self.host_impact_chart(data["attack_surface"])
        if host_chart:
            charts["host_impact"] = host_chart

        exploitation_chart = self.exploitation_progress_chart(data["attack_surface"])
        if exploitation_chart:
            charts["exploitation_progress"] = exploitation_chart

        # Phase 2 charts
        timeline = self.timeline_chart(data.get("evidence", {}))
        if timeline:
            charts["timeline"] = timeline

        evidence_phase = self.evidence_by_phase_chart(data.get("evidence_counts", {}))
        if evidence_phase:
            charts["evidence_by_phase"] = evidence_phase

        service_exposure = self.service_exposure_chart(data["attack_surface"])
        if service_exposure:
            charts["service_exposure"] = service_exposure

        credentials_chart = self.credentials_by_service_chart(
            data.get("credentials", [])
        )
        if credentials_chart:
            charts["credentials_by_service"] = credentials_chart

        return charts

    # =========================================================================
    # Detection Coverage Charts
    # =========================================================================

    def detection_coverage_pie_chart(self, summary) -> str:
        """
        Generate pie chart showing detection coverage breakdown.

        Args:
            summary: EngagementDetectionSummary or dict with detection stats

        Returns:
            Chart.js JSON config string
        """
        # Handle both object and dict
        if hasattr(summary, "detected"):
            detected = summary.detected
            not_detected = summary.not_detected
            partial = getattr(summary, "partial", 0)
            offline = getattr(summary, "offline", 0)
        else:
            detected = summary.get("detected", 0)
            not_detected = summary.get("not_detected", 0)
            partial = summary.get("partial", 0)
            offline = summary.get("offline", 0)

        data = {
            "Detected": detected,
            "Not Detected": not_detected,
            "Partial": partial,
            "Offline": offline,
        }

        # Filter out zero values
        filtered_data = {k: v for k, v in data.items() if v > 0}

        if not filtered_data:
            return ""

        labels = list(filtered_data.keys())
        values = list(filtered_data.values())

        # Detection-specific colors
        color_map = {
            "Detected": "#28a745",  # Green
            "Not Detected": "#dc3545",  # Red
            "Partial": "#ffc107",  # Yellow
            "Offline": "#6c757d",  # Gray
        }
        colors = [color_map.get(k, "#17a2b8") for k in labels]

        config = {
            "type": "doughnut",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "data": values,
                        "backgroundColor": colors,
                        "borderWidth": 2,
                        "borderColor": "#fff",
                    }
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": True,
                "plugins": {
                    "legend": {"position": "right", "labels": {"font": {"size": 14}}},
                    "title": {
                        "display": True,
                        "text": "Detection Coverage",
                        "font": {"size": 16, "weight": "bold"},
                    },
                },
            },
        }

        return json.dumps(config)

    def detection_by_tactic_chart(self, tactic_summary) -> str:
        """
        Generate horizontal bar chart showing detection rates by MITRE tactic.

        Args:
            tactic_summary: Dict mapping tactic_id -> TacticResult

        Returns:
            Chart.js JSON config string
        """
        if not tactic_summary:
            return ""

        # Filter tactics that have been tested
        tested_tactics = [
            (tid, tactic)
            for tid, tactic in tactic_summary.items()
            if hasattr(tactic, "techniques_tested") and tactic.techniques_tested > 0
        ]

        if not tested_tactics:
            return ""

        # Sort by tactic order if available
        labels = []
        detected_data = []
        not_detected_data = []

        for tid, tactic in tested_tactics:
            labels.append(tactic.tactic_name if hasattr(tactic, "tactic_name") else tid)
            detected_data.append(
                tactic.techniques_detected
                if hasattr(tactic, "techniques_detected")
                else 0
            )
            not_detected_data.append(
                tactic.techniques_not_detected
                if hasattr(tactic, "techniques_not_detected")
                else 0
            )

        config = {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Detected",
                        "data": detected_data,
                        "backgroundColor": "#28a745",
                        "stack": "stack0",
                    },
                    {
                        "label": "Not Detected",
                        "data": not_detected_data,
                        "backgroundColor": "#dc3545",
                        "stack": "stack0",
                    },
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": True,
                "indexAxis": "y",
                "plugins": {
                    "legend": {"display": True, "position": "top"},
                    "title": {
                        "display": True,
                        "text": "Detection Coverage by MITRE ATT&CK Tactic",
                        "font": {"size": 16, "weight": "bold"},
                    },
                },
                "scales": {
                    "x": {
                        "stacked": True,
                        "title": {"display": True, "text": "Techniques"},
                    },
                    "y": {"stacked": True},
                },
            },
        }

        return json.dumps(config)

    def detection_by_category_chart(self, detection_results) -> str:
        """
        Generate bar chart showing detection rates by attack category.

        Args:
            detection_results: List of DetectionResult objects

        Returns:
            Chart.js JSON config string
        """
        from souleyez.detection.attack_signatures import get_signature

        if not detection_results:
            return ""

        # Group by category
        categories = {}
        for result in detection_results:
            # Get attack type
            attack_type = getattr(result, "attack_type", None)
            if not attack_type and isinstance(result, dict):
                attack_type = result.get("attack_type")
            if not attack_type:
                continue

            # Get status
            status = getattr(result, "status", None)
            if not status and isinstance(result, dict):
                status = result.get("status")

            # Get category from signature
            sig = get_signature(attack_type)
            category = sig.get("category", "unknown")

            if category not in categories:
                categories[category] = {"detected": 0, "not_detected": 0}

            if status == "detected":
                categories[category]["detected"] += 1
            elif status == "not_detected":
                categories[category]["not_detected"] += 1

        if not categories:
            return ""

        # Sort and build chart data
        labels = list(categories.keys())
        detected_data = [categories[c]["detected"] for c in labels]
        not_detected_data = [categories[c]["not_detected"] for c in labels]

        # Capitalize labels
        labels = [label.replace("_", " ").title() for label in labels]

        config = {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Detected",
                        "data": detected_data,
                        "backgroundColor": "#28a745",
                    },
                    {
                        "label": "Not Detected",
                        "data": not_detected_data,
                        "backgroundColor": "#dc3545",
                    },
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": True,
                "plugins": {
                    "legend": {"display": True, "position": "top"},
                    "title": {
                        "display": True,
                        "text": "Detection by Attack Category",
                        "font": {"size": 16, "weight": "bold"},
                    },
                },
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "title": {"display": True, "text": "Attack Count"},
                    }
                },
            },
        }

        return json.dumps(config)

    def generate_detection_charts(self, data) -> Dict:
        """
        Generate all detection coverage charts.

        Args:
            data: DetectionReportData object

        Returns:
            Dict of chart_name -> chart_config_json
        """
        charts = {}

        # Coverage pie chart
        if hasattr(data, "summary"):
            coverage_chart = self.detection_coverage_pie_chart(data.summary)
            if coverage_chart:
                charts["detection_coverage"] = coverage_chart

        # Tactic bar chart
        if hasattr(data, "tactic_summary"):
            tactic_chart = self.detection_by_tactic_chart(data.tactic_summary)
            if tactic_chart:
                charts["detection_by_tactic"] = tactic_chart

        # Category chart
        if hasattr(data, "detection_results"):
            category_chart = self.detection_by_category_chart(data.detection_results)
            if category_chart:
                charts["detection_by_category"] = category_chart

        return charts
