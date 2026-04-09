import pandas as pd
import geopandas as gpd
import requests
import numpy as np
from io import BytesIO

# Finnish spectrum allocation by operator and technology.
# Based on Traficom public license data.
FREQUENCY_BANDS = {
    ("Elisa", "4G"): ["800 MHz", "1800 MHz", "2100 MHz", "2600 MHz"],
    ("Elisa", "5G"): ["3500 MHz", "26 GHz"],
    ("DNA",   "4G"): ["800 MHz", "1800 MHz", "2600 MHz"],
    ("DNA",   "5G"): ["3500 MHz", "26 GHz"],
    ("Telia", "4G"): ["700 MHz", "1800 MHz", "2100 MHz"],
    ("Telia", "5G"): ["3500 MHz", "700 MHz"],
}

MNC_TO_OPERATOR = {1: "Elisa", 3: "DNA", 5: "Telia"}
RADIO_TO_TECH   = {"LTE": "4G", "NR": "5G"}

# Mast height ranges in metres. Urban towers are shorter because
# they sit on rooftops or in dense areas with closer spacing.
# Rural towers are taller to cover more ground.
MAST_HEIGHT = {
    "urban":    (15, 30),
    "suburban": (25, 40),
    "rural":    (35, 55),
}


def fetch_municipality_boundaries():
    """Fetch Finnish municipality polygons from Statistics Finland WFS."""
    url = (
        "https://geo.stat.fi/geoserver/tilastointialueet/wfs"
        "?service=WFS"
        "&version=2.0.0"
        "&request=GetFeature"
        "&typeNames=tilastointialueet:kunta4500k"
        "&outputFormat=application/json"
    )
    print("Fetching municipality boundaries from Statistics Finland...")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    municipalities = gpd.read_file(BytesIO(response.content))
    # Statistics Finland uses ETRS-TM35FIN (EPSG:3067). Convert to WGS84
    # so it matches the OpenCelliD coordinates.
    municipalities = municipalities.to_crs(epsg=4326)
    print(f"Loaded {len(municipalities)} municipality polygons.")
    return municipalities


def load_opencellid(path="data/raw/opencellid_finland.csv"):
    """Load the filtered Finnish tower data and keep only 4G and 5G."""
    df = pd.read_csv(path)
    df = df[df["radio"].isin(["LTE", "NR"])].copy()
    df = df[df["net"].isin(MNC_TO_OPERATOR.keys())].copy()
    df = df.dropna(subset=["lat", "lon"]).copy()
    print(f"Towers after filtering to 4G/5G and known operators: {len(df)}")
    return df


def assign_urban_class(row, municipalities):
    """Classify a tower as urban, suburban, or rural.

    Uses the municipality name as a proxy. Oulu, Tampere, Helsinki and
    other major cities are urban. Municipalities with fewer than roughly
    20,000 people are rural. Everything else is suburban.

    This is a simplified heuristic. The generator does not load a full
    population density grid at this stage.
    """
    urban_cities = {
        "Helsinki", "Espoo", "Tampere", "Vantaa", "Oulu",
        "Turku", "Jyväskylä", "Lahti", "Kuopio", "Pori",
    }
    suburban_cities = {
        "Joensuu", "Lappeenranta", "Hämeenlinna", "Vaasa",
        "Rovaniemi", "Seinäjoki", "Mikkeli", "Kotka", "Salo",
    }
    name = row.get("municipality", "")
    if name in urban_cities:
        return "urban"
    if name in suburban_cities:
        return "suburban"
    return "rural"


def spatial_join_municipalities(towers_df, municipalities):
    """Join tower points to municipality polygons."""
    gdf = gpd.GeoDataFrame(
        towers_df,
        geometry=gpd.points_from_xy(towers_df["lon"], towers_df["lat"]),
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(gdf, municipalities[["nimi", "geometry"]], how="left", predicate="within")
    joined = joined.rename(columns={"nimi": "municipality"})
    # Towers that fall outside all polygons (e.g. on water) get unknown.
    joined["municipality"] = joined["municipality"].fillna("unknown")
    return joined


def assign_region(municipality_name, municipalities_df):
    """Map municipality name to one of Finland's 19 regions.

    Statistics Finland's WFS layer includes a region code field. This
    function builds a lookup from the already-fetched GeoDataFrame.
    """
    # Build a name-to-region mapping from the municipalities GeoDataFrame.
    # The field name varies by layer version so we check for common names.
    region_col = None
    for col in ["maakunta_nimi", "maakuntanimi", "mknimi"]:
        if col in municipalities_df.columns:
            region_col = col
            break

    if region_col is None:
        return "unknown"

    match = municipalities_df[municipalities_df["nimi"] == municipality_name]
    if match.empty:
        return "unknown"
    return match.iloc[0][region_col]


def build_dim_towers(opencellid_path="data/raw/opencellid_finland.csv",
                     output_path="data/generated/dim_towers.csv"):

    towers_raw = load_opencellid(opencellid_path)
    municipalities = fetch_municipality_boundaries()

    towers = spatial_join_municipalities(towers_raw, municipalities)

    rng = np.random.default_rng(seed=42)

    rows = []
    for i, row in enumerate(towers.itertuples(), start=1):
        operator  = MNC_TO_OPERATOR.get(row.net, "unknown")
        technology = RADIO_TO_TECH.get(row.radio, "unknown")
        urban_class = assign_urban_class(row._asdict(), municipalities)

        bands = FREQUENCY_BANDS.get((operator, technology), ["unknown"])
        freq_band = rng.choice(bands)

        height_min, height_max = MAST_HEIGHT[urban_class]
        mast_height = round(float(rng.uniform(height_min, height_max)), 1)

        municipality = getattr(row, "municipality", "unknown")

        rows.append({
            "tower_id":       f"TWR-{i:05d}",
            "latitude":       round(row.lat, 6),
            "longitude":      round(row.lon, 6),
            "municipality":   municipality,
            "region":         assign_region(municipality, municipalities),
            "operator":       operator,
            "technology":     technology,
            "frequency_band": freq_band,
            "mast_height_m":  mast_height,
        })

    dim_towers = pd.DataFrame(rows)
    dim_towers.to_csv(output_path, index=False)
    print(f"Saved {len(dim_towers)} towers to {output_path}")
    print(dim_towers.head())
    return dim_towers


if __name__ == "__main__":
    build_dim_towers()
