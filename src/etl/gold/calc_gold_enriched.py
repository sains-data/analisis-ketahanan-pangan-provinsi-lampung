"""
Gold Layer ETL: Enhanced Food Security Analytics Script

This script creates an enriched analytics table by joining all silver layer
data sources to enable comprehensive food security analysis.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pyspark.sql import DataFrame
from pyspark.sql.functions import avg, col, count, lower, regexp_replace
from pyspark.sql.functions import sum as _sum
from pyspark.sql.functions import when

from config.settings import HDFS_CONFIG
from utils.spark_utils import SparkSessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Spark Session
spark = SparkSessionManager.get_session("CalculateGoldEnriched")

# Read silver tables
logger.info("Reading silver layer data...")
df_produksi = spark.table("silver.produksi_pangan")

# Table dependency configuration
REQUIRED_TABLES = ["silver.produksi_pangan"]  # Tables that must exist
OPTIONAL_TABLES = {
    "silver.harga_pangan": "price data",
    "silver.cuaca": "weather data", 
    "silver.sosial_ekonomi": "socioeconomic data",
    "silver.konsumsi_pangan": "consumption data",
    "silver.ikp": "food security index data"
}

def load_table_with_dependency_check(table_name: str, required: bool = True) -> Optional[DataFrame]:
    """
    Load table with proper dependency checking and error handling
    
    Args:
        table_name: Name of the table to load
        required: Whether this table is required for processing
        
    Returns:
        DataFrame or None: Loaded DataFrame or None if optional and missing
        
    Raises:
        RuntimeError: If required table is missing
    """
    try:
        df = spark.table(table_name)
        row_count = df.count()
        logger.info(f"Successfully loaded {table_name} with {row_count} rows")
        return df
    except Exception as e:
        if required:
            logger.error(f"CRITICAL: Required table {table_name} is missing or inaccessible: {e}")
            raise RuntimeError(f"Pipeline cannot proceed without required table: {table_name}") from e
        else:
            description = OPTIONAL_TABLES.get(table_name, "optional data")
            logger.warning(f"Optional table {table_name} ({description}) is not available: {e}")
            logger.info(f"Pipeline will continue without {description}")
            return None

# Load required tables (fail fast if missing)
logger.info("Loading required silver layer tables...")
df_produksi = load_table_with_dependency_check("silver.produksi_pangan", required=True)
assert df_produksi is not None, "Required produksi_pangan table must not be None"

# Load optional tables (graceful degradation)
logger.info("Loading optional silver layer tables...")
df_harga = load_table_with_dependency_check("silver.harga_pangan", required=False)
df_cuaca = load_table_with_dependency_check("silver.cuaca", required=False)
df_sosial = load_table_with_dependency_check("silver.sosial_ekonomi", required=False)
df_konsumsi = load_table_with_dependency_check("silver.konsumsi_pangan", required=False)
df_ikp = load_table_with_dependency_check("silver.ikp", required=False)

# Log pipeline capabilities based on available data
available_features = ["production metrics"]
if df_harga: available_features.append("price analysis")
if df_cuaca: available_features.append("weather correlations")
if df_sosial: available_features.append("socioeconomic indicators")
if df_konsumsi: available_features.append("consumption patterns")
if df_ikp: available_features.append("food security indexing")

logger.info(f"Pipeline capabilities for this run: {', '.join(available_features)}")


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

# Join with optional datasets, logging what's being included
if df_harga:
    logger.info("Including price data in enriched analysis")
    df_harga_agg = df_harga.groupBy("kabupaten_kota", "tahun").agg(
        avg("harga_produsen").alias("avg_harga_produsen"),
        avg("harga_konsumen").alias("avg_harga_konsumen")
    )
    df_prod_agg = df_prod_agg.join(df_harga_agg, ["kabupaten_kota", "tahun"], "left")
else:
    logger.info("Price analysis will be skipped - no harga_pangan data available")

if df_cuaca:
    logger.info("Including weather data in enriched analysis")
    df_cuaca_agg = df_cuaca.groupBy("kabupaten_kota", "tahun").agg(
        avg("curah_hujan").alias("avg_curah_hujan"), avg("suhu_rata_rata").alias("avg_suhu")
    )
    df_prod_agg = df_prod_agg.join(df_cuaca_agg, ["kabupaten_kota", "tahun"], "left")
else:
    logger.info("Weather correlation analysis will be skipped - no cuaca data available")

if df_sosial:
    logger.info("Including socioeconomic data in enriched analysis")
    df_prod_agg = df_prod_agg.join(df_sosial, ["kabupaten_kota", "tahun"], "left")
else:
    logger.info("Socioeconomic analysis will be skipped - no sosial_ekonomi data available")

if df_konsumsi:
    logger.info("Including consumption data in enriched analysis")
    df_konsumsi_agg = df_konsumsi.groupBy("kabupaten_kota", "tahun").agg(
        _sum("konsumsi_per_kapita").alias("total_konsumsi_per_kapita")
    )
    df_prod_agg = df_prod_agg.join(df_konsumsi_agg, ["kabupaten_kota", "tahun"], "left")
else:
    logger.info("Consumption pattern analysis will be skipped - no konsumsi_pangan data available")

if df_ikp:
    logger.info("Including food security index data in enriched analysis")
    df_ikp_agg = df_ikp.groupBy("kabupaten_kota", "tahun").agg(
        avg("skor_ikp").alias("skor_ikp"),
        avg("kategori_ikp").alias("kategori_ikp"),
    )
    df_prod_agg = df_prod_agg.join(df_ikp_agg, ["kabupaten_kota", "tahun"], "left")
else:
    logger.info("Food security indexing will be skipped - no ikp data available")

# Derived metrics with defensive programming for missing columns
logger.info("Calculating derived metrics...")

df_gold = df_prod_agg

# Only calculate per capita metrics if population data is available
if "jumlah_penduduk" in df_gold.columns:
    logger.info("Calculating per capita production metrics")
    df_gold = df_gold.withColumn(
        "produksi_per_kapita", 
        when(col("jumlah_penduduk") > 0, col("total_produksi") / col("jumlah_penduduk"))
        .otherwise(None)
    )
else:
    logger.warning("Population data not available - per capita metrics will be null")
    df_gold = df_gold.withColumn("produksi_per_kapita", col("total_produksi").cast("double"))

# Calculate availability score based on production
df_gold = df_gold.withColumn(
    "skor_ketersediaan",
    when(col("total_produksi") > 50000, 80)
    .when(col("total_produksi") > 20000, 60)
    .otherwise(40),
).withColumn(
    "kategori_ketahanan",
    when(col("skor_ketersediaan") >= 70, "Tahan")
    .when(col("skor_ketersediaan") >= 50, "Sedang")
    .otherwise("Rentan"),
)

# Log final dataset characteristics
final_row_count = df_gold.count()
final_columns = len(df_gold.columns)
logger.info(f"Enriched dataset prepared with {final_row_count} rows and {final_columns} columns")

# Write to Gold layer
gold_path = f"{HDFS_CONFIG['base_url']}{HDFS_CONFIG['data_paths']['gold']}/ketahanan_pangan_enriched"
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
        avg_harga_produsen DOUBLE,
        avg_harga_konsumen DOUBLE,
        avg_curah_hujan DOUBLE,
        avg_suhu DOUBLE,
        jumlah_penduduk DOUBLE,
        persentase_miskin DOUBLE,
        pengeluaran_per_kapita DOUBLE,
        total_konsumsi_per_kapita DOUBLE,
        skor_ikp DOUBLE,
        kategori_ikp DOUBLE,
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
# Final validation before completion
try:
    # Verify the gold dataset has expected structure and data
    if df_gold.count() == 0:
        raise RuntimeError("Gold layer dataset is empty - pipeline failed to produce valid results")
    
    required_gold_columns = ["kabupaten_kota", "tahun", "total_produksi", "kategori_ketahanan"]
    missing_required = [col for col in required_gold_columns if col not in df_gold.columns]
    if missing_required:
        raise RuntimeError(f"Gold layer missing required columns: {missing_required}")
    
    logger.info("Enhanced food security analytics calculation completed successfully!")
    logger.info(f"Final output contains data for {df_gold.select('kabupaten_kota').distinct().count()} districts")
    
except Exception as e:
    logger.error(f"Gold layer validation failed: {e}")
    SparkSessionManager.stop_session()
    raise

SparkSessionManager.stop_session()
