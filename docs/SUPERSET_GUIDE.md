# Panduan Visualisasi Apache Superset
## Analisis Data Ketahanan Pangan untuk Provinsi Lampung

Panduan ini menyediakan instruksi komprehensif untuk menggunakan Apache Superset dalam menganalisis dan memvisualisasikan data ketahanan pangan dari pipeline Big Data Lampung.

## Daftar Isi
- [Memulai](#memulai)
- [Setup Koneksi Data](#setup-koneksi-data)
- [Dataset yang Tersedia](#dataset-yang-tersedia)
- [Membuat Visualisasi](#membuat-visualisasi)
- [Contoh Analisis Ketahanan Pangan](#contoh-analisis-ketahanan-pangan)
- [Membangun Dashboard](#membangun-dashboard)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Memulai

### Mengakses Superset
1. **Buka Superset**: Navigasikan ke http://localhost:8090
2. **Login**: Gunakan kredensial `admin/admin`
3. **Gambaran Interface**: 
   - **SQL Lab**: Untuk custom queries dan eksplorasi data
   - **Charts**: Membuat visualisasi individual
   - **Dashboards**: Menggabungkan multiple charts
   - **Datasets**: Mengelola sumber data

### Persyaratan Sistem
- Pastikan sistem Big Data berjalan: `./start-system.sh`
- Verifikasi data gold layer tersedia: `bash run_gold.sh`
- Konfirmasi konektivitas Superset ke Hive

## Setup Koneksi Data

### Menambahkan Koneksi Database Hive

1. **Navigasi ke Settings > Database Connections**
2. **Klik "+ Database"**
3. **Konfigurasi Koneksi**:
   ```
   Database Name: Lampung Food Security
   SQLAlchemy URI: hive://hive@hiveserver2:10000/gold
   ```
4. **Test Connection** dan **Save**

### Mendaftarkan Dataset

Setelah terhubung, daftarkan dataset kunci berikut:

1. **Dataset Utama**: `gold.ketahanan_pangan_enriched`
   - **Deskripsi**: Metrik ketahanan pangan komprehensif dengan integrasi multi-sumber
   - **Kunci untuk**: Analitik advanced dan korelasi

2. **Dataset Dasar**: `gold.ketahanan_pangan_kab`
   - **Deskripsi**: Indikator ketahanan pangan dasar berdasarkan kabupaten
   - **Kunci untuk**: Perbandingan sederhana dan tren

## Dataset yang Tersedia

### `gold.ketahanan_pangan_enriched`
**Dataset utama untuk analisis ketahanan pangan komprehensif**

| Kolom | Deskripsi | Tipe | Penggunaan Analisis |
|-------|-----------|------|---------------------|
| `kabupaten_kota` | Nama Kabupaten/Kota | String | Filtering geografis |
| `tahun` | Tahun | Integer | Analisis time series |
| `total_produksi` | Total produksi pangan (ton) | Double | Tren produksi |
| `avg_produktivitas` | Produktivitas rata-rata (ton/ha) | Double | Analisis efisiensi |
| `total_luas_panen` | Total luas panen (ha) | Double | Analisis penggunaan lahan |
| `jenis_komoditas` | Jumlah jenis komoditas | Long | Keragaman tanaman |
| `avg_harga` | Harga pangan rata-rata | Double | Analisis harga |
| `avg_curah_hujan` | Curah hujan rata-rata (mm) | Double | Dampak iklim |
| `avg_suhu` | Suhu rata-rata (°C) | Double | Korelasi cuaca |
| `jumlah_penduduk` | Jumlah penduduk | Double | Kalkulasi per kapita |
| `persentase_miskin` | Persentase kemiskinan | Double | Penilaian kerentanan |
| `pengeluaran_per_kapita` | Pengeluaran per kapita | Double | Analisis ekonomi |
| `total_konsumsi_pangan` | Total konsumsi pangan | Double | Analisis permintaan |
| `ikp` | Indeks Ketahanan Pangan | Double | Scoring keamanan |
| `peringkat_kab_kota` | Peringkat kabupaten | Double | Analisis komparatif |
| `kelompok_ikp` | Grup kategori IKP | Double | Klasifikasi |
| `produksi_per_kapita` | Produksi per kapita | Double | **Metrik kunci** |
| `skor_ketersediaan` | Skor ketersediaan | Double | **Metrik kunci** |
| `kategori_ketahanan` | Kategori keamanan | String | **Klasifikasi kunci** |

## Membuat Visualisasi

### 1. Analisis Geografis

#### **Peta: Ketahanan Pangan berdasarkan Kabupaten**
```sql
-- Query contoh untuk ketahanan pangan tingkat kabupaten
SELECT 
  kabupaten_kota,
  AVG(skor_ketersediaan) as avg_security_score,
  AVG(produksi_per_kapita) as avg_production_per_capita,
  kategori_ketahanan
FROM gold.ketahanan_pangan_enriched 
GROUP BY kabupaten_kota, kategori_ketahanan
ORDER BY avg_security_score DESC
```

**Jenis Chart**: Table atau Big Number
**Kegunaan**: Identifikasi kabupaten paling/kurang aman pangan

#### **Setup Visualisasi Peta**
1. **Jenis Chart**: Pilih "Country Map" atau "Table"
2. **Metrics**: `skor_ketersediaan`, `produksi_per_kapita`
3. **Dimensions**: `kabupaten_kota`
4. **Color By**: `kategori_ketahanan`

### 2. Analisis Time Series

#### **Tren Produksi dari Waktu ke Waktu**
```sql
-- Tren produksi berdasarkan tahun
SELECT 
  tahun,
  SUM(total_produksi) as total_production,
  AVG(avg_produktivitas) as avg_productivity,
  COUNT(DISTINCT kabupaten_kota) as districts_count
FROM gold.ketahanan_pangan_enriched 
GROUP BY tahun
ORDER BY tahun
```

**Jenis Chart**: Line Chart
**X-Axis**: `tahun` (Tahun)
**Y-Axis**: `total_production`, `avg_productivity`

#### **Pola Ketahanan Pangan Musiman**
```sql
-- Tren ketahanan pangan year-over-year
SELECT 
  tahun,
  kategori_ketahanan,
  COUNT(*) as district_count,
  AVG(skor_ketersediaan) as avg_score
FROM gold.ketahanan_pangan_enriched 
GROUP BY tahun, kategori_ketahanan
ORDER BY tahun, kategori_ketahanan
```

**Jenis Chart**: Stacked Bar Chart
**Kegunaan**: Lacak perbaikan/penurunan ketahanan pangan

### 3. Analisis Ekonomi dan Harga

#### **Korelasi Harga vs Produksi**
```sql
-- Hubungan harga dan produksi
SELECT 
  kabupaten_kota,
  AVG(avg_harga) as average_price,
  AVG(total_produksi) as average_production,
  AVG(skor_ketersediaan) as security_score
FROM gold.ketahanan_pangan_enriched 
WHERE avg_harga IS NOT NULL 
  AND total_produksi IS NOT NULL
GROUP BY kabupaten_kota
```

**Jenis Chart**: Scatter Plot
**X-Axis**: `average_price`
**Y-Axis**: `average_production`
**Size**: `security_score`

#### **Dampak Kemiskinan terhadap Ketahanan Pangan**
```sql
-- Korelasi kemiskinan dengan ketidakamanan pangan
SELECT 
  CASE 
    WHEN persentase_miskin < 10 THEN 'Kemiskinan Rendah'
    WHEN persentase_miskin < 20 THEN 'Kemiskinan Sedang'
    ELSE 'Kemiskinan Tinggi'
  END as poverty_level,
  AVG(skor_ketersediaan) as avg_food_security,
  COUNT(*) as district_count
FROM gold.ketahanan_pangan_enriched 
WHERE persentase_miskin IS NOT NULL
GROUP BY 
  CASE 
    WHEN persentase_miskin < 10 THEN 'Kemiskinan Rendah'
    WHEN persentase_miskin < 20 THEN 'Kemiskinan Sedang'
    ELSE 'Kemiskinan Tinggi'
  END
```

**Jenis Chart**: Bar Chart
**Kegunaan**: Menunjukkan hubungan kemiskinan-ketahanan pangan

### 4. Analisis Dampak Iklim

#### **Efek Curah Hujan pada Produksi**
```sql
-- Dampak iklim terhadap produktivitas pertanian
SELECT 
  CASE 
    WHEN avg_curah_hujan < 100 THEN 'Curah Hujan Rendah'
    WHEN avg_curah_hujan < 200 THEN 'Curah Hujan Sedang'
    ELSE 'Curah Hujan Tinggi'
  END as rainfall_category,
  AVG(avg_produktivitas) as avg_productivity,
  AVG(total_produksi) as avg_production,
  COUNT(*) as observations
FROM gold.ketahanan_pangan_enriched 
WHERE avg_curah_hujan IS NOT NULL
GROUP BY 
  CASE 
    WHEN avg_curah_hujan < 100 THEN 'Curah Hujan Rendah'
    WHEN avg_curah_hujan < 200 THEN 'Curah Hujan Sedang'
    ELSE 'Curah Hujan Tinggi'
  END
```

**Jenis Chart**: Box Plot atau Bar Chart
**Kegunaan**: Memahami dampak cuaca terhadap pertanian

#### **Suhu vs Produktivitas**
```sql
-- Korelasi suhu dengan hasil panen
SELECT 
  kabupaten_kota,
  AVG(avg_suhu) as temperature,
  AVG(avg_produktivitas) as productivity,
  AVG(skor_ketersediaan) as food_security
FROM gold.ketahanan_pangan_enriched 
WHERE avg_suhu IS NOT NULL 
  AND avg_produktivitas IS NOT NULL
GROUP BY kabupaten_kota
```

**Jenis Chart**: Scatter Plot
**X-Axis**: `temperature`
**Y-Axis**: `productivity`

### 5. Penilaian Kerentanan

#### **Kabupaten Paling Rentan**
```sql
-- Identifikasi kabupaten yang memerlukan intervensi
SELECT 
  kabupaten_kota,
  AVG(skor_ketersediaan) as avg_security_score,
  AVG(persentase_miskin) as avg_poverty_rate,
  AVG(produksi_per_kapita) as avg_production_per_capita,
  kategori_ketahanan,
  COUNT(*) as years_observed
FROM gold.ketahanan_pangan_enriched 
GROUP BY kabupaten_kota, kategori_ketahanan
HAVING kategori_ketahanan IN ('Rentan', 'Sedang')
ORDER BY avg_security_score ASC
LIMIT 10
```

**Jenis Chart**: Table dengan conditional formatting
**Kegunaan**: Targeting intervensi kebijakan

#### **Distribusi Ketahanan Pangan**
```sql
-- Lanskap ketahanan pangan secara keseluruhan
SELECT 
  kategori_ketahanan,
  COUNT(*) as district_years,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM gold.ketahanan_pangan_enriched 
GROUP BY kategori_ketahanan
```

**Jenis Chart**: Pie Chart
**Kegunaan**: Gambaran umum status keamanan

## Contoh Analisis Ketahanan Pangan

### Metrik Dashboard Eksekutif

#### **Key Performance Indicators (KPIs)**
1. **Total Kabupaten Dipantau**: `COUNT(DISTINCT kabupaten_kota)`
2. **Skor Ketahanan Pangan Rata-rata**: `AVG(skor_ketersediaan)`
3. **Kabupaten Rentan**: `COUNT(*)` WHERE `kategori_ketahanan = 'Rentan'`
4. **Total Produksi Pangan**: `SUM(total_produksi)`
5. **Produksi Per Kapita**: `AVG(produksi_per_kapita)`

#### **Analisis Tren**
- **Perubahan Year-over-Year**: Bandingkan metrik tahun ini vs tahun sebelumnya
- **Pola Musiman**: Analisis bulanan/kuartalan jika data mendukung
- **Perbandingan Regional**: Benchmarking performa kabupaten

#### **Query Sistem Alert**
```sql
-- Kabupaten yang memerlukan perhatian segera
SELECT 
  kabupaten_kota,
  tahun,
  skor_ketersediaan,
  kategori_ketahanan,
  produksi_per_kapita
FROM gold.ketahanan_pangan_enriched 
WHERE kategori_ketahanan = 'Rentan' 
  AND skor_ketersediaan < 50
ORDER BY skor_ketersediaan ASC
```

### Analisis Dampak Kebijakan

#### **Efektivitas Intervensi**
```sql
-- Lacak perbaikan di kabupaten yang ditargetkan
SELECT 
  kabupaten_kota,
  tahun,
  skor_ketersediaan,
  LAG(skor_ketersediaan, 1) OVER (
    PARTITION BY kabupaten_kota 
    ORDER BY tahun
  ) as previous_score,
  skor_ketersediaan - LAG(skor_ketersediaan, 1) OVER (
    PARTITION BY kabupaten_kota 
    ORDER BY tahun
  ) as score_change
FROM gold.ketahanan_pangan_enriched 
ORDER BY kabupaten_kota, tahun
```

#### **Insight Alokasi Resource**
- **Area Dampak Tinggi**: Kabupaten dengan skor rendah tapi potensi perbaikan tinggi
- **Efisiensi Resource**: Area dengan perbaikan skor terbaik per investasi
- **Penilaian Risiko**: Kabupaten dengan tren menurun

## Membangun Dashboard

### Membuat Dashboard Ketahanan Pangan Komprehensif

1. **Struktur Dashboard**:
   ```
   ┌─────────────────────────────────────────────────────────────┐
   │                    KETAHANAN PANGAN LAMPUNG                 │
   │                       DASHBOARD                             │
   ├─────────┬─────────┬─────────┬─────────┬─────────────────────┤
   │   KPI   │   KPI   │   KPI   │   KPI   │     Kotak Alert     │
   │  Total  │  Rata2  │ Kab.    │ Total   │   (Kabupaten        │
   │Kabupaten│Keamanan │ Rentan  │Produksi │   Kritis)           │
   ├─────────┴─────────┴─────────┴─────────┴─────────────────────┤
   │                                                             │
   │              PETA KETAHANAN PANGAN PER KABUPATEN            │
   │                    (Tampilan Geografis)                     │
   │                                                             │
   ├─────────────────────────┬───────────────────────────────────┤
   │     TREN PRODUKSI       │      HARGA vs PRODUKSI            │
   │      (Time Series)      │       (Scatter Plot)              │
   ├─────────────────────────┼───────────────────────────────────┤
   │   DAMPAK IKLIM          │    RANKING KERENTANAN             │
   │   (Bar Chart)           │       (Table)                     │
   └─────────────────────────┴───────────────────────────────────┘
   ```

2. **Filter Dashboard**:
   - **Pemilih Tahun**: Multi-select untuk rentang waktu
   - **Filter Kabupaten**: Pilih wilayah tertentu
   - **Kategori Keamanan**: Filter berdasarkan Tahan/Sedang/Rentan
   - **Filter Kualitas Data**: Eksklusi record yang tidak lengkap

3. **Fitur Interaktif**:
   - **Cross-filtering**: Klik peta untuk update semua chart
   - **Drill-down**: Kabupaten → tingkat Sub-kabupaten (jika data tersedia)
   - **Opsi Export**: Laporan PDF, download data CSV

### Langkah-langkah Pembuatan Dashboard

1. **Buat Chart Individual** (15-20 visualisasi)
2. **Organisir berdasarkan Tema**:
   - **Overview**: KPI dan metrik ringkasan
   - **Geografis**: Peta dan analisis regional
   - **Temporal**: Tren dan time series
   - **Korelasional**: Hubungan dan dampak
3. **Tambah Dashboard**:
   - **Layout**: Drag dan drop charts
   - **Filters**: Tambah filter global
   - **Styling**: Skema warna yang konsisten
4. **Test Interaktivitas**: Pastikan cross-filtering berfungsi
5. **Share Dashboard**: Set permission untuk stakeholder

## Best Practices

### Pertimbangan Kualitas Data
- **Penanganan Missing Data**: Gunakan WHERE clauses untuk eksklusi null
- **Deteksi Outlier**: Identifikasi dan investigasi nilai ekstrem
- **Kesegaran Data**: Monitor keberhasilan pipeline ETL
- **Validasi**: Cross-check agregasi dengan source data

### Optimasi Performa
- **Efisiensi Query**: Gunakan GROUP BY dan WHERE clauses yang tepat
- **Caching**: Aktifkan dashboard caching untuk load time yang lebih cepat
- **Agregasi**: Pre-aggregate metrik yang sering digunakan
- **Indexing**: Pastikan tabel Hive dipartisi dengan benar

### Panduan Visualisasi
- **Konsistensi Warna**: Gunakan warna standar untuk kategori ketahanan pangan
  - 🟢 Hijau: "Tahan" (Aman)
  - 🟡 Kuning: "Sedang" (Moderat)
  - 🔴 Merah: "Rentan" (Vulnerable)
- **Label Jelas**: Selalu sertakan unit dan deskripsi
- **Responsive Design**: Pastikan dashboard berfungsi di berbagai ukuran layar
- **Aksesibilitas**: Gunakan palet yang ramah buta warna

### Keamanan dan Access Control
- **User Roles**: Set permission yang tepat untuk berbagai jenis pengguna
- **Sensitivitas Data**: Perhatikan data regional yang bersifat rahasia
- **Export Controls**: Batasi kemampuan export data sesuai kebutuhan

## Troubleshooting

### Masalah Umum

#### **Masalah Koneksi**
```
Error: "Could not connect to database"
```
**Solusi**: 
1. Verifikasi Hive berjalan: `docker ps | grep hive`
2. Test koneksi: `docker exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000`
3. Periksa format URI: `hive://hive@hiveserver2:10000/gold`

#### **Tidak Ada Data di Charts**
```
Error: "No data available"
```
**Solusi**:
1. Verifikasi data ada: `SELECT COUNT(*) FROM gold.ketahanan_pangan_enriched`
2. Periksa filter: Hapus semua filter dan coba lagi
3. Validasi SQL: Test query di SQL Lab terlebih dahulu

#### **Performa Lambat**
```
Masalah: Charts membutuhkan waktu lama untuk load
```
**Solusi**:
1. Tambahkan WHERE clauses untuk batasi data range
2. Gunakan LIMIT dalam development
3. Periksa eksekusi query Hive di logs
4. Pertimbangkan optimasi partisi data

#### **Error Visualisasi**
```
Error: "Chart failed to render"
```
**Solusi**:
1. Validasi tipe data sesuai persyaratan chart
2. Periksa nilai null di kolom kunci
3. Sederhanakan query untuk identifikasi kolom bermasalah
4. Review log Superset untuk pesan error detail

### Mendapatkan Bantuan
- **Dokumentasi Superset**: https://superset.apache.org/docs/
- **SQL Lab**: Test query sebelum membuat charts
- **Forum Komunitas**: Apache Superset community support
- **Tim Proyek**: Konsultasi dengan tim data engineering untuk masalah pipeline

## Langkah Selanjutnya

### Analitik Advanced
1. **Predictive Modeling**: Gunakan data historis untuk forecast tren ketahanan pangan
2. **Integrasi Machine Learning**: Implementasi model ML untuk prediksi risiko
3. **Real-time Monitoring**: Setup alert untuk threshold kritis
4. **Integrasi Data Eksternal**: Sertakan prakiraan cuaca, harga pasar

### Reporting dan Sharing
1. **Laporan Otomatis**: Jadwal laporan email harian/mingguan
2. **Akses Mobile**: Optimasi dashboard untuk tampilan mobile
3. **Integrasi API**: Hubungkan ke sistem eksternal
4. **Dashboard Publik**: Share insight yang tepat dengan publik

### Capacity Building
1. **Pelatihan Pengguna**: Latih pembuat kebijakan dalam penggunaan dashboard
2. **Dokumentasi**: Pertahankan prosedur analisis yang terupdate
3. **Knowledge Transfer**: Dokumentasi insight analitik dan metodologi
4. **Continuous Improvement**: Update dashboard reguler berdasarkan feedback pengguna

---

**Kontak**: Untuk dukungan teknis Sistem Big Data Ketahanan Pangan Lampung, konsultasi dengan tim proyek atau review [README.md](../README.md) utama untuk panduan administrasi sistem.