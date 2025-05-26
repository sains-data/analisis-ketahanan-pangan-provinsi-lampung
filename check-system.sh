#!/bin/bash

echo "=== System Health Check ==="
echo ""

echo "1. Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(namenode|datanode|resourcemanager|nodemanager|hive|spark|airflow|superset)"

echo ""
echo "2. HDFS Status:"
docker exec namenode hdfs dfsadmin -safemode get
docker exec namenode hdfs dfs -ls / 2>/dev/null || echo "HDFS not accessible"

echo ""
echo "3. YARN Status:"
docker exec resourcemanager yarn node -list 2>/dev/null || echo "YARN not accessible"

echo ""
echo "4. Hive Status:"
docker exec hiveserver2 /opt/hive/bin/beeline -u jdbc:hive2://hiveserver2:10000 -e "SHOW DATABASES;" --silent=true 2>/dev/null || echo "Hive not accessible"

echo ""
echo "5. Spark Status:"
docker exec spark-master /spark/bin/spark-submit --version 2>/dev/null | head -3 || echo "Spark not accessible"

echo ""
echo "6. Service URLs:"
echo "- NameNode UI: http://localhost:9870"
echo "- ResourceManager UI: http://localhost:8088"
echo "- Spark Master UI: http://localhost:8080"
echo "- Airflow UI: http://localhost:8085"
echo "- Superset UI: http://localhost:8089"

echo ""
echo "=== Health Check Complete ==="
