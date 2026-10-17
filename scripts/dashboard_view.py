"""
LedgerFlow — Executive Banking Data Platform & Lakehouse Portal
---------------------------------------------------------------
Clean, professional corporate red theme (HSBC / Santander style)
featuring real interactive Chart.js visualizations, KPI cards, and data explorer.
"""

def render_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LedgerFlow — Banking Data Engineering Platform</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --red-primary: #A61C1C;
            --red-dark: #7A1212;
            --red-hover: #8C1616;
            --red-light: #FDF2F2;
            --red-border: #F8D7DA;
            --bg-page: #F5F6F8;
            --bg-card: #FFFFFF;
            --text-title: #1A1F2C;
            --text-body: #4A5568;
            --text-muted: #718096;
            --border-color: #E2E8F0;
            --border-subtle: #EDF2F7;
            --green: #2B8A3E;
            --gray-tag: #EDF2F7;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'IBM Plex Sans', 'Segoe UI', -apple-system, sans-serif;
            background-color: var(--bg-page);
            color: var(--text-body);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }

        /* Top Brand Header */
        .top-navbar {
            background-color: var(--red-primary);
            color: #FFFFFF;
            padding: 14px 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        }

        .brand-section {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-logo {
            font-weight: 700;
            font-size: 19px;
            letter-spacing: -0.01em;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .brand-tag {
            font-size: 11px;
            background-color: rgba(255, 255, 255, 0.2);
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .nav-btn {
            background-color: rgba(255, 255, 255, 0.12);
            color: #FFFFFF;
            padding: 7px 14px;
            border-radius: 5px;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            transition: background-color 0.15s ease;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .nav-btn:hover {
            background-color: rgba(255, 255, 255, 0.25);
        }

        .nav-btn-white {
            background-color: #FFFFFF;
            color: var(--red-primary);
            border: 1px solid #FFFFFF;
        }

        .nav-btn-white:hover {
            background-color: #FFF5F5;
            color: var(--red-dark);
        }

        /* Main Container */
        .main-container {
            max-width: 1280px;
            margin: 28px auto;
            padding: 0 24px 48px;
        }

        /* Platform Introduction Banner */
        .intro-banner {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-left: 5px solid var(--red-primary);
            border-radius: 6px;
            padding: 20px 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }

        .intro-text h1 {
            font-size: 22px;
            font-weight: 700;
            color: var(--text-title);
            margin-bottom: 4px;
        }

        .intro-text p {
            font-size: 14px;
            color: var(--text-muted);
        }

        .system-status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 600;
            color: var(--green);
            background-color: #EBFBEE;
            border: 1px solid #D3F9D8;
            padding: 6px 12px;
            border-radius: 4px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--green);
            border-radius: 50%;
        }

        /* KPI Cards Grid */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(195px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 18px 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
            transition: border-color 0.15s ease;
        }

        .kpi-card:hover {
            border-color: #CBD5E1;
        }

        .kpi-label {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 6px;
        }

        .kpi-number {
            font-size: 26px;
            font-weight: 700;
            color: var(--text-title);
            font-family: 'IBM Plex Mono', monospace;
            letter-spacing: -0.02em;
        }

        .kpi-subtext {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .kpi-highlight {
            color: var(--red-primary);
        }

        /* Charts Section */
        .charts-row {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }

        @media (max-width: 960px) {
            .charts-row {
                grid-template-columns: 1fr;
            }
        }

        .chart-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 20px 22px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }

        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-subtle);
        }

        .chart-header h3 {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-title);
        }

        .chart-header .chart-meta {
            font-size: 12px;
            color: var(--text-muted);
        }

        .chart-container {
            position: relative;
            height: 270px;
            width: 100%;
        }

        /* Architecture Steps Horizontal Bar */
        .pipeline-flow {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 20px 24px;
            margin-bottom: 24px;
        }

        .flow-headline {
            font-size: 14px;
            font-weight: 700;
            color: var(--text-title);
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .flow-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
        }

        .flow-box {
            background: #FAFAFA;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 14px 16px;
            border-top: 3px solid var(--red-primary);
        }

        .flow-num {
            font-size: 11px;
            font-weight: 700;
            color: var(--red-primary);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 4px;
        }

        .flow-name {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-title);
            margin-bottom: 3px;
        }

        .flow-detail {
            font-size: 12px;
            color: var(--text-muted);
        }

        /* Interactive Table Section */
        .table-section {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
            margin-bottom: 32px;
        }

        .table-toolbar {
            padding: 16px 20px;
            background: #FFFFFF;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }

        .table-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-title);
        }

        .tab-buttons {
            display: flex;
            gap: 6px;
        }

        .tab-btn {
            background: #EDF2F7;
            border: 1px solid #E2E8F0;
            color: var(--text-body);
            padding: 6px 14px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .tab-btn.active {
            background: var(--red-primary);
            color: #FFFFFF;
            border-color: var(--red-primary);
        }

        .tab-btn:hover:not(.active) {
            background: #E2E8F0;
        }

        .table-wrapper {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th {
            background: #F8FAFC;
            color: var(--text-muted);
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            padding: 11px 16px;
            border-bottom: 1px solid var(--border-color);
        }

        td {
            padding: 12px 16px;
            font-size: 13px;
            border-bottom: 1px solid #F1F5F9;
            color: var(--text-title);
            font-family: 'IBM Plex Mono', monospace;
        }

        tr:hover td {
            background-color: #F8FAFC;
        }

        /* Footer */
        .footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 13px;
            padding-top: 24px;
            border-top: 1px solid var(--border-color);
        }
    </style>
</head>
<body>

    <!-- Red Brand Header -->
    <header class="top-navbar">
        <div class="brand-section">
            <div class="brand-logo">
                <span>🏦</span> LedgerFlow
            </div>
            <span class="brand-tag">Banking Data Warehouse</span>
        </div>
        <div class="nav-links">
            <a href="/audit-report" class="nav-btn">📑 Quality Audit Report</a>
            <a href="/docs" class="nav-btn nav-btn-white">⚡ Swagger API Docs</a>
            <a href="https://github.com/Spidey173/LedgerFlow" target="_blank" class="nav-btn">🐙 GitHub</a>
            <a href="/?format=json" class="nav-btn">💾 JSON</a>
        </div>
    </header>

    <!-- Content Body -->
    <main class="main-container">

        <!-- Intro -->
        <section class="intro-banner">
            <div class="intro-text">
                <h1>Banking Data Pipeline & Analytical Warehouse</h1>
                <p>Topological Batch ETL, AWS S3 Lakehouse Ingestion & Automated Dead Letter Queue (DLQ) across 5.86M banking records.</p>
            </div>
            <div class="system-status">
                <span class="status-dot"></span>
                <span>PostgreSQL Warehouse Active • 41 Tests Passing</span>
            </div>
        </section>

        <!-- KPI Grid -->
        <section class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Deposits</div>
                <div class="kpi-number kpi-highlight">$3.98B</div>
                <div class="kpi-subtext">Active Account Balances</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Curated Customers</div>
                <div class="kpi-number">55,050</div>
                <div class="kpi-subtext">91.75% Verification Rate</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Curated Accounts</div>
                <div class="kpi-number">87,177</div>
                <div class="kpi-subtext">Savings, Current, FD, NRI</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Transactions</div>
                <div class="kpi-number">1,835,551</div>
                <div class="kpi-subtext">Topologically Validated</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Active Loans</div>
                <div class="kpi-number">$5.46B</div>
                <div class="kpi-subtext">13,098 Active Portfolios</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Audited DLQ</div>
                <div class="kpi-number" style="color: var(--red-primary);">720,520</div>
                <div class="kpi-subtext">Isolated with Rejection Reason</div>
            </div>
        </section>

        <!-- Charts Row -->
        <section class="charts-row">
            <!-- Ingestion Funnel Chart -->
            <div class="chart-card">
                <div class="chart-header">
                    <h3>Data Quality & Ingestion Funnel by Entity</h3>
                    <span class="chart-meta">Curated Clean vs. Quarantined DLQ</span>
                </div>
                <div class="chart-container">
                    <canvas id="ingestionBarChart"></canvas>
                </div>
            </div>

            <!-- Customer Risk Breakdown Chart -->
            <div class="chart-card">
                <div class="chart-header">
                    <h3>Customer Risk Portfolio</h3>
                    <span class="chart-meta">Credit Score Segments</span>
                </div>
                <div class="chart-container">
                    <canvas id="segmentDoughnutChart"></canvas>
                </div>
            </div>
        </section>

        <!-- Pipeline Architecture Flow -->
        <section class="pipeline-flow">
            <div class="flow-headline">End-to-End Enterprise Architecture</div>
            <div class="flow-grid">
                <div class="flow-box">
                    <div class="flow-num">Stage 01</div>
                    <div class="flow-name">Secure Payload</div>
                    <div class="flow-detail">AES-256 Protected ZIP</div>
                </div>
                <div class="flow-box">
                    <div class="flow-num">Stage 02</div>
                    <div class="flow-name">AWS SSM Key</div>
                    <div class="flow-detail">KMS SecureString Decryption</div>
                </div>
                <div class="flow-box">
                    <div class="flow-num">Stage 03</div>
                    <div class="flow-name">AWS S3 Bronze</div>
                    <div class="flow-detail">Raw Object Storage</div>
                </div>
                <div class="flow-box">
                    <div class="flow-num">Stage 04</div>
                    <div class="flow-name">Data Quality</div>
                    <div class="flow-detail">41 Pytest Rules & DLQ</div>
                </div>
                <div class="flow-box">
                    <div class="flow-num">Stage 05</div>
                    <div class="flow-name">PostgreSQL</div>
                    <div class="flow-detail">Customer 360 & Analytics</div>
                </div>
            </div>
        </section>

        <!-- Live Relational Data Explorer -->
        <section class="table-section">
            <div class="table-toolbar">
                <div class="table-title">Live Warehouse Data Explorer</div>
                <div class="tab-buttons">
                    <button class="tab-btn active" onclick="switchTable('customers')">Customers</button>
                    <button class="tab-btn" onclick="switchTable('accounts')">Accounts</button>
                    <button class="tab-btn" onclick="switchTable('transactions')">Transactions</button>
                    <button class="tab-btn" onclick="switchTable('c360')">Customer 360</button>
                </div>
            </div>
            <div class="table-wrapper">
                <table id="dataTable">
                    <!-- Populated by JavaScript -->
                </table>
            </div>
        </section>

        <footer class="footer">
            LedgerFlow Banking Platform • Built with Python, PostgreSQL, AWS S3, and FastAPI • 41 Unit Tests Passing
        </footer>
    </main>

    <script>
        // 1. Data Ingestion Bar Chart
        const ctxBar = document.getElementById('ingestionBarChart').getContext('2d');
        new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: ['Transactions', 'Cards Txns', 'Payments', 'Accounts', 'Customers', 'Cards', 'Loans'],
                datasets: [
                    {
                        label: 'Curated Clean Records',
                        data: [1835551, 2521980, 549015, 87177, 55050, 54643, 20137],
                        backgroundColor: '#A61C1C',
                        borderRadius: 4
                    },
                    {
                        label: 'Quarantined DLQ',
                        data: [164449, 478020, 50985, 7823, 4950, 10357, 1863],
                        backgroundColor: '#CBD5E1',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            font: { family: 'IBM Plex Sans', size: 12 },
                            boxWidth: 14
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + Number(context.raw).toLocaleString() + ' rows';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'IBM Plex Sans', size: 11 } }
                    },
                    y: {
                        grid: { color: '#EDF2F7' },
                        ticks: {
                            callback: function(val) {
                                return (val >= 1000000 ? (val / 1000000) + 'M' : (val / 1000) + 'k');
                            },
                            font: { family: 'IBM Plex Mono', size: 11 }
                        }
                    }
                }
            }
        });

        // 2. Customer Risk Segment Doughnut Chart
        const ctxPie = document.getElementById('segmentDoughnutChart').getContext('2d');
        new Chart(ctxPie, {
            type: 'doughnut',
            data: {
                labels: ['Subprime / High Risk', 'Standard / Moderate Risk', 'Premium / Low Risk'],
                datasets: [{
                    data: [34871, 15121, 5058],
                    backgroundColor: ['#A61C1C', '#E2A03F', '#2B8A3E'],
                    borderWidth: 2,
                    borderColor: '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: { family: 'IBM Plex Sans', size: 11 },
                            boxWidth: 12,
                            padding: 12
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = 55050;
                                const pct = ((context.raw / total) * 100).toFixed(1);
                                return context.label + ': ' + Number(context.raw).toLocaleString() + ' (' + pct + '%)';
                            }
                        }
                    }
                },
                cutout: '62%'
            }
        });

        // 3. Interactive Data Table
        const datasets = {
            customers: {
                headers: ["Cust ID", "Name", "City", "State", "Occupation", "Income", "Credit Score", "Risk Tier"],
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
                headers: ["Txn ID", "Account ID", "Date", "Type", "Amount", "Channel", "Merchant Category"],
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

        function switchTable(name) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            const item = datasets[name];
            const table = document.getElementById('dataTable');

            let ths = '<thead><tr>';
            item.headers.forEach(h => ths += `<th>${h}</th>`);
            ths += '</tr></thead>';

            let trs = '<tbody>';
            item.rows.forEach(r => {
                trs += '<tr>';
                r.forEach(c => trs += `<td>${c}</td>`);
                trs += '</tr>';
            });
            trs += '</tbody>';

            table.innerHTML = ths + trs;
        }

        // Initialize table with customers view
        switchTable('customers');
    </script>
</body>
</html>
"""
