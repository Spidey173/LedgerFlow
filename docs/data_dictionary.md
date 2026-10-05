# LedgerFlow: Data Dictionary & Curated Schemas
 
This document details the curated schemas, constraints, field definitions, and business rules enforced across the LedgerFlow Enterprise Banking Data Warehouse.

---

## 1. Customers (`customers`)
Primary dimension table containing core demographic and financial profile data.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `customer_id` | INT | NO | **PK** | Unique identifier; cannot be empty | Unique customer number (e.g. `1001`) |
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

## 2. Accounts (`accounts`)
Deposit and transactional accounts held by customers.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `account_id` | INT | NO | **PK** | Unique identifier; cannot be empty | Account number (`14742`) |
| `customer_id` | INT | NO | **FK -> customers.customer_id** | Must exist in curated customers | Owning customer ID |
| `branch_id` | INT | NO | None | Master branch lookup | Associated branch number |
| `account_type` | VARCHAR(50) | NO | None | Domain: `Savings`, `Current`, `Salary`, `Fixed Deposit`, `NRI` | Product classification |
| `balance` | NUMERIC(15,2)| NO | None | Non-negative (`>= 0.00`), 2 decimals | Available balance |
| `open_date` | DATE | YES | None | Standardized `YYYY-MM-DD` | Account opening date |
| `status` | VARCHAR(30) | NO | None | Domain: `Active`, `Dormant`, `Closed` | Operational status of account |

---

## 3. Transactions (`transactions`)
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

## 4. Loans (`loans`)
Credit facilities and disbursed loans.

| Column | Data Type | Nullable | Primary / Foreign Key | Validation / Business Rule | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `loan_id` | INT | NO | **PK** | Unique loan identifier | Loan facility ID |
| `customer_id` | INT | NO | **FK -> customers.customer_id** | Must exist in curated customers | Borrower customer ID |
| `branch_id` | INT | NO | None | Branch lookup | Booking branch |
| `loan_type` | VARCHAR(50) | NO | None | Domain: `Auto Loan`, `Business Loan`, `Education Loan`, `Gold Loan`, `Home Loan`, `Personal Loan` | Product type |
| `loan_amount` | NUMERIC(15,2)| NO | None | Strictly positive (`> 0.00`) | Sanctioned principal amount |
| `interest_rate`| NUMERIC(5,2) | NO | None | Realistic range (`1.00% - 50.00%`)| Annual interest rate percentage |
| `term_months` | INT | NO | None | Positive integer (`> 0`) | Loan tenure in months (e.g. `60`) |
| `start_date` | DATE | NO | None | Standardized `YYYY-MM-DD` | Disbursal date |
| `status` | VARCHAR(30) | NO | None | Domain: `Active`, `Closed`, `Defaulted`, `Written Off` | Repayment and recovery status |

---

## 5. Loan Payments (`loan_payments`)
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

## 6. Cards (`cards`)
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

## 7. Card Transactions (`card_transactions`)
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

## 8. Analytical Mart: Customer 360 (`customer_360`)
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
