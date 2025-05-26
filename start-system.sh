#!/bin/bash

echo "Starting Lampung Food Security Big Data System..."

# Create necessary directories with correct permissions
mkdir -p dags logs scripts data/{bronze,silver,gold}
# Fix YARN local dir permissions for NodeManager
chmod -R 777 data/yarn/local 2>/dev/null || true
sudo chown -R 50000:0 data/yarn/local
chmod -R 755 logs dags 2>/dev/null || true
sudo chown -R 50000:0 logs dags

# Stop any existing containers
echo "Cleaning up existing containers..."
docker-compose down -v

echo "Starting Hadoop ecosystem..."
docker-compose up -d namenode datanode1 datanode2
sleep 45

echo "Starting YARN..."
docker-compose up -d resourcemanager nodemanager1 nodemanager2
sleep 30

echo "Starting Hive..."
docker-compose up -d postgres
sleep 20
docker-compose up -d hive-metastore
sleep 30
docker-compose up -d hiveserver2
sleep 30

echo "Starting Spark..."
docker-compose up -d spark-master spark-worker1 spark-worker2
sleep 30

echo "Starting Airflow..."
docker-compose up -d airflow-postgres
sleep 20
docker-compose up -d airflow-webserver airflow-scheduler
sleep 45

echo "Starting Superset..."
docker-compose up -d superset
sleep 30

# Initialize HDFS directories
echo "Creating HDFS directories..."
docker exec namenode hdfs dfs -mkdir -p /data/{bronze,silver,gold}
docker exec namenode hdfs dfs -mkdir -p /user/hive/warehouse
docker exec namenode hdfs dfs -mkdir -p /spark-logs
docker exec namenode hdfs dfs -chmod 777 /data
docker exec namenode hdfs dfs -chmod 777 /user/hive/warehouse
docker exec namenode hdfs dfs -chmod 777 /spark-logs

# Create Hive databases
echo "Creating Hive databases..."
sleep 10
docker exec hiveserver2 /opt/hive/bin/beeline -u jdbc:hive2://hiveserver2:10000 -e "CREATE DATABASE IF NOT EXISTS bronze;" || true
docker exec hiveserver2 /opt/hive/bin/beeline -u jdbc:hive2://hiveserver2:10000 -e "CREATE DATABASE IF NOT EXISTS silver;" || true
docker exec hiveserver2 /opt/hive/bin/beeline -u jdbc:hive2://hiveserver2:10000 -e "CREATE DATABASE IF NOT EXISTS gold;" || true

echo "System startup complete!"
echo ""
echo "Access URLs:"
echo "- Hadoop NameNode: http://localhost:9870"
echo "- YARN ResourceManager: http://localhost:8088"
echo "- Spark Master: http://localhost:8080"
echo "- Airflow: http://localhost:8085 (admin/admin)"
echo "- Superset: http://localhost:8088 (admin/admin123)"
echo "- HiveServer2: jdbc:hive2://localhost:10000"
echo ""
echo "Checking system status..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
