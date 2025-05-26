from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

# Default arguments
default_args = {
    'owner': 'lampung-foodsec-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': 300  # 5 minutes
}

dag = DAG(
    'lampung_foodsec_dag',
    default_args=default_args,
    description='Lampung Food Security Medallion Pipeline',
    schedule_interval=None,  # Set to None for manual trigger, or '@daily' for scheduled
    catchup=False,
    tags=['food-security', 'big-data', 'lampung']
)

# Bronze Layer: Ingest CSVs to HDFS
bronze_task = BashOperator(
    task_id='bronze_layer_ingest',
    bash_command='bash /data/run_bronze.sh',
    dag=dag,
    doc_md="""
    Ingests all CSVs from data/bronze/ into HDFS /data/bronze/ using the run_bronze.sh script.
    """
)

# Silver Layer: Run Spark jobs for cleaning and transformation
silver_task = BashOperator(
    task_id='silver_layer_etl',
    bash_command='bash /data/run_silver.sh',
    dag=dag,
    doc_md="""
    Runs Spark jobs to clean and transform data from bronze to silver layer using run_silver.sh.
    """
)

# Gold Layer: Run Spark job for business metrics
gold_task = BashOperator(
    task_id='gold_layer_etl',
    bash_command='bash /data/run_gold.sh',
    dag=dag,
    doc_md="""
    Runs Spark job to calculate business metrics and indicators for the gold layer using run_gold.sh.
    """
)

# Validation: Check gold table in Hive
validate_gold_task = BashOperator(
    task_id='validate_gold_table',
    bash_command='docker compose exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SHOW TABLES IN gold; SELECT COUNT(*) FROM gold.ketahanan_pangan_kab;"',
    dag=dag,
    doc_md="""
    Validates the gold layer by listing tables and counting rows in gold.ketahanan_pangan_kab in Hive.
    """
)

bronze_task >> silver_task >> gold_task >> validate_gold_task
