"""
Deliverable templates management.
"""

import json
import os
from typing import Dict, List, Optional

from .database import get_db


class TemplateManager:
    """Manage deliverable templates."""

    def __init__(self):
        self.db = get_db()
        self._ensure_builtin_templates()

    def _ensure_builtin_templates(self):
        """Load built-in templates from JSON files if not already loaded."""
        # Get list of existing builtin template names
        existing = self.db.execute(
            "SELECT name FROM deliverable_templates WHERE is_builtin = 1"
        )
        existing_names = {t["name"] for t in existing} if existing else set()

        # Load built-in templates from data/templates/
        templates_dir = self._get_templates_dir()

        builtin_templates = [
            # Original templates
            "pci_dss_4.0.json",
            "owasp_top10_2021.json",
            "hipaa_security.json",
            "nist_csf.json",
            # Compliance Frameworks
            "soc2_type2.json",
            "iso27001.json",
            "cis_controls_v8.json",
            "cmmc_2.0.json",
            "gdpr_article32.json",
            "glba_safeguards.json",
            # Pentest Methodologies
            "ptes_standard.json",
            "internal_network.json",
            "external_network.json",
            "webapp_advanced.json",
            "red_team.json",
            "cloud_security.json",
            "active_directory.json",
            # Industry-Specific
            "nerc_cip.json",
            "hitrust_csf.json",
            "ffiec_cat.json",
        ]

        for template_file in builtin_templates:
            template_path = os.path.join(templates_dir, template_file)
            if os.path.exists(template_path):
                try:
                    with open(template_path, "r") as f:
                        template_data = json.load(f)

                    # Skip if template already exists
                    if template_data["name"] in existing_names:
                        continue

                    self.create_template(
                        name=template_data["name"],
                        description=template_data.get("description"),
                        framework=template_data.get("framework"),
                        engagement_type=template_data.get("engagement_type"),
                        deliverables=template_data["deliverables"],
                        is_builtin=True,
                    )
                except Exception as e:
                    print(f"⚠️  Failed to load template {template_file}: {e}")

    def _get_templates_dir(self) -> str:
        """Get path to templates directory across all installation types."""
        import sys
        from pathlib import Path

        # Check environment variable first
        env_root = os.environ.get("SOULEYEZ_ROOT")
        if env_root:
            env_path = os.path.join(env_root, "data", "templates")
            if os.path.isdir(env_path):
                return env_path

        # Possible locations in priority order
        possible_paths = [
            # Package bundled: souleyez/data/templates/
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
                "templates",
            ),
            # Debian package install
            "/usr/share/souleyez/templates",
            # User local install
            os.path.expanduser("~/.local/share/souleyez/templates"),
            # System-wide pip install
            os.path.join(sys.prefix, "share", "souleyez", "templates"),
        ]

        for path in possible_paths:
            if os.path.isdir(path) and os.listdir(path):
                return path

        # Fallback to development path (may not exist)
        return possible_paths[0]

    def create_template(
        self,
        name: str,
        deliverables: List[Dict],
        description: str = None,
        framework: str = None,
        engagement_type: str = None,
        created_by: str = None,
        is_builtin: bool = False,
    ) -> int:
        """Create a new deliverable template."""
        deliverables_json = json.dumps(deliverables)

        template_id = self.db.insert(
            "deliverable_templates",
            {
                "name": name,
                "description": description,
                "framework": framework,
                "engagement_type": engagement_type,
                "deliverables_json": deliverables_json,
                "created_by": created_by,
                "is_builtin": 1 if is_builtin else 0,
            },
        )

        return template_id

    def get_template(self, template_id: int) -> Optional[Dict]:
        """Get template by ID."""
        template = self.db.execute_one(
            "SELECT * FROM deliverable_templates WHERE id = ?", (template_id,)
        )

        if template:
            template["deliverables"] = json.loads(template["deliverables_json"])

        return template

    def list_templates(
        self,
        framework: str = None,
        engagement_type: str = None,
        include_custom: bool = True,
    ) -> List[Dict]:
        """List available templates."""
        query = "SELECT * FROM deliverable_templates WHERE 1=1"
        params = []

        if framework:
            query += " AND framework = ?"
            params.append(framework)

        if engagement_type:
            query += " AND engagement_type = ?"
            params.append(engagement_type)

        if not include_custom:
            query += " AND is_builtin = 1"

        query += " ORDER BY is_builtin DESC, name ASC"

        templates = self.db.execute(query, tuple(params))

        # Parse deliverables JSON for each
        for template in templates:
            template["deliverables"] = json.loads(template["deliverables_json"])

        return templates

    def apply_template(self, template_id: int, engagement_id: int) -> int:
        """Apply a template to an engagement."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        from .deliverables import DeliverableManager

        dm = DeliverableManager()

        count = 0
        for deliverable_config in template["deliverables"]:
            # Inject engagement_id into validation queries
            validation_query = deliverable_config.get("validation_query")
            if validation_query:
                validation_query = self._inject_engagement_filter(
                    validation_query, engagement_id
                )

            dm.add_deliverable(
                engagement_id=engagement_id,
                category=deliverable_config["category"],
                title=deliverable_config["title"],
                description=deliverable_config.get("description"),
                target_type=deliverable_config.get("target_type", "manual"),
                target_value=deliverable_config.get("target_value"),
                auto_validate=deliverable_config.get("auto_validate", False),
                validation_query=validation_query,
                priority=deliverable_config.get("priority", "medium"),
            )
            count += 1

        return count

    def _inject_engagement_filter(self, query: str, engagement_id: int) -> str:
        """
        Inject engagement_id filter into validation queries.

        Handles different table structures:
        - Tables with direct engagement_id: hosts, findings, credentials, osint_data
        - Tables requiring JOIN: services (via hosts)
        """
        import re

        query_lower = query.lower()

        # For services table, need to join through hosts
        if "from services" in query_lower and "join" not in query_lower:
            # Replace "FROM services" with a JOIN to hosts
            query = re.sub(
                r"FROM\s+services\b",
                f"FROM services s JOIN hosts h ON s.host_id = h.id",
                query,
                flags=re.IGNORECASE,
            )
            # Add WHERE clause with engagement filter
            if "where" in query_lower:
                query = re.sub(
                    r"\bWHERE\b",
                    f"WHERE h.engagement_id = {engagement_id} AND",
                    query,
                    flags=re.IGNORECASE,
                )
            else:
                query += f" WHERE h.engagement_id = {engagement_id}"
        # For tables with direct engagement_id column
        elif any(
            table in query_lower
            for table in [
                "from hosts",
                "from findings",
                "from credentials",
                "from osint_data",
            ]
        ):
            if "where" in query_lower:
                query = re.sub(
                    r"\bWHERE\b",
                    f"WHERE engagement_id = {engagement_id} AND",
                    query,
                    flags=re.IGNORECASE,
                )
            else:
                query += f" WHERE engagement_id = {engagement_id}"

        return query

    def delete_template(self, template_id: int) -> bool:
        """Delete a custom template (cannot delete built-in)."""
        template = self.get_template(template_id)
        if not template:
            return False

        if template["is_builtin"]:
            raise ValueError("Cannot delete built-in templates")

        self.db.execute(
            "DELETE FROM deliverable_templates WHERE id = ?", (template_id,)
        )
        return True

    def export_template(self, template_id: int) -> str:
        """Export template as JSON string."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        export_data = {
            "name": template["name"],
            "description": template["description"],
            "framework": template["framework"],
            "engagement_type": template["engagement_type"],
            "deliverables": template["deliverables"],
        }

        return json.dumps(export_data, indent=2)

    def import_template(self, json_data: str, created_by: str = None) -> int:
        """Import template from JSON string."""
        try:
            template_data = json.loads(json_data)

            return self.create_template(
                name=template_data["name"],
                description=template_data.get("description"),
                framework=template_data.get("framework"),
                engagement_type=template_data.get("engagement_type"),
                deliverables=template_data["deliverables"],
                created_by=created_by,
                is_builtin=False,
            )
        except Exception as e:
            raise ValueError(f"Failed to import template: {e}")
