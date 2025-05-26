# Sistem Big Data Ketahanan Pangan Lampung - Dokumentasi Arsitektur

## Daftar Isi
- [Gambaran Sistem](#gambaran-sistem)
- [Prinsip Arsitektur](#prinsip-arsitektur)
- [Stack Teknologi](#stack-teknologi)
- [Arsitektur Medallion](#arsitektur-medallion)
- [Arsitektur Komponen](#arsitektur-komponen)
- [Alur Data](#alur-data)
- [Pengaturan Infrastruktur](#pengaturan-infrastruktur)
- [Arsitektur Keamanan](#arsitektur-keamanan)
- [Pertimbangan Performa](#pertimbangan-performa)
- [Skalabilitas](#skalabilitas)
- [Monitoring dan Observabilitas](#monitoring-dan-observabilitas)

## Gambaran Sistem

Sistem Big Data Ketahanan Pangan Lampung adalah platform analitik komprehensif yang dirancang untuk menganalisis kondisi ketahanan pangan di Provinsi Lampung, Indonesia. Sistem ini memproses multiple sumber data untuk memberikan insight bagi pengambilan kebijakan dan perencanaan ketahanan pangan.

### Tujuan Utama
- Menganalisis pola produksi, konsumsi, dan harga pangan
- Memantau dampak iklim terhadap produktivitas pertanian
- Menilai faktor sosial ekonomi yang mempengaruhi ketahanan pangan
- Menyediakan dashboard real-time untuk pengambil keputusan
- Memungkinkan analitik prediktif untuk perencanaan ketahanan pangan

### Karakteristik Sistem
- **Volume Data**: Memproses jutaan record dari multiple sumber
- **Variasi Data**: Data terstruktur dari lembaga pemerintah (BPS, BMKG)
- **Kecepatan Data**: Batch processing dengan update harian/mingguan
- **Skalabilitas**: Horizontally scalable menggunakan ekosistem Hadoop
- **Reliabilitas**: Fault-tolerant dengan validasi data dan quality checks

## Prinsip Arsitektur

### 1. Arsitektur Medallion (Bronze-Silver-Gold)
- **Layer Bronze**: Ingesti dan penyimpanan data mentah
- **Layer Silver**: Data yang dibersihkan, divalidasi, dan distandarisasi
- **Layer Gold**: Analitik business-ready dan metrik yang diagregasi

### 2. Separation of Concerns
- **Ingesti Data**: Terisolasi dari logic pemrosesan
- **Pemrosesan Data**: Operasi ETL dalam layer khusus
- **Penyajian Data**: Layer analitik dan visualisasi
- **Orkestrasi**: Manajemen workflow terpisah dari business logic

### 3. Skalabilitas dan Performa
- **Horizontal Scaling**: Pemrosesan terdistribusi dengan Spark
- **Partitioning**: Data dipartisi berdasarkan tahun untuk query yang efisien
- **Caching**: Strategic caching untuk data yang sering diakses
- **Parallel Processing**: Concurrent ETL jobs jika memungkinkan

### 4. Kualitas Data dan Governance
- **Validasi Schema**: Diberlakukan di setiap layer
- **Data Lineage**: Transformasi data yang dapat dilacak
- **Metrik Kualitas**: Automated data quality scoring
- **Error Handling**: Graceful failure dan retry mechanisms

## Stack Teknologi

### Platform Big Data Inti
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Apache Spark  │  │ Apache Hadoop   │  │  Apache Hive    │
│   (Processing)  │  │     (Storage)   │  │   (Querying)    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Orkestrasi dan Workflow
```
┌─────────────────┐  ┌─────────────────┐
│ Apache Airflow  │  │    Docker       │
│ (Orchestration) │  │ (Containerization)│
└─────────────────┘  └─────────────────┘
```

### Analitik dan Visualisasi
```
┌─────────────────┐  ┌─────────────────┐
│Apache Superset  │  │    Python       │
│(Visualization)  │  │   (Analytics)   │
└─────────────────┘  └─────────────────┘
```

### Detail Teknologi

#### Penyimpanan Data
- **HDFS**: Distributed file system untuk data mentah dan olahan
- **Parquet**: Format penyimpanan kolumnar untuk analitik yang dioptimasi
- **Hive Metastore**: Manajemen schema dan metadata catalog

#### Pemrosesan Data
- **Apache Spark**: Distributed data processing engine
- **PySpark**: Python API untuk pengembangan Spark
- **Spark SQL**: Interface SQL untuk transformasi data

#### Orkestrasi
- **Apache Airflow**: Orkestrasi workflow dan penjadwalan
- **Docker Compose**: Orkestrasi service dan deployment

#### Analitik
- **Apache Superset**: Business intelligence dan visualisasi
- **Hive**: Interface querying seperti SQL
- **Python**: Analisis data dan machine learning

## Arsitektur Medallion

### Layer Bronze (Data Mentah)
```
HDFS: /data/bronze/
├── produksi_pangan.csv      # Data produksi
├── harga_pangan.csv         # Data harga
├── cuaca.csv                # Data cuaca
├── sosial_ekonomi.csv       # Data sosial ekonomi
├── konsumsi_pangan.csv      # Data konsumsi
└── ikp.csv                  # Data Indeks Ketahanan Pangan
```

**Karakteristik:**
- File CSV mentah seperti yang diingesti dari sistem sumber
- Tidak ada validasi schema atau transformasi data
- Preservasi data historis
- Immutable setelah ditulis

### Layer Silver (Data Bersih)
```
HDFS: /data/silver/
├── produksi_pangan/         # Dipartisi berdasarkan tahun
├── harga_pangan/
├── cuaca/
├── sosial_ekonomi/
├── konsumsi_pangan/
└── ikp/
```

**Karakteristik:**
- Format Parquet untuk penyimpanan dan querying yang efisien
- Validasi kualitas data dan cleansing diterapkan
- Schema standar di semua dataset
- Dipartisi berdasarkan tahun untuk performa
- Hive external tables untuk akses SQL

### Layer Gold (Siap Analitik)
```
HDFS: /data/gold/
├── ketahanan_pangan_kab/        # Metrik ketahanan pangan regional
├── ketahanan_pangan_enriched/   # Tabel analitik komprehensif
├── trend_produksi/              # Analisis tren produksi
└── indikator_agregat/           # Indikator teragregasi
```

**Karakteristik:**
- Metrik business dan KPI
- Data teragregasi dan diperkaya
- Dioptimasi untuk konsumsi dashboard
- Analitik yang dihitung sebelumnya untuk performa

## Arsitektur Komponen

### Layer Ingesti Data
```
┌─────────────────────────────────────────────────────────────┐
│                     Sumber Data                            │
├─────────────────────────────────────────────────────────────┤
│  Data BPS  │ Data BMKG  │ Data Regional  │  External APIs  │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  Script Ingesti                           │
├─────────────────────────────────────────────────────────────┤
│         Validasi Data & Quality Checks                    │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Layer Bronze                           │
│                  (Penyimpanan HDFS)                       │
└─────────────────────────────────────────────────────────────┘
```

### Layer Pemrosesan Data
```
┌─────────────────────────────────────────────────────────────┐
│                  Apache Spark Cluster                     │
├─────────────────────────────────────────────────────────────┤
│  Spark Master  │  Spark Workers  │  Driver Applications   │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Script ETL                             │
├─────────────────────────────────────────────────────────────┤
│ Data Cleaning │ Validation │ Transformation │ Aggregation │
└─────────────────────────────────────────────────────────────┘
```

### Layer Penyajian Data
```
┌─────────────────────────────────────────────────────────────┐
│                     Hive Metastore                       │
├─────────────────────────────────────────────────────────────┤
│              Manajemen Schema & Metadata                  │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    HiveServer2                            │
├─────────────────────────────────────────────────────────────┤
│               Interface SQL & Query Engine                │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  Apache Superset                         │
├─────────────────────────────────────────────────────────────┤
│           Dashboards & Visualisasi                        │
└─────────────────────────────────────────────────────────────┘
```

## Alur Data

### Pipeline Data End-to-End
```
[Sumber Data] → [Layer Bronze] → [Layer Silver] → [Layer Gold] → [Analitik]
```

### Diagram Alur Detail
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Data CSV   │────▶│    HDFS     │────▶│   Spark     │────▶│   Parquet   │
│  (Sumber)   │    │  (Bronze)   │    │  (ETL Jobs) │    │  (Silver)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │
                                                                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Superset    │◀───│    Hive     │◀───│   Spark     │◀───│   Silver    │
│(Dashboard)  │    │ (Metadata)  │    │(Analytics)  │    │   Layer     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
                                      ┌─────────────┐
                                      │    Gold     │
                                      │   Layer     │
                                      └─────────────┘
```

### Workflow Pemrosesan
1. **Ingesti Data**: File CSV diupload ke HDFS layer bronze
2. **Validasi Data**: Quality checks dan validasi schema
3. **Pembersihan Data**: Hapus record yang tidak valid, standardisasi format
4. **Transformasi Data**: Terapkan business rules dan kalkulasi
5. **Pengkayaan Data**: Join multiple dataset, hitung metrik turunan
6. **Penyimpanan Data**: Tulis ke layer silver/gold sebagai Parquet
7. **Registrasi Metadata**: Buat/update tabel Hive
8. **Analitik**: Generate metrik business dan KPI
9. **Visualisasi**: Buat dashboard dan laporan

## Pengaturan Infrastruktur

### Arsitektur Container
```
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Network                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │  NameNode  │  │ DataNode1  │  │ DataNode2  │  │   YARN     │    │
│  │    HDFS    │  │    HDFS    │  │    HDFS    │  │ResourceMgr │    │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘    │
│                                                                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │Spark Master│  │Spark Worker│  │Spark Worker│  │ HiveServer2│    │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘    │
│                                                                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                    │
│  │   Airflow  │  │  Superset  │  │Hive Meta   │                    │
│  │ Scheduler  │  │            │  │   store    │                    │
│  └────────────┘  └────────────┘  └────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Dependensi Service
```
Superset ──┐
           ├──▶ HiveServer2 ──▶ Hive Metastore
Airflow ───┘                          │
                                      ▼
Spark ─────────────────────────▶ HDFS Cluster
                                (NameNode + DataNodes)
```

### Alokasi Resource
| Service | CPU | Memory | Storage | Replicas |
|---------|-----|--------|---------|----------|
| NameNode | 1 | 2GB | 50GB | 1 |
| DataNode | 1 | 2GB | 100GB | 2+ |
| Spark Master | 1 | 1GB | 10GB | 1 |
| Spark Worker | 2 | 4GB | 20GB | 2+ |
| HiveServer2 | 2 | 4GB | 20GB | 1 |
| Hive Metastore | 1 | 2GB | 20GB | 1 |
| Airflow | 1 | 2GB | 10GB | 1 |
| Superset | 1 | 2GB | 10GB | 1 |

## Arsitektur Keamanan

### Autentikasi dan Otorisasi
```
┌─────────────────────────────────────────────────────────────┐
│                    Layer Keamanan                         │
├─────────────────────────────────────────────────────────────┤
│  Network Security  │  Application Security  │  Data Security │
├─────────────────────────────────────────────────────────────┤
│   - Docker Network │   - Service Auth      │  - Encryption  │
│   - Port Isolation │   - User Management   │  - Access Control│
│   - Firewall Rules │   - Session Management│  - Data Masking │
└─────────────────────────────────────────────────────────────┘
```

### Proteksi Data
- **Encryption at Rest**: Data sensitif dienkripsi di HDFS
- **Encryption in Transit**: TLS untuk komunikasi antar service
- **Access Control**: Permission berbasis role di Hive
- **Data Lineage**: Lacak akses dan modifikasi data
- **Audit Logging**: Audit trail yang komprehensif

## Pertimbangan Performa

### Strategi Optimasi
1. **Partitioning**: Data dipartisi berdasarkan tahun untuk query yang efisien
2. **Columnar Storage**: Format Parquet untuk workload analitik
3. **Compression**: Kompresi LZ4/Snappy untuk efisiensi storage
4. **Indexing**: Strategic indexing di Hive untuk performa query
5. **Caching**: Spark caching untuk analitik iteratif
6. **Resource Management**: YARN untuk alokasi resource yang optimal

### Tuning Performa
```
Konfigurasi Spark:
├── spark.sql.adaptive.enabled = true
├── spark.sql.adaptive.coalescePartitions.enabled = true
├── spark.sql.adaptive.skewJoin.enabled = true
├── spark.serializer = KryoSerializer
└── spark.sql.execution.arrow.pyspark.enabled = true

Konfigurasi HDFS:
├── dfs.blocksize = 128MB
├── dfs.replication = 2
└── dfs.namenode.handler.count = 20

Konfigurasi Hive:
├── hive.exec.dynamic.partition = true
├── hive.exec.compress.output = true
└── hive.optimize.ppd = true
```

### Performa Query
- **Partition Pruning**: Query otomatis filter berdasarkan partisi tahun
- **Predicate Pushdown**: Kondisi filter didorong ke storage layer
- **Vectorized Execution**: Eksekusi query yang dioptimasi di Hive
- **Cost-Based Optimization**: Optimasi query plan berdasarkan statistik

## Skalabilitas

### Horizontal Scaling
```
Setup Saat Ini → Setup Skala Besar

HDFS Cluster:           HDFS Cluster:
├── 1 NameNode         ├── 1 NameNode (HA)
└── 2 DataNodes        └── 4+ DataNodes

Spark Cluster:          Spark Cluster:
├── 1 Master           ├── 1 Master (HA)
└── 2 Workers          └── 4+ Workers
```

### Strategi Auto-Scaling
1. **Container Orchestration**: Kubernetes untuk dynamic scaling
2. **Resource Monitoring**: Automatic scaling berdasarkan penggunaan CPU/Memory
3. **Queue Management**: YARN queues untuk isolasi workload
4. **Storage Scaling**: Tambah DataNodes berdasarkan utilisasi storage

### Perencanaan Kapasitas
| Volume Data | HDFS Nodes | Spark Workers | Waktu Pemrosesan |
|-------------|------------|---------------|------------------|
| 1-10 GB | 2 DataNodes | 2 Workers | 10-30 menit |
| 10-100 GB | 3-4 DataNodes | 3-4 Workers | 30-60 menit |
| 100GB-1TB | 5+ DataNodes | 5+ Workers | 1-3 jam |

## Monitoring dan Observabilitas

### Stack Monitoring
```
┌─────────────────────────────────────────────────────────────┐
│                    Layer Monitoring                       │
├─────────────────────────────────────────────────────────────┤
│  Application Logs  │  System Metrics  │  Business Metrics  │
├─────────────────────────────────────────────────────────────┤
│   - Spark Logs     │   - CPU/Memory   │  - Data Quality    │
│   - Airflow Logs   │   - Disk Usage   │  - Pipeline SLA    │
│   - Hive Logs      │   - Network I/O  │  - Processing Time │
└─────────────────────────────────────────────────────────────┘
```

### Metrik Utama
1. **Metrik Infrastruktur**
   - Utilisasi dan kesehatan HDFS
   - Waktu eksekusi Spark job dan success rate
   - Utilisasi resource (CPU, Memory, Disk)

2. **Metrik Kualitas Data**
   - Skor kelengkapan data
   - Success rate validasi schema
   - Rate deteksi outlier

3. **Metrik Business**
   - Kepatuhan SLA pipeline
   - Metrik kesegaran data
   - Statistik penggunaan dashboard

### Alerting
- **Critical Alerts**: Kegagalan service, masalah kualitas data
- **Warning Alerts**: Degradasi performa, threshold kapasitas
- **Info Alerts**: Penyelesaian pipeline yang sukses, maintenance windows