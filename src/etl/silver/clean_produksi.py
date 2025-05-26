"""
Silver Layer ETL: Production Data Cleaning Script

This script processes production data from the bronze layer, performs cleaning
and validation, and writes the cleaned data to the silver layer with proper
partitioning.
"""

import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pyspark.sql.functions import col
from pyspark.sql.functions import round as spark_round
from pyspark.sql.types import DoubleType, IntegerType

from config.settings import FILE_CONFIG, HDFS_CONFIG, HIVE_CONFIG, QUALITY_CONFIG
from utils.data_quality import (
    calculate_data_quality_score,
    clean_invalid_markers,
    generate_quality_report,
    standardize_region_names,
    validate_bronze_data,
)
from utils.spark_utils import (
    SparkSessionManager,
    clean_text_column,
    create_hive_table,
    read_csv_from_hdfs,
    validate_data_quality,
    write_parquet_to_hdfs,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class ProductionDataCleaner:
    """Handles cleaning and transformation of production data"""

    def __init__(self):
        self.spark = SparkSessionManager.get_session("CleanProduksiData")
        self.input_path = (
            f"{str(HDFS_CONFIG['data_paths']['bronze'])}/produksi_pangan.csv"
        )
        self.output_path = f"{str(HDFS_CONFIG['data_paths']['silver'])}/produksi_pangan"
        self.table_name = "produksi_pangan"
        self.database = str(HIVE_CONFIG["databases"]["silver"])

    def load_bronze_data(self):
        """Load production data from bronze layer"""
        logger.info("Loading production data from bronze layer")

        df = read_csv_from_hdfs(
            self.spark,
            self.input_path,
            separator=str(FILE_CONFIG["csv_separator"]),
            header=bool(FILE_CONFIG["header"]),
            infer_schema=bool(FILE_CONFIG["infer_schema"]),
        )

        logger.info(f"Loaded {df.count()} rows from bronze layer")
        return df

    def validate_input_data(self, df):
        """Validate input data quality"""
        logger.info("Validating input data quality")

        validation_results = validate_bronze_data(df, self.table_name)
        quality_score = calculate_data_quality_score(validation_results)

        logger.info(f"Input data quality score: {quality_score}/100")

        if quality_score < 60:
            logger.warning("Input data quality is below acceptable threshold")
            print(generate_quality_report(validation_results))

        return validation_results

    def clean_and_transform(self, df):
        """Apply cleaning and transformation rules"""
        logger.info("Starting data cleaning and transformation")

        # Remove invalid markers
        df_cleaned = clean_invalid_markers(df)

        # Standardize region names
        df_cleaned = standardize_region_names(df_cleaned, "kabupaten_kota")

        # Data type conversions and validations
        df_cleaned = df_cleaned.withColumn("tahun", col("tahun").cast(IntegerType()))
        df_cleaned = df_cleaned.withColumn(
            "produksi", col("produksi").cast(DoubleType())
        )
        df_cleaned = df_cleaned.withColumn(
            "luas_panen", col("luas_panen").cast(DoubleType())
        )
        df_cleaned = df_cleaned.withColumn(
            "produktivitas", col("produktivitas").cast(DoubleType())
        )

        # Filter out invalid records
        df_cleaned = df_cleaned.filter(
            col("produksi").isNotNull()
            & (col("produksi") > 0)
            & col("luas_panen").isNotNull()
            & (col("luas_panen") > 0)
            & col("tahun").isNotNull()
            & col("kabupaten_kota").isNotNull()
        )

        # Calculate derived metrics
        df_cleaned = df_cleaned.withColumn(
            "produktivitas_per_ha", spark_round(col("produksi") / col("luas_panen"), 4)
        )

        # Clean text columns
        df_cleaned = clean_text_column(df_cleaned, "kabupaten_kota")
        df_cleaned = clean_text_column(df_cleaned, "komoditas")

        # Remove duplicates
        df_cleaned = df_cleaned.dropDuplicates()

        # Validate year range
        df_cleaned = df_cleaned.filter((col("tahun") >= 2000) & (col("tahun") <= 2030))

        # Filter out obvious data entry errors (production > 1M tons for a
        # single record)
        df_cleaned = df_cleaned.filter(col("produksi") <= 1000000)

        logger.info(f"Cleaning completed. Rows after cleaning: {df_cleaned.count()}")
        return df_cleaned

    def validate_output_data(self, df):
        """Validate cleaned data quality"""
        logger.info("Validating cleaned data quality")

        # Check required columns are present and have data
        required_columns = list(QUALITY_CONFIG["required_columns"].get("produksi", []))
        validation_passed = validate_data_quality(df, required_columns, min_rows=100)

        if not validation_passed:
            raise ValueError("Output data validation failed")

        # Additional business rule validations
        invalid_productivity = df.filter(
            (col("produktivitas_per_ha") <= 0)
            | (
                col("produktivitas_per_ha") > 100
            )  # Extremely high productivity threshold
        ).count()

        if invalid_productivity > 0:
            logger.warning(
                f"Found {invalid_productivity} records with suspicious "
                f"productivity values"
            )

        logger.info("Output data validation passed")
        return True

    def save_to_silver(self, df):
        """Save cleaned data to silver layer"""
        logger.info(f"Saving cleaned data to silver layer: {self.output_path}")

        # Write parquet files partitioned by year
        write_parquet_to_hdfs(
            df,
            self.output_path,
            partition_by=str(FILE_CONFIG["partition_column"]),
            mode=str(FILE_CONFIG["write_mode"]),
        )

        # Define table schema
        columns = {
            "kabupaten_kota": "STRING",
            "komoditas": "STRING",
            "produksi": "DOUBLE",
            "luas_panen": "DOUBLE",
            "produktivitas": "DOUBLE",
            "produktivitas_per_ha": "DOUBLE",
        }

        partition_columns = {"tahun": "INT"}

        # Create Hive table
        create_hive_table(
            self.spark,
            self.database,
            self.table_name,
            columns,
            partition_columns,
            self.output_path,
            "PARQUET",
        )

        logger.info(
            f"Successfully created Hive table: {self.database}.{self.table_name}"
        )

    def run_pipeline(self):
        """Execute the complete cleaning pipeline"""
        try:
            logger.info("Starting production data cleaning pipeline")

            # Load data
            df_bronze = self.load_bronze_data()

            # Validate input
            self.validate_input_data(df_bronze)

            # Clean and transform
            df_silver = self.clean_and_transform(df_bronze)

            # Validate output
            self.validate_output_data(df_silver)

            # Save to silver layer
            self.save_to_silver(df_silver)

            logger.info("Production data cleaning pipeline completed successfully")

            # Print summary statistics
            logger.info("Pipeline Summary:")
            logger.info(f"- Input rows: {df_bronze.count()}")
            logger.info(f"- Output rows: {df_silver.count()}")
            reduction_pct = (
                (df_bronze.count() - df_silver.count()) / df_bronze.count() * 100
            )
            logger.info(f"- Data reduction: {reduction_pct:.2f}%")

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise
        finally:
            SparkSessionManager.stop_session()


def main():
    """Main entry point"""
    cleaner = ProductionDataCleaner()
    cleaner.run_pipeline()


if __name__ == "__main__":
    main()
