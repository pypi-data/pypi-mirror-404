"""
<!--
title: "Stamp — Execution Trace Artifact"
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
ai_assistance_details: "AI-assisted drafting of execution trace structure and serialization helpers, with human-defined audit semantics, review, and final control."
dependencies: []
anchors: []
-->
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import json


@dataclass(frozen=True)
class ArtifactTrace:
    artifact: str
    passed: bool
    diagnostic_count: int


@dataclass(frozen=True)
class ExecutionTrace:
    """
    A deterministic, machine-readable record of a Stamp execution.

    NOTE: This artifact intentionally does not embed diagnostics. It captures
    run context + per-artifact summaries suitable for audit, CI, and enforcement.
    """
    trace_version: str
    tool: str
    tool_version: str
    command: str
    schema: str
    started_at: str
    finished_at: str
    exit_code: int
    artifacts: List[ArtifactTrace]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_dict(), indent=2),
            encoding="utf-8",
        )


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
