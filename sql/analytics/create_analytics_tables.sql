-- Bank Data Warehouse Analytics Tables
-- Database: bank_dwh

DROP TABLE IF EXISTS monthly_customer_summary;
DROP TABLE IF EXISTS monthly_branch_summary;
DROP TABLE IF EXISTS customer_360;

-- 1. Monthly Customer Summary
CREATE TABLE monthly_customer_summary AS
WITH txns AS (
    SELECT 
        a.customer_id,
        TO_CHAR(t.txn_date, 'YYYY-MM') AS month_year,
        COUNT(t.transaction_id) AS total_transactions,
        SUM(CASE WHEN t.txn_type IN ('Deposit', 'Transfer In', 'Interest Credit') THEN t.amount ELSE 0 END) AS total_credits,
        SUM(CASE WHEN t.txn_type IN ('Withdrawal', 'Transfer Out', 'Fee Debit') THEN t.amount ELSE 0 END) AS total_debits
    FROM accounts a
    JOIN transactions t ON a.account_id = t.account_id
    GROUP BY a.customer_id, TO_CHAR(t.txn_date, 'YYYY-MM')
),
loans_agg AS (
    SELECT 
        l.customer_id,
        COUNT(DISTINCT l.loan_id) AS active_loans,
        SUM(l.loan_amount) AS total_loan_balance
    FROM loans l
    WHERE l.status = 'Active'
    GROUP BY l.customer_id
),
cards_agg AS (
    SELECT 
        c.customer_id,
        TO_CHAR(ct.txn_date, 'YYYY-MM') AS month_year,
        COUNT(ct.card_txn_id) AS card_txns_count,
        SUM(ct.amount) AS total_card_spend,
        SUM(ct.is_fraud) AS fraud_txns_count
    FROM cards c
    JOIN card_transactions ct ON c.card_id = ct.card_id
    GROUP BY c.customer_id, TO_CHAR(ct.txn_date, 'YYYY-MM')
)
SELECT 
    c.customer_id,
    c.name AS customer_name,
    COALESCE(tx.month_year, cd.month_year) AS month_year,
    c.annual_income,
    c.credit_score,
    COALESCE(tx.total_transactions, 0) AS bank_transactions_count,
    COALESCE(tx.total_credits, 0) AS total_income_credits,
    COALESCE(tx.total_debits, 0) AS total_expense_debits,
    COALESCE(tx.total_credits, 0) - COALESCE(tx.total_debits, 0) AS net_cashflow,
    COALESCE(cd.total_card_spend, 0) AS total_card_spend,
    COALESCE(cd.fraud_txns_count, 0) AS card_fraud_count,
    COALESCE(la.total_loan_balance, 0) AS outstanding_loan_balance
FROM customers c
LEFT JOIN txns tx ON c.customer_id = tx.customer_id
LEFT JOIN cards_agg cd ON c.customer_id = cd.customer_id AND tx.month_year = cd.month_year
LEFT JOIN loans_agg la ON c.customer_id = la.customer_id;

CREATE INDEX idx_mcs_customer_month ON monthly_customer_summary(customer_id, month_year);


-- 2. Monthly Branch Summary
CREATE TABLE monthly_branch_summary AS
SELECT 
    a.branch_id,
    TO_CHAR(t.txn_date, 'YYYY-MM') AS month_year,
    COUNT(DISTINCT a.customer_id) AS active_customers,
    COUNT(DISTINCT a.account_id) AS total_accounts,
    COUNT(t.transaction_id) AS total_transactions,
    SUM(t.amount) AS total_volume,
    SUM(CASE WHEN t.txn_type IN ('Deposit', 'Transfer In') THEN t.amount ELSE 0 END) AS deposit_volume,
    SUM(CASE WHEN t.txn_type IN ('Withdrawal', 'Transfer Out') THEN t.amount ELSE 0 END) AS withdrawal_volume
FROM accounts a
JOIN transactions t ON a.account_id = t.account_id
GROUP BY a.branch_id, TO_CHAR(t.txn_date, 'YYYY-MM');

CREATE INDEX idx_mbs_branch_month ON monthly_branch_summary(branch_id, month_year);


-- 3. Customer 360 Consolidated Profile
CREATE TABLE customer_360 AS
WITH acc_summary AS (
    SELECT 
        customer_id,
        COUNT(account_id) AS total_accounts,
        SUM(balance) AS total_deposit_balance
    FROM accounts
    GROUP BY customer_id
),
loan_summary AS (
    SELECT 
        customer_id,
        COUNT(loan_id) AS total_loans,
        SUM(loan_amount) AS total_loan_amount,
        SUM(CASE WHEN status = 'Active' THEN loan_amount ELSE 0 END) AS active_loan_amount
    FROM loans
    GROUP BY customer_id
),
card_summary AS (
    SELECT 
        customer_id,
        COUNT(card_id) AS total_cards,
        SUM(credit_limit) AS total_credit_limit
    FROM cards
    GROUP BY customer_id
),
txn_totals AS (
    SELECT 
        a.customer_id,
        COUNT(t.transaction_id) AS lifetime_transactions,
        SUM(t.amount) AS lifetime_transaction_volume
    FROM accounts a
    JOIN transactions t ON a.account_id = t.account_id
    GROUP BY a.customer_id
)
SELECT 
    c.customer_id,
    c.name,
    c.gender,
    c.city,
    c.state,
    c.email,
    c.occupation,
    c.annual_income,
    c.credit_score,
    c.join_date,
    COALESCE(a.total_accounts, 0) AS total_accounts,
    COALESCE(a.total_deposit_balance, 0) AS total_deposit_balance,
    COALESCE(l.total_loans, 0) AS total_loans,
    COALESCE(l.active_loan_amount, 0) AS active_loan_amount,
    COALESCE(cd.total_cards, 0) AS total_cards,
    COALESCE(cd.total_credit_limit, 0) AS total_credit_limit,
    COALESCE(t.lifetime_transactions, 0) AS lifetime_transactions,
    COALESCE(t.lifetime_transaction_volume, 0) AS lifetime_transaction_volume,
    -- Financial Health Indicator
    CASE 
        WHEN c.credit_score >= 750 AND COALESCE(a.total_deposit_balance, 0) > 50000 THEN 'Premium / Low Risk'
        WHEN c.credit_score >= 650 THEN 'Standard / Moderate Risk'
        ELSE 'Subprime / High Risk'
    END AS customer_segment
FROM customers c
LEFT JOIN acc_summary a ON c.customer_id = a.customer_id
LEFT JOIN loan_summary l ON c.customer_id = l.customer_id
LEFT JOIN card_summary cd ON c.customer_id = cd.customer_id
LEFT JOIN txn_totals t ON c.customer_id = t.customer_id;

CREATE UNIQUE INDEX idx_c360_customer_id ON customer_360(customer_id);
