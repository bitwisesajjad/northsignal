# northsignal — Telecom Data Engineering Portfolio Project

**Repository:** https://github.com/bitwisesajjad/northsignal

## What This Project Is

A full end-to-end data engineering and analytics project built around a realistic simulation of telecom network operations data, set in Oulu, Finland. The goal is to cover every layer of a modern data stack: ingestion, storage, transformation, warehousing, orchestration, containerization, and visualization.

The dataset is synthetic but grounded in real open data sources. Every dimension, tower locations, weather, geography, customer behavior, signal metrics, is anchored to something that actually exists. Nothing is fabricated without a real-world reference.

---

## The Story Behind the Data

Oulu is home to significant telecom R&D activity, particularly around 5G and 6G radio access network development. This project simulates what a data engineer at a telecom Network Operations Center (NOC) in Oulu would actually work with.

Cell towers placed at real GPS coordinates across Finnish regions. Signal quality metrics reported per tower every few minutes. Customer connections, data usage, handover events. Network incidents, outages, maintenance tickets, degraded service windows. Spectrum band allocation per tower. Weather data from Oulu that correlates with signal drops in winter, because Finnish winters are harsh and that shows up in the numbers.

This is not a generic churn dataset. It is a RAN operations dataset with a Finnish identity, and that specificity is the point.

---

## Real Data Sources Used

Each source contributes statistical truth to one dimension of the synthetic dataset.

| Source                                                 | What It Provides                                                                                  | URL                               |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------- | --------------------------------- |
| Traficom (Finnish Transport and Communications Agency) | Real Finnish cell tower GPS coordinates, operator, frequency band, mast height                    | traficom.fi/en/open-data          |
| OpenCelliD                                             | Crowdsourced global tower database: tower IDs, coordinates, signal range, technology type (4G/5G) | opencellid.org                    |
| FMI (Finnish Meteorological Institute)                 | Historical weather data for Oulu: temperature, snow, wind, for seasonal signal correlation        | en.ilmatieteenlaitos.fi/open-data |
| Statistics Finland                                     | Population density, municipality boundaries, urban/rural classification across Finnish regions    | stat.fi/en                        |
| IBM Watson Telco Churn Dataset (Kaggle)                | Customer behavioral distributions: contract types, usage levels, churn rates                      | kaggle.com                        |
| Telecom KPI datasets (Kaggle/GitHub)                   | Real signal metric ranges: RSRP, SINR, throughput, latency, handover frequency                    | kaggle.com                        |

The generation layer reads distributions from these sources and uses them as constraints when producing millions of synthetic rows.

---

## Full Architecture

```
DATA SOURCES LAYER
├── Traficom API               real Finnish tower locations
├── OpenCelliD                 tower signal parameters
├── FMI API                    Oulu historical weather
├── Statistics Finland API     population and geography
└── Kaggle datasets            behavioral and KPI distributions

GENERATION LAYER
└── Python scripts             produce 1M+ row synthetic dataset grounded in real distributions

INGESTION LAYER
└── Apache Kafka               stream CDR and network events in real time

STORAGE LAYER
└── Azure Data Lake (ADLS Gen2) raw landing zone

PROCESSING LAYER
└── PySpark on Azure Databricks clean, transform, enrich, write to Delta Lake

WAREHOUSE LAYER
├── PostgreSQL                 local development star schema
└── Azure Synapse Analytics    production star schema

ORCHESTRATION LAYER
└── Apache Airflow             DAG scheduling and pipeline dependency management

CONTAINERIZATION LAYER
├── Docker                     all components containerized
└── Kubernetes (AKS)           deploy and manage containers, expose public endpoints

VISUALIZATION LAYER
├── Power BI + DAX             executive KPI dashboard with time intelligence
├── Python visuals in Power BI custom charts using matplotlib/plotly inside Power BI
├── Kepler.gl or Folium        live map of tower health and incident hotspots
└── Grafana                    real-time pipeline and infrastructure monitoring

DOCUMENTATION LAYER
└── GitHub repository          README, architecture diagram, data dictionary, setup guide
```

---

## Why Each Layer Exists

**Data Sources Layer**
Without real sources, synthetic data is just made-up numbers. These open datasets give the generator realistic ranges, distributions, and geographic truth. The output feels credible because every dimension is anchored to something that actually exists.

**Generation Layer**
No public telecom operations dataset exists at the scale needed to practice big data engineering. So this project builds one, honestly. The generator learns what real data looks like from the sources above, then produces statistically faithful rows at scale. This is also where pandas, statistical sampling, and time-series generation come in.

**Ingestion Layer — why Kafka?**
Real telecom networks produce events continuously. A call starts. A handover happens. A tower reports a signal drop. Kafka is a message broker built for exactly this: high-throughput, continuous event streams. A producer pushes events in, a consumer reads them out and passes them downstream. This is how production telemetry pipelines in the industry work.

**Storage Layer — why a Data Lake first?**
Raw data needs to land somewhere cheap and schema-flexible before any transformation happens. Azure Data Lake stores everything as files, Parquet, CSV, JSON, organized by date and source. It's the raw zone. You never transform in place. You always keep the original. That's a core principle in data engineering, and it saves you when something goes wrong downstream.

**Processing Layer — why PySpark?**
Pandas runs out of memory at scale. PySpark splits the work across multiple machines so it doesn't. Databricks is the managed platform that runs those Spark jobs without requiring manual cluster setup. Cleaning, joining dimensions, computing derived columns, writing to the warehouse, all of that happens here.

**Warehouse Layer — why a Star Schema?**
A star schema has two types of tables. Fact tables record things that happened: a network event, a customer session. Dimension tables provide context: which tower, which customer, which time period. This structure makes analytical queries fast and Power BI models clean. PostgreSQL handles local development without cloud costs. Synapse is the production version.

**Orchestration Layer — why Airflow?**
Every step in the pipeline depends on the one before it. Airflow lets you define a DAG (Directed Acyclic Graph) that maps those dependencies explicitly. Fetch the weather data first, then run the generator, then land files in the lake, then run the Spark job, then load to the warehouse. If anything fails, Airflow retries it, logs the failure, and stops downstream tasks from running on bad data.

**Containerization Layer — why Docker and Kubernetes?**
Docker packages each component, Kafka, Airflow, the generator scripts, into a container with all its dependencies bundled in. No more "it works on my machine." Kubernetes manages those containers: scheduling them across machines, restarting crashed ones, scaling up under load. Running on AKS (Azure Kubernetes Service) makes the whole project publicly accessible via a URL.

**Visualization Layer**
Power BI connected to Synapse answers the business questions with interactive dashboards. DAX computes the KPIs: rolling averages, time intelligence, SLA compliance flags. The map shows tower health geographically, which is immediately readable by anyone. Grafana watches the pipeline itself. Is Kafka healthy? Did the last Spark job take longer than usual? That kind of monitoring is what keeps a real pipeline trustworthy.

---

## The Star Schema (Warehouse Design)

```
FACT_NETWORK_EVENTS          one row per tower measurement interval
├── event_id
├── tower_id                 FK to DIM_TOWERS
├── customer_id              FK to DIM_CUSTOMERS
├── time_id                  FK to DIM_TIME
├── weather_id               FK to DIM_WEATHER
├── rsrp_dbm                 signal strength
├── sinr_db                  signal quality
├── throughput_mbps
├── latency_ms
├── handover_flag
└── incident_id              FK to DIM_INCIDENTS (nullable)

DIM_TOWERS
├── tower_id
├── latitude
├── longitude
├── municipality
├── region
├── operator
├── technology (4G/5G)
├── frequency_band
└── mast_height_m

DIM_CUSTOMERS
├── customer_id
├── contract_type
├── device_type
├── subscription_tier
└── churn_risk_score

DIM_TIME
├── time_id
├── timestamp
├── hour, day, week, month, year
├── is_weekend
└── season

DIM_WEATHER
├── weather_id
├── temperature_c
├── snow_depth_cm
├── wind_speed_ms
└── condition

DIM_INCIDENTS
├── incident_id
├── incident_type
├── severity
├── resolution_time_minutes
└── affected_towers_count
```

---

## Key Business Questions the Dashboard Answers

1. Which towers in Northern Finland show degraded RSRP in winter months, and does snow depth correlate with signal drop?
2. What is the 30-day rolling average throughput per region, and which regions are trending below SLA thresholds?
3. Which customer segments experience the most handover failures, and what is their churn risk?
4. What percentage of network incidents are resolved within SLA, broken down by incident type and severity?
5. How does 5G coverage compare to 4G across Finnish municipalities by population density?

---

## Technologies

| Technology              | Purpose                                      | Where It Appears                 |
| ----------------------- | -------------------------------------------- | -------------------------------- |
| Python                  | Data generation, API calls, pipeline scripts | Generation and processing layers |
| Apache Kafka            | Real-time event streaming                    | Ingestion layer                  |
| Azure Data Lake Gen2    | Raw data storage                             | Storage layer                    |
| PySpark / Databricks    | Large-scale data transformation              | Processing layer                 |
| PostgreSQL              | Local star schema development                | Warehouse layer                  |
| Azure Synapse Analytics | Production data warehouse                    | Warehouse layer                  |
| Apache Airflow          | Pipeline orchestration and scheduling        | Orchestration layer              |
| Docker                  | Containerizing all components                | Containerization layer           |
| Kubernetes / AKS        | Managing and deploying containers publicly   | Containerization layer           |
| Power BI + DAX          | Executive dashboard and KPI reporting        | Visualization layer              |
| Python in Power BI      | Custom visual scripts                        | Visualization layer              |
| Kepler.gl / Folium      | Geographic tower map                         | Visualization layer              |
| Grafana                 | Pipeline and infrastructure monitoring       | Visualization layer              |
| GitHub                  | Version control and documentation            | Throughout                       |

---

## Folder Structure

```
northsignal/
├── data/
│   ├── raw/                  downloaded source files from APIs
│   ├── generated/            synthetic dataset output files
│   └── warehouse/            local PostgreSQL exports
├── src/
│   ├── sources/              scripts that fetch from Traficom, FMI, OpenCelliD, etc.
│   ├── generator/            synthetic dataset generation scripts
│   ├── kafka/                producer and consumer scripts
│   ├── spark/                PySpark transformation jobs
│   ├── warehouse/            SQL schema definitions and load scripts
│   └── viz/                  Folium/Kepler map scripts, Power BI Python visuals
├── airflow/
│   └── dags/                 Airflow DAG definitions
├── k8s/
│   └── manifests/            Kubernetes deployment YAML files
├── docker/
│   └── Dockerfile.*          one per service
├── powerbi/
│   └── northsignal.pbix      Power BI report file
├── docs/
│   ├── architecture.png      architecture diagram
│   └── data_dictionary.md    field-by-field description of all tables
└── README.md
```

---

## Status

- [ ] Fetch and explore Traficom tower data
- [ ] Fetch and explore OpenCelliD data for Finland
- [ ] Set up FMI API access and pull Oulu weather history
- [ ] Design final star schema in detail
- [ ] Build dataset generator (Phase 1: towers and geography)
- [ ] Build dataset generator (Phase 2: network events and KPIs)
- [ ] Build dataset generator (Phase 3: customers and incidents)
- [ ] Set up Kafka locally in Docker
- [ ] Set up Airflow locally in Docker
- [ ] Set up local PostgreSQL and load star schema
- [ ] Write PySpark transformation jobs
- [ ] Deploy to Azure (Data Lake, Databricks, Synapse)
- [ ] Deploy Kafka and Airflow to Kubernetes (AKS)
- [ ] Build Power BI model and DAX measures
- [ ] Build tower map visualization
- [ ] Set up Grafana monitoring
- [ ] Write GitHub README and architecture diagram
- [ ] Make dashboard publicly accessible
