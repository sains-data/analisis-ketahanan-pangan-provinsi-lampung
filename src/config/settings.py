"""
Centralized configuration settings for Lampung Food Security Big Data System
"""

import os
from pathlib import Path

# Base project directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# HDFS Configuration
HDFS_CONFIG = {
    "namenode_host": "namenode",
    "namenode_port": 9000,
    "base_url": "hdfs://namenode:9000",
    "data_paths": {
        "bronze": "/data/bronze",
        "silver": "/data/silver",
        "gold": "/data/gold",
    },
}

# Spark Configuration
SPARK_CONFIG = {
    "app_name": "LampungFoodSecurity",
    "master": "spark://spark-master:7077",
    "warehouse_dir": "hdfs://namenode:9000/user/hive/warehouse",
    "hive_support": True,
    "serializer": "org.apache.spark.serializer.KryoSerializer",
    "sql_adaptive_enabled": True,
    "sql_adaptive_coalesce_partitions_enabled": True,
}

# Hive Configuration
HIVE_CONFIG = {
    "host": "hiveserver2",
    "port": 10000,
    "databases": {"bronze": "bronze", "silver": "silver", "gold": "gold"},
    "jdbc_url": "jdbc:hive2://hiveserver2:10000",
}

# Data Schema Configuration
DATA_SCHEMAS = {
    "bronze": {
        "produksi_pangan": [
            "kabupaten_kota",
            "komoditas",
            "produksi",
            "luas_panen",
            "produktivitas",
            "tahun",
        ],
        "harga_pangan": [
            "kabupaten_kota",
            "komoditas",
            "harga_produsen",
            "harga_konsumen",
            "tahun",
        ],
        "cuaca": [
            "kabupaten_kota",
            "curah_hujan",
            "suhu_rata_rata",
            "kelembaban",
            "tahun",
        ],
        "sosial_ekonomi": [
            "kabupaten_kota",
            "jumlah_penduduk",
            "tingkat_kemiskinan",
            "ipkm",
            "tahun",
        ],
        "konsumsi_pangan": [
            "kabupaten_kota",
            "komoditas",
            "konsumsi_per_kapita",
            "tahun",
        ],
        "ikp": ["kabupaten_kota", "skor_ikp", "kategori_ikp", "tahun"],
    }
}

# File Processing Configuration
FILE_CONFIG = {
    "csv_separator": ",",
    "encoding": "utf-8",
    "header": True,
    "infer_schema": True,
    "partition_column": "tahun",
    "output_format": "parquet",
    "write_mode": "overwrite",
}

# Data Quality Configuration
QUALITY_CONFIG = {
    "outlier_detection": {
        "curah_hujan_max": 5000,  # mm per year
    },
    "invalid_markers": ["#N/A", "8888", "9999", "-", ""],
    "required_columns": {
        "all": ["tahun", "kabupaten_kota"],
        "produksi": ["produksi", "luas_panen"],
        "harga": ["harga_produsen"],
        "cuaca": ["curah_hujan"],
    },
}

# Environment Variables
ENV_CONFIG = {
    "python_path": os.getenv("PYTHONPATH", str(PROJECT_ROOT / "src")),
    "java_home": os.getenv("JAVA_HOME", "/opt/java/openjdk"),
    "spark_home": os.getenv("SPARK_HOME", "/spark"),
    "hadoop_home": os.getenv("HADOOP_HOME", "/opt/hadoop"),
}

# Logging Configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "level": "DEBUG",
            "formatter": "detailed",
            "class": "logging.FileHandler",
            "filename": str(PROJECT_ROOT / "logs" / "pipeline.log"),
            "mode": "a",
        },
    },
    "loggers": {
        "": {"handlers": ["default", "file"], "level": "DEBUG", "propagate": False}
    },
}

# Pipeline Configuration
PIPELINE_CONFIG = {
    "batch_size": 10000,
    "max_retries": 3,
    "retry_delay": 60,  # seconds
    "timeout": 3600,  # seconds
    "checkpoint_enabled": True,
    "checkpoint_location": "hdfs://namenode:9000/tmp/checkpoints",
}

# Airflow Configuration
AIRFLOW_CONFIG = {
    "dag_id": "lampung_foodsec_dag",
    "schedule_interval": None,
    "max_active_runs": 1,
    "catchup": False,
    "retries": 2,
    "retry_delay": 300,  # seconds
}

# Superset Configuration
SUPERSET_CONFIG = {
    "host": "superset", 
    "port": 8088,
    "admin_user": "admin",
    "database_uri": "hive://hive@hiveserver2:10000/gold",
}
