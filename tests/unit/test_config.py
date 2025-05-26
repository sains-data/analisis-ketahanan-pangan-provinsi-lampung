"""
Unit tests for configuration module
"""

from src.config.settings import HDFS_CONFIG, HIVE_CONFIG, SPARK_CONFIG


def test_spark_config_exists():
    """Test that Spark configuration is properly defined"""
    assert SPARK_CONFIG is not None
    assert "app_name" in SPARK_CONFIG
    assert "master" in SPARK_CONFIG


def test_hdfs_config_exists():
    """Test that HDFS configuration is properly defined"""
    assert HDFS_CONFIG is not None
    assert "namenode_host" in HDFS_CONFIG
    assert "base_url" in HDFS_CONFIG


def test_hive_config_exists():
    """Test that Hive configuration is properly defined"""
    assert HIVE_CONFIG is not None
    assert "host" in HIVE_CONFIG
    assert "port" in HIVE_CONFIG
