"""
Example DAG: Planalytix Data Sync Pipeline

This DAG demonstrates how to use the Planalytix Airflow provider to:
1. Trigger data syncs for multiple connections
2. Wait for syncs to complete
3. Process the results

Prerequisites:
- Install the planalytix-airflow package
- Create an Airflow connection 'planalytix_default' with your API key
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

from planalytix_provider.operators.sync import PlanalytixSyncOperator
from planalytix_provider.sensors.sync import PlanalytixSyncSensor


# Default arguments for all tasks
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# Define the DAG
with DAG(
    dag_id="planalytix_data_sync",
    default_args=default_args,
    description="Sync data from multiple sources using Planalytix",
    schedule_interval="0 6 * * *",  # Daily at 6 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["planalytix", "data-sync", "etl"],
) as dag:
    
    # Start marker
    start = EmptyOperator(task_id="start")
    
    # Sync Salesforce data
    sync_salesforce = PlanalytixSyncOperator(
        task_id="sync_salesforce",
        connection_id="{{ var.value.planalytix_salesforce_connection_id }}",
        sync_type="incremental",
        wait_for_completion=True,
        poll_interval=30,
        timeout=3600,  # 1 hour
    )
    
    # Sync HubSpot data
    sync_hubspot = PlanalytixSyncOperator(
        task_id="sync_hubspot",
        connection_id="{{ var.value.planalytix_hubspot_connection_id }}",
        sync_type="incremental",
        wait_for_completion=True,
        poll_interval=30,
        timeout=3600,
    )
    
    # Sync PostgreSQL data (full refresh weekly, incremental otherwise)
    sync_postgres = PlanalytixSyncOperator(
        task_id="sync_postgres",
        connection_id="{{ var.value.planalytix_postgres_connection_id }}",
        sync_type="{{ 'full' if dag_run.logical_date.weekday() == 0 else 'incremental' }}",
        streams=["orders", "customers", "products"],  # Only sync specific tables
        wait_for_completion=True,
        poll_interval=60,
        timeout=7200,  # 2 hours for full sync
    )
    
    # Process sync results
    def log_sync_results(**context):
        """Log the results of all sync operations."""
        task_ids = ["sync_salesforce", "sync_hubspot", "sync_postgres"]
        
        for task_id in task_ids:
            results = context["ti"].xcom_pull(
                task_ids=task_id,
                key="return_value",
            )
            if results:
                status = results.get("status", "unknown")
                job_id = results.get("job_id", "unknown")
                
                print(f"{task_id}: Job {job_id} - Status: {status}")
                
                if "results" in results:
                    summary = results["results"].get("summary", {})
                    rows = summary.get("total_rows_synced", 0)
                    print(f"  Rows synced: {rows}")
    
    process_results = PythonOperator(
        task_id="process_results",
        python_callable=log_sync_results,
        trigger_rule=TriggerRule.ALL_DONE,  # Run even if some syncs failed
    )
    
    # End marker
    end = EmptyOperator(
        task_id="end",
        trigger_rule=TriggerRule.ALL_DONE,
    )
    
    # Define task dependencies
    # Syncs run in parallel after start
    start >> [sync_salesforce, sync_hubspot, sync_postgres]
    
    # Process results after all syncs complete
    [sync_salesforce, sync_hubspot, sync_postgres] >> process_results >> end


# Alternative pattern: Trigger and wait separately
with DAG(
    dag_id="planalytix_async_sync",
    default_args=default_args,
    description="Async pattern: trigger syncs then wait",
    schedule_interval="0 8 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["planalytix", "data-sync", "async"],
) as async_dag:
    
    # Trigger sync without waiting
    trigger_sync = PlanalytixSyncOperator(
        task_id="trigger_sync",
        connection_id="{{ var.value.planalytix_main_connection_id }}",
        sync_type="incremental",
        wait_for_completion=False,  # Don't wait
    )
    
    # Do other work while sync runs
    other_work = EmptyOperator(task_id="other_work")
    
    # Then wait for sync to complete using sensor
    wait_for_sync = PlanalytixSyncSensor(
        task_id="wait_for_sync",
        job_id="{{ ti.xcom_pull(task_ids='trigger_sync', key='job_id') }}",
        poke_interval=30,
        timeout=3600,
        mode="reschedule",  # Free up worker slot while waiting
    )
    
    # Continue with downstream tasks
    downstream = EmptyOperator(task_id="downstream_processing")
    
    trigger_sync >> other_work >> wait_for_sync >> downstream
