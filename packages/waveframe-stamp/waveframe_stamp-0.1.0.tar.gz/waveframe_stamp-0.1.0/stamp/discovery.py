"""
<!--
title: "Stamp — Artifact Discovery Module"
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
ai_assistance_details: "AI-assisted drafting of artifact discovery logic and structural traversal rules, with human-defined constraints, review, and final validation."
dependencies: []
anchors: []
-->
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Union


EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    "archive",
    "traces",
    ".stamp",
}

EXCLUDED_FILENAMES = {
    "stamp-validation-trace.json",
}

EXCLUDED_SUFFIXES = (
    "-trace.json",
)


@dataclass(frozen=True)
class DiscoveredArtifact:
    """
    Represents a filesystem-discovered artifact candidate.

    Discovery is purely structural:
    - no parsing
    - no validation
    - no schema awareness

    This defines the epistemic boundary of governable artifacts.
    """
    path: Path
    size_bytes: int


def _is_excluded(path: Path) -> bool:
    """
    Determine whether a path should be excluded from discovery.

    Exclusions are deterministic and governance-driven.
    """
    # Directory-based exclusions
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True

    name = path.name

    # Exact filename exclusions
    if name in EXCLUDED_FILENAMES:
        return True

    # Suffix-based exclusions (e.g. execution traces)
    if any(name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES):
        return True

    return False


def discover_artifacts(
    roots: Iterable[Union[str, Path]]
) -> List[DiscoveredArtifact]:
    """
    Recursively discover candidate artifacts starting from given root paths.

    This function performs filesystem traversal only.
    It does not parse files, inspect contents, or apply schemas.

    Exclusion rules define the universe of governable artifacts.
    """
    artifacts: List[DiscoveredArtifact] = []

    for root in roots:
        root_path = Path(root).resolve()

        # Single file root
        if root_path.is_file():
            if _is_excluded(root_path):
                continue
            try:
                artifacts.append(
                    DiscoveredArtifact(
                        path=root_path,
                        size_bytes=root_path.stat().st_size,
                    )
                )
            except OSError:
                continue
            continue

        # Non-directory root
        if not root_path.is_dir():
            continue

        # Directory traversal
        for path in root_path.rglob("*"):
            if not path.is_file():
                continue

            if _is_excluded(path):
                continue

            try:
                size = path.stat().st_size
            except OSError:
                continue

            artifacts.append(
                DiscoveredArtifact(
                    path=path,
                    size_bytes=size,
                )
            )

    return artifacts
