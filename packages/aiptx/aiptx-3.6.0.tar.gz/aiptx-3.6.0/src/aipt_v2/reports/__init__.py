"""
AIPT Report Generation

Generates professional pentest reports in multiple formats:
- HTML (standalone, styled)
- Markdown (for documentation)
- JSON (for integration)
"""

from .generator import ReportGenerator, ReportConfig
from .html_report import generate_html_report

__all__ = [
    "ReportGenerator",
    "ReportConfig",
    "generate_html_report",
]
