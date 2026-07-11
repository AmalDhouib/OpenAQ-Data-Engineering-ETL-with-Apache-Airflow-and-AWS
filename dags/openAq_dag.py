from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

import os
import sys

current_file = os.path.abspath(__file__)
dag_directory = os.path.dirname(current_file)
project_root = os.path.dirname(dag_directory)
sys.path.insert(0, project_root)

from pipelines.openAq_pipeline import openAq_pipeline
from pipelines.aws_s3_pipeline import upload_s3_pipeline

file_postfix = datetime.now().strftime("%Y%m%d")

default_args = {
    "owner": "DHOUIB Amal",
    "start_date": datetime(2026, 7, 5)
}

dag = DAG(
    dag_id="etl_openAq_pipeline",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
    tags=["openaq", "etl", "pipeline"]
)
# extraction from openAq
extract = PythonOperator(
    task_id="extract_openAq",
    python_callable=openAq_pipeline,
    op_kwargs={
        "file_name": f"openaq_measurements_{file_postfix}",
        "limit": 10,
        "page": 1,
        "iso": "FR"
    },
    dag=dag
)
# upload to s3
upload_s3 = PythonOperator(
    task_id='s3_upload',
    python_callable=upload_s3_pipeline,
    dag=dag
)

extract >> upload_s3