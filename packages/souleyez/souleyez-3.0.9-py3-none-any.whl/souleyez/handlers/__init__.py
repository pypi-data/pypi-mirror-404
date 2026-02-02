#!/usr/bin/env python3
"""
Tool handlers package.

Each tool has a handler class that consolidates:
- Parsing logic (from result_handler.py)
- Display logic (from interactive.py)
- Capability flags (replaces manual lists)

Auto-discovery: Handlers are registered automatically when imported.
"""
