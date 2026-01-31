"""
<!--
title: "Stamp — Metadata Extraction Module"
filetype: "operational"
type: "specification"
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
ai_assistance_details: "AI-assisted drafting of metadata extraction logic and precedence rules, with human-defined contracts, review, and final validation."
dependencies: []
anchors: []
-->
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import ruamel.yaml


@dataclass(frozen=True)
class ExtractedMetadata:
    artifact_path: Path
    metadata: Optional[Any]
    raw_block: Optional[str]
    error: Optional[str]


_yaml = ruamel.yaml.YAML(typ="safe")


def extract_metadata(path: Path) -> ExtractedMetadata:
    """
    Extract metadata from an artifact.

    Deterministic priority rules:

      1. Markdown YAML frontmatter (if present)
         - If valid: returned immediately
         - If malformed: error returned, no fallback

      2. HTML-comment metadata
         - Raw or docstring-wrapped
         - Used only if no frontmatter exists

      3. No metadata
    """

    # Markdown frontmatter has absolute priority
    if path.suffix.lower() == ".md":
        md_result = _extract_markdown_frontmatter(path)

        # Frontmatter exists (valid or invalid)
        if md_result.raw_block is not None or md_result.error is not None:
            return md_result

    # Fallback: HTML comment metadata (raw or docstring-wrapped)
    html_result = _extract_html_comment_metadata(path)
    if html_result.metadata is not None or html_result.error is not None:
        return html_result

    # No metadata found
    return ExtractedMetadata(
        artifact_path=path,
        metadata=None,
        raw_block=None,
        error=None,
    )


def _extract_markdown_frontmatter(path: Path) -> ExtractedMetadata:
    """
    Extract YAML frontmatter from a Markdown file.

    Frontmatter must be the first block in the file.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return ExtractedMetadata(
            artifact_path=path,
            metadata=None,
            raw_block=None,
            error=str(e),
        )

    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        return ExtractedMetadata(
            artifact_path=path,
            metadata=None,
            raw_block=None,
            error=None,
        )

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            raw_block = "\n".join(lines[1:i])
            try:
                data = _yaml.load(raw_block)
            except Exception as e:
                return ExtractedMetadata(
                    artifact_path=path,
                    metadata=None,
                    raw_block=raw_block,
                    error=str(e),
                )

            return ExtractedMetadata(
                artifact_path=path,
                metadata=data,
                raw_block=raw_block,
                error=None,
            )

    return ExtractedMetadata(
        artifact_path=path,
        metadata=None,
        raw_block=None,
        error="Unterminated YAML frontmatter block",
    )


def _extract_html_comment_metadata(path: Path) -> ExtractedMetadata:
    """
    Extract metadata from an HTML comment block at the top of a file.

    Supported forms (must be first non-whitespace content):

      <!-- ... -->

      \"\"\"
      <!-- ... -->
      \"\"\"

      '''
      <!-- ... -->
      '''
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return ExtractedMetadata(
            artifact_path=path,
            metadata=None,
            raw_block=None,
            error=str(e),
        )

    stripped = text.lstrip()

    # Unwrap top-level docstring if present
    for quote in ('"""', "'''"):
        if stripped.startswith(quote):
            end = stripped.find(quote, len(quote))
            if end == -1:
                return ExtractedMetadata(
                    artifact_path=path,
                    metadata=None,
                    raw_block=None,
                    error="Unterminated docstring metadata block",
                )
            stripped = stripped[len(quote):end].lstrip()
            break

    # Expect HTML comment at top
    if not stripped.startswith("<!--"):
        return ExtractedMetadata(
            artifact_path=path,
            metadata=None,
            raw_block=None,
            error=None,
        )

    end_idx = stripped.find("-->")
    if end_idx == -1:
        return ExtractedMetadata(
            artifact_path=path,
            metadata=None,
            raw_block=None,
            error="Unterminated HTML comment metadata block",
        )

    raw_block = stripped[4:end_idx].strip()

    try:
        data = _yaml.load(raw_block)
    except Exception as e:
        return ExtractedMetadata(
            artifact_path=path,
            metadata=None,
            raw_block=raw_block,
            error=str(e),
        )

    return ExtractedMetadata(
        artifact_path=path,
        metadata=data,
        raw_block=raw_block,
        error=None,
    )
