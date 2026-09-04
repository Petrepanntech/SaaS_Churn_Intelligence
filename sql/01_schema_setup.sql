-- ====================================================================
-- Project: SaaS Customer Churn & Revenue Retention Intelligence
-- Module: 01_schema_setup.sql
-- Author: Peter Akpan (Petre Pann) - Pann Labs
-- Description: Core schema creation, indexing, and base analytical views
-- ====================================================================

DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    industry TEXT NOT NULL,
    subscription_tier TEXT NOT NULL,      -- Starter, Professional, Enterprise
    contract_type TEXT NOT NULL,          -- Month-to-Month, 1-Year, 2-Year
    payment_method TEXT NOT NULL,         -- Bank Transfer, Credit Card, Electronic Check
    signup_cohort TEXT NOT NULL,          -- YYYY-MM
    tenure_months INTEGER NOT NULL,       -- Months active with service
    monthly_charges REAL NOT NULL,        -- Current Monthly Recurring Revenue (MRR)
    total_charges REAL NOT NULL,          -- Cumulative billings to date
    active_user_seats INTEGER NOT NULL,   -- Provisioned seats
    feature_adoption_rate INTEGER NOT NULL, -- 0 to 100 benchmark score
    support_tickets_30d INTEGER NOT NULL, -- Recent ticket volume
    days_since_last_login INTEGER NOT NULL, -- Inactivity metric
    nps_score INTEGER NOT NULL,           -- Net Promoter Score rating (1-10)
    churn_risk_score REAL NOT NULL,       -- Modeled churn probability percentage
    risk_tier TEXT NOT NULL,              -- High Risk, Medium Risk, Low Risk
    churn_status INTEGER NOT NULL,        -- 0 = Active, 1 = Churned
    churn_reason TEXT NOT NULL            -- Primary exit driver if churned
);

-- Performance Indexes for Analytics Workloads
CREATE INDEX idx_customers_cohort ON customers(signup_cohort);
CREATE INDEX idx_customers_contract ON customers(contract_type);
CREATE INDEX idx_customers_risk ON customers(risk_tier);
CREATE INDEX idx_customers_status ON customers(churn_status);
CREATE INDEX idx_customers_tier ON customers(subscription_tier);

-- Analytical View: Executive Revenue Telemetry
DROP VIEW IF EXISTS v_executive_retention_kpi;

CREATE VIEW v_executive_retention_kpi AS
SELECT 
    COUNT(*) AS total_customers,
    SUM(CASE WHEN churn_status = 0 THEN 1 ELSE 0 END) AS active_accounts,
    SUM(CASE WHEN churn_status = 1 THEN 1 ELSE 0 END) AS churned_accounts,
    ROUND(AVG(churn_status) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(CASE WHEN churn_status = 0 THEN monthly_charges ELSE 0 END), 2) AS active_mrr,
    ROUND(SUM(CASE WHEN churn_status = 1 THEN monthly_charges ELSE 0 END), 2) AS lost_mrr,
    ROUND(SUM(CASE WHEN churn_status = 0 AND risk_tier = 'High Risk' THEN monthly_charges ELSE 0 END), 2) AS high_risk_mrr,
    ROUND(AVG(tenure_months), 1) AS avg_tenure_months,
    ROUND(AVG(feature_adoption_rate), 1) AS avg_feature_adoption
FROM customers;
