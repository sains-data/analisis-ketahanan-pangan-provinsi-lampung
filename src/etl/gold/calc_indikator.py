"""
Gold Layer ETL: Food Security Indicators Calculation Script

This script processes silver layer data to calculate food security indicators
and writes the results to the gold layer with proper partitioning.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pyspark.sql import DataFrame
from pyspark.sql.functions import avg, col, count
from pyspark.sql.functions import sum as spark_sum
from pyspark.sql.functions import when

from config.settings import HDFS_CONFIG
from utils.spark_utils import SparkSessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Spark Session
spark = SparkSessionManager.get_session("CalculateIndicators")

# Table dependency configuration
REQUIRED_TABLES = ["silver.produksi_pangan"]  # Tables that must exist
OPTIONAL_TABLES = {
    "silver.harga_pangan": "price data",
    "silver.cuaca": "weather data"
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

# Read silver data with dependency checking
logger.info("Loading required silver layer tables...")
df_produksi = load_table_with_dependency_check("silver.produksi_pangan", required=True)
assert df_produksi is not None, "Required produksi_pangan table must not be None"

logger.info("Loading optional silver layer tables...")
df_harga = load_table_with_dependency_check("silver.harga_pangan", required=False)
df_cuaca = load_table_with_dependency_check("silver.cuaca", required=False)

# Log pipeline capabilities based on available data
available_features = ["production indicators"]
if df_harga: available_features.append("price analysis")
if df_cuaca: available_features.append("weather correlations")

logger.info(f"Pipeline capabilities for this run: {', '.join(available_features)}")

# Calculate food security indicators
logger.info("Calculating food security indicators...")
df_indicators = (
    df_produksi.groupBy("kabupaten_kota", "tahun")
    .agg(
        spark_sum("produksi").alias("total_produksi"),
        avg("produktivitas").alias("avg_produktivitas"),
        spark_sum("luas_panen").alias("total_luas_panen"),
        count("komoditas").alias("jenis_komoditas"),
    )
    .withColumn("produksi_per_kapita", col("total_produksi") / 1000)
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

# Log dataset characteristics
final_row_count = df_indicators.count()
final_columns = len(df_indicators.columns)
logger.info(f"Indicators dataset prepared with {final_row_count} rows and {final_columns} columns")

# Write to Gold layer
gold_path = f"{HDFS_CONFIG['base_url']}{HDFS_CONFIG['data_paths']['gold']}/ketahanan_pangan_kab"
logger.info(f"Writing indicators to gold layer: {gold_path}")

df_indicators.write.mode("overwrite").partitionBy("tahun").parquet(gold_path)

# Create Gold Hive table
logger.info("Creating/updating Hive table...")
spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS gold.ketahanan_pangan_kab (
        kabupaten_kota STRING,
        total_produksi DOUBLE,
        avg_produktivitas DOUBLE,
        total_luas_panen DOUBLE,
        jenis_komoditas LONG,
        produksi_per_kapita DOUBLE,
        skor_ketersediaan DOUBLE,
        kategori_ketahanan STRING
    )
    PARTITIONED BY (tahun INT)
    STORED AS PARQUET
    LOCATION '{gold_path}'
"""
)

spark.sql("MSCK REPAIR TABLE gold.ketahanan_pangan_kab")

# Final validation before completion
try:
    # Verify the gold dataset has expected structure and data
    if df_indicators.count() == 0:
        raise RuntimeError("Gold layer indicators dataset is empty - pipeline failed to produce valid results")
    
    required_gold_columns = ["kabupaten_kota", "tahun", "total_produksi", "kategori_ketahanan"]
    missing_required = [col for col in required_gold_columns if col not in df_indicators.columns]
    if missing_required:
        raise RuntimeError(f"Gold layer missing required columns: {missing_required}")
    
    logger.info("Food security indicators calculation completed successfully!")
    logger.info(f"Final output contains data for {df_indicators.select('kabupaten_kota').distinct().count()} districts")
    
except Exception as e:
    logger.error(f"Gold layer validation failed: {e}")
    SparkSessionManager.stop_session()
    raise

SparkSessionManager.stop_session()
