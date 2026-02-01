#!/usr/bin/env python3
import csv
import json
from pathlib import Path

from .utils import HISTORY_FILE, ensure_dirs, read_json, timestamp_str, write_json

# Export directory for JSON/CSV exports
EXPORT_DIR = Path.home() / ".souleyez" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_history():
    ensure_dirs()
    return read_json(HISTORY_FILE)


def add_history_entry(
    target, args, label, logpath, xmlpath=None, tool="nmap", summary=None
):
    """
    Add an entry to the history.
    """
    ensure_dirs()
    h = load_history()
    entry = {
        "ts": timestamp_str(),
        "tool": tool,
        "target": target,
        "args": args,
        "label": label,
        "log": str(logpath),
        "xml": str(xmlpath) if xmlpath else None,
        "summary": summary if isinstance(summary, dict) else None,
    }
    h.insert(0, entry)
    write_json(HISTORY_FILE, h[:200])
    return entry


def get_tools():
    """
    Return a sorted list of unique tool names present in history.
    """
    h = load_history()
    tools = sorted({(e.get("tool") or "").lower() for e in h if e.get("tool")})
    return tools


def _safe_filename_component(s):
    s = str(s or "")
    return "".join(c if (c.isalnum() or c in (".", "-", "_")) else "_" for c in s)


def _make_export_name(entry, ext):
    ts = entry.get("ts") or timestamp_str()
    tool = _safe_filename_component(entry.get("tool") or "tool")
    target = _safe_filename_component(entry.get("target") or "target")
    label = _safe_filename_component(entry.get("label") or "")
    base = f"{ts}_{tool}_{target}"
    if label:
        base += f"_{label}"
    return EXPORT_DIR / (base + "." + ext)


def export_entry_json(entry):
    path = _make_export_name(entry, "json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)
    return path


def export_entry_csv(entry):
    path = _make_export_name(entry, "csv")
    per_host = []
    summary = entry.get("summary") or {}
    if isinstance(summary, dict):
        per_host = summary.get("per_host") or []
    if not per_host:
        per_host = [{"addr": "", "up": None, "open": summary.get("open_ports", 0)}]

    with open(path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "timestamp",
                "tool",
                "target",
                "label",
                "host",
                "up",
                "open_ports",
                "log",
                "xml",
            ]
        )
        for h in per_host:
            writer.writerow(
                [
                    entry.get("ts", ""),
                    entry.get("tool", ""),
                    entry.get("target", ""),
                    entry.get("label", ""),
                    h.get("addr", ""),
                    bool(h.get("up")) if h.get("up") is not None else "",
                    h.get("open", 0),
                    entry.get("log", ""),
                    entry.get("xml", ""),
                ]
            )
    return path
