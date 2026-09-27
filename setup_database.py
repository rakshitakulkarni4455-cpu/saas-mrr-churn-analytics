import sqlite3

# Connect to or create local SQLite database
db_name = "saas_intelligence.db"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

print("Setting up SaaS relational schema...")

# 1. Plans Dimension Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS plans (
    plan_id INTEGER PRIMARY KEY,
    plan_name TEXT NOT NULL,
    monthly_price_usd REAL NOT NULL
);
""")

# 2. Customers Dimension Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    country TEXT NOT NULL
);
""")

# 3. Monthly Subscription Activity / Billing Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS monthly_subscriptions (
    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    activity_month TEXT NOT NULL, -- Format: YYYY-MM
    status TEXT NOT NULL,          -- Active, Cancelled
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
);
""")

# Insert Subscription Plans
cursor.execute("DELETE FROM plans;")
cursor.executemany("""
INSERT INTO plans (plan_id, plan_name, monthly_price_usd) VALUES (?, ?, ?);
""", [
    (1, "Basic Tier", 29.00),
    (2, "Professional Tier", 79.00),
    (3, "Enterprise Tier", 199.00)
])

# Insert Customer Records
cursor.execute("DELETE FROM customers;")
customers_data = [
    (101, "Acme Corp", "2024-01-10", "USA"),
    (102, "BlueSky Media", "2024-01-15", "India"),
    (103, "Crestline Logistics", "2024-01-22", "UK"),
    (104, "Delta Tech", "2024-02-05", "USA"),
    (105, "Echo Digital", "2024-02-18", "Germany"),
    (106, "Falcon Systems", "2024-03-01", "India"),
    (107, "Global Ventures", "2024-03-12", "Canada")
]
cursor.executemany("""
INSERT INTO customers (customer_id, customer_name, signup_date, country) VALUES (?, ?, ?, ?);
""", customers_data)

# Insert Multi-Month Subscription Activity (Showing Upgrades, Downgrades, & Churn)
cursor.execute("DELETE FROM monthly_subscriptions;")
subscription_events = [
    # January 2024 (Cohort 1 starts)
    (101, 1, "2024-01", "Active"),  # Acme starts on Basic ($29)
    (102, 2, "2024-01", "Active"),  # BlueSky starts on Pro ($79)
    (103, 3, "2024-01", "Active"),  # Crestline starts on Enterprise ($199)

    # February 2024
    (101, 2, "2024-02", "Active"),  # Acme UPGRADED: Basic -> Pro ($79) -> Expansion MRR
    (102, 2, "2024-02", "Active"),  # BlueSky retained ($79)
    (103, 1, "2024-02", "Active"),  # Crestline DOWNGRADED: Enterprise -> Basic ($29) -> Contraction MRR
    (104, 1, "2024-02", "Active"),  # Delta Tech new ($29)
    (105, 2, "2024-02", "Active"),  # Echo Digital new ($79)

    # March 2024
    (101, 2, "2024-03", "Active"),  # Acme retained ($79)
    (102, 2, "2024-03", "Cancelled"), # BlueSky CANCELLED ($0) -> Churned MRR
    (103, 1, "2024-03", "Active"),  # Crestline retained ($29)
    (104, 3, "2024-03", "Active"),  # Delta Tech UPGRADED: Basic -> Enterprise ($199)
    (105, 2, "2024-03", "Active"),  # Echo retained ($79)
    (106, 1, "2024-03", "Active"),  # Falcon Systems new ($29)
    (107, 2, "2024-03", "Active")   # Global Ventures new ($79)
]

cursor.executemany("""
INSERT INTO monthly_subscriptions (customer_id, plan_id, activity_month, status)
VALUES (?, ?, ?, ?);
""", subscription_events)

conn.commit()
conn.close()

print(f"SUCCESS: Database '{db_name}' initialized with schema, plans, and historical events!")