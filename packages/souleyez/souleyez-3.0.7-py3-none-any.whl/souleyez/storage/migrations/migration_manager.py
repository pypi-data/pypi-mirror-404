#!/usr/bin/env python3
"""
souleyez.storage.migrations.migration_manager - Database migration system

Uses compiled registry pattern for Nuitka compatibility.
All migrations are imported in __init__.py and registered in MIGRATIONS_REGISTRY.
"""

import sqlite3
from typing import Dict, List

# Import registry from package
from . import MIGRATIONS_REGISTRY, get_all_versions


class MigrationManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Create migrations tracking table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT version FROM schema_migrations ORDER BY version")
        versions = [row[0] for row in cursor.fetchall()]
        conn.close()
        return versions

    def get_pending_migrations(self) -> List[Dict[str, str]]:
        """Get list of pending migrations to apply."""
        applied = set(self.get_applied_migrations())

        # Use compiled registry instead of file discovery
        pending = []
        for version in get_all_versions():
            if version not in applied:
                module = MIGRATIONS_REGISTRY[version]
                name = getattr(module, "DESCRIPTION", version)
                pending.append({"version": version, "name": name, "module": module})

        return pending

    def apply_migration(self, migration: Dict[str, str], silent: bool = False) -> bool:
        """Apply a single migration."""
        if not silent:
            print(f"[{migration['version']}] Applying migration: {migration['name']}")

        try:
            # Set environment variable for migration scripts to check
            import os

            old_silent = os.environ.get("SOULEYEZ_MIGRATION_SILENT")
            if silent:
                os.environ["SOULEYEZ_MIGRATION_SILENT"] = "1"

            # Get migration module from registry (already imported)
            migration_module = migration["module"]

            # Execute upgrade function
            conn = sqlite3.connect(self.db_path)
            migration_module.upgrade(conn)

            # Record migration
            conn.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                (migration["version"], migration["name"]),
            )
            conn.commit()
            conn.close()

            # Restore environment variable
            if silent:
                if old_silent is None:
                    os.environ.pop("SOULEYEZ_MIGRATION_SILENT", None)
                else:
                    os.environ["SOULEYEZ_MIGRATION_SILENT"] = old_silent

            if not silent:
                print(f"[{migration['version']}] ✅ Successfully applied")
            return True

        except Exception as e:
            if not silent:
                print(f"[{migration['version']}] ❌ Failed: {e}")
            return False

    def migrate(self, silent: bool = False) -> int:
        """Apply all pending migrations. Returns number of migrations applied."""
        pending = self.get_pending_migrations()

        if not pending:
            if not silent:
                print("✅ Database is up to date. No migrations to apply.")
            return 0

        if not silent:
            print(f"Found {len(pending)} pending migration(s)")

        applied_count = 0
        for migration in pending:
            if self.apply_migration(migration, silent=silent):
                applied_count += 1
            else:
                if not silent:
                    print("\n❌ Migration failed. Stopping.")
                break

        if applied_count == len(pending) and not silent:
            print(f"\n✅ All {applied_count} migration(s) applied successfully!")

        return applied_count

    def rollback(self, steps: int = 1) -> int:
        """
        Rollback last N migrations.
        Returns number of migrations rolled back.
        """
        applied = self.get_applied_migrations()

        if not applied:
            print("No migrations to rollback")
            return 0

        if steps > len(applied):
            print(f"Only {len(applied)} migrations applied, rolling back all")
            steps = len(applied)

        # Get migrations to rollback (in reverse order)
        to_rollback = applied[-steps:]

        rolled_back = 0
        for version in reversed(to_rollback):
            print(f"[{version}] Rolling back...")

            try:
                # Get migration module from registry
                migration_module = MIGRATIONS_REGISTRY.get(version)

                if not migration_module:
                    print(f"[{version}] ❌ Migration not found in registry")
                    continue

                # Check if downgrade function exists
                if not hasattr(migration_module, "downgrade"):
                    print(f"[{version}] ❌ No downgrade() function found")
                    continue

                # Execute downgrade
                conn = sqlite3.connect(self.db_path)
                migration_module.downgrade(conn)

                # Remove from migrations table
                conn.execute(
                    "DELETE FROM schema_migrations WHERE version = ?", (version,)
                )
                conn.commit()
                conn.close()

                print(f"[{version}] ✅ Rolled back successfully")
                rolled_back += 1

            except Exception as e:
                print(f"[{version}] ❌ Rollback failed: {e}")
                break

        if rolled_back > 0:
            print(f"\n✅ Rolled back {rolled_back} migration(s)")

        return rolled_back

    def status(self):
        """Show migration status."""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        print("=" * 80)
        print("DATABASE MIGRATION STATUS")
        print("=" * 80)
        print(f"Database: {self.db_path}")
        print(f"Applied migrations: {len(applied)}")
        print(f"Pending migrations: {len(pending)}")
        print()

        if applied:
            print("✅ Applied:")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT version, name, applied_at
                FROM schema_migrations
                ORDER BY version
            """)
            for row in cursor.fetchall():
                print(f"  [{row[0]}] {row[1]} (applied: {row[2]})")
            conn.close()
            print()

        if pending:
            print("⏳ Pending:")
            for mig in pending:
                print(f"  [{mig['version']}] {mig['name']}")
        else:
            print("✅ Database is up to date!")

        print("=" * 80)
