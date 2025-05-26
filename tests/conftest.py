"""
Pytest configuration and fixtures
"""
import os
import sys
from pathlib import Path

import pytest

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment variables for testing
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"


@pytest.fixture(scope="session")
def spark_session():
    """Create a Spark session for testing (if available)"""
    try:
        from pyspark.sql import SparkSession

        spark = (
            SparkSession.builder.appName("TestSession").master("local[2]").getOrCreate()
        )
        yield spark
        spark.stop()
    except ImportError:
        pytest.skip("PySpark not available for testing")
