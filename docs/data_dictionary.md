# LedgerFlow: Data Dictionary & Curated Schemas

This document details the curated schemas, constraints, field definitions, and business rules enforced across the 10 datasets and analytical marts of the LedgerFlow Enterprise Banking Data Warehouse.

---

## 1. Branches (`branches`)
Master lookup table defining physical banking branch networks and regulatory identifiers.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `branch_id` | INT | NO | **PK** | Unique identifier; positive integer | Branch ID (`101`) |
| `branch_name` | VARCHAR(150) | NO | None | Stripped whitespace, Title Case | Branch location name (`Connaught Place Central`) |
| `city` | VARCHAR(100) | NO | None | Title Case normalized | Branch municipality (`New Delhi`) |
| `state` | VARCHAR(100) | NO | None | Title Case normalized | State jurisdiction (`Delhi`) |
| `opened_date` | DATE | YES | None | Standardized `YYYY-MM-DD` | Branch commissioning date (`2015-06-01`) |
| `ifsc_code` | VARCHAR(30) | NO | None | Alphanumeric regulatory routing code | Bank branch IFSC code (`BANK0000101`) |

---

## 2. Employees (`employees`)
Staff and branch personnel managing operations and customer relationships.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `employee_id` | INT | NO | **PK** | Unique employee number | Employee identifier (`501`) |
| `name` | VARCHAR(150) | NO | None | Stripped whitespace, Title Case | Full employee name (`Rajesh Sharma`) |
| `branch_id` | INT | NO | **FK -> branches.branch_id** | Must exist in curated branches | Assigned branch location |
| `role` | VARCHAR(100) | NO | None | Valid roles: `Teller`, `Customer Service`, `Relationship Manager`, `Loan Officer`, `Branch Manager`, `Compliance Officer` | Staff title |
| `hire_date` | DATE | YES | None | Standardized `YYYY-MM-DD` | Employment commencement date |
| `salary` | NUMERIC(12,2)| NO | None | Strictly positive (`> 0.00`) | Base annual compensation |

---

## 3. Customers (`customers`)
Primary dimension table containing core demographic and financial profile data.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `customer_id` | INT | NO | **PK** | Unique identifier; cannot be empty | Unique customer number (`1001`) |
| `name` | VARCHAR(150) | NO | None | Whitespace stripped, converted to Title Case | Full legal name (`Pooja Garcia`) |
| `gender` | VARCHAR(20) | YES | None | Capitalized standard format | `Male`, `Female`, `Other` |
| `date_of_birth`| DATE | YES | None | Standardized `YYYY-MM-DD` | Date of birth (`1987-12-11`) |
| `city` | VARCHAR(100) | YES | None | Title Case normalized | Customer city (`Ahmedabad`) |
| `state` | VARCHAR(100) | YES | None | Title Case normalized | Customer state (`Gujarat`) |
| `phone` | VARCHAR(30) | YES | None | Normalized digits | Primary contact number |
| `email` | VARCHAR(150) | NO | None | Lowercase; RFC regex compliant | Valid email address (`customer0@mailbank.com`) |
| `occupation` | VARCHAR(100) | YES | None | Title Case normalized | Primary occupation (`Salaried - Private`) |
| `annual_income`| NUMERIC(15,2)| NO | None | Strictly positive (`> 0.0`) | Gross annual earnings in local currency |
| `join_date` | DATE | YES | None | Standardized `YYYY-MM-DD` | Customer onboarding date (`2018-02-23`) |
| `credit_score` | INT | NO | None | Strict FICO range (`300 - 850`) | Creditworthiness score (invalid quarantined to DLQ) |

---

## 4. Accounts (`accounts`)
Deposit and transactional accounts held by customers.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `account_id` | INT | NO | **PK** | Unique identifier; cannot be empty | Account number (`14742`) |
| `customer_id` | INT | NO | **FK -> customers.customer_id** | Must exist in curated customers | Owning customer ID |
| `branch_id` | INT | NO | **FK -> branches.branch_id** | Must exist in curated branches | Booking branch number |
| `account_type` | VARCHAR(50) | NO | None | Domain: `Savings`, `Current`, `Salary`, `Fixed Deposit`, `NRI` | Product classification |
| `balance` | NUMERIC(15,2)| NO | None | Non-negative (`>= 0.00`), 2 decimals | Available balance |
| `open_date` | DATE | YES | None | Standardized `YYYY-MM-DD` | Account opening date |
| `status` | VARCHAR(30) | NO | None | Domain: `Active`, `Dormant`, `Closed` | Operational status of account |

---

## 5. Transactions (`transactions`)
Core ledger of deposit, withdrawal, and transfer events on bank accounts.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `transaction_id`| INT | NO | **PK** | Unique transaction identifier | Transaction reference ID (`1`) |
| `account_id` | INT | NO | **FK -> accounts.account_id** | Must exist in curated accounts | Debited / Credited account |
| `txn_date` | DATE | NO | None | Standardized `YYYY-MM-DD` | Posting date |
| `txn_type` | VARCHAR(50) | NO | None | Domain: `Deposit`, `Withdrawal`, `Transfer Out`, `Transfer In`, `Fee Debit`, `Interest Credit` | Transaction type |
| `amount` | NUMERIC(15,2)| NO | None | Strictly positive (`> 0.00`) | Transaction amount |
| `channel` | VARCHAR(50) | YES | None | Domain: `Mobile App`, `Branch`, `ATM`, `UPI`, `POS`, `Online Banking` | Ingress channel |
| `merchant_category`| VARCHAR(100)| YES| None | Title Case normalized | Transaction categorization |

---

## 6. Loans (`loans`)
Credit facilities and disbursed loans.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `loan_id` | INT | NO | **PK** | Unique loan identifier | Loan facility ID |
| `customer_id` | INT | NO | **FK -> customers.customer_id** | Must exist in curated customers | Borrower customer ID |
| `branch_id` | INT | NO | **FK -> branches.branch_id** | Must exist in curated branches | Booking branch |
| `loan_type` | VARCHAR(50) | NO | None | Domain: `Auto Loan`, `Business Loan`, `Education Loan`, `Gold Loan`, `Home Loan`, `Personal Loan` | Product type |
| `loan_amount` | NUMERIC(15,2)| NO | None | Strictly positive (`> 0.00`) | Sanctioned principal amount |
| `interest_rate`| NUMERIC(5,2) | NO | None | Realistic range (`1.00% - 50.00%`)| Annual interest rate percentage |
| `term_months` | INT | NO | None | Positive integer (`> 0`) | Loan tenure in months (e.g. `60`) |
| `start_date` | DATE | NO | None | Standardized `YYYY-MM-DD` | Disbursal date |
| `status` | VARCHAR(30) | NO | None | Domain: `Active`, `Closed`, `Defaulted`, `Written Off` | Repayment and recovery status |

---

## 7. Loan Payments (`loan_payments`)
Repayment schedule events against loan facilities.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `payment_id` | INT | NO | **PK** | Unique repayment record | Repayment ID |
| `loan_id` | INT | NO | **FK -> loans.loan_id** | Must exist in curated loans | Repaid loan reference |
| `payment_date` | DATE | NO | None | Standardized `YYYY-MM-DD` | Installment realization date |
| `amount_paid` | NUMERIC(15,2)| NO | None | Strictly positive (`> 0.00`) | Total EMI amount paid |
| `principal_component`| NUMERIC(15,2)| NO | None | Non-negative; reconciles with interest | Principal reduction portion |
| `interest_component`| NUMERIC(15,2)| NO | None | Non-negative; reconciles with principal| Interest portion paid |
| `late_payment_flag` | SMALLINT | NO | None | Binary (`0` or `1`) | Flag indicating delinquency |

---

## 8. Cards (`cards`)
Debit and Credit card instruments issued to account holders.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `card_id` | INT | NO | **PK** | Unique card identifier | Card reference number |
| `customer_id` | INT | NO | **FK -> customers.customer_id** | Must exist in curated customers | Primary cardholder |
| `account_id` | INT | NO | **FK -> accounts.account_id** | Must exist in curated accounts | Settlement account |
| `card_type` | VARCHAR(50) | NO | None | Domain: `Debit`, `Credit - Classic`, `Credit - Gold`, `Credit - Platinum` | Card product tier |
| `issue_date` | DATE | NO | None | Standardized `YYYY-MM-DD` | Issue date |
| `expiry_date`| DATE | NO | None | Standardized `YYYY-MM-DD`; `expiry >= issue` | Expiration date |
| `credit_limit`| NUMERIC(15,2)| NO | None | Non-negative (`>= 0.00`) | Assigned credit limit |
| `status` | VARCHAR(30) | NO | None | Domain: `Active`, `Blocked`, `Expired` | Security card status |

---

## 9. Card Transactions (`card_transactions`)
Point of Sale, Online, and ATM authorizations executed with cards.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `card_txn_id` | INT | NO | **PK** | Unique card transaction ID | Authorization reference |
| `card_id` | INT | NO | **FK -> cards.card_id** | Must exist in curated cards | Swiped / tapped card ID |
| `txn_date` | DATE | NO | None | Standardized `YYYY-MM-DD` | Authorization timestamp |
| `merchant_category`| VARCHAR(100)| NO | None | Title Case normalized | Merchant domain (e.g. `Travel`, `Groceries`) |
| `amount` | NUMERIC(15,2)| NO | None | Strictly positive (`> 0.00`) | Settled amount |
| `is_fraud` | SMALLINT | NO | None | Binary (`0` = Clean, `1` = Fraudulent) | Machine learning fraud classification |

---

## 10. Support Tickets (`support_tickets`)
Customer service inquiries, complaints, and disputes.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ticket_id` | INT | NO | **PK** | Unique support ticket ID | Ticket reference (`8001`) |
| `customer_id` | INT | NO | **FK -> customers.customer_id** | Must exist in curated customers | Customer initiating issue |
| `issue_type` | VARCHAR(100) | NO | None | Title Case normalized | Category (`Card Dispute`, `Billing Query`) |
| `date_opened` | DATE | NO | None | Standardized `YYYY-MM-DD` | Incident report date |
| `date_resolved`| DATE | YES | None | Standardized `YYYY-MM-DD`; `resolved >= opened` | Resolution date (null if open) |
| `status` | VARCHAR(30) | NO | None | Domain: `Resolved`, `Open`, `Escalated` | Ticket lifecycle status |
| `satisfaction_score`| INT | YES | None | Integer between `1` and `5` | Post-resolution CSAT score |

---

## 11. Analytical Marts

### 11.1 Customer 360 (`customer_360`)
Materialized single-view of the customer aggregating accounts, credit, loan balances, lifetime spending, and automated risk scoring.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `customer_id` | INT (PK) | Customer identifier |
| `name` | VARCHAR(150) | Full legal name |
| `annual_income` | NUMERIC(15,2) | Verified gross income |
| `credit_score` | INT | FICO / CIBIL credit score |
| `total_accounts` | INT | Total active/dormant deposit accounts |
| `total_deposit_balance` | NUMERIC(15,2) | Total funds on deposit |
| `total_loans` | INT | Total lifetime loans contracted |
| `active_loan_amount` | NUMERIC(15,2) | Outstanding debt across active loans |
| `total_cards` | INT | Number of issued card instruments |
| `total_credit_limit` | NUMERIC(15,2) | Aggregate revolving credit line |
| `lifetime_transactions` | INT | Count of ledger transactions |
| `lifetime_transaction_volume` | NUMERIC(15,2) | Total transaction turnover |
| `customer_segment` | VARCHAR(50) | Dynamic Tier: `Premium / Low Risk`, `Standard / Moderate Risk`, `Subprime / High Risk` |

### 11.2 Monthly Customer Summary (`monthly_customer_summary`)
Monthly financial cashflow mart detailing credit/debit totals, card spend, and outstanding obligations per customer.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `customer_id` | INT | Customer identifier |
| `customer_name` | VARCHAR(150) | Customer legal name |
| `month_year` | VARCHAR(7) | Calendar month (`YYYY-MM`) |
| `annual_income` | NUMERIC(15,2) | Customer annual income |
| `credit_score` | INT | Credit score |
| `bank_transactions_count` | INT | Count of account ledger transactions in the month |
| `total_income_credits` | NUMERIC(15,2) | Inflow volume (Deposits, Transfers In, Interest) |
| `total_expense_debits` | NUMERIC(15,2) | Outflow volume (Withdrawals, Transfers Out, Fees) |
| `net_cashflow` | NUMERIC(15,2) | Net monthly cash balance delta (`credits - debits`) |
| `total_card_spend` | NUMERIC(15,2) | Credit and debit card authorization total |
| `card_fraud_count` | INT | Flagged fraudulent card transactions |
| `outstanding_loan_balance` | NUMERIC(15,2) | Current active loan debt |

### 11.3 Monthly Branch Summary (`monthly_branch_summary`)
Operational metrics aggregating branch-level transactional turnover, active customer counts, and liquidity movements.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `branch_id` | INT | Branch identifier |
| `month_year` | VARCHAR(7) | Calendar month (`YYYY-MM`) |
| `active_customers` | INT | Distinct customers transacting at branch in the month |
| `total_accounts` | INT | Distinct accounts domiciled at branch |
| `total_transactions` | INT | Number of ledger transactions |
| `total_volume` | NUMERIC(15,2) | Aggregate transaction turnover |
| `deposit_volume` | NUMERIC(15,2) | Total deposits received |
| `withdrawal_volume` | NUMERIC(15,2) | Total withdrawals disbursed |
