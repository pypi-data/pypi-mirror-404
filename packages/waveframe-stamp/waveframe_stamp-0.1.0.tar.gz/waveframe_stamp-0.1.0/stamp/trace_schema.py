"""
<!--
title: "Stamp — Trace Artifact Schema"
filetype: "schema"
type: "normative"
domain: "methodology"
version: "0.1.0"
doi: "TBD-0.1.0"
status: "Active"
created: "2026-01-27"
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
ai_assistance_details: "AI-assisted drafting of the execution trace JSON Schema and validation scaffolding, with human-defined ABI constraints, review, and final control."
dependencies: []
anchors: []
-->
"""

from __future__ import annotations

from typing import Any, Dict, List

from jsonschema import Draft202012Validator


TRACE_SCHEMA_VERSION = "0.0.1"
TRACE_SCHEMA_ID = "https://waveframelabs.org/schemas/stamp-trace-0.0.1.json"

STAMP_TRACE_SCHEMA_V0_0_1: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": TRACE_SCHEMA_ID,
    "title": "Stamp Trace Schema v0.0.1",
    "description": "Schema for deterministic Stamp execution trace artifacts.",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "trace_version",
        "tool",
        "tool_version",
        "command",
        "schema",
        "started_at",
        "finished_at",
        "exit_code",
        "artifacts",
    ],
    "properties": {
        "trace_version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
        "tool": {"type": "string", "minLength": 1},
        "tool_version": {"type": "string", "minLength": 1},
        "command": {"type": "string", "minLength": 1},
        "schema": {"type": "string", "minLength": 1},
        "started_at": {"type": "string", "minLength": 1},
        "finished_at": {"type": "string", "minLength": 1},
        "exit_code": {"type": "integer"},
        "artifacts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["artifact", "passed", "diagnostic_count"],
                "properties": {
                    "artifact": {"type": "string", "minLength": 1},
                    "passed": {"type": "boolean"},
                    "diagnostic_count": {"type": "integer", "minimum": 0},
                },
            },
        },
    },
}


def validate_trace(trace: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate a trace dict against the v0.0.1 schema.

    Returns a list of jsonschema error objects (empty list means valid).
    """
    validator = Draft202012Validator(STAMP_TRACE_SCHEMA_V0_0_1)
    errors = sorted(validator.iter_errors(trace), key=lambda e: (list(e.path), e.message))
    return [
        {
            "message": e.message,
            "instance_path": "/" + "/".join(str(p) for p in e.path),
            "schema_path": "/" + "/".join(str(p) for p in e.schema_path),
            "validator": e.validator,
        }
        for e in errors
    ]
