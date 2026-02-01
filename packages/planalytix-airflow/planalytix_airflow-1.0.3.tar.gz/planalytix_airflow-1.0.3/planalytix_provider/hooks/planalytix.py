"""
Planalytix Hook for Apache Airflow.

Provides a connection interface to the Planalytix API for triggering
and monitoring data syncs.
"""

from typing import Any, Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import warnings

# Suppress deprecation warnings for Airflow imports during transition
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    # Try Airflow 3.x SDK first, fall back to 2.x
    try:
        from airflow.sdk.bases.hook import BaseHook
    except ImportError:
        from airflow.hooks.base import BaseHook

from airflow.exceptions import AirflowException


class PlanalytixHook(BaseHook):
    """
    Hook for interacting with the Planalytix API.
    
    Uses API key authentication for secure access to the orchestration API.
    
    :param planalytix_conn_id: Airflow connection ID for Planalytix
    :param api_key: Optional API key (overrides connection)
    :param base_url: Optional base URL (overrides connection)
    """
    
    conn_name_attr = "planalytix_conn_id"
    default_conn_name = "planalytix_default"
    conn_type = "planalytix"
    hook_name = "Planalytix"
    
    # Connection form fields for Airflow UI
    @staticmethod
    def get_connection_form_widgets() -> Dict[str, Any]:
        """Return connection form widgets for Airflow UI."""
        from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
        from wtforms import StringField
        
        return {
            "api_key": StringField(
                "API Key",
                widget=BS3TextFieldWidget(),
                description="Planalytix API key (starts with flx_)",
            ),
            "organization_id": StringField(
                "Organization ID",
                widget=BS3TextFieldWidget(),
                description="Optional: Override organization ID",
            ),
        }
    
    @staticmethod
    def get_ui_field_behaviour() -> Dict[str, Any]:
        """Return custom field behaviors for Airflow UI."""
        return {
            "hidden_fields": ["port", "schema", "login"],
            "relabeling": {
                "host": "Planalytix URL",
                "password": "API Key",
            },
            "placeholders": {
                "host": "https://api.planalytix.com",
                "password": "flx_xxxxxxxxxxxx",
            },
        }
    
    def __init__(
        self,
        planalytix_conn_id: str = default_conn_name,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        super().__init__()
        self.planalytix_conn_id = planalytix_conn_id
        self._api_key = api_key
        self._base_url = base_url
        self._session: Optional[requests.Session] = None
    
    def get_conn(self) -> requests.Session:
        """
        Get a requests session configured for Planalytix API.
        
        :return: Configured requests Session
        """
        if self._session is None:
            self._session = self._create_session()
        return self._session
    
    def _create_session(self) -> requests.Session:
        """Create and configure a requests session."""
        session = requests.Session()
        
        # Get connection details
        conn = self.get_connection(self.planalytix_conn_id)
        
        # Determine API key
        api_key = self._api_key or conn.password or conn.extra_dejson.get("api_key")
        if not api_key:
            raise AirflowException(
                f"No API key found for connection '{self.planalytix_conn_id}'. "
                "Set the password field or 'api_key' in extras."
            )
        
        # Determine base URL
        base_url = self._base_url or conn.host
        if not base_url:
            raise AirflowException(
                f"No base URL found for connection '{self.planalytix_conn_id}'. "
                "Set the host field."
            )
        
        # Ensure URL has scheme
        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"
        
        self._base_url = base_url.rstrip("/")
        
        # Configure session
        session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "planalytix-airflow/1.0.0",
        })
        
        # Add organization ID if specified
        org_id = conn.extra_dejson.get("organization_id")
        if org_id:
            session.headers["X-Organization-ID"] = org_id
        
        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    @property
    def base_url(self) -> str:
        """Get the base URL, initializing connection if needed."""
        if self._base_url is None:
            self.get_conn()
        return self._base_url
    
    def trigger_sync(
        self,
        connection_id: str,
        sync_type: str = "incremental",
        streams: Optional[List[str]] = None,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Trigger a sync job for a connection.
        
        :param connection_id: Planalytix connection ID to sync
        :param sync_type: Type of sync - 'incremental' or 'full'
        :param streams: Optional list of specific streams to sync
        :param priority: Job priority - 'low', 'normal', or 'high' (Enterprise)
        :param metadata: Optional metadata to attach (e.g., dag_id, task_id)
        :param idempotency_key: Optional key to prevent duplicate jobs
        :return: API response with job details
        """
        url = f"{self.base_url}/api/v1/connections/{connection_id}/sync"
        
        payload = {
            "sync_type": sync_type,
            "priority": priority,
        }
        
        if streams:
            payload["streams"] = streams
        if metadata:
            payload["metadata"] = metadata
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key
        
        response = self.get_conn().post(url, json=payload)
        
        if response.status_code == 409:
            # Sync already in progress
            data = response.json()
            self.log.warning(
                "Sync already in progress for connection %s: job %s",
                connection_id,
                data.get("existing_job_id"),
            )
            return data
        
        response.raise_for_status()
        return response.json()
    
    def get_job(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a sync job.
        
        :param job_id: The job ID to check
        :return: Job status and details
        """
        url = f"{self.base_url}/api/v1/jobs/{job_id}"
        response = self.get_conn().get(url)
        response.raise_for_status()
        return response.json()
    
    def get_job_results(self, job_id: str) -> Dict[str, Any]:
        """
        Get the results of a completed sync job.
        
        :param job_id: The job ID
        :return: Job results including sync statistics
        """
        url = f"{self.base_url}/api/v1/jobs/{job_id}/results"
        response = self.get_conn().get(url)
        response.raise_for_status()
        return response.json()
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a running or queued sync job.
        
        :param job_id: The job ID to cancel
        :return: Cancellation confirmation
        """
        url = f"{self.base_url}/api/v1/jobs/{job_id}/cancel"
        response = self.get_conn().post(url)
        response.raise_for_status()
        return response.json()
    
    def list_jobs(
        self,
        status: Optional[str] = None,
        connection_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List sync jobs with optional filtering.
        
        :param status: Filter by status (queued, running, completed, failed, cancelled)
        :param connection_id: Filter by connection ID
        :param limit: Maximum number of jobs to return
        :param offset: Offset for pagination
        :return: List of jobs with pagination info
        """
        url = f"{self.base_url}/api/v1/jobs"
        params = {"limit": limit, "offset": offset}
        
        if status:
            params["status"] = status
        if connection_id:
            params["connection_id"] = connection_id
        
        response = self.get_conn().get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test the connection to Planalytix API.
        
        :return: Tuple of (success, message)
        """
        try:
            response = self.list_jobs(limit=1)
            return True, f"Connection successful. API responding."
        except requests.exceptions.RequestException as e:
            return False, f"Connection failed: {str(e)}"
