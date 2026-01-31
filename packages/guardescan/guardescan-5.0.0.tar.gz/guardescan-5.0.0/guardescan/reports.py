"""
GuardeScan Report Generators
Generate JSON, HTML, Markdown, and SARIF reports
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from guardescan.core import ScanResult, Severity

VERSION = '3.0.0'


def generate_all_reports(result: ScanResult, base_name: str, output_dir: str = '.'):
    """Generate all report formats"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # JSON
    json_path = output_path / f"{base_name}_report.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"  JSON: {json_path}")
    
    # HTML
    html_path = output_path / f"{base_name}_report.html"
    generate_html_report(result, str(html_path))
    print(f"  HTML: {html_path}")
    
    # Markdown
    md_path = output_path / f"{base_name}_report.md"
    generate_markdown_report(result, str(md_path))
    print(f"  Markdown: {md_path}")
    
    # SARIF
    sarif_path = output_path / f"{base_name}_report.sarif"
    generate_sarif_report(result, str(sarif_path))
    print(f"  SARIF: {sarif_path}")


def generate_html_report(result: ScanResult, path: str):
    """Generate a beautiful HTML report"""
    
    severity_colors = {
        'critical': '#ef4444',
        'high': '#f97316',
        'medium': '#eab308',
        'low': '#22c55e',
        'info': '#6b7280'
    }
    
    grade_colors = {
        'A+': '#22c55e', 'A': '#22c55e',
        'B+': '#3b82f6', 'B': '#3b82f6',
        'C+': '#eab308', 'C': '#eab308',
        'D+': '#f97316', 'D': '#f97316',
        'F': '#ef4444'
    }
    
    vuln_rows = '\n'.join([f'''
        <tr>
            <td><span class="badge" style="background:{severity_colors.get(v.severity.value, '#6b7280')}">{v.severity.value.upper()}</span></td>
            <td><strong>{v.title}</strong></td>
            <td>{v.confidence:.0%}</td>
            <td>{v.line_number or 'N/A'}</td>
            <td>{', '.join(v.detected_by)}</td>
        </tr>
    ''' for v in result.vulnerabilities])
    
    vuln_details = '\n'.join([f'''
        <div class="vuln-card" style="border-left: 4px solid {severity_colors.get(v.severity.value, '#6b7280')}">
            <h3>{v.title}</h3>
            <p><strong>Severity:</strong> {v.severity.value.upper()} | <strong>Confidence:</strong> {v.confidence:.0%} | <strong>Line:</strong> {v.line_number or 'N/A'}</p>
            <p>{v.description}</p>
            {f'<pre><code>{v.code_snippet}</code></pre>' if v.code_snippet else ''}
            <p class="recommendation"><strong>Recommendation:</strong> {v.recommendation}</p>
            {f'<p><small>CWE: {v.cwe_id} | SWC: {v.swc_id}</small></p>' if v.cwe_id or v.swc_id else ''}
        </div>
    ''' for v in result.vulnerabilities])
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GuardeScan Report - {result.contract_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #e2e8f0; min-height: 100vh; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .header {{ text-align: center; padding: 3rem 0; }}
        .header h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; background: linear-gradient(90deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .header .subtitle {{ color: #94a3b8; }}
        .grade-badge {{ display: inline-block; font-size: 4rem; font-weight: bold; padding: 1rem 2.5rem; border-radius: 1rem; background: {grade_colors.get(result.grade.value, '#6b7280')}; color: white; margin: 1.5rem 0; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }}
        .score-text {{ font-size: 1.25rem; color: #94a3b8; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin: 2rem 0; }}
        .stat {{ background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border-radius: 1rem; padding: 1.5rem; text-align: center; border: 1px solid rgba(255,255,255,0.1); }}
        .stat .value {{ font-size: 2rem; font-weight: bold; color: #60a5fa; }}
        .stat .label {{ color: #94a3b8; font-size: 0.875rem; margin-top: 0.5rem; }}
        .card {{ background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border-radius: 1rem; padding: 1.5rem; margin: 1.5rem 0; border: 1px solid rgba(255,255,255,0.1); }}
        .card h2 {{ color: #60a5fa; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 0.875rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ color: #60a5fa; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 0.5rem; color: white; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
        .vuln-card {{ background: rgba(0,0,0,0.2); border-radius: 0.75rem; padding: 1.25rem; margin: 1rem 0; }}
        .vuln-card h3 {{ color: #f8fafc; margin-bottom: 0.5rem; }}
        .vuln-card pre {{ background: #0f172a; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; margin: 1rem 0; font-size: 0.875rem; }}
        .vuln-card code {{ color: #a5f3fc; }}
        .recommendation {{ background: rgba(34, 197, 94, 0.1); border-left: 3px solid #22c55e; padding: 0.75rem 1rem; border-radius: 0 0.5rem 0.5rem 0; margin-top: 1rem; }}
        .footer {{ text-align: center; padding: 2rem; color: #64748b; font-size: 0.875rem; }}
        .safe {{ background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05)); text-align: center; padding: 2rem; border-radius: 1rem; }}
        .safe h3 {{ color: #22c55e; font-size: 1.5rem; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>GuardeScan Security Report</h1>
            <p class="subtitle">{result.contract_name} | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <div class="grade-badge">{result.grade.value}</div>
            <p class="score-text">Security Score: {result.score:.1f}/100 | Risk: {result.risk_rating}</p>
        </div>
        
        <div class="stats">
            <div class="stat"><div class="value">{len(result.vulnerabilities)}</div><div class="label">Vulnerabilities</div></div>
            <div class="stat"><div class="value">{len(result.gas_issues)}</div><div class="label">Gas Issues</div></div>
            <div class="stat"><div class="value">{result.scan_time:.2f}s</div><div class="label">Scan Time</div></div>
            <div class="stat"><div class="value">{result.solidity_version or 'N/A'}</div><div class="label">Solidity</div></div>
            <div class="stat"><div class="value">{result.function_count or 'N/A'}</div><div class="label">Functions</div></div>
            <div class="stat"><div class="value">{len(result.scanners_used)}</div><div class="label">Scanners</div></div>
        </div>
        
        <div class="card">
            <h2>Vulnerability Summary</h2>
            {f'<div class="safe"><h3>✓ No Vulnerabilities Detected</h3><p>This contract passed all security checks.</p></div>' if not result.vulnerabilities else f'''
            <table>
                <thead><tr><th>Severity</th><th>Issue</th><th>Confidence</th><th>Line</th><th>Detected By</th></tr></thead>
                <tbody>{vuln_rows}</tbody>
            </table>'''}
        </div>
        
        {f'<div class="card"><h2>Vulnerability Details</h2>{vuln_details}</div>' if result.vulnerabilities else ''}
        
        <div class="footer">
            <p>Generated by GuardeScan v{VERSION}</p>
            <p>Scanners: {', '.join(result.scanners_used)}</p>
        </div>
    </div>
</body>
</html>'''
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_markdown_report(result: ScanResult, path: str):
    """Generate a Markdown report"""
    
    severity_emoji = {
        Severity.CRITICAL: '🔴',
        Severity.HIGH: '🟠',
        Severity.MEDIUM: '🟡',
        Severity.LOW: '🟢',
        Severity.INFO: '🔵'
    }
    
    vuln_sections = ''
    for i, v in enumerate(result.vulnerabilities, 1):
        emoji = severity_emoji.get(v.severity, '⚪')
        vuln_sections += f'''
### {i}. {emoji} {v.title}

| Property | Value |
|----------|-------|
| Severity | **{v.severity.value.upper()}** |
| Confidence | {v.confidence:.0%} |
| Line | {v.line_number or 'N/A'} |
| CWE | {v.cwe_id or 'N/A'} |
| SWC | {v.swc_id or 'N/A'} |

{v.description}

{'```solidity' + chr(10) + v.code_snippet + chr(10) + '```' if v.code_snippet else ''}

**Recommendation:** {v.recommendation}

---
'''
    
    md = f'''# GuardeScan Security Report

**Contract:** `{result.contract_name}`  
**File:** `{result.contract_path}`  
**Grade:** {result.grade.value} ({result.score:.1f}/100)  
**Risk:** {result.risk_rating}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Summary

| Metric | Value |
|--------|-------|
| Vulnerabilities | {len(result.vulnerabilities)} |
| Gas Issues | {len(result.gas_issues)} |
| Scan Time | {result.scan_time:.2f}s |
| Solidity | {result.solidity_version or 'Unknown'} |
| Functions | {result.function_count or 'N/A'} |
| Scanners | {', '.join(result.scanners_used)} |

---

## Vulnerabilities

{vuln_sections if result.vulnerabilities else '✅ **No vulnerabilities detected!**'}

## Gas Optimization

{chr(10).join([f'- **{g.issue_type}** (Line {g.line_number or "N/A"}): {g.description} (~{g.savings_percent}% savings)' for g in result.gas_issues[:10]]) if result.gas_issues else 'No gas optimization issues found.'}

---

*Generated by GuardeScan v{VERSION}*
'''
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(md)


def generate_sarif_report(result: ScanResult, path: str):
    """Generate SARIF report for CI/CD integration"""
    
    # Build rules
    rules = []
    rules_seen = set()
    for v in result.vulnerabilities:
        if v.vuln_id not in rules_seen:
            rules.append({
                "id": v.vuln_id,
                "name": v.title,
                "shortDescription": {"text": v.title},
                "fullDescription": {"text": v.description},
                "help": {"text": v.recommendation, "markdown": f"**Recommendation:** {v.recommendation}"},
                "defaultConfiguration": {
                    "level": "error" if v.severity in [Severity.CRITICAL, Severity.HIGH] else "warning" if v.severity == Severity.MEDIUM else "note"
                },
                "properties": {
                    "precision": "high" if v.confidence >= 0.8 else "medium",
                    "security-severity": "9.0" if v.severity == Severity.CRITICAL else "7.0" if v.severity == Severity.HIGH else "5.0"
                }
            })
            rules_seen.add(v.vuln_id)
    
    # Build results
    results = []
    for v in result.vulnerabilities:
        results.append({
            "ruleId": v.vuln_id,
            "level": "error" if v.severity in [Severity.CRITICAL, Severity.HIGH] else "warning",
            "message": {"text": v.description},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": result.contract_path},
                    "region": {"startLine": v.line_number or 1}
                }
            }],
            "fingerprints": {
                "primaryLocationLineHash": f"{v.vuln_id}:{v.line_number or 0}"
            }
        })
    
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "GuardeScan",
                    "version": VERSION,
                    "informationUri": "https://guardescan.io",
                    "rules": rules
                }
            },
            "results": results,
            "invocations": [{
                "executionSuccessful": True,
                "endTimeUtc": datetime.utcnow().isoformat() + "Z"
            }]
        }]
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(sarif, f, indent=2)
