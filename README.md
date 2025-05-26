# Sistem Big Data Ketahanan Pangan Lampung

Proyek ini adalah sistem analitik big data untuk analisis ketahanan pangan di Provinsi Lampung, Indonesia, menggunakan ekosistem Hadoop dan arsitektur Medallion (Bronze-Silver-Gold).

## 📋 Daftar Isi

- [Gambaran Sistem](#gambaran-sistem)
- [Arsitektur Sistem](#arsitektur-sistem)
- [Teknologi yang Digunakan](#teknologi-yang-digunakan)
- [Panduan Memulai](#panduan-memulai)
- [Arsitektur Data](#arsitektur-data)
- [Kualitas Data dan Standar Engineering](#kualitas-data-dan-standar-engineering)
- [Otomatisasi Pipeline](#otomatisasi-pipeline)
- [Orkestrasi dengan Airflow](#orkestrasi-dengan-airflow)
- [Visualisasi dengan Superset](#visualisasi-dengan-superset)
- [Lingkungan Pengembangan](#lingkungan-pengembangan)
- [Pemecahan Masalah](#pemecahan-masalah)
- [Kontribusi](#kontribusi)

## 🎯 Gambaran Sistem

### Tujuan Proyek
Sistem ini dikembangkan untuk menganalisis kondisi ketahanan pangan di Provinsi Lampung dengan memanfaatkan teknologi big data untuk memberikan wawasan yang dapat digunakan dalam pengambilan kebijakan dan perencanaan ketahanan pangan.

### Objektif Utama
- ✅ Menganalisis pola produksi, konsumsi, dan harga pangan
- ✅ Memantau dampak iklim terhadap produktivitas pertanian
- ✅ Menilai faktor sosial ekonomi yang mempengaruhi ketahanan pangan
- ✅ Menyediakan dashboard real-time untuk pengambil keputusan
- ✅ Memungkinkan analitik prediktif untuk perencanaan ketahanan pangan

### Karakteristik Sistem
- **Volume Data**: Memproses jutaan record dari berbagai sumber
- **Variasi Data**: Data terstruktur dari instansi pemerintah (BPS, BMKG)
- **Kecepatan Data**: Pemrosesan batch dengan update harian/mingguan
- **Skalabilitas**: Dapat diskalakan secara horizontal menggunakan ekosistem Hadoop
- **Reliabilitas**: Fault-tolerant dengan validasi data dan pemeriksaan kualitas

## 🏗️ Arsitektur Sistem

### Arsitektur Medallion (Bronze-Silver-Gold)
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Data Mentah │────▶│ Bronze Layer│────▶│Silver Layer │────▶│ Gold Layer  │
│ (CSV Files) │    │ (HDFS Raw)  │    │(Data Bersih)│    │(Analitik)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

- **Bronze Layer**: Data mentah dalam HDFS - data asli dari sumber tanpa transformasi
- **Silver Layer**: Data yang telah dibersihkan dan divalidasi menggunakan Spark
- **Gold Layer**: Data siap analitik dengan metrik bisnis dan indikator
- **Hive**: Query interface SQL-like dan manajemen skema
- **Superset**: Visualisasi dan dashboard

### Diagram Arsitektur Sistem

![Diagram Arsitektur](docs/ARCHITECTURE_DIAGRAM.md)

Arsitektur pipeline big data komprehensif yang menunjukkan alur data dari sumber eksternal melalui lapisan medallion (Bronze-Silver-Gold), komponen infrastruktur, orkestrasi, dan visualisasi analitik.

*Arsitektur ini mendemonstrasikan sistem big data production-ready menggunakan komponen ekosistem Hadoop, pipeline ETL otomatis, manajemen kualitas data, dan kemampuan business intelligence untuk analisis ketahanan pangan di Provinsi Lampung.*

## 🛠️ Teknologi yang Digunakan

### Platform Big Data Inti
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Apache Spark  │  │ Apache Hadoop   │  │  Apache Hive    │
│   (Pemrosesan)  │  │    (Storage)    │  │   (Querying)    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Orkestrasi dan Workflow
```
┌─────────────────┐  ┌─────────────────┐
│ Apache Airflow  │  │     Docker      │
│ (Orkestrasi)    │  │(Containerisasi) │
└─────────────────┘  └─────────────────┘
```

### Analitik dan Visualisasi
```
┌─────────────────┐  ┌─────────────────┐
│Apache Superset  │  │     Python      │
│ (Visualisasi)   │  │   (Analitik)    │
└─────────────────┘  └─────────────────┘
```

### Detail Teknologi

#### Penyimpanan Data
- **HDFS**: Sistem file terdistribusi untuk data mentah dan terproses
- **Parquet**: Format penyimpanan columnar untuk analitik yang dioptimalkan
- **Hive Metastore**: Manajemen skema dan katalog metadata

#### Pemrosesan Data
- **Apache Spark**: Engine pemrosesan data terdistribusi
- **PySpark**: Python API untuk pengembangan Spark
- **Spark SQL**: Interface SQL untuk transformasi data

#### Orkestrasi
- **Apache Airflow**: Orkestrasi workflow dan penjadwalan
- **Docker Compose**: Orkestrasi service dan deployment

#### Analitik
- **Apache Superset**: Business intelligence dan visualisasi
- **Hive**: Interface query SQL-like
- **Python**: Analisis data dan machine learning

## 🚀 Panduan Memulai

### 1. Setup Lingkungan Pengembangan
```bash
# Setup lingkungan pengembangan (Python, dependencies, tools)
./setup_dev_env.sh

# Aktifkan virtual environment
source .venv/bin/activate
```

### 2. Memulai Sistem Big Data
```bash
# Jalankan semua container Hadoop, Spark, Hive, Airflow, dan Superset
./start-system.sh

# Tunggu hingga semua service healthy
docker compose ps
```

### 3. Proses Data Real
```bash
# Script bronze secara otomatis menyalin dataset dan ingest ke HDFS
bash run_bronze.sh
```
Script ini secara otomatis menyalin data real dari folder `datasets/` ke `data/bronze/` dan ingest ke HDFS.

### 4. Jalankan Pipeline Otomatis
```bash
# Opsi A: Gunakan script otomatisasi (direkomendasikan)
bash run_bronze.sh   # Ingest data ke HDFS
bash run_silver.sh   # Bersihkan dan transformasi data
bash run_gold.sh     # Hitung metrik bisnis

# Opsi B: Manual step-by-step (untuk pembelajaran)
```

### 5. Langkah Manual Pipeline (Alternatif)

**Ingest data ke HDFS (Bronze Layer):**
```bash
docker compose exec namenode hdfs dfs -mkdir -p /data/bronze
docker compose exec namenode hdfs dfs -put -f /data/bronze/produksi_pangan.csv /data/bronze/
docker compose exec namenode hdfs dfs -put -f /data/bronze/harga_pangan.csv /data/bronze/
docker compose exec namenode hdfs dfs -put -f /data/bronze/cuaca.csv /data/bronze/
docker compose exec namenode hdfs dfs -put -f /data/bronze/sosial_ekonomi.csv /data/bronze/
docker compose exec namenode hdfs dfs -put -f /data/bronze/konsumsi_pangan.csv /data/bronze/
docker compose exec namenode hdfs dfs -put -f /data/bronze/ikp.csv /data/bronze/
docker compose exec namenode hdfs dfs -ls /data/bronze
```
Anda akan melihat file CSV terdaftar di HDFS.

**Jalankan job Spark ke Silver Layer:**
```bash
docker compose exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "CREATE DATABASE IF NOT EXISTS silver;"
docker compose exec spark-master /spark/bin/spark-submit --master spark://spark-master:7077 /scripts/clean_produksi.py
docker compose exec spark-master /spark/bin/spark-submit --master spark://spark-master:7077 /scripts/clean_harga.py
docker compose exec spark-master /spark/bin/spark-submit --master spark://spark-master:7077 /scripts/clean_cuaca.py
docker compose exec spark-master /spark/bin/spark-submit --master spark://spark-master:7077 /scripts/clean_sosial_ekonomi.py
docker compose exec spark-master /spark/bin/spark-submit --master spark://spark-master:7077 /scripts/clean_konsumsi.py
docker compose exec spark-master /spark/bin/spark-submit --master spark://spark-master:7077 /scripts/clean_ikp.py
```
Ini akan membersihkan dan mentransformasi data, menulis file Parquet ke HDFS `/data/silver/` dan membuat tabel Hive di database `silver`.

**Validasi Data Silver di Hive:**
```bash
docker compose exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SHOW TABLES IN silver;"
docker compose exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SELECT COUNT(*) FROM silver.produksi_pangan;"
docker compose exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SELECT COUNT(*) FROM silver.harga_pangan;"
docker compose exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SELECT COUNT(*) FROM silver.cuaca;"
```
Anda akan melihat jumlah baris untuk setiap tabel.

**Jalankan job Spark ke Gold Layer:**
```bash
docker compose exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "CREATE DATABASE IF NOT EXISTS gold;"
docker compose exec spark-master /spark/bin/spark-submit --master spark://spark-master:7077 /scripts/calc_indikator.py
docker compose exec spark-master /spark/bin/spark-submit --master spark://spark-master:7077 /scripts/calc_gold_enriched.py
```
Ini akan menghitung metrik dan indikator bisnis, menulis ke `/data/gold/` dan membuat tabel Hive di database `gold`.

**Validasi Data Gold di Hive:**
```bash
docker compose exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SHOW TABLES IN gold;"
docker compose exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SELECT * FROM gold.ketahanan_pangan_kab LIMIT 10;"
docker compose exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SELECT * FROM gold.ketahanan_pangan_enriched LIMIT 10;"
```
Anda akan melihat tabel gold layer dan data real.

### 6. Orkestrasi dan Visualisasi

**(Opsional) Orkestrasi dengan Airflow:**
- Akses Airflow di [http://localhost:8085](http://localhost:8085) (admin/admin)
- Trigger DAG untuk pipeline lengkap jika tersedia (lihat direktori `dags/`).

## 📊 Arsitektur Data

### Bronze Layer (Data Mentah)
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
- File CSV mentah seperti yang diingest dari sistem sumber
- Tanpa validasi skema atau transformasi data
- Preservasi data historis
- Immutable setelah ditulis

### Silver Layer (Data Bersih)
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
- Format Parquet untuk penyimpanan dan query yang efisien
- Validasi dan pembersihan kualitas data diterapkan
- Skema standar di semua dataset
- Dipartisi berdasarkan tahun untuk performa
- Tabel eksternal Hive untuk akses SQL

### Gold Layer (Siap Analitik)
```
HDFS: /data/gold/
├── ketahanan_pangan_kab/        # Metrik ketahanan pangan regional
├── ketahanan_pangan_enriched/   # Tabel analitik komprehensif
├── trend_produksi/              # Analisis trend produksi
└── indikator_agregat/           # Indikator teragregasi
```

**Karakteristik:**
- Metrik bisnis dan KPI
- Data teragregasi dan diperkaya
- Dioptimalkan untuk konsumsi dashboard
- Analitik pre-calculated untuk performa

## 🔍 Kualitas Data dan Standar Engineering

### Metodologi Pembersihan Data

Semua script pembersihan data mengikuti metodologi **Pembersihan dan Standardisasi Data yang Robust**, diimplementasikan melalui modul `src/utils/data_quality.py` yang baru:

1. **Validasi Kualitas Otomatis**
   - Validasi skema terhadap struktur yang diharapkan
   - Pemeriksaan kelengkapan, keunikan, validitas, dan konsistensi
   - Deteksi outlier menggunakan metode IQR dan Z-score
   - Profiling data komprehensif dan penilaian kualitas

2. **Pemrosesan Data Standar**
   - Drop atau isi nilai yang hilang berdasarkan aturan bisnis
   - Standardisasi format numerik (mis. `125,89` → `125.89`)
   - Partisi berdasarkan tahun untuk performa query optimal
   - Tangani outlier dan nilai khusus (`8888`, `#N/A`, dll.)
   - Penamaan kolom snake_case yang konsisten

3. **Konfigurasi Terpusat**
   - Skema data didefinisikan di `src/config/settings.py`
   - Threshold kualitas dan aturan validasi terpusat
   - Fungsi validasi yang dapat digunakan kembali di semua script ETL

4. **Error Handling dan Logging**
   - Logging komprehensif di setiap langkah pemrosesan
   - Error handling yang graceful dengan pesan error yang detail
   - Laporan kualitas data dengan insight yang actionable

Metodologi ini diimplementasikan di semua script ETL menggunakan utilities bersama dari `src/utils/`, memastikan konsistensi dan maintainability di seluruh pipeline.

## ⚡ Otomatisasi Pipeline

Untuk mengotomatisasi setiap layer dari pipeline medallion, gunakan script yang disediakan:

### Script Bronze Layer
```bash
bash run_bronze.sh
```
Ingest semua CSV dari `data/bronze/` ke HDFS `/data/bronze/`. Membuat direktori HDFS jika diperlukan, upload semua CSV, dan list file di HDFS. Aman untuk dijalankan berulang.

### Script Silver Layer
```bash
bash run_silver.sh
```
Memastikan database Hive `silver` ada, menjalankan job Spark untuk membersihkan dan mentransformasi data (semua script `clean_*.py`), dan list tabel Hive yang dihasilkan. Aman untuk dijalankan berulang.

### Script Gold Layer
```bash
bash run_gold.sh
```
Memastikan database Hive `gold` ada, menjalankan job Spark untuk menghitung metrik bisnis (`calc_indikator.py` dan `calc_gold_enriched.py`), dan list tabel Hive yang dihasilkan. Aman untuk dijalankan berulang.

**Best practice:** Jalankan script ini secara berurutan setelah menyalin data real dan menjalankan sistem. Ini memastikan setiap layer dibangun di atas layer sebelumnya dan pipeline dapat direproduksi.

Anda juga dapat mengintegrasikan script ini ke dalam Airflow atau orchestrator lain untuk otomatisasi penuh.

## 🔄 Orkestrasi dengan Airflow

Proyek ini menggunakan Apache Airflow untuk mengorkestrasi pipeline data medallion. DAG Airflow (`dags/lampung_foodsec_dag.py`) mengotomatisasi tahapan berikut:

- Ingest Bronze Layer (`run_bronze.sh`)
- ETL Silver Layer (`run_silver.sh`)
- Kalkulasi metrik Gold Layer (`run_gold.sh`)
- Validasi tabel Gold di Hive

Untuk menggunakan Airflow untuk orkestrasi pipeline:
- Pastikan semua service berjalan (`./start-system.sh`).
- Akses UI Airflow di [http://localhost:8085](http://localhost:8085) (admin/admin).
- DAG `lampung_foodsec_dag` akan muncul otomatis jika ada di direktori `dags/`.
- Trigger DAG secara manual atau jadwalkan sesuai kebutuhan. Monitor status task dan log melalui UI Airflow.
- Setiap task sesuai dengan tahap pipeline dan menjalankan script atau command validasi terkait.

Airflow menyediakan monitoring terpusat, logging, dan kemampuan retry untuk pipeline medallion lengkap.

## 📈 Visualisasi dengan Superset

### Akses Superset
- Akses Superset di [http://localhost:8088](http://localhost:8088)
- Login: `admin` / `admin123`

### Setup Database Hive
- **Tambahkan Hive sebagai database:**
  - Pergi ke Data > Databases > + Database
  - SQLAlchemy URI: `hive://hive@hiveserver2:10000/gold`
  - Test koneksi dan simpan.

### Setup Dataset
- **Tambahkan tabel `gold.ketahanan_pangan_kab` sebagai dataset:**
  - Pergi ke Data > Datasets > + Dataset
  - Pilih database Hive dan pilih tabel gold.
- **Tambahkan tabel `gold.ketahanan_pangan_enriched` sebagai dataset:**
  - Dataset analitik komprehensif yang menggabungkan semua data silver layer
- **Mark `tahun` sebagai kolom temporal:**
  - Edit dataset, pergi ke Columns, dan set `tahun` sebagai temporal untuk chart berbasis waktu.

### Membuat Chart dan Dashboard
- **Buat chart dan dashboard:**
  - Gunakan tombol Explore untuk membuat visualisasi dan tambahkan ke dashboard.

## 💻 Lingkungan Pengembangan

### Setup Lingkungan Python
- Gunakan `.venv` yang dikelola oleh [uv](https://github.com/astral-sh/uv)
- Jalankan `./setup_dev_env.sh` untuk setup lingkungan pengembangan lengkap
- Install dependencies dengan `uv pip install <package>`
- Aktifkan environment: `source .venv/bin/activate`

### Struktur Proyek
```
src/
├── config/          # Manajemen konfigurasi
│   ├── settings.py  # Konfigurasi terpusat
│   └── __init__.py
├── utils/           # Utilities umum
│   ├── spark_utils.py      # Manajemen sesi Spark
│   ├── data_quality.py     # Fungsi validasi data
│   └── __init__.py
├── etl/            # Kode pipeline ETL
│   ├── silver/     # Script layer silver
│   ├── gold/       # Script layer gold
│   └── __init__.py
└── __init__.py

scripts/            # Script operasi dan deployment
dags/              # DAG Airflow
docs/              # Dokumentasi
tests/             # Unit dan integration test
```

### Kualitas Kode & Type Checking
- **Type Checking**: Menggunakan pyright dengan konfigurasi yang dioptimalkan untuk pengembangan big data
- **Code Formatting**: Black, isort untuk gaya kode yang konsisten
- **Linting**: Flake8 untuk pemeriksaan kualitas kode
- **Tools Kualitas Kode**: Formatting dan type checking otomatis

Jalankan pemeriksaan kualitas:
```bash
# Type checking (dikonfigurasi untuk bekerja dengan PySpark/Airflow)
pyright

# Format kode
./scripts/format_code.sh

# Jalankan test
./scripts/run_tests.sh
```

### Manajemen Konfigurasi
Semua konfigurasi terpusat di `src/config/settings.py`:
- Pengaturan koneksi Spark, HDFS, dan Hive
- Skema data dan threshold kualitas
- Konfigurasi pipeline dan logging

Ini menggantikan nilai hardcode di seluruh codebase dan membuat sistem lebih maintainable.

## 📋 Tabel Gold Layer

Pipeline sekarang menghasilkan dua tabel gold-layer:

- **gold.ketahanan_pangan_kab**: Tabel gold asli, fokus pada produksi dan metrik ketahanan pangan dasar.
- **gold.ketahanan_pangan_enriched**: Tabel analitik terintegrasi penuh yang baru. Tabel ini menggabungkan semua data silver-layer (produksi, harga, cuaca, sosial ekonomi, konsumsi, dan IKP) untuk setiap region dan tahun. Memungkinkan analitik multi-dimensi yang lebih kaya dan dashboarding di Hive dan Superset.

Kedua tabel dibuat otomatis oleh pipeline dan tersedia untuk query dan visualisasi.

## 🔧 Troubleshooting

### Masalah Big Data Stack
- **Superset 'fatal error':** Coba tambahkan dataset atau jalankan query; koneksi mungkin masih valid.
- **'Datetime column not provided':** Edit dataset dan mark kolom (mis. `tahun`) sebagai temporal.
- **Superset gagal start:** Periksa volume `superset_data` dan reset jika diperlukan.
- **Job Spark gagal dengan 'Database not found':** Pastikan database ada di Hive sebelum menjalankan job Spark.
- **Spark tidak melihat tabel Hive:** Pastikan `hive-site.xml` dimount ke `/spark/conf/hive-site.xml` di semua container Spark dan direktori ada.
- **Masalah HDFS:** Periksa kesehatan datanode/namenode dan permissions. Gunakan `docker compose logs` untuk debugging.

### Masalah Lingkungan Pengembangan
- **Error type checking:** Konfigurasi di `pyrightconfig.json` dioptimalkan untuk pengembangan big data. Warning import PySpark/Airflow diharapkan dan disuppress.
- **Masalah virtual environment:** Hapus `.venv` dan jalankan ulang `./setup_dev_env.sh`
- **Error import di IDE:** Pastikan IDE menggunakan interpreter `.venv/bin/python` dan `src/` ada di Python path.

### Validasi Pipeline
- Setelah setiap langkah, gunakan query Hive untuk check jumlah baris dan data real.
- Check direktori HDFS dengan `docker compose exec namenode hdfs dfs -ls /data/silver` dan `/data/gold`.
- Gunakan log Airflow dan SQL Lab Superset untuk validasi lebih lanjut.

### Troubleshooting Umum
- **Schema mismatch errors:** Jika mendapat "Column cannot be converted, Expected: double, Found: BINARY", bersihkan data silver dan jalankan ulang dengan explicit type casting
- **'Datetime column not provided':** Edit dataset dan mark kolom (contoh: `tahun`) sebagai temporal
- **Superset 'fatal error':** Coba tambah dataset atau jalankan SQL Lab query; koneksi mungkin masih valid
- **Development Issues:** Lihat `docs/TYPE_CHECKING.md` dan `docs/DEVELOPMENT.md` untuk panduan detail

## 🤝 Kontribusi

### Panduan Gaya Kode
- **Python**: snake_case untuk variables/functions, PascalCase untuk classes
- **Imports**: Gunakan isort dan black untuk formatting konsisten
- **Type Hints**: Tambahkan type annotation di mana membantu (dikonfigurasi untuk kompatibilitas PySpark)
- **Dokumentasi**: Docstring komprehensif dan komentar inline
- **Testing**: Tambahkan unit test untuk utilities dan functions baru

### Workflow Pengembangan
1. Buat feature branch dari main
2. Buat perubahan menggunakan struktur proyek yang established
3. Jalankan pemeriksaan kualitas: `./scripts/format_code.sh && ./scripts/type_check.sh`
4. Tambah/update test sesuai kebutuhan: `./scripts/run_tests.sh`
5. Update dokumentasi jika diperlukan
6. Submit pull request dengan commit message yang deskriptif

### Panduan Arsitektur
- Gunakan konfigurasi terpusat dari `src/config/settings.py`
- Manfaatkan utilities bersama dari `src/utils/`
- Ikuti pola arsitektur medallion (Bronze → Silver → Gold)
- Implementasikan proper error handling dan logging
- Pastikan semua script idempotent dan aman untuk dijalankan ulang

## 📊 Tujuan Proyek
- Menganalisis data produksi pangan, harga, iklim, dan sosial ekonomi
- Memberikan insight actionable untuk kebijakan ketahanan pangan
- Mendemonstrasikan pipeline big data modern menggunakan tools open source

## 📞 Data Real Sources
- Dataset real disimpan di folder `datasets/` dan disalin ke `data/bronze/` untuk pemrosesan.
- Dataset tersedia: produksi_pangan.csv, harga_pangan.csv, cuaca.csv, sosial_ekonomi.csv, konsumsi_pangan.csv, ikp.csv
- Sumber data termasuk BPS (Badan Pusat Statistik), BMKG (Badan Meteorologi), dan institusi pemerintah lainnya.
- **Dependencies Python harus dikelola dengan [uv](https://github.com/astral-sh/uv)**. Jangan gunakan pip langsung; selalu gunakan `uv pip install <package>` di dalam root proyek.
- Untuk refresh data di bronze layer:
  1. Update dataset di folder `datasets/`  
  2. Jalankan: `bash run_bronze.sh` (otomatis menyalin dan ingest data)

---

## 👥 Kontributor

Tim mahasiswa Institut Teknologi Sumatera:

- **Galin Nichola Gibran** (121140050)
- **Sesilia Putri Subandi** (122450012)  
- **Cintya Bella** (122450066)
- **Novelia Adinda** (122450104)
- **Dhafin Razaqa Luthfi** (122450133)