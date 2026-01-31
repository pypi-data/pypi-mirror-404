"""
<!--
title: "Stamp — Canonical Diagnostic Object Translation"
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
ai_assistance_details: "AI-assisted drafting of diagnostic translation structure and helper routines, with human-defined semantics, ABI guarantees, review, and final control."
dependencies: []
anchors: []
-->
"""

from __future__ import annotations

from typing import Any, Dict, List

from jsonschema.exceptions import ValidationError


# --- Canonical Diagnostic ID Mapping (ABI) -----------------------------

_CANONICAL_ID_MAP: Dict[str, str] = {
    "additionalProperties": "object.no_additional_properties",
    "required": "required.missing",
    "enum": "enum.invalid",
    "type": "type.mismatch",
}


# --- Public API --------------------------------------------------------

def translate_validation_errors_to_cdos(
    *,
    errors: List[ValidationError],
    schema: Dict[str, Any],
    instance: Any,
) -> List[Dict[str, Any]]:
    """
    Translate jsonschema ValidationError objects into Canonical Diagnostic Objects (CDOs).

    This function is schema-agnostic and performs no policy interpretation.
    """
    diagnostics: List[Dict[str, Any]] = []

    for error in errors:
        # --- Conditional normalization ---------------------------------
        if _is_conditional_violation(error):
            diagnostic = {
                "id": "conditional.violation",
                "severity": "error",
                "schema_keyword": error.validator,
                "instance_path": _format_path(error.path),
                "schema_path": _format_path(error.schema_path),
                "message": (
                    "Conditional constraint violated: metadata state is incompatible "
                    "with schema conditional logic."
                ),
                "details": {
                    "condition": error.validator,
                    "note": "See schema conditional (if/then/not) rules for resolution.",
                },
                "fix": None,
            }
            diagnostics.append(diagnostic)
            continue

        # --- Standard diagnostic path ----------------------------------
        diagnostic: Dict[str, Any] = {
            "id": _map_error_to_id(error),
            "severity": "error",
            "schema_keyword": error.validator,
            "instance_path": _format_path(error.path),
            "schema_path": _format_path(error.schema_path),
            "message": error.message,
            "details": _extract_details(error),
            "fix": _infer_fix_capability(error),
        }

        diagnostics.append(diagnostic)

    return diagnostics


# --- Internals ---------------------------------------------------------

def _is_conditional_violation(error: ValidationError) -> bool:
    """
    Detect violations originating from conditional schema logic
    (if / then / else / not / allOf).
    """
    if error.validator == "not":
        return True

    schema_path = list(error.schema_path or [])
    return "allOf" in schema_path or "then" in schema_path or "else" in schema_path


def _map_error_to_id(error: ValidationError) -> str:
    """
    Map a jsonschema validator keyword to a stable, semantic diagnostic ID.
    """
    return _CANONICAL_ID_MAP.get(
        error.validator,
        f"{error.validator}.violation",
    )


def _format_path(path: Any) -> str:
    """
    Convert a jsonschema path iterator into a JSON Pointer–like string.
    """
    if not path:
        return ""
    return "/" + "/".join(str(p) for p in path)


def _extract_details(error: ValidationError) -> Dict[str, Any]:
    """
    Extract structured details from a ValidationError where possible.
    """
    details: Dict[str, Any] = {}

    if error.validator == "required":
        # Message format: "'field' is a required property"
        parts = error.message.split("'")
        if len(parts) >= 2:
            details["missing_property"] = parts[1]

    elif error.validator == "enum":
        details["allowed_values"] = error.validator_value
        details["value"] = error.instance

    elif error.validator == "type":
        details["expected_type"] = error.validator_value
        details["actual_type"] = type(error.instance).__name__
        details["value"] = error.instance

    return details


def _infer_fix_capability(error: ValidationError) -> Any:
    """
    Determine whether a violation is mechanically fixable.
    This is intentionally conservative.
    """
    if error.validator == "additionalProperties":
        # Message format: "Additional properties are not allowed ('foo' was unexpected)"
        parts = error.message.split("'")
        key = parts[1] if len(parts) >= 2 else None

        return {
            "fixable": True,
            "strategy": "prune",
            "parameters": {
                "key": key,
            },
        }

    return None
