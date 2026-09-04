"""
Telemetry JSON Exporter for Web Dashboard
Author: Peter Akpan (Petre Pann) - Pann Labs
Description: Extracts aggregated SQL analytics, distributions, and account records
             from retention.db and outputs docs/data/telemetry.json for GitHub Pages.
"""

import sqlite3
import json
import os

DB_PATH = r"c:\Users\WELCOME\Desktop\Desktop\Pann Labs\SaaS_Churn_Intelligence\data\retention.db"
OUTPUT_PATH = r"c:\Users\WELCOME\Desktop\Desktop\Pann Labs\SaaS_Churn_Intelligence\docs\data\telemetry.json"

def export():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("Extracting executive telemetry from SQLite...")

    # 1. Executive Summary KPIs
    cursor.execute("""
    SELECT 
        COUNT(*) AS total_customers,
        SUM(CASE WHEN churn_status = 0 THEN 1 ELSE 0 END) AS active_accounts,
        SUM(CASE WHEN churn_status = 1 THEN 1 ELSE 0 END) AS churned_accounts,
        ROUND(AVG(churn_status) * 100.0, 2) AS churn_rate_pct,
        ROUND(SUM(CASE WHEN churn_status = 0 THEN monthly_charges ELSE 0 END), 2) AS active_mrr,
        ROUND(SUM(CASE WHEN churn_status = 1 THEN monthly_charges ELSE 0 END), 2) AS lost_mrr,
        SUM(CASE WHEN churn_status = 0 AND risk_tier = 'High Risk' THEN 1 ELSE 0 END) AS high_risk_accounts,
        ROUND(SUM(CASE WHEN churn_status = 0 AND risk_tier = 'High Risk' THEN monthly_charges ELSE 0 END), 2) AS high_risk_mrr,
        ROUND(AVG(tenure_months), 1) AS avg_tenure_months,
        ROUND(AVG(feature_adoption_rate), 1) AS avg_feature_adoption
    FROM customers;
    """)
    summary = dict(cursor.fetchone())

    # 2. Contract Breakdown
    cursor.execute("""
    SELECT 
        contract_type,
        COUNT(*) AS total_accounts,
        SUM(CASE WHEN churn_status = 1 THEN 1 ELSE 0 END) AS churned_accounts,
        ROUND(AVG(churn_status) * 100.0, 1) AS churn_rate_pct,
        ROUND(SUM(CASE WHEN churn_status = 0 THEN monthly_charges ELSE 0 END), 2) AS active_mrr,
        ROUND(SUM(CASE WHEN churn_status = 1 THEN monthly_charges ELSE 0 END), 2) AS leaked_mrr,
        ROUND(AVG(total_charges), 2) AS avg_clv
    FROM customers
    GROUP BY contract_type
    ORDER BY total_accounts DESC;
    """)
    contracts = [dict(row) for row in cursor.fetchall()]

    # 3. Subscription Tier Breakdown
    cursor.execute("""
    SELECT 
        subscription_tier,
        COUNT(*) AS total_accounts,
        ROUND(AVG(churn_status) * 100.0, 1) AS churn_rate_pct,
        ROUND(SUM(CASE WHEN churn_status = 0 THEN monthly_charges ELSE 0 END), 2) AS active_mrr,
        ROUND(SUM(CASE WHEN churn_status = 1 THEN monthly_charges ELSE 0 END), 2) AS lost_mrr,
        ROUND(AVG(CASE WHEN churn_status = 0 THEN total_charges END), 2) AS active_avg_clv
    FROM customers
    GROUP BY subscription_tier
    ORDER BY active_mrr DESC;
    """)
    tiers = [dict(row) for row in cursor.fetchall()]

    # 4. Industry Breakdown
    cursor.execute("""
    SELECT 
        industry,
        COUNT(*) AS total_accounts,
        ROUND(AVG(churn_status) * 100.0, 1) AS churn_rate_pct,
        ROUND(SUM(CASE WHEN churn_status = 0 THEN monthly_charges ELSE 0 END), 2) AS active_mrr,
        ROUND(SUM(CASE WHEN churn_status = 1 THEN monthly_charges ELSE 0 END), 2) AS leaked_mrr,
        ROUND(AVG(feature_adoption_rate), 1) AS avg_feature_adoption
    FROM customers
    GROUP BY industry
    ORDER BY leaked_mrr DESC;
    """)
    industries = [dict(row) for row in cursor.fetchall()]

    # 5. Churn Reasons
    cursor.execute("""
    SELECT 
        churn_reason,
        COUNT(*) AS frequency,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM customers WHERE churn_status = 1), 1) AS pct_of_churn
    FROM customers
    WHERE churn_status = 1
    GROUP BY churn_reason
    ORDER BY frequency DESC;
    """)
    churn_reasons = [dict(row) for row in cursor.fetchall()]

    # 6. Cohort Retention Matrix (Last 12 cohorts)
    cursor.execute("""
    WITH cohort_base AS (
        SELECT signup_cohort, COUNT(*) AS initial_size FROM customers GROUP BY signup_cohort
    )
    SELECT 
        c.signup_cohort,
        b.initial_size,
        COUNT(CASE WHEN c.churn_status = 0 THEN 1 END) AS currently_active,
        ROUND(COUNT(CASE WHEN c.churn_status = 0 THEN 1 END) * 100.0 / b.initial_size, 1) AS retention_rate_pct,
        ROUND(COUNT(CASE WHEN c.tenure_months >= 3 AND (c.churn_status = 0 OR c.tenure_months > 3) THEN 1 END) * 100.0 / b.initial_size, 1) AS m3_pct,
        ROUND(COUNT(CASE WHEN c.tenure_months >= 6 AND (c.churn_status = 0 OR c.tenure_months > 6) THEN 1 END) * 100.0 / b.initial_size, 1) AS m6_pct,
        ROUND(COUNT(CASE WHEN c.tenure_months >= 12 AND (c.churn_status = 0 OR c.tenure_months > 12) THEN 1 END) * 100.0 / b.initial_size, 1) AS m12_pct
    FROM customers c
    JOIN cohort_base b ON c.signup_cohort = b.signup_cohort
    GROUP BY c.signup_cohort, b.initial_size
    ORDER BY c.signup_cohort ASC;
    """)
    cohorts = [dict(row) for row in cursor.fetchall()]

    # 7. Customer Accounts Sample for Interactive Table (Top 300 accounts by MRR)
    cursor.execute("""
    SELECT 
        customer_id,
        company_name,
        industry,
        subscription_tier,
        contract_type,
        monthly_charges,
        tenure_months,
        active_user_seats,
        feature_adoption_rate,
        support_tickets_30d,
        days_since_last_login,
        nps_score,
        churn_risk_score,
        risk_tier,
        churn_status,
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
                THEN 'Schedule Executive Re-engagement Audit'
            WHEN support_tickets_30d >= 4 
                THEN 'Deploy Senior Solution Engineer for Rapid Triage'
            WHEN contract_type = 'Month-to-Month' AND nps_score <= 5 
                THEN 'Present Annual Contract with 15% Incentive'
            WHEN feature_adoption_rate < 40 
                THEN 'Enroll in Hands-on Workflow Clinic'
            ELSE 'Maintain Standard Success Cadence'
        END AS recommended_action
    FROM customers
    ORDER BY monthly_charges DESC
    LIMIT 300;
    """)
    customers = [dict(row) for row in cursor.fetchall()]

    # 8. Interactive Pre-Packaged SQL Queries Catalog
    sql_catalog = [
        {
            "id": "q1",
            "title": "Revenue Exposure by Contract Type",
            "description": "Calculates leaked MRR, active MRR, and churn rates across contract types.",
            "sql": "SELECT contract_type, COUNT(*) AS accounts, ROUND(AVG(churn_status)*100, 1) AS churn_rate_pct, ROUND(SUM(CASE WHEN churn_status = 1 THEN monthly_charges ELSE 0 END), 2) AS leaked_mrr, ROUND(SUM(CASE WHEN churn_status = 0 THEN monthly_charges ELSE 0 END), 2) AS active_mrr FROM customers GROUP BY contract_type ORDER BY leaked_mrr DESC;"
        },
        {
            "id": "q2",
            "title": "High-Risk Customer Triage (Top 10 Accounts by MRR)",
            "description": "Filters active accounts in High Risk band and ranks by monthly billing.",
            "sql": "SELECT customer_id, company_name, subscription_tier, contract_type, monthly_charges, churn_risk_score, days_since_last_login, support_tickets_30d FROM customers WHERE churn_status = 0 AND risk_tier = 'High Risk' ORDER BY monthly_charges DESC LIMIT 10;"
        },
        {
            "id": "q3",
            "title": "Support Ticket Friction Correlation",
            "description": "Examines churn rates grouped by support ticket volume in the past 30 days.",
            "sql": "SELECT support_tickets_30d AS tickets, COUNT(*) AS accounts, ROUND(AVG(churn_status)*100, 1) AS churn_rate_pct, ROUND(AVG(nps_score), 1) AS avg_nps FROM customers GROUP BY support_tickets_30d ORDER BY tickets ASC;"
        },
        {
            "id": "q4",
            "title": "Industry Churn & Feature Adoption Profile",
            "description": "Benchmarks feature adoption scores against churn rates across industries.",
            "sql": "SELECT industry, COUNT(*) AS accounts, ROUND(AVG(churn_status)*100, 1) AS churn_rate_pct, ROUND(AVG(feature_adoption_rate), 1) AS avg_adoption_rate, ROUND(AVG(total_charges), 2) AS avg_lifetime_revenue FROM customers GROUP BY industry ORDER BY churn_rate_pct DESC;"
        }
    ]

    # Pre-compute results for the SQL catalog
    for q in sql_catalog:
        cursor.execute(q["sql"])
        rows = [dict(r) for r in cursor.fetchall()]
        q["columns"] = list(rows[0].keys()) if rows else []
        q["results"] = rows

    payload = {
        "generated_at": "2026-09-04",
        "project": "SaaS Customer Churn & Revenue Retention Intelligence",
        "author": "Peter Akpan (Petre Pann)",
        "summary": summary,
        "contracts": contracts,
        "tiers": tiers,
        "industries": industries,
        "churn_reasons": churn_reasons,
        "cohorts": cohorts,
        "customers": customers,
        "sql_catalog": sql_catalog
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    conn.close()
    print(f"Successfully exported dashboard telemetry to: {OUTPUT_PATH}")
    print(f"Total customers exported: {len(customers)} | Cohorts: {len(cohorts)} | SQL queries: {len(sql_catalog)}")

if __name__ == "__main__":
    export()
