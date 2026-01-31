"""
<!--
title: "Stamp — Schema Loading and Resolution Module"
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
ai_assistance_details: "AI-assisted drafting of schema loading pathways and resolution semantics, with human-defined trust boundaries, review, and final control."
dependencies: []
anchors: []
-->
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Union
import json
import urllib.request


@dataclass(frozen=True)
class ResolvedSchema:
    source: str          # local | remote | inline
    identifier: str
    uri: Optional[str]
    schema: dict


def load_schema(source: Union[Path, str, dict]) -> ResolvedSchema:
    """
    Load a JSON Schema from a local file, remote URL, or inline dict.

    No validation, no ref resolution, no trust assumptions.
    """

    # Inline schema
    if isinstance(source, dict):
        identifier = source.get("$id", "inline-schema")
        return ResolvedSchema(
            source="inline",
            identifier=identifier,
            uri=source.get("$id"),
            schema=source,
        )

    # Remote URL (string)
    if isinstance(source, str) and source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source) as response:
            text = response.read().decode("utf-8")
        data = json.loads(text)
        identifier = data.get("$id", source)
        return ResolvedSchema(
            source="remote",
            identifier=identifier,
            uri=source,
            schema=data,
        )

    # Local filesystem path (Path or str)
    if isinstance(source, str):
        source = Path(source)

    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
        data = json.loads(text)
        identifier = data.get("$id", source.name)
        return ResolvedSchema(
            source="local",
            identifier=identifier,
            uri=data.get("$id"),
            schema=data,
        )

    raise ValueError(f"Unsupported schema source: {source}")
