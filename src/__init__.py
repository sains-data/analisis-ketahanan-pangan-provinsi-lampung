"""
Lampung Food Security Big Data System

A comprehensive big data analytics system for food security analysis in Lampung
Province, Indonesia,
using the Hadoop ecosystem and the Medallion (Bronze-Silver-Gold) architecture.

This package contains:
- config: Configuration management
- etl: ETL scripts for data processing
- utils: Common utilities and helpers
"""

__version__ = "1.0.0"
__author__ = "Institut Teknologi Sumatera - Lampung Food Security Team"

from .config.settings import HDFS_CONFIG, HIVE_CONFIG, SPARK_CONFIG
from .utils.data_quality import DataQualityValidator, validate_bronze_data

# Import commonly used utilities for convenience
from .utils.spark_utils import SparkSessionManager, create_spark_session

__all__ = [
    "SparkSessionManager",
    "create_spark_session",
    "DataQualityValidator",
    "validate_bronze_data",
    "SPARK_CONFIG",
    "HDFS_CONFIG",
    "HIVE_CONFIG",
]
