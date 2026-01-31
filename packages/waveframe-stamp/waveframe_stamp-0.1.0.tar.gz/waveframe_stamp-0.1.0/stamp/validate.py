"""
<!--
title: "Stamp — Metadata Validation and Diagnostic Emission Module"
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
ai_assistance_details: "AI-assisted drafting of validation flow and diagnostic translation integration, with human-defined semantics, review, and final control."
dependencies: []
anchors: []
-->
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft202012Validator

from stamp.cdo import translate_validation_errors_to_cdos  # type: ignore
from stamp.extract import ExtractedMetadata
from stamp.schema import ResolvedSchema


@dataclass(frozen=True)
class ValidationResult:
    artifact_path: Optional[Path]
    schema_id: str
    diagnostics: List[Dict[str, Any]]


def _validate_instance(instance: Any, schema: Dict[str, Any]) -> List[Any]:
    """
    Run Draft 2020-12 validation and collect ALL errors.
    Returns raw jsonschema error objects.
    """
    validator = Draft202012Validator(schema)
    return list(validator.iter_errors(instance))


def validate_artifact(
    *,
    extracted: ExtractedMetadata,
    resolved_schema: ResolvedSchema,
) -> ValidationResult:
    """
    Validate extracted metadata against a resolved schema and emit
    Canonical Diagnostic Objects (CDOs).
    """
    instance = extracted.metadata

    raw_errors = _validate_instance(
        instance=instance,
        schema=resolved_schema.schema,
    )

    diagnostics = translate_validation_errors_to_cdos(
        errors=raw_errors,
        instance=instance,
        schema=resolved_schema.schema,
    )

    return ValidationResult(
        artifact_path=extracted.artifact_path,
        schema_id=resolved_schema.identifier,
        diagnostics=diagnostics,
    )
