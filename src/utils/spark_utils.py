"""
Spark utilities for session management and common operations
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_replace
from pyspark.sql.types import StructType

if TYPE_CHECKING:
    from pyspark.sql import DataFrame

from ..config.settings import HDFS_CONFIG, SPARK_CONFIG

logger = logging.getLogger(__name__)


class SparkSessionManager:
    """Manages Spark session creation, configuration, and cleanup"""

    _instance: Optional[SparkSession] = None

    @classmethod
    def get_session(
        cls, app_name: Optional[str] = None, configs: Optional[Dict[str, Any]] = None
    ) -> SparkSession:
        """
        Get or create a Spark session with standard configuration

        Args:
            app_name: Application name for the Spark session
            configs: Additional Spark configurations

        Returns:
            SparkSession: Configured Spark session
        """
        if cls._instance is None or (
            cls._instance is not None and cls._instance._jsc.sc().isStopped()
        ):
            cls._instance = cls._create_session(app_name, configs)

        return cls._instance

    @classmethod
    def _create_session(
        cls, app_name: Optional[str] = None, configs: Optional[Dict[str, Any]] = None
    ) -> SparkSession:
        """Create a new Spark session with configuration"""

        session_name = app_name or str(SPARK_CONFIG["app_name"])
        logger.info(f"Creating Spark session: {session_name}")

        builder = (
            SparkSession.builder.appName(session_name)
            .config("spark.sql.warehouse.dir", SPARK_CONFIG["warehouse_dir"])
            .config("spark.serializer", SPARK_CONFIG["serializer"])
            .config("spark.sql.adaptive.enabled", SPARK_CONFIG["sql_adaptive_enabled"])
            .config(
                "spark.sql.adaptive.coalescePartitions.enabled",
                SPARK_CONFIG["sql_adaptive_coalesce_partitions_enabled"],
            )
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
            .config("spark.sql.adaptive.skewJoin.enabled", "true")
            .config("spark.sql.adaptive.localShuffleReader.enabled", "true")
        )

        # Add custom configurations
        if configs:
            for key, value in configs.items():
                builder = builder.config(key, value)

        # Enable Hive support if configured
        if SPARK_CONFIG["hive_support"]:
            builder = builder.enableHiveSupport()

        session = builder.getOrCreate()

        # Set log level to reduce verbosity
        session.sparkContext.setLogLevel("WARN")

        logger.info(f"Spark session created successfully: {session_name}")
        return session

    @classmethod
    def stop_session(cls):
        """Stop the current Spark session"""
        if cls._instance is not None and not cls._instance._jsc.sc().isStopped():
            logger.info("Stopping Spark session")
            cls._instance.stop()
            cls._instance = None


def create_spark_session(
    app_name: str, configs: Optional[Dict[str, Any]] = None
) -> SparkSession:
    """
    Convenience function to create a Spark session

    Args:
        app_name: Application name
        configs: Additional configurations

    Returns:
        SparkSession: Configured Spark session
    """
    return SparkSessionManager.get_session(app_name, configs)


def read_csv_from_hdfs(
    spark: SparkSession,
    file_path: str,
    schema: Optional[StructType] = None,
    separator: str = ",",
    header: bool = True,
    infer_schema: bool = True,
) -> "DataFrame":
    """
    Read CSV file from HDFS with error handling

    Args:
        spark: Spark session
        file_path: HDFS file path
        schema: Optional schema definition
        separator: CSV separator
        header: Whether CSV has header
        infer_schema: Whether to infer schema

    Returns:
        DataFrame: Loaded DataFrame
    """
    try:
        full_path = f"{HDFS_CONFIG['base_url']}{file_path}"
        logger.info(f"Reading CSV from: {full_path}")

        reader = (
            spark.read.format("csv")
            .option("header", header)
            .option("sep", separator)
            .option("encoding", "utf-8")
            .option("multiline", "true")
            .option("escape", '"')
            .option("quote", '"')
        )

        if schema:
            reader = reader.schema(schema)
        elif infer_schema:
            reader = reader.option("inferSchema", "true")

        df = reader.load(full_path)
        logger.info(f"Successfully loaded CSV with {df.count()} rows")
        return df

    except Exception as e:
        logger.error(f"Error reading CSV from {file_path}: {str(e)}")
        raise


def write_parquet_to_hdfs(
    df: "DataFrame",
    output_path: str,
    partition_by: Optional[str] = None,
    mode: str = "overwrite",
) -> None:
    """
    Write DataFrame to HDFS as Parquet with error handling

    Args:
        df: DataFrame to write
        output_path: HDFS output path
        partition_by: Column to partition by
        mode: Write mode (overwrite, append, etc.)
    """
    try:
        full_path = f"{HDFS_CONFIG['base_url']}{output_path}"
        logger.info(f"Writing Parquet to: {full_path}")

        writer = df.write.mode(mode).format("parquet")

        if partition_by:
            writer = writer.partitionBy(partition_by)

        writer.save(full_path)
        logger.info(f"Successfully wrote Parquet to {output_path}")

    except Exception as e:
        logger.error(f"Error writing Parquet to {output_path}: {str(e)}")
        raise


def create_hive_table(
    spark: SparkSession,
    database: str,
    table_name: str,
    columns: Dict[str, str],
    partition_columns: Optional[Dict[str, str]] = None,
    location: Optional[str] = None,
    storage_format: str = "PARQUET",
) -> None:
    """
    Create Hive external table

    Args:
        spark: Spark session
        database: Hive database name
        table_name: Table name
        columns: Dictionary of column names and types
        partition_columns: Partition columns and types
        location: HDFS location for external table
        storage_format: Storage format (PARQUET, ORC, etc.)
    """
    try:
        # Create database if not exists
        spark.sql(f"CREATE DATABASE IF NOT EXISTS {database}")

        # Build column definitions
        column_defs = [f"{name} {dtype}" for name, dtype in columns.items()]
        columns_sql = ",\n    ".join(column_defs)

        # Build partition clause
        partition_sql = ""
        if partition_columns:
            partition_defs = [
                f"{name} {dtype}" for name, dtype in partition_columns.items()
            ]
            partition_sql = f"PARTITIONED BY ({', '.join(partition_defs)})"

        # Build location clause
        location_sql = ""
        if location:
            full_location = f"{HDFS_CONFIG['base_url']}{location}"
            location_sql = f"LOCATION '{full_location}'"

        # Create table SQL
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {database}.{table_name} (
            {columns_sql}
        )
        {partition_sql}
        STORED AS {storage_format}
        {location_sql}
        """

        logger.info(f"Creating Hive table: {database}.{table_name}")
        spark.sql(create_sql)

        # Repair partitions if it's a partitioned table
        if partition_columns:
            spark.sql(f"MSCK REPAIR TABLE {database}.{table_name}")

        logger.info(f"Successfully created Hive table: {database}.{table_name}")

    except Exception as e:
        logger.error(f"Error creating Hive table {database}.{table_name}: {str(e)}")
        raise


def clean_text_column(df: "DataFrame", column_name: str) -> "DataFrame":
    """
    Clean text column by removing special characters and normalizing

    Args:
        df: Input DataFrame
        column_name: Column name to clean

    Returns:
        DataFrame: DataFrame with cleaned column
    """
    return df.withColumn(
        column_name, regexp_replace(col(column_name), r"[^a-zA-Z0-9\s]", "")
    ).withColumn(column_name, regexp_replace(col(column_name), r"\s+", " "))


def handle_missing_values(
    df: "DataFrame",
    strategy: str = "drop",
    fill_values: Optional[Dict[str, Any]] = None,
) -> "DataFrame":
    """
    Handle missing values in DataFrame

    Args:
        df: Input DataFrame
        strategy: Strategy for handling missing values ('drop', 'fill')
        fill_values: Dictionary of column names and fill values

    Returns:
        DataFrame: DataFrame with handled missing values
    """
    if strategy == "drop":
        return df.dropna()
    elif strategy == "fill" and fill_values:
        return df.fillna(fill_values)
    else:
        logger.warning(
            "Invalid strategy or missing fill_values, returning original DataFrame"
        )
        return df


def validate_data_quality(
    df: "DataFrame", required_columns: list, min_rows: int = 1
) -> bool:
    """
    Validate basic data quality checks

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        min_rows: Minimum number of rows required

    Returns:
        bool: True if validation passes
    """
    try:
        # Check if required columns exist
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False

        # Check minimum row count
        row_count = df.count()
        if row_count < min_rows:
            logger.error(
                f"Insufficient data: {row_count} rows, minimum required: {min_rows}"
            )
            return False

        logger.info(
            f"Data quality validation passed: {row_count} rows, "
            f"all required columns present"
        )
        return True

    except Exception as e:
        logger.error(f"Error during data quality validation: {str(e)}")
        return False
