# Data Dictionary

## OpenCelliD — Finland Tower Data
Source: OpenCelliD (Unwired Labs)  
File: `data/raw/opencellid_finland.csv`  
Rows: 33,063  
Filter: MCC 244 (Finland only)

| Column | Description |
|--------|-------------|
| radio | Network technology: GSM (2G), UMTS (3G), LTE (4G), NR (5G) |
| mcc | Mobile Country Code. 244 for Finland |
| net | Mobile Network Code (MNC). Identifies the operator: 1 = Elisa, 3 = DNA, 5 = Telia |
| area | Location Area Code (LAC). Groups cells into geographic areas within a network |
| cell | Cell ID. Unique identifier for a single antenna within an area |
| unit | Secondary cell identifier, used in some network types. Usually 0 |
| lon | Longitude of the tower in decimal degrees |
| lat | Latitude of the tower in decimal degrees |
| range | Estimated signal range of the tower in meters |
| samples | Number of measurements used to calculate this tower's position |
| changeable | Whether the tower position can be updated by new measurements. 1 = yes |
| created | Unix timestamp when this tower was first added to the database |
| updated | Unix timestamp when this tower record was last updated |
| averageSignal | Average signal strength across all measurements for this tower |
