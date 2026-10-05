-- 25 Production Business & Financial Analytics Queries
-- Database: bank_dwh

-- Query 1: Top 10 Customers by Total Lifetime Transaction Spend / Volume
SELECT customer_id, name, city, annual_income, lifetime_transaction_volume
FROM customer_360
ORDER BY lifetime_transaction_volume DESC
LIMIT 10;

-- Query 2: Monthly Transaction Volume and Value Trend
SELECT 
    TO_CHAR(txn_date, 'YYYY-MM') AS txn_month,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_volume,
    ROUND(AVG(amount), 2) AS avg_ticket_size
FROM transactions
GROUP BY TO_CHAR(txn_date, 'YYYY-MM')
ORDER BY txn_month;

-- Query 3: Loan Portfolio Summary by Loan Type
SELECT 
    loan_type,
    COUNT(*) AS total_loans,
    ROUND(SUM(loan_amount), 2) AS total_principal_disbursed,
    ROUND(AVG(interest_rate), 2) AS avg_interest_rate,
    ROUND(AVG(loan_amount), 2) AS avg_ticket_size
FROM loans
GROUP BY loan_type
ORDER BY total_principal_disbursed DESC;

-- Query 4: Non-Performing Assets (NPA) & Loan Default Rate Analysis
SELECT 
    status AS loan_status,
    COUNT(*) AS loan_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct_of_portfolio,
    ROUND(SUM(loan_amount), 2) AS total_exposure
FROM loans
GROUP BY status
ORDER BY total_exposure DESC;

-- Query 5: Average Deposit Balance by Branch
SELECT 
    branch_id,
    COUNT(account_id) AS total_accounts,
    ROUND(AVG(balance), 2) AS avg_account_balance,
    ROUND(SUM(balance), 2) AS total_branch_deposits
FROM accounts
GROUP BY branch_id
ORDER BY total_branch_deposits DESC
LIMIT 15;

-- Query 6: Dormant Accounts with Substantial Balances (> 50,000)
SELECT account_id, customer_id, branch_id, account_type, balance, open_date
FROM accounts
WHERE status = 'Dormant' AND balance > 50000
ORDER BY balance DESC
LIMIT 20;

-- Query 7: Customers with Multiple Active Loans (Cross-Indebtedness)
SELECT 
    c.customer_id,
    c.name,
    c.annual_income,
    COUNT(l.loan_id) AS active_loan_count,
    ROUND(SUM(l.loan_amount), 2) AS total_borrowed
FROM customers c
JOIN loans l ON c.customer_id = l.customer_id
WHERE l.status = 'Active'
GROUP BY c.customer_id, c.name, c.annual_income
HAVING COUNT(l.loan_id) > 1
ORDER BY active_loan_count DESC, total_borrowed DESC
LIMIT 20;

-- Query 8: Top Merchant Categories by Card Spend
SELECT 
    merchant_category,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_spend,
    ROUND(AVG(amount), 2) AS avg_spend
FROM card_transactions
GROUP BY merchant_category
ORDER BY total_spend DESC;

-- Query 9: Card Fraud Exposure Analysis by Merchant Category
SELECT 
    merchant_category,
    COUNT(*) AS total_txns,
    SUM(is_fraud) AS fraudulent_txns,
    ROUND(SUM(is_fraud) * 100.0 / COUNT(*), 3) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END), 2) AS total_fraud_loss
FROM card_transactions
GROUP BY merchant_category
ORDER BY total_fraud_loss DESC;

-- Query 10: Late Payment Delinquency Ratio on Loans
SELECT 
    l.loan_type,
    COUNT(lp.payment_id) AS total_installments_paid,
    SUM(lp.late_payment_flag) AS late_installments_count,
    ROUND(SUM(lp.late_payment_flag) * 100.0 / COUNT(lp.payment_id), 2) AS delinquency_rate_pct
FROM loan_payments lp
JOIN loans l ON lp.loan_id = l.loan_id
GROUP BY l.loan_type
ORDER BY delinquency_rate_pct DESC;

-- Query 11: Customer Segment Breakdown in Customer 360
SELECT 
    customer_segment,
    COUNT(*) AS customer_count,
    ROUND(AVG(annual_income), 2) AS avg_annual_income,
    ROUND(AVG(total_deposit_balance), 2) AS avg_deposit_balance,
    ROUND(AVG(credit_score), 1) AS avg_credit_score
FROM customer_360
GROUP BY customer_segment
ORDER BY avg_deposit_balance DESC;

-- Query 12: Channels with Highest Transaction Velocity
SELECT 
    channel,
    COUNT(*) AS txn_count,
    ROUND(SUM(amount), 2) AS total_volume,
    ROUND(AVG(amount), 2) AS avg_transaction_value
FROM transactions
GROUP BY channel
ORDER BY txn_count DESC;

-- Query 13: Credit Card Utilization Analysis by Card Tier
SELECT 
    card_type,
    COUNT(*) AS card_count,
    ROUND(AVG(credit_limit), 2) AS avg_credit_limit,
    ROUND(SUM(credit_limit), 2) AS total_credit_exposure
FROM cards
WHERE card_type LIKE 'Credit%'
GROUP BY card_type
ORDER BY total_credit_exposure DESC;

-- Query 14: Top 10 High Net Worth Customers (Balance to Income Ratio)
SELECT 
    customer_id,
    name,
    annual_income,
    total_deposit_balance,
    ROUND(total_deposit_balance / NULLIF(annual_income, 0), 2) AS balance_to_income_ratio
FROM customer_360
WHERE annual_income > 1000000
ORDER BY total_deposit_balance DESC
LIMIT 10;

-- Query 15: Interest vs Principal Realization on Loans
SELECT 
    TO_CHAR(payment_date, 'YYYY') AS payment_year,
    ROUND(SUM(amount_paid), 2) AS total_collections,
    ROUND(SUM(principal_component), 2) AS total_principal_recovered,
    ROUND(SUM(interest_component), 2) AS total_interest_earned,
    ROUND(SUM(interest_component) * 100.0 / SUM(amount_paid), 2) AS interest_yield_pct
FROM loan_payments
GROUP BY TO_CHAR(payment_date, 'YYYY')
ORDER BY payment_year;

-- Query 16: Account Type Distribution and Average Holdings
SELECT 
    account_type,
    COUNT(*) AS account_count,
    ROUND(SUM(balance), 2) AS total_balance,
    ROUND(AVG(balance), 2) AS avg_balance
FROM accounts
GROUP BY account_type
ORDER BY total_balance DESC;

-- Query 17: Branch Efficiency - Deposits vs Disbursed Loans
SELECT 
    a.branch_id,
    ROUND(SUM(DISTINCT a.balance), 2) AS total_deposits,
    ROUND(COALESCE(SUM(DISTINCT l.loan_amount), 0), 2) AS total_loans_issued
FROM accounts a
LEFT JOIN loans l ON a.branch_id = l.branch_id
GROUP BY a.branch_id
ORDER BY total_deposits DESC
LIMIT 15;

-- Query 18: Cardholder Fraud Victims Profiling
SELECT 
    c.customer_id,
    c.name,
    c.city,
    COUNT(ct.card_txn_id) AS fraudulent_events,
    ROUND(SUM(ct.amount), 2) AS total_fraud_amount
FROM card_transactions ct
JOIN cards cd ON ct.card_id = cd.card_id
JOIN customers c ON cd.customer_id = c.customer_id
WHERE ct.is_fraud = 1
GROUP BY c.customer_id, c.name, c.city
ORDER BY total_fraud_amount DESC
LIMIT 15;

-- Query 19: Monthly Cashflow Surpluses (Top Saver Customers)
SELECT 
    customer_id,
    customer_name,
    month_year,
    total_income_credits,
    total_expense_debits,
    net_cashflow
FROM monthly_customer_summary
WHERE net_cashflow > 100000
ORDER BY net_cashflow DESC
LIMIT 15;

-- Query 20: Credit Score Tier vs Loan Default Probability
SELECT 
    CASE 
        WHEN c.credit_score >= 750 THEN 'Excellent (750-850)'
        WHEN c.credit_score >= 650 THEN 'Good (650-749)'
        WHEN c.credit_score >= 550 THEN 'Fair (550-649)'
        ELSE 'Poor (< 550)'
    END AS credit_tier,
    COUNT(l.loan_id) AS total_loans,
    SUM(CASE WHEN l.status IN ('Defaulted', 'Written Off') THEN 1 ELSE 0 END) AS defaulted_loans,
    ROUND(SUM(CASE WHEN l.status IN ('Defaulted', 'Written Off') THEN 1 ELSE 0 END) * 100.0 / COUNT(l.loan_id), 2) AS default_rate_pct
FROM loans l
JOIN customers c ON l.customer_id = c.customer_id
GROUP BY 1
ORDER BY default_rate_pct DESC;

-- Query 21: Highest Daily Transaction Velocity by Channel
SELECT 
    txn_date,
    channel,
    COUNT(*) AS daily_txns,
    ROUND(SUM(amount), 2) AS daily_amount
FROM transactions
GROUP BY txn_date, channel
ORDER BY daily_amount DESC
LIMIT 10;

-- Query 22: Cards Nearing Expiration
SELECT card_id, customer_id, card_type, expiry_date, status
FROM cards
WHERE status = 'Active' AND expiry_date BETWEEN '2026-09-30' AND '2027-03-31'
ORDER BY expiry_date ASC
LIMIT 15;

-- Query 23: Geographic Concentration of Depositors by State
SELECT 
    state,
    COUNT(DISTINCT customer_id) AS customer_count,
    ROUND(SUM(total_deposit_balance), 2) AS aggregate_state_deposits,
    ROUND(AVG(total_deposit_balance), 2) AS avg_deposits_per_customer
FROM customer_360
GROUP BY state
ORDER BY aggregate_state_deposits DESC
LIMIT 10;

-- Query 24: Customer Age Group vs Banking Channel Preferences
SELECT 
    CASE 
        WHEN EXTRACT(YEAR FROM AGE(c.date_of_birth)) < 30 THEN 'Gen Z (< 30)'
        WHEN EXTRACT(YEAR FROM AGE(c.date_of_birth)) < 50 THEN 'Millennials (30-49)'
        ELSE 'Seniors (50+)'
    END AS age_cohort,
    t.channel,
    COUNT(*) AS txn_count,
    ROUND(SUM(t.amount), 2) AS total_channel_spend
FROM customers c
JOIN accounts a ON c.customer_id = a.customer_id
JOIN transactions t ON a.account_id = t.account_id
GROUP BY 1, 2
ORDER BY 1, txn_count DESC;

-- Query 25: Overall Bank Health & KPI Snapshot
SELECT 
    (SELECT COUNT(*) FROM customers) AS total_curated_customers,
    (SELECT COUNT(*) FROM accounts) AS total_curated_accounts,
    (SELECT ROUND(SUM(balance), 2) FROM accounts) AS total_deposit_holdings,
    (SELECT COUNT(*) FROM loans WHERE status = 'Active') AS total_active_loans,
    (SELECT ROUND(SUM(loan_amount), 2) FROM loans WHERE status = 'Active') AS active_loan_portfolio,
    (SELECT COUNT(*) FROM cards WHERE status = 'Active') AS active_cards,
    (SELECT COUNT(*) FROM transactions) AS lifetime_transactions_recorded,
    (SELECT COUNT(*) FROM card_transactions) AS lifetime_card_transactions_recorded;
