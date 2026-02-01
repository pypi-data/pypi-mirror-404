"""
Planalytix Sync Operator for Apache Airflow.

Triggers and optionally waits for Planalytix data sync jobs.
"""

from typing import Any, Dict, List, Optional, Sequence
import time

from airflow.models import BaseOperator
from airflow.utils.context import Context
from airflow.exceptions import AirflowException

# Handle Airflow 2.x vs 3.x import differences
try:
    # Airflow 3.x
    from airflow.models.baseoperatorlink import BaseOperatorLink
except ImportError:
    try:
        # Airflow 2.x alternative location
        from airflow.models.baseoperator import BaseOperatorLink
    except ImportError:
        # Fallback: create a dummy class if not available
        class BaseOperatorLink:
            """Fallback BaseOperatorLink for compatibility."""
            name = "Link"
            def get_link(self, operator, *, ti_key):
                return ""

try:
    from airflow.models.taskinstancekey import TaskInstanceKey
except ImportError:
    # Airflow 2.x fallback
    TaskInstanceKey = Any

from planalytix_provider.hooks.planalytix import PlanalytixHook


class PlanalytixJobLink(BaseOperatorLink):
    """Link to the Planalytix job in the UI."""
    
    name = "Planalytix Job"
    
    def get_link(
        self,
        operator: BaseOperator,
        *,
        ti_key: TaskInstanceKey,
    ) -> str:
        """Get link to job in Planalytix UI."""
        # Get job_id from XCom
        from airflow.models import XCom
        
        job_id = XCom.get_value(
            ti_key=ti_key,
            key="job_id",
        )
        
        if not job_id:
            return ""
        
        # Get base URL from operator or default
        base_url = getattr(operator, "base_url", "https://app.planalytix.io")
        return f"{base_url}/jobs/{job_id}"


class PlanalytixSyncOperator(BaseOperator):
    """
    Triggers a Planalytix sync job for a connection.
    
    This operator can either:
    - Trigger and immediately return (wait_for_completion=False)
    - Trigger and wait for the job to complete (wait_for_completion=True)
    
    :param connection_id: Planalytix connection ID to sync
    :param planalytix_conn_id: Airflow connection ID for Planalytix API
    :param sync_type: Type of sync - 'incremental' or 'full' (default: incremental)
    :param streams: Optional list of specific streams to sync
    :param priority: Job priority - 'low', 'normal', or 'high' (Enterprise only)
    :param wait_for_completion: Whether to wait for the job to complete
    :param poll_interval: Seconds between status checks when waiting
    :param timeout: Maximum seconds to wait for completion
    :param fail_on_error: Whether to fail the task if sync fails
    
    Example usage::
    
        sync_salesforce = PlanalytixSyncOperator(
            task_id="sync_salesforce",
            connection_id="conn_abc123",
            sync_type="incremental",
            wait_for_completion=True,
            poll_interval=30,
            timeout=3600,
        )
    """
    
    template_fields: Sequence[str] = (
        "connection_id",
        "sync_type",
        "streams",
        "priority",
        "metadata",
        "idempotency_key",
    )
    
    operator_extra_links = (PlanalytixJobLink(),)
    
    ui_color = "#3B82F6"  # Planalytix blue
    ui_fgcolor = "#FFFFFF"
    
    def __init__(
        self,
        *,
        connection_id: str,
        planalytix_conn_id: str = "planalytix_default",
        sync_type: str = "incremental",
        streams: Optional[List[str]] = None,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        wait_for_completion: bool = True,
        poll_interval: int = 30,
        timeout: int = 3600,
        fail_on_error: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.connection_id = connection_id
        self.planalytix_conn_id = planalytix_conn_id
        self.sync_type = sync_type
        self.streams = streams
        self.priority = priority
        self.metadata = metadata or {}
        self.idempotency_key = idempotency_key
        self.wait_for_completion = wait_for_completion
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.fail_on_error = fail_on_error
        self.base_url = None  # Set during execution for job link
    
    def execute(self, context: Context) -> Dict[str, Any]:
        """Execute the sync operation."""
        hook = PlanalytixHook(planalytix_conn_id=self.planalytix_conn_id)
        self.base_url = hook.base_url
        
        # Add Airflow context to metadata
        enriched_metadata = {
            **self.metadata,
            "dag_id": context["dag"].dag_id,
            "task_id": self.task_id,
            "run_id": context["run_id"],
            "execution_date": str(context["execution_date"]),
        }
        
        # Generate idempotency key if not provided
        idempotency_key = self.idempotency_key
        if not idempotency_key:
            # Use dag_id + task_id + run_id for natural idempotency
            idempotency_key = f"{context['dag'].dag_id}_{self.task_id}_{context['run_id']}"
        
        self.log.info(
            "Triggering sync for connection %s (type=%s, priority=%s)",
            self.connection_id,
            self.sync_type,
            self.priority,
        )
        
        # Trigger the sync
        try:
            response = hook.trigger_sync(
                connection_id=self.connection_id,
                sync_type=self.sync_type,
                streams=self.streams,
                priority=self.priority,
                metadata=enriched_metadata,
                idempotency_key=idempotency_key,
            )
        except Exception as e:
            raise AirflowException(f"Failed to trigger sync: {e}") from e
        
        job_id = response.get("job_id") or response.get("existing_job_id")
        if not job_id:
            raise AirflowException(f"No job_id in response: {response}")
        
        self.log.info("Sync job created: %s", job_id)
        
        # Push job_id to XCom for downstream tasks and links
        context["ti"].xcom_push(key="job_id", value=job_id)
        context["ti"].xcom_push(key="connection_id", value=self.connection_id)
        
        if not self.wait_for_completion:
            self.log.info("Not waiting for completion (wait_for_completion=False)")
            return {"job_id": job_id, "status": response.get("status", "queued")}
        
        # Wait for completion
        return self._wait_for_job(hook, job_id, context)
    
    def _wait_for_job(
        self,
        hook: PlanalytixHook,
        job_id: str,
        context: Context,
    ) -> Dict[str, Any]:
        """Wait for a job to complete."""
        start_time = time.time()
        
        self.log.info(
            "Waiting for job %s to complete (poll_interval=%ds, timeout=%ds)",
            job_id,
            self.poll_interval,
            self.timeout,
        )
        
        terminal_states = {"completed", "failed", "cancelled"}
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > self.timeout:
                raise AirflowException(
                    f"Job {job_id} did not complete within {self.timeout} seconds"
                )
            
            try:
                job = hook.get_job(job_id)
            except Exception as e:
                self.log.warning("Error checking job status: %s", e)
                time.sleep(self.poll_interval)
                continue
            
            status = job.get("status", "unknown")
            
            self.log.info(
                "Job %s status: %s (elapsed: %.0fs)",
                job_id,
                status,
                elapsed,
            )
            
            # Log progress if available
            progress = job.get("progress", {})
            if progress:
                self.log.info("Progress: %s", progress)
            
            if status in terminal_states:
                # Job finished
                context["ti"].xcom_push(key="job_status", value=status)
                
                if status == "completed":
                    self.log.info("Job %s completed successfully", job_id)
                    
                    # Try to get results
                    try:
                        results = hook.get_job_results(job_id)
                        context["ti"].xcom_push(key="job_results", value=results)
                        return {
                            "job_id": job_id,
                            "status": status,
                            "results": results,
                        }
                    except Exception as e:
                        self.log.warning("Could not fetch job results: %s", e)
                        return {"job_id": job_id, "status": status}
                
                elif status == "failed":
                    error = job.get("error", {})
                    error_msg = error.get("message", "Unknown error")
                    
                    if self.fail_on_error:
                        raise AirflowException(
                            f"Job {job_id} failed: {error_msg}"
                        )
                    else:
                        self.log.error("Job %s failed: %s", job_id, error_msg)
                        return {"job_id": job_id, "status": status, "error": error}
                
                elif status == "cancelled":
                    if self.fail_on_error:
                        raise AirflowException(f"Job {job_id} was cancelled")
                    else:
                        self.log.warning("Job %s was cancelled", job_id)
                        return {"job_id": job_id, "status": status}
            
            time.sleep(self.poll_interval)
    
    def on_kill(self) -> None:
        """Cancel the job when the task is killed."""
        # Try to cancel the job if we have a job_id
        # This requires accessing XCom which isn't directly available here
        self.log.warning(
            "Task killed. To cancel the Planalytix job, use the Planalytix UI."
        )
