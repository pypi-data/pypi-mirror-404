"""
<!--
title: "Stamp — Command Line Interface Entry Point"
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
ai_assistance_details: "AI-assisted drafting of CLI composition and command wiring, with human-defined structure, semantics, and final validation."
dependencies: []
anchors: []
-->
"""

from __future__ import annotations

import typer

from stamp.cli.validate import app as validate_app
from stamp.cli.fix import app as fix_app

cli = typer.Typer(add_completion=False, help="Stamp CLI — schema validation and remediation tools.")

cli.add_typer(validate_app, name="validate")
cli.add_typer(fix_app, name="fix")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
