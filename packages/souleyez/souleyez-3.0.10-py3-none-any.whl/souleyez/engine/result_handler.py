#!/usr/bin/env python3
"""
souleyez.engine.result_handler - Auto-parse job results
"""

import logging
import os
from typing import Any, Dict, Optional

from .job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS, STATUS_WARNING

logger = logging.getLogger(__name__)


# Common error patterns that indicate tool failure (not "no results")
TOOL_ERROR_PATTERNS = {
    "common": [
        "connection refused",
        "connection timed out",
        "no route to host",
        "network is unreachable",
        "name or service not known",
        "temporary failure in name resolution",
        "host is down",
        "connection reset by peer",
        "failed to run command",  # stdbuf wrapper error when tool not found
        "no such file or directory",  # command not found
    ],
    "nmap": [
        "host seems down",
        "note: host seems down",
        "failed to resolve",
    ],
    "gobuster": [
        "timeout occurred during the request",
        "error on running gobuster",
        "unable to connect",
        "context deadline exceeded",
    ],
    "hydra": [
        "can not connect",
        "could not connect",
        "error connecting",
        "target does not support",
    ],
    "nikto": [
        "error connecting to host",
        "unable to connect",
        "no web server found",
    ],
    "nuclei": [
        "could not connect",
        "context deadline exceeded",
        # Note: "no address found" removed - nuclei reports this as [INF] when
        # templates try alternate ports, not a real error. Exit code 0 = success.
    ],
    "ffuf": [
        "error making request",
        "context deadline exceeded",
    ],
    "katana": [
        "no such file or directory",
        "failed to run command",
        "chromium not found",
        "headless browser error",
        "context deadline exceeded",
        "connection refused",
    ],
    "sqlmap": [
        # Note: 'target url content is not stable' is a WARNING, not an error
        # sqlmap handles it and continues scanning - don't mark as error
        # Note: 'unable to connect' can be temporary - sqlmap retries
        # Note: '[ERROR] all tested parameters do not appear to be injectable' is NOT an error
        # - it means the scan completed but found no SQLi vulnerabilities (= no_results)
        # Only mark as error for actual failures like persistent connection issues
        "[critical] connection timed out to the target url",
    ],
    "enum4linux": [
        "could not initialise",
        "nt_status_connection_refused",
        "nt_status_host_unreachable",
        "nt_status_io_timeout",
    ],
    "smbmap": [
        "could not connect",
        "connection error",
        "nt_status_connection_refused",
    ],
}


def detect_tool_error(log_content: str, tool: str) -> Optional[str]:
    """
    Check log content for tool errors that indicate failure (not just "no results").

    Args:
        log_content: The log file content
        tool: Tool name (lowercase)

    Returns:
        Error pattern found, or None if no error detected
    """
    log_lower = log_content.lower()

    # Check common patterns
    for pattern in TOOL_ERROR_PATTERNS["common"]:
        if pattern in log_lower:
            return pattern

    # Check tool-specific patterns
    tool_patterns = TOOL_ERROR_PATTERNS.get(tool, [])
    for pattern in tool_patterns:
        if pattern in log_lower:
            return pattern

    return None


def handle_job_result(job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process completed job and parse results into database.

    Args:
        job: Job dict from background system

    Returns:
        Parse results or None if not applicable

    Note:
        Auto-chaining is handled separately in background.py
        to avoid duplicate job creation.
    """
    tool = job.get("tool", "").lower()
    log_path = job.get("log")

    # Always try to parse if log file exists
    # Status checks were causing race conditions where jobs showed "done"
    # but get_job() returned stale status, causing parse to be skipped
    # The caller (background.py) only calls us for completed jobs anyway
    if not log_path or not os.path.exists(log_path):
        logger.error(
            f"Job {job.get('id')} parse failed: log file missing or does not exist (path={log_path})"
        )
        return None

    # Get engagement ID from job or fall back to current engagement
    engagement_id = job.get("engagement_id")

    if not engagement_id:
        try:
            from souleyez.storage.engagements import EngagementManager

            em = EngagementManager()
            engagement = em.get_current()

            if not engagement:
                logger.error(
                    f"Job {job.get('id')} parse failed: no engagement_id and no current engagement"
                )
                return None

            engagement_id = engagement["id"]
        except Exception as e:
            logger.error(
                f"Job {job.get('id')} parse failed: engagement lookup error: {e}"
            )
            return None

    # Try new handler system first (with fallback to legacy)
    parse_result = None

    try:
        from souleyez.handlers.registry import get_handler
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        handler = get_handler(tool)
        if handler:
            try:
                # Pass managers so handlers can store credentials/findings
                host_manager = HostManager()
                findings_manager = FindingsManager()
                credentials_manager = CredentialsManager()

                parse_result = handler.parse_job(
                    engagement_id,
                    log_path,
                    job,
                    host_manager=host_manager,
                    findings_manager=findings_manager,
                    credentials_manager=credentials_manager,
                )
                logger.debug(
                    f"Job {job.get('id')} parsed by handler: {handler.tool_name}"
                )
                # Handler succeeded - skip legacy code and return
                return parse_result
            except Exception as e:
                logger.error(f"Handler parse failed for {tool}: {e}")
                # Fall through to legacy code
    except ImportError:
        # Handler system not available, fall through to legacy
        pass

    # Legacy parser fallback
    if tool == "nmap" or tool == "ard":
        # ARD plugin uses nmap under the hood
        parse_result = parse_nmap_job(engagement_id, log_path, job)
    elif tool == "nuclei":
        parse_result = parse_nuclei_job(engagement_id, log_path, job)
    elif tool == "theharvester":
        parse_result = parse_theharvester_job(engagement_id, log_path, job)
    elif tool == "gobuster":
        parse_result = parse_gobuster_job(engagement_id, log_path, job)
    elif tool == "crackmapexec":
        parse_result = parse_crackmapexec_job(engagement_id, log_path, job)
    elif tool == "enum4linux":
        parse_result = parse_enum4linux_job(engagement_id, log_path, job)
    elif tool == "msf_auxiliary":
        parse_result = parse_msf_auxiliary_job(engagement_id, log_path, job)
    elif tool == "msf_exploit":
        parse_result = parse_msf_exploit_job(engagement_id, log_path, job)
    elif tool == "sqlmap":
        parse_result = parse_sqlmap_job(engagement_id, log_path, job)
    elif tool == "smbmap":
        parse_result = parse_smbmap_job(engagement_id, log_path, job)
    elif tool == "whois":
        parse_result = parse_whois_job(engagement_id, log_path, job)
    elif tool == "dnsrecon":
        parse_result = parse_dnsrecon_job(engagement_id, log_path, job)

    elif tool == "wpscan":
        parse_result = parse_wpscan_job(engagement_id, log_path, job)
    elif tool == "hydra":
        parse_result = parse_hydra_job(engagement_id, log_path, job)
    elif tool == "ffuf":
        parse_result = parse_ffuf_job(engagement_id, log_path, job)
    elif tool == "searchsploit":
        parse_result = parse_searchsploit_job(engagement_id, log_path, job)
    elif tool in [
        "impacket-secretsdump",
        "impacket-getnpusers",
        "impacket-psexec",
        "impacket-smbclient",
    ]:
        parse_result = parse_impacket_job(engagement_id, log_path, job)
    elif tool == "responder":
        parse_result = parse_responder_job(engagement_id, log_path, job)
    elif tool == "bloodhound":
        parse_result = parse_bloodhound_job(engagement_id, log_path, job)
    elif tool == "nikto":
        parse_result = parse_nikto_job(engagement_id, log_path, job)
    elif tool == "dalfox":
        parse_result = parse_dalfox_job(engagement_id, log_path, job)
    elif tool == "http_fingerprint":
        parse_result = parse_http_fingerprint_job(engagement_id, log_path, job)
    elif tool == "hashcat":
        parse_result = parse_hashcat_job(engagement_id, log_path, job)
    elif tool == "john":
        parse_result = parse_john_job(engagement_id, log_path, job)
    else:
        # No parser for this tool - log it so we know
        logger.warning(
            f"Job {job.get('id')} has no parser for tool '{tool}' - results not extracted"
        )

    # NOTE: Auto-chaining is now handled in background.py after parsing completes
    # This avoids duplicate job creation and gives better control over timing

    return parse_result


def reparse_job(job_id: int) -> Dict[str, Any]:
    """
    Re-parse an existing job using updated parser logic.

    This is useful when parsers are updated and you want to
    re-extract data from existing job logs without re-running the job.

    Args:
        job_id: The job ID to re-parse

    Returns:
        Dict with 'success', 'message', and optionally 'parse_result'
    """
    from .background import _read_jobs, _write_jobs, get_job

    # Get the job
    job = get_job(job_id)
    if not job:
        return {"success": False, "message": f"Job {job_id} not found"}

    log_path = job.get("log")
    tool = job.get("tool", "").lower()

    # Allow hashcat to work without log file (can check potfile directly)
    if not log_path or not os.path.exists(log_path):
        if tool != "hashcat":
            return {"success": False, "message": f"Log file not found: {log_path}"}
    if not tool:
        return {"success": False, "message": "Job has no tool specified"}

    # Get engagement ID
    engagement_id = job.get("engagement_id")
    if not engagement_id:
        try:
            from souleyez.storage.engagements import EngagementManager

            em = EngagementManager()
            engagement = em.get_current()
            if engagement:
                engagement_id = engagement["id"]
        except Exception:
            pass

    if not engagement_id:
        return {"success": False, "message": "Could not determine engagement ID"}

    # Try new handler system first
    parse_result = None
    handler_succeeded = False

    try:
        from souleyez.handlers.registry import get_handler
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        handler = get_handler(tool)
        if handler:
            try:
                # Pass managers so handlers can store credentials/findings
                host_manager = HostManager()
                findings_manager = FindingsManager()
                credentials_manager = CredentialsManager()

                parse_result = handler.parse_job(
                    engagement_id,
                    log_path,
                    job,
                    host_manager=host_manager,
                    findings_manager=findings_manager,
                    credentials_manager=credentials_manager,
                )
                if parse_result and "error" not in parse_result:
                    handler_succeeded = True
                    logger.debug(
                        f"Job {job_id} reparsed by handler: {handler.tool_name}"
                    )
            except Exception as e:
                logger.error(f"Handler reparse failed for {tool}: {e}")
    except ImportError:
        pass

    # Legacy parser fallback (if handler didn't handle it)
    if not handler_succeeded:
        try:
            if tool == "nmap" or tool == "ard":
                # ARD plugin uses nmap under the hood
                parse_result = parse_nmap_job(engagement_id, log_path, job)
            elif tool == "nuclei":
                parse_result = parse_nuclei_job(engagement_id, log_path, job)
            elif tool == "theharvester":
                parse_result = parse_theharvester_job(engagement_id, log_path, job)
            elif tool == "gobuster":
                parse_result = parse_gobuster_job(engagement_id, log_path, job)
            elif tool == "crackmapexec":
                parse_result = parse_crackmapexec_job(engagement_id, log_path, job)
            elif tool == "enum4linux":
                parse_result = parse_enum4linux_job(engagement_id, log_path, job)
            elif tool == "msf_auxiliary":
                parse_result = parse_msf_auxiliary_job(engagement_id, log_path, job)
            elif tool == "msf_exploit":
                parse_result = parse_msf_exploit_job(engagement_id, log_path, job)
            elif tool == "sqlmap":
                parse_result = parse_sqlmap_job(engagement_id, log_path, job)
            elif tool == "smbmap":
                parse_result = parse_smbmap_job(engagement_id, log_path, job)
            elif tool == "whois":
                parse_result = parse_whois_job(engagement_id, log_path, job)
            elif tool == "dnsrecon":
                parse_result = parse_dnsrecon_job(engagement_id, log_path, job)
            elif tool == "wpscan":
                parse_result = parse_wpscan_job(engagement_id, log_path, job)
            elif tool == "hydra":
                parse_result = parse_hydra_job(engagement_id, log_path, job)
            elif tool == "ffuf":
                parse_result = parse_ffuf_job(engagement_id, log_path, job)
            elif tool == "searchsploit":
                parse_result = parse_searchsploit_job(engagement_id, log_path, job)
            elif tool in [
                "impacket-secretsdump",
                "impacket-getnpusers",
                "impacket-psexec",
                "impacket-smbclient",
            ]:
                parse_result = parse_impacket_job(engagement_id, log_path, job)
            elif tool == "responder":
                parse_result = parse_responder_job(engagement_id, log_path, job)
            elif tool == "bloodhound":
                parse_result = parse_bloodhound_job(engagement_id, log_path, job)
            elif tool == "nikto":
                parse_result = parse_nikto_job(engagement_id, log_path, job)
            elif tool == "dalfox":
                parse_result = parse_dalfox_job(engagement_id, log_path, job)
            elif tool == "http_fingerprint":
                parse_result = parse_http_fingerprint_job(engagement_id, log_path, job)
            else:
                return {
                    "success": False,
                    "message": f"No parser available for tool: {tool}",
                }

        except Exception as e:
            return {"success": False, "message": f"Parse error: {str(e)}"}

    if not parse_result:
        return {"success": False, "message": "Parser returned no results"}

    if "error" in parse_result:
        return {"success": False, "message": f"Parse error: {parse_result['error']}"}

    # Update job status and parse_result in jobs.json
    new_status = parse_result.get("status")
    jobs = _read_jobs()
    for j in jobs:
        if j.get("id") == job_id:
            old_status = j.get("status")
            if new_status:
                j["status"] = new_status
            j["parse_result"] = parse_result  # Save the updated parse_result!
            j["reparsed"] = True
            logger.info(f"Job {job_id} reparsed: status {old_status} -> {new_status}")
            break
    _write_jobs(jobs)

    # Trigger auto-chain after reparse (like job completion does)
    try:
        from souleyez.core.tool_chaining import ToolChaining

        tc = ToolChaining()
        chained_job_ids = tc.auto_chain(job=job, parse_results=parse_result)
        if chained_job_ids:
            logger.info(f"Reparse triggered {len(chained_job_ids)} auto-chain job(s)")
    except Exception as e:
        logger.debug(f"Auto-chain after reparse failed: {e}")

    return {
        "success": True,
        "message": f"Job {job_id} re-parsed successfully",
        "old_status": job.get("status"),
        "new_status": new_status,
        "parse_result": parse_result,
    }


def reparse_jobs_by_tool(tool: str, limit: int = 100) -> Dict[str, Any]:
    """
    Re-parse all jobs for a specific tool.

    Args:
        tool: Tool name (e.g., 'enum4linux', 'msf_auxiliary')
        limit: Maximum number of jobs to reparse

    Returns:
        Dict with summary of results
    """
    from .background import list_jobs

    jobs = list_jobs(limit=limit)
    tool_jobs = [j for j in jobs if j.get("tool", "").lower() == tool.lower()]

    results = {
        "tool": tool,
        "total": len(tool_jobs),
        "success": 0,
        "failed": 0,
        "updated": [],
        "errors": [],
    }

    for job in tool_jobs:
        job_id = job.get("id")
        old_status = job.get("status")

        result = reparse_job(job_id)

        if result.get("success"):
            results["success"] += 1
            new_status = result.get("new_status")
            if old_status != new_status:
                results["updated"].append(
                    {"id": job_id, "old": old_status, "new": new_status}
                )
        else:
            results["failed"] += 1
            results["errors"].append({"id": job_id, "error": result.get("message")})

    return results


def parse_nmap_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse nmap job results."""
    try:
        from souleyez.core.cve_matcher import CVEMatcher
        from souleyez.parsers.nmap_parser import parse_nmap_log
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        # Parse the log file
        parsed = parse_nmap_log(log_path)

        if "error" in parsed:
            return {"error": parsed["error"]}

        # Import into database
        hm = HostManager()
        result = hm.import_nmap_results(engagement_id, parsed)
        logger.info(
            f"Nmap import: {result['hosts_added']} hosts, {result['services_added']} services in engagement {engagement_id}"
        )
        logger.debug(f"Info scripts to process: {len(parsed.get('info_scripts', []))}")

        # Check for CVEs and common issues
        fm = FindingsManager()
        cve_matcher = CVEMatcher()
        findings_added = 0

        # First, store any script-detected vulnerabilities (from --script vuln)
        for vuln in parsed.get("vulnerabilities", []):
            host_ip = vuln.get("host_ip")
            if not host_ip:
                continue

            # Find host ID
            host = hm.get_host_by_ip(engagement_id, host_ip)
            if not host:
                continue

            host_id = host["id"]

            # Determine severity from CVSS score
            cvss = vuln.get("cvss_score")
            if cvss:
                if cvss >= 9.0:
                    severity = "critical"
                elif cvss >= 7.0:
                    severity = "high"
                elif cvss >= 4.0:
                    severity = "medium"
                else:
                    severity = "low"
            else:
                # Default based on script type
                severity = "high" if vuln.get("state") == "VULNERABLE" else "medium"

            # Build references string from CVE IDs
            cve_ids = vuln.get("cve_ids", [])
            refs = None
            if cve_ids:
                cve_refs = [
                    f"https://nvd.nist.gov/vuln/detail/{cve}" for cve in cve_ids[:3]
                ]
                refs = ", ".join(cve_refs)
            elif vuln.get("references"):
                refs = ", ".join(vuln.get("references", [])[:3])

            # Build description with CVSS and CVE info
            description = vuln.get(
                "description", f"Detected by nmap script: {vuln.get('script')}"
            )
            if cvss:
                description += f"\n\nCVSS Score: {cvss}"
            if cve_ids:
                description += f"\nCVE IDs: {', '.join(cve_ids[:5])}"

            # Build title - include CVE if available
            title = vuln.get("title", vuln.get("script", "Unknown Vulnerability"))
            if cve_ids and cve_ids[0] not in title:
                title = f"{cve_ids[0]}: {title}"

            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                title=title,
                finding_type="vulnerability",
                severity=severity,
                description=description,
                port=vuln.get("port"),
                tool="nmap",
                refs=refs,
                evidence=f"Host: {vuln.get('host_ip', 'unknown')}:{vuln.get('port', 'N/A')}\nScript: {vuln.get('script', 'nmap')}",
            )
            findings_added += 1

        # Then check for inferred CVEs based on service versions
        for host_data in parsed.get("hosts", []):
            if host_data.get("status") == "up":
                # Find host ID
                host = hm.get_host_by_ip(engagement_id, host_data.get("ip"))
                if not host:
                    continue

                host_id = host["id"]

                # Check each service for CVEs and common issues
                for svc in host_data.get("services", []):
                    service_info = {
                        "service_name": svc.get("service", ""),
                        "version": svc.get("version", ""),
                        "port": svc.get("port"),
                        "protocol": svc.get("protocol", "tcp"),
                    }

                    # Also check database for stored version if not in parsed data
                    if not service_info["version"]:
                        services = hm.get_host_services(host_id)
                        for stored_svc in services:
                            if stored_svc["port"] == svc.get("port"):
                                service_info["version"] = stored_svc.get(
                                    "service_version", ""
                                )
                                break

                    # Check for CVEs
                    cve_findings = cve_matcher.parse_nmap_service(service_info)
                    for finding in cve_findings:
                        fm.add_finding(
                            engagement_id=engagement_id,
                            host_id=host_id,
                            title=finding["title"],
                            finding_type="vulnerability",
                            severity=finding["severity"],
                            description=finding["description"],
                            port=finding.get("port"),
                            tool="nmap",
                            refs=f"https://nvd.nist.gov/vuln/detail/{finding.get('cve_id')}",
                        )
                        findings_added += 1

                    # Check for common issues
                    issue_findings = cve_matcher.scan_for_common_issues(service_info)
                    for finding in issue_findings:
                        fm.add_finding(
                            engagement_id=engagement_id,
                            host_id=host_id,
                            title=finding["title"],
                            finding_type="misconfiguration",
                            severity=finding["severity"],
                            description=finding["description"],
                            port=finding.get("port"),
                            tool="nmap",
                        )
                        findings_added += 1

        # Store info script findings (vnc-info, ssh-hostkey, etc.)
        for info in parsed.get("info_scripts", []):
            host_ip = info.get("host_ip")
            if not host_ip:
                logger.warning(f"Info script missing host_ip: {info.get('script')}")
                continue

            # Find host ID
            host = hm.get_host_by_ip(engagement_id, host_ip)
            if not host:
                logger.warning(
                    f"Host not found for info script: {host_ip} in engagement {engagement_id}"
                )
                continue

            host_id = host["id"]

            # Build finding title and description
            script_name = info.get("script", "unknown")
            title = info.get("title", script_name)
            description = info.get("description", "")

            # Add port to title if available
            port = info.get("port")
            if port:
                title = f"{title} (port {port})"

            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                title=title,
                finding_type="info",
                severity="info",
                description=description,
                port=port,
                tool="nmap",
                evidence=f"Host: {host_ip}:{port if port else 'N/A'}\nScript: {script_name}",
            )
            findings_added += 1

        # Build host details list for summary
        host_details = []
        for host_data in parsed.get("hosts", []):
            if host_data.get("status") == "up":
                services = host_data.get("services", [])
                service_count = len(services)

                # Get top ports for detailed scans
                top_ports = []
                for svc in services[:5]:  # Top 5 ports
                    port = svc.get("port")
                    service_name = svc.get("service", "unknown")
                    top_ports.append(f"{port}/{service_name}")

                host_details.append(
                    {
                        "ip": host_data.get("ip"),
                        "hostname": host_data.get("hostname"),
                        "os": host_data.get("os"),
                        "service_count": service_count,
                        "top_ports": top_ports,
                    }
                )

        # Determine scan type based on job args
        args = job.get("args", [])
        is_discovery = "-sn" in args or "--discovery" in args
        is_full_scan = any(x in args for x in ["-sV", "-O", "-A", "-p1-65535"])

        # Collect all services for tool chaining
        # Only include actionable port states (open, filtered)
        # Exclude closed/unfiltered - no point chaining on inaccessible ports
        chainable_states = {"open", "filtered", "open|filtered"}
        all_services = []
        for host_data in parsed.get("hosts", []):
            if host_data.get("status") == "up":
                for svc in host_data.get("services", []):
                    port_state = svc.get("state", "open").lower()
                    if port_state in chainable_states:
                        all_services.append(
                            {
                                "ip": host_data.get("ip"),
                                "port": svc.get("port"),
                                "protocol": svc.get("protocol", "tcp"),
                                "state": port_state,
                                "service_name": svc.get("service", ""),
                                "version": svc.get("version", ""),
                            }
                        )

        # Check for nmap errors before determining status
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()
        nmap_error = detect_tool_error(log_content, "nmap")

        # Determine status based on results
        hosts_up = len([h for h in parsed.get("hosts", []) if h.get("status") == "up"])
        if nmap_error:
            status = STATUS_ERROR  # Tool failed to run properly
        elif hosts_up > 0:
            status = STATUS_DONE  # Found hosts
        else:
            status = STATUS_NO_RESULTS  # No hosts up

        return {
            "tool": "nmap",
            "status": status,
            "hosts_added": result["hosts_added"],
            "services_added": result["services_added"],
            "findings_added": findings_added,
            "host_details": host_details,
            "is_discovery": is_discovery,
            "is_full_scan": is_full_scan,
            "services": all_services,  # For tool chaining
            "hosts": parsed.get("hosts", []),  # For tool chaining
        }
    except Exception as e:
        return {"error": str(e)}


def parse_theharvester_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse theHarvester job results."""
    try:
        from souleyez.parsers.theharvester_parser import (
            get_osint_stats,
            parse_theharvester_output,
        )
        from souleyez.storage.hosts import HostManager
        from souleyez.storage.osint import OsintManager

        # Read the log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

        # Parse theHarvester output
        target = job.get("target", "")
        parsed = parse_theharvester_output(log_content, target)

        # Store OSINT data
        om = OsintManager()
        osint_added = 0

        # Add emails
        if parsed["emails"]:
            count = om.bulk_add_osint_data(
                engagement_id, "email", parsed["emails"], "theHarvester", target
            )
            osint_added += count

        # Add hosts/subdomains
        if parsed["hosts"]:
            count = om.bulk_add_osint_data(
                engagement_id, "host", parsed["hosts"], "theHarvester", target
            )
            osint_added += count

        # Add IPs
        if parsed["ips"]:
            count = om.bulk_add_osint_data(
                engagement_id, "ip", parsed["ips"], "theHarvester", target
            )
            osint_added += count

        # Add URLs
        if parsed["urls"]:
            count = om.bulk_add_osint_data(
                engagement_id, "url", parsed["urls"], "theHarvester", target
            )
            osint_added += count

        # Add ASNs
        if parsed["asns"]:
            count = om.bulk_add_osint_data(
                engagement_id, "asn", parsed["asns"], "theHarvester", target
            )
            osint_added += count

        # Also add discovered IPs and hosts to the hosts table if they look valid
        hm = HostManager()
        hosts_added = 0

        for ip in parsed["ips"]:
            try:
                # Try to add IP as a host with 'discovered' status
                host_id = hm.add_or_update_host(
                    engagement_id, {"ip": ip, "status": "discovered"}
                )
                hosts_added += 1
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)
                logger.info(f"Added IP {ip} to hosts table (host_id={host_id})")
            except Exception as e:
                # Log the error but continue processing other IPs
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)
                logger.warning(f"Failed to add IP {ip} to hosts: {e}")

        stats = get_osint_stats(parsed)

        # Determine status based on results
        total_osint_found = (
            len(parsed["emails"])
            + len(parsed["hosts"])
            + len(parsed["ips"])
            + len(parsed["urls"])
        )
        if total_osint_found > 0:
            status = STATUS_DONE  # Found OSINT data
        else:
            status = STATUS_NO_RESULTS  # No data found

        return {
            "tool": "theHarvester",
            "status": status,
            "osint_added": osint_added,
            "hosts_added": hosts_added,
            "stats": stats,
            "domains": (
                [target] if target else []
            ),  # For auto-chaining to whois/dnsrecon
            "target": target,  # Original target domain
            "urls": parsed[
                "urls"
            ],  # All URLs - processed by tool_chaining special handler
            "ips": parsed["ips"],  # All IPs for nmap auto-chaining
        }
    except Exception as e:
        return {"error": str(e)}


def _matches_path_pattern(path: str, pattern: str) -> bool:
    """
    Check if a path matches a pattern using smart matching rules.

    For most patterns: substring match (e.g., 'phpmyadmin' in '/phpmyadmin/index.php')
    For 'api' and 'rest': exact path segment match only
        - Matches: /api, /api/, /api/users, /rest, /rest/products
        - Does NOT match: /apis, /restore, /restaurants, /api.js

    Args:
        path: URL path (e.g., '/api/users' or '/restore')
        pattern: Pattern to match (e.g., 'api' or 'rest')

    Returns:
        True if the path matches the pattern
    """
    # Patterns that require exact path segment matching (not substring)
    EXACT_SEGMENT_PATTERNS = {"api", "rest"}

    if pattern in EXACT_SEGMENT_PATTERNS:
        # Split path into segments and check for exact match
        # /api → ['', 'api'] → 'api' in segments
        # /api/users → ['', 'api', 'users'] → 'api' in segments
        # /apis → ['', 'apis'] → 'api' NOT in segments
        # /restore → ['', 'restore'] → 'rest' NOT in segments
        segments = path.rstrip("/").split("/")
        return pattern in segments
    else:
        # Default: substring match
        return pattern in path


def _create_findings_for_sensitive_paths(
    engagement_id: int, host_id: int, paths: list, job: Optional[Dict[str, Any]] = None
) -> list:
    """
    Analyze discovered paths and create findings for sensitive/interesting ones.

    Args:
        engagement_id: Engagement ID
        host_id: Host ID where paths were discovered
        paths: List of path dictionaries from gobuster
        job: Optional job dict for metadata (includes deduplication info)

    Returns:
        List of created findings (with id, title, severity, etc.)
    """
    from souleyez.storage.findings import FindingsManager
    from souleyez.storage.hosts import HostManager

    # Define sensitive path patterns with severity and descriptions
    SENSITIVE_PATTERNS = {
        # Database admin interfaces (Critical/High)
        "phpmyadmin": {
            "severity": "high",
            "title": "Database Admin Interface: phpMyAdmin",
            "description": "phpMyAdmin interface exposed. This provides direct database access and is a high-value target. Check for default credentials and known CVEs.",
        },
        "adminer": {
            "severity": "high",
            "title": "Database Admin Interface: Adminer",
            "description": "Adminer database management tool exposed. Provides access to multiple database types.",
        },
        "mysql": {
            "severity": "medium",
            "title": "MySQL Related Path",
            "description": "MySQL related endpoint discovered. May provide database information or access.",
        },
        # Admin panels (High)
        "admin": {
            "severity": "high",
            "title": "Admin Panel Discovered",
            "description": "Administrative interface found. May allow privileged access if credentials are compromised.",
        },
        "administrator": {
            "severity": "high",
            "title": "Administrator Panel",
            "description": "Administrator interface discovered. Target for credential attacks and privilege escalation.",
        },
        "cpanel": {
            "severity": "high",
            "title": "cPanel Interface",
            "description": "cPanel control panel exposed. Provides server-wide administration capabilities.",
        },
        "plesk": {
            "severity": "high",
            "title": "Plesk Control Panel",
            "description": "Plesk web hosting control panel discovered.",
        },
        "console": {
            "severity": "high",
            "title": "Console Interface",
            "description": "Administrative console interface found. May provide system-level access.",
        },
        "dashboard": {
            "severity": "medium",
            "title": "Dashboard Interface",
            "description": "Dashboard interface discovered. May contain sensitive information or administrative functions.",
        },
        "manager": {
            "severity": "medium",
            "title": "Management Interface",
            "description": "Management interface found. Review for administrative capabilities.",
        },
        # Backup/Config (High/Medium)
        "backup": {
            "severity": "high",
            "title": "Backup Directory",
            "description": "Backup directory discovered. May contain database dumps, source code, or sensitive data.",
        },
        "backups": {
            "severity": "high",
            "title": "Backups Directory",
            "description": "Backups directory found. Check for downloadable backup files.",
        },
        "config": {
            "severity": "medium",
            "title": "Configuration Directory",
            "description": "Configuration directory discovered. May expose configuration files with credentials.",
        },
        "configuration": {
            "severity": "medium",
            "title": "Configuration Path",
            "description": "Configuration path found. Review for exposed settings and credentials.",
        },
        ".env": {
            "severity": "critical",
            "title": "Environment File Exposed",
            "description": "Environment configuration file (.env) is accessible. Likely contains database credentials, API keys, and secrets.",
        },
        ".git": {
            "severity": "critical",
            "title": "Git Repository Exposed",
            "description": "Git repository (.git) directory is accessible. Can be downloaded to recover source code and commit history.",
        },
        ".svn": {
            "severity": "critical",
            "title": "SVN Repository Exposed",
            "description": "Subversion (.svn) directory exposed. May allow source code recovery.",
        },
        # Upload directories (Medium)
        "upload": {
            "severity": "medium",
            "title": "Upload Directory",
            "description": "File upload directory discovered. Check for upload functionality and file execution capabilities.",
        },
        "uploads": {
            "severity": "medium",
            "title": "Uploads Directory",
            "description": "Uploads directory found. May allow file upload and potential code execution.",
        },
        "files": {
            "severity": "low",
            "title": "Files Directory",
            "description": "Files directory discovered. May contain user-uploaded or system files.",
        },
        # Development/Testing (Medium)
        "test": {
            "severity": "medium",
            "title": "Test Environment",
            "description": "Test environment or directory found. Often has weaker security than production.",
        },
        "testing": {
            "severity": "medium",
            "title": "Testing Directory",
            "description": "Testing directory discovered. May have debug features enabled.",
        },
        "dev": {
            "severity": "medium",
            "title": "Development Environment",
            "description": "Development environment found. Typically has less security controls than production.",
        },
        "development": {
            "severity": "medium",
            "title": "Development Directory",
            "description": "Development directory discovered. May expose debug information or development tools.",
        },
        "staging": {
            "severity": "medium",
            "title": "Staging Environment",
            "description": "Staging environment found. May mirror production with weaker access controls.",
        },
        "debug": {
            "severity": "medium",
            "title": "Debug Interface",
            "description": "Debug interface or directory discovered. May expose sensitive debugging information.",
        },
        # WordPress (Medium)
        "wp-admin": {
            "severity": "medium",
            "title": "WordPress Admin Panel (wp-admin)",
            "description": "WordPress admin login page found. Target for brute-force attacks.",
        },
        "wp-login": {
            "severity": "medium",
            "title": "WordPress Login (wp-login)",
            "description": "WordPress login page discovered.",
        },
        "wp-content": {
            "severity": "low",
            "title": "WordPress Installation (wp-content)",
            "description": "WordPress installation detected. Run WPScan for detailed enumeration.",
        },
        "xmlrpc": {
            "severity": "medium",
            "title": "WordPress XML-RPC (xmlrpc.php)",
            "description": "WordPress XML-RPC interface exposed. Can be used for brute-force attacks and DDoS amplification.",
        },
        "wp-json": {
            "severity": "medium",
            "title": "WordPress REST API (wp-json)",
            "description": "WordPress REST API endpoint. May expose user enumeration via /wp-json/wp/v2/users.",
        },
        # API endpoints (Low/Info)
        "api": {
            "severity": "low",
            "title": "API Endpoint",
            "description": "API endpoint discovered. Review for authentication requirements and exposed functionality.",
        },
        "rest": {
            "severity": "low",
            "title": "REST API Endpoint",
            "description": "REST API endpoint discovered. Test for authentication bypass and injection vulnerabilities.",
        },
        "swagger": {
            "severity": "medium",
            "title": "Swagger API Documentation",
            "description": "Swagger API documentation interface found. Exposes API structure and endpoints.",
        },
        "graphql": {
            "severity": "low",
            "title": "GraphQL Endpoint",
            "description": "GraphQL endpoint discovered. Test for introspection and injection vulnerabilities.",
        },
        # Vulnerable Web Applications (High)
        "juice": {
            "severity": "high",
            "title": "OWASP Juice Shop Detected",
            "description": "OWASP Juice Shop vulnerable web application found. This is an intentionally insecure application for training purposes.",
        },
        "juice-shop": {
            "severity": "high",
            "title": "OWASP Juice Shop Detected",
            "description": "OWASP Juice Shop vulnerable web application found. This is an intentionally insecure application for training purposes.",
        },
        "dvwa": {
            "severity": "high",
            "title": "Damn Vulnerable Web App (DVWA) Detected",
            "description": "DVWA intentionally vulnerable application found. Contains multiple security vulnerabilities for testing.",
        },
        "webgoat": {
            "severity": "high",
            "title": "OWASP WebGoat Detected",
            "description": "OWASP WebGoat training application found. Contains intentional security flaws for educational purposes.",
        },
        "mutillidae": {
            "severity": "high",
            "title": "Mutillidae Vulnerable App Detected",
            "description": "Mutillidae intentionally vulnerable application found. Contains OWASP Top 10 vulnerabilities.",
        },
        "bwapp": {
            "severity": "high",
            "title": "bWAPP Detected",
            "description": "buggy Web Application (bWAPP) found. Contains over 100 web vulnerabilities for testing.",
        },
        "hackazon": {
            "severity": "high",
            "title": "Hackazon Vulnerable App Detected",
            "description": "Hackazon vulnerable e-commerce application found. Contains realistic web vulnerabilities.",
        },
    }

    fm = FindingsManager()
    hm = HostManager()

    # Get host info for finding description
    host_info = hm.get_host(host_id)
    host_ip = host_info.get("ip_address", "Unknown") if host_info else "Unknown"

    findings_created = 0
    created_findings = []  # List of finding dicts for auto-chaining

    for path_dict in paths:
        url = path_dict.get("url", "")
        status_code = path_dict.get("status_code", 0)

        # Only create findings for accessible paths (2xx, 3xx, 401, 403, 5xx)
        # 403 is interesting because it confirms the path exists even if forbidden
        # 5xx errors indicate the path exists but has server-side issues (valuable for testing)
        if status_code not in [
            200,
            201,
            301,
            302,
            303,
            307,
            308,
            401,
            403,
            500,
            502,
            503,
        ]:
            continue

        # Extract path from URL
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = parsed.path.lower()

        # Check each sensitive pattern
        for pattern, info in SENSITIVE_PATTERNS.items():
            if _matches_path_pattern(path, pattern):
                # Create finding
                description = f"{info['description']}\n\nURL: {url}\nStatus: {status_code}\nHost: {host_ip}"

                # Add deduplication attribution if this scan covered multiple IPs
                if job:
                    metadata = job.get("metadata", {})
                    associated_ips = metadata.get("associated_ips", [])
                    if associated_ips and len(associated_ips) > 1:
                        representative_ip = metadata.get("representative_ip", host_ip)
                        domain = metadata.get("domain_context", "")
                        description += f"\n\n[Web Target Deduplication] This finding was discovered on {representative_ip}"
                        description += (
                            f" (representative IP for {len(associated_ips)} IPs serving"
                        )
                        if domain:
                            description += f" {domain}"
                        description += (
                            f"). All affected IPs: {', '.join(associated_ips)}"
                        )

                finding_data = {
                    "title": info["title"],
                    "description": description,
                    "severity": info["severity"],
                    "tool": "gobuster",
                    "host_id": host_id,
                    "job_id": job.get("id") if job else None,
                }

                # Check if finding already exists (avoid duplicates)
                existing_findings = fm.list_findings(engagement_id)
                duplicate = False
                for existing in existing_findings:
                    if (
                        existing.get("title") == finding_data["title"]
                        and existing.get("host_id") == host_id
                        and url in existing.get("description", "")
                    ):
                        duplicate = True
                        break

                if not duplicate:
                    finding_id = fm.add_finding(
                        engagement_id=engagement_id,
                        title=finding_data["title"],
                        finding_type="web_discovery",
                        severity=finding_data["severity"],
                        description=finding_data.get("description"),
                        host_id=finding_data.get("host_id"),
                        tool=finding_data.get("tool"),
                    )
                    findings_created += 1

                    # Add to created_findings list for auto-chaining
                    created_findings.append(
                        {
                            "id": finding_id,
                            "title": finding_data["title"],
                            "severity": finding_data["severity"],
                            "tool": "gobuster",
                            "url": url,  # Include full URL for finding-based auto-chains
                        }
                    )

                # Only match first pattern to avoid duplicate findings
                break

    return created_findings


def parse_gobuster_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse gobuster job results."""
    try:
        from urllib.parse import urlparse

        from souleyez.parsers.gobuster_parser import (
            generate_next_steps,
            get_paths_stats,
            parse_gobuster_output,
        )
        from souleyez.storage.hosts import HostManager
        from souleyez.storage.web_paths import WebPathsManager

        # Read the log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

        # Parse gobuster output
        target = job.get("target", "")
        parsed = parse_gobuster_output(log_content, target)

        # Get or create host from target URL
        hm = HostManager()
        host_id = None

        if parsed["target_url"]:
            parsed_url = urlparse(parsed["target_url"])
            hostname = parsed_url.hostname

            if hostname:
                # Try to find existing host by hostname
                hosts = hm.list_hosts(engagement_id)
                for host in hosts:
                    if (
                        host.get("hostname") == hostname
                        or host.get("ip_address") == hostname
                    ):
                        host_id = host["id"]
                        break

                # Create host if not found
                if not host_id:
                    # Try to determine if it's an IP or hostname
                    import re

                    is_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname)

                    if is_ip:
                        host_id = hm.add_or_update_host(
                            engagement_id, {"ip": hostname, "status": "up"}
                        )
                    else:
                        # It's a hostname - we need an IP, so skip host creation for now
                        # Just store paths without host_id (will need to fix schema)
                        pass

        # Store web paths
        wpm = WebPathsManager()
        paths_added = 0
        created_findings = []  # Initialize here

        if host_id and parsed["paths"]:
            paths_added = wpm.bulk_add_web_paths(host_id, parsed["paths"])

            # Check for sensitive paths and create findings
            created_findings = _create_findings_for_sensitive_paths(
                engagement_id, host_id, parsed["paths"], job
            )

        stats = get_paths_stats(parsed)

        # Extract PHP files for auto-chaining SQLMap with --crawl
        # Include 200 (accessible), 401 (auth-required), 403 (forbidden) - all can have parameters
        # Exclude 404 (doesn't exist) and 5xx (server error)
        # Store as tuples (url, status_code) to enable prioritization in tool_chaining.py
        php_files = [
            (path.get("url"), path.get("status_code"))
            for path in parsed["paths"]
            if path.get("url", "").endswith(".php")
            and path.get("status_code") in [200, 401, 403]
        ]

        # Extract ASP/ASPX files for auto-chaining SQLMap (same logic as PHP)
        asp_files = [
            (path.get("url"), path.get("status_code"))
            for path in parsed["paths"]
            if (
                path.get("url", "").lower().endswith(".asp")
                or path.get("url", "").lower().endswith(".aspx")
            )
            and path.get("status_code") in [200, 401, 403]
        ]

        # Extract high-value directories (redirects) for auto-chaining
        # These are vulnerable web apps that should be crawled by sqlmap
        high_value_dir_keywords = [
            "mutillidae",
            "dvwa",
            "bwapp",
            "webgoat",
            "phpmyadmin",
            "juice",
            "juice-shop",  # OWASP Juice Shop
            "hackazon",
            "pentesterlab",
            "vulnhub",  # Other vulnerable apps
            "api",
            "rest",
            "graphql",  # Modern API endpoints
            "drupal",
            "wordpress",
            "joomla",
            "moodle",
            "magento",
            "phpbb",
            "opencart",
            "prestashop",
            "zen-cart",
            "oscommerce",
            "wp-content",
            "wp-admin",
            "wp-includes",  # WordPress directory indicators
        ]

        high_value_dirs = []
        redirect_codes = [301, 302, 303, 307, 308]
        for path in parsed["paths"]:
            # Look for redirects to directories (all redirect codes)
            # 302 is common for CMS paths (e.g., /dashboard -> /wp-admin/)
            if path.get("status_code") in redirect_codes and path.get("redirect"):
                url = path.get("url", "").lower()
                redirect = path.get("redirect", "").lower()

                # Check if URL or redirect contains high-value keywords
                if any(
                    keyword in url or keyword in redirect
                    for keyword in high_value_dir_keywords
                ):
                    # Use the redirect target (with trailing slash)
                    high_value_dirs.append(path.get("redirect"))
                    logger.info(
                        f"Detected high-value directory: {path.get('redirect')}"
                    )

        logger.info(
            f"Gobuster result summary: {len(php_files)} PHP files, {len(asp_files)} ASP files, {len(high_value_dirs)} high-value directories"
        )

        # Generate next steps for manual follow-up
        next_steps = generate_next_steps(parsed)

        # Check for wildcard response (for auto-retry)
        wildcard_detected = False
        exclude_length = None

        if "the server returns a status code that matches" in log_content:
            wildcard_detected = True
            # Extract response length: "=> 403 (Length: 1434)"
            import re

            length_match = re.search(r"\(Length: (\d+)\)", log_content)
            if length_match:
                exclude_length = length_match.group(1)
                logger.info(f"Gobuster wildcard detected: Length {exclude_length}b")

        # Check for host-level redirect (for auto-retry with corrected target)
        host_redirect_detected = False
        redirect_target = None

        if "HOST_REDIRECT_TARGET:" in log_content:
            host_redirect_detected = True
            import re

            redirect_match = re.search(r"HOST_REDIRECT_TARGET:\s*(\S+)", log_content)
            if redirect_match:
                redirect_target = redirect_match.group(1)
                logger.info(f"Gobuster host redirect detected: {redirect_target}")

        # Check for gobuster errors
        gobuster_error = detect_tool_error(log_content, "gobuster")

        # Determine status based on results
        if gobuster_error:
            status = STATUS_ERROR  # Tool failed to connect
        elif host_redirect_detected:
            # Host redirect detected - warning status (triggers auto-retry with corrected target)
            status = STATUS_WARNING
        elif wildcard_detected:
            # Wildcard detected - warning status (triggers auto-retry)
            status = STATUS_WARNING
        elif stats["total"] > 0:
            # Found paths - done
            status = STATUS_DONE
        else:
            # No paths found - no_results
            status = STATUS_NO_RESULTS

        result = {
            "tool": "gobuster",
            "status": status,
            "paths_added": paths_added,
            "total_paths": stats["total"],
            "paths_found": stats["total"],  # For dashboard display
            "redirects_found": stats.get("redirects", 0),
            "by_status": stats["by_status"],
            "target_url": parsed.get("target_url"),
            "findings": created_findings,  # Include findings for auto-chaining
            "php_files": php_files,  # For SQLMap --crawl auto-chaining
            "asp_files": asp_files,  # For SQLMap --crawl auto-chaining (ASP/ASPX)
            "high_value_dirs": high_value_dirs,  # High-value directories to crawl
            "next_steps": next_steps,  # Suggested manual follow-up actions
        }

        # Add wildcard info if detected
        if wildcard_detected:
            result["wildcard_detected"] = True
            if exclude_length:
                result["exclude_length"] = exclude_length

        # Add host redirect info if detected
        if host_redirect_detected:
            result["host_redirect_detected"] = True
            if redirect_target:
                result["redirect_target"] = redirect_target

        return result
    except Exception as e:
        return {"error": str(e)}


def parse_sqlmap_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse sqlmap job results."""
    try:
        from urllib.parse import urlparse

        from souleyez.parsers.sqlmap_parser import get_sqli_stats, parse_sqlmap_output
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager
        from souleyez.storage.sqlmap_data import SQLMapDataManager

        # Read the log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

        # Parse sqlmap output
        target = job.get("target", "")
        parsed = parse_sqlmap_output(log_content, target)

        # Get or create host from target URL
        hm = HostManager()
        host_id = None

        if parsed["target_url"]:
            parsed_url = urlparse(parsed["target_url"])
            hostname = parsed_url.hostname

            if hostname:
                # Try to find existing host
                import re

                is_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname)

                if is_ip:
                    host = hm.get_host_by_ip(engagement_id, hostname)
                    if host:
                        host_id = host["id"]
                    else:
                        host_id = hm.add_or_update_host(
                            engagement_id, {"ip": hostname, "status": "up"}
                        )
                else:
                    # Try to match by hostname (check both hostname field and ip field)
                    hosts = hm.list_hosts(engagement_id)
                    for h in hosts:
                        # Match against ip_address, ip (normalized), or hostname fields
                        if (
                            h.get("hostname") == hostname
                            or h.get("ip") == hostname
                            or h.get("ip_address") == hostname
                        ):
                            host_id = h["id"]
                            break

                    # If host not found, try to resolve hostname to IP and create
                    if not host_id:
                        try:
                            import socket

                            ip_address = socket.gethostbyname(hostname)
                            host_id = hm.add_or_update_host(
                                engagement_id,
                                {
                                    "ip": ip_address,
                                    "hostname": hostname,
                                    "status": "up",
                                },
                            )
                        except (socket.gaierror, socket.herror):
                            # Cannot resolve hostname, skip exploitation findings
                            pass

        # Create virtual HTTP/HTTPS service for web targets
        if host_id and parsed["target_url"]:
            parsed_url = urlparse(parsed["target_url"])
            port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)

            # Check if service already exists
            existing_services = hm.get_host_services(host_id)
            service_exists = any(s.get("port") == port for s in existing_services)

            if not service_exists:
                # Create virtual HTTP/HTTPS service entry
                hm.add_service(
                    host_id,
                    {
                        "port": port,
                        "protocol": "tcp",
                        "service_name": parsed_url.scheme,  # 'http' or 'https'
                        "state": "open",
                    },
                )

        # Extract port from URL for finding association
        target_port = None
        if parsed["target_url"]:
            parsed_url = urlparse(parsed["target_url"])
            target_port = parsed_url.port or (
                443 if parsed_url.scheme == "https" else 80
            )

        # Store vulnerabilities as findings
        fm = FindingsManager()
        findings_added = 0
        credentials_added = 0  # Track credentials extracted from dumps
        extracted_credentials = []  # For chaining to hydra

        for vuln in parsed["vulnerabilities"]:
            # Determine severity
            vuln_type = vuln.get("vuln_type", "unknown")
            if vuln_type == "sqli" and vuln.get("injectable"):
                severity = "critical"
                finding_type = "sql_injection"
                title = f"SQL Injection in parameter '{vuln['parameter']}'"
            elif vuln_type == "xss":
                severity = vuln.get("severity", "medium")
                finding_type = "xss"
                title = f"Possible XSS in parameter '{vuln['parameter']}'"
            elif vuln_type == "file_inclusion":
                severity = vuln.get("severity", "high")
                finding_type = "file_inclusion"
                title = f"Possible File Inclusion in parameter '{vuln['parameter']}'"
            else:
                severity = "medium"
                finding_type = "web_vulnerability"
                title = f"Vulnerability in parameter '{vuln['parameter']}'"

            # Create description
            description = vuln.get("description", "")
            if vuln.get("technique"):
                description += f"\nTechnique: {vuln['technique']}"
            if vuln.get("dbms"):
                description += f"\nDBMS: {vuln['dbms']}"

            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                port=target_port,
                title=title,
                finding_type=finding_type,
                severity=severity,
                description=description,
                tool="sqlmap",
                path=vuln.get("url"),
            )
            findings_added += 1

        # === EXPLOITATION FINDINGS ===
        # Track progressive exploitation levels beyond just detecting the vulnerability

        # Level 2: Database Enumeration (Exploitation Confirmed)
        databases = parsed.get("databases", [])
        if databases and host_id:
            dbms_info = parsed.get("dbms", "Unknown")
            db_count = len(databases)

            # Limit database list in description (show first 10)
            db_list = databases[:10]
            db_list_str = ", ".join(db_list)
            if len(databases) > 10:
                db_list_str += f" ... and {len(databases) - 10} more"

            description = f"SQL injection was successfully exploited to enumerate {db_count} database(s).\n\n"
            description += f"DBMS: {dbms_info}\n"
            description += f"Databases: {db_list_str}\n\n"
            description += "This confirms the SQL injection vulnerability is exploitable and provides access to database structure."

            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                port=target_port,
                title=f"SQL Injection Exploited - {db_count} Database(s) Enumerated",
                finding_type="sql_injection_exploitation",
                severity="critical",
                description=description,
                tool="sqlmap",
                path=parsed.get("target_url"),
            )
            findings_added += 1

        # Level 3: Table Enumeration (Deeper Exploitation)
        tables = parsed.get("tables", {})
        if tables and host_id:
            total_tables = sum(len(table_list) for table_list in tables.values())

            if total_tables > 0:
                description = f"SQL injection was exploited to enumerate {total_tables} table(s) across {len(tables)} database(s).\n\n"

                # List tables by database (limit to first 5 databases, first 10 tables each)
                for idx, (db_name, table_list) in enumerate(list(tables.items())[:5]):
                    description += (
                        f"\nDatabase '{db_name}' ({len(table_list)} tables):\n"
                    )
                    shown_tables = table_list[:10]
                    description += "  - " + "\n  - ".join(shown_tables)
                    if len(table_list) > 10:
                        description += f"\n  ... and {len(table_list) - 10} more tables"

                if len(tables) > 5:
                    remaining_dbs = len(tables) - 5
                    remaining_tables = sum(
                        len(table_list)
                        for db_name, table_list in list(tables.items())[5:]
                    )
                    description += f"\n\n... and {remaining_tables} more tables in {remaining_dbs} other database(s)"

                description += "\n\nTable structure reveals potential sensitive data locations and attack surface."

                fm.add_finding(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    port=target_port,
                    title=f"SQL Injection Exploited - {total_tables} Table(s) Enumerated",
                    finding_type="sql_injection_exploitation",
                    severity="high",
                    description=description,
                    tool="sqlmap",
                    path=parsed.get("target_url"),
                )
                findings_added += 1

        # Level 4: Data Dumped (CRITICAL - Actual Data Breach!)
        dumped_data = parsed.get("dumped_data", {})
        if dumped_data and host_id:
            total_rows = sum(data.get("row_count", 0) for data in dumped_data.values())
            total_tables_dumped = len(dumped_data)

            description = f"🚨 DATA BREACH CONFIRMED 🚨\n\n"
            description += f"SQL injection was exploited to dump actual data from {total_tables_dumped} table(s).\n"
            description += f"Total rows exfiltrated: {total_rows}\n\n"

            # List dumped tables with row counts (limit to first 10)
            description += "Tables dumped:\n"
            for idx, (table_key, data_info) in enumerate(
                list(dumped_data.items())[:10]
            ):
                row_count = data_info.get("row_count", 0)
                columns = data_info.get("columns", [])
                csv_path = data_info.get("csv_path")

                description += f"\n  • {table_key} ({row_count} rows)\n"
                if columns:
                    col_list = ", ".join(columns[:5])
                    if len(columns) > 5:
                        col_list += f" ... and {len(columns) - 5} more columns"
                    description += f"    Columns: {col_list}\n"
                if csv_path:
                    description += f"    CSV: {csv_path}\n"

            if len(dumped_data) > 10:
                remaining = len(dumped_data) - 10
                description += f"\n  ... and {remaining} more table(s) dumped"

            description += "\n\n⚠️ IMMEDIATE ACTION REQUIRED ⚠️\n"
            description += "- Review dumped data for PII/PCI/PHI exposure\n"
            description += "- Notify security team and stakeholders\n"
            description += "- Consider breach notification requirements\n"
            description += "- Patch SQL injection vulnerability immediately\n"
            description += "- Implement WAF/IDS rules\n"
            description += "- Review database access logs"

            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                port=target_port,
                title=f"🚨 SQL Injection Data Breach - {total_rows} Row(s) Exfiltrated",
                finding_type="data_breach",
                severity="critical",
                description=description,
                tool="sqlmap",
                path=parsed.get("target_url"),
            )
            findings_added += 1

            # Extract credentials from dumped data
            credentials_added, extracted_credentials = _extract_credentials_from_dump(
                dumped_data=dumped_data,
                engagement_id=engagement_id,
                host_id=host_id,
                job_id=job.get("id"),
            )

            if credentials_added > 0:
                from souleyez.log_config import get_logger

                logger = get_logger(__name__)
                logger.info(
                    f"SQLMap: Extracted {credentials_added} credentials from dumped tables"
                )

        # Store SQLMap database discoveries
        # Store if we have host_id AND (databases OR tables OR dumped data)
        has_data_to_store = (
            parsed.get("databases") or parsed.get("tables") or parsed.get("dumped_data")
        )

        if host_id and has_data_to_store:
            sdm = SQLMapDataManager()
            dbms_type = parsed.get("dbms", "Unknown")

            # Store databases
            db_ids = {}
            for db_name in parsed.get("databases", []):
                db_id = sdm.add_database(engagement_id, host_id, db_name, dbms_type)
                if db_id:
                    db_ids[db_name] = db_id

            # Store tables
            table_ids = {}
            for db_table_key, table_list in parsed.get("tables", {}).items():
                # db_table_key might be "database" or include more context
                # If we have multiple databases, tables dict might be keyed by database name
                for table_name in table_list:
                    # Try to get database ID from db_ids
                    db_id = db_ids.get(db_table_key)
                    if not db_id and db_ids:
                        # Fallback: use first database if only one exists
                        db_id = list(db_ids.values())[0]

                    if db_id:
                        table_id = sdm.add_table(db_id, table_name)
                        if table_id:
                            full_key = f"{db_table_key}.{table_name}"
                            table_ids[full_key] = table_id

            # Store columns
            for table_key, column_list in parsed.get("columns", {}).items():
                table_id = table_ids.get(table_key)
                if table_id:
                    columns = [{"name": col} for col in column_list]
                    sdm.add_columns(table_id, columns)

            # Store dumped data (extract db/table from key if not already stored)
            for data_key, dump_info in parsed.get("dumped_data", {}).items():
                table_id = table_ids.get(data_key)

                # If table not already stored, extract db.table from key and create them
                if not table_id and "." in data_key:
                    db_name, table_name = data_key.rsplit(".", 1)

                    # Get or create database
                    db_id = db_ids.get(db_name)
                    if not db_id:
                        db_id = sdm.add_database(
                            engagement_id, host_id, db_name, dbms_type
                        )
                        if db_id:
                            db_ids[db_name] = db_id

                    # Create table
                    if db_id:
                        row_count = dump_info.get(
                            "row_count", len(dump_info.get("rows", []))
                        )
                        table_id = sdm.add_table(db_id, table_name, row_count)
                        if table_id:
                            table_ids[data_key] = table_id

                            # Store columns from dumped data
                            if dump_info.get("columns"):
                                columns = [
                                    {"name": col} for col in dump_info["columns"]
                                ]
                                sdm.add_columns(table_id, columns)

                # Store the dumped data
                if table_id:
                    sdm.add_dumped_data(
                        table_id, dump_info.get("rows", []), dump_info.get("csv_path")
                    )

        stats = get_sqli_stats(parsed)

        # Check for sqlmap errors
        sqlmap_error = detect_tool_error(log_content, "sqlmap")

        # Determine status based on results
        if sqlmap_error:
            status = STATUS_ERROR  # Tool failed to connect
        elif stats["sqli_confirmed"] or stats["xss_possible"] or stats["fi_possible"]:
            status = STATUS_DONE  # Found injection vulnerabilities
        else:
            status = STATUS_NO_RESULTS  # No injections found

        return {
            "tool": "sqlmap",
            "status": status,
            "findings_added": findings_added,
            "sqli_confirmed": stats["sqli_confirmed"],
            "xss_possible": stats["xss_possible"],
            "fi_possible": stats["fi_possible"],
            "urls_tested": stats["urls_tested"],
            "databases": parsed.get("databases", []),
            "tables": parsed.get("tables", {}),
            "columns": parsed.get("columns", {}),
            "dumped_tables": stats.get("dumped_tables", 0),
            "dumped_rows": stats.get("dumped_rows", 0),
            "dumped_data": parsed.get("dumped_data", {}),  # Full dump data for display
            # NEW: Add chaining flags
            "dbms": parsed.get("dbms"),  # Database type (sqlite, mysql, etc.)
            "sql_injection_confirmed": parsed.get("sql_injection_confirmed", False),
            "injectable_parameter": parsed.get("injectable_parameter", ""),
            "injectable_url": parsed.get(
                "injectable_url", target
            ),  # FIX: Use correct key
            "injectable_post_data": parsed.get(
                "injectable_post_data", ""
            ),  # For POST injections
            "injectable_method": parsed.get("injectable_method", "GET"),  # GET or POST
            "all_injection_points": parsed.get(
                "all_injection_points", []
            ),  # For fallback
            "databases_enumerated": len(parsed.get("databases", [])) > 0,
            "tables_enumerated": len(parsed.get("tables", {})) > 0,
            "columns_enumerated": len(parsed.get("columns", {})) > 0,
            # NEW: Post-exploitation flags for advanced chaining
            "is_dba": parsed.get("is_dba", False),
            "privileges": parsed.get("privileges", []),
            "current_user": parsed.get("current_user"),
            "file_read_success": parsed.get("file_read_success", False),
            "os_command_success": parsed.get("os_command_success", False),
            # Credentials flag for cross-tool chaining (hydra, etc.)
            "credentials_dumped": credentials_added > 0,
            "credentials_count": credentials_added,
            "credentials": extracted_credentials,  # For direct chaining to hydra
        }
    except Exception as e:
        return {"error": str(e)}


def _extract_credentials_from_dump(
    dumped_data: Dict, engagement_id: int, host_id: int, job_id: int
) -> tuple:
    """
    Extract credentials from SQLMap dumped data.

    Args:
        dumped_data: Dict of {table_key: {rows, columns, row_count, csv_path}}
        engagement_id: Engagement ID
        host_id: Host ID
        job_id: Job ID for tracking

    Returns:
        tuple: (count of credentials added, list of plaintext credential dicts for chaining)
    """
    from souleyez.intelligence.sensitive_tables import is_sensitive_table
    from souleyez.log_config import get_logger
    from souleyez.storage.credentials import CredentialsManager
    from souleyez.storage.hosts import HostManager

    logger = get_logger(__name__)
    cred_manager = CredentialsManager()
    hm = HostManager()

    # Get host IP for credential tracking
    host = hm.get_host(host_id)
    host_ip = host.get("ip_address", "unknown") if host else "unknown"

    credentials_added = 0
    credentials_list = []  # For chaining - only plaintext passwords

    for table_key, data_info in dumped_data.items():
        # Parse table name
        parts = table_key.split(".")
        table_name = parts[-1]
        db_name = parts[0] if len(parts) > 1 else "unknown"

        # Check if this is a credentials table
        is_sensitive, category, priority = is_sensitive_table(table_name)

        if category != "credentials":
            continue  # Only extract from credential tables

        rows = data_info.get("rows", [])
        columns = data_info.get("columns", [])

        if not rows or not columns:
            continue

        # Find username and password columns
        # Strategy: Exact matches first, then substring matches (with ID column blocklist)
        username_col = None
        password_col = None

        # Prioritized patterns: more specific first (username, uname before email)
        username_patterns = [
            "username",
            "uname",
            "user_name",
            "login",
            "account",
            "email",
            "user",
        ]
        password_patterns = [
            "password",
            "passwd",
            "pass",
            "pwd",
            "hash",
            "pwd_hash",
            "password_hash",
        ]

        # Blocklist for columns that are likely foreign keys or IDs
        id_columns = ["id", "user_id", "userid", "account_id", "user_fk"]

        # Step 1: Try EXACT matches first for username (more reliable)
        for pattern in username_patterns:
            for col in columns:
                if col.lower() == pattern:
                    # Skip obvious ID columns even if they match
                    if col.lower() in id_columns:
                        continue
                    username_col = col
                    break
            if username_col:
                break

        # Step 2: Fall back to SUBSTRING matches only if no exact match for username
        if not username_col:
            for pattern in username_patterns:
                for col in columns:
                    if pattern in col.lower():
                        # Skip columns that are likely foreign keys
                        if col.lower() in id_columns:
                            continue
                        username_col = col
                        break
                if username_col:
                    break

        # Step 1: Try EXACT matches first for password (more reliable)
        for pattern in password_patterns:
            for col in columns:
                if col.lower() == pattern:
                    # Skip obvious ID columns even if they match
                    if col.lower() in id_columns:
                        continue
                    password_col = col
                    break
            if password_col:
                break

        # Step 2: Fall back to SUBSTRING matches only if no exact match for password
        if not password_col:
            for pattern in password_patterns:
                for col in columns:
                    if pattern in col.lower():
                        # Skip columns that are likely foreign keys
                        if col.lower() in id_columns:
                            continue
                        password_col = col
                        break
                if password_col:
                    break

        if not username_col or not password_col:
            logger.debug(f"Skipping {table_key}: missing username/password columns")
            continue

        # Extract credentials from rows
        for row in rows:
            username = str(row.get(username_col, "")).strip()
            password = str(row.get(password_col, "")).strip()

            # Handle SQLMap's <blank> placeholder for NULL/empty values
            if username in ["<blank>", "NULL", "None", ""]:
                # Try email as fallback for username
                email = str(row.get("email", "")).strip()
                if email and email not in ["<blank>", "NULL", "None", ""]:
                    username = email
                else:
                    continue  # No valid username found

            if not password or password in ["NULL", "None", "", "<blank>"]:
                continue

            # Detect hash type
            credential_type = _detect_hash_type(password)

            # Add to credentials database
            try:
                cred_manager.add_credential(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    username=username,
                    password=password,
                    credential_type=credential_type,
                    tool="sqlmap",
                    service="web",
                )
                credentials_added += 1
                # Add to credentials list for chaining (only plaintext passwords)
                if credential_type == "password":
                    credentials_list.append(
                        {"username": username, "password": password}
                    )
            except Exception as e:
                logger.warning(f"Failed to add credential {username}: {e}")

    return credentials_added, credentials_list


def _detect_hash_type(password: str) -> str:
    """
    Detect hash type from password string.

    Args:
        password: Password or hash string

    Returns:
        str: Credential type ('password', 'hash:bcrypt', 'hash:md5', etc.)
    """
    import re

    # Check for hash prefixes
    if (
        password.startswith("$2y$")
        or password.startswith("$2a$")
        or password.startswith("$2b$")
    ):
        return "hash:bcrypt"
    elif password.startswith("$1$"):
        return "hash:md5crypt"
    elif password.startswith("$5$"):
        return "hash:sha256crypt"
    elif password.startswith("$6$"):
        return "hash:sha512crypt"
    elif password.startswith("$apr1$"):
        return "hash:apr1"
    elif password.startswith("{SHA}") or password.startswith("{SSHA}"):
        return "hash:ldap"

    # Check hex patterns
    if re.match(r"^[a-fA-F0-9]{32}$", password):
        return "hash:md5"
    elif re.match(r"^[a-fA-F0-9]{40}$", password):
        return "hash:sha1"
    elif re.match(r"^[a-fA-F0-9]{64}$", password):
        return "hash:sha256"
    elif re.match(r"^[a-fA-F0-9]{128}$", password):
        return "hash:sha512"

    # Check for NTLM hash
    if re.match(r"^[a-fA-F0-9]{32}:[a-fA-F0-9]{32}$", password):
        return "hash:ntlm"

    # Likely plaintext if short and no special patterns
    if len(password) < 20 and not re.search(r"[\$\{\}]", password):
        return "password"

    # Default to generic hash
    return "hash"


def parse_msf_auxiliary_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Parse MSF auxiliary module job results."""
    try:
        import re

        from souleyez.parsers.msf_parser import parse_msf_log
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        # Read raw log for connection failure detection
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            raw_content = f.read()

        # Check for connection failures BEFORE parsing
        connection_failure = False
        failure_reason = None
        connection_failure_patterns = [
            (r"Could not connect.*timed?\s*out", "Connection timed out"),
            (r"Connection refused", "Connection refused"),
            (r"Rex::ConnectionTimeout", "Connection timed out"),
            (r"Rex::ConnectionRefused", "Connection refused"),
            (r"No route to host", "No route to host"),
            (r"Network is unreachable", "Network unreachable"),
        ]
        for pattern, reason in connection_failure_patterns:
            if re.search(pattern, raw_content, re.IGNORECASE):
                connection_failure = True
                failure_reason = reason
                break

        # Parse the log
        parsed = parse_msf_log(log_path)

        if "error" in parsed:
            return {"error": parsed["error"]}

        target = job.get("target", "")
        hm = HostManager()
        fm = FindingsManager()
        cm = CredentialsManager()

        services_added = 0
        findings_added = 0
        credentials_added = 0
        finding_summaries = []  # Store summaries for display

        # Get or create host
        host = hm.get_host_by_ip(engagement_id, target)
        if not host:
            host_id = hm.add_host(engagement_id, target)
        else:
            host_id = host["id"]

        # Add services if any
        for svc in parsed.get("services", []):
            hm.add_service(
                host_id,
                {
                    "port": svc.get("port"),
                    "protocol": svc.get("protocol", "tcp"),
                    "state": svc.get("state", "open"),
                    "service": svc.get("service_name"),
                    "version": svc.get("service_version"),
                },
            )
            services_added += 1

        # Add findings
        for finding in parsed.get("findings", []):
            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                title=finding.get("title"),
                finding_type=(
                    "credential"
                    if "credential" in finding.get("title", "").lower()
                    else "security_issue"
                ),
                severity=finding.get("severity", "info"),
                description=finding.get("description"),
                tool="msf_auxiliary",
                port=finding.get("port"),
            )
            findings_added += 1
            # Store summary with details for job display
            finding_summaries.append(
                {
                    "title": finding.get("title"),
                    "severity": finding.get("severity", "info"),
                    "description": finding.get("description", "")[
                        :200
                    ],  # Truncate for display
                }
            )

        # Add credentials if any
        credential_summaries = []
        for cred in parsed.get("credentials", []):
            cm.add_credential(
                engagement_id=engagement_id,
                host_id=host_id,
                service=cred.get("service", "unknown"),
                username=cred.get("username", ""),
                password=cred.get("password", ""),
                credential_type="password",
                tool="msf_auxiliary",
                port=cred.get("port"),
                status=cred.get("status", "valid"),
            )
            credentials_added += 1
            # Store credential summary (mask password for display)
            credential_summaries.append(
                {
                    "username": cred.get("username", ""),
                    "service": cred.get("service", "unknown"),
                    "port": cred.get("port"),
                }
            )

        # Determine status and summary
        has_results = services_added > 0 or findings_added > 0 or credentials_added > 0

        # Check if parser returned a status override (e.g., 'warning' for false positives)
        parser_status = parsed.get("status")
        parser_warning = parsed.get("warning")

        if parser_status == "warning" and parser_warning:
            # Parser detected a warning condition (e.g., false positive detection)
            final_status = STATUS_WARNING
            summary = parser_warning
        elif has_results:
            final_status = STATUS_DONE
            summary = (
                f"Found {findings_added} findings, {credentials_added} credentials"
            )
        elif connection_failure:
            final_status = STATUS_WARNING
            summary = f"Target unreachable: {failure_reason}"
        else:
            final_status = STATUS_NO_RESULTS
            summary = "No results found (target responded but nothing discovered)"

        return {
            "tool": "msf_auxiliary",
            "status": final_status,
            "summary": summary,
            "host": target,
            "services_added": services_added,
            "findings_added": findings_added,
            "credentials_added": credentials_added,
            "findings": finding_summaries,  # Include actual finding details
            "credentials": credential_summaries,  # Include credential info (no passwords)
        }
    except Exception as e:
        return {"error": str(e)}


def parse_msf_exploit_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Parse MSF exploit module job results."""
    try:
        import re

        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        # Read the log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        target = job.get("target", "")
        hm = HostManager()
        fm = FindingsManager()

        findings_added = 0
        exploit_success = False

        # Get or create host
        host = hm.get_host_by_ip(engagement_id, target)
        if not host:
            host_id = hm.add_host(engagement_id, target)
        else:
            host_id = host["id"]

        # Extract exploit name from header or args
        exploit_match = re.search(r"Exploit:\s*(.+)$", content, re.MULTILINE)
        exploit_name = exploit_match.group(1).strip() if exploit_match else "unknown"

        # Check for successful exploitation indicators
        # Common success patterns in MSF output
        # NOTE: These must be specific - avoid patterns that match failure messages
        success_patterns = [
            r"\[\*\]\s+Command shell session \d+ opened",
            r"\[\*\]\s+Meterpreter session \d+ opened",
            r"\[\+\]\s+\d+\.\d+\.\d+\.\d+:\d+\s+-\s+Session \d+ created",
            r"\[\+\].*shell.*opened",
            r"\[\+\].*session.*created",
            # Removed 'Exploit completed.*session' - matched "no session was created" falsely
            # Removed 'Starting the payload handler' - appears before exploit even runs
            # Removed 'Sending stage' - appears before session confirmed
        ]

        for pattern in success_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                exploit_success = True
                break

        # Also check for explicit failure indicators
        failure_patterns = [
            r"Exploit completed, but no session was created",
            r"\[-\].*failed",
            r"\[-\].*Exploit aborted",
            r"\[-\].*not valid",
            r"\[-\].*unreachable",
            r"\[-\].*timed?\s*out",
            r"\[-\].*ConnectionTimeout",
            r"\[-\].*Connection refused",
            r"No session was created",
        ]

        explicit_failure = False
        failure_reason = None
        for pattern in failure_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                explicit_failure = True
                # Extract the failure reason from the match
                failure_reason = match.group(0).strip()
                break

        # Create finding based on result
        if exploit_success:
            # Extract session info if available
            session_match = re.search(
                r"session (\d+) (opened|created)", content, re.IGNORECASE
            )
            session_info = (
                f" (Session {session_match.group(1)})" if session_match else ""
            )

            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                title=f'Exploit Successful: {exploit_name.split("/")[-1]}',
                finding_type="vulnerability",
                severity="critical",
                description=f"Successfully exploited {target} using {exploit_name}.{session_info}\n\nThis confirms the vulnerability is exploitable.",
                tool="msf_exploit",
            )
            findings_added += 1
        elif not explicit_failure:
            # Check for [+] lines that might indicate partial success
            plus_lines = re.findall(r"\[\+\]\s+(.+)", content)
            if plus_lines:
                for line in plus_lines[:3]:  # Limit to first 3 findings
                    fm.add_finding(
                        engagement_id=engagement_id,
                        host_id=host_id,
                        title=f'{exploit_name.split("/")[-1]}: {line[:60]}',
                        finding_type="security_issue",
                        severity="medium",
                        description=f"Exploit output: {line}",
                        tool="msf_exploit",
                    )
                    findings_added += 1

        # Determine final status and summary
        if exploit_success:
            final_status = STATUS_DONE
            summary = f"Exploit successful: {exploit_name.split('/')[-1]}"
        elif explicit_failure:
            final_status = STATUS_WARNING
            # Clean up the failure reason for display
            if failure_reason:
                # Extract meaningful part from MSF output
                if "no session was created" in failure_reason.lower():
                    summary = f"Exploit failed: no session created"
                elif (
                    "unreachable" in failure_reason.lower()
                    or "timed out" in failure_reason.lower()
                ):
                    summary = f"Exploit failed: target unreachable"
                elif "not valid" in failure_reason.lower():
                    summary = f"Exploit failed: invalid configuration"
                elif "connection refused" in failure_reason.lower():
                    summary = f"Exploit failed: connection refused"
                else:
                    summary = f"Exploit failed: {failure_reason[:50]}"
            else:
                summary = f"Exploit failed: {exploit_name.split('/')[-1]}"
        elif findings_added > 0:
            final_status = STATUS_DONE
            summary = f"Exploit output captured ({findings_added} findings)"
        else:
            final_status = STATUS_NO_RESULTS
            summary = f"Exploit completed: no session or findings"

        return {
            "tool": "msf_exploit",
            "status": final_status,
            "summary": summary,
            "host": target,
            "exploit": exploit_name,
            "success": exploit_success,
            "explicit_failure": explicit_failure,
            "findings_added": findings_added,
        }
    except Exception as e:
        return {"error": str(e)}


def parse_smbmap_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse smbmap job results."""
    try:
        from souleyez.parsers.smbmap_parser import extract_findings, parse_smbmap_output
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager
        from souleyez.storage.smb_shares import SMBSharesManager

        # Read the log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

        # Parse smbmap output
        target = job.get("target", "")
        parsed = parse_smbmap_output(log_content, target)

        # Get or create host from target
        hm = HostManager()
        host_id = None

        if parsed["target"]:
            # Try to find existing host
            import re

            is_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", parsed["target"])

            if is_ip:
                host = hm.get_host_by_ip(engagement_id, parsed["target"])
                if host:
                    host_id = host["id"]
                else:
                    # Create host
                    host_id = hm.add_or_update_host(
                        engagement_id, {"ip": parsed["target"], "status": "up"}
                    )

        if not host_id:
            return {"error": "Could not determine target host"}

        # Store SMB shares
        smm = SMBSharesManager()
        shares_added = 0
        files_added = 0

        for share in parsed["shares"]:
            share_id = smm.add_share(host_id, share)
            shares_added += 1

            # Add files if any
            share_files = [
                f for f in parsed["files"] if f.get("share") == share["name"]
            ]
            for file_data in share_files:
                smm.add_file(share_id, file_data)
                files_added += 1

        # Extract and store findings
        fm = FindingsManager()
        findings_added = 0

        findings = extract_findings(parsed)
        for finding in findings:
            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                finding_type="smb_share",
                severity=finding.get("severity"),
                title=finding.get("title"),
                description=finding.get("description"),
                evidence=finding.get("evidence"),
                tool="smbmap",
            )
            findings_added += 1

        # Check for smbmap errors
        smbmap_error = detect_tool_error(log_content, "smbmap")

        # Determine status
        if smbmap_error:
            status = STATUS_ERROR  # Tool failed to connect
        elif shares_added > 0 or findings_added > 0:
            status = STATUS_DONE
        else:
            status = STATUS_NO_RESULTS

        return {
            "tool": "smbmap",
            "host": parsed["target"],
            "connection_status": parsed.get(
                "status", "Unknown"
            ),  # SMB connection status
            "status": status,  # Job status
            "shares_added": shares_added,
            "files_added": files_added,
            "findings_added": findings_added,
        }
    except Exception as e:
        return {"error": str(e)}


def parse_whois_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse WHOIS job results."""
    try:
        from souleyez.parsers.whois_parser import (
            extract_emails,
            map_to_osint_data,
            parse_whois_output,
        )
        from souleyez.storage.osint import OsintManager

        # Read the log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

        # Parse WHOIS output
        target = job.get("target", "")
        parsed = parse_whois_output(log_content, target)

        # Store OSINT data
        om = OsintManager()
        osint_record = map_to_osint_data(parsed, engagement_id)
        om.add_osint_data(
            engagement_id,
            osint_record["data_type"],
            osint_record["target"],  # This is the 'value' parameter
            source=osint_record["source"],
            target=target,
            summary=osint_record["summary"],
            content=osint_record["content"],
            metadata=osint_record["metadata"],
        )

        # Extract emails and add separately for better querying
        emails = extract_emails(parsed)
        emails_added = 0
        if emails:
            emails_added = om.bulk_add_osint_data(
                engagement_id, "email", emails, "whois", target
            )

        return {
            "tool": "whois",
            "status": (
                STATUS_DONE
                if (parsed.get("registrar") or parsed.get("nameservers"))
                else STATUS_NO_RESULTS
            ),
            "domain": parsed.get("domain", target),
            "registrar": parsed.get("registrar"),
            "created": parsed.get("dates", {}).get("created"),
            "expires": parsed.get("dates", {}).get("expires"),
            "emails_found": len(emails),
            "nameservers": len(parsed.get("nameservers", [])),
            "osint_records_added": 1,
            "emails_added": emails_added,
        }
    except Exception as e:
        return {"error": str(e)}


def parse_dnsrecon_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse dnsrecon job results."""
    try:
        from souleyez.parsers.dnsrecon_parser import parse_dnsrecon_output
        from souleyez.storage.hosts import HostManager
        from souleyez.storage.osint import OsintManager

        # Read the log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

        # Parse dnsrecon output
        target = job.get("target", "")
        parsed = parse_dnsrecon_output(log_content, target)

        # Store OSINT data
        om = OsintManager()
        osint_added = 0

        # Add nameservers
        if parsed["nameservers"]:
            count = om.bulk_add_osint_data(
                engagement_id, "nameserver", parsed["nameservers"], "dnsrecon", target
            )
            osint_added += count

        # Add mail servers
        if parsed["mail_servers"]:
            count = om.bulk_add_osint_data(
                engagement_id, "mail_server", parsed["mail_servers"], "dnsrecon", target
            )
            osint_added += count

        # Add TXT records
        if parsed["txt_records"]:
            # Limit TXT record length
            txt_records = [txt[:500] for txt in parsed["txt_records"]]
            count = om.bulk_add_osint_data(
                engagement_id, "txt_record", txt_records, "dnsrecon", target
            )
            osint_added += count

        # Add subdomains/hosts
        if parsed["subdomains"]:
            count = om.bulk_add_osint_data(
                engagement_id, "host", parsed["subdomains"], "dnsrecon", target
            )
            osint_added += count

        # Also add discovered hosts to the hosts table
        hm = HostManager()
        hosts_added = 0

        for host_data in parsed.get("hosts", []):
            try:
                hostname = host_data.get("hostname", "")
                ip = host_data.get("ip", "")

                if ip and hostname:
                    hm.add_or_update_host(
                        engagement_id,
                        {
                            "ip": ip,
                            "hostname": hostname,
                            "status": "up",
                            "notes": f"Discovered by dnsrecon for domain: {target}",
                        },
                    )
                    hosts_added += 1
            except Exception:
                pass  # Skip if invalid

        return {
            "tool": "dnsrecon",
            "domain": parsed.get("target_domain", target),
            "hosts_found": len(parsed.get("hosts", [])),
            "nameservers": len(parsed.get("nameservers", [])),
            "mail_servers": len(parsed.get("mail_servers", [])),
            "txt_records": len(parsed.get("txt_records", [])),
            "subdomains": len(parsed.get("subdomains", [])),
            "osint_records_added": osint_added,
            "hosts_added": hosts_added,
            "status": (
                STATUS_DONE
                if (osint_added > 0 or hosts_added > 0)
                else STATUS_NO_RESULTS
            ),
        }
    except Exception as e:
        return {"error": str(e)}


def parse_wpscan_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse WPScan job results."""
    try:
        from souleyez.parsers.wpscan_parser import parse_wpscan_output
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        # Read the log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

        # Parse WPScan output
        target = job.get("target", "")
        parsed = parse_wpscan_output(log_content, target)

        # Get or create host
        hm = HostManager()
        host = hm.get_host_by_ip(engagement_id, target)
        if not host:
            host = hm.add_or_update_host(engagement_id, {"ip": target, "status": "up"})
        host_id = host["id"]

        # Add findings
        fm = FindingsManager()
        findings_added = 0

        # WordPress version vulnerabilities
        for vuln in parsed.get("findings", []):
            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                title=vuln["title"],
                finding_type="vulnerability",
                severity=vuln["severity"],
                description=vuln["description"],
                tool="wpscan",
                refs=", ".join(vuln.get("references", [])),
            )
            findings_added += 1

        return {
            "tool": "wpscan",
            "status": STATUS_DONE if findings_added > 0 else STATUS_NO_RESULTS,
            "target": target,
            "wp_version": parsed.get("wordpress_version"),
            "plugins_found": len(parsed.get("plugins", [])),
            "themes_found": len(parsed.get("themes", [])),
            "users_found": len(parsed.get("users", [])),
            "findings_added": findings_added,
            "users": parsed.get("users", []),  # For hydra chaining
        }
    except Exception as e:
        return {"error": str(e)}


def parse_hydra_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse Hydra job results."""
    try:
        from souleyez.parsers.hydra_parser import parse_hydra_output
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        # Read the log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

        # Parse Hydra output
        target = job.get("target", "")
        parsed = parse_hydra_output(log_content, target)

        # Add credentials for each host found in results
        cm = CredentialsManager()
        hm = HostManager()
        creds_added = 0
        usernames_added = 0
        hosts_affected = set()

        # Get target host for username-only entries
        target_host = parsed.get("target_host", target)
        # Extract IP from URL if needed
        if "://" in str(target_host):
            from urllib.parse import urlparse

            parsed_url = urlparse(target_host)
            target_host = parsed_url.hostname or target_host

        for cred in parsed.get("credentials", []):
            # Get actual host from credential (Hydra reports it in each success line)
            actual_host = cred.get("host", target_host)

            # Skip if still contains multi-target string
            if not actual_host or " " in str(actual_host):
                continue

            hosts_affected.add(actual_host)

            # Get or create host for this specific IP
            host = hm.get_host_by_ip(engagement_id, actual_host)
            if not host:
                host = hm.add_or_update_host(
                    engagement_id, {"ip": actual_host, "status": "up"}
                )
            host_id = host["id"]

            # Add credential (CredentialsManager should handle duplicate detection)
            cm.add_credential(
                engagement_id=engagement_id,
                host_id=host_id,
                username=cred["username"],
                password=cred["password"],
                service=cred.get("service", parsed.get("service", "unknown")),
                port=cred.get("port", parsed.get("port")),
                credential_type="password",
                tool="hydra",
                status="valid",
            )
            creds_added += 1

        # Handle username-only enumeration results (valid username, password unknown)
        for username in parsed.get("usernames", []):
            # Get target host
            actual_host = target_host
            if not actual_host or " " in str(actual_host):
                continue

            hosts_affected.add(actual_host)

            # Get or create host
            host = hm.get_host_by_ip(engagement_id, actual_host)
            if not host:
                host = hm.add_or_update_host(
                    engagement_id, {"ip": actual_host, "status": "up"}
                )
            host_id = host["id"]

            # Add username-only credential (password unknown)
            cm.add_credential(
                engagement_id=engagement_id,
                host_id=host_id,
                username=username,
                password="",  # Unknown password
                service=parsed.get("service", "http-post-form"),
                port=parsed.get("port"),
                credential_type="username",  # Mark as username-only
                tool="hydra",
                status="username_valid",  # Username validated, password unknown
            )
            usernames_added += 1

        # Create findings for discovered credentials/usernames
        fm = FindingsManager()
        findings_added = 0

        # Finding for valid credentials (high severity)
        if parsed.get("credentials"):
            cred_list = parsed["credentials"]
            usernames_str = ", ".join([c["username"] for c in cred_list])
            service = parsed.get("service", "unknown")
            port = parsed.get("port", "")

            # Get host_id for first affected host
            first_host = list(hosts_affected)[0] if hosts_affected else target_host
            host = hm.get_host_by_ip(engagement_id, first_host)
            finding_host_id = host["id"] if host else None

            fm.add_finding(
                engagement_id=engagement_id,
                title=f"Valid Credentials Found - {service.upper()}",
                finding_type="credential",
                severity="high",
                description=f"Hydra brute-force attack discovered {len(cred_list)} valid credential(s) on {service}:{port}.\n\n"
                f"Affected usernames: {usernames_str}\n\n"
                f"These credentials allow direct access to the service.",
                host_id=finding_host_id,
                tool="hydra",
            )
            findings_added += 1

        # Finding for username enumeration (medium severity)
        if parsed.get("usernames"):
            username_list = parsed["usernames"]
            usernames_str = ", ".join(username_list)
            service = parsed.get("service", "http-post-form")
            port = parsed.get("port", 80)

            # Get host_id for finding
            first_host = list(hosts_affected)[0] if hosts_affected else target_host
            host = hm.get_host_by_ip(engagement_id, first_host)
            finding_host_id = host["id"] if host else None

            fm.add_finding(
                engagement_id=engagement_id,
                title="Username Enumeration - Valid Usernames Discovered",
                finding_type="enumeration",
                severity="medium",
                description=f"Username enumeration via {service}:{port} revealed {len(username_list)} valid username(s).\n\n"
                f"Valid usernames: {usernames_str}\n\n"
                f"The application differentiates between valid and invalid usernames in error messages, "
                f"allowing attackers to enumerate valid accounts. These usernames can be targeted for "
                f"password attacks.",
                host_id=finding_host_id,
                tool="hydra",
            )
            findings_added += 1

        # Check for hydra errors
        hydra_error = detect_tool_error(log_content, "hydra")
        summary = None

        # Determine status based on results
        if hydra_error:
            hydra_error_lower = hydra_error.lower()
            # Network/connectivity errors - service couldn't be reached
            # These are warnings, not failures: the job ran, just couldn't connect
            # STATUS_WARNING distinguishes from STATUS_NO_RESULTS (service responded, no creds found)
            if "connection refused" in hydra_error_lower:
                status = STATUS_WARNING
                summary = "Target unreachable (connection refused)"
            elif "timed out" in hydra_error_lower or "timeout" in hydra_error_lower:
                status = STATUS_WARNING
                summary = "Target unreachable (connection timed out)"
            elif (
                "could not connect" in hydra_error_lower
                or "can not connect" in hydra_error_lower
            ):
                status = STATUS_WARNING
                summary = "Target unreachable (could not connect)"
            elif "no route to host" in hydra_error_lower:
                status = STATUS_WARNING
                summary = "Target unreachable (no route to host)"
            elif "network is unreachable" in hydra_error_lower:
                status = STATUS_WARNING
                summary = "Target unreachable (network unreachable)"
            else:
                status = STATUS_ERROR  # Actual tool failure
                summary = f"Error: {hydra_error}"
        elif len(parsed.get("credentials", [])) > 0:
            status = STATUS_DONE  # Found valid credentials
            cred_count = len(parsed.get("credentials", []))
            summary = (
                f"Found {cred_count} valid credential{'s' if cred_count != 1 else ''}"
            )
        elif len(parsed.get("usernames", [])) > 0:
            status = (
                STATUS_DONE  # Found valid usernames (partial success is still a result)
            )
            user_count = len(parsed.get("usernames", []))
            summary = (
                f"Found {user_count} valid username{'s' if user_count != 1 else ''}"
            )
        else:
            status = STATUS_NO_RESULTS  # No valid credentials or usernames found
            summary = "No valid credentials found (target responded)"

        result = {
            "tool": "hydra",
            "status": status,
            "target": target,
            "hosts_affected": list(hosts_affected),
            "service": parsed.get("service"),
            "port": parsed.get("port"),
            "credentials_found": len(parsed.get("credentials", [])),
            "credentials_added": creds_added,
            "usernames_found": len(parsed.get("usernames", [])),
            "usernames": parsed.get(
                "usernames", []
            ),  # Include actual list for auto-chaining
            "usernames_added": usernames_added,
            "findings_added": findings_added,
            "attempts": parsed.get("attempts", 0),
        }
        if summary:
            result["summary"] = summary
        return result
    except Exception as e:
        return {"error": str(e)}


def parse_nuclei_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse nuclei job results."""
    try:
        from souleyez.parsers.nuclei_parser import parse_nuclei
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        target = job.get("target", "")
        parsed = parse_nuclei(log_path, target)

        if "error" in parsed:
            return parsed

        # Get or create host
        hm = HostManager()
        host_id = None

        # Extract host from target URL
        from urllib.parse import urlparse

        parsed_url = urlparse(target)
        target_host = parsed_url.hostname or target

        if target_host:
            host_id = hm.add_or_update_host(
                engagement_id, {"ip": target_host, "status": "up"}
            )

        # Store findings
        fm = FindingsManager()
        findings_added = 0

        for finding in parsed.get("findings", []):
            severity = finding.get("severity", "info")

            # Map nuclei severity to souleyez severity (1-5)
            severity_map = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}

            title = finding.get("name", "Unknown Vulnerability")
            description = finding.get("description", "")

            # Add CVE and reference info to description
            if finding.get("cve_id"):
                description += f"\n\nCVE: {finding['cve_id']}"
            if finding.get("cvss_score"):
                description += f"\nCVSS Score: {finding['cvss_score']}"
            if finding.get("references"):
                description += f"\n\nReferences:\n" + "\n".join(finding["references"])

            # Add deduplication attribution if this scan covered multiple IPs
            metadata = job.get("metadata", {})
            associated_ips = metadata.get("associated_ips", [])
            if associated_ips and len(associated_ips) > 1:
                representative_ip = metadata.get("representative_ip", target_host)
                domain = metadata.get("domain_context", "")
                description += f"\n\n[Web Target Deduplication] This finding was discovered on {representative_ip}"
                description += (
                    f" (representative IP for {len(associated_ips)} IPs serving"
                )
                if domain:
                    description += f" {domain}"
                description += f"). All affected IPs: {', '.join(associated_ips)}"

            # Build evidence with matched_at, cve_id, and template_id
            evidence = f"Template: {finding.get('template_id', 'unknown')}"
            if finding.get("matched_at"):
                evidence += f"\nMatched at: {finding.get('matched_at')}"
            if finding.get("cve_id"):
                evidence += f"\nCVE: {finding.get('cve_id')}"

            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                title=title,
                description=description,
                severity=severity,  # Use string severity from nuclei
                finding_type="vulnerability",
                tool="nuclei",
                evidence=evidence,
            )
            findings_added += 1

        # Check for nuclei errors
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()
        nuclei_error = detect_tool_error(log_content, "nuclei")

        # Determine status based on results
        if nuclei_error:
            status = STATUS_ERROR  # Tool failed to connect
        elif parsed.get("findings_count", 0) > 0:
            status = STATUS_DONE  # Found vulnerabilities
        else:
            status = STATUS_NO_RESULTS  # No vulnerabilities found

        return {
            "tool": "nuclei",
            "status": status,
            "target": target,
            "findings_count": parsed.get("findings_count", 0),
            "findings_added": findings_added,
            "critical": parsed.get("critical", 0),
            "high": parsed.get("high", 0),
            "medium": parsed.get("medium", 0),
            "low": parsed.get("low", 0),
            "info": parsed.get("info", 0),
        }
    except Exception as e:
        logger.error(
            "parse_nuclei_job exception",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "target": job.get("target", ""),
                "job_id": job.get("id"),
            },
        )
        return {"error": str(e)}


def parse_enum4linux_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse enum4linux job results."""
    try:
        from souleyez.parsers.enum4linux_parser import (
            categorize_share,
            get_smb_stats,
            parse_enum4linux_output,
        )
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

        target = job.get("target", "")
        parsed = parse_enum4linux_output(log_content, target)

        hm = HostManager()
        host_id = None

        if parsed["target"]:
            import re

            is_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", parsed["target"])
            if is_ip:
                host = hm.get_host_by_ip(engagement_id, parsed["target"])
                if host:
                    host_id = host["id"]
                else:
                    host_id = hm.add_or_update_host(
                        engagement_id, {"ip": parsed["target"], "status": "up"}
                    )

        from souleyez.storage.credentials import CredentialsManager

        cm = CredentialsManager()
        credentials_added = 0

        for username in parsed["users"]:
            cm.add_credential(
                engagement_id=engagement_id,
                host_id=host_id,
                username=username,
                password="",
                credential_type="smb",
                service="smb",
                port=445,
                tool="enum4linux",
            )
            credentials_added += 1

        fm = FindingsManager()
        findings_added = 0

        for share in parsed["shares"]:
            category = categorize_share(share)
            if category == "open":
                severity = "high"
            elif category == "readable":
                severity = "medium"
            elif category == "restricted":
                severity = "low"
            else:
                severity = "info"

            share_name = share["name"]
            share_type = share.get("type", "Unknown")
            mapping = share.get("mapping", "N/A")

            if mapping == "OK":
                listing = share.get("listing", "N/A")
                writing = share.get("writing", "N/A")
                access_desc = f"Mapping={mapping}, Listing={listing}, Writing={writing}"
            else:
                access_desc = f"Access denied (Mapping={mapping})"

            title = f"SMB Share: {share_name} ({share_type})"
            description = f"Share: {share_name}\nType: {share_type}\nComment: {share.get('comment', 'N/A')}\nAccess: {access_desc}"

            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                title=title,
                finding_type="smb_share",
                severity=severity,
                description=description,
                tool="enum4linux",
                port=445,
            )
            findings_added += 1

        stats = get_smb_stats(parsed)

        # Extract domains for auto-chaining
        # Filter out common workgroup names - these aren't AD domains
        domains = []
        workgroup = stats.get("workgroup")
        common_workgroups = {"WORKGROUP", "MYGROUP", "MSHOME", "HOME"}
        if workgroup and workgroup.upper() not in common_workgroups:
            domains.append({"domain": workgroup, "ip": parsed["target"]})

        # Check for enum4linux errors
        enum4linux_error = detect_tool_error(log_content, "enum4linux")

        # Determine status: done if we found any results (shares, users, or findings)
        # enum4linux often has partial failures (some queries fail, others succeed)
        has_results = (
            findings_added > 0
            or credentials_added > 0
            or len(parsed["users"]) > 0
            or stats["total_shares"] > 0
        )

        # Check for positive indicators even without findings
        has_positive_output = "[+]" in log_content

        # Prioritize results over errors - partial success is still success
        if has_results:
            status = STATUS_DONE
        elif has_positive_output:
            # Got some positive output but no parsed findings - still useful
            status = STATUS_DONE
        elif enum4linux_error:
            status = STATUS_WARNING  # Partial failure, not total error
        else:
            status = STATUS_NO_RESULTS

        return {
            "tool": "enum4linux",
            "status": status,
            "findings_added": findings_added,
            "credentials_added": credentials_added,
            "users_found": len(parsed["users"]),
            "shares_found": stats["total_shares"],
            "accessible_shares": stats["accessible_shares"],
            "writable_shares": stats["writable_shares"],
            "workgroup": stats.get("workgroup"),
            "domains": domains,  # For auto-chaining to GetNPUsers and other AD tools
        }
    except Exception as e:
        return {"error": str(e)}


def parse_crackmapexec_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse CrackMapExec job results."""
    try:
        from souleyez.parsers.crackmapexec_parser import parse_crackmapexec
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.hosts import HostManager

        target = job.get("target", "")
        parsed = parse_crackmapexec(log_path, target)

        if "error" in parsed:
            return parsed

        hm = HostManager()
        cm = CredentialsManager()

        # Store hosts
        for host in parsed["findings"].get("hosts", []):
            hm.add_or_update_host(
                engagement_id,
                {
                    "ip": host["ip"],
                    "hostname": host.get("hostname"),
                    "domain": host.get("domain"),
                    "os": host.get("os"),
                    "status": "up",
                },
            )

        # Store credentials
        creds_added = 0
        for cred in parsed["findings"].get("credentials", []):
            host = hm.get_host_by_ip(engagement_id, target)
            if host:
                cm.add_credential(
                    engagement_id=engagement_id,
                    host_id=host["id"],
                    username=cred["username"],
                    password=cred["password"],
                    service="smb",
                    credential_type="password",
                    tool="crackmapexec",
                    status="valid",
                )
                creds_added += 1

        return {
            "tool": "crackmapexec",
            "status": (
                STATUS_DONE
                if (len(parsed["findings"].get("hosts", [])) > 0 or creds_added > 0)
                else STATUS_NO_RESULTS
            ),
            "target": target,
            "hosts_found": parsed.get("hosts_found", 0),
            "shares_found": parsed.get("shares_found", 0),
            "users_found": parsed.get("users_found", 0),
            "credentials_added": creds_added,
            "vulnerabilities_found": parsed.get("vulnerabilities_found", 0),
            "domains": parsed.get(
                "domains", []
            ),  # For auto-chaining to GetNPUsers and other AD tools
        }
    except Exception as e:
        return {"error": str(e)}


def parse_ffuf_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse ffuf job results."""
    try:
        from souleyez.parsers.ffuf_parser import parse_ffuf
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        target = job.get("target", "")
        parsed = parse_ffuf(log_path, target)

        if "error" in parsed:
            return parsed

        # Extract base target for host tracking
        from urllib.parse import urlparse

        parsed_url = urlparse(target.replace("FUZZ", ""))
        target_host = parsed_url.hostname or target

        hm = HostManager()
        host_id = None

        if target_host:
            host_id = hm.add_or_update_host(
                engagement_id, {"ip": target_host, "status": "up"}
            )

        # Store web paths
        from souleyez.storage.web_paths import WebPathsManager

        wpm = WebPathsManager()
        paths_added = 0
        created_findings = []

        if host_id and parsed.get("paths"):
            paths_added = wpm.bulk_add_web_paths(host_id, parsed["paths"])

            # Check for sensitive paths and create findings (same as gobuster)
            created_findings = _create_findings_for_sensitive_paths(
                engagement_id, host_id, parsed["paths"], job
            )

        # Check for ffuf errors
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()
        ffuf_error = detect_tool_error(log_content, "ffuf")

        # Determine status
        if ffuf_error:
            status = STATUS_ERROR  # Tool failed to connect
        elif parsed.get("results_found", 0) > 0:
            status = STATUS_DONE
        else:
            status = STATUS_NO_RESULTS

        return {
            "tool": "ffuf",
            "status": status,
            "target": target,
            "results_found": parsed.get("results_found", 0),
            "paths_added": paths_added,
            "findings_added": len(created_findings),
            "method": parsed.get("method"),
            "parameters_found": parsed.get("paths", []),  # Enable ffuf → sqlmap chain
        }
    except Exception as e:
        return {"error": str(e)}


def parse_searchsploit_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse searchsploit job results."""
    try:
        from souleyez.parsers.searchsploit_parser import parse_searchsploit
        from souleyez.storage.exploits import add_exploit

        target = job.get("target", "")

        # Get service context if search was triggered from discovered services
        service_context = job.get("metadata", {}).get("service_context", {})
        service_id = service_context.get("service_id") if service_context else None

        # Parse the log file
        parsed = parse_searchsploit(log_path, target)

        if "error" in parsed:
            return {"error": parsed["error"]}

        # Store exploits in database
        exploits_added = 0

        for exploit in parsed.get("exploits", []):
            add_exploit(
                engagement_id=engagement_id,
                edb_id=exploit.get("edb_id", ""),
                title=exploit.get("title", ""),
                platform=exploit.get("platform", ""),
                exploit_type=exploit.get("type", ""),
                url=exploit.get("url", ""),
                date_published=exploit.get("date", ""),
                search_term=target,
                service_id=service_id,  # Link to service if available
            )
            exploits_added += 1

        return {
            "tool": "searchsploit",
            "status": STATUS_DONE if exploits_added > 0 else STATUS_NO_RESULTS,
            "target": target,
            "exploit_count": parsed.get("exploit_count", 0),
            "exploits_added": exploits_added,
        }
    except Exception as e:
        return {"error": str(e)}


def parse_impacket_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse Impacket tool job results."""
    try:
        from souleyez.parsers.impacket_parser import parse_impacket
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.hosts import HostManager

        target = job.get("target", "")
        tool = job.get("tool", "")

        # Parse the log file
        parsed = parse_impacket(log_path, target, tool)

        if "error" in parsed:
            return parsed

        # Get or create host
        hm = HostManager()
        host_id = None

        # Extract IP from target (may be in format DOMAIN/user:pass@IP)
        import re

        ip_match = re.search(r"@?(\d+\.\d+\.\d+\.\d+)", target)
        if ip_match:
            host_ip = ip_match.group(1)
            host_id = hm.add_or_update_host(
                engagement_id, {"ip": host_ip, "status": "up"}
            )

        cm = CredentialsManager()
        creds_added = 0
        hashes_added = 0

        # Store credentials from secretsdump
        if "secretsdump" in tool.lower():
            # Store plaintext credentials
            for cred in parsed.get("credentials", []):
                cm.add_credential(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    username=cred.get("username"),
                    password=cred.get("password"),
                    service="windows",
                    status="valid",
                    credential_type="password",
                    tool=tool,
                    domain=cred.get("domain"),
                )
                creds_added += 1

            # Store NTLM hashes
            for hash_data in parsed.get("hashes", []):
                cm.add_credential(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    username=hash_data.get("username"),
                    password=hash_data.get("nt_hash"),
                    service="windows",
                    status="valid",
                    credential_type="hash",
                    tool=tool,
                    notes=f"RID: {hash_data.get('rid')}, LM: {hash_data.get('lm_hash')}",
                )
                hashes_added += 1

        # Store AS-REP hashes from GetNPUsers
        elif "getnpusers" in tool.lower():
            for hash_data in parsed.get("hashes", []):
                cm.add_credential(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    username=hash_data.get("username"),
                    password=hash_data.get("hash"),
                    service="kerberos",
                    status="untested",
                    credential_type="asrep_hash",
                    tool=tool,
                    domain=hash_data.get("domain"),
                    notes="Crackable with hashcat mode 18200",
                )
                hashes_added += 1

        # For psexec and smbclient, just record success
        success = parsed.get("success", False)

        result = {
            "tool": tool,
            "target": target,
            "credentials_added": creds_added,
            "hashes_added": hashes_added,
            "success": success,
            "status": (
                STATUS_DONE
                if (creds_added > 0 or hashes_added > 0 or success)
                else STATUS_NO_RESULTS
            ),
            **{
                k: v
                for k, v in parsed.items()
                if k not in ["credentials", "hashes", "tickets"]
            },
        }

        # Include hashes for chaining
        if "getnpusers" in tool.lower():
            result["asrep_hashes"] = parsed.get("hashes", [])  # For chaining to hashcat
        elif "secretsdump" in tool.lower():
            result["hashes"] = parsed.get("hashes", [])  # For chaining to hashcat

        return result
    except Exception as e:
        return {"error": str(e)}


def parse_responder_job(engagement_id: int, log_path: str, job: Dict) -> Dict:
    """Parse and store Responder results."""
    try:
        from souleyez.parsers.responder_parser import (
            parse_responder,
            store_responder_results,
        )

        target = job.get("target", "")
        parsed = parse_responder(log_path, target)

        job_id = job.get("id")
        store_responder_results(parsed, engagement_id, job_id)

        return {
            "tool": "responder",
            "status": (
                STATUS_DONE
                if parsed.get("credentials_captured", 0) > 0
                else STATUS_NO_RESULTS
            ),
            "interface": target,
            "credentials_captured": parsed.get("credentials_captured", 0),
            "summary": parsed.get("summary", "No results"),
        }
    except Exception as e:
        return {"error": str(e)}


def parse_bloodhound_job(engagement_id: int, log_path: str, job: Dict) -> Dict:
    """Parse and store Bloodhound results."""
    try:
        from souleyez.parsers.bloodhound_parser import (
            parse_bloodhound,
            store_bloodhound_results,
        )

        target = job.get("target", "")
        parsed = parse_bloodhound(log_path, target)

        job_id = job.get("id")
        store_bloodhound_results(parsed, engagement_id, job_id)

        stats = parsed.get("statistics", {})
        total_objects = (
            stats.get("users", 0) + stats.get("computers", 0) + stats.get("groups", 0)
        )
        return {
            "tool": "bloodhound",
            "status": STATUS_DONE if total_objects > 0 else STATUS_NO_RESULTS,
            "target": target,
            "users": stats.get("users", 0),
            "computers": stats.get("computers", 0),
            "groups": stats.get("groups", 0),
            "collection_path": parsed.get("collection_path", ""),
            "summary": parsed.get("summary", "No results"),
        }
    except Exception as e:
        return {"error": str(e)}


def reparse_all_sqlmap_jobs() -> Dict[str, Any]:
    """
    Re-parse all completed sqlmap jobs to refresh their parse_results.

    Returns:
        Dict with counts: {'reparsed': N, 'failed': N, 'skipped': N}
    """
    from souleyez.engine.background import _read_jobs, _update_job

    jobs = _read_jobs()
    stats = {"reparsed": 0, "failed": 0, "skipped": 0}

    for job in jobs:
        if job.get("tool", "").lower() != "sqlmap":
            continue
        if job.get("status") not in ["done", "no_results"]:
            stats["skipped"] += 1
            continue

        try:
            parse_result = handle_job_result(job)
            if parse_result:
                _update_job(job["id"], parse_result=parse_result)
                stats["reparsed"] += 1
            else:
                stats["skipped"] += 1
        except Exception as e:
            logger.warning(f"Failed to reparse job {job['id']}: {e}")
            stats["failed"] += 1

    return stats


def parse_nikto_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse nikto web server scanner results."""
    try:
        from souleyez.parsers.nikto_parser import (
            generate_next_steps,
            parse_nikto_output,
        )
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        target = job.get("target", "")

        # Read log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            output = f.read()

        parsed = parse_nikto_output(output, target)

        # Get or create host
        hm = HostManager()
        host_id = None

        # Use target IP from parsed output, or extract from target
        target_ip = parsed.get("target_ip") or parsed.get("target_hostname")
        if not target_ip:
            from urllib.parse import urlparse

            parsed_url = urlparse(target)
            target_ip = parsed_url.hostname or target

        if target_ip:
            host_id = hm.add_or_update_host(
                engagement_id,
                {
                    "ip": target_ip,
                    "hostname": parsed.get("target_hostname", ""),
                    "status": "up",
                },
            )

        # Store findings
        fm = FindingsManager()
        findings_added = 0

        for finding in parsed.get("findings", []):
            severity = finding.get("severity", "info")

            # Build title from OSVDB or path + description
            osvdb = finding.get("osvdb")
            path = finding.get("path", "/")
            desc = finding.get("description", "")

            if osvdb:
                title = f"Nikto: {osvdb} - {path}"
            elif path:
                title = f"Nikto: {path} - {desc[:50]}{'...' if len(desc) > 50 else ''}"
            else:
                title = f"Nikto Finding: {desc[:60]}{'...' if len(desc) > 60 else ''}"

            # Build description with server info
            description = desc
            if parsed.get("server"):
                description += f"\n\nServer: {parsed['server']}"
            if osvdb:
                description += f"\n\nReference: {osvdb}"
            if path:
                description += f"\nPath: {path}"

            # Build evidence
            evidence = f"Detected by Nikto web scanner"
            if path:
                evidence += f"\nPath: {path}"
            if osvdb:
                evidence += f"\nOSVDB: {osvdb}"

            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                title=title,
                description=description,
                severity=severity,
                finding_type="misconfiguration",
                tool="nikto",
                evidence=evidence,
            )
            findings_added += 1

        # Generate next steps for manual follow-up
        next_steps = generate_next_steps(parsed, target)

        # Check for nikto errors
        nikto_error = detect_tool_error(output, "nikto")

        # Determine status based on results
        if nikto_error:
            status = STATUS_ERROR  # Tool failed to connect
        elif findings_added > 0:
            status = STATUS_DONE
        else:
            status = STATUS_NO_RESULTS

        return {
            "tool": "nikto",
            "status": status,
            "target": target,
            "target_ip": parsed.get("target_ip", ""),
            "server": parsed.get("server", ""),
            "findings_count": parsed["stats"]["total"],
            "findings_added": findings_added,
            "by_severity": parsed["stats"]["by_severity"],
            "next_steps": next_steps,  # Suggested manual follow-up actions
        }

    except Exception as e:
        logger.error(f"Error parsing nikto job: {e}")
        return {"error": str(e)}


def parse_http_fingerprint_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Parse HTTP fingerprint results.

    Returns fingerprint data for use in auto-chaining context.
    This enables downstream tools (nikto, nuclei, etc.) to make smarter decisions
    based on detected WAF, CDN, or managed hosting platform.
    """
    try:
        from urllib.parse import urlparse

        from souleyez.parsers.http_fingerprint_parser import (
            build_fingerprint_context,
            generate_next_steps,
            get_tool_recommendations,
            parse_http_fingerprint_output,
        )
        from souleyez.storage.hosts import HostManager

        target = job.get("target", "")

        # Read log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            output = f.read()

        parsed = parse_http_fingerprint_output(output, target)

        # Extract host from target URL
        parsed_url = urlparse(target)
        target_host = parsed_url.hostname or target

        # Update host with fingerprint info if we have useful data
        if target_host and (parsed.get("server") or parsed.get("managed_hosting")):
            hm = HostManager()
            host_data = {"ip": target_host, "status": "up"}
            # Store server info in notes or a dedicated field
            # For now, we just ensure the host exists
            hm.add_or_update_host(engagement_id, host_data)

        # Build fingerprint context for chaining
        fingerprint_context = build_fingerprint_context(parsed)

        # Get tool recommendations
        recommendations = get_tool_recommendations(parsed)

        # Generate next steps for manual follow-up
        next_steps = generate_next_steps(parsed, target)

        # Determine status and build summary
        summary_parts = []

        if parsed.get("error"):
            # Network errors (connection refused, timeout, etc.) are findings about the target,
            # not job failures. The job ran successfully - it just couldn't reach the target.
            status = STATUS_WARNING
            summary_parts.append(f"Unreachable: {parsed.get('error')}")
        elif (
            parsed.get("managed_hosting")
            or parsed.get("waf")
            or parsed.get("cdn")
            or parsed.get("cms_detected")
            or parsed.get("admin_panels")
            or parsed.get("api_endpoints")
        ):
            status = STATUS_DONE  # Found useful info
        elif parsed.get("server"):
            status = STATUS_DONE
        else:
            status = STATUS_NO_RESULTS

        # Build summary for successful scans
        if not parsed.get("error"):
            if parsed.get("server"):
                summary_parts.append(f"Server: {parsed.get('server')}")
            if parsed.get("managed_hosting"):
                summary_parts.append(f"Platform: {parsed.get('managed_hosting')}")
            if parsed.get("waf"):
                summary_parts.append(f"WAF: {', '.join(parsed.get('waf', []))}")
            if parsed.get("cdn"):
                summary_parts.append(f"CDN: {', '.join(parsed.get('cdn', []))}")
            if parsed.get("technologies"):
                techs = parsed.get("technologies", [])
                if len(techs) <= 3:
                    summary_parts.append(f"Tech: {', '.join(techs)}")
                else:
                    summary_parts.append(
                        f"Tech: {', '.join(techs[:3])} +{len(techs)-3} more"
                    )
            if parsed.get("cms_detected"):
                cms = parsed.get("cms_detected", {})
                cms_name = cms.get("name", "Unknown CMS")
                summary_parts.append(f"CMS: {cms_name}")
            if parsed.get("admin_panels"):
                panel_count = len(parsed.get("admin_panels", []))
                summary_parts.append(f"Admin: {panel_count} panel(s)")
            if parsed.get("api_endpoints"):
                api_count = len(parsed.get("api_endpoints", []))
                summary_parts.append(f"API: {api_count} endpoint(s)")

        summary = (
            " | ".join(summary_parts)
            if summary_parts
            else "No fingerprint data detected"
        )

        # Get effective URL from smart protocol detection (HTTPS upgrade)
        effective_url = parsed.get("effective_url") or target
        protocol_detection = parsed.get("protocol_detection")

        # If protocol was upgraded, update the service info to reflect actual protocol
        effective_parsed = urlparse(effective_url)
        effective_scheme = effective_parsed.scheme or "http"
        effective_port = effective_parsed.port or (
            443 if effective_scheme == "https" else 80
        )

        return {
            "tool": "http_fingerprint",
            "status": status,
            "target": target,
            "target_host": target_host,
            "summary": summary,
            # Core fingerprint data
            "server": parsed.get("server"),
            "managed_hosting": parsed.get("managed_hosting"),
            "waf": parsed.get("waf", []),
            "cdn": parsed.get("cdn", []),
            "technologies": parsed.get("technologies", []),
            "status_code": parsed.get("status_code"),
            # Robots.txt and sitemap paths for chaining
            "robots_paths": parsed.get("robots_paths", []),
            "sitemap_paths": parsed.get("sitemap_paths", []),
            # CMS, admin panels, and API detection for chaining
            "cms_detected": parsed.get("cms_detected"),
            "admin_panels": parsed.get("admin_panels", []),
            "api_endpoints": parsed.get("api_endpoints", []),
            # Smart protocol detection - pass effective URL to downstream chains
            "effective_url": effective_url,
            "protocol_detection": protocol_detection,
            # For auto-chaining context
            "http_fingerprint": fingerprint_context.get("http_fingerprint", {}),
            "recommendations": recommendations,
            # Suggested next steps for manual follow-up
            "next_steps": next_steps,
            # Pass through for downstream chains (use effective protocol)
            "services": [
                {
                    "ip": target_host,
                    "port": effective_port,
                    "service_name": effective_scheme,
                    "product": parsed.get("server", ""),
                }
            ],
        }

    except Exception as e:
        logger.error(f"Error parsing http_fingerprint job: {e}")
        return {"error": str(e)}


def parse_dalfox_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse Dalfox XSS scanner results."""
    try:
        from souleyez.parsers.dalfox_parser import parse_dalfox_output
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        target = job.get("target", "")

        # Read log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            output = f.read()

        parsed = parse_dalfox_output(output, target)

        # Get or create host
        hm = HostManager()
        host_id = None

        # Extract host from target URL
        from urllib.parse import urlparse

        parsed_url = urlparse(target)
        target_host = parsed_url.hostname or target

        if target_host:
            host_id = hm.add_or_update_host(
                engagement_id, {"ip": target_host, "status": "up"}
            )

        # Store findings
        fm = FindingsManager()
        findings_added = 0

        for vuln in parsed.get("vulnerabilities", []):
            xss_type = vuln.get("type", "XSS")
            url = vuln.get("url", target)
            param = vuln.get("parameter", "")
            payload = vuln.get("payload", "")

            title = f"XSS Vulnerability ({xss_type})"
            if param:
                title += f" in parameter '{param}'"

            description = f"Cross-Site Scripting ({xss_type}) vulnerability detected."
            description += f"\n\nVulnerable URL: {url}"
            if param:
                description += f"\nVulnerable Parameter: {param}"
            if payload:
                description += f"\n\nPayload:\n```\n{payload}\n```"

            # XSS is typically high severity
            severity = (
                "high" if xss_type in ["Reflected", "Stored", "DOM"] else "medium"
            )

            evidence = f"Detected by Dalfox XSS scanner"
            evidence += f"\nType: {xss_type}"
            if payload:
                evidence += f"\nPayload: {payload[:200]}"

            fm.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                title=title,
                description=description,
                severity=severity,
                finding_type="vulnerability",
                tool="dalfox",
                evidence=evidence,
            )
            findings_added += 1

        # Determine status
        if findings_added > 0:
            status = STATUS_DONE
        else:
            status = STATUS_NO_RESULTS

        return {
            "tool": "dalfox",
            "status": status,
            "target": target,
            "vulnerabilities_count": len(parsed.get("vulnerabilities", [])),
            "findings_added": findings_added,
        }

    except Exception as e:
        logger.error(f"Error parsing dalfox job: {e}")
        return {"error": str(e)}


def parse_hashcat_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse hashcat job results and extract cracked passwords."""
    try:
        from souleyez.parsers.hashcat_parser import (
            map_to_credentials,
            parse_hashcat_output,
        )
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.findings import FindingsManager

        # Read the log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

        # Parse hashcat output
        hash_file = job.get("metadata", {}).get("hash_file", "")
        parsed = parse_hashcat_output(log_content, hash_file)

        # Store credentials
        cm = CredentialsManager()
        creds_added = 0
        cracked_summary = []

        for cracked in parsed.get("cracked", []):
            try:
                # Extract username if available (Kerberos hashes include it)
                username = cracked.get("username", "")
                hash_type = cracked.get("hash_type", "unknown")
                password = cracked["password"]

                # Determine service based on hash type
                if hash_type == "kerberos":
                    service = "kerberos"
                else:
                    service = "cracked_hash"

                cm.add_credential(
                    engagement_id=engagement_id,
                    host_id=None,  # Hash cracking typically not tied to a specific host
                    username=username,
                    password=password,
                    service=service,
                    credential_type="password",
                    tool="hashcat",
                    status="cracked",
                    notes=f"Cracked {hash_type} hash: {cracked['hash'][:50]}...",
                )
                creds_added += 1
                if username:
                    cracked_summary.append(f"{username}:{password}")
                else:
                    cracked_summary.append(f"*:{password}")
                logger.info(f"Hashcat cracked: {username or '?'}:{password}")
            except Exception as e:
                logger.debug(f"Error adding credential: {e}")
                pass  # Skip duplicates

        # Create finding if we cracked passwords
        fm = FindingsManager()
        findings_added = 0

        if parsed.get("cracked"):
            # Build description with cracked passwords summary
            desc_lines = [
                f"Hashcat successfully cracked {len(parsed['cracked'])} password hash(es).",
                "",
                f"Status: {parsed['stats'].get('status', 'unknown')}",
                f"Cracked: {parsed['stats'].get('cracked_count', len(parsed['cracked']))}",
                "",
                "Cracked credentials:",
            ]
            for cred in cracked_summary[:10]:  # Show first 10
                desc_lines.append(f"  - {cred}")
            if len(cracked_summary) > 10:
                desc_lines.append(f"  ... and {len(cracked_summary) - 10} more")

            fm.add_finding(
                engagement_id=engagement_id,
                title=f"Password Hashes Cracked - {len(parsed['cracked'])} passwords recovered",
                finding_type="credential",
                severity="high",
                description="\n".join(desc_lines),
                tool="hashcat",
            )
            findings_added += 1

        # Determine status based on cracked passwords
        hashcat_status = parsed["stats"].get("status", "unknown")
        potfile_hits = parsed["stats"].get("potfile_hits", 0)

        if creds_added > 0 or hashcat_status == "cracked":
            status = STATUS_DONE
        elif hashcat_status == "already_cracked" or potfile_hits > 0:
            # Hashes were already cracked in a previous run - still a success
            status = STATUS_DONE
        elif hashcat_status == "exhausted":
            status = STATUS_NO_RESULTS  # Ran to completion but found nothing
        else:
            status = STATUS_NO_RESULTS

        return {
            "tool": "hashcat",
            "status": status,
            "cracked_count": len(parsed.get("cracked", [])),
            "credentials_added": creds_added,
            "findings_added": findings_added,
            "hashcat_status": parsed["stats"].get("status", "unknown"),
            "potfile_hits": potfile_hits,
        }

    except Exception as e:
        logger.error(f"Error parsing hashcat job: {e}")
        return {"error": str(e)}


def parse_john_job(
    engagement_id: int, log_path: str, job: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse John the Ripper job results and extract cracked passwords."""
    try:
        from souleyez.parsers.john_parser import parse_john_output
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.findings import FindingsManager

        # Read the log file
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

        # Get hash file from job metadata if available
        hash_file = job.get("metadata", {}).get("hash_file", None)

        # Parse john output
        parsed = parse_john_output(log_content, hash_file)

        # Store credentials
        cm = CredentialsManager()
        creds_added = 0

        for cred in parsed.get("cracked", []):
            username = cred.get("username", "")
            password = cred.get("password", "")

            if password:  # At minimum we need a password
                try:
                    cm.add_credential(
                        engagement_id=engagement_id,
                        host_id=None,  # Hash cracking typically not tied to a specific host
                        username=username if username != "unknown" else "",
                        password=password,
                        service="cracked_hash",
                        credential_type="password",
                        tool="john",
                        status="cracked",
                        notes=f"Cracked by John the Ripper",
                    )
                    creds_added += 1
                except Exception:
                    pass  # Skip duplicates

        # Create finding if we cracked passwords
        fm = FindingsManager()
        findings_added = 0

        if parsed.get("cracked"):
            usernames = [
                c.get("username", "unknown")
                for c in parsed["cracked"]
                if c.get("username")
            ]
            usernames_str = ", ".join(usernames[:10])  # First 10
            if len(usernames) > 10:
                usernames_str += f" (+{len(usernames) - 10} more)"

            fm.add_finding(
                engagement_id=engagement_id,
                title=f"Password Hashes Cracked - {len(parsed['cracked'])} passwords recovered",
                finding_type="credential",
                severity="high",
                description=f"John the Ripper successfully cracked {len(parsed['cracked'])} password hash(es).\n\n"
                f"Usernames: {usernames_str}\n"
                f"Session status: {parsed.get('session_status', 'unknown')}",
                tool="john",
            )
            findings_added += 1

        # Determine status
        if creds_added > 0:
            status = STATUS_DONE
        elif parsed.get("session_status") == "completed":
            status = STATUS_NO_RESULTS  # Ran to completion but found nothing
        else:
            status = STATUS_NO_RESULTS

        return {
            "tool": "john",
            "status": status,
            "cracked_count": len(parsed.get("cracked", [])),
            "credentials_added": creds_added,
            "findings_added": findings_added,
            "session_status": parsed.get("session_status", "unknown"),
            "total_loaded": parsed.get("total_loaded", 0),
        }

    except Exception as e:
        logger.error(f"Error parsing john job: {e}")
        return {"error": str(e)}
