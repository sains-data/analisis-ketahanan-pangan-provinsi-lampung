#!/bin/bash
set -e

# Ensure Hive 'gold' database exists
echo "[Gold] Creating Hive database 'gold' (if not exists)..."
docker exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "CREATE DATABASE IF NOT EXISTS gold;"

# Run Spark job for gold layer
echo "[Gold] Running Spark job: calc_indikator.py..."
docker exec spark-master /spark/bin/spark-submit --master spark://spark-master:7077 /scripts/calc_indikator.py

echo "[Gold] Running Spark job: calc_gold_enriched.py..."
docker exec spark-master /spark/bin/spark-submit --master spark://spark-master:7077 /scripts/calc_gold_enriched.py

# Validate Hive tables
echo "[Gold] Listing tables in Hive database 'gold':"
docker exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SHOW TABLES IN gold;"
