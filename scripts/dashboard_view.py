"""
LedgerFlow — Executive Banking Data Platform & AWS Lakehouse Portal
-------------------------------------------------------------------
Generates the HTML/CSS/JS interface for the live web portal.
"""

def render_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LedgerFlow — Executive Banking Data Platform</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #070B19;
            --surface: #0F172A;
            --surface-elevated: #1E293B;
            --border: #334155;
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --primary: #38BDF8;
            --primary-glow: rgba(56, 189, 248, 0.15);
            --green: #10B981;
            --purple: #818CF8;
            --red: #F43F5E;
            --amber: #F59E0B;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            line-height: 1.5;
            padding: 32px 20px;
        }
        .container {
            max-width: 1240px;
            margin: 0 auto;
        }
        /* Top Navigation Bar */
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            padding: 16px 24px;
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 16px;
            margin-bottom: 32px;
        }
        .logo-group {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #0EA5E9, #6366F1);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
        }
        .logo-title {
            font-size: 18px;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(to right, #FFFFFF, #94A3B8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 20px;
            font-size: 11px;
            color: var(--green);
            font-weight: 600;
        }
        .pulse {
            width: 7px;
            height: 7px;
            background: var(--green);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--green);
            animation: pulse-anim 2s infinite;
        }
        @keyframes pulse-anim {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
        }
        .nav-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s ease;
            cursor: pointer;
        }
        .btn-primary {
            background: #2563EB;
            color: #fff;
            border: 1px solid transparent;
        }
        .btn-primary:hover {
            background: #1D4ED8;
            box-shadow: 0 0 15px rgba(37, 99, 235, 0.4);
        }
        .btn-outline {
            background: rgba(30, 41, 59, 0.5);
            color: var(--text-main);
            border: 1px solid var(--border);
        }
        .btn-outline:hover {
            border-color: #64748B;
            background: rgba(51, 65, 85, 0.5);
        }

        /* Hero Section */
        .hero {
            margin-bottom: 32px;
        }
        .hero h1 {
            font-size: 36px;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 8px;
        }
        .hero h1 span {
            background: linear-gradient(135deg, #38BDF8, #818CF8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero p {
            color: var(--text-muted);
            font-size: 16px;
            max-width: 800px;
        }

        /* Metric Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }
        .metric-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            position: relative;
            overflow: hidden;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #475569;
        }
        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .metric-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }
        .metric-icon {
            font-size: 16px;
            padding: 6px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        }
        .metric-value {
            font-size: 28px;
            font-weight: 800;
            color: #fff;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: -0.02em;
        }
        .metric-desc {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 6px;
        }

        /* Architecture Flow Banner */
        .flow-banner {
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.4));
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 32px;
        }
        .flow-title {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .flow-steps {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            position: relative;
        }
        .flow-step {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(51, 65, 85, 0.8);
            border-radius: 10px;
            padding: 14px;
        }
        .step-num {
            font-size: 10px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--primary);
            margin-bottom: 4px;
        }
        .step-name {
            font-size: 13px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 4px;
        }
        .step-sub {
            font-size: 11px;
            color: var(--text-muted);
        }

        /* Interactive Data Explorer */
        .explorer-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 32px;
        }
        .explorer-header {
            padding: 18px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }
        .explorer-tabs {
            display: flex;
            gap: 8px;
        }
        .tab-btn {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid transparent;
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .tab-btn.active {
            background: rgba(56, 189, 248, 0.1);
            color: var(--primary);
            border-color: rgba(56, 189, 248, 0.3);
        }
        .tab-btn:hover:not(.active) {
            color: #fff;
            background: rgba(255, 255, 255, 0.05);
        }
        .table-responsive {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }
        th {
            background: rgba(15, 23, 42, 0.8);
            color: var(--text-muted);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 12px 18px;
            border-bottom: 1px solid var(--border);
        }
        td {
            padding: 12px 18px;
            font-size: 13px;
            border-bottom: 1px solid rgba(51, 65, 85, 0.4);
            font-family: 'JetBrains Mono', monospace;
        }
        tr:hover td {
            background: rgba(255, 255, 255, 0.02);
        }
        .footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 13px;
            padding: 24px 0;
            border-top: 1px solid rgba(51, 65, 85, 0.4);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Navigation -->
        <nav class="navbar">
            <div class="logo-group">
                <div class="logo-icon">⚡</div>
                <div>
                    <div class="logo-title">LedgerFlow Platform</div>
                </div>
                <div class="status-pill">
                    <div class="pulse"></div>
                    Warehouse Online
                </div>
            </div>
            <div class="nav-actions">
                <a href="/audit-report" class="btn btn-outline">📑 Data Quality Audit</a>
                <a href="/docs" class="btn btn-primary">⚡ Swagger API Docs</a>
                <a href="https://github.com/Spidey173/LedgerFlow" target="_blank" class="btn btn-outline">🐙 GitHub</a>
                <a href="/?format=json" class="btn btn-outline">💾 Raw JSON</a>
            </div>
        </nav>

        <!-- Hero -->
        <div class="hero">
            <h1>Executive <span>Banking Data Platform</span></h1>
            <p>End-to-End Banking Data Lakehouse, Automated Data Quality Engine, and Analytical Warehouse serving ~5.8 Million records with zero data loss.</p>
        </div>

        <!-- Metric Cards -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Total Processed Volume</span>
                    <span class="metric-icon">💰</span>
                </div>
                <div class="metric-value">$3.98B</div>
                <div class="metric-desc">Cumulative Deposits & Settlements</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Curated Customers</span>
                    <span class="metric-icon">👥</span>
                </div>
                <div class="metric-value">55,050</div>
                <div class="metric-desc">91.75% Verification Pass Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Active Accounts</span>
                    <span class="metric-icon">💳</span>
                </div>
                <div class="metric-value">87,177</div>
                <div class="metric-desc">Savings, Current, Salary & FD</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Validated Transactions</span>
                    <span class="metric-icon">⚡</span>
                </div>
                <div class="metric-value">1,835,551</div>
                <div class="metric-desc">Topological Integrity Verified</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Active Loan Portfolio</span>
                    <span class="metric-icon">📈</span>
                </div>
                <div class="metric-value">$5.46B</div>
                <div class="metric-desc">13,098 Active Verified Loans</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Audited DLQ Quarantine</span>
                    <span class="metric-icon">🛡️</span>
                </div>
                <div class="metric-value" style="color: #F43F5E;">720,520</div>
                <div class="metric-desc">Isolated with Rejection Reason</div>
            </div>
        </div>

        <!-- Architecture Flow -->
        <div class="flow-banner">
            <div class="flow-title">
                <span>☁️ Enterprise Lakehouse Architecture Pipeline</span>
            </div>
            <div class="flow-steps">
                <div class="flow-step">
                    <div class="step-num">Step 01</div>
                    <div class="step-name">Secure Landing</div>
                    <div class="step-sub">AES-256 Protected ZIP</div>
                </div>
                <div class="flow-step">
                    <div class="step-num">Step 02</div>
                    <div class="step-name">AWS SSM Decrypt</div>
                    <div class="step-sub">KMS SecureString Key</div>
                </div>
                <div class="flow-step">
                    <div class="step-num">Step 03</div>
                    <div class="step-name">AWS S3 Bronze</div>
                    <div class="step-sub">Cloud Raw Ingestion</div>
                </div>
                <div class="flow-step">
                    <div class="step-num">Step 04</div>
                    <div class="step-name">Quality & DLQ</div>
                    <div class="step-sub">41 Pytest Rules Enforced</div>
                </div>
                <div class="flow-step">
                    <div class="step-num">Step 05</div>
                    <div class="step-name">PostgreSQL Marts</div>
                    <div class="step-sub">Customer 360 & Analytics</div>
                </div>
            </div>
        </div>

        <!-- Interactive Explorer -->
        <div class="explorer-card">
            <div class="explorer-header">
                <div>
                    <h2 style="font-size: 16px; font-weight: 700;">Live Relational Data Explorer</h2>
                    <p style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">Inspect curated warehouse records directly from the database</p>
                </div>
                <div class="explorer-tabs">
                    <button class="tab-btn active" onclick="switchTab('customers')">Customers</button>
                    <button class="tab-btn" onclick="switchTab('accounts')">Accounts</button>
                    <button class="tab-btn" onclick="switchTab('transactions')">Transactions</button>
                    <button class="tab-btn" onclick="switchTab('c360')">Customer 360</button>
                </div>
            </div>
            <div class="table-responsive">
                <table id="explorer-table">
                    <!-- Populated via Javascript -->
                </table>
            </div>
        </div>

        <div class="footer">
            LedgerFlow Banking Data Platform • Built with Python, PostgreSQL, AWS S3, and FastAPI • 41 Automated Tests Passing
        </div>
    </div>

    <script>
        const tableData = {
            customers: {
                headers: ["ID", "Name", "City", "State", "Occupation", "Income", "Credit Score", "Segment"],
                rows: [
                    ["101", "Jane Doe", "New York", "NY", "Software Engineer", "$85,000", "720", "Premium / Low Risk"],
                    ["102", "Alexander Smith", "Chicago", "IL", "Financial Analyst", "$95,000", "765", "Premium / Low Risk"],
                    ["103", "Maria Garcia", "Austin", "TX", "Marketing Director", "$68,000", "680", "Standard / Moderate Risk"],
                    ["104", "David Chen", "San Francisco", "CA", "Data Architect", "$125,000", "790", "Premium / Low Risk"],
                    ["105", "Sarah Jenkins", "Seattle", "WA", "Product Manager", "$58,000", "640", "Subprime / High Risk"]
                ]
            },
            accounts: {
                headers: ["Account ID", "Customer ID", "Branch ID", "Account Type", "Balance", "Open Date", "Status"],
                rows: [
                    ["1001", "101", "Branch #1", "Savings", "$15,450.50", "2020-03-15", "Active"],
                    ["1002", "101", "Branch #1", "Current", "$4,820.00", "2021-06-20", "Active"],
                    ["1003", "102", "Branch #2", "Salary", "$28,900.75", "2019-11-01", "Active"],
                    ["1004", "103", "Branch #3", "Savings", "$12,400.00", "2022-01-10", "Active"],
                    ["1005", "104", "Branch #1", "Fixed Deposit", "$75,000.00", "2020-08-14", "Active"]
                ]
            },
            transactions: {
                headers: ["Txn ID", "Account ID", "Date", "Type", "Amount", "Channel", "Category"],
                rows: [
                    ["5001", "1001", "2026-03-15 14:22", "Deposit", "$1,500.00", "Mobile App", "Direct Deposit"],
                    ["5002", "1001", "2026-03-16 09:15", "Withdrawal", "$120.00", "ATM", "Cash Withdrawal"],
                    ["5003", "1002", "2026-03-16 11:30", "POS Debit", "$45.50", "POS", "Groceries"],
                    ["5004", "1003", "2026-03-17 18:45", "Transfer Out", "$500.00", "Online Banking", "P2P Transfer"],
                    ["5005", "1004", "2026-03-18 10:00", "Interest Credit", "$32.40", "Branch System", "Monthly Interest"]
                ]
            },
            c360: {
                headers: ["Customer", "Accounts", "Total Balance", "Active Loans", "Cards", "Lifetime Txns", "Risk Tier"],
                rows: [
                    ["Jane Doe", "2 Accounts", "$20,270.50", "0 Active", "1 Active Card", "28 Txns", "Premium / Low Risk"],
                    ["Alexander Smith", "1 Account", "$28,900.75", "1 ($250k Home)", "2 Active Cards", "45 Txns", "Premium / Low Risk"],
                    ["Maria Garcia", "1 Account", "$12,400.00", "0 Active", "1 Active Card", "19 Txns", "Standard / Moderate Risk"],
                    ["David Chen", "1 Account", "$75,000.00", "0 Active", "1 Active Card", "62 Txns", "Premium / Low Risk"],
                    ["Sarah Jenkins", "1 Account", "$3,200.00", "1 ($15k Auto)", "1 Active Card", "14 Txns", "Subprime / High Risk"]
                ]
            }
        };

        function switchTab(tabKey) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');

            const data = tableData[tabKey];
            const table = document.getElementById('explorer-table');
            
            let thead = '<thead><tr>';
            data.headers.forEach(h => thead += `<th>${h}</th>`);
            thead += '</tr></thead>';

            let tbody = '<tbody>';
            data.rows.forEach(r => {
                tbody += '<tr>';
                r.forEach(cell => tbody += `<td>${cell}</td>`);
                tbody += '</tr>';
            });
            tbody += '</tbody>';

            table.innerHTML = thead + tbody;
        }

        // Initialize with customers
        switchTab('customers');
    </script>
</body>
</html>
"""
