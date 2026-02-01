"""
AIPT Report Generator

Generates professional pentest reports from pipeline results.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models.findings import Finding, Severity
from ..models.phase_result import PipelineResult


logger = logging.getLogger(__name__)


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    # Report metadata
    client_name: str = "Client"
    project_name: str = "Security Assessment"
    assessor_name: str = "AIPT"

    # Output settings
    output_dir: Path = field(default_factory=lambda: Path("./reports"))
    formats: list[str] = field(default_factory=lambda: ["html", "json", "markdown"])

    # Content settings
    include_evidence: bool = True
    include_remediation: bool = True
    include_ai_reasoning: bool = True
    redact_sensitive: bool = False


@dataclass
class ReportData:
    """Data structure for report generation"""
    # Metadata
    scan_id: str
    target: str
    generated_at: datetime
    config: ReportConfig

    # Findings by severity
    critical_findings: list[Finding] = field(default_factory=list)
    high_findings: list[Finding] = field(default_factory=list)
    medium_findings: list[Finding] = field(default_factory=list)
    low_findings: list[Finding] = field(default_factory=list)
    info_findings: list[Finding] = field(default_factory=list)

    # Statistics
    total_findings: int = 0
    unique_vuln_types: int = 0
    sources: list[str] = field(default_factory=list)

    # AI-specific
    ai_findings_count: int = 0
    ai_reasoning_samples: list[str] = field(default_factory=list)

    @classmethod
    def from_pipeline_result(
        cls,
        result: PipelineResult,
        config: ReportConfig,
    ) -> "ReportData":
        """Create ReportData from pipeline result"""
        findings = result.get_all_findings()

        # Group by severity
        critical = [f for f in findings if f.severity == Severity.CRITICAL]
        high = [f for f in findings if f.severity == Severity.HIGH]
        medium = [f for f in findings if f.severity == Severity.MEDIUM]
        low = [f for f in findings if f.severity == Severity.LOW]
        info = [f for f in findings if f.severity == Severity.INFO]

        # Extract unique sources
        sources = list(set(f.source for f in findings))

        # Count AI findings
        ai_findings = [f for f in findings if f.source == "aipt" or f.ai_reasoning]
        ai_reasoning = [f.ai_reasoning for f in ai_findings if f.ai_reasoning][:5]

        # Unique vulnerability types
        unique_types = len(set(f.vuln_type for f in findings))

        return cls(
            scan_id=result.scan_id,
            target=result.target,
            generated_at=datetime.utcnow(),
            config=config,
            critical_findings=critical,
            high_findings=high,
            medium_findings=medium,
            low_findings=low,
            info_findings=info,
            total_findings=len(findings),
            unique_vuln_types=unique_types,
            sources=sources,
            ai_findings_count=len(ai_findings),
            ai_reasoning_samples=ai_reasoning,
        )

    def get_severity_counts(self) -> dict[str, int]:
        return {
            "critical": len(self.critical_findings),
            "high": len(self.high_findings),
            "medium": len(self.medium_findings),
            "low": len(self.low_findings),
            "info": len(self.info_findings),
        }

    def get_risk_score(self) -> int:
        """Calculate overall risk score (0-100)"""
        score = 0
        score += len(self.critical_findings) * 25
        score += len(self.high_findings) * 15
        score += len(self.medium_findings) * 8
        score += len(self.low_findings) * 2
        return min(100, score)

    def get_risk_rating(self) -> str:
        """Get risk rating based on score"""
        score = self.get_risk_score()
        if score >= 75:
            return "Critical"
        elif score >= 50:
            return "High"
        elif score >= 25:
            return "Medium"
        elif score > 0:
            return "Low"
        return "Informational"


class ReportGenerator:
    """
    Generates professional pentest reports.

    Example:
        generator = ReportGenerator(config)
        paths = await generator.generate(pipeline_result)
        print(f"Reports saved to: {paths}")
    """

    def __init__(self, config: ReportConfig | None = None):
        self.config = config or ReportConfig()

    async def generate(self, result: PipelineResult) -> dict[str, Path]:
        """
        Generate reports in all configured formats.

        Args:
            result: Pipeline result with findings

        Returns:
            Dictionary of format -> file path
        """
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare report data
        data = ReportData.from_pipeline_result(result, self.config)

        generated_files = {}

        if "html" in self.config.formats:
            path = await self._generate_html(data)
            generated_files["html"] = path

        if "json" in self.config.formats:
            path = await self._generate_json(data, result)
            generated_files["json"] = path

        if "markdown" in self.config.formats:
            path = await self._generate_markdown(data)
            generated_files["markdown"] = path

        logger.info(f"Generated {len(generated_files)} report(s)")
        return generated_files

    async def _generate_html(self, data: ReportData) -> Path:
        """Generate HTML report"""
        from .html_report import generate_html_report

        html_content = generate_html_report(data)

        filename = f"aipt3_report_{data.scan_id}_{data.generated_at.strftime('%Y%m%d_%H%M%S')}.html"
        path = self.config.output_dir / filename

        path.write_text(html_content)
        logger.info(f"Generated HTML report: {path}")

        return path

    async def _generate_json(self, data: ReportData, result: PipelineResult) -> Path:
        """Generate JSON report"""
        json_data = {
            "metadata": {
                "scan_id": data.scan_id,
                "target": data.target,
                "generated_at": data.generated_at.isoformat(),
                "client_name": data.config.client_name,
                "project_name": data.config.project_name,
                "assessor": data.config.assessor_name,
            },
            "summary": {
                "total_findings": data.total_findings,
                "severity_counts": data.get_severity_counts(),
                "risk_score": data.get_risk_score(),
                "risk_rating": data.get_risk_rating(),
                "unique_vuln_types": data.unique_vuln_types,
                "sources": data.sources,
                "ai_findings_count": data.ai_findings_count,
            },
            "findings": [f.to_dict() for f in result.get_all_findings()],
            "phases": {
                phase.value: {
                    "status": pr.status.value,
                    "duration": pr.duration_seconds,
                    "findings_count": len(pr.findings),
                    "errors": pr.errors,
                }
                for phase, pr in result.phase_results.items()
            },
        }

        filename = f"aipt3_report_{data.scan_id}_{data.generated_at.strftime('%Y%m%d_%H%M%S')}.json"
        path = self.config.output_dir / filename

        path.write_text(json.dumps(json_data, indent=2, default=str))
        logger.info(f"Generated JSON report: {path}")

        return path

    async def _generate_markdown(self, data: ReportData) -> Path:
        """Generate Markdown report"""
        lines = [
            f"# Security Assessment Report",
            f"",
            f"**Target:** {data.target}",
            f"**Scan ID:** {data.scan_id}",
            f"**Date:** {data.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Risk Rating:** {data.get_risk_rating()} ({data.get_risk_score()}/100)",
            f"",
            f"## Executive Summary",
            f"",
            f"This automated security assessment identified **{data.total_findings}** vulnerabilities:",
            f"",
            f"| Severity | Count |",
            f"|----------|-------|",
            f"| Critical | {len(data.critical_findings)} |",
            f"| High | {len(data.high_findings)} |",
            f"| Medium | {len(data.medium_findings)} |",
            f"| Low | {len(data.low_findings)} |",
            f"| Info | {len(data.info_findings)} |",
            f"",
        ]

        # Add findings sections
        for severity_name, findings in [
            ("Critical", data.critical_findings),
            ("High", data.high_findings),
            ("Medium", data.medium_findings),
            ("Low", data.low_findings),
        ]:
            if findings:
                lines.append(f"## {severity_name} Severity Findings")
                lines.append("")

                for i, finding in enumerate(findings, 1):
                    lines.append(f"### {i}. {finding.title}")
                    lines.append(f"")
                    lines.append(f"**URL:** `{finding.url}`")
                    if finding.parameter:
                        lines.append(f"**Parameter:** `{finding.parameter}`")
                    lines.append(f"**Source:** {finding.source}")
                    lines.append(f"")
                    if finding.description:
                        lines.append(f"**Description:**")
                        lines.append(f"{finding.description}")
                        lines.append(f"")
                    if finding.evidence and self.config.include_evidence:
                        lines.append(f"**Evidence:**")
                        lines.append(f"```")
                        lines.append(finding.evidence[:1000])
                        lines.append(f"```")
                        lines.append(f"")
                    if finding.remediation and self.config.include_remediation:
                        lines.append(f"**Remediation:**")
                        lines.append(f"{finding.remediation}")
                        lines.append(f"")

        # Footer
        lines.extend([
            f"---",
            f"",
            f"*Generated by AIPT - AI-Powered Penetration Testing Framework*",
        ])

        content = "\n".join(lines)

        filename = f"aipt3_report_{data.scan_id}_{data.generated_at.strftime('%Y%m%d_%H%M%S')}.md"
        path = self.config.output_dir / filename

        path.write_text(content)
        logger.info(f"Generated Markdown report: {path}")

        return path
