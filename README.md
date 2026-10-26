#  YouTube Trends & Engagement Analytics

### End-to-End Data Engineering Project | Microsoft Fabric • PySpark • Delta Lake • Power BI

Turning raw YouTube trending-video data into actionable insights through a modern Lakehouse architecture.

##  Project Overview

**What content attracts the most views on YouTube? Which videos generate the highest engagement? How do trending-video patterns differ across regions?**

This project explores these questions by building an end-to-end analytics pipeline using Microsoft Fabric.

I collected trending-video metadata from the **YouTube Data API**, transformed the data using **PySpark**, implemented a **Bronze–Silver–Gold Medallion Architecture**, and developed an interactive **Power BI dashboard**.

The solution demonstrates the journey from raw API data to business-ready analytics.

##  Project Highlights

| Metric | Result |
|---|---|
| Trending-video observations processed | 2,500 |
| Unique videos analysed | 1,952 |
| Regions covered | 13 |
| Architecture | Bronze → Silver → Gold |
| Gold analytics tables | 3 |
| Dashboard | Power BI |

##  Solution Architecture

<img width="1695" height="928" alt="image" src="https://github.com/user-attachments/assets/a8d855bc-4529-477e-833f-514c759ae4fb" />


### Bronze Layer — Raw Data Ingestion

- Retrieved trending-video metadata using the YouTube Data API.
- Collected video details, categories, channels, timestamps and engagement metrics.
- Stored the raw dataset in JSONL format in Microsoft Fabric Lakehouse.
- Preserved the original source data for subsequent transformations.

### Silver Layer — Data Cleaning and Validation

Developed PySpark transformations to:

- Handle missing descriptions and nullable fields.
- Convert API timestamps into Spark timestamp format.
- Validate numerical engagement metrics.
- Identify duplicate observations and repeated video IDs across regions.
- Add processing metadata.
- Persist the cleaned dataset as a Delta table.

**Output:** `silver_youtube_videos`

### Gold Layer — Analytics-Ready Data

Created three Gold Delta tables to support reporting and analysis.

| Gold Table | Purpose |
|---|---|
| `gold_youtube_category` | Analyse category popularity using observed video views |
| `gold_youtube_engagement` | Calculate video-level engagement rates |
| `gold_youtube_region` | Compare trending-video samples across regions |

Used PySpark aggregations, distinct counts and window functions to prepare reporting datasets while accounting for repeated video observations.

##  Power BI Dashboard

Built an interactive Power BI report connected to Microsoft Fabric Gold tables through a semantic model.

The dashboard provides:

**1. Content Category Popularity**

Identify the categories contributing the most observed video views.

**2. Unique Videos and Regional Coverage**

Track the number of unique videos analysed and the geographic coverage of the sample.

**3. Video Engagement Analysis**

Rank videos by a calculated engagement-rate metric:

`Engagement Rate (%) = (Likes + Comments) / Views × 100`

The Top 10 engagement visual excludes videos with fewer than 10,000 views to reduce the influence of very small view counts.

**4. Regional Trends**

Compare average overall video views for videos appearing in the trending samples of different regions.

### Dashboard Preview

<img width="777" height="441" alt="image" src="https://github.com/user-attachments/assets/5bbfbc80-c75b-4cb8-9687-dfb13733c967" />


## 🔎 Key Insights

- **Gaming** emerged as a leading category by observed views within the collected sample.
- The dataset contained **1,952 distinct videos** from 2,500 trending observations, reflecting some overlap across regions.
- Engagement rates varied considerably between videos, demonstrating that view count alone does not fully describe audience interaction.
- Average overall video views differed across regional trending samples.

These insights describe the collected dataset and should not be interpreted as platform-wide YouTube statistics.

## 🛠️ Technology Stack

| Technology | Application |
|---|---|
| Python | YouTube API ingestion |
| YouTube Data API | Trending-video metadata |
| Microsoft Fabric | Lakehouse and analytics platform |
| PySpark | Data transformation and validation |
| Delta Lake | Silver and Gold table storage |
| SQL | Data exploration and validation |
| Power BI | Dashboard and reporting |
| GitHub | Source control and project documentation |

## 📁 Repository Structure

```text
youtube-trends-fabric-analytics/
│
├── notebooks/
│   └── 02_fabric_medallion_pipeline.ipynb
│
├── powerbi/
│   ├── README.md
│   └── YouTube_Trends_Analytics.pbix
│
├── screenshots/
│   └── dashboard_overview.png
│
├── 01_bronze_ingestion.py
│
└── README.md
```

*File names may differ slightly from the example structure.*

## 🧪 Data Quality and Validation

The pipeline incorporates validation checks covering:

- Missing values and data completeness
- Duplicate video observations
- Timestamp conversion accuracy
- Invalid or negative numeric metrics
- Engagement-rate calculation validity
- Regional data consistency

These checks help improve the reliability of the datasets used for reporting.

## ⚠️ Dataset Scope and Limitations

This project uses a sample of trending-video observations collected through the YouTube Data API.

- It does not represent every video uploaded to YouTube or a complete historical month of activity.
- Overall video view counts are not country-specific view counts.
- A video may appear in multiple regional trending samples.
- Engagement rate is a custom analytical metric, not an official YouTube engagement measure.
- API quotas and collection timing affect the available sample.

## 🚀 What This Project Demonstrates

This project showcases practical experience in:

- REST API data ingestion
- End-to-end ETL/ELT pipeline development
- Medallion Lakehouse architecture
- PySpark data engineering
- Delta Lake data modelling
- Data quality and validation
- Analytics-ready Gold layer design
- Power BI reporting and visualisation

**From raw API responses to an interactive analytics dashboard — built using Microsoft Fabric.**

---

### Future Enhancements

Potential improvements include scheduled ingestion, incremental data processing, historical trend analysis, automated data-quality monitoring and expanded dashboard interactivity.
