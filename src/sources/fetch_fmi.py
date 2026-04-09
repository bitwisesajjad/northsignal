import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta

NS_WFS = "http://www.opengis.net/wfs/2.0"
NS_BSWFS = "http://xml.fmi.fi/schema/wfs/2.0"


def generate_weekly_ranges(year):
    ranges = []
    start = datetime(year, 1, 1)
    end_of_year = datetime(year, 12, 31, 23, 59, 59)

    while start <= end_of_year:
        end = min(start + timedelta(days=6, hours=23, minutes=59, seconds=59), end_of_year)
        ranges.append((
            start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            end.strftime("%Y-%m-%dT%H:%M:%SZ")
        ))
        start += timedelta(days=7)

    return ranges


def fetch_week(start, end):
    query = (
        f"service=WFS"
        f"&version=2.0.0"
        f"&request=getFeature"
        f"&storedquery_id=fmi::observations::weather::simple"
        f"&fmisid=101794"
        f"&starttime={start}"
        f"&endtime={end}"
        f"&parameters=t2m,snow_aws,ws_10min"
    )

    response = requests.get(f"https://opendata.fmi.fi/wfs?{query}")
    response.raise_for_status()

    root = ET.fromstring(response.text)
    observations = {}

    for member in root.findall(f"{{{NS_WFS}}}member"):
        element = member.find(f"{{{NS_BSWFS}}}BsWfsElement")
        time = element.find(f"{{{NS_BSWFS}}}Time").text
        param = element.find(f"{{{NS_BSWFS}}}ParameterName").text
        value = element.find(f"{{{NS_BSWFS}}}ParameterValue").text

        if time not in observations:
            observations[time] = {"time": time}

        observations[time][param] = None if value == "NaN" else float(value)

    return list(observations.values())


all_observations = []
weeks = []
for year in [2022, 2023, 2024, 2025]:
    weeks.extend(generate_weekly_ranges(year))

for start, end in weeks:
    print(f"Fetching {start[:10]} to {end[:10]}...")
    rows = fetch_week(start, end)
    all_observations.extend(rows)

df = pd.DataFrame(all_observations)
df = df.rename(columns={
    "t2m": "temperature_c",
    "snow_aws": "snow_depth_cm",
    "ws_10min": "wind_speed_ms"
})
df = df[["time", "temperature_c", "snow_depth_cm", "wind_speed_ms"]]
df = df.sort_values("time").reset_index(drop=True)

df.to_csv("data/raw/fmi_oulu_2022_2025.csv", index=False)
print(f"Saved {len(df)} observations to data/raw/fmi_oulu_2022_2025.csv")