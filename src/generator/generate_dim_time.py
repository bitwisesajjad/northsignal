import pandas as pd

# Time range matches the FMI weather data: 2022-01-01 to 2025-12-31.
# Interval matches FMI observation frequency: every 10 minutes.
START = "2022-01-01 00:00:00"
END   = "2025-12-31 23:50:00"
FREQ  = "10min"

# Finnish meteorological seasons by month.
SEASON_MAP = {
    12: "winter", 1: "winter", 2: "winter",
    3:  "spring", 4: "spring", 5: "spring",
    6:  "summer", 7: "summer", 8: "summer",
    9:  "autumn", 10: "autumn", 11: "autumn",
}


def build_dim_time(output_path="data/generated/dim_time.csv"):

    timestamps = pd.date_range(start=START, end=END, freq=FREQ)
    print(f"Generating {len(timestamps):,} time dimension rows...")

    dim_time = pd.DataFrame({"timestamp": timestamps})

    dim_time["time_id"]   = [f"TIME-{i:07d}" for i in range(1, len(dim_time) + 1)]
    dim_time["hour"]      = dim_time["timestamp"].dt.hour
    dim_time["day"]       = dim_time["timestamp"].dt.day
    dim_time["week"]      = dim_time["timestamp"].dt.isocalendar().week.astype(int)
    dim_time["month"]     = dim_time["timestamp"].dt.month
    dim_time["year"]      = dim_time["timestamp"].dt.year
    dim_time["is_weekend"] = dim_time["timestamp"].dt.dayofweek >= 5
    dim_time["season"]    = dim_time["month"].map(SEASON_MAP)

    # Reorder columns to match the schema definition.
    dim_time = dim_time[[
        "time_id", "timestamp", "hour", "day",
        "week", "month", "year", "is_weekend", "season"
    ]]

    dim_time.to_csv(output_path, index=False)
    print(f"Saved {len(dim_time):,} rows to {output_path}")
    print("\nSample rows:")
    print(dim_time.head(3).to_string(index=False))
    print("\nSeason distribution:")
    print(dim_time["season"].value_counts())

    return dim_time


if __name__ == "__main__":
    build_dim_time()
