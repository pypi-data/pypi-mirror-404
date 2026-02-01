#!/usr/bin/env python3
"""
souleyez.storage.hosts - Host and service management
"""

from typing import Any, Dict, List, Optional

from souleyez.log_config import get_logger

from .database import get_db

logger = get_logger(__name__)


class HostManager:
    def __init__(self):
        self.db = get_db()

    def add_or_update_host(self, engagement_id: int, host_data: Dict[str, Any]) -> int:
        """
        Add or update a host in the database.

        Args:
            engagement_id: Engagement ID
            host_data: Host data from parser (ip, hostname, status, os)

        Returns:
            host_id
        """
        ip = host_data.get("ip")
        if not ip:
            raise ValueError("Host must have an IP address")

        # Determine scope status for this host
        scope_status = self._determine_scope_status(engagement_id, ip)

        # Check if host already exists
        existing = self.db.execute_one(
            "SELECT id, scope_status FROM hosts WHERE engagement_id = ? AND ip_address = ?",
            (engagement_id, ip),
        )

        if existing:
            # Update existing host
            host_id = existing["id"]
            # Only update fields that have values (don't overwrite with NULL)
            update_data = {}

            # Always update status
            update_data["status"] = host_data.get("status", "up")

            # Update scope_status if it was unknown and we now have a determination
            if existing.get("scope_status") == "unknown" and scope_status != "unknown":
                update_data["scope_status"] = scope_status

            # Only update these fields if they have values
            if host_data.get("hostname"):
                update_data["hostname"] = host_data["hostname"]
            if host_data.get("domain"):
                update_data["domain"] = host_data["domain"]
            if host_data.get("os"):
                update_data["os_name"] = host_data["os"]
            if host_data.get("mac_address"):
                update_data["mac_address"] = host_data["mac_address"]
            if host_data.get("os_accuracy") is not None:
                update_data["os_accuracy"] = host_data["os_accuracy"]

            if update_data:
                updates = ", ".join([f"{k} = ?" for k in update_data.keys()])
                values = list(update_data.values()) + [host_id]
                self.db.execute(
                    f"UPDATE hosts SET {updates} WHERE id = ?", tuple(values)
                )

            return host_id
        else:
            # Insert new host
            host_id = self.db.insert(
                "hosts",
                {
                    "engagement_id": engagement_id,
                    "ip_address": ip,
                    "hostname": host_data.get("hostname"),
                    "domain": host_data.get("domain"),
                    "os_name": host_data.get("os"),
                    "mac_address": host_data.get("mac_address"),
                    "os_accuracy": host_data.get("os_accuracy"),
                    "status": host_data.get("status", "up"),
                    "scope_status": scope_status,
                },
            )

            return host_id

    def _determine_scope_status(self, engagement_id: int, ip: str) -> str:
        """
        Determine scope status for a host based on engagement scope.

        Args:
            engagement_id: Engagement ID
            ip: IP address to check

        Returns:
            'in_scope', 'out_of_scope', or 'unknown'
        """
        try:
            from souleyez.security.scope_validator import ScopeValidator

            validator = ScopeValidator(engagement_id)
            if validator.has_scope_defined():
                result = validator.validate_ip(ip)
                return "in_scope" if result.is_in_scope else "out_of_scope"
            return "unknown"  # No scope defined
        except Exception as e:
            logger.warning(f"Failed to determine scope status for {ip}: {e}")
            return "unknown"

    def update_scope_status(self, host_id: int, scope_status: str) -> bool:
        """
        Update scope status for a host.

        Args:
            host_id: Host ID
            scope_status: 'in_scope', 'out_of_scope', or 'unknown'

        Returns:
            True if successful
        """
        valid_statuses = ["in_scope", "out_of_scope", "unknown"]
        if scope_status not in valid_statuses:
            raise ValueError(
                f"Invalid scope_status: {scope_status}. Must be one of: {valid_statuses}"
            )

        try:
            self.db.execute(
                "UPDATE hosts SET scope_status = ? WHERE id = ?",
                (scope_status, host_id),
            )
            return True
        except Exception:
            return False

    def revalidate_scope_status(self, engagement_id: int) -> Dict[str, int]:
        """
        Revalidate scope status for all hosts in an engagement.

        Call this after scope entries are added/modified to update all hosts.

        Args:
            engagement_id: Engagement ID

        Returns:
            {'updated': N, 'in_scope': X, 'out_of_scope': Y}
        """
        hosts = self.list_hosts(engagement_id)
        updated = 0
        in_scope = 0
        out_of_scope = 0

        for host in hosts:
            ip = host.get("ip") or host.get("ip_address")
            new_status = self._determine_scope_status(engagement_id, ip)
            if new_status != host.get("scope_status"):
                self.update_scope_status(host["id"], new_status)
                updated += 1

            if new_status == "in_scope":
                in_scope += 1
            elif new_status == "out_of_scope":
                out_of_scope += 1

        return {"updated": updated, "in_scope": in_scope, "out_of_scope": out_of_scope}

    def add_service(self, host_id: int, service_data: Dict[str, Any]) -> int:
        """
        Add or update a service for a host.

        Uses atomic upsert (INSERT ... ON CONFLICT DO UPDATE) to handle
        duplicate services properly without race conditions.

        Args:
            host_id: Host ID
            service_data: Service data (port, protocol, state, service, version)

        Returns:
            service_id
        """
        port = service_data.get("port")
        protocol = service_data.get("protocol", "tcp")

        if not port:
            raise ValueError("Service must have a port")

        state = service_data.get("state", "open")
        service_name = service_data.get("service") or "unknown"
        service_version = service_data.get("version")
        service_product = service_data.get("product")

        # Use atomic upsert - INSERT with ON CONFLICT UPDATE
        # This handles duplicates properly without race conditions
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO services (host_id, port, protocol, state, service_name, service_version, service_product)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(host_id, port, protocol) DO UPDATE SET
                    state = excluded.state,
                    service_name = excluded.service_name,
                    service_version = COALESCE(excluded.service_version, service_version),
                    service_product = COALESCE(excluded.service_product, service_product)
            """,
                (
                    host_id,
                    port,
                    protocol,
                    state,
                    service_name,
                    service_version,
                    service_product,
                ),
            )
            conn.commit()

            # Get the service_id (either newly inserted or existing)
            result = cursor.execute(
                "SELECT id FROM services WHERE host_id = ? AND port = ? AND protocol = ?",
                (host_id, port, protocol),
            ).fetchone()
            return result[0] if result else 0
        except Exception as e:
            conn.rollback()
            raise e

    def import_nmap_results(
        self, engagement_id: int, parsed_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Import parsed nmap results into the database.

        Args:
            engagement_id: Engagement ID
            parsed_data: Output from nmap_parser.parse_nmap_text()

        Returns:
            {'hosts_added': N, 'services_added': M} - N is count of live hosts only (status='up')
        """
        hosts_added = 0
        services_added = 0

        for host_data in parsed_data.get("hosts", []):
            # Add/update host
            host_id = self.add_or_update_host(engagement_id, host_data)

            # Only count live hosts
            if host_data.get("status") == "up":
                hosts_added += 1

            # Add services
            for service_data in host_data.get("services", []):
                self.add_service(host_id, service_data)
                services_added += 1

        return {"hosts_added": hosts_added, "services_added": services_added}

    def list_hosts(self, engagement_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """List all hosts in engagement with optional limit."""
        query = "SELECT * FROM hosts WHERE engagement_id = ? ORDER BY ip_address"
        params = [engagement_id]

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        hosts = self.db.execute(query, tuple(params))

        # Normalize column names for compatibility (ip_address -> ip)
        return [
            {**host, "ip": host.get("ip_address") or host.get("ip")} for host in hosts
        ]

    def get_host(self, host_id: int) -> Optional[Dict[str, Any]]:
        """Get a single host by ID."""
        host = self.db.execute_one("SELECT * FROM hosts WHERE id = ?", (host_id,))
        if host:
            # Normalize column names for compatibility (ip_address -> ip)
            host["ip"] = host.get("ip_address") or host.get("ip")
        return host

    def get_host_services(self, host_id: int) -> List[Dict[str, Any]]:
        """Get all services for a host."""
        return self.db.execute(
            "SELECT * FROM services WHERE host_id = ? ORDER BY port", (host_id,)
        )

    def get_all_services(
        self,
        engagement_id: int,
        service_name: str = None,
        port_min: int = None,
        port_max: int = None,
        protocol: str = None,
        sort_by: str = "port",
    ) -> List[Dict[str, Any]]:
        """
        Get all services across all hosts in engagement with optional filters.

        Args:
            engagement_id: Engagement ID
            service_name: Filter by service name (partial match)
            port_min: Filter by minimum port number
            port_max: Filter by maximum port number
            protocol: Filter by protocol (tcp/udp)
            sort_by: Sort by 'port', 'service', or 'protocol' (default: 'port')

        Returns:
            List of service dicts with host information
        """
        query = """
            SELECT
                s.*,
                h.ip_address,
                h.hostname
            FROM services s
            JOIN hosts h ON s.host_id = h.id
            WHERE h.engagement_id = ?
        """
        params = [engagement_id]

        if service_name:
            query += " AND s.service_name LIKE ?"
            params.append(f"%{service_name}%")

        if port_min is not None:
            query += " AND s.port >= ?"
            params.append(port_min)

        if port_max is not None:
            query += " AND s.port <= ?"
            params.append(port_max)

        if protocol:
            query += " AND s.protocol = ?"
            params.append(protocol)

        # Add sorting
        if sort_by == "service":
            query += " ORDER BY s.service_name, s.port"
        elif sort_by == "protocol":
            query += " ORDER BY s.protocol, s.port"
        else:  # default to port
            query += " ORDER BY s.port"

        return self.db.execute(query, tuple(params))

    def get_host_by_ip(self, engagement_id: int, ip: str) -> Optional[Dict[str, Any]]:
        """Get host by IP address."""
        return self.db.execute_one(
            "SELECT * FROM hosts WHERE engagement_id = ? AND ip_address = ?",
            (engagement_id, ip),
        )

    def search_hosts(
        self,
        engagement_id: int,
        search: str = None,
        os_name: str = None,
        status: str = None,
        tags: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Search and filter hosts.

        Args:
            engagement_id: Engagement ID
            search: Search in IP address and hostname
            os_name: Filter by OS name (partial match)
            status: Filter by status (up/down)
            tags: Filter by tag (partial match)

        Returns:
            List of matching hosts
        """
        query = "SELECT * FROM hosts WHERE engagement_id = ?"
        params = [engagement_id]

        if search:
            query += " AND (ip_address LIKE ? OR hostname LIKE ?)"
            search_pattern = f"%{search}%"
            params.append(search_pattern)
            params.append(search_pattern)

        if os_name:
            query += " AND os_name LIKE ?"
            params.append(f"%{os_name}%")

        if status:
            query += " AND status = ?"
            params.append(status)

        if tags:
            query += " AND tags LIKE ?"
            params.append(f"%{tags}%")

        query += " ORDER BY ip_address"

        return self.db.execute(query, tuple(params))

    def add_tag(self, host_id: int, tag: str) -> bool:
        """
        Add a tag to a host.

        Args:
            host_id: Host ID
            tag: Tag to add

        Returns:
            True if successful
        """
        host = self.db.execute_one("SELECT tags FROM hosts WHERE id = ?", (host_id,))
        if not host:
            return False

        current_tags = host.get("tags", "") or ""
        tag_list = [t.strip() for t in current_tags.split(",") if t.strip()]

        # Add tag if not already present
        if tag not in tag_list:
            tag_list.append(tag)

        new_tags = ", ".join(tag_list)

        try:
            self.db.execute(
                "UPDATE hosts SET tags = ? WHERE id = ?", (new_tags, host_id)
            )
            return True
        except Exception:
            return False

    def remove_tag(self, host_id: int, tag: str) -> bool:
        """
        Remove a tag from a host.

        Args:
            host_id: Host ID
            tag: Tag to remove

        Returns:
            True if successful
        """
        host = self.db.execute_one("SELECT tags FROM hosts WHERE id = ?", (host_id,))
        if not host:
            return False

        current_tags = host.get("tags", "") or ""
        tag_list = [t.strip() for t in current_tags.split(",") if t.strip()]

        # Remove tag if present
        if tag in tag_list:
            tag_list.remove(tag)

        new_tags = ", ".join(tag_list)

        try:
            self.db.execute(
                "UPDATE hosts SET tags = ? WHERE id = ?", (new_tags, host_id)
            )
            return True
        except Exception:
            return False

    def set_tags(self, host_id: int, tags: str) -> bool:
        """
        Set tags for a host (replaces existing tags).

        Args:
            host_id: Host ID
            tags: Comma-separated tags

        Returns:
            True if successful
        """
        try:
            self.db.execute("UPDATE hosts SET tags = ? WHERE id = ?", (tags, host_id))
            return True
        except Exception:
            return False

    def get_all_tags(self, engagement_id: int) -> List[str]:
        """Get list of all unique tags used in engagement."""
        hosts = self.db.execute(
            "SELECT tags FROM hosts WHERE engagement_id = ?", (engagement_id,)
        )

        all_tags = set()
        for host in hosts:
            tags_str = host.get("tags", "") or ""
            if tags_str:
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                all_tags.update(tags)

        return sorted(list(all_tags))

    def update_host_status(
        self,
        host_id: int,
        status: str = None,
        access_level: str = None,
        notes: str = None,
    ) -> bool:
        """
        Update host status and access level.

        Args:
            host_id: Host ID
            status: Host status (active/compromised/offline)
            access_level: Access level (none/user/admin/root)
            notes: Optional notes

        Returns:
            bool: True if successful
        """
        updates = []
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)

        if access_level:
            updates.append("access_level = ?")
            params.append(access_level)

        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if not updates:
            return False

        params.append(host_id)
        query = f"UPDATE hosts SET {', '.join(updates)} WHERE id = ?"

        try:
            self.db.execute(query, tuple(params))
            return True
        except Exception:
            return False

    def update_hostname(self, host_id: int, hostname: str) -> bool:
        """
        Update hostname for a host.

        Args:
            host_id: Host ID
            hostname: New hostname

        Returns:
            bool: True if successful
        """
        try:
            self.db.execute(
                "UPDATE hosts SET hostname = ? WHERE id = ?", (hostname, host_id)
            )
            return True
        except Exception:
            return False

    def update_os(self, host_id: int, os_name: str) -> bool:
        """
        Update OS name for a host.

        Args:
            host_id: Host ID
            os_name: New OS name

        Returns:
            bool: True if successful
        """
        try:
            self.db.execute(
                "UPDATE hosts SET os_name = ? WHERE id = ?", (os_name, host_id)
            )
            return True
        except Exception:
            return False

    def delete_host(self, host_id: int) -> bool:
        """
        Delete a host and all associated data (services, findings, etc.).

        Args:
            host_id: Host ID to delete

        Returns:
            bool: True if successful, False otherwise

        Raises:
            PermissionError: If user lacks HOST_DELETE permission
        """
        # Check permission
        from souleyez.auth import get_current_user
        from souleyez.auth.permissions import Permission, PermissionChecker

        user = get_current_user()
        if user:
            checker = PermissionChecker(user.role, user.tier)
            if not checker.has_permission(Permission.HOST_DELETE):
                raise PermissionError("Permission denied: HOST_DELETE required")

        try:
            # Delete all associated data in correct order (respecting foreign keys)
            # Note: Foreign keys are not enabled by default in SQLite, so we handle explicitly

            # 1. Delete services (has FK to hosts with CASCADE)
            self.db.execute("DELETE FROM services WHERE host_id = ?", (host_id,))

            # 2. Delete web paths (has FK to hosts with CASCADE)
            self.db.execute("DELETE FROM web_paths WHERE host_id = ?", (host_id,))

            # 3. Delete SMB shares (has FK to hosts with CASCADE)
            self.db.execute("DELETE FROM smb_shares WHERE host_id = ?", (host_id,))

            # 4. Update findings to set host_id to NULL (has FK with SET NULL)
            self.db.execute(
                "UPDATE findings SET host_id = NULL WHERE host_id = ?", (host_id,)
            )

            # 5. Update credentials to set host_id to NULL (has FK but no ON DELETE clause)
            self.db.execute(
                "UPDATE credentials SET host_id = NULL WHERE host_id = ?", (host_id,)
            )

            # 6. Finally delete the host
            self.db.execute("DELETE FROM hosts WHERE id = ?", (host_id,))

            logger.info(f"Deleted host {host_id} and all associated data")
            return True
        except Exception as e:
            logger.error(f"Failed to delete host {host_id}: {e}")
            return False

    def get_host_vulnerability_count(self, host_id: int) -> int:
        """
        Get count of vulnerabilities (findings) for a specific host.

        Args:
            host_id: Host ID

        Returns:
            Count of vulnerability findings for this host
        """
        result = self.db.execute_one(
            """SELECT COUNT(*) as count FROM findings 
               WHERE host_id = ? 
               AND finding_type IN ('vulnerability', 'sql_injection', 'xss', 'file_inclusion', 
                                   'web_vulnerability', 'sql_injection_exploitation')""",
            (host_id,),
        )
        return result["count"] if result else 0
