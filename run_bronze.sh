#!/bin/bash
set -e

# Copy datasets from datasets/ to data/bronze/ for processing
echo "[Bronze] Copying datasets from datasets/ to data/bronze/..."
mkdir -p data/bronze
cp datasets/*.csv data/bronze/
echo "  Copied $(ls datasets/*.csv | wc -l) datasets to bronze layer"

# Ingest all CSVs from data/bronze/ to HDFS /data/bronze/
echo "[Bronze] Creating HDFS directory /data/bronze (if not exists)..."
docker compose exec namenode hdfs dfs -mkdir -p /data/bronze

echo "[Bronze] Uploading CSVs to HDFS..."
for file in data/bronze/*.csv; do
  echo "  Uploading $file..."
  docker compose exec namenode hdfs dfs -put -f /data/bronze/$(basename "$file") /data/bronze/
done

echo "[Bronze] Listing files in HDFS /data/bronze:"
docker compose exec namenode hdfs dfs -ls /data/bronze
