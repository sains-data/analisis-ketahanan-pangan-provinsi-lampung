# Sistem Big Data Ketahanan Pangan Lampung

Sistem analitik big data untuk menganalisis ketahanan pangan di Provinsi Lampung menggunakan ekosistem Hadoop dan arsitektur Medallion (Bronze-Silver-Gold).

## 🎯 Gambaran Sistem

**Tujuan:** Menganalisis kondisi ketahanan pangan di Provinsi Lampung untuk mendukung pengambilan kebijakan.

**Fitur Utama:**
- Analisis pola produksi, konsumsi, dan harga pangan
- Monitoring dampak iklim terhadap produktivitas pertanian
- Evaluasi faktor sosial ekonomi
- Dashboard real-time untuk pengambil keputusan
- Analitik prediktif untuk perencanaan

## 🏗️ Arsitektur Sistem

### Arsitektur Medallion
```
Data Mentah → Bronze Layer → Silver Layer → Gold Layer → Dashboard
(CSV Files)   (HDFS Raw)    (Data Bersih)  (Analitik)   (Superset)
```

### Teknologi Stack
- **Storage:** Hadoop HDFS, Parquet
- **Processing:** Apache Spark, PySpark
- **Query:** Apache Hive, Hive SQL
- **Orchestration:** Apache Airflow, Docker
- **Visualization:** Apache Superset
- **Language:** Python 3.9+

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Setup lingkungan pengembangan
./setup_dev_env.sh
source .venv/bin/activate

# Start semua services
./start-system.sh
```

### 2. Jalankan Pipeline
```bash
# Otomatis (Recommended)
bash run_bronze.sh   # Ingest data ke HDFS
bash run_silver.sh   # Bersihkan dan transformasi
bash run_gold.sh     # Hitung metrik bisnis
```

### 3. Akses Dashboard
- **Superset:** http://localhost:8088 (admin/admin123)
- **Airflow:** http://localhost:8085 (admin/admin)
- **Spark UI:** http://localhost:8080

## 📊 Struktur Data

### Bronze Layer (Data Mentah)
```
/data/bronze/
├── produksi_pangan.csv
├── harga_pangan.csv
├── cuaca.csv
├── sosial_ekonomi.csv
├── konsumsi_pangan.csv
└── ikp.csv
```

### Silver Layer (Data Bersih)
- Format Parquet untuk efisiensi
- Validasi dan pembersihan kualitas data
- Partisi berdasarkan tahun
- Tabel Hive untuk akses SQL

### Gold Layer (Siap Analitik)
- **ketahanan_pangan_kab:** Metrik ketahanan regional
- **ketahanan_pangan_enriched:** Data analitik komprehensif
- KPI dan metrik bisnis pre-calculated

## 🔧 Konfigurasi

### Kualitas Data
- Validasi skema otomatis
- Deteksi outlier (IQR, Z-score)
- Pembersihan nilai missing
- Standardisasi format

### Pipeline Management
- Konfigurasi terpusat di `src/config/settings.py`
- Error handling dan logging komprehensif
- Script idempotent dan aman untuk re-run

## 🛠️ Development

### Struktur Proyek
```
src/
├── config/          # Konfigurasi terpusat
├── utils/           # Utilities umum
├── etl/            # Pipeline ETL
└── tests/          # Unit tests

scripts/            # Script operasi
dags/              # Airflow DAGs
datasets/          # Data mentah
```

### Quality Assurance
```bash
# Type checking
pyright

# Format code
./scripts/format_code.sh

# Run tests
./scripts/run_tests.sh
```

## 📈 Monitoring & Troubleshooting

### Health Checks
```bash
# Cek status services
docker compose ps

# Validate data di setiap layer
docker compose exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 \
  -e "SELECT COUNT(*) FROM silver.produksi_pangan;"
```

### Common Issues
- **Superset connection:** Test koneksi dengan `hive://hive@hiveserver2:10000/gold`
- **Spark jobs:** Cek logs dengan `docker compose logs spark-master`
- **HDFS issues:** Validate dengan `hdfs dfs -ls /data`

## 📊 Data Sources

**Real datasets dari:**
- BPS (Badan Pusat Statistik)
- BMKG (Badan Meteorologi & Geofisika)
- PIHPS (Sistem Informasi Harga Pangan)
- Lembaga Pemerintah terkait

## 👥 Team

**Institut Teknologi Sumatera:**
- Galin Nichola Gibran (121140050)
- Sesilia Putri Subandi (122450012)
- Cintya Bella (122450066)
- Novelia Adinda (122450104)
- Dhafin Razaqa Luthfi (122450133)