"""
LedgerFlow — Data Quality & Dead Letter Queue (DLQ) Audit Report Generator
--------------------------------------------------------------------------
Clean, non-AI corporate red banking style for executive compliance & governance.
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
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    rows_html = ""
    for d in AUDIT_DATASETS:
        bar_color = "#2B8A3E" if d["pass_rate"] >= 90 else "#D97706"
        rows_html += f"""
        <tr>
            <td style="font-weight: 600; color: #1E293B;">{d['name']}</td>
            <td>{d['raw']:,}</td>
            <td style="color: #2B8A3E; font-weight: 600;">{d['curated']:,}</td>
            <td style="color: #A61C1C; font-weight: 600;">{d['bad']:,}</td>
            <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="flex: 1; height: 7px; background: #E2E8F0; border-radius: 4px; overflow: hidden;">
                        <div style="width: {d['pass_rate']}%; height: 100%; background: {bar_color}; border-radius: 4px;"></div>
                    </div>
                    <span style="font-size: 12px; font-weight: 600; color: {bar_color}; min-width: 44px;">{d['pass_rate']}%</span>
                </div>
            </td>
            <td style="font-size: 12px; color: #475569;">{d['stage']}</td>
            <td style="font-size: 12px; color: #64748B;">{d['top_reason']}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LedgerFlow — Data Quality & DLQ Audit Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --red-primary: #A61C1C;
            --red-dark: #7A1212;
            --bg-page: #F5F6F8;
            --bg-card: #FFFFFF;
            --text-title: #1A1F2C;
            --text-body: #4A5568;
            --text-muted: #718096;
            --border-color: #E2E8F0;
            --green: #2B8A3E;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'IBM Plex Sans', 'Segoe UI', -apple-system, sans-serif;
            background-color: var(--bg-page);
            color: var(--text-body);
            line-height: 1.5;
            padding-bottom: 48px;
        }}
        .top-navbar {{
            background-color: var(--red-primary);
            color: #FFFFFF;
            padding: 14px 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        }}
        .brand-section {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .brand-logo {{
            font-weight: 700;
            font-size: 18px;
            color: #FFFFFF;
        }}
        .nav-links {{
            display: flex;
            gap: 10px;
        }}
        .nav-btn {{
            background-color: rgba(255, 255, 255, 0.12);
            color: #FFFFFF;
            padding: 6px 14px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .nav-btn:hover {{ background-color: rgba(255, 255, 255, 0.25); }}
        .nav-btn-white {{
            background-color: #FFFFFF;
            color: var(--red-primary);
            border: 1px solid #FFFFFF;
        }}
        .main-container {{
            max-width: 1280px;
            margin: 28px auto;
            padding: 0 24px;
        }}
        .page-header {{
            background: #FFFFFF;
            border: 1px solid var(--border-color);
            border-left: 5px solid var(--red-primary);
            border-radius: 6px;
            padding: 20px 24px;
            margin-bottom: 24px;
        }}
        .page-header h1 {{
            font-size: 22px;
            font-weight: 700;
            color: var(--text-title);
            margin-bottom: 4px;
        }}
        .page-header p {{
            font-size: 14px;
            color: var(--text-muted);
        }}
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .kpi-box {{
            background: #FFFFFF;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 18px 20px;
        }}
        .kpi-box-label {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 4px;
        }}
        .kpi-box-val {{
            font-size: 26px;
            font-weight: 700;
            color: var(--text-title);
            font-family: 'IBM Plex Mono', monospace;
        }}
        .kpi-box-sub {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        .table-card {{
            background: #FFFFFF;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            overflow: hidden;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }}
        .table-card-head {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .table-card-head h2 {{
            font-size: 15px;
            font-weight: 700;
            color: var(--text-title);
        }}
        .badge-verified {{
            padding: 4px 10px;
            background: #EBFBEE;
            border: 1px solid #D3F9D8;
            color: var(--green);
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th {{
            background: #F8FAFC;
            color: var(--text-muted);
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            padding: 11px 16px;
            border-bottom: 1px solid var(--border-color);
        }}
        td {{
            padding: 12px 16px;
            font-size: 13px;
            border-bottom: 1px solid #F1F5F9;
            font-family: 'IBM Plex Mono', monospace;
        }}
        tr:hover td {{
            background-color: #F8FAFC;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 16px;
        }}
        .info-card {{
            background: #FFFFFF;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 20px;
        }}
        .info-card h3 {{
            font-size: 14px;
            font-weight: 700;
            color: var(--red-primary);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .info-card ul {{
            padding-left: 18px;
        }}
        .info-card li {{
            font-size: 13px;
            color: var(--text-body);
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <header class="top-navbar">
        <div class="brand-section">
            <div class="brand-logo">🏦 LedgerFlow</div>
            <span style="font-size: 11px; opacity: 0.85;">Governance & Audit Trail</span>
        </div>
        <div class="nav-links">
            <a href="/" class="nav-btn nav-btn-white">Executive Dashboard</a>
            <a href="/docs" class="nav-btn">Swagger API Docs</a>
        </div>
    </header>

    <div class="main-container">
        <div class="page-header">
            <h1>Data Quality & Dead Letter Queue (DLQ) Audit Report</h1>
            <p>Verification metrics, rejection root cause analysis, and referential constraints across 5,868,950 banking records.</p>
        </div>

        <div class="kpi-row">
            <div class="kpi-box">
                <div class="kpi-box-label">Total Ingested Records</div>
                <div class="kpi-box-val">{TOTAL_RAW:,}</div>
                <div class="kpi-box-sub">10 Relational Datasets</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-box-label">Curated Clean Records</div>
                <div class="kpi-box-val" style="color: var(--green);">{TOTAL_CURATED:,}</div>
                <div class="kpi-box-sub">Loaded to Warehouse</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-box-label">Quarantined (DLQ)</div>
                <div class="kpi-box-val" style="color: var(--red-primary);">{TOTAL_BAD:,}</div>
                <div class="kpi-box-sub">Isolated with Reason</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-box-label">Overall Pass Rate</div>
                <div class="kpi-box-val">{OVERALL_PASS_RATE}%</div>
                <div class="kpi-box-sub">Data Quality Integrity</div>
            </div>
        </div>

        <div class="table-card">
            <div class="table-card-head">
                <h2>Entity-Level Data Quality & Quarantine Breakdown</h2>
                <span class="badge-verified">41 Pytest Rules Verified</span>
            </div>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Dataset</th>
                            <th>Raw Ingested</th>
                            <th>Curated Clean</th>
                            <th>Quarantined</th>
                            <th style="min-width: 170px;">Pass Rate</th>
                            <th>Validation Stage</th>
                            <th>Primary Quarantine Root Cause</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="info-grid">
            <div class="info-card">
                <h3>Dead Letter Queue (DLQ) Governance</h3>
                <ul>
                    <li><strong>rejection_reason:</strong> Explicit business logic failure reason (e.g., Credit score out of bounds, Orphan customer FK).</li>
                    <li><strong>validation_stage:</strong> Identifies failing stage (Schema Integrity, Primary Key, Domain Boundary, Accounting Reconciliation).</li>
                    <li><strong>processed_at:</strong> UTC execution timestamp documenting batch origin.</li>
                    <li><strong>Storage:</strong> Isolated in AWS S3 at <code>s3://ledgerflow-banking-511492912610/quarantine/</code>.</li>
                </ul>
            </div>
            <div class="info-card">
                <h3>Enterprise Security & Compliance</h3>
                <ul>
                    <li><strong>AWS SSM Parameter Store:</strong> Decryption keys fetched dynamically via KMS-encrypted <code>SecureString</code>.</li>
                    <li><strong>AES-256 Encrypted Ingestion:</strong> Raw payloads protected using password-protected ZIP archives.</li>
                    <li><strong>Zero Data Loss:</strong> Corrupted or non-compliant records quarantined rather than silently discarded.</li>
                    <li><strong>Topological Order:</strong> Dependencies resolved strictly from master branches down to transaction ledgers.</li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    report_path = "docs/audit_report.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(generate_audit_report_html())
    print(f"Audit report HTML generated successfully at: {report_path}")
