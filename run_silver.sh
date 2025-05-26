#!/bin/bash
set -e

# Ensure Hive 'silver' database exists
echo "[Silver] Creating Hive database 'silver' (if not exists)..."
docker exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "CREATE DATABASE IF NOT EXISTS silver;"

# Run Spark jobs for silver layer
echo "[Silver] Running Spark job: clean_produksi.py (using robust src/etl version)..."
docker exec spark-master /spark/bin/spark-submit --master spark://spark-master:7077 /src/etl/silver/clean_produksi.py

echo "[Silver] Note: Only produksi data cleaning is implemented with robust ETL pattern."
echo "[Silver] Other datasets would need similar ETL scripts in src/etl/silver/ for full processing."

# Validate Hive tables
echo "[Silver] Listing tables in Hive database 'silver':"
docker exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SHOW TABLES IN silver;"
