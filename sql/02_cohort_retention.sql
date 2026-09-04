-- ====================================================================
-- Project: SaaS Customer Churn & Revenue Retention Intelligence
-- Module: 02_cohort_retention.sql
-- Author: Peter Akpan (Petre Pann) - Pann Labs
-- Description: Longitudinal cohort retention matrix analyzing customer
--              survival rates across signup cohorts and tenure stages.
-- ====================================================================

WITH cohort_base AS (
    SELECT 
        signup_cohort,
        COUNT(*) AS initial_cohort_size,
        SUM(monthly_charges) AS cohort_initial_mrr
    FROM customers
    GROUP BY signup_cohort
),
cohort_survival AS (
    SELECT 
        c.signup_cohort,
        b.initial_cohort_size,
        b.cohort_initial_mrr,
        COUNT(CASE WHEN c.churn_status = 0 THEN 1 END) AS currently_active_accounts,
        ROUND(COUNT(CASE WHEN c.churn_status = 0 THEN 1 END) * 100.0 / b.initial_cohort_size, 2) AS current_retention_rate_pct,
        COUNT(CASE WHEN c.tenure_months >= 3 AND (c.churn_status = 0 OR c.tenure_months > 3) THEN 1 END) AS retained_at_m3,
        COUNT(CASE WHEN c.tenure_months >= 6 AND (c.churn_status = 0 OR c.tenure_months > 6) THEN 1 END) AS retained_at_m6,
        COUNT(CASE WHEN c.tenure_months >= 12 AND (c.churn_status = 0 OR c.tenure_months > 12) THEN 1 END) AS retained_at_m12,
        ROUND(SUM(CASE WHEN c.churn_status = 0 THEN c.monthly_charges ELSE 0 END), 2) AS current_retained_mrr,
        ROUND(AVG(c.tenure_months), 1) AS avg_cohort_tenure
    FROM customers c
    JOIN cohort_base b ON c.signup_cohort = b.signup_cohort
    GROUP BY c.signup_cohort, b.initial_cohort_size, b.cohort_initial_mrr
)
SELECT 
    signup_cohort,
    initial_cohort_size,
    currently_active_accounts,
    current_retention_rate_pct,
    ROUND(retained_at_m3 * 100.0 / initial_cohort_size, 1) AS retention_m3_pct,
    ROUND(retained_at_m6 * 100.0 / initial_cohort_size, 1) AS retention_m6_pct,
    ROUND(retained_at_m12 * 100.0 / initial_cohort_size, 1) AS retention_m12_pct,
    cohort_initial_mrr,
    current_retained_mrr,
    ROUND((current_retained_mrr - cohort_initial_mrr) * 100.0 / cohort_initial_mrr, 2) AS net_mrr_growth_pct
FROM cohort_survival
ORDER BY signup_cohort DESC;
