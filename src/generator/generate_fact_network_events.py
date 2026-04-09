import pandas as pd
import numpy as np

# Target row count. Adjust downward for faster local testing.
TARGET_ROWS = 1_000_000

# Fraction of events that have an associated incident.
INCIDENT_RATE = 0.05

# Baseline metric ranges by technology.
# Values are (low, high) tuples. Units match the schema definition.
METRICS_BASELINE = {
    "4G": {
        "rsrp_dbm":       (-110.0, -80.0),
        "sinr_db":        (0.0,    20.0),
        "throughput_mbps": (5.0,   150.0),
        "latency_ms":     (20.0,   60.0),
    },
    "5G": {
        "rsrp_dbm":       (-105.0, -75.0),
        "sinr_db":        (5.0,    30.0),
        "throughput_mbps": (50.0,  900.0),
        "latency_ms":     (1.0,    10.0),
    },
}

# Weather degradation multipliers applied to the baseline ranges.
# Values below 1.0 shift metrics toward the worse end of their range.
WEATHER_DEGRADATION = {
    "clear":    {"rsrp": 0.00, "throughput": 0.00, "latency": 0.00},
    "windy":    {"rsrp": 0.05, "throughput": 0.10, "latency": 0.10},
    "snow":     {"rsrp": 0.15, "throughput": 0.25, "latency": 0.20},
    "blizzard": {"rsrp": 0.30, "throughput": 0.50, "latency": 0.40},
}

# Incident severity degradation. Applied on top of weather degradation.
INCIDENT_DEGRADATION = {
    "low":      {"rsrp": 0.05, "throughput": 0.10, "latency": 0.15},
    "medium":   {"rsrp": 0.15, "throughput": 0.25, "latency": 0.25},
    "high":     {"rsrp": 0.25, "throughput": 0.50, "latency": 0.40},
    "critical": {"rsrp": 0.40, "throughput": 0.80, "latency": 0.60},
}

# Handover probability by condition. Increases during incidents and
# bad weather because devices search for a better signal.
HANDOVER_PROB = {
    "clear":    0.05,
    "windy":    0.08,
    "snow":     0.12,
    "blizzard": 0.20,
}


def degrade(low, high, factor):
    """Shift the sampling range toward the worse (low) end by factor."""
    new_high = high - (high - low) * factor
    return low, max(new_high, low)


def sample_metrics(technology, condition, severity, rng):
    base = METRICS_BASELINE[technology]
    wd   = WEATHER_DEGRADATION[condition]
    id_  = INCIDENT_DEGRADATION[severity] if severity else {"rsrp": 0, "throughput": 0, "latency": 0}

    rsrp_low,       rsrp_high       = degrade(*base["rsrp_dbm"],       wd["rsrp"]       + id_["rsrp"])
    sinr_low,       sinr_high       = base["sinr_db"]
    through_low,    through_high    = degrade(*base["throughput_mbps"], wd["throughput"] + id_["throughput"])
    latency_low,    latency_high    = degrade(*base["latency_ms"],      -(wd["latency"]  + id_["latency"]))

    # Latency degrades upward, so we invert: degrade pushes latency high.
    lat_low  = base["latency_ms"][0]
    lat_high = base["latency_ms"][1] + base["latency_ms"][1] * (wd["latency"] + id_["latency"])

    rsrp       = round(float(rng.uniform(rsrp_low,    rsrp_high)),    2)
    sinr       = round(float(rng.uniform(sinr_low,    sinr_high)),    2)
    throughput = round(float(rng.uniform(through_low, through_high)), 2)
    latency    = round(float(rng.uniform(lat_low,     lat_high)),     2)

    return rsrp, sinr, throughput, latency


def build_fact_network_events(
    towers_path    = "data/generated/dim_towers.csv",
    customers_path = "data/generated/dim_customers.csv",
    time_path      = "data/generated/dim_time.csv",
    weather_path   = "data/generated/dim_weather.csv",
    incidents_path = "data/generated/dim_incidents.csv",
    output_path    = "data/generated/fact_network_events.csv",
    target_rows    = TARGET_ROWS,
    seed           = 42,
):
    rng = np.random.default_rng(seed=seed)

    print("Loading dimension tables...")
    towers    = pd.read_csv(towers_path)
    customers = pd.read_csv(customers_path)
    dim_time  = pd.read_csv(time_path,    parse_dates=["timestamp"])
    weather   = pd.read_csv(weather_path, parse_dates=["timestamp"])
    incidents = pd.read_csv(incidents_path)

    # 
    weather.index = pd.to_datetime(weather["timestamp"]).dt.tz_localize(None)
    weather = weather.drop(columns=["timestamp"])

    # Separate towers by technology so we can route premium customers
    # preferentially to 5G towers.
    towers_5g = towers[towers["technology"] == "5G"].reset_index(drop=True)
    towers_4g = towers[towers["technology"] == "4G"].reset_index(drop=True)

    # Separate customers by tier.
    cust_premium  = customers[customers["subscription_tier"] == "premium"]
    cust_standard = customers[customers["subscription_tier"] == "standard"]
    cust_basic    = customers[customers["subscription_tier"] == "basic"]

    incident_ids = incidents["incident_id"].tolist()
    incident_map = incidents.set_index("incident_id")["severity"].to_dict()

    # How many towers report at each timestamp to hit the target row count.
    towers_per_ts = max(1, target_rows // len(dim_time))
    print(f"Timestamps:       {len(dim_time):,}")
    print(f"Towers per ts:    {towers_per_ts}")
    print(f"Expected rows:    {len(dim_time) * towers_per_ts:,}")

    rows = []

    for i, ts_row in enumerate(dim_time.itertuples(), start=1):
        ts        = ts_row.timestamp
        time_id   = ts_row.time_id

        # Match weather to this timestamp. Use nearest if exact miss.
        if ts in weather.index:
            w_row = weather.loc[ts]
        else:
            nearest = weather.index.get_indexer([ts], method="nearest")[0]
            w_row   = weather.iloc[nearest]

        weather_id = w_row["weather_id"]
        condition  = w_row["condition"]
        handover_p = HANDOVER_PROB[condition]

        # Sample towers for this timestamp.
        # If 5G towers exist, send premium customers there.
        if len(towers_5g) > 0 and towers_per_ts >= 2:
            n_5g = max(1, towers_per_ts // 3)
            n_4g = towers_per_ts - n_5g
            selected_towers = pd.concat([
                towers_5g.sample(n=min(n_5g, len(towers_5g)), random_state=i),
                towers_4g.sample(n=min(n_4g, len(towers_4g)), random_state=i),
            ]).reset_index(drop=True)
        else:
            selected_towers = towers.sample(
                n=min(towers_per_ts, len(towers)), random_state=i
            ).reset_index(drop=True)

        for t_row in selected_towers.itertuples():
            technology = t_row.technology

            # Assign a customer. Premium on 5G, basic skews to 4G.
            if technology == "5G" and len(cust_premium) > 0:
                customer = cust_premium.sample(1, random_state=i).iloc[0]
            elif technology == "4G" and len(cust_basic) > 0 and rng.random() < 0.4:
                customer = cust_basic.sample(1, random_state=i).iloc[0]
            else:
                customer = cust_standard.sample(1, random_state=i).iloc[0]

            # Assign incident with probability INCIDENT_RATE.
            incident_id = None
            severity    = None
            if rng.random() < INCIDENT_RATE:
                incident_id = str(rng.choice(incident_ids))
                severity    = incident_map[incident_id]

            rsrp, sinr, throughput, latency = sample_metrics(
                technology, condition, severity, rng
            )

            handover = bool(rng.random() < handover_p)

            rows.append({
                "event_id":        f"EVT-{len(rows) + 1:07d}",
                "tower_id":        t_row.tower_id,
                "customer_id":     customer["customer_id"],
                "time_id":         time_id,
                "weather_id":      weather_id,
                "incident_id":     incident_id,
                "rsrp_dbm":        rsrp,
                "sinr_db":         sinr,
                "throughput_mbps": throughput,
                "latency_ms":      latency,
                "handover_flag":   handover,
            })

        if i % 10_000 == 0:
            print(f"  Processed {i:,} / {len(dim_time):,} timestamps "
                  f"({len(rows):,} rows so far)...")

    print(f"\nBuilding DataFrame from {len(rows):,} rows...")
    fact = pd.DataFrame(rows)
    fact.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")

    print("\nSample rows:")
    print(fact.head(3).to_string(index=False))
    print("\nIncident rate (actual):")
    print(round(fact["incident_id"].notna().mean(), 4))
    print("\nHandover rate (actual):")
    print(round(fact["handover_flag"].mean(), 4))
    print("\nRSRP stats:")
    print(fact["rsrp_dbm"].describe().round(2))

    return fact


if __name__ == "__main__":
    build_fact_network_events()
