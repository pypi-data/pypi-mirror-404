"""
<!--
title: "Stamp — Remediation Summary and Action Classification Module"
filetype: "operational"
type: "specification"
domain: "methodology"
version: "0.1.0"
doi: "TBD-0.1.0"
status: "Active"
created: "2026-01-16"
updated: "2026-01-29"
author:
  name: "Shawn C. Wright"
  email: "swright@waveframelabs.org"
  orcid: "https://orcid.org/0009-0006-6043-9295"
maintainer:
  name: "Waveframe Labs"
  url: "https://waveframelabs.org"
license: "Apache-2.0"
copyright:
  holder: "Waveframe Labs"
  year: "2026"
ai_assisted: "partial"
ai_assistance_details: "AI-assisted drafting of remediation classification logic and summary structure, with human-defined decision taxonomy, review, and final control."
dependencies: []
anchors: []
-->
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


# -----------------------------
# Action classification helpers
# -----------------------------

def _classify_action_type(diagnostic: Dict[str, Any]) -> str:
    """
    Classify what kind of human action is required for a diagnostic.

    This is intentionally deterministic and schema-agnostic.
    """
    rule_id = diagnostic.get("id")
    schema_keyword = diagnostic.get("schema_keyword")

    # Conditional / disclosure logic
    if schema_keyword in {"if", "then", "else", "not", "allOf", "anyOf", "oneOf"}:
        return "disclosure_decision"

    # Governance-controlled enums
    if rule_id == "enum.invalid":
        return "governance_decision"

    # Missing required fields or malformed values
    if rule_id in {
        "required.missing",
        "pattern.violation",
        "type.mismatch",
        "format.violation",
    }:
        return "author_decision"

    # Additional properties (may be auto-fixable)
    if rule_id == "object.no_additional_properties":
        fix = diagnostic.get("fix")
        if fix and fix.get("fixable"):
            return "auto_fixable"
        return "author_decision"

    # Conservative fallback
    return "author_decision"


def _extract_field_path(diagnostic: Dict[str, Any]) -> str:
    """
    Normalize instance_path into a human-readable field path.
    """
    path = diagnostic.get("instance_path", "")
    if not path:
        return "<root>"

    # instance_path is JSON Pointer–like (/a/b/c)
    return path.lstrip("/").replace("/", ".")


# -----------------------------
# Public API
# -----------------------------

def build_remediation_summary(
    *,
    diagnostics: List[Dict[str, Any]],
    artifact: Path,
    schema: Path,
    fix_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a human-action remediation summary from validation diagnostics
    and optional fix results.

    This does NOT enforce policy.
    This does NOT mutate artifacts.
    It only explains what remains and why.
    """

    passed = len(diagnostics) == 0

    auto_fix_applied = 0
    if fix_result:
        auto_fix_applied = fix_result.get("applied_fix_count", 0)

    human_items: List[Dict[str, Any]] = []

    for d in diagnostics:
        action_type = _classify_action_type(d)

        # Skip auto-fixable issues if fixes were already applied
        if action_type == "auto_fixable" and fix_result:
            continue

        human_items.append(
            {
                "field": _extract_field_path(d),
                "rule": d.get("schema_keyword"),
                "reason": d.get("message"),
                "action_type": action_type,
                "severity": d.get("severity"),
            }
        )

    blocking = any(
        item["severity"] == "error"
        for item in human_items
    )

    return {
        "artifact": str(artifact),
        "schema": str(schema),
        "validation": {
            "passed": passed,
            "diagnostic_count": len(diagnostics),
        },
        "auto_fix": {
            "applied": auto_fix_applied,
            "skipped": len(diagnostics) - auto_fix_applied,
        },
        "human_action_required": {
            "required": not passed,
            "blocking": blocking,
            "item_count": len(human_items),
            "items": human_items,
        },
    }
