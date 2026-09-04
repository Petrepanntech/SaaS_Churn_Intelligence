-- ====================================================================
-- Project: SaaS Customer Churn & Revenue Retention Intelligence
-- Module: 03_revenue_leakage_clv.sql
-- Author: Peter Akpan (Petre Pann) - Pann Labs
-- Description: Financial telemetry isolating Monthly Recurring Revenue
--              leakage, Customer Lifetime Value (CLV), and contract exposure.
-- ====================================================================

-- Part 1: Revenue Exposure by Contract Type
SELECT 
    contract_type,
    COUNT(*) AS total_accounts,
    SUM(CASE WHEN churn_status = 1 THEN 1 ELSE 0 END) AS churned_accounts,
    ROUND(AVG(churn_status) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(monthly_charges), 2) AS total_committed_mrr,
    ROUND(SUM(CASE WHEN churn_status = 1 THEN monthly_charges ELSE 0 END), 2) AS leaked_mrr,
    ROUND(SUM(CASE WHEN churn_status = 0 AND risk_tier = 'High Risk' THEN monthly_charges ELSE 0 END), 2) AS endangered_mrr,
    ROUND(AVG(total_charges), 2) AS avg_historical_clv
FROM customers
GROUP BY contract_type
ORDER BY leaked_mrr DESC;

-- Part 2: Revenue Leakage by Subscription Tier
SELECT 
    subscription_tier,
    COUNT(*) AS total_accounts,
    ROUND(AVG(churn_status) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(CASE WHEN churn_status = 0 THEN monthly_charges ELSE 0 END), 2) AS active_mrr,
    ROUND(SUM(CASE WHEN churn_status = 1 THEN monthly_charges ELSE 0 END), 2) AS lost_mrr,
    ROUND(AVG(CASE WHEN churn_status = 0 THEN total_charges END), 2) AS active_avg_clv,
    ROUND(AVG(CASE WHEN churn_status = 1 THEN total_charges END), 2) AS churned_avg_clv
FROM customers
GROUP BY subscription_tier
ORDER BY lost_mrr DESC;

-- Part 3: Industry Churn & CLV Profile
SELECT 
    industry,
    COUNT(*) AS accounts,
    ROUND(AVG(churn_status) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(CASE WHEN churn_status = 1 THEN monthly_charges ELSE 0 END), 2) AS monthly_revenue_leakage,
    ROUND(AVG(total_charges), 2) AS mean_customer_clv,
    ROUND(AVG(feature_adoption_rate), 1) AS mean_feature_adoption
FROM customers
GROUP BY industry
ORDER BY monthly_revenue_leakage DESC;
