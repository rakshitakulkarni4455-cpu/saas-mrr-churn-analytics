import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

conn = sqlite3.connect("saas_intelligence.db")

sql_query = """
WITH monthly_revenue_per_client AS (
    SELECT 
        s.activity_month,
        c.customer_id,
        s.status,
        CASE WHEN s.status = 'Cancelled' THEN 0.0 ELSE p.monthly_price_usd END AS current_revenue
    FROM monthly_subscriptions s
    JOIN customers c ON s.customer_id = c.customer_id
    JOIN plans p ON s.plan_id = p.plan_id
),
revenue_lagged AS (
    SELECT 
        activity_month,
        customer_id,
        status,
        current_revenue,
        LAG(current_revenue, 1) OVER (PARTITION BY customer_id ORDER BY activity_month) AS previous_revenue
    FROM monthly_revenue_per_client
),
revenue_classification AS (
    SELECT 
        activity_month,
        CASE WHEN previous_revenue IS NULL THEN current_revenue ELSE 0.0 END AS new_mrr,
        CASE WHEN current_revenue > previous_revenue AND previous_revenue IS NOT NULL THEN (current_revenue - previous_revenue) ELSE 0.0 END AS expansion_mrr,
        CASE WHEN current_revenue < previous_revenue AND current_revenue > 0 THEN (previous_revenue - current_revenue) ELSE 0.0 END AS contraction_mrr,
        CASE WHEN status = 'Cancelled' OR (current_revenue = 0 AND previous_revenue > 0) THEN previous_revenue ELSE 0.0 END AS churned_mrr,
        current_revenue
    FROM revenue_lagged
)
SELECT 
    activity_month,
    ROUND(SUM(new_mrr), 2) AS new_mrr,
    ROUND(SUM(expansion_mrr), 2) AS expansion_mrr,
    ROUND(SUM(contraction_mrr), 2) AS contraction_mrr,
    ROUND(SUM(churned_mrr), 2) AS churned_mrr,
    ROUND(SUM(current_revenue), 2) AS net_mrr
FROM revenue_classification
GROUP BY activity_month
ORDER BY activity_month;
"""

df = pd.read_sql_query(sql_query, conn)
conn.close()

# Plotting
fig, ax1 = plt.subplots(figsize=(10, 5))

months = df["activity_month"]
x = range(len(months))

# Bar components
ax1.bar(x, df["new_mrr"], label="New MRR ($)", color="#2b5c8f", width=0.45)
ax1.bar(x, df["expansion_mrr"], bottom=df["new_mrr"], label="Expansion MRR ($)", color="#48a9a6", width=0.45)
ax1.bar(x, -df["contraction_mrr"], label="Contraction MRR (-$)", color="#e49273", width=0.45)
ax1.bar(x, -df["churned_mrr"], bottom=-df["contraction_mrr"], label="Churned MRR (-$)", color="#d05353", width=0.45)

# Net MRR line trend
ax1.plot(x, df["net_mrr"], color="#111111", marker="o", linewidth=2.5, label="Net Ending MRR ($)")

ax1.axhline(0, color="gray", linewidth=0.8, linestyle="--")
ax1.set_xticks(x)
ax1.set_xticklabels(months, fontsize=11, fontweight="bold")
ax1.set_title("SaaS Monthly Recurring Revenue (MRR) Waterfall Dynamics", fontsize=13, fontweight="bold", pad=15)
ax1.set_ylabel("Revenue ($ USD)", fontsize=11)
ax1.legend(loc="upper left")
ax1.grid(axis="y", linestyle=":", alpha=0.7)

plt.tight_layout()
chart_file = "saas_mrr_waterfall_chart.png"
plt.savefig(chart_file, dpi=300)
print(f"SUCCESS: Saved analytical visualization to '{chart_file}'")
plt.show()