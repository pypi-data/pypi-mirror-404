#!/usr/bin/env python3
"""
Simple plugin loader for souleyez (L1).
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any, Dict


def _safe_import_module(fullname: str):
    """Import module and return it, or None on error."""
    try:
        return importlib.import_module(fullname)
    except Exception as e:
        try:
            print(f"[plugin loader] could not import {fullname}: {e}")
        except Exception:
            pass
        return None


def discover_plugins() -> Dict[str, Any]:
    """
    Return mapping of plugin_key -> plugin_object
    plugin_key is plugin.tool if set and truthy, otherwise module name.
    """
    plugins = {}

    try:
        pkg = importlib.import_module("souleyez.plugins")
    except Exception as e:
        print("[plugin loader] cannot import souleyez.plugins:", e)
        return plugins

    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        if name in ("plugin_base", "plugin_template", "__init__"):
            continue

        full = f"souleyez.plugins.{name}"
        mod = _safe_import_module(full)
        if not mod:
            continue

        plugin = getattr(mod, "plugin", None)
        if not plugin:
            continue

        try:
            module_help = getattr(mod, "HELP", None)
            if module_help and not getattr(plugin, "HELP", None):
                plugin.HELP = module_help
        except Exception:
            pass

        try:
            if not getattr(plugin, "name", None):
                if module_help and isinstance(module_help, dict):
                    plugin.name = module_help.get("name") or name
                else:
                    plugin.name = name
        except Exception:
            pass

        try:
            if not getattr(plugin, "tool", None):
                if module_help and isinstance(module_help, dict):
                    plugin.tool = module_help.get("tool") or name
                else:
                    plugin.tool = getattr(plugin, "name", name)
        except Exception:
            pass

        try:
            if not getattr(plugin, "category", None):
                if module_help and isinstance(module_help, dict):
                    plugin.category = module_help.get("category") or "network"
                else:
                    plugin.category = "network"
        except Exception:
            pass

        # Use module name as key for consistency with tool_order/desc_map/name_map
        # The module name (e.g., 'dns_hijack') is more descriptive than the tool
        # name (e.g., 'dig') and allows multiple plugins using the same tool
        key = name.lower()

        plugins[key] = plugin

    return plugins


load = discover_plugins
