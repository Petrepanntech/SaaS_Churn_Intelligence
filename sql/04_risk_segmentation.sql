-- ====================================================================
-- Project: SaaS Customer Churn & Revenue Retention Intelligence
-- Module: 04_risk_segmentation.sql
-- Author: Peter Akpan (Petre Pann) - Pann Labs
-- Description: Multi-factor risk segmentation and operational triage
--              allocating prescriptive retention interventions by MRR.
-- ====================================================================

WITH active_risk_profile AS (
    SELECT 
        customer_id,
        company_name,
        industry,
        subscription_tier,
        contract_type,
        monthly_charges,
        tenure_months,
        feature_adoption_rate,
        support_tickets_30d,
        days_since_last_login,
        nps_score,
        churn_risk_score,
        risk_tier,
        CASE
            WHEN days_since_last_login >= 14 AND feature_adoption_rate < 40 
                THEN 'Dormant Account / Low Adoption'
            WHEN support_tickets_30d >= 4 
                THEN 'Product Friction / Ticket Escalation'
            WHEN contract_type = 'Month-to-Month' AND nps_score <= 5 
                THEN 'Immediate Renewal Risk / Low NPS'
            WHEN churn_risk_score >= 65.0 
                THEN 'Compounded Risk Indicators'
            ELSE 'Healthy Engagement'
        END AS primary_churn_trigger,
        CASE
            WHEN days_since_last_login >= 14 
                THEN 'Schedule Executive Re-engagement & Audit'
            WHEN support_tickets_30d >= 4 
                THEN 'Deploy Senior Solution Engineer for Rapid Triage'
            WHEN contract_type = 'Month-to-Month' AND nps_score <= 5 
                THEN 'Present Annual Contract with 15% Incentive'
            WHEN feature_adoption_rate < 40 
                THEN 'Enroll in Hands-on Workflow Optimization Clinic'
            ELSE 'Maintain Standard Success Cadence'
        END AS recommended_retention_action
    FROM customers
    WHERE churn_status = 0
)
SELECT 
    DENSE_RANK() OVER (ORDER BY monthly_charges DESC) AS revenue_priority_rank,
    customer_id,
    company_name,
    subscription_tier,
    contract_type,
    monthly_charges AS mrr,
    tenure_months,
    churn_risk_score,
    risk_tier,
    primary_churn_trigger,
    recommended_retention_action
FROM active_risk_profile
WHERE risk_tier = 'High Risk'
ORDER BY monthly_charges DESC
LIMIT 50;
