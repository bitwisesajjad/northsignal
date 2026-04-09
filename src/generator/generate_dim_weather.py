import pandas as pd
import numpy as np

# Thresholds for deriving weather condition from raw FMI measurements.
# Based on Finnish Meteorological Institute classification guidelines.
BLIZZARD_WIND_MS    = 10.0  # metres per second
BLIZZARD_SNOW_CM    = 10.0  # centimetres
WINDY_WIND_MS       = 7.0
SNOW_DEPTH_CM       = 2.0   # any snow on the ground


def derive_condition(row):
    wind = row["wind_speed_ms"]
    snow = row["snow_depth_cm"]

    wind = wind if pd.notna(wind) else 0.0
    snow = snow if pd.notna(snow) else 0.0

    if wind >= BLIZZARD_WIND_MS and snow >= BLIZZARD_SNOW_CM:
        return "blizzard"
    if snow >= SNOW_DEPTH_CM:
        return "snow"
    if wind >= WINDY_WIND_MS:
        return "windy"
    return "clear"


def build_dim_weather(fmi_path="data/raw/fmi_oulu_2022_2025.csv",
                      output_path="data/generated/dim_weather.csv"):

    print("Loading FMI weather data...")
    fmi = pd.read_csv(fmi_path, parse_dates=["time"])
    print(f"Loaded {len(fmi):,} observations.")

    fmi = fmi.sort_values("time").reset_index(drop=True)

    dim_weather = pd.DataFrame({
        "weather_id":    [f"WTH-{i:07d}" for i in range(1, len(fmi) + 1)],
        "timestamp":     fmi["time"],
        "temperature_c": fmi["temperature_c"].round(1),
        "snow_depth_cm": fmi["snow_depth_cm"].round(1),
        "wind_speed_ms": fmi["wind_speed_ms"].round(1),
    })

    print("Deriving condition labels...")
    dim_weather["condition"] = dim_weather.apply(derive_condition, axis=1)

    # Keep timestamp for joining to DIM_TIME and FACT_NETWORK_EVENTS.
    # It is not part of the final warehouse schema but is needed during
    # the fact table generation step to match weather to events.
    dim_weather = dim_weather[[
        "weather_id", "timestamp", "temperature_c",
        "snow_depth_cm", "wind_speed_ms", "condition"
    ]]

    dim_weather.to_csv(output_path, index=False)
    print(f"Saved {len(dim_weather):,} rows to {output_path}")

    print("\nCondition distribution:")
    print(dim_weather["condition"].value_counts())
    print("\nTemperature stats:")
    print(dim_weather["temperature_c"].describe().round(2))
    print("\nNull counts:")
    print(dim_weather.isnull().sum())

    return dim_weather


if __name__ == "__main__":
    build_dim_weather()
