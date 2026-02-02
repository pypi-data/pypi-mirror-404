#!/usr/bin/env python3
"""
souleyez.plugins.service_explorer - Unified service exploration tool

Connects to and explores various services after access is discovered:
- FTP (anonymous or authenticated)
- SFTP (SSH file transfer)
- SMB (Windows shares)
- NFS (Network file system)
- TFTP (Trivial FTP)
- Redis (NoSQL database)
- MongoDB (NoSQL database)

This tool is designed to auto-chain from discovery tools when access is found.
"""

import ftplib  # nosec B402 - intentional for pentesting FTP services
import json
import os
import socket
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .plugin_base import PluginBase

HELP = {
    "name": "Service Explorer - Unified File/Data Browser",
    "description": (
        "Connects to and explores services after access is discovered.\n\n"
        "Supported protocols:\n"
        "  - ftp://   - FTP file browsing (anonymous or authenticated)\n"
        "  - sftp://  - SFTP/SSH file browsing\n"
        "  - smb://   - SMB/Windows share browsing\n"
        "  - nfs://   - NFS mount browsing\n"
        "  - tftp://  - TFTP file retrieval\n"
        "  - redis:// - Redis database exploration\n"
        "  - mongo:// - MongoDB database exploration\n\n"
        "Auto-chains from findings like 'FTP anonymous access' or 'SMB null session'.\n"
    ),
    "usage": "souleyez jobs enqueue service_explorer <protocol://target>",
    "examples": [
        "souleyez jobs enqueue service_explorer ftp://anonymous@192.168.1.100",
        "souleyez jobs enqueue service_explorer ftp://user:pass@192.168.1.100",
        "souleyez jobs enqueue service_explorer smb://192.168.1.100/share",
        "souleyez jobs enqueue service_explorer redis://192.168.1.100:6379",
    ],
    "flags": [
        ["--depth <n>", "Maximum directory depth to explore (default: 3)"],
        ["--download", "Download interesting files to evidence folder"],
        ["--download-all", "Download ALL files (use with caution)"],
        ["--timeout <sec>", "Connection timeout (default: 10)"],
    ],
    "presets": [
        {
            "name": "FTP Anonymous",
            "args": ["ftp://anonymous@{target}"],
            "desc": "Browse FTP with anonymous login",
        },
        {
            "name": "FTP Anon+Download",
            "args": ["ftp://anonymous@{target}", "--download"],
            "desc": "FTP anonymous + download interesting files",
        },
        {
            "name": "FTP with Creds",
            "args": ["ftp://{target}"],
            "desc": "Browse FTP (will prompt for creds)",
        },
        {
            "name": "Redis",
            "args": ["redis://{target}:6379"],
            "desc": "Explore Redis database",
        },
        {
            "name": "MongoDB",
            "args": ["mongodb://{target}:27017"],
            "desc": "Explore MongoDB database",
        },
        {"name": "NFS", "args": ["nfs://{target}"], "desc": "Browse NFS exports"},
        {
            "name": "SFTP",
            "args": ["sftp://{target}"],
            "desc": "Browse via SFTP (needs creds)",
        },
    ],
    "help_sections": [
        {
            "title": "URL Format & Protocols",
            "color": "cyan",
            "content": [
                {
                    "title": "Format",
                    "desc": "protocol://[user:pass@]host[:port][/path]",
                },
                {
                    "title": "Examples",
                    "desc": "Common URL formats for each protocol",
                    "tips": [
                        "FTP: ftp://anonymous@192.168.1.100",
                        "FTP w/creds: ftp://admin:password@192.168.1.100",
                        "SFTP: sftp://user:pass@192.168.1.100",
                        "NFS: nfs://192.168.1.100/export",
                        "Redis: redis://192.168.1.100:6379",
                        "MongoDB: mongodb://192.168.1.100:27017",
                        "TFTP: tftp://192.168.1.100/filename",
                    ],
                },
            ],
        },
        {
            "title": "Auto-Chain Triggers",
            "color": "green",
            "content": [
                {
                    "title": "How It Works",
                    "desc": "Service Explorer auto-runs when access is discovered by other tools",
                },
                {
                    "title": "Triggers",
                    "desc": "These findings trigger Service Explorer",
                    "tips": [
                        "FTP Anonymous: MSF finds anonymous FTP -> auto explores files",
                        "Redis No-Auth: Nmap finds redis -> auto explores database",
                        "NFS Exports: MSF finds NFS exports -> auto explores shares",
                        "MongoDB No-Auth: Nmap finds mongodb -> auto explores database",
                    ],
                },
            ],
        },
        {
            "title": "What Gets Flagged",
            "color": "yellow",
            "content": [
                {
                    "title": "Interesting Files",
                    "desc": "These file patterns are auto-flagged for review",
                    "tips": [
                        "Credentials: *.conf, *.ini, *.env, passwd, shadow, *.pem, *.key",
                        "Database: *.sql, *.db, *.sqlite, *.mdb",
                        "Backups: *.bak, *.backup, *.tar.gz, *.zip",
                        "CTF Flags: flag*, proof*, root.txt, user.txt",
                        "Source Code: *.php, *.asp, *.jsp",
                    ],
                },
            ],
        },
    ],
}

# Interesting file patterns to flag/download
INTERESTING_PATTERNS = [
    # Credentials & configs
    "*.conf",
    "*.config",
    "*.cfg",
    "*.ini",
    "*.env",
    "*.htpasswd",
    "*.htaccess",
    "passwd",
    "shadow",
    "*.pem",
    "*.key",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "authorized_keys",
    "*.pfx",
    "*.p12",
    "credentials*",
    "secrets*",
    "password*",
    # Database
    "*.sql",
    "*.db",
    "*.sqlite",
    "*.mdb",
    # Backups
    "*.bak",
    "*.backup",
    "*.old",
    "*.orig",
    "*.save",
    "*.tar",
    "*.tar.gz",
    "*.tgz",
    "*.zip",
    "*.rar",
    "*.7z",
    # Source code
    "*.php",
    "*.asp",
    "*.aspx",
    "*.jsp",
    # CTF flags
    "flag*",
    "*flag*",
    "FLAG*",
    "proof*",
    "root.txt",
    "user.txt",
    "local.txt",
    # Interesting docs
    "readme*",
    "README*",
    "todo*",
    "TODO*",
    "notes*",
    "NOTES*",
]


class ProtocolHandler(ABC):
    """Base class for protocol-specific handlers."""

    def __init__(
        self,
        target: str,
        username: str = None,
        password: str = None,
        port: int = None,
        timeout: int = 10,
    ):
        self.target = target
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.files_found: List[Dict[str, Any]] = []
        self.interesting_files: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.downloaded: List[str] = []

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the service. Returns True on success."""
        pass

    @abstractmethod
    def list_directory(self, path: str = "/") -> List[Dict[str, Any]]:
        """List contents of a directory. Returns list of file info dicts."""
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file. Returns True on success."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close the connection."""
        pass

    def is_interesting(self, filename: str) -> bool:
        """Check if a filename matches interesting patterns."""
        import fnmatch

        filename_lower = filename.lower()
        for pattern in INTERESTING_PATTERNS:
            if fnmatch.fnmatch(filename_lower, pattern.lower()):
                return True
        return False

    def explore(
        self, path: str = "/", depth: int = 3, current_depth: int = 0
    ) -> List[Dict[str, Any]]:
        """Recursively explore directories up to max depth."""
        if current_depth >= depth:
            return []

        results = []
        try:
            items = self.list_directory(path)
            for item in items:
                item["path"] = path
                item["full_path"] = os.path.join(path, item["name"]).replace("\\", "/")
                results.append(item)

                # Flag interesting files
                if self.is_interesting(item["name"]):
                    item["interesting"] = True
                    self.interesting_files.append(item)

                # Recurse into directories
                if item.get("type") == "directory":
                    subpath = item["full_path"]
                    results.extend(self.explore(subpath, depth, current_depth + 1))
        except Exception as e:
            self.errors.append(f"Error exploring {path}: {e}")

        return results


class FTPHandler(ProtocolHandler):
    """FTP protocol handler using ftplib."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ftp: Optional[ftplib.FTP] = None
        self.port = self.port or 21

    def connect(self) -> bool:
        try:
            self.ftp = ftplib.FTP()  # nosec B321 - intentional for pentesting
            self.ftp.connect(self.target, self.port, timeout=self.timeout)

            # Login
            username = self.username or "anonymous"
            password = self.password or "anonymous@"
            self.ftp.login(username, password)
            return True
        except Exception as e:
            self.errors.append(f"FTP connection failed: {e}")
            return False

    def list_directory(self, path: str = "/") -> List[Dict[str, Any]]:
        if not self.ftp:
            return []

        items = []
        try:
            self.ftp.cwd(path)

            # Try MLSD first (more detailed)
            try:
                for name, facts in self.ftp.mlsd():
                    if name in (".", ".."):
                        continue
                    item = {
                        "name": name,
                        "type": "directory" if facts.get("type") == "dir" else "file",
                        "size": int(facts.get("size", 0)),
                    }
                    items.append(item)
            except (ftplib.error_perm, AttributeError):
                # Fall back to NLST
                names = self.ftp.nlst()
                for name in names:
                    if name in (".", ".."):
                        continue
                    # Try to determine if it's a directory
                    is_dir = False
                    try:
                        self.ftp.cwd(name)
                        self.ftp.cwd("..")
                        is_dir = True
                    except ftplib.error_perm:
                        pass

                    items.append(
                        {
                            "name": name,
                            "type": "directory" if is_dir else "file",
                            "size": 0,
                        }
                    )
        except Exception as e:
            self.errors.append(f"FTP list error at {path}: {e}")

        return items

    def download_file(self, remote_path: str, local_path: str) -> bool:
        if not self.ftp:
            return False

        try:
            # Navigate to directory
            dirname = os.path.dirname(remote_path)
            filename = os.path.basename(remote_path)

            if dirname:
                self.ftp.cwd(dirname)

            # Download
            with open(local_path, "wb") as f:
                self.ftp.retrbinary(f"RETR {filename}", f.write)

            self.downloaded.append(remote_path)
            return True
        except Exception as e:
            self.errors.append(f"FTP download error {remote_path}: {e}")
            return False

    def disconnect(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except Exception:
                pass
            self.ftp = None


class TFTPHandler(ProtocolHandler):
    """TFTP protocol handler - attempts to retrieve common files."""

    # Common files found on TFTP servers (routers, network devices)
    COMMON_TFTP_FILES = [
        "running-config",
        "startup-config",
        "config.txt",
        "config",
        "backup.cfg",
        "router.cfg",
        "switch.cfg",
        "etc/passwd",
        "etc/shadow",
        "boot.ini",
        "win.ini",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port = self.port or 69

    def connect(self) -> bool:
        # TFTP is connectionless, just verify target is reachable
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            sock.close()
            return True
        except Exception as e:
            self.errors.append(f"TFTP target unreachable: {e}")
            return False

    def list_directory(self, path: str = "/") -> List[Dict[str, Any]]:
        # TFTP doesn't support directory listing
        # Return list of common files to try
        return [
            {"name": f, "type": "file", "size": 0, "note": "common TFTP file"}
            for f in self.COMMON_TFTP_FILES
        ]

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file via TFTP using system tftp client."""
        try:
            import subprocess

            result = subprocess.run(
                ["tftp", self.target, "-c", "get", remote_path, local_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                self.downloaded.append(remote_path)
                return True
            return False
        except FileNotFoundError:
            # tftp client not installed, try atftp
            try:
                import subprocess

                result = subprocess.run(
                    ["atftp", "-g", "-r", remote_path, "-l", local_path, self.target],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                    self.downloaded.append(remote_path)
                    return True
            except Exception:
                pass
            self.errors.append("No TFTP client available (tftp/atftp)")
            return False
        except Exception as e:
            self.errors.append(f"TFTP download error {remote_path}: {e}")
            return False

    def disconnect(self):
        pass  # TFTP is connectionless


class RedisHandler(ProtocolHandler):
    """Redis protocol handler for exploring Redis databases."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port = self.port or 6379
        self.client = None

    def connect(self) -> bool:
        try:
            import redis

            self.client = redis.Redis(
                host=self.target,
                port=self.port,
                password=self.password,
                socket_timeout=self.timeout,
                decode_responses=True,
            )
            # Test connection
            self.client.ping()
            return True
        except ImportError:
            self.errors.append("redis-py not installed (pip install redis)")
            return False
        except Exception as e:
            self.errors.append(f"Redis connection failed: {e}")
            return False

    def list_directory(self, path: str = "/") -> List[Dict[str, Any]]:
        """List Redis keys (path is used as pattern)."""
        if not self.client:
            return []

        items = []
        try:
            pattern = "*" if path == "/" else f"{path}*"
            keys = self.client.keys(pattern)[:1000]  # Limit to 1000 keys

            for key in keys:
                try:
                    key_type = self.client.type(key)
                    size = 0
                    if key_type == "string":
                        size = self.client.strlen(key)
                    elif key_type in ("list", "set", "zset"):
                        size = (
                            self.client.llen(key)
                            if key_type == "list"
                            else self.client.scard(key)
                        )

                    items.append(
                        {
                            "name": key,
                            "type": key_type,
                            "size": size,
                        }
                    )
                except Exception:
                    items.append({"name": key, "type": "unknown", "size": 0})

            # Also get server info
            try:
                info = self.client.info()
                items.append(
                    {
                        "name": "__SERVER_INFO__",
                        "type": "info",
                        "size": 0,
                        "data": {
                            "redis_version": info.get("redis_version"),
                            "os": info.get("os"),
                            "used_memory_human": info.get("used_memory_human"),
                            "connected_clients": info.get("connected_clients"),
                            "total_keys": sum(
                                info.get(f"db{i}", {}).get("keys", 0) for i in range(16)
                            ),
                        },
                    }
                )
            except Exception:
                pass

        except Exception as e:
            self.errors.append(f"Redis key listing error: {e}")

        return items

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Dump a Redis key's value to a file."""
        if not self.client:
            return False

        try:
            key = remote_path
            key_type = self.client.type(key)

            if key_type == "string":
                value = self.client.get(key)
            elif key_type == "list":
                value = self.client.lrange(key, 0, -1)
            elif key_type == "set":
                value = list(self.client.smembers(key))
            elif key_type == "zset":
                value = self.client.zrange(key, 0, -1, withscores=True)
            elif key_type == "hash":
                value = self.client.hgetall(key)
            else:
                value = f"Unknown type: {key_type}"

            with open(local_path, "w") as f:
                if isinstance(value, (list, dict)):
                    json.dump(value, f, indent=2, default=str)
                else:
                    f.write(str(value))

            self.downloaded.append(key)
            return True
        except Exception as e:
            self.errors.append(f"Redis dump error {remote_path}: {e}")
            return False

    def disconnect(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None


class SFTPHandler(ProtocolHandler):
    """SFTP protocol handler using paramiko."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port = self.port or 22
        self.sftp = None
        self.transport = None

    def connect(self) -> bool:
        try:
            import paramiko

            self.transport = paramiko.Transport((self.target, self.port))
            self.transport.connect(
                username=self.username or "anonymous", password=self.password or ""
            )
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            return True
        except ImportError:
            self.errors.append("paramiko not installed (pip install paramiko)")
            return False
        except Exception as e:
            self.errors.append(f"SFTP connection failed: {e}")
            return False

    def list_directory(self, path: str = "/") -> List[Dict[str, Any]]:
        if not self.sftp:
            return []

        items = []
        try:
            for entry in self.sftp.listdir_attr(path):
                import stat

                is_dir = stat.S_ISDIR(entry.st_mode)
                items.append(
                    {
                        "name": entry.filename,
                        "type": "directory" if is_dir else "file",
                        "size": entry.st_size,
                        "mtime": entry.st_mtime,
                    }
                )
        except Exception as e:
            self.errors.append(f"SFTP list error at {path}: {e}")

        return items

    def download_file(self, remote_path: str, local_path: str) -> bool:
        if not self.sftp:
            return False

        try:
            self.sftp.get(remote_path, local_path)
            self.downloaded.append(remote_path)
            return True
        except Exception as e:
            self.errors.append(f"SFTP download error {remote_path}: {e}")
            return False

    def disconnect(self):
        if self.sftp:
            try:
                self.sftp.close()
            except Exception:
                pass
            self.sftp = None
        if self.transport:
            try:
                self.transport.close()
            except Exception:
                pass
            self.transport = None


class NFSHandler(ProtocolHandler):
    """NFS protocol handler using showmount and mount commands."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port = self.port or 2049
        self.mount_point = None
        self.export_path = None

    def connect(self) -> bool:
        """Check NFS exports available on target."""
        try:
            import subprocess

            result = subprocess.run(
                ["showmount", "-e", self.target],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if result.returncode != 0:
                self.errors.append(f"showmount failed: {result.stderr}")
                return False

            # Parse exports
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            if not lines:
                self.errors.append("No NFS exports found")
                return False

            # Use first export or specified path
            self.export_path = (
                self.password or lines[0].split()[0]
            )  # Reuse password field for export path
            return True
        except FileNotFoundError:
            self.errors.append("showmount not installed (apt install nfs-common)")
            return False
        except Exception as e:
            self.errors.append(f"NFS connection failed: {e}")
            return False

    def list_directory(self, path: str = "/") -> List[Dict[str, Any]]:
        """List NFS export contents by mounting temporarily."""
        import subprocess
        import tempfile

        items = []

        # Create temporary mount point
        self.mount_point = tempfile.mkdtemp(prefix="souleyez_nfs_")

        try:
            # Mount the export
            mount_target = f"{self.target}:{self.export_path}"
            result = subprocess.run(
                [
                    "mount",
                    "-t",
                    "nfs",
                    "-o",
                    "ro,nolock",
                    mount_target,
                    self.mount_point,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self.errors.append(f"NFS mount failed: {result.stderr}")
                return items

            # List files
            full_path = os.path.join(self.mount_point, path.lstrip("/"))
            if os.path.isdir(full_path):
                for entry in os.listdir(full_path):
                    entry_path = os.path.join(full_path, entry)
                    try:
                        stat_info = os.stat(entry_path)
                        items.append(
                            {
                                "name": entry,
                                "type": (
                                    "directory" if os.path.isdir(entry_path) else "file"
                                ),
                                "size": stat_info.st_size,
                                "mtime": stat_info.st_mtime,
                            }
                        )
                    except Exception:
                        items.append({"name": entry, "type": "unknown", "size": 0})

        except Exception as e:
            self.errors.append(f"NFS list error: {e}")
        finally:
            # Unmount
            try:
                subprocess.run(
                    ["umount", self.mount_point], capture_output=True, timeout=10
                )
            except Exception:
                pass

        return items

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from NFS share."""
        import shutil
        import subprocess
        import tempfile

        if not self.mount_point:
            self.mount_point = tempfile.mkdtemp(prefix="souleyez_nfs_")

        try:
            # Mount if not already mounted
            mount_target = f"{self.target}:{self.export_path}"
            subprocess.run(
                [
                    "mount",
                    "-t",
                    "nfs",
                    "-o",
                    "ro,nolock",
                    mount_target,
                    self.mount_point,
                ],
                capture_output=True,
                timeout=30,
            )

            # Copy file
            src_path = os.path.join(self.mount_point, remote_path.lstrip("/"))
            if os.path.exists(src_path):
                shutil.copy2(src_path, local_path)
                self.downloaded.append(remote_path)
                return True
            else:
                self.errors.append(f"File not found: {remote_path}")
                return False

        except Exception as e:
            self.errors.append(f"NFS download error {remote_path}: {e}")
            return False
        finally:
            try:
                subprocess.run(
                    ["umount", self.mount_point], capture_output=True, timeout=10
                )
            except Exception:
                pass

    def disconnect(self):
        """Cleanup mount point."""
        import subprocess

        if self.mount_point:
            try:
                subprocess.run(
                    ["umount", self.mount_point], capture_output=True, timeout=10
                )
                os.rmdir(self.mount_point)
            except Exception:
                pass
            self.mount_point = None


class MongoDBHandler(ProtocolHandler):
    """MongoDB protocol handler using pymongo."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port = self.port or 27017
        self.client = None

    def connect(self) -> bool:
        try:
            from pymongo import MongoClient
            from pymongo.errors import ServerSelectionTimeoutError

            # Build connection URI
            if self.username and self.password:
                uri = f"mongodb://{self.username}:{self.password}@{self.target}:{self.port}"
            else:
                uri = f"mongodb://{self.target}:{self.port}"

            self.client = MongoClient(uri, serverSelectionTimeoutMS=self.timeout * 1000)
            # Test connection
            self.client.admin.command("ping")
            return True
        except ImportError:
            self.errors.append("pymongo not installed (pip install pymongo)")
            return False
        except Exception as e:
            self.errors.append(f"MongoDB connection failed: {e}")
            return False

    def list_directory(self, path: str = "/") -> List[Dict[str, Any]]:
        """List MongoDB databases and collections."""
        if not self.client:
            return []

        items = []
        try:
            if path == "/" or path == "":
                # List databases
                for db_name in self.client.list_database_names():
                    db = self.client[db_name]
                    items.append(
                        {
                            "name": db_name,
                            "type": "database",
                            "size": 0,
                            "collections": len(db.list_collection_names()),
                        }
                    )

                # Also get server info
                try:
                    info = self.client.admin.command("serverStatus")
                    items.append(
                        {
                            "name": "__SERVER_INFO__",
                            "type": "info",
                            "size": 0,
                            "data": {
                                "version": info.get("version"),
                                "uptime": info.get("uptime"),
                                "connections": info.get("connections", {}).get(
                                    "current"
                                ),
                            },
                        }
                    )
                except Exception:
                    pass
            else:
                # List collections in database
                db_name = path.strip("/").split("/")[0]
                db = self.client[db_name]
                for coll_name in db.list_collection_names():
                    coll = db[coll_name]
                    items.append(
                        {
                            "name": coll_name,
                            "type": "collection",
                            "size": coll.estimated_document_count(),
                        }
                    )

        except Exception as e:
            self.errors.append(f"MongoDB list error: {e}")

        return items

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Dump MongoDB collection to JSON file."""
        if not self.client:
            return False

        try:
            parts = remote_path.strip("/").split("/")
            if len(parts) < 2:
                self.errors.append("Path must be /database/collection")
                return False

            db_name, coll_name = parts[0], parts[1]
            db = self.client[db_name]
            coll = db[coll_name]

            # Export collection (limit to 10000 docs)
            docs = list(coll.find().limit(10000))

            with open(local_path, "w") as f:
                json.dump(docs, f, indent=2, default=str)

            self.downloaded.append(remote_path)
            return True
        except Exception as e:
            self.errors.append(f"MongoDB dump error {remote_path}: {e}")
            return False

    def disconnect(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None


class ServiceExplorerPlugin(PluginBase):
    """Unified service explorer plugin."""

    name = "Service Explorer"
    tool = "service_explorer"
    category = "discovery_collection"
    HELP = HELP

    # Protocol handler mapping
    PROTOCOLS = {
        "ftp": FTPHandler,
        "tftp": TFTPHandler,
        "redis": RedisHandler,
        "sftp": SFTPHandler,
        "nfs": NFSHandler,
        "mongo": MongoDBHandler,
        "mongodb": MongoDBHandler,  # Alias
    }

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Service Explorer runs in Python, not via external command."""
        return None

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute service exploration."""
        args = args or []

        # Check if any arg is a URL (for preset support)
        # Presets can pass URLs like ftp://anonymous@{target} in args
        for arg in args:
            if "://" in arg:
                target = arg
                args = [a for a in args if a != arg]
                break

        # Parse options
        depth = 3
        download = False
        download_all = False
        timeout = 10

        i = 0
        while i < len(args):
            if args[i] == "--depth" and i + 1 < len(args):
                depth = int(args[i + 1])
                i += 2
            elif args[i] == "--download":
                download = True
                i += 1
            elif args[i] == "--download-all":
                download_all = True
                download = True
                i += 1
            elif args[i] == "--timeout" and i + 1 < len(args):
                timeout = int(args[i + 1])
                i += 2
            else:
                i += 1

        # Parse target URL
        parsed = self._parse_target(target)
        if not parsed:
            self._write_log(log_path, {"error": f"Invalid target format: {target}"})
            return 1

        protocol, host, port, username, password, path = parsed

        # Get handler
        handler_class = self.PROTOCOLS.get(protocol)
        if not handler_class:
            self._write_log(log_path, {"error": f"Unsupported protocol: {protocol}"})
            return 1

        # Create handler and connect
        handler = handler_class(
            target=host,
            username=username,
            password=password,
            port=port,
            timeout=timeout,
        )

        if not handler.connect():
            self._write_log(
                log_path, {"error": "Connection failed", "errors": handler.errors}
            )
            return 1

        # Explore
        try:
            files = handler.explore(path or "/", depth=depth)
            handler.files_found = files

            # Download interesting files if requested
            if download:
                evidence_dir = self._get_evidence_dir(host, protocol)
                files_to_download = (
                    handler.interesting_files if not download_all else files
                )

                for item in files_to_download:
                    if item.get("type") == "file":
                        remote_path = item.get("full_path", item["name"])
                        local_name = (
                            remote_path.replace("/", "_").replace("\\", "_").lstrip("_")
                        )
                        local_path = os.path.join(evidence_dir, local_name)

                        handler.download_file(remote_path, local_path)

            # Write results
            results = {
                "protocol": protocol,
                "target": host,
                "port": port,
                "username": username or "anonymous",
                "files_found": len(files),
                "interesting_files": len(handler.interesting_files),
                "downloaded": len(handler.downloaded),
                "files": files,
                "interesting": handler.interesting_files,
                "downloaded_files": handler.downloaded,
                "errors": handler.errors,
            }

            self._write_log(log_path, results)

        finally:
            handler.disconnect()

        # Return success if we found anything
        if handler.files_found or handler.interesting_files:
            return 0
        elif handler.errors:
            return 1
        else:
            return 0

    def _parse_target(
        self, target: str
    ) -> Optional[Tuple[str, str, int, str, str, str]]:
        """Parse target URL into components."""
        # Handle simple format: protocol://host
        if "://" not in target:
            # Assume it's just a host, try to detect protocol from args
            return None

        try:
            parsed = urlparse(target)
            protocol = parsed.scheme.lower()
            host = parsed.hostname
            port = parsed.port
            username = parsed.username
            password = parsed.password
            path = parsed.path or "/"

            if not host:
                return None

            return (protocol, host, port, username, password, path)
        except Exception:
            return None

    def _get_evidence_dir(self, host: str, protocol: str) -> str:
        """Get or create evidence directory for downloads."""
        base_dir = Path.home() / ".souleyez" / "evidence" / host / protocol
        base_dir.mkdir(parents=True, exist_ok=True)
        return str(base_dir)

    def _write_log(self, log_path: str, data: dict):
        """Write results to log file."""
        if log_path:
            with open(log_path, "w") as f:
                json.dump(data, f, indent=2, default=str)


# Export the plugin (loader expects lowercase 'plugin')
plugin = ServiceExplorerPlugin()
