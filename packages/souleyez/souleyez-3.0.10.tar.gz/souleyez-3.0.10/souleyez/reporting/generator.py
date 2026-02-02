#!/usr/bin/env python3
"""
Professional penetration test report generator.
Creates comprehensive, client-ready reports in multiple formats.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates professional pentest reports from engagement data."""

    def __init__(self):
        from souleyez.intelligence.surface_analyzer import AttackSurfaceAnalyzer
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.engagements import EngagementManager
        from souleyez.storage.evidence import EvidenceManager
        from souleyez.storage.findings import FindingsManager

        self.em = EngagementManager()
        self.evm = EvidenceManager()
        self.analyzer = AttackSurfaceAnalyzer()
        self.findings_mgr = FindingsManager()
        self.creds_mgr = CredentialsManager()
        self._ai_service = None  # Lazy load

    @property
    def ai_service(self):
        """Lazy load AI report service."""
        if self._ai_service is None:
            from souleyez.ai.report_service import AIReportService

            self._ai_service = AIReportService()
        return self._ai_service

    def generate_report(
        self,
        engagement_id: int,
        format: str = "markdown",
        output_path: Optional[str] = None,
        report_type: str = "technical",
        ai_enhanced: bool = False,
        compare_to: Optional[int] = None,
    ) -> str:
        """
        Generate comprehensive pentest report.

        Args:
            engagement_id: Engagement to report on
            format: 'markdown', 'html', or 'pdf'
            output_path: Custom output path (optional)
            report_type: 'executive', 'technical', or 'summary'
            ai_enhanced: Enable AI-powered content generation (PRO tier)
            compare_to: Previous engagement ID to compare against (optional)

        Returns:
            Path to generated report file
        """
        # Check PRO tier if AI requested
        if ai_enhanced:
            self._check_ai_permission()

        # Validate report type
        valid_types = ["executive", "technical", "summary", "detection"]
        if report_type not in valid_types:
            raise ValueError(
                f"Invalid report_type '{report_type}'. Must be one of: {', '.join(valid_types)}"
            )

        # Detection reports use a different generation path
        if report_type == "detection":
            return self._generate_detection_report(engagement_id, format, output_path)

        # Gather all data
        data = self._gather_report_data(engagement_id)
        data["report_type"] = report_type
        data["ai_enhanced"] = ai_enhanced

        # Gather comparison data if requested
        if compare_to:
            data["comparison"] = self._gather_comparison_data(compare_to)
        else:
            data["comparison"] = None

        # Generate AI content if enabled
        if ai_enhanced:
            if self.ai_service.is_available():
                logger.info("AI enhancement enabled - generating AI content")
                data["ai_content"] = self._generate_ai_content(engagement_id, data)
            else:
                logger.warning(
                    "AI enhancement requested but provider not available - falling back to standard report"
                )
                data["ai_content"] = None
        else:
            data["ai_content"] = None

        # Generate report based on format
        if format == "markdown":
            report_content = self._generate_markdown(data)
            ext = ".md"
        elif format == "html":
            report_content = self._generate_html(data)
            ext = ".html"
        elif format == "pdf":
            # Generate HTML first, then convert to PDF
            html_content = self._generate_html(data)
            return self._convert_to_pdf(html_content, data, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Write report to file
        if not output_path:
            output_path = self._default_output_path(data["engagement"]["name"], ext)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        return output_path

    def _gather_report_data(self, engagement_id: int) -> Dict:
        """Gather all data needed for report."""
        engagement = self.em.get_by_id(engagement_id)
        evidence = self.evm.get_all_evidence(engagement_id)
        attack_surface = self.analyzer.analyze_engagement(engagement_id)
        findings = self.findings_mgr.list_findings(engagement_id)
        credentials = self.creds_mgr.list_credentials(engagement_id)

        # Organize findings by severity
        findings_by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": [],
        }
        for finding in findings:
            severity = finding.get("severity", "info")
            findings_by_severity[severity].append(finding)

        # Evidence counts
        evidence_counts = {
            "reconnaissance": len(evidence.get("reconnaissance", [])),
            "enumeration": len(evidence.get("enumeration", [])),
            "exploitation": len(evidence.get("exploitation", [])),
            "post_exploitation": len(evidence.get("post_exploitation", [])),
        }

        # Collect unique tools used from findings and evidence
        tools_used = set()

        # Tools from findings
        for finding in findings:
            tool = finding.get("tool")
            if tool and tool.strip() and tool.lower() not in ["unknown", "none", "n/a"]:
                tools_used.add(tool)

        # Tools from evidence (all phases)
        for phase_evidence in evidence.values():
            if isinstance(phase_evidence, list):
                for item in phase_evidence:
                    if isinstance(item, dict):
                        tool = item.get("tool")
                        if (
                            tool
                            and tool.strip()
                            and tool.lower() not in ["unknown", "none", "n/a"]
                        ):
                            tools_used.add(tool)

        # Tools from credentials
        for cred in credentials:
            source = cred.get("source")
            if (
                source
                and source.strip()
                and source.lower() not in ["unknown", "none", "n/a"]
            ):
                tools_used.add(source)

        return {
            "engagement": engagement,
            "attack_surface": attack_surface,
            "findings": findings,
            "findings_by_severity": findings_by_severity,
            "credentials": credentials,
            "evidence": evidence,
            "evidence_counts": evidence_counts,
            "tools_used": sorted(list(tools_used)),  # Sorted list of unique tools
            "generated_at": datetime.now(),
        }

    def _gather_comparison_data(self, previous_engagement_id: int) -> Optional[Dict]:
        """Gather data from a previous engagement for comparison.

        Args:
            previous_engagement_id: ID of the previous engagement to compare against

        Returns:
            Dict with previous engagement data and metrics, or None if not found
        """
        from souleyez.reporting.metrics import MetricsCalculator

        try:
            previous_engagement = self.em.get_by_id(previous_engagement_id)
            if not previous_engagement:
                logger.warning(
                    f"Previous engagement {previous_engagement_id} not found"
                )
                return None

            # Gather previous engagement data
            previous_data = self._gather_report_data(previous_engagement_id)

            # Calculate metrics for previous engagement
            metrics_calc = MetricsCalculator()
            previous_metrics = metrics_calc.get_dashboard_metrics(previous_data)

            return {
                "engagement": previous_engagement,
                "metrics": previous_metrics,
                "findings_by_severity": previous_data["findings_by_severity"],
                "data": previous_data,
            }
        except Exception as e:
            logger.warning(f"Failed to gather comparison data: {e}")
            return None

    def _generate_markdown(self, data: Dict) -> str:
        """Generate Markdown report."""
        from souleyez.reporting.formatters import MarkdownFormatter

        formatter = MarkdownFormatter()
        sections = []

        # Title page
        sections.append(formatter.title_page(data["engagement"], data["generated_at"]))

        # Table of contents
        sections.append(formatter.table_of_contents())

        # Get report type and AI content
        report_type = data.get("report_type", "technical")
        ai_content = data.get("ai_content")

        # Executive Summary (AI-enhanced if available)
        if ai_content and ai_content.get("executive_summary"):
            sections.append(
                formatter.ai_executive_summary(
                    ai_content["executive_summary"], ai_content.get("provider", "AI")
                )
            )
        else:
            sections.append(
                formatter.executive_summary(
                    data["engagement"],
                    data["findings_by_severity"],
                    data["attack_surface"]["overview"],
                    report_type,
                )
            )

        # Engagement Overview
        sections.append(
            formatter.engagement_overview(
                data["engagement"], data["tools_used"], report_type
            )
        )

        # Note: Attack Surface section removed - now covered by Intelligence Hub

        # Findings Summary
        sections.append(formatter.findings_summary(data["findings_by_severity"]))

        # Key Findings Summary (Top Critical/High) - for quick scanning
        sections.append(formatter.key_findings_summary(data["findings_by_severity"]))

        # Detailed Findings
        sections.append(
            formatter.detailed_findings(data["findings_by_severity"], report_type)
        )

        # Note: Evidence section removed - evidence is now displayed with each finding card

        # Recommendations (AI-enhanced if available)
        if ai_content and ai_content.get("remediation_plan"):
            sections.append(
                formatter.ai_remediation_plan(
                    ai_content["remediation_plan"], ai_content.get("provider", "AI")
                )
            )
        else:
            sections.append(
                formatter.recommendations(
                    data["findings_by_severity"],
                    data["attack_surface"]["recommendations"],
                )
            )

        # Appendix with Methodology (moved here for cleaner report flow)
        sections.append(
            formatter.appendix(
                data["attack_surface"]["hosts"],
                data["credentials"],
                include_methodology=True,
            )
        )

        # Footer
        sections.append(formatter.footer(data["generated_at"]))

        return "\n\n".join(sections)

    def _generate_html(self, data: Dict) -> str:
        """Generate HTML report with enhanced visualizations."""
        import markdown

        from souleyez.reporting.attack_chain import AttackChainAnalyzer
        from souleyez.reporting.charts import ChartGenerator
        from souleyez.reporting.compliance_mappings import ComplianceMappings
        from souleyez.reporting.formatters import HTMLFormatter, MarkdownFormatter
        from souleyez.reporting.metrics import MetricsCalculator

        formatter = HTMLFormatter()
        md_formatter = MarkdownFormatter()
        metrics_calc = MetricsCalculator()
        chart_gen = ChartGenerator()
        compliance_mapper = ComplianceMappings()
        chain_analyzer = AttackChainAnalyzer()

        # Get report type
        report_type = data.get("report_type", "technical")

        # Calculate metrics, charts, and compliance
        metrics = metrics_calc.get_dashboard_metrics(data)
        charts = chart_gen.generate_all_charts(data)

        # Get all findings as flat list for compliance mapping
        all_findings = []
        for severity_findings in data["findings_by_severity"].values():
            all_findings.extend(severity_findings)
        compliance_data = compliance_mapper.get_compliance_coverage(all_findings)

        # Build attack chain (legacy)
        attack_chain = chain_analyzer.build_attack_chain(
            data.get("evidence", {}), all_findings, data.get("credentials", [])
        )
        attack_summary = chain_analyzer.get_attack_summary(attack_chain)

        # Build host-centric attack chain (new visualization)
        host_centric_chain = chain_analyzer.build_host_centric_chain(
            data.get("evidence", {}),
            all_findings,
            data.get("credentials", []),
            data.get("attack_surface"),
        )

        sections = []
        ai_content = data.get("ai_content")

        # Title page (all types)
        sections.append(
            md_formatter.title_page(data["engagement"], data["generated_at"])
        )

        # Executive One-Pager (first page summary - all report types)
        sections.append(
            formatter.executive_one_pager(
                metrics, data["findings_by_severity"], data["engagement"]
            )
        )

        # Compare to Previous (if comparison data provided)
        comparison = data.get("comparison")
        if comparison:
            sections.append(
                formatter.compare_to_previous(
                    metrics,
                    comparison["metrics"],
                    data["engagement"],
                    comparison["engagement"],
                )
            )

        # Table of contents (technical only)
        if report_type in ["technical", "executive"]:
            sections.append(md_formatter.table_of_contents())

        # Executive Summary (AI-enhanced if available)
        if ai_content and ai_content.get("executive_summary"):
            sections.append(
                formatter.ai_executive_summary(
                    ai_content["executive_summary"], ai_content.get("provider", "AI")
                )
            )
        else:
            sections.append(
                md_formatter.executive_summary(
                    data["engagement"],
                    data["findings_by_severity"],
                    data["attack_surface"]["overview"],
                    report_type,
                )
            )

        # Intelligence Hub (all report types - near the top for visibility)
        sections.append(formatter.intelligence_hub_section(data["attack_surface"]))

        # Risk Quadrant (visual risk matrix - all report types)
        sections.append(formatter.risk_quadrant(data["findings_by_severity"]))

        # Remediation Timeline (visual timeline - all report types)
        sections.append(formatter.remediation_timeline(metrics))

        # Executive Dashboard (executive and summary)
        if report_type in ["executive", "summary"]:
            sections.append(formatter.executive_dashboard(metrics))

        # Charts Section
        if report_type == "executive":
            # Executive: Key charts only (severity, exploitation rate)
            exec_charts = {
                "severity_distribution": charts.get("severity_distribution"),
                "exploitation_progress": charts.get("exploitation_progress"),
            }
            sections.append(formatter.charts_section(exec_charts))
        elif report_type == "summary":
            # Summary: Basic chart only
            summary_charts = {
                "severity_distribution": charts.get("severity_distribution")
            }
            sections.append(formatter.charts_section(summary_charts))
        else:
            # Technical: All charts
            sections.append(formatter.charts_section(charts))

        # Engagement Overview (technical only)
        if report_type == "technical":
            sections.append(
                md_formatter.engagement_overview(
                    data["engagement"], data["tools_used"], report_type
                )
            )
            # Note: Attack Surface section removed - now covered by Intelligence Hub

        # Findings Summary (all types)
        sections.append(md_formatter.findings_summary(data["findings_by_severity"]))

        # Key Findings Summary (Top Critical/High) - for quick scanning
        sections.append(md_formatter.key_findings_summary(data["findings_by_severity"]))

        # Compliance Mapping (executive and technical)
        if report_type in ["executive", "technical"]:
            sections.append(
                formatter.compliance_section(all_findings, compliance_data, report_type)
            )

        # Detailed Findings
        if report_type == "executive":
            # Executive: Top 5 critical/high only
            top_findings = self._filter_top_findings(
                data["findings_by_severity"], limit=5
            )
            sections.append(formatter.detailed_findings_collapsible(top_findings))
        elif report_type == "summary":
            # Summary: Top 3 critical/high only
            top_findings = self._filter_top_findings(
                data["findings_by_severity"], limit=3
            )
            sections.append(formatter.detailed_findings_collapsible(top_findings))
        else:
            # Technical: All findings
            sections.append(
                formatter.detailed_findings_collapsible(data["findings_by_severity"])
            )

        # Attack Chain Visualization (technical only)
        if report_type == "technical":
            sections.append(
                md_formatter.attack_chain_section(
                    attack_chain, attack_summary, host_centric_chain
                )
            )

        # Note: Evidence section removed - evidence is now displayed with each finding card

        # Recommendations (AI-enhanced if available)
        if ai_content and ai_content.get("remediation_plan"):
            sections.append(
                formatter.ai_remediation_plan(
                    ai_content["remediation_plan"], ai_content.get("provider", "AI")
                )
            )
        elif report_type == "executive":
            # Executive: Business-focused recommendations
            sections.append(
                self._generate_executive_recommendations(
                    data["findings_by_severity"], metrics
                )
            )
        else:
            # Technical/Summary: Standard recommendations
            sections.append(
                md_formatter.recommendations(
                    data["findings_by_severity"],
                    data["attack_surface"]["recommendations"],
                )
            )

        # Appendix with Methodology (technical only)
        # Note: Methodology moved to appendix for cleaner report flow
        if report_type == "technical":
            sections.append(
                md_formatter.appendix(
                    data["attack_surface"]["hosts"],
                    data["credentials"],
                    include_methodology=True,
                )
            )

        # Footer (all types)
        sections.append(md_formatter.footer(data["generated_at"]))

        # Join all sections
        markdown_content = "\n\n".join(sections)

        # Convert markdown to HTML with extensions
        html_content = markdown.markdown(
            markdown_content, extensions=["tables", "nl2br", "sane_lists"]
        )

        # Wrap in HTML structure
        html_parts = [
            formatter.html_header(data["engagement"]["name"]),
            html_content,
            formatter.html_footer(),
        ]

        return "\n".join(html_parts)

    def _convert_to_pdf(
        self, html_content: str, data: Dict, output_path: Optional[str] = None
    ) -> str:
        """Convert HTML to PDF using WeasyPrint (primary) or wkhtmltopdf (fallback)."""
        if not output_path:
            output_path = self._default_output_path(data["engagement"]["name"], ".pdf")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Try WeasyPrint first (preferred - pure Python, better CSS support)
        try:
            from weasyprint import CSS, HTML
            from weasyprint.text.fonts import FontConfiguration

            font_config = FontConfiguration()

            # Additional CSS for PDF rendering
            pdf_css = CSS(
                string="""
                @page {
                    size: Letter;
                    margin: 20mm 15mm;
                }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                /* Ensure charts don't break across pages */
                .chart-container, .finding-card, details {
                    page-break-inside: avoid;
                }
            """,
                font_config=font_config,
            )

            html_doc = HTML(string=html_content)
            html_doc.write_pdf(
                output_path, stylesheets=[pdf_css], font_config=font_config
            )

            logger.info(f"PDF generated with WeasyPrint: {output_path}")
            return output_path

        except ImportError:
            logger.warning("WeasyPrint not available, trying wkhtmltopdf...")
        except Exception as e:
            # WeasyPrint failed - log and try fallback
            logger.error(f"WeasyPrint PDF generation failed: {e}")
            raise RuntimeError(f"PDF generation failed: {e}")

        # Fallback to wkhtmltopdf
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html_content)
            html_path = f.name

        try:
            import subprocess

            result = subprocess.run(
                [
                    "wkhtmltopdf",
                    "--enable-local-file-access",
                    "--page-size",
                    "Letter",
                    "--margin-top",
                    "20mm",
                    "--margin-bottom",
                    "20mm",
                    "--margin-left",
                    "15mm",
                    "--margin-right",
                    "15mm",
                    html_path,
                    output_path,
                ],
                check=True,
                capture_output=True,
            )

            return output_path

        except FileNotFoundError:
            raise RuntimeError(
                "PDF generation requires WeasyPrint or wkhtmltopdf.\n"
                "Install WeasyPrint: pip install weasyprint\n"
                "Or wkhtmltopdf: sudo apt install wkhtmltopdf"
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"PDF conversion failed: {e.stderr.decode()}")
        finally:
            try:
                os.remove(html_path)
            except:
                pass

    def _default_output_path(
        self, engagement_name: str, ext: str, suffix: str = ""
    ) -> str:
        """Generate default output path.

        Args:
            engagement_name: Name of the engagement
            ext: File extension (e.g., '.html', '.pdf')
            suffix: Optional suffix to add before '_report' (e.g., '_detection')

        Returns:
            Full path to output file
        """
        # Save to ./reports directory (relative to project root or CWD)
        # Try to use project root first, fallback to CWD
        project_root = os.getcwd()

        # Check if we're in souleyez directory structure
        if "souleyez" in project_root and os.path.exists(
            os.path.join(project_root, "setup.py")
        ):
            output_dir = os.path.join(project_root, "reports")
        else:
            # Fallback to ./reports in current directory
            output_dir = os.path.join(os.getcwd(), "reports")

        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = engagement_name.replace(" ", "_").replace("/", "_")
        filename = f"{safe_name}{suffix}_report_{timestamp}{ext}"

        return os.path.join(output_dir, filename)

    def _filter_top_findings(self, findings: Dict, limit: int = 5) -> Dict:
        """Filter to top N critical/high findings for executive/summary reports."""
        filtered = {"critical": [], "high": [], "medium": [], "low": [], "info": []}

        # Get critical and high findings
        critical = findings.get("critical", [])
        high = findings.get("high", [])

        # Combine and take top N
        top_findings = (critical + high)[:limit]

        # Split back into severity categories
        for finding in top_findings:
            severity = finding.get("severity", "info").lower()
            if severity in filtered:
                filtered[severity].append(finding)

        return filtered

    def _generate_executive_recommendations(self, findings: Dict, metrics: Dict) -> str:
        """Generate business-focused recommendations for executive report."""
        section = """## EXECUTIVE RECOMMENDATIONS

### Immediate Actions (24-48 Hours)

"""
        # Critical findings
        critical_count = len(findings.get("critical", []))
        if critical_count > 0:
            section += f"**{critical_count} Critical vulnerabilities require immediate remediation:**\n\n"
            for idx, finding in enumerate(findings["critical"][:3], 1):
                section += f"{idx}. {finding['title']}\n"
                section += f"   - **Business Impact:** High risk of data breach or system compromise\n"
                section += f"   - **Recommended Action:** Emergency patch or system isolation\n\n"
        else:
            section += "✓ No critical vulnerabilities identified.\n\n"

        section += """### Short-Term (1-2 Weeks)

**Remediation Timeline:**
"""
        timeline = metrics.get("remediation_timeline", {})
        section += f"- Estimated effort: {timeline.get('total_days', 0)} business days ({timeline.get('weeks', 0)} weeks)\n"
        section += f"- Critical issues: {timeline.get('critical', 0)} days\n"
        section += f"- High priority: {timeline.get('high', 0)} days\n\n"

        section += """### Compliance & Risk Posture

"""
        section += f"**Overall Risk Score:** {metrics.get('risk_score', 0)}/100 ({metrics.get('risk_level', 'UNKNOWN')})\n\n"

        if metrics.get("risk_score", 0) >= 75:
            section += "⚠️ **Action Required:** Critical risk level requires board notification and immediate action plan.\n\n"
        elif metrics.get("risk_score", 0) >= 50:
            section += "⚠️ **Action Required:** High risk level requires executive review and remediation plan.\n\n"
        else:
            section += (
                "✓ Risk level is manageable with standard remediation timeline.\n\n"
            )

        section += """### Budget Considerations

**Estimated Costs:**
- Internal remediation effort (based on timeline)
- Potential security tool investments (WAF, IDS/IPS)
- Third-party security services (if needed)
- Compliance audit requirements

**ROI of Remediation:**
- Reduced risk of data breach (avg cost: $4.45M)
- Improved compliance posture
- Enhanced customer trust
- Reduced insurance premiums

### Next Steps

1. Review this report with security and IT leadership
2. Prioritize critical findings for immediate action
3. Allocate resources and budget for remediation
4. Schedule follow-up assessment after remediation
5. Implement continuous monitoring
6. Update security policies and procedures

---"""

        return section

    def _check_ai_permission(self):
        """Verify user has PRO tier for AI features."""
        try:
            from souleyez.auth import get_current_user
            from souleyez.auth.permissions import Tier

            user = get_current_user()
            if user is None:
                # No user context (e.g., CLI mode) - allow if AI is available
                return

            if user.tier != Tier.PRO:
                raise PermissionError(
                    "AI-enhanced reports require a PRO license. "
                    "Upgrade at https://www.cybersoulsecurity.com/souleyez"
                )
        except ImportError:
            # Auth module not available - allow
            pass

    def _generate_ai_content(self, engagement_id: int, data: Dict) -> Dict:
        """Generate all AI content for report."""

        ai_content = {
            "executive_summary": None,
            "remediation_plan": None,
            "risk_rating": None,
            "enhanced_findings": {},
            "provider": None,
            "errors": [],
        }

        try:
            ai_content["provider"] = self.ai_service.provider.provider_type.value
        except Exception:
            pass

        # Generate executive summary
        try:
            ai_content["executive_summary"] = (
                self.ai_service.generate_executive_summary(engagement_id)
            )
            if ai_content["executive_summary"]:
                logger.info("AI executive summary generated")
        except Exception as e:
            ai_content["errors"].append(f"Executive summary: {e}")
            logger.warning(f"AI executive summary failed: {e}")

        # Generate remediation plan
        try:
            ai_content["remediation_plan"] = self.ai_service.generate_remediation_plan(
                engagement_id
            )
            if ai_content["remediation_plan"]:
                logger.info("AI remediation plan generated")
        except Exception as e:
            ai_content["errors"].append(f"Remediation plan: {e}")
            logger.warning(f"AI remediation plan failed: {e}")

        # Generate risk rating
        try:
            ai_content["risk_rating"] = self.ai_service.generate_risk_rating(
                engagement_id
            )
        except Exception as e:
            ai_content["errors"].append(f"Risk rating: {e}")

        # Enhance top critical/high findings (limit to 10 for cost control)
        try:
            priority_findings = (
                data["findings_by_severity"].get("critical", [])[:5]
                + data["findings_by_severity"].get("high", [])[:5]
            )
            for finding in priority_findings:
                try:
                    enhanced = self.ai_service.enhance_finding(finding)
                    if enhanced:
                        ai_content["enhanced_findings"][finding["id"]] = enhanced
                except Exception as e:
                    logger.warning(
                        f"Failed to enhance finding {finding.get('id')}: {e}"
                    )
        except Exception as e:
            ai_content["errors"].append(f"Finding enhancement: {e}")

        return ai_content

    # =========================================================================
    # Detection Coverage Report Generation
    # =========================================================================

    def _generate_detection_report(
        self, engagement_id: int, format: str, output_path: Optional[str] = None
    ) -> str:
        """
        Generate detection coverage report.

        This is a standalone report type focused on SIEM detection validation.

        Args:
            engagement_id: Engagement to report on
            format: 'html' or 'pdf' (markdown also supported)
            output_path: Custom output path (optional)

        Returns:
            Path to generated report file
        """
        import markdown

        from souleyez.integrations.wazuh.config import WazuhConfig
        from souleyez.reporting.charts import ChartGenerator
        from souleyez.reporting.detection_report import DetectionReportGatherer
        from souleyez.reporting.formatters import HTMLFormatter, MarkdownFormatter

        # Check if Wazuh is configured
        config = WazuhConfig.get_config(engagement_id)
        if not config or not config.get("enabled"):
            raise ValueError(
                "Detection reports require Wazuh integration. "
                "Configure with 'souleyez wazuh config' first."
            )

        # Gather detection data
        gatherer = DetectionReportGatherer(engagement_id)
        data = gatherer.gather_data()

        # Generate charts
        chart_gen = ChartGenerator()
        charts = chart_gen.generate_detection_charts(data)

        # Generate report based on format
        if format == "html":
            report_content = self._generate_detection_html(data, charts)
            ext = ".html"
        elif format == "pdf":
            html_content = self._generate_detection_html(data, charts)
            return self._convert_detection_to_pdf(html_content, data, output_path)
        elif format == "markdown":
            report_content = self._generate_detection_markdown(data)
            ext = ".md"
        else:
            raise ValueError(f"Unsupported format for detection report: {format}")

        # Write report to file
        if not output_path:
            output_path = self._default_output_path(
                data.engagement.get("name", "detection"), ext, suffix="_detection"
            )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info(f"Detection report generated: {output_path}")
        return output_path

    def _generate_detection_markdown(self, data) -> str:
        """Generate detection report in Markdown format."""
        from souleyez.reporting.formatters import MarkdownFormatter

        formatter = MarkdownFormatter()
        sections = []

        # Title page
        sections.append(
            formatter.detection_title_page(data.engagement, data.generated_at)
        )

        # Executive summary
        sections.append(formatter.detection_executive_summary(data))

        # Coverage overview
        sections.append(formatter.detection_coverage_overview(data))

        # MITRE heatmap
        sections.append(formatter.mitre_heatmap_section(data))

        # Severity breakdown
        sections.append(formatter.severity_breakdown_section(data))

        # Top triggered rules
        sections.append(formatter.top_rules_section(data))

        # Detected attacks table
        sections.append(formatter.detected_attacks_table(data))

        # Sample alerts with content
        sections.append(formatter.sample_alerts_section(data))

        # Detection gaps
        sections.append(formatter.detection_gaps_section(data))

        # Vulnerability context (Wazuh)
        sections.append(formatter.vulnerability_section(data))

        # Rule recommendations
        sections.append(formatter.rule_recommendations_section(data))

        # Per-host analysis
        sections.append(formatter.per_host_detection_section(data))

        # Footer
        sections.append(f"""
---

*Detection Coverage Report generated by SoulEyez*
*{data.generated_at.strftime('%B %d, %Y at %H:%M:%S')}*
""")

        return "\n\n".join(sections)

    def _generate_detection_html(self, data, charts: Dict) -> str:
        """Generate detection report in HTML format with heatmap."""
        import markdown

        from souleyez.reporting.formatters import HTMLFormatter

        # Helper to convert markdown with table support
        def md_to_html(md_text: str) -> str:
            return markdown.markdown(md_text, extensions=["tables", "fenced_code"])

        formatter = HTMLFormatter()
        sections = []

        # HTML header with detection-specific styles
        sections.append(
            formatter.detection_report_header(
                f"Detection Coverage - {data.engagement.get('name', 'Report')}"
            )
        )
        sections.append('<div class="container">')

        # Title
        title_md = f"""# DETECTION COVERAGE REPORT
## {data.engagement.get('name', 'Unknown Engagement')}

**Generated:** {data.generated_at.strftime('%B %d, %Y at %H:%M:%S')}
**SIEM Type:** {data.siem_type.upper()}
"""
        sections.append(md_to_html(title_md))

        # Stats cards
        summary = data.summary
        sections.append(f"""
<div class="detection-stat-grid">
    <div class="detection-stat-card coverage">
        <div class="detection-stat-value">{summary.coverage_percent}%</div>
        <div class="detection-stat-label">Coverage Rate</div>
    </div>
    <div class="detection-stat-card">
        <div class="detection-stat-value">{summary.total_attacks}</div>
        <div class="detection-stat-label">Total Attacks</div>
    </div>
    <div class="detection-stat-card detected">
        <div class="detection-stat-value">{summary.detected}</div>
        <div class="detection-stat-label">Detected</div>
    </div>
    <div class="detection-stat-card not-detected">
        <div class="detection-stat-value">{summary.not_detected}</div>
        <div class="detection-stat-label">Not Detected</div>
    </div>
</div>
""")

        # Coverage overview
        overview_md = formatter.detection_coverage_overview(data)
        sections.append(md_to_html(overview_md))

        # Charts
        if charts.get("detection_coverage"):
            sections.append(f"""
<div class="chart-container" style="max-width: 400px; margin: 20px auto;">
    <canvas id="detectionCoverageChart"></canvas>
</div>
<script>
new Chart(document.getElementById('detectionCoverageChart'), {charts['detection_coverage']});
</script>
""")

        if charts.get("detection_by_tactic"):
            sections.append(f"""
<div class="chart-container" style="max-width: 800px; margin: 20px auto;">
    <canvas id="detectionTacticChart"></canvas>
</div>
<script>
new Chart(document.getElementById('detectionTacticChart'), {charts['detection_by_tactic']});
</script>
""")

        # MITRE ATT&CK Heatmap (HTML version)
        sections.append(formatter.mitre_heatmap_html(data))

        # Severity breakdown
        severity_md = formatter.severity_breakdown_section(data)
        sections.append(md_to_html(severity_md))

        # Top triggered rules
        top_rules_md = formatter.top_rules_section(data)
        sections.append(md_to_html(top_rules_md))

        # Detected attacks table
        detected_md = formatter.detected_attacks_table(data)
        sections.append(md_to_html(detected_md))

        # Sample alerts with content
        samples_md = formatter.sample_alerts_section(data)
        sections.append(md_to_html(samples_md))

        # Detection gaps (with warning styling)
        if data.gaps:
            sections.append("""
<div class="gap-warning">
    <h4>Detection Gaps Identified</h4>
    <p>The following attacks were NOT detected by the SIEM. These represent potential blindspots that should be addressed.</p>
</div>
""")
        gaps_md = formatter.detection_gaps_section(data)
        sections.append(md_to_html(gaps_md))

        # Vulnerability context (Wazuh)
        vuln_md = formatter.vulnerability_section(data)
        sections.append(md_to_html(vuln_md))

        # Rule recommendations
        recs_md = formatter.rule_recommendations_section(data)
        sections.append(md_to_html(recs_md))

        # Per-host analysis
        host_md = formatter.per_host_detection_section(data)
        sections.append(md_to_html(host_md))

        # Footer
        sections.append(f"""
<hr>
<p style="text-align: center; color: #6c757d;">
    <em>Detection Coverage Report generated by SoulEyez</em><br>
    {data.generated_at.strftime('%B %d, %Y at %H:%M:%S')}
</p>
""")

        # HTML footer with Chart.js
        sections.append("""
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
""")
        sections.append(formatter.html_footer())

        return "\n".join(sections)

    def _convert_detection_to_pdf(
        self, html_content: str, data, output_path: Optional[str] = None
    ) -> str:
        """Convert detection HTML report to PDF."""
        if not output_path:
            output_path = self._default_output_path(
                data.engagement.get("name", "detection"), ".pdf", suffix="_detection"
            )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Try WeasyPrint first (better CSS support)
        try:
            from weasyprint import CSS, HTML

            # Inline all external resources for PDF
            html_content = html_content.replace(
                "https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js", ""
            )

            html = HTML(string=html_content)
            css = CSS(string="""
                @page {
                    size: letter;
                    margin: 20mm 15mm;
                }
                body {
                    background: white !important;
                }
                .container {
                    box-shadow: none !important;
                }
                .chart-container {
                    page-break-inside: avoid;
                }
                .mitre-heatmap {
                    page-break-inside: avoid;
                }
            """)
            html.write_pdf(output_path, stylesheets=[css])
            logger.info(f"PDF generated with WeasyPrint: {output_path}")
            return output_path

        except ImportError:
            logger.warning("WeasyPrint not available, trying wkhtmltopdf")

        # Fallback to wkhtmltopdf
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as tmp:
            tmp.write(html_content)
            tmp_path = tmp.name

        try:
            subprocess.run(
                ["wkhtmltopdf", "--quiet", tmp_path, output_path], check=True
            )
            logger.info(f"PDF generated with wkhtmltopdf: {output_path}")
            return output_path
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"PDF conversion failed: {e}")
            raise ValueError(
                "PDF generation requires WeasyPrint or wkhtmltopdf. "
                "Install with: pip install weasyprint"
            )
        finally:
            os.unlink(tmp_path)
