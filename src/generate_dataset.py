"""
SaaS Customer Churn & Revenue Retention Dataset Generator
Author: Peter Akpan (Petre Pann) - Pann Labs
Description: Synthesizes a realistic, high-fidelity enterprise B2B dataset
             demonstrating behavioral, financial, and engagement metrics.
"""

import csv
import random
import math
from datetime import datetime, timedelta

# Set seed for exact reproducibility
random.seed(42)

NUM_CUSTOMERS = 5000

INDUSTRIES = ["Technology", "Healthcare", "Financial Services", "E-Commerce", "Manufacturing", "Education"]
TIERS = [
    {"name": "Starter", "base_mrr": 99, "weight": 40, "seat_range": (1, 10)},
    {"name": "Professional", "base_mrr": 299, "weight": 40, "seat_range": (5, 35)},
    {"name": "Enterprise", "base_mrr": 899, "weight": 20, "seat_range": (20, 150)}
]
CONTRACT_TYPES = ["Month-to-Month", "1-Year", "2-Year"]
PAYMENT_METHODS = ["Bank Transfer", "Credit Card", "Electronic Check"]

COMPANY_PREFIXES = [
    "Apex", "Vanguard", "Nexus", "Quantum", "Hyperion", "Aura", "Catalyst", "Pulse",
    "Vertex", "Starlight", "Beacon", "Cobalt", "Crest", "Elevation", "Frontier",
    "Horizon", "Integra", "Kinetic", "Luminary", "Meridian", "Nova", "Omni", "Pinnacle",
    "Acro", "Boreal", "Cortex", "Equinox", "Flux", "Galactic", "Helix", "Infini",
    "Krypton", "Matrix", "Neutron", "Optima", "Prism", "Radiant", "Solaris", "Titan",
    "Zenith", "Strata", "Synapse", "Vortex", "Vector", "Zenith", "Aegis", "Orion"
]
COMPANY_MIDDLES = [
    "Data", "Cloud", "Digital", "Bio", "Cyber", "Logic", "Meta", "Omni", "Global",
    "Enterprise", "Strategic", "Capital", "Insight", "Dynamic", "Applied", "Core",
    "Prime", "Direct", "NextGen", "Adaptive", "Secure", "Venture", "Smart"
]
COMPANY_SUFFIXES = [
    "Systems", "Technologies", "Analytics", "Solutions", "Health", "Logistics",
    "Enterprises", "Global", "Networks", "Labs", "Partners", "Dynamics", "Cloud",
    "Group", "Consulting", "Ventures", "Holdings", "Corp", "Industries", "Media"
]

CHURN_REASONS = [
    "Missing Core Feature",
    "Competitor Migration",
    "Budget Reallocation / Price",
    "Poor Onboarding Experience",
    "Low User Adoption",
    "Executive Leadership Turnover"
]

def generate_company_name(i):
    p = COMPANY_PREFIXES[i % len(COMPANY_PREFIXES)]
    m = COMPANY_MIDDLES[(i // len(COMPANY_PREFIXES)) % len(COMPANY_MIDDLES)]
    s = COMPANY_SUFFIXES[(i // (len(COMPANY_PREFIXES) * len(COMPANY_MIDDLES))) % len(COMPANY_SUFFIXES)]
    variant = (i // (len(COMPANY_PREFIXES) * len(COMPANY_MIDDLES) * len(COMPANY_SUFFIXES)))
    if variant > 0:
        return f"{p} {m} {s} {variant + 1}"
    return f"{p} {m} {s}"

def run():
    print(f"Generating {NUM_CUSTOMERS} realistic B2B customer records...")
    existing_names = set()
    rows = []

    # Cohort months from 2024-01 to 2026-06 (30 months)
    start_date = datetime(2024, 1, 1)
    cohort_dates = []
    curr = start_date
    while curr <= datetime(2026, 6, 1):
        cohort_dates.append(curr.strftime("%Y-%m"))
        # advance 1 month
        month = curr.month + 1
        year = curr.year
        if month > 12:
            month = 1
            year += 1
        curr = datetime(year, month, 1)

    for i in range(1, NUM_CUSTOMERS + 1):
        cust_id = f"CUST-{10000 + i}"
        company_name = generate_company_name(i)
        industry = random.choice(INDUSTRIES)
        
        # Tier selection
        tier_choice = random.choices(TIERS, weights=[t["weight"] for t in TIERS])[0]
        tier_name = tier_choice["name"]
        seats = random.randint(*tier_choice["seat_range"])
        
        # Monthly charge with variance
        seat_addon = (seats - tier_choice["seat_range"][0]) * 8.5
        monthly_charges = round(tier_choice["base_mrr"] + seat_addon + random.uniform(-10, 25), 2)
        
        # Contract type weighting
        contract_type = random.choices(CONTRACT_TYPES, weights=[55, 30, 15])[0]
        payment_method = random.choices(PAYMENT_METHODS, weights=[35, 45, 20])[0]
        
        # Signup cohort
        signup_cohort = random.choice(cohort_dates)
        cohort_dt = datetime.strptime(signup_cohort, "%Y-%m")
        max_tenure = max(1, int((datetime(2026, 8, 1) - cohort_dt).days / 30.4))
        tenure_months = random.randint(1, min(max_tenure, 36))
        
        # Behavioral factors
        feature_adoption = random.randint(15, 98)
        support_tickets_30d = random.choices([0, 1, 2, 3, 4, 5, 6], weights=[35, 30, 15, 10, 5, 3, 2])[0]
        days_since_login = random.choices(
            [0, 1, 2, 3, 5, 8, 14, 21, 30, 45],
            weights=[30, 25, 15, 10, 8, 5, 3, 2, 1, 1]
        )[0]
        nps_score = random.choices(list(range(1, 11)), weights=[3, 4, 5, 6, 8, 10, 18, 22, 16, 8])[0]
        
        # Calculate realistic churn probability using logistic function
        logit = -1.8  # baseline
        
        # Contract impact
        if contract_type == "Month-to-Month":
            logit += 0.95
        elif contract_type == "2-Year":
            logit -= 1.10
            
        # Support ticket friction
        if support_tickets_30d >= 4:
            logit += 1.45
        elif support_tickets_30d == 0:
            logit += 0.20  # lack of engagement can also signal churn
            
        # Inactivity impact
        if days_since_login > 15:
            logit += 1.60
        elif days_since_login <= 2:
            logit -= 0.65
            
        # Feature adoption impact
        if feature_adoption < 35:
            logit += 1.15
        elif feature_adoption > 75:
            logit -= 0.85
            
        # NPS impact
        if nps_score <= 5:
            logit += 0.90
        elif nps_score >= 9:
            logit -= 0.95
            
        # Tenure curve (early tenure has higher churn)
        if tenure_months <= 3:
            logit += 0.60
        elif tenure_months > 18:
            logit -= 0.75
            
        prob = 1.0 / (1.0 + math.exp(-logit))
        churn_risk_score = round(prob * 100, 1)
        
        is_churned = 1 if random.random() < prob else 0
        churn_reason = random.choice(CHURN_REASONS) if is_churned else "N/A"
        
        total_charges = round(monthly_charges * tenure_months * random.uniform(0.96, 1.04), 2)
        
        # Risk Tier categorization
        if churn_risk_score >= 65.0:
            risk_tier = "High Risk"
        elif churn_risk_score >= 35.0:
            risk_tier = "Medium Risk"
        else:
            risk_tier = "Low Risk"
            
        rows.append({
            "customer_id": cust_id,
            "company_name": company_name,
            "industry": industry,
            "subscription_tier": tier_name,
            "contract_type": contract_type,
            "payment_method": payment_method,
            "signup_cohort": signup_cohort,
            "tenure_months": tenure_months,
            "monthly_charges": monthly_charges,
            "total_charges": total_charges,
            "active_user_seats": seats,
            "feature_adoption_rate": feature_adoption,
            "support_tickets_30d": support_tickets_30d,
            "days_since_last_login": days_since_login,
            "nps_score": nps_score,
            "churn_risk_score": churn_risk_score,
            "risk_tier": risk_tier,
            "churn_status": is_churned,
            "churn_reason": churn_reason
        })

    output_path = r"c:\Users\WELCOME\Desktop\Desktop\Pann Labs\SaaS_Churn_Intelligence\data\customer_churn_records.csv"
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    churn_count = sum(1 for r in rows if r["churn_status"] == 1)
    churn_rate = (churn_count / NUM_CUSTOMERS) * 100
    mrr_at_risk = sum(r["monthly_charges"] for r in rows if r["risk_tier"] == "High Risk" and r["churn_status"] == 0)
    
    print(f"Generated {NUM_CUSTOMERS} records successfully.")
    print(f"Overall Churn Rate: {churn_rate:.1f}% ({churn_count} churned accounts)")
    print(f"Active MRR in High Risk Band: ${mrr_at_risk:,.2f}")
    print(f"Saved dataset to: {output_path}")

if __name__ == "__main__":
    run()
