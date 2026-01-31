"""
<!--
title: "Stamp — Fix Command Interface"
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
ai_assistance_details: "AI-assisted drafting of CLI command structure and validation flow, with human-authored logic, review, and final control."
dependencies: []
anchors: []
-->
"""

from __future__ import annotations

import typer
from pathlib import Path

from stamp.extract import extract_metadata
from stamp.schema import load_schema
from stamp.validate import validate_artifact
from stamp.fix import apply_fix_proposals

app = typer.Typer(add_completion=False, help="Apply safe fixes to artifacts.")


@app.command("apply")
def apply(
    artifact: Path = typer.Argument(..., exists=True, readable=True),
    schema: Path = typer.Option(..., "--schema", exists=True, readable=True),
    out: Path = typer.Option(..., "--out", help="Output path for fixed artifact."),
) -> None:
    """
    Apply safe fix proposals to an artifact.

    This command:
      - re-validates the artifact
      - applies ONLY fixable strategies
      - never mutates in place
    """

    extracted = extract_metadata(artifact)
    resolved_schema = load_schema(schema)

    result = validate_artifact(
        extracted=extracted,
        resolved_schema=resolved_schema,
    )

    apply_fix_proposals(
        artifact=artifact,
        diagnostics=result.diagnostics,
        out_path=out,
    )

    typer.echo(f"✔ Fixed artifact written to {out}")
