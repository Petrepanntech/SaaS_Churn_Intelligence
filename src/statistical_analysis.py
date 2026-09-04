"""
Statistical Inference & Churn Diagnostics Engine
Author: Peter Akpan (Petre Pann) - Pann Labs
Description: Calculates statistical distributions, churn odds ratios,
             cross-tabulations, and correlation metrics.
"""

import sqlite3
import math

DB_PATH = r"c:\Users\WELCOME\Desktop\Desktop\Pann Labs\SaaS_Churn_Intelligence\data\retention.db"

def calculate_odds_ratio(a, b, c, d):
    # a: Exposed Churned, b: Exposed Retained
    # c: Unexposed Churned, d: Unexposed Retained
    if b == 0 or c == 0 or d == 0:
        return 0.0
    return round((a * d) / (b * c), 2)

def run_diagnostics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("================================================================")
    print("      SAAS CHURN STATISTICAL DIAGNOSTICS & INFERENCE REPORT      ")
    print("================================================================")

    # 1. Baseline Metrics
    cursor.execute("""
    SELECT 
        COUNT(*) AS total_n,
        SUM(churn_status) AS churned_n,
        ROUND(AVG(churn_status) * 100, 2) AS churn_rate_pct,
        ROUND(SUM(CASE WHEN churn_status = 0 THEN monthly_charges ELSE 0 END), 2) AS active_mrr,
        ROUND(SUM(CASE WHEN churn_status = 1 THEN monthly_charges ELSE 0 END), 2) AS lost_mrr
    FROM customers;
    """)
    total_n, churned_n, churn_rate, active_mrr, lost_mrr = cursor.fetchone()
    print(f"\n[1] Overall Population Baseline:")
    print(f"    Total Accounts Analyzed : {total_n:,}")
    print(f"    Total Churned Accounts  : {churned_n:,} ({churn_rate}%)")
    print(f"    Active Portfolio MRR    : ${active_mrr:,.2f}")
    print(f"    Lost Annualized Run-Rate: ${lost_mrr * 12:,.2f}")

    # 2. Contract Type Odds Ratio
    cursor.execute("""
    SELECT 
        contract_type,
        SUM(churn_status) AS churned,
        SUM(CASE WHEN churn_status = 0 THEN 1 ELSE 0 END) AS active
    FROM customers
    GROUP BY contract_type;
    """)
    contract_stats = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
    m2m_churned, m2m_active = contract_stats["Month-to-Month"]
    y2_churned, y2_active = contract_stats["2-Year"]
    contract_or = calculate_odds_ratio(m2m_churned, m2m_active, y2_churned, y2_active)

    print(f"\n[2] Contract Type Risk Analysis:")
    for c_type, (ch, act) in contract_stats.items():
        rate = (ch / (ch + act)) * 100
        print(f"    {c_type:<15}: Churn Rate = {rate:.1f}% ({ch:,} / {ch + act:,})")
    print(f"    --> Month-to-Month Churn Odds Ratio vs 2-Year Contract: {contract_or}x")

    # 3. Support Ticket Thresholding (Friction Impact)
    cursor.execute("""
    SELECT 
        CASE WHEN support_tickets_30d >= 4 THEN '>= 4 Tickets' ELSE '< 4 Tickets' END AS ticket_band,
        SUM(churn_status) AS churned,
        SUM(CASE WHEN churn_status = 0 THEN 1 ELSE 0 END) AS active
    FROM customers
    GROUP BY ticket_band;
    """)
    ticket_stats = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
    high_tix_ch, high_tix_act = ticket_stats[">= 4 Tickets"]
    low_tix_ch, low_tix_act = ticket_stats["< 4 Tickets"]
    ticket_or = calculate_odds_ratio(high_tix_ch, high_tix_act, low_tix_ch, low_tix_act)

    print(f"\n[3] Support Friction Analysis (30-Day Ticket Velocity):")
    high_tix_rate = (high_tix_ch / (high_tix_ch + high_tix_act)) * 100
    low_tix_rate = (low_tix_ch / (low_tix_ch + low_tix_act)) * 100
    print(f"    Accounts with >= 4 Support Tickets : Churn Rate = {high_tix_rate:.1f}%")
    print(f"    Accounts with < 4 Support Tickets  : Churn Rate = {low_tix_rate:.1f}%")
    print(f"    --> Support Friction Churn Odds Ratio: {ticket_or}x")

    # 4. Inactivity & Login Staleness Impact
    cursor.execute("""
    SELECT 
        CASE WHEN days_since_last_login >= 14 THEN 'Dormant (>= 14d)' ELSE 'Active (< 14d)' END AS activity_band,
        SUM(churn_status) AS churned,
        SUM(CASE WHEN churn_status = 0 THEN 1 ELSE 0 END) AS active
    FROM customers
    GROUP BY activity_band;
    """)
    inact_stats = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
    dorm_ch, dorm_act = inact_stats["Dormant (>= 14d)"]
    act_ch, act_act = inact_stats["Active (< 14d)"]
    inact_or = calculate_odds_ratio(dorm_ch, dorm_act, act_ch, act_act)

    print(f"\n[4] User Staleness Analysis (Days Since Last Login):")
    dorm_rate = (dorm_ch / (dorm_ch + dorm_act)) * 100
    act_rate = (act_ch / (act_ch + act_act)) * 100
    print(f"    Dormant Accounts (>= 14 days idle): Churn Rate = {dorm_rate:.1f}%")
    print(f"    Active Accounts (< 14 days idle)  : Churn Rate = {act_rate:.1f}%")
    print(f"    --> Inactivity Churn Odds Ratio: {inact_or}x")

    # 5. Top Churn Drivers Cited
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
    print(f"\n[5] Primary Exit Reasons Cited:")
    for reason, freq, pct in cursor.fetchall():
        print(f"    - {reason:<32}: {freq:,} accounts ({pct}%)")

    conn.close()
    print("\n================================================================")
    print("                     DIAGNOSTICS COMPLETE                       ")
    print("================================================================")

if __name__ == "__main__":
    run_diagnostics()
