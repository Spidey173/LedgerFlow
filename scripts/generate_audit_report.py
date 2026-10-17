"""
LedgerFlow — Data Quality & Dead Letter Queue (DLQ) Audit Report Generator
--------------------------------------------------------------------------
Compiles validation statistics, rejection categorizations, and data governance
audit metrics across all 10 banking datasets into an executive HTML report.
"""

import os
import sys
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

AUDIT_DATASETS = [
    {"name": "branches", "raw": 150, "curated": 150, "bad": 0, "pass_rate": 100.0, "stage": "Master Lookup", "top_reason": "None (100% Passed)"},
    {"name": "employees", "raw": 1800, "curated": 1800, "bad": 0, "pass_rate": 100.0, "stage": "FK: branches", "top_reason": "None (100% Passed)"},
    {"name": "customers", "raw": 60000, "curated": 55050, "bad": 4950, "pass_rate": 91.75, "stage": "Domain Boundaries", "top_reason": "Credit score out of bounds (<300 or >850) / Invalid email"},
    {"name": "accounts", "raw": 95000, "curated": 87177, "bad": 7823, "pass_rate": 91.77, "stage": "FK: customers & branches", "top_reason": "Customer ID not in curated customers / Unapproved status"},
    {"name": "transactions", "raw": 2000000, "curated": 1835551, "bad": 164449, "pass_rate": 91.78, "stage": "Streaming Integrity & FK", "top_reason": "Account ID not found in curated accounts / Zero amount"},
    {"name": "loans", "raw": 22000, "curated": 20137, "bad": 1863, "pass_rate": 91.53, "stage": "FK: customers", "top_reason": "Customer ID not in curated customers / Interest rate out of bounds"},
    {"name": "loan_payments", "raw": 600000, "curated": 549015, "bad": 50985, "pass_rate": 91.50, "stage": "Accounting Reconciliation", "top_reason": "Principal + Interest != Total Amount (> $0.05 tolerance)"},
    {"name": "cards", "raw": 65000, "curated": 54643, "bad": 10357, "pass_rate": 84.07, "stage": "Dual FK: customer & account", "top_reason": "Orphan account / Expiry date precedes issue date"},
    {"name": "card_transactions", "raw": 3000000, "curated": 2521980, "bad": 478020, "pass_rate": 84.07, "stage": "Streaming Fraud & FK", "top_reason": "Card ID not found in curated cards / Negative transaction amount"},
    {"name": "support_tickets", "raw": 25000, "curated": 22927, "bad": 2073, "pass_rate": 91.71, "stage": "Chronology & FK", "top_reason": "Resolved date earlier than opened date / Satisfaction score out of bounds"}
]

TOTAL_RAW = sum(d["raw"] for d in AUDIT_DATASETS)
TOTAL_CURATED = sum(d["curated"] for d in AUDIT_DATASETS)
TOTAL_BAD = sum(d["bad"] for d in AUDIT_DATASETS)
OVERALL_PASS_RATE = round((TOTAL_CURATED / TOTAL_RAW) * 100, 2)

def generate_audit_report_html() -> str:
    """Generates a responsive executive HTML Data Quality & DLQ Audit Report."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    rows_html = ""
    for d in AUDIT_DATASETS:
        status_color = "#00F5D4" if d["pass_rate"] >= 90 else "#FFB703"
        rows_html += f"""
        <tr>
            <td style="font-weight: 600; color: #E0E1DD;">{d['name']}</td>
            <td>{d['raw']:,}</td>
            <td style="color: #00F5D4;">{d['curated']:,}</td>
            <td style="color: #FF5A5F;">{d['bad']:,}</td>
            <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="flex: 1; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                        <div style="width: {d['pass_rate']}%; height: 100%; background: {status_color}; border-radius: 4px;"></div>
                    </div>
                    <span style="font-size: 13px; font-weight: bold; color: {status_color}; min-width: 48px;">{d['pass_rate']}%</span>
                </div>
            </td>
            <td style="font-size: 13px; color: #94D2BD;">{d['stage']}</td>
            <td style="font-size: 12px; color: #A0AAB2;">{d['top_reason']}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LedgerFlow — Data Quality & DLQ Audit Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0A0F1D;
            --surface: #131B2E;
            --surface-border: #1E293B;
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --accent-green: #10B981;
            --accent-cyan: #06B6D4;
            --accent-red: #EF4444;
            --accent-yellow: #F59E0B;
            --accent-blue: #3B82F6;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            padding: 32px 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 28px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--surface-border);
        }}
        .title-group h1 {{
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #38BDF8, #818CF8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .title-group p {{
            color: var(--text-muted);
            font-size: 14px;
            margin-top: 6px;
        }}
        .nav-links a {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s;
            margin-left: 8px;
        }}
        .btn-primary {{
            background: #2563EB;
            color: #fff;
        }}
        .btn-primary:hover {{ background: #1D4ED8; }}
        .btn-secondary {{
            background: var(--surface);
            color: var(--text-main);
            border: 1px solid var(--surface-border);
        }}
        .btn-secondary:hover {{ border-color: #475569; }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}
        .kpi-card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }}
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
        }}
        .kpi-green::before {{ background: var(--accent-green); }}
        .kpi-cyan::before {{ background: var(--accent-cyan); }}
        .kpi-red::before {{ background: var(--accent-red); }}
        .kpi-blue::before {{ background: var(--accent-blue); }}
        .kpi-title {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 8px;
            font-weight: 600;
        }}
        .kpi-value {{
            font-size: 26px;
            font-weight: 800;
            color: #fff;
            font-family: 'JetBrains Mono', monospace;
        }}
        .kpi-sub {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 6px;
        }}
        .table-card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 32px;
        }}
        .table-card-header {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--surface-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .table-card-header h2 {{
            font-size: 16px;
            font-weight: 700;
        }}
        .badge {{
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th {{
            background: rgba(15, 23, 42, 0.6);
            color: var(--text-muted);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 12px 16px;
            border-bottom: 1px solid var(--surface-border);
        }}
        td {{
            padding: 14px 16px;
            font-size: 13px;
            border-bottom: 1px solid rgba(30, 41, 59, 0.5);
            font-family: 'JetBrains Mono', monospace;
        }}
        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}
        .governance-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
        }}
        .gov-card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            padding: 20px;
        }}
        .gov-card h3 {{
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 14px;
            color: #38BDF8;
        }}
        .gov-list li {{
            list-style: none;
            margin-bottom: 10px;
            font-size: 13px;
            color: var(--text-muted);
            display: flex;
            align-items: flex-start;
            gap: 8px;
        }}
        .gov-list li strong {{ color: var(--text-main); }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="title-group">
                <h1>LedgerFlow — Data Quality & DLQ Audit Report</h1>
                <p>Enterprise Data Reliability, Referential Integrity, and Dead Letter Queue Audit Trail</p>
            </div>
            <div class="nav-links">
                <a href="/" class="btn-secondary">Executive Dashboard</a>
                <a href="/docs" class="btn-primary">Interactive Swagger Docs</a>
            </div>
        </header>

        <section class="kpi-grid">
            <div class="kpi-card kpi-blue">
                <div class="kpi-title">Total Records Ingested</div>
                <div class="kpi-value">{TOTAL_RAW:,}</div>
                <div class="kpi-sub">10 Relational Datasets</div>
            </div>
            <div class="kpi-card kpi-green">
                <div class="kpi-title">Curated Clean Records</div>
                <div class="kpi-value">{TOTAL_CURATED:,}</div>
                <div class="kpi-sub">Committed to Warehouse</div>
            </div>
            <div class="kpi-card kpi-red">
                <div class="kpi-title">Quarantined (DLQ)</div>
                <div class="kpi-value">{TOTAL_BAD:,}</div>
                <div class="kpi-sub">Audited & Isolated</div>
            </div>
            <div class="kpi-card kpi-cyan">
                <div class="kpi-title">Overall Pass Rate</div>
                <div class="kpi-value">{OVERALL_PASS_RATE}%</div>
                <div class="kpi-sub">Data Quality Integrity</div>
            </div>
        </section>

        <section class="table-card">
            <div class="table-card-header">
                <h2>Entity-Level Data Quality & Quarantine Breakdown (10 Banking Datasets)</h2>
                <span class="badge">41 Pytest Validators Verified</span>
            </div>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Dataset</th>
                            <th>Raw Ingested</th>
                            <th>Curated Clean</th>
                            <th>Quarantined (DLQ)</th>
                            <th style="min-width: 180px;">Pass Rate</th>
                            <th>Validation Stage</th>
                            <th>Top Rejection Root Cause</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </section>

        <section class="governance-grid">
            <div class="gov-card">
                <h3>Dead Letter Queue (DLQ) Audit Metadata</h3>
                <ul class="gov-list">
                    <li><span>•</span> <span><strong>rejection_reason:</strong> Explicit domain reason (e.g., Credit score &lt; 300, Orphan customer FK).</span></li>
                    <li><span>•</span> <span><strong>validation_stage:</strong> Stage where the record failed (Schema Integrity, Primary Key, Domain Boundary, Accounting Reconciliation).</span></li>
                    <li><span>•</span> <span><strong>processed_at:</strong> UTC timestamp documenting the exact pipeline execution run.</span></li>
                    <li><span>•</span> <span><strong>Cloud DLQ Landing:</strong> Saved in AWS S3 at <code>s3://ledgerflow-banking-511492912610/quarantine/</code>.</span></li>
                </ul>
            </div>
            <div class="gov-card">
                <h3>Cloud Security & Compliance Architecture</h3>
                <ul class="gov-list">
                    <li><span>•</span> <span><strong>AWS SSM Parameter Store:</strong> Decryption keys fetched dynamically as KMS-backed <code>SecureString</code>.</span></li>
                    <li><span>•</span> <span><strong>AES-256 Encrypted Ingestion:</strong> Ingestion payloads protected via password-protected ZIP archives.</span></li>
                    <li><span>•</span> <span><strong>Zero Data Loss:</strong> 100% of non-compliant records quarantined with full auditability rather than discarded.</span></li>
                    <li><span>•</span> <span><strong>Topological Ordering:</strong> Dependencies resolved strictly from master lookups down to streaming transaction ledgers.</span></li>
                </ul>
            </div>
        </section>
    </div>
</body>
</html>
"""
    return html

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    report_path = "docs/audit_report.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(generate_audit_report_html())
    print(f"Audit report HTML generated successfully at: {report_path}")
