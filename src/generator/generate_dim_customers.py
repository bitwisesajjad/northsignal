import pandas as pd
import numpy as np

# Number of customers to generate.
N_CUSTOMERS = 50_000

# Contract type distribution derived from IBM Watson Telco Churn dataset.
# Month-to-month dominates in real telecom data.
CONTRACT_TYPES = ["month_to_month", "one_year", "two_year"]
CONTRACT_WEIGHTS = [0.55, 0.25, 0.20]

# Device type distribution. Smartphones make up the vast majority.
# IoT devices are a small but growing segment in Finnish networks.
DEVICE_TYPES = ["smartphone", "tablet", "mobile_router", "iot_device"]
DEVICE_WEIGHTS = [0.70, 0.12, 0.10, 0.08]

# Subscription tier distribution. Most customers are on standard plans.
SUBSCRIPTION_TIERS = ["basic", "standard", "premium"]
TIER_WEIGHTS = [0.30, 0.50, 0.20]

# Churn risk score ranges per contract type.
# Derived from IBM dataset churn rates: month-to-month churns at roughly
# 3x the rate of two-year contract customers.
CHURN_RISK_RANGES = {
    "month_to_month": (0.40, 1.00),
    "one_year":       (0.15, 0.55),
    "two_year":       (0.00, 0.30),
}


def generate_churn_risk(contract_type, rng):
    low, high = CHURN_RISK_RANGES[contract_type]
    # Beta distribution keeps scores away from hard edges and produces
    # a realistic spread rather than a flat uniform distribution.
    raw = rng.beta(a=2, b=3)
    return round(float(low + raw * (high - low)), 4)


def build_dim_customers(output_path="data/generated/dim_customers.csv",
                        n=N_CUSTOMERS,
                        seed=42):

    rng = np.random.default_rng(seed=seed)

    contract_types = rng.choice(CONTRACT_TYPES, size=n, p=CONTRACT_WEIGHTS)
    device_types   = rng.choice(DEVICE_TYPES,   size=n, p=DEVICE_WEIGHTS)
    tiers          = rng.choice(SUBSCRIPTION_TIERS, size=n, p=TIER_WEIGHTS)

    churn_scores = [
        generate_churn_risk(c, rng) for c in contract_types
    ]

    dim_customers = pd.DataFrame({
        "customer_id":       [f"CUST-{i:05d}" for i in range(1, n + 1)],
        "contract_type":     contract_types,
        "device_type":       device_types,
        "subscription_tier": tiers,
        "churn_risk_score":  churn_scores,
    })

    dim_customers.to_csv(output_path, index=False)
    print(f"Saved {len(dim_customers)} customers to {output_path}")
    print("\nDistribution check:")
    print(dim_customers["contract_type"].value_counts(normalize=True).round(3))
    print(dim_customers["subscription_tier"].value_counts(normalize=True).round(3))
    print(dim_customers["device_type"].value_counts(normalize=True).round(3))
    print(f"\nChurn risk score stats:\n{dim_customers['churn_risk_score'].describe().round(3)}")

    return dim_customers


if __name__ == "__main__":
    build_dim_customers()
