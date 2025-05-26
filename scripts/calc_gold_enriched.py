"""
Gold Layer ETL: Enhanced Food Security Analytics Script

This script creates an enriched analytics table by joining all silver layer
data sources to enable comprehensive food security analysis.
"""

import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent))

from pyspark.sql.functions import avg, col, count, lower, regexp_replace
from pyspark.sql.functions import sum as _sum
from pyspark.sql.functions import when

from src.config.settings import HDFS_CONFIG, HIVE_CONFIG
from src.utils.spark_utils import SparkSessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Spark Session
spark_manager = SparkSessionManager("CalculateGoldEnriched")
spark = spark_manager.get_session()

# Read silver tables
logger.info("Reading silver layer data...")
df_produksi = spark.table("silver.produksi_pangan")

# Load tables with error handling instead of existence checks
def safe_load_table(table_name):
    try:
        return spark.table(table_name)
    except Exception as e:
        logger.warning(f"Could not load {table_name}: {e}")
        return None

df_harga = safe_load_table("silver.harga_pangan")
df_cuaca = safe_load_table("silver.cuaca")
df_sosial = safe_load_table("silver.sosial_ekonomi")
df_konsumsi = safe_load_table("silver.konsumsi_pangan")
df_ikp = safe_load_table("silver.ikp")


# Standardize join keys
def std_kabupaten_kota(df, colname):
    return df.withColumn(
        colname, lower(regexp_replace(col(colname), r"[^a-zA-Z0-9\s]", ""))
    )


df_produksi = std_kabupaten_kota(df_produksi, "kabupaten_kota")
if df_harga:
    df_harga = std_kabupaten_kota(df_harga, "kabupaten_kota")
if df_cuaca:
    df_cuaca = std_kabupaten_kota(df_cuaca, "kabupaten_kota")
if df_sosial:
    df_sosial = std_kabupaten_kota(df_sosial, "kabupaten_kota")
if df_konsumsi:
    df_konsumsi = std_kabupaten_kota(df_konsumsi, "kabupaten_kota")
if df_ikp:
    df_ikp = std_kabupaten_kota(
        df_ikp.withColumnRenamed("nama_kabupaten", "kabupaten_kota"), "kabupaten_kota"
    )

# Aggregate silver tables
logger.info("Aggregating and joining data from multiple sources...")
df_prod_agg = df_produksi.groupBy("kabupaten_kota", "tahun").agg(
    _sum("produksi").alias("total_produksi"),
    avg("produktivitas").alias("avg_produktivitas"),
    _sum("luas_panen").alias("total_luas_panen"),
    count("komoditas").alias("jenis_komoditas"),
)

if df_harga:
    df_harga_agg = df_harga.groupBy("kabupaten_kota", "tahun").agg(
        avg("harga").alias("avg_harga")
    )
    df_prod_agg = df_prod_agg.join(df_harga_agg, ["kabupaten_kota", "tahun"], "left")

if df_cuaca:
    df_cuaca_agg = df_cuaca.groupBy("kabupaten_kota", "tahun").agg(
        avg("curah_hujan").alias("avg_curah_hujan"), avg("suhu").alias("avg_suhu")
    )
    df_prod_agg = df_prod_agg.join(df_cuaca_agg, ["kabupaten_kota", "tahun"], "left")

if df_sosial:
    df_prod_agg = df_prod_agg.join(df_sosial, ["kabupaten_kota", "tahun"], "left")

if df_konsumsi:
    df_konsumsi_agg = df_konsumsi.groupBy("kabupaten_kota", "tahun").agg(
        _sum("konsumsi_pangan").alias("total_konsumsi_pangan")
    )
    df_prod_agg = df_prod_agg.join(df_konsumsi_agg, ["kabupaten_kota", "tahun"], "left")

if df_ikp:
    df_ikp_agg = df_ikp.groupBy("kabupaten_kota", "tahun").agg(
        avg("ikp").alias("ikp"),
        avg("peringkat_kab_kota").alias("peringkat_kab_kota"),
        avg("kelompok_ikp").alias("kelompok_ikp"),
    )
    df_prod_agg = df_prod_agg.join(df_ikp_agg, ["kabupaten_kota", "tahun"], "left")

# Derived metrics
df_gold = (
    df_prod_agg.withColumn(
        "produksi_per_kapita", col("total_produksi") / col("jumlah_penduduk")
    )
    .withColumn(
        "skor_ketersediaan",
        when(col("total_produksi") > 50000, 80)
        .when(col("total_produksi") > 20000, 60)
        .otherwise(40),
    )
    .withColumn(
        "kategori_ketahanan",
        when(col("skor_ketersediaan") >= 70, "Tahan")
        .when(col("skor_ketersediaan") >= 50, "Sedang")
        .otherwise("Rentan"),
    )
)

# Write to Gold layer
gold_path = f"{HDFS_CONFIG['base_url']}{HDFS_CONFIG['gold_path']}/ketahanan_pangan_enriched"
logger.info(f"Writing enriched data to gold layer: {gold_path}")
df_gold.write.mode("overwrite").partitionBy("tahun").parquet(gold_path)

# Create Gold Hive table
logger.info("Creating/updating enriched Hive table...")
spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS gold.ketahanan_pangan_enriched (
        kabupaten_kota STRING,
        total_produksi DOUBLE,
        avg_produktivitas DOUBLE,
        total_luas_panen DOUBLE,
        jenis_komoditas LONG,
        avg_harga DOUBLE,
        avg_curah_hujan DOUBLE,
        avg_suhu DOUBLE,
        jumlah_penduduk DOUBLE,
        persentase_miskin DOUBLE,
        pengeluaran_per_kapita DOUBLE,
        total_konsumsi_pangan DOUBLE,
        ikp DOUBLE,
        peringkat_kab_kota DOUBLE,
        kelompok_ikp DOUBLE,
        produksi_per_kapita DOUBLE,
        skor_ketersediaan DOUBLE,
        kategori_ketahanan STRING
    )
    PARTITIONED BY (tahun INT)
    STORED AS PARQUET
    LOCATION '{gold_path}'
"""
)
spark.sql("MSCK REPAIR TABLE gold.ketahanan_pangan_enriched")
logger.info("Enhanced food security analytics calculation completed successfully!")

spark_manager.stop()
