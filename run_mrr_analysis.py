import sqlite3
import pandas as pd

# Connect to our newly created SaaS database
conn = sqlite3.connect("saas_intelligence.db")

# Advanced SQL Analytical Query
sql_query = """
WITH monthly_revenue_per_client AS (
    -- Step 1: Calculate monthly revenue for each client
    SELECT 
        s.activity_month,
        c.customer_id,
        c.customer_name,
        s.status,
        CASE 
            WHEN s.status = 'Cancelled' THEN 0.0
            ELSE p.monthly_price_usd 
        END AS current_revenue
    FROM monthly_subscriptions s
    JOIN customers c ON s.customer_id = c.customer_id
    JOIN plans p ON s.plan_id = p.plan_id
),
revenue_lagged AS (
    -- Step 2: Use LAG() Window Function to find previous month's revenue
    SELECT 
        activity_month,
        customer_id,
        customer_name,
        status,
        current_revenue,
        LAG(current_revenue, 1) OVER (
            PARTITION BY customer_id 
            ORDER BY activity_month
        ) AS previous_revenue
    FROM monthly_revenue_per_client
),
revenue_classification AS (
    -- Step 3: Categorize every dollar movement using conditional CASE WHEN
    SELECT 
        activity_month,
        customer_id,
        customer_name,
        current_revenue,
        COALESCE(previous_revenue, 0.0) AS previous_revenue,
        CASE 
            WHEN previous_revenue IS NULL THEN current_revenue 
            ELSE 0.0 
        END AS new_mrr,
        CASE 
            WHEN current_revenue > previous_revenue AND previous_revenue IS NOT NULL 
            THEN (current_revenue - previous_revenue) 
            ELSE 0.0 
        END AS expansion_mrr,
        CASE 
            WHEN current_revenue < previous_revenue AND current_revenue > 0 
            THEN (previous_revenue - current_revenue) 
            ELSE 0.0 
        END AS contraction_mrr,
        CASE 
            WHEN status = 'Cancelled' OR (current_revenue = 0 AND previous_revenue > 0) 
            THEN previous_revenue 
            ELSE 0.0 
        END AS churned_mrr,
        CASE 
            WHEN current_revenue = previous_revenue AND status != 'Cancelled' 
            THEN current_revenue 
            ELSE 0.0 
        END AS retained_mrr
    FROM revenue_lagged
)
-- Step 4: Executive Monthly MRR Waterfall Summary
SELECT 
    activity_month,
    ROUND(SUM(new_mrr), 2) AS total_new_mrr,
    ROUND(SUM(expansion_mrr), 2) AS total_expansion_mrr,
    ROUND(SUM(contraction_mrr), 2) AS total_contraction_mrr,
    ROUND(SUM(churned_mrr), 2) AS total_churned_mrr,
    ROUND(SUM(current_revenue), 2) AS net_mrr
FROM revenue_classification
GROUP BY activity_month
ORDER BY activity_month;
"""

print("Executing SaaS Monthly Recurring Revenue (MRR) Waterfall Analysis...\n")
df_waterfall = pd.read_sql_query(sql_query, conn)
print(df_waterfall.to_string(index=False))

# --- QUERY 2: Cohort Logo Churn Summary ---
churn_query = """
SELECT 
    activity_month,
    COUNT(DISTINCT customer_id) AS total_customers_billed,
    SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS churned_logos,
    ROUND((SUM(CASE WHEN status = 'Cancelled' THEN 1.0 ELSE 0.0 END) / COUNT(DISTINCT customer_id)) * 100, 2) AS logo_churn_rate_pct
FROM monthly_subscriptions
GROUP BY activity_month
ORDER BY activity_month;
"""

print("\n\nExecuting Logo Churn Rate Analysis...\n")
df_churn = pd.read_sql_query(churn_query, conn)
print(df_churn.to_string(index=False))

conn.close()