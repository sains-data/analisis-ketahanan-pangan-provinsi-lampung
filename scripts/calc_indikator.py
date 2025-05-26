"""
Gold Layer ETL: Food Security Indicators Calculation Script

This script processes silver layer data to calculate food security indicators
and writes the results to the gold layer with proper partitioning.
"""

import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent))

from pyspark.sql.functions import avg, col, count
from pyspark.sql.functions import sum as spark_sum
from pyspark.sql.functions import when

from src.config.settings import HDFS_CONFIG, HIVE_CONFIG
from src.utils.spark_utils import SparkSessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Spark Session
spark_manager = SparkSessionManager("CalculateIndicators")
spark = spark_manager.get_session()

# Read silver data
logger.info("Reading silver layer data...")
df_produksi = spark.table("silver.produksi_pangan")
df_harga = (
    spark.table("silver.harga_pangan")
    if spark.catalog.tableExists("silver.harga_pangan")
    else None
)
df_cuaca = (
    spark.table("silver.cuaca") if spark.catalog.tableExists("silver.cuaca") else None
)

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

# Write to Gold layer
gold_path = f"{HDFS_CONFIG['base_url']}{HDFS_CONFIG['gold_path']}/ketahanan_pangan_kab"
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
logger.info("Food security indicators calculation completed successfully!")

spark_manager.stop()
