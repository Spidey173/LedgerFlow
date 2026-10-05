-- Bank Data Warehouse DDL Schema (All 10 Core & Master Datasets)
-- Database: bank_dwh

DROP TABLE IF EXISTS support_tickets CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS branches CASCADE;
DROP TABLE IF EXISTS card_transactions CASCADE;
DROP TABLE IF EXISTS cards CASCADE;
DROP TABLE IF EXISTS loan_payments CASCADE;
DROP TABLE IF EXISTS loans CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- 1. Branches Table (Master)
CREATE TABLE branches (
    branch_id INT PRIMARY KEY,
    branch_name VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    opened_date DATE,
    ifsc_code VARCHAR(30) NOT NULL
);

-- 2. Employees Table (Master)
CREATE TABLE employees (
    employee_id INT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    branch_id INT NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    role VARCHAR(100) NOT NULL,
    hire_date DATE,
    salary NUMERIC(12, 2) NOT NULL CHECK (salary > 0)
);

-- 3. Customers Table (Core Dimension)
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    gender VARCHAR(20),
    date_of_birth DATE,
    city VARCHAR(100),
    state VARCHAR(100),
    phone VARCHAR(30),
    email VARCHAR(150) NOT NULL,
    occupation VARCHAR(100),
    annual_income NUMERIC(15, 2) CHECK (annual_income > 0),
    join_date DATE,
    credit_score INT CHECK (credit_score BETWEEN 300 AND 850)
);

-- 4. Accounts Table
CREATE TABLE accounts (
    account_id INT PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    branch_id INT NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    account_type VARCHAR(50) NOT NULL,
    balance NUMERIC(15, 2) NOT NULL CHECK (balance >= 0),
    open_date DATE,
    status VARCHAR(30) NOT NULL
);

-- 5. Transactions Table
CREATE TABLE transactions (
    transaction_id INT PRIMARY KEY,
    account_id INT NOT NULL REFERENCES accounts(account_id) ON DELETE RESTRICT,
    txn_date DATE NOT NULL,
    txn_type VARCHAR(50) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    channel VARCHAR(50),
    merchant_category VARCHAR(100)
);

-- 6. Loans Table
CREATE TABLE loans (
    loan_id INT PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    branch_id INT NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    loan_type VARCHAR(50) NOT NULL,
    loan_amount NUMERIC(15, 2) NOT NULL CHECK (loan_amount > 0),
    interest_rate NUMERIC(5, 2) NOT NULL,
    term_months INT NOT NULL CHECK (term_months > 0),
    start_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL
);

-- 7. Loan Payments Table
CREATE TABLE loan_payments (
    payment_id INT PRIMARY KEY,
    loan_id INT NOT NULL REFERENCES loans(loan_id) ON DELETE RESTRICT,
    payment_date DATE NOT NULL,
    amount_paid NUMERIC(15, 2) NOT NULL CHECK (amount_paid > 0),
    principal_component NUMERIC(15, 2) NOT NULL,
    interest_component NUMERIC(15, 2) NOT NULL,
    late_payment_flag SMALLINT NOT NULL CHECK (late_payment_flag IN (0, 1))
);

-- 8. Cards Table
CREATE TABLE cards (
    card_id INT PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    account_id INT NOT NULL REFERENCES accounts(account_id) ON DELETE RESTRICT,
    card_type VARCHAR(50) NOT NULL,
    issue_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    credit_limit NUMERIC(15, 2) NOT NULL DEFAULT 0 CHECK (credit_limit >= 0),
    status VARCHAR(30) NOT NULL
);

-- 9. Card Transactions Table
CREATE TABLE card_transactions (
    card_txn_id INT PRIMARY KEY,
    card_id INT NOT NULL REFERENCES cards(card_id) ON DELETE RESTRICT,
    txn_date DATE NOT NULL,
    merchant_category VARCHAR(100) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    is_fraud SMALLINT NOT NULL CHECK (is_fraud IN (0, 1))
);

-- 10. Support Tickets Table
CREATE TABLE support_tickets (
    ticket_id INT PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    issue_type VARCHAR(100) NOT NULL,
    date_opened DATE NOT NULL,
    date_resolved DATE,
    status VARCHAR(30) NOT NULL,
    satisfaction_score INT CHECK (satisfaction_score BETWEEN 1 AND 5)
);

-- Indexes on Foreign Keys and Temporal Columns
CREATE INDEX idx_accounts_customer_id ON accounts(customer_id);
CREATE INDEX idx_accounts_branch_id ON accounts(branch_id);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_txn_date ON transactions(txn_date);
CREATE INDEX idx_loans_customer_id ON loans(customer_id);
CREATE INDEX idx_loans_branch_id ON loans(branch_id);
CREATE INDEX idx_loan_payments_loan_id ON loan_payments(loan_id);
CREATE INDEX idx_cards_customer_id ON cards(customer_id);
CREATE INDEX idx_cards_account_id ON cards(account_id);
CREATE INDEX idx_card_txns_card_id ON card_transactions(card_id);
CREATE INDEX idx_card_txns_txn_date ON card_transactions(txn_date);
CREATE INDEX idx_employees_branch_id ON employees(branch_id);
CREATE INDEX idx_tickets_customer_id ON support_tickets(customer_id);
