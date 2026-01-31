"""
<!--
title: "Stamp — Validation Command Interface"
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
ai_assistance_details: "AI-assisted drafting of validation command structure, trace handling, and reporting logic, with human-authored semantics, review, and final control."
dependencies: []
anchors: []
-->
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import typer

from stamp.extract import extract_metadata
from stamp.schema import load_schema
from stamp.validate import validate_artifact, ValidationResult
from stamp.fix import build_fix_proposals
from stamp.remediation import build_remediation_summary
from stamp.discovery import discover_artifacts
from stamp.trace import (
    ExecutionTrace,
    ArtifactTrace,
    now_utc,
)
from stamp.trace_schema import validate_trace


# -----------------------------
# Tool identity (single source)
# -----------------------------

STAMP_TOOL_NAME = "stamp"
STAMP_TOOL_VERSION = "0.1.0"
TRACE_VERSION = "0.0.1"


app = typer.Typer(
    help="Validate artifacts against a metadata schema."
)


def _emit(obj: object) -> None:
    """
    Emit structured CLI output as explicit JSON.

    This is the canonical output path for all validation results.
    """
    typer.echo(json.dumps(obj, indent=2))


def _is_passed(result: ValidationResult) -> bool:
    """
    A validation passes iff there are no error-severity diagnostics.
    """
    return not any(d.get("severity") == "error" for d in result.diagnostics)


def _write_validated_trace(trace: ExecutionTrace, path: Path) -> None:
    """
    Validate a trace artifact against the trace schema before writing.

    Trace artifacts are immutable execution evidence and are NOT
    subject to metadata governance.
    """
    errors = validate_trace(trace.to_dict())
    if errors:
        typer.secho(
            "Trace validation failed; trace artifact was not written.",
            fg=typer.colors.RED,
            err=True,
        )
        for e in errors:
            typer.secho(
                f"- {e['message']} (at {e['instance_path']})",
                fg=typer.colors.RED,
                err=True,
            )
        raise typer.Exit(code=2)

    trace.write_json(path)


# -----------------------------
# Single-artifact validation
# -----------------------------

@app.command("run")
def run(
    artifact: Path,
    schema: Path = typer.Option(..., "--schema"),
    summary: bool = typer.Option(False, "--summary"),
    remediation: bool = typer.Option(False, "--remediation"),
    fix_proposals: bool = typer.Option(False, "--fix-proposals"),
    trace_out: Optional[Path] = typer.Option(None, "--trace-out"),
):
    """
    Validate a single artifact.

    Single-artifact validation assumes explicit user intent and does
    not apply governance discovery rules.
    """
    started_at = now_utc()

    extracted = extract_metadata(artifact)
    resolved_schema = load_schema(schema)

    result = validate_artifact(
        extracted=extracted,
        resolved_schema=resolved_schema,
    )

    passed = _is_passed(result)
    exit_code = 0 if passed else 1

    if fix_proposals:
        _emit(build_fix_proposals(result))
    elif remediation:
        _emit(build_remediation_summary(result))
    elif summary:
        _emit(
            {
                "artifact": str(artifact),
                "schema": str(schema),
                "passed": passed,
                "diagnostic_count": len(result.diagnostics),
            }
        )
    else:
        _emit(result.diagnostics)

    finished_at = now_utc()

    if trace_out is not None:
        trace = ExecutionTrace(
            trace_version=TRACE_VERSION,
            tool=STAMP_TOOL_NAME,
            tool_version=STAMP_TOOL_VERSION,
            command="validate run",
            schema=str(schema),
            started_at=started_at,
            finished_at=finished_at,
            exit_code=exit_code,
            artifacts=[
                ArtifactTrace(
                    artifact=str(artifact),
                    passed=passed,
                    diagnostic_count=len(result.diagnostics),
                )
            ],
        )
        _write_validated_trace(trace, trace_out)

    raise typer.Exit(code=exit_code)


# -----------------------------
# Repository validation
# -----------------------------

@app.command("repo")
def repo(
    root: Path,
    schema: Path = typer.Option(..., "--schema"),
    trace_out: Optional[Path] = typer.Option(None, "--trace-out"),
):
    """
    Validate all governed artifacts under a root path.

    An artifact is considered governed iff it explicitly declares metadata.
    Files without metadata are discovered but intentionally ignored.
    """
    started_at = now_utc()

    resolved_schema = load_schema(schema)
    artifacts = discover_artifacts([root])

    artifact_traces: List[ArtifactTrace] = []
    passed_count = 0
    failed_count = 0

    for artifact in artifacts:
        extracted = extract_metadata(artifact.path)

        # GOVERNANCE GATE:
        # Only artifacts that explicitly declare metadata are governed
        if extracted.metadata is None:
            continue

        result = validate_artifact(
            extracted=extracted,
            resolved_schema=resolved_schema,
        )

        passed = _is_passed(result)

        artifact_traces.append(
            ArtifactTrace(
                artifact=str(artifact.path),
                passed=passed,
                diagnostic_count=len(result.diagnostics),
            )
        )

        if passed:
            passed_count += 1
        else:
            failed_count += 1

    _emit(
        {
            "root": str(root),
            "total_artifacts": len(artifact_traces),
            "passed": passed_count,
            "failed": failed_count,
        }
    )

    finished_at = now_utc()
    exit_code = 0 if failed_count == 0 else 1

    if trace_out is not None:
        trace = ExecutionTrace(
            trace_version=TRACE_VERSION,
            tool=STAMP_TOOL_NAME,
            tool_version=STAMP_TOOL_VERSION,
            command="validate repo",
            schema=str(schema),
            started_at=started_at,
            finished_at=finished_at,
            exit_code=exit_code,
            artifacts=artifact_traces,
        )
        _write_validated_trace(trace, trace_out)

    raise typer.Exit(code=exit_code)
