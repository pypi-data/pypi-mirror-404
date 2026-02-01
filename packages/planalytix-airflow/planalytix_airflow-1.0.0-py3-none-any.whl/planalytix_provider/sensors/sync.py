"""
Planalytix Sync Sensor for Apache Airflow.

Waits for a Planalytix sync job to complete.
"""

from typing import Any, Dict, Optional, Sequence

from airflow.sensors.base import BaseSensorOperator
from airflow.utils.context import Context
from airflow.exceptions import AirflowException

from planalytix_provider.hooks.planalytix import PlanalytixHook


class PlanalytixSyncSensor(BaseSensorOperator):
    """
    Waits for a Planalytix sync job to reach a terminal state.
    
    This sensor is useful when:
    - You trigger a sync with wait_for_completion=False
    - You need to check on a job triggered externally
    - You want more control over the waiting logic
    
    :param job_id: The job ID to monitor (can be templated from XCom)
    :param planalytix_conn_id: Airflow connection ID for Planalytix API
    :param success_states: States considered successful (default: ['completed'])
    :param failure_states: States considered failed (default: ['failed', 'cancelled'])
    :param soft_fail: If True, mark task as skipped on failure instead of failed
    
    Example usage::
    
        # Wait for a job triggered by upstream task
        wait_for_sync = PlanalytixSyncSensor(
            task_id="wait_for_sync",
            job_id="{{ ti.xcom_pull(task_ids='trigger_sync', key='job_id') }}",
            poke_interval=30,
            timeout=3600,
        )
    """
    
    template_fields: Sequence[str] = ("job_id",)
    
    ui_color = "#93C5FD"  # Light blue
    ui_fgcolor = "#1E3A8A"
    
    def __init__(
        self,
        *,
        job_id: str,
        planalytix_conn_id: str = "planalytix_default",
        success_states: Optional[list] = None,
        failure_states: Optional[list] = None,
        soft_fail: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.job_id = job_id
        self.planalytix_conn_id = planalytix_conn_id
        self.success_states = success_states or ["completed"]
        self.failure_states = failure_states or ["failed", "cancelled"]
        self.soft_fail = soft_fail
        self._hook: Optional[PlanalytixHook] = None
    
    def poke(self, context: Context) -> bool:
        """Check if the job has reached a terminal state."""
        if not self.job_id:
            raise AirflowException("job_id is required but was empty")
        
        hook = self._get_hook()
        
        self.log.info("Checking status of job %s", self.job_id)
        
        try:
            job = hook.get_job(self.job_id)
        except Exception as e:
            self.log.warning("Error fetching job status: %s", e)
            return False
        
        status = job.get("status", "unknown")
        
        self.log.info("Job %s status: %s", self.job_id, status)
        
        # Log progress if available
        progress = job.get("progress", {})
        if progress:
            self.log.info("Progress: %s", progress)
        
        # Check for success
        if status in self.success_states:
            self.log.info("Job %s completed successfully", self.job_id)
            
            # Push results to XCom
            try:
                results = hook.get_job_results(self.job_id)
                context["ti"].xcom_push(key="job_results", value=results)
            except Exception as e:
                self.log.warning("Could not fetch job results: %s", e)
            
            context["ti"].xcom_push(key="job_status", value=status)
            return True
        
        # Check for failure
        if status in self.failure_states:
            error = job.get("error", {})
            error_msg = error.get("message", f"Job ended with status: {status}")
            
            context["ti"].xcom_push(key="job_status", value=status)
            context["ti"].xcom_push(key="job_error", value=error)
            
            if self.soft_fail:
                from airflow.exceptions import AirflowSkipException
                raise AirflowSkipException(f"Job {self.job_id} {status}: {error_msg}")
            else:
                raise AirflowException(f"Job {self.job_id} {status}: {error_msg}")
        
        # Still running
        return False
    
    def _get_hook(self) -> PlanalytixHook:
        """Get or create the Planalytix hook."""
        if self._hook is None:
            self._hook = PlanalytixHook(planalytix_conn_id=self.planalytix_conn_id)
        return self._hook
