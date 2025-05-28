"""
Silver Layer ETL: Weather Data Cleaning Script

This script processes weather data from the bronze layer, performs cleaning
and validation, and writes the cleaned data to the silver layer with proper
partitioning using functional programming approach.
"""

import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pyspark.sql.functions import col, when, year, lit, regexp_replace, to_date
from pyspark.sql.types import DoubleType, StringType

from config.settings import FILE_CONFIG, HDFS_CONFIG, HIVE_CONFIG
from utils.data_quality import clean_invalid_markers
from utils.spark_utils import (
    SparkSessionManager,
    create_hive_table,
    read_csv_with_file_config,
    validate_data_quality,
    write_parquet_to_hdfs,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def load_bronze_data(spark):
    """Load weather data from bronze layer"""
    logger.info("Loading weather data from bronze layer")
    
    input_path = f"{str(HDFS_CONFIG['data_paths']['bronze'])}/cuaca.csv"
    filename = "cuaca.csv"
    
    df = read_csv_with_file_config(
        spark,
        input_path,
        filename,
        header=bool(FILE_CONFIG["header"]),
        infer_schema=False,  # We'll handle schema ourselves
    )

    logger.info(f"Loaded {df.count()} rows from bronze layer")
    return df


def validate_input_data(df):
    """Validate input data quality"""
    logger.info("Validating input data quality")

    # Log available columns for debugging
    logger.info(f"Available columns: {df.columns}")
    
    # Show sample data for debugging
    logger.info("Sample raw data:")
    df.show(5, truncate=False)

    expected_columns = ["TANGGAL", "suhu", "curah_hujan"]
    missing_columns = set(expected_columns) - set(df.columns)
    
    if missing_columns:
        logger.error(f"Missing expected columns: {missing_columns}")
        return False

    logger.info("Input data structure validation passed")
    return True


def clean_weather_columns(df):
    """Clean and convert weather data columns"""
    return (df
            .withColumn("curah_hujan", 
                       when(col("curah_hujan") == "-", None)
                       .when(col("curah_hujan") == "", None)
                       .otherwise(col("curah_hujan")))
            .withColumn("suhu", col("suhu").cast(DoubleType()))
            .withColumn("curah_hujan", col("curah_hujan").cast(DoubleType())))


def extract_year_from_date(df):
    """Extract year from date column in DD-MM-YYYY format"""
    return df.withColumn(
        "tahun",
        year(
            when(
                col("TANGGAL").rlike(r"\d{2}-\d{2}-\d{4}"),
                to_date(col("TANGGAL"), "dd-MM-yyyy")
            ).otherwise(None)
        )
    )


def add_missing_schema_columns(df):
    """Add missing columns to match expected schema"""
    return (df
            .withColumn("kabupaten_kota", lit("Lampung"))  # Province-wide data
            .withColumnRenamed("suhu", "suhu_rata_rata")
            .withColumn("kelembaban", lit(None).cast(DoubleType()))  # Not available
            .withColumnRenamed("TANGGAL", "tanggal"))


def handle_placeholder_values(df):
    """Handle placeholder values like 8888"""
    return df.withColumn(
        "curah_hujan",
        when(col("curah_hujan") == 8888, None).otherwise(col("curah_hujan"))
    )


def filter_valid_records(df):
    """Filter out invalid records"""
    return df.filter(
        col("tahun").isNotNull()
        & col("kabupaten_kota").isNotNull()
        & (col("tahun") >= 2000) 
        & (col("tahun") <= 2030)
        & (col("curah_hujan").isNull() | (col("curah_hujan") >= 0))
        & (col("suhu_rata_rata").isNull() | (col("suhu_rata_rata") >= -50))
        & (col("suhu_rata_rata").isNull() | (col("suhu_rata_rata") <= 60))
    )


def clean_and_transform(df):
    """Apply cleaning and transformation rules using function composition"""
    logger.info("Starting data cleaning and transformation")

    # Function composition pipeline
    df_cleaned = (df
                  .transform(clean_invalid_markers)
                  .transform(clean_weather_columns)
                  .transform(handle_placeholder_values)
                  .transform(extract_year_from_date)
                  .transform(add_missing_schema_columns)
                  .transform(filter_valid_records)
                  .dropDuplicates()
                  .select("kabupaten_kota", "curah_hujan", "suhu_rata_rata", 
                         "kelembaban", "tahun", "tanggal"))

    logger.info(f"Cleaning completed. Rows after cleaning: {df_cleaned.count()}")
    
    # Show sample cleaned data for debugging
    if df_cleaned.count() > 0:
        logger.info("Sample cleaned data:")
        df_cleaned.show(5, truncate=False)
    else:
        logger.warning("No data remaining after cleaning - checking intermediate steps")
        # Debug intermediate steps
        df_temp = df.transform(clean_invalid_markers).transform(clean_weather_columns)
        logger.info(f"After weather columns cleaning: {df_temp.count()} rows")
        df_temp = df_temp.transform(handle_placeholder_values).transform(extract_year_from_date)
        logger.info(f"After year extraction: {df_temp.count()} rows")
        df_temp.show(5, truncate=False)
    
    return df_cleaned


def validate_output_data(df):
    """Validate cleaned data quality"""
    logger.info("Validating cleaned data quality")

    required_columns = ["kabupaten_kota", "curah_hujan", "tahun"]
    validation_passed = validate_data_quality(df, required_columns, min_rows=50)

    if not validation_passed:
        raise ValueError("Output data validation failed")

    # Log data quality metrics
    null_rainfall = df.filter(col("curah_hujan").isNull()).count()
    null_temperature = df.filter(col("suhu_rata_rata").isNull()).count()
    
    logger.info(f"Records with null rainfall: {null_rainfall}")
    logger.info(f"Records with null temperature: {null_temperature}")

    # Check for extreme values
    extreme_rainfall = df.filter(col("curah_hujan") > 500).count()
    if extreme_rainfall > 0:
        logger.info(f"Found {extreme_rainfall} records with rainfall > 500mm")

    logger.info("Output data validation passed")
    return True


def save_to_silver(spark, df):
    """Save cleaned data to silver layer"""
    output_path = f"{str(HDFS_CONFIG['data_paths']['silver'])}/cuaca"
    database = str(HIVE_CONFIG["databases"]["silver"])
    table_name = "cuaca"
    
    logger.info(f"Saving cleaned data to silver layer: {output_path}")

    # Write parquet files partitioned by year
    write_parquet_to_hdfs(
        df,
        output_path,
        partition_by=str(FILE_CONFIG["partition_column"]),
        mode=str(FILE_CONFIG["write_mode"]),
    )

    # Define table schema
    columns = {
        "kabupaten_kota": "STRING",
        "curah_hujan": "DOUBLE",
        "suhu_rata_rata": "DOUBLE",
        "kelembaban": "DOUBLE",
        "tanggal": "STRING",
    }

    partition_columns = {"tahun": "INT"}

    # Create Hive table
    create_hive_table(
        spark,
        database,
        table_name,
        columns,
        partition_columns,
        output_path,
        "PARQUET",
    )

    logger.info(f"Successfully created Hive table: {database}.{table_name}")


def run_pipeline():
    """Execute the complete cleaning pipeline using functional composition"""
    spark = None
    try:
        logger.info("Starting weather data cleaning pipeline")

        # Initialize Spark session
        spark = SparkSessionManager.get_session("CleanCuacaData")

        # Execute pipeline
        df_bronze = load_bronze_data(spark)
        validate_input_data(df_bronze)
        df_silver = clean_and_transform(df_bronze)
        validate_output_data(df_silver)
        save_to_silver(spark, df_silver)

        logger.info("Weather data cleaning pipeline completed successfully")

        # Print summary statistics
        input_count = df_bronze.count()
        output_count = df_silver.count()
        reduction_pct = (input_count - output_count) / input_count * 100

        logger.info("Pipeline Summary:")
        logger.info(f"- Input rows: {input_count}")
        logger.info(f"- Output rows: {output_count}")
        logger.info(f"- Data reduction: {reduction_pct:.2f}%")

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise
    finally:
        if spark:
            SparkSessionManager.stop_session()


def main():
    """Main entry point"""
    run_pipeline()


if __name__ == "__main__":
    main()