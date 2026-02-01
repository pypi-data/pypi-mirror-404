"""
Unit tests for PlanalytixSyncOperator.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

# We need to mock Airflow modules before importing our code
import sys

# Create mock modules
mock_airflow = MagicMock()
mock_base_operator = MagicMock()
mock_context = MagicMock()
mock_exceptions = MagicMock()


class MockAirflowException(Exception):
    """Mock AirflowException for testing."""
    pass


mock_exceptions.AirflowException = MockAirflowException

sys.modules["airflow"] = mock_airflow
sys.modules["airflow.models"] = MagicMock()
sys.modules["airflow.models.baseoperator"] = mock_base_operator
sys.modules["airflow.models.taskinstancekey"] = MagicMock()
sys.modules["airflow.utils.context"] = mock_context
sys.modules["airflow.exceptions"] = mock_exceptions
sys.modules["airflow.hooks.base"] = MagicMock()

from planalytix_provider.operators.sync import PlanalytixSyncOperator


class MockContext:
    """Mock Airflow execution context."""
    
    def __init__(self):
        self.ti = MagicMock()
        self.ti.xcom_push = MagicMock()
        self.dag = MagicMock()
        self.dag.dag_id = "test_dag"
        self._data = {
            "ti": self.ti,
            "dag": self.dag,
            "run_id": "test_run_123",
            "execution_date": datetime(2024, 1, 15, 10, 30),
        }
    
    def __getitem__(self, key):
        return self._data.get(key)
    
    def get(self, key, default=None):
        return self._data.get(key, default)


class TestPlanalytixSyncOperatorInit:
    """Tests for operator initialization."""
    
    def test_required_connection_id(self):
        """Test connection_id is required."""
        operator = PlanalytixSyncOperator(
            task_id="test",
            connection_id="conn_abc123",
        )
        assert operator.connection_id == "conn_abc123"
    
    def test_default_values(self):
        """Test default parameter values."""
        operator = PlanalytixSyncOperator(
            task_id="test",
            connection_id="conn_abc123",
        )
        
        assert operator.planalytix_conn_id == "planalytix_default"
        assert operator.sync_type == "incremental"
        assert operator.streams is None
        assert operator.priority == "normal"
        assert operator.wait_for_completion is True
        assert operator.poll_interval == 30
        assert operator.timeout == 3600
        assert operator.fail_on_error is True
    
    def test_custom_values(self):
        """Test custom parameter values."""
        operator = PlanalytixSyncOperator(
            task_id="test",
            connection_id="conn_abc123",
            planalytix_conn_id="custom_conn",
            sync_type="full",
            streams=["orders", "customers"],
            priority="high",
            wait_for_completion=False,
            poll_interval=60,
            timeout=7200,
            fail_on_error=False,
        )
        
        assert operator.planalytix_conn_id == "custom_conn"
        assert operator.sync_type == "full"
        assert operator.streams == ["orders", "customers"]
        assert operator.priority == "high"
        assert operator.wait_for_completion is False
        assert operator.poll_interval == 60
        assert operator.timeout == 7200
        assert operator.fail_on_error is False
    
    def test_template_fields(self):
        """Test template fields are defined."""
        assert "connection_id" in PlanalytixSyncOperator.template_fields
        assert "sync_type" in PlanalytixSyncOperator.template_fields
        assert "streams" in PlanalytixSyncOperator.template_fields
        assert "priority" in PlanalytixSyncOperator.template_fields
        assert "metadata" in PlanalytixSyncOperator.template_fields
        assert "idempotency_key" in PlanalytixSyncOperator.template_fields


class TestPlanalytixSyncOperatorExecute:
    """Tests for operator execution."""
    
    @patch("planalytix_provider.operators.sync.PlanalytixHook")
    def test_execute_triggers_sync(self, mock_hook_class):
        """Test execute triggers a sync."""
        mock_hook = MagicMock()
        mock_hook.base_url = "https://api.planalytix.io"
        mock_hook.trigger_sync.return_value = {
            "job_id": "job_abc123",
            "status": "queued",
        }
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "completed",
        }
        mock_hook.get_job_results.return_value = {
            "summary": {"total_rows_synced": 1000},
        }
        mock_hook_class.return_value = mock_hook
        
        operator = PlanalytixSyncOperator(
            task_id="test",
            connection_id="conn_abc123",
        )
        
        context = MockContext()
        result = operator.execute(context)
        
        mock_hook.trigger_sync.assert_called_once()
        assert result["job_id"] == "job_abc123"
    
    @patch("planalytix_provider.operators.sync.PlanalytixHook")
    def test_execute_adds_airflow_metadata(self, mock_hook_class):
        """Test execute adds Airflow context to metadata."""
        mock_hook = MagicMock()
        mock_hook.base_url = "https://api.planalytix.io"
        mock_hook.trigger_sync.return_value = {
            "job_id": "job_abc123",
            "status": "completed",
        }
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "completed",
        }
        mock_hook.get_job_results.return_value = {}
        mock_hook_class.return_value = mock_hook
        
        operator = PlanalytixSyncOperator(
            task_id="test_task",
            connection_id="conn_abc123",
        )
        
        context = MockContext()
        operator.execute(context)
        
        call_kwargs = mock_hook.trigger_sync.call_args.kwargs
        assert "dag_id" in call_kwargs["metadata"]
        assert "task_id" in call_kwargs["metadata"]
        assert "run_id" in call_kwargs["metadata"]
    
    @patch("planalytix_provider.operators.sync.PlanalytixHook")
    def test_execute_generates_idempotency_key(self, mock_hook_class):
        """Test execute generates idempotency key if not provided."""
        mock_hook = MagicMock()
        mock_hook.base_url = "https://api.planalytix.io"
        mock_hook.trigger_sync.return_value = {
            "job_id": "job_abc123",
            "status": "completed",
        }
        mock_hook.get_job.return_value = {"status": "completed"}
        mock_hook.get_job_results.return_value = {}
        mock_hook_class.return_value = mock_hook
        
        operator = PlanalytixSyncOperator(
            task_id="test_task",
            connection_id="conn_abc123",
        )
        
        context = MockContext()
        operator.execute(context)
        
        call_kwargs = mock_hook.trigger_sync.call_args.kwargs
        assert call_kwargs["idempotency_key"] is not None
        assert "test_dag" in call_kwargs["idempotency_key"]
        assert "test_task" in call_kwargs["idempotency_key"]
    
    @patch("planalytix_provider.operators.sync.PlanalytixHook")
    def test_execute_uses_provided_idempotency_key(self, mock_hook_class):
        """Test execute uses provided idempotency key."""
        mock_hook = MagicMock()
        mock_hook.base_url = "https://api.planalytix.io"
        mock_hook.trigger_sync.return_value = {
            "job_id": "job_abc123",
            "status": "completed",
        }
        mock_hook.get_job.return_value = {"status": "completed"}
        mock_hook.get_job_results.return_value = {}
        mock_hook_class.return_value = mock_hook
        
        operator = PlanalytixSyncOperator(
            task_id="test_task",
            connection_id="conn_abc123",
            idempotency_key="my_custom_key",
        )
        
        context = MockContext()
        operator.execute(context)
        
        call_kwargs = mock_hook.trigger_sync.call_args.kwargs
        assert call_kwargs["idempotency_key"] == "my_custom_key"
    
    @patch("planalytix_provider.operators.sync.PlanalytixHook")
    def test_execute_pushes_job_id_to_xcom(self, mock_hook_class):
        """Test execute pushes job_id to XCom."""
        mock_hook = MagicMock()
        mock_hook.base_url = "https://api.planalytix.io"
        mock_hook.trigger_sync.return_value = {
            "job_id": "job_abc123",
            "status": "completed",
        }
        mock_hook.get_job.return_value = {"status": "completed"}
        mock_hook.get_job_results.return_value = {}
        mock_hook_class.return_value = mock_hook
        
        operator = PlanalytixSyncOperator(
            task_id="test_task",
            connection_id="conn_abc123",
        )
        
        context = MockContext()
        operator.execute(context)
        
        context["ti"].xcom_push.assert_any_call(key="job_id", value="job_abc123")
    
    @patch("planalytix_provider.operators.sync.PlanalytixHook")
    def test_execute_no_wait(self, mock_hook_class):
        """Test execute returns immediately when wait_for_completion=False."""
        mock_hook = MagicMock()
        mock_hook.base_url = "https://api.planalytix.io"
        mock_hook.trigger_sync.return_value = {
            "job_id": "job_abc123",
            "status": "queued",
        }
        mock_hook_class.return_value = mock_hook
        
        operator = PlanalytixSyncOperator(
            task_id="test_task",
            connection_id="conn_abc123",
            wait_for_completion=False,
        )
        
        context = MockContext()
        result = operator.execute(context)
        
        assert result["job_id"] == "job_abc123"
        assert result["status"] == "queued"
        mock_hook.get_job.assert_not_called()


class TestPlanalytixSyncOperatorWait:
    """Tests for waiting for job completion."""
    
    @patch("planalytix_provider.operators.sync.time")
    @patch("planalytix_provider.operators.sync.PlanalytixHook")
    def test_wait_polls_until_complete(self, mock_hook_class, mock_time):
        """Test waiting polls until job completes."""
        mock_hook = MagicMock()
        mock_hook.base_url = "https://api.planalytix.io"
        mock_hook.trigger_sync.return_value = {"job_id": "job_123"}
        mock_hook.get_job.side_effect = [
            {"status": "queued"},
            {"status": "running", "progress": {"rows_synced": 100}},
            {"status": "running", "progress": {"rows_synced": 500}},
            {"status": "completed"},
        ]
        mock_hook.get_job_results.return_value = {"summary": {"total": 1000}}
        mock_hook_class.return_value = mock_hook
        
        mock_time.time.side_effect = [0, 10, 20, 30, 40]
        mock_time.sleep = MagicMock()
        
        operator = PlanalytixSyncOperator(
            task_id="test",
            connection_id="conn_abc",
            poll_interval=10,
        )
        
        context = MockContext()
        result = operator.execute(context)
        
        assert result["status"] == "completed"
        assert mock_hook.get_job.call_count == 4
    
    @patch("planalytix_provider.operators.sync.time")
    @patch("planalytix_provider.operators.sync.PlanalytixHook")
    def test_wait_raises_on_failure(self, mock_hook_class, mock_time):
        """Test waiting raises exception on job failure."""
        mock_hook = MagicMock()
        mock_hook.base_url = "https://api.planalytix.io"
        mock_hook.trigger_sync.return_value = {"job_id": "job_123"}
        mock_hook.get_job.return_value = {
            "status": "failed",
            "error": {"message": "Source connection failed"},
        }
        mock_hook_class.return_value = mock_hook
        
        mock_time.time.side_effect = [0, 10]
        
        operator = PlanalytixSyncOperator(
            task_id="test",
            connection_id="conn_abc",
            fail_on_error=True,
        )
        
        context = MockContext()
        
        with pytest.raises(MockAirflowException) as exc_info:
            operator.execute(context)
        
        assert "failed" in str(exc_info.value).lower()
    
    @patch("planalytix_provider.operators.sync.time")
    @patch("planalytix_provider.operators.sync.PlanalytixHook")
    def test_wait_continues_on_failure_when_fail_on_error_false(
        self, mock_hook_class, mock_time
    ):
        """Test waiting returns result when fail_on_error=False."""
        mock_hook = MagicMock()
        mock_hook.base_url = "https://api.planalytix.io"
        mock_hook.trigger_sync.return_value = {"job_id": "job_123"}
        mock_hook.get_job.return_value = {
            "status": "failed",
            "error": {"message": "Source connection failed"},
        }
        mock_hook_class.return_value = mock_hook
        
        mock_time.time.side_effect = [0, 10]
        
        operator = PlanalytixSyncOperator(
            task_id="test",
            connection_id="conn_abc",
            fail_on_error=False,
        )
        
        context = MockContext()
        result = operator.execute(context)
        
        assert result["status"] == "failed"
        assert "error" in result
    
    @patch("planalytix_provider.operators.sync.time")
    @patch("planalytix_provider.operators.sync.PlanalytixHook")
    def test_wait_raises_on_timeout(self, mock_hook_class, mock_time):
        """Test waiting raises exception on timeout."""
        mock_hook = MagicMock()
        mock_hook.base_url = "https://api.planalytix.io"
        mock_hook.trigger_sync.return_value = {"job_id": "job_123"}
        mock_hook.get_job.return_value = {"status": "running"}
        mock_hook_class.return_value = mock_hook
        
        # Simulate time passing beyond timeout
        mock_time.time.side_effect = [0, 100, 200, 400, 700, 1000, 1500, 2000, 4000]
        mock_time.sleep = MagicMock()
        
        operator = PlanalytixSyncOperator(
            task_id="test",
            connection_id="conn_abc",
            timeout=3600,
            poll_interval=30,
        )
        
        context = MockContext()
        
        with pytest.raises(MockAirflowException) as exc_info:
            operator.execute(context)
        
        assert "timeout" in str(exc_info.value).lower() or "3600" in str(exc_info.value)


class TestPlanalytixSyncOperatorConflict:
    """Tests for handling sync already in progress."""
    
    @patch("planalytix_provider.operators.sync.PlanalytixHook")
    def test_handles_existing_job(self, mock_hook_class):
        """Test handling of existing job ID from 409 response."""
        mock_hook = MagicMock()
        mock_hook.base_url = "https://api.planalytix.io"
        mock_hook.trigger_sync.return_value = {
            "existing_job_id": "job_existing",
            "error": "Sync already in progress",
        }
        mock_hook.get_job.return_value = {"status": "completed"}
        mock_hook.get_job_results.return_value = {}
        mock_hook_class.return_value = mock_hook
        
        operator = PlanalytixSyncOperator(
            task_id="test",
            connection_id="conn_abc",
        )
        
        context = MockContext()
        result = operator.execute(context)
        
        # Should use existing_job_id if job_id not present
        assert result["job_id"] == "job_existing"
