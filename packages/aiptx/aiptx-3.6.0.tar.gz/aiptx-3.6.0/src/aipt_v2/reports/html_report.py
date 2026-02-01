"""
AIPT HTML Report Template

Generates a standalone HTML report with embedded CSS.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .generator import ReportData


def generate_html_report(data: "ReportData") -> str:
    """Generate standalone HTML report"""

    severity_counts = data.get_severity_counts()
    risk_score = data.get_risk_score()
    risk_rating = data.get_risk_rating()

    # Build findings HTML
    findings_html = ""

    for severity_name, findings, color in [
        ("Critical", data.critical_findings, "#dc2626"),
        ("High", data.high_findings, "#ea580c"),
        ("Medium", data.medium_findings, "#ca8a04"),
        ("Low", data.low_findings, "#2563eb"),
        ("Informational", data.info_findings, "#6b7280"),
    ]:
        if findings:
            findings_html += f"""
            <div class="severity-section">
                <h2 style="color: {color};">{severity_name} Severity ({len(findings)})</h2>
            """

            for i, finding in enumerate(findings, 1):
                evidence_html = ""
                if finding.evidence and data.config.include_evidence:
                    evidence_html = f"""
                    <div class="evidence">
                        <strong>Evidence:</strong>
                        <pre>{_escape_html(finding.evidence[:2000])}</pre>
                    </div>
                    """

                remediation_html = ""
                if finding.remediation and data.config.include_remediation:
                    remediation_html = f"""
                    <div class="remediation">
                        <strong>Remediation:</strong>
                        <p>{_escape_html(finding.remediation)}</p>
                    </div>
                    """

                ai_html = ""
                if finding.ai_reasoning and data.config.include_ai_reasoning:
                    ai_html = f"""
                    <div class="ai-reasoning">
                        <strong>AI Analysis:</strong>
                        <p>{_escape_html(finding.ai_reasoning[:500])}</p>
                    </div>
                    """

                findings_html += f"""
                <div class="finding" style="border-left-color: {color};">
                    <h3>{i}. {_escape_html(finding.title)}</h3>
                    <div class="finding-meta">
                        <span class="badge" style="background-color: {color};">{severity_name}</span>
                        <span class="badge source">{finding.source}</span>
                        <span class="vuln-type">{finding.vuln_type.value}</span>
                    </div>
                    <div class="finding-details">
                        <p><strong>URL:</strong> <code>{_escape_html(finding.url)}</code></p>
                        {f'<p><strong>Parameter:</strong> <code>{_escape_html(finding.parameter)}</code></p>' if finding.parameter else ''}
                        {f'<p><strong>Description:</strong> {_escape_html(finding.description)}</p>' if finding.description else ''}
                        {evidence_html}
                        {remediation_html}
                        {ai_html}
                    </div>
                </div>
                """

            findings_html += "</div>"

    # Risk color
    risk_colors = {
        "Critical": "#dc2626",
        "High": "#ea580c",
        "Medium": "#ca8a04",
        "Low": "#2563eb",
        "Informational": "#6b7280",
    }
    risk_color = risk_colors.get(risk_rating, "#6b7280")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Assessment Report - {_escape_html(data.target)}</title>
    <style>
        :root {{
            --primary: #1e40af;
            --critical: #dc2626;
            --high: #ea580c;
            --medium: #ca8a04;
            --low: #2563eb;
            --info: #6b7280;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}

        header {{
            background: linear-gradient(135deg, var(--primary), #3b82f6);
            color: white;
            padding: 3rem 2rem;
            margin-bottom: 2rem;
            border-radius: 0 0 1rem 1rem;
        }}

        header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        header .meta {{
            opacity: 0.9;
            font-size: 0.95rem;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .summary-card {{
            background: var(--card-bg);
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .summary-card h3 {{
            font-size: 0.875rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}

        .summary-card .value {{
            font-size: 2rem;
            font-weight: 700;
        }}

        .risk-score {{
            background: {risk_color};
            color: white;
        }}

        .severity-breakdown {{
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }}

        .severity-dot {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
            font-size: 0.875rem;
        }}

        .severity-dot::before {{
            content: '';
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}

        .severity-dot.critical::before {{ background: var(--critical); }}
        .severity-dot.high::before {{ background: var(--high); }}
        .severity-dot.medium::before {{ background: var(--medium); }}
        .severity-dot.low::before {{ background: var(--low); }}
        .severity-dot.info::before {{ background: var(--info); }}

        .severity-section {{
            margin-bottom: 2rem;
        }}

        .severity-section h2 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--border);
        }}

        .finding {{
            background: var(--card-bg);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-left: 4px solid;
        }}

        .finding h3 {{
            font-size: 1.125rem;
            margin-bottom: 0.75rem;
        }}

        .finding-meta {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
        }}

        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            color: white;
        }}

        .badge.source {{
            background: var(--primary);
        }}

        .vuln-type {{
            font-size: 0.875rem;
            color: var(--text-muted);
        }}

        .finding-details p {{
            margin-bottom: 0.5rem;
        }}

        .finding-details code {{
            background: var(--bg);
            padding: 0.125rem 0.375rem;
            border-radius: 0.25rem;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 0.875rem;
        }}

        .evidence, .remediation, .ai-reasoning {{
            margin-top: 1rem;
            padding: 1rem;
            background: var(--bg);
            border-radius: 0.5rem;
        }}

        .evidence pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 0.8rem;
            max-height: 300px;
            overflow-y: auto;
        }}

        .ai-reasoning {{
            border-left: 3px solid var(--primary);
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        @media print {{
            body {{ background: white; }}
            .container {{ max-width: 100%; }}
            .finding {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>Security Assessment Report</h1>
            <div class="meta">
                <p><strong>Target:</strong> {_escape_html(data.target)}</p>
                <p><strong>Scan ID:</strong> {data.scan_id}</p>
                <p><strong>Date:</strong> {data.generated_at.strftime('%B %d, %Y at %H:%M UTC')}</p>
                <p><strong>Client:</strong> {_escape_html(data.config.client_name)} | <strong>Project:</strong> {_escape_html(data.config.project_name)}</p>
            </div>
        </div>
    </header>

    <div class="container">
        <section class="summary-grid">
            <div class="summary-card risk-score">
                <h3>Risk Rating</h3>
                <div class="value">{risk_rating}</div>
                <div style="font-size: 0.875rem; opacity: 0.9;">Score: {risk_score}/100</div>
            </div>

            <div class="summary-card">
                <h3>Total Findings</h3>
                <div class="value">{data.total_findings}</div>
                <div class="severity-breakdown">
                    <span class="severity-dot critical">{severity_counts['critical']}</span>
                    <span class="severity-dot high">{severity_counts['high']}</span>
                    <span class="severity-dot medium">{severity_counts['medium']}</span>
                    <span class="severity-dot low">{severity_counts['low']}</span>
                </div>
            </div>

            <div class="summary-card">
                <h3>AI Findings</h3>
                <div class="value">{data.ai_findings_count}</div>
                <div style="font-size: 0.875rem; color: var(--text-muted);">Strix AI-discovered vulnerabilities</div>
            </div>

            <div class="summary-card">
                <h3>Scan Sources</h3>
                <div class="value">{len(data.sources)}</div>
                <div style="font-size: 0.875rem; color: var(--text-muted);">{', '.join(data.sources) if data.sources else 'N/A'}</div>
            </div>
        </section>

        <section class="findings">
            {findings_html if findings_html else '<p style="text-align: center; color: var(--text-muted); padding: 3rem;">No vulnerabilities found.</p>'}
        </section>
    </div>

    <footer>
        <p>Generated by <strong>AIPT</strong> - AI-Powered Penetration Testing Framework</p>
        <p>Report generated on {data.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </footer>
</body>
</html>"""

    return html


def _escape_html(text: str) -> str:
    """Escape HTML special characters"""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
