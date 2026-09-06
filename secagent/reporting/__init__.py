"""Reporting module for SARIF and Markdown outputs."""

from secagent.reporting.sarif import generate_sarif_report
from secagent.reporting.markdown import generate_markdown_summary

__all__ = ["generate_sarif_report", "generate_markdown_summary"]
