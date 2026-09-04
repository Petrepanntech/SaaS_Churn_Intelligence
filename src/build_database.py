"""
SQLite Database ETL & Table Builder
Author: Peter Akpan (Petre Pann) - Pann Labs
Description: Ingests raw CSV records, defines relational schema with strict types,
             creates performance indexes, and compiles analytical views.
"""

import sqlite3
import csv
import os

DB_PATH = r"c:\Users\WELCOME\Desktop\Desktop\Pann Labs\SaaS_Churn_Intelligence\data\retention.db"
CSV_PATH = r"c:\Users\WELCOME\Desktop\Desktop\Pann Labs\SaaS_Churn_Intelligence\data\customer_churn_records.csv"

def build():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Raw CSV not found at {CSV_PATH}. Run generate_dataset.py first.")

    # Remove existing db if present to ensure clean rebuild
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Building schema in retention.db...")
    cursor.execute("""
    CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY,
        company_name TEXT NOT NULL,
        industry TEXT NOT NULL,
        subscription_tier TEXT NOT NULL,
        contract_type TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        signup_cohort TEXT NOT NULL,
        tenure_months INTEGER NOT NULL,
        monthly_charges REAL NOT NULL,
        total_charges REAL NOT NULL,
        active_user_seats INTEGER NOT NULL,
        feature_adoption_rate INTEGER NOT NULL,
        support_tickets_30d INTEGER NOT NULL,
        days_since_last_login INTEGER NOT NULL,
        nps_score INTEGER NOT NULL,
        churn_risk_score REAL NOT NULL,
        risk_tier TEXT NOT NULL,
        churn_status INTEGER NOT NULL,
        churn_reason TEXT NOT NULL
    );
    """)

    # Performance and query indexes
    cursor.execute("CREATE INDEX idx_customers_cohort ON customers(signup_cohort);")
    cursor.execute("CREATE INDEX idx_customers_contract ON customers(contract_type);")
    cursor.execute("CREATE INDEX idx_customers_risk ON customers(risk_tier);")
    cursor.execute("CREATE INDEX idx_customers_status ON customers(churn_status);")
    cursor.execute("CREATE INDEX idx_customers_tier ON customers(subscription_tier);")

    # Ingest CSV rows
    print("Ingesting CSV records...")
    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = [
            (
                r["customer_id"],
                r["company_name"],
                r["industry"],
                r["subscription_tier"],
                r["contract_type"],
                r["payment_method"],
                r["signup_cohort"],
                int(r["tenure_months"]),
                float(r["monthly_charges"]),
                float(r["total_charges"]),
                int(r["active_user_seats"]),
                int(r["feature_adoption_rate"]),
                int(r["support_tickets_30d"]),
                int(r["days_since_last_login"]),
                int(r["nps_score"]),
                float(r["churn_risk_score"]),
                r["risk_tier"],
                int(r["churn_status"]),
                r["churn_reason"]
            )
            for r in reader
        ]

    cursor.executemany("""
    INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, records)

    # Create analytical view: Executive KPI Summary
    cursor.execute("""
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
    """)

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM customers;")
    count = cursor.fetchone()[0]
    cursor.execute("SELECT * FROM v_executive_retention_kpi;")
    kpis = cursor.fetchone()

    conn.close()

    print(f"Successfully loaded {count} records into SQLite.")
    print(f"Active MRR: ${kpis[4]:,.2f} | Lost MRR: ${kpis[5]:,.2f} | High-Risk MRR: ${kpis[6]:,.2f}")

if __name__ == "__main__":
    build()
