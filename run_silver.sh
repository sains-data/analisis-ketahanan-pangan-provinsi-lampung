#!/bin/bash
set -e

# Ensure Hive 'silver' database exists
echo "[Silver] Creating Hive database 'silver' (if not exists)..."
docker exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "CREATE DATABASE IF NOT EXISTS silver;"

# Run Spark jobs for silver layer
echo "[Silver] Running Spark job: clean_produksi.py (using robust src/etl version)..."
docker exec spark-master sh -c "cd /src && /spark/bin/spark-submit --master spark://spark-master:7077 etl/silver/clean_produksi.py"

echo "[Silver] Running Spark job: clean_harga.py..."
docker exec spark-master sh -c "cd /src && /spark/bin/spark-submit --master spark://spark-master:7077 etl/silver/clean_harga.py"

echo "[Silver] Running Spark job: clean_cuaca.py..."
docker exec spark-master sh -c "cd /src && /spark/bin/spark-submit --master spark://spark-master:7077 etl/silver/clean_cuaca.py"

echo "[Silver] Running Spark job: clean_sosial_ekonomi.py..."
docker exec spark-master sh -c "cd /src && /spark/bin/spark-submit --master spark://spark-master:7077 etl/silver/clean_sosial_ekonomi.py"

echo "[Silver] Running Spark job: clean_konsumsi_pangan.py..."
docker exec spark-master sh -c "cd /src && /spark/bin/spark-submit --master spark://spark-master:7077 etl/silver/clean_konsumsi_pangan.py"

echo "[Silver] Running Spark job: clean_ikp.py..."
docker exec spark-master sh -c "cd /src && /spark/bin/spark-submit --master spark://spark-master:7077 etl/silver/clean_ikp.py"

echo "[Silver] Note: All silver layer ETL scripts implemented with robust functional programming pattern."
echo "[Silver] Datasets processed: produksi, harga, cuaca, sosial_ekonomi, konsumsi_pangan, and ikp."

# Validate Hive tables
echo "[Silver] Listing tables in Hive database 'silver':"
docker exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SHOW TABLES IN silver;"
