# Arsitektur Pipeline Big Data Ketahanan Pangan Lampung

Diagram ini mengilustrasikan arsitektur pipeline big data yang komprehensif, menunjukkan alur data dari sumber eksternal melalui layer medallion (Bronze-Silver-Gold), komponen infrastruktur, orkestrasi, dan visualisasi analitik.

```mermaid
flowchart TD
    %% Sumber Data
    BPS[("BPS<br/>Badan Pusat<br/>Statistik")]
    BMKG[("BMKG<br/>Badan Meteorologi<br/>& Geofisika")]
    PIHPS[("PIHPS<br/>Sistem Informasi<br/>Harga Pangan")]
    GOVT[("Lembaga<br/>Pemerintah")]

    %% Layer Bronze
    subgraph BRONZE ["LAYER BRONZE (Data Mentah)"]
        HDFS_BRONZE[("HDFS<br/>/data/bronze/<br/>File CSV Mentah")]
        FILES["File CSV:<br/>• produksi_pangan.csv<br/>• harga_pangan.csv<br/>• cuaca.csv<br/>• sosial_ekonomi.csv<br/>• konsumsi_pangan.csv<br/>• ikp.csv"]
    end

    %% Layer Silver
    subgraph SILVER ["LAYER SILVER (Data Bersih)"]
        SPARK_ETL["Apache Spark<br/>ETL Jobs"]
        HDFS_SILVER[("HDFS<br/>/data/silver/<br/>File Parquet")]
        HIVE_SILVER[("Tabel Hive<br/>silver.produksi_pangan<br/>silver.harga_pangan<br/>silver.cuaca<br/>silver.sosial_ekonomi<br/>silver.konsumsi_pangan<br/>silver.ikp")]
    end

    %% Layer Gold
    subgraph GOLD ["LAYER GOLD (Siap Analitik)"]
        SPARK_ANALYTICS["Spark Analytics<br/>Business Logic"]
        HDFS_GOLD[("HDFS<br/>/data/gold/<br/>File Parquet")]
        HIVE_GOLD[("Tabel Hive<br/>gold.ketahanan_pangan_kab<br/>gold.ketahanan_pangan_enriched")]
    end

    %% Infrastruktur Pemrosesan & Penyimpanan
    subgraph INFRA ["INFRASTRUKTUR BIG DATA"]
        HADOOP[("Ekosistem Hadoop<br/>HDFS Distributed Storage")]
        SPARK_MASTER["Spark Cluster<br/>Master + Workers"]
        HIVE_META[("Hive Metastore<br/>Manajemen Schema")]
    end

    %% Orkestrasi
    subgraph ORCHESTRATION ["ORKESTRASI"]
        AIRFLOW["Apache Airflow<br/>Otomasi Pipeline<br/>DAG: lampung_foodsec_dag"]
        SCRIPTS["Script Otomasi<br/>• run_bronze.sh<br/>• run_silver.sh<br/>• run_gold.sh"]
    end

    %% Analitik & Visualisasi
    subgraph ANALYTICS ["ANALITIK & VISUALISASI"]
        SUPERSET["Apache Superset<br/>Business Intelligence<br/>Dashboards & Reports"]
        HIVE_QUERY["Hive SQL<br/>Ad-hoc Queries"]
    end

    %% Kualitas Data
    subgraph QUALITY ["KUALITAS DATA"]
        DQ_UTILS["Quality Utils<br/>src/utils/data_quality.py<br/>• Validation<br/>• Profiling<br/>• Scoring"]
        CONFIG["Config Management<br/>src/config/settings.py<br/>• Schemas<br/>• Thresholds"]
    end

    %% Koneksi Alur Data
    BPS --> HDFS_BRONZE
    BMKG --> HDFS_BRONZE
    PIHPS --> HDFS_BRONZE
    GOVT --> HDFS_BRONZE

    HDFS_BRONZE --> FILES
    FILES --> SPARK_ETL

    SPARK_ETL --> HDFS_SILVER
    HDFS_SILVER --> HIVE_SILVER

    HIVE_SILVER --> SPARK_ANALYTICS
    SPARK_ANALYTICS --> HDFS_GOLD
    HDFS_GOLD --> HIVE_GOLD

    %% Koneksi Infrastruktur
    HADOOP -.-> HDFS_BRONZE
    HADOOP -.-> HDFS_SILVER
    HADOOP -.-> HDFS_GOLD
    SPARK_MASTER -.-> SPARK_ETL
    SPARK_MASTER -.-> SPARK_ANALYTICS
    HIVE_META -.-> HIVE_SILVER
    HIVE_META -.-> HIVE_GOLD

    %% Koneksi Orkestrasi
    AIRFLOW --> SCRIPTS
    SCRIPTS --> SPARK_ETL
    SCRIPTS --> SPARK_ANALYTICS

    %% Koneksi Analitik
    HIVE_GOLD --> SUPERSET
    HIVE_GOLD --> HIVE_QUERY

    %% Koneksi Kualitas
    DQ_UTILS -.-> SPARK_ETL
    DQ_UTILS -.-> SPARK_ANALYTICS
    CONFIG -.-> DQ_UTILS

    %% Styling - Claude AI Color Palette
    classDef sourceStyle fill:#FEF3E2,stroke:#F59E0B,stroke-width:2px,color:#000000
    classDef bronzeStyle fill:#FFF4ED,stroke:#FF6B35,stroke-width:2px,color:#000000
    classDef silverStyle fill:#F1F5F9,stroke:#64748B,stroke-width:2px,color:#000000
    classDef goldStyle fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#000000
    classDef infraStyle fill:#EFF6FF,stroke:#2563EB,stroke-width:2px,color:#000000
    classDef analyticsStyle fill:#F0F9FF,stroke:#0EA5E9,stroke-width:2px,color:#000000
    classDef orchestrationStyle fill:#F5F3FF,stroke:#7C3AED,stroke-width:2px,color:#000000
    classDef qualityStyle fill:#ECFDF5,stroke:#10B981,stroke-width:2px,color:#000000

    class BPS,BMKG,PIHPS,GOVT sourceStyle
    class HDFS_BRONZE,FILES bronzeStyle
    class SPARK_ETL,HDFS_SILVER,HIVE_SILVER silverStyle
    class SPARK_ANALYTICS,HDFS_GOLD,HIVE_GOLD goldStyle
    class HADOOP,SPARK_MASTER,HIVE_META infraStyle
    class SUPERSET,HIVE_QUERY analyticsStyle
    class AIRFLOW,SCRIPTS orchestrationStyle
    class DQ_UTILS,CONFIG qualityStyle
```

## Komponen Arsitektur

### Sumber Data
- **BPS**: Badan Pusat Statistik (data produksi, konsumsi)
- **BMKG**: Badan Meteorologi dan Geofisika (data cuaca, iklim)
- **PIHPS**: Sistem Informasi Harga Pangan
- **Lembaga Pemerintah**: Data sosial ekonomi tambahan

### Layer Arsitektur Medallion
- **Bronze**: File CSV mentah disimpan di HDFS
- **Silver**: File Parquet yang dibersihkan dan divalidasi dengan tabel Hive
- **Gold**: Metrik business dan indikator siap analitik

### Infrastruktur
- **Hadoop HDFS**: Distributed file storage
- **Apache Spark**: Distributed processing engine
- **Hive**: Data warehouse dan interface SQL
- **Airflow**: Orkestrasi workflow
- **Superset**: Business intelligence dan visualisasi

### Kualitas Data & Engineering
- Manajemen konfigurasi terpusat
- Validasi dan profiling data otomatis
- Quality scoring dan reporting
- Penegakan schema dan consistency checks