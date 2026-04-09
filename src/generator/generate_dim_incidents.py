import pandas as pd
import numpy as np

N_INCIDENTS = 5_000

# Incident type distribution. Equipment failures are the most common
# day-to-day issue. Fiber cuts and blizzard damage are rarer but severe.
INCIDENT_TYPES = [
    "power_outage",
    "congestion",
    "equipment_failure",
    "weather_damage",
    "fiber_cut",
    "interference",
]
INCIDENT_WEIGHTS = [0.15, 0.25, 0.30, 0.15, 0.10, 0.05]

# Severity distribution. Most incidents are low or medium.
# Critical incidents are rare by definition.
SEVERITIES = ["low", "medium", "high", "critical"]
SEVERITY_WEIGHTS = [0.40, 0.35, 0.18, 0.07]

# Resolution time in minutes, sampled per severity level.
# Low: 15 to 60 minutes. Critical: up to 48 hours (2880 minutes).
RESOLUTION_RANGES = {
    "low":      (15,   60),
    "medium":   (60,   360),
    "high":     (360,  1440),
    "critical": (1440, 2880),
}

# Affected tower count ranges per incident type.
# A fiber cut or power outage can take down a cluster of towers sharing
# the same infrastructure. Equipment failure is almost always one tower.
AFFECTED_TOWERS_RANGES = {
    "power_outage":      (2, 20),
    "congestion":        (1,  5),
    "equipment_failure": (1,  2),
    "weather_damage":    (3, 30),
    "fiber_cut":         (5, 50),
    "interference":      (1,  8),
}


def sample_resolution_time(severity, rng):
    low, high = RESOLUTION_RANGES[severity]
    # Gamma distribution produces a right-skewed spread: most incidents
    # resolve near the lower bound, but a tail of stubborn cases drags out.
    scale = (high - low) / 4.0
    raw = rng.gamma(shape=2.0, scale=scale)
    return int(np.clip(low + raw, low, high))


def sample_affected_towers(incident_type, rng):
    low, high = AFFECTED_TOWERS_RANGES[incident_type]
    return int(rng.integers(low, high + 1))


def build_dim_incidents(output_path="data/generated/dim_incidents.csv",
                        n=N_INCIDENTS,
                        seed=42):

    rng = np.random.default_rng(seed=seed)

    incident_types = rng.choice(INCIDENT_TYPES, size=n, p=INCIDENT_WEIGHTS)
    severities     = rng.choice(SEVERITIES,     size=n, p=SEVERITY_WEIGHTS)

    resolution_times = [sample_resolution_time(s, rng) for s in severities]
    affected_towers  = [sample_affected_towers(t, rng) for t in incident_types]

    dim_incidents = pd.DataFrame({
        "incident_id":             [f"INC-{i:05d}" for i in range(1, n + 1)],
        "incident_type":           incident_types,
        "severity":                severities,
        "resolution_time_minutes": resolution_times,
        "affected_towers_count":   affected_towers,
    })

    dim_incidents.to_csv(output_path, index=False)
    print(f"Saved {len(dim_incidents):,} incidents to {output_path}")

    print("\nIncident type distribution:")
    print(dim_incidents["incident_type"].value_counts())
    print("\nSeverity distribution:")
    print(dim_incidents["severity"].value_counts())
    print("\nResolution time stats (minutes):")
    print(dim_incidents["resolution_time_minutes"].describe().round(1))
    print("\nAffected towers stats:")
    print(dim_incidents["affected_towers_count"].describe().round(1))

    return dim_incidents


if __name__ == "__main__":
    build_dim_incidents()
