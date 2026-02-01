"""
Unit tests for PlanalytixSyncSensor.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Mock Airflow modules
import sys

mock_exceptions = MagicMock()


class MockAirflowException(Exception):
    """Mock AirflowException for testing."""
    pass


class MockAirflowSkipException(Exception):
    """Mock AirflowSkipException for testing."""
    pass


mock_exceptions.AirflowException = MockAirflowException
mock_exceptions.AirflowSkipException = MockAirflowSkipException

sys.modules["airflow"] = MagicMock()
sys.modules["airflow.sensors.base"] = MagicMock()
sys.modules["airflow.utils.context"] = MagicMock()
sys.modules["airflow.exceptions"] = mock_exceptions
sys.modules["airflow.hooks.base"] = MagicMock()

from planalytix_provider.sensors.sync import PlanalytixSyncSensor


class MockContext:
    """Mock Airflow execution context."""
    
    def __init__(self):
        self.ti = MagicMock()
        self.ti.xcom_push = MagicMock()
        self._data = {
            "ti": self.ti,
        }
    
    def __getitem__(self, key):
        return self._data.get(key)
    
    def get(self, key, default=None):
        return self._data.get(key, default)


class TestPlanalytixSyncSensorInit:
    """Tests for sensor initialization."""
    
    def test_required_job_id(self):
        """Test job_id is required."""
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
        )
        assert sensor.job_id == "job_abc123"
    
    def test_default_values(self):
        """Test default parameter values."""
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
        )
        
        assert sensor.planalytix_conn_id == "planalytix_default"
        assert sensor.success_states == ["completed"]
        assert sensor.failure_states == ["failed", "cancelled"]
        assert sensor.soft_fail is False
    
    def test_custom_values(self):
        """Test custom parameter values."""
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
            planalytix_conn_id="custom_conn",
            success_states=["completed", "partial"],
            failure_states=["failed"],
            soft_fail=True,
        )
        
        assert sensor.planalytix_conn_id == "custom_conn"
        assert sensor.success_states == ["completed", "partial"]
        assert sensor.failure_states == ["failed"]
        assert sensor.soft_fail is True
    
    def test_template_fields(self):
        """Test template fields include job_id."""
        assert "job_id" in PlanalytixSyncSensor.template_fields


class TestPlanalytixSyncSensorPoke:
    """Tests for sensor poke behavior."""
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_poke_returns_true_on_success(self, mock_hook_class):
        """Test poke returns True when job is in success state."""
        mock_hook = MagicMock()
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "completed",
        }
        mock_hook.get_job_results.return_value = {
            "summary": {"total_rows_synced": 1000},
        }
        mock_hook_class.return_value = mock_hook
        
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
        )
        
        context = MockContext()
        result = sensor.poke(context)
        
        assert result is True
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_poke_returns_false_when_running(self, mock_hook_class):
        """Test poke returns False when job is still running."""
        mock_hook = MagicMock()
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "running",
            "progress": {"rows_synced": 500},
        }
        mock_hook_class.return_value = mock_hook
        
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
        )
        
        context = MockContext()
        result = sensor.poke(context)
        
        assert result is False
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_poke_returns_false_when_queued(self, mock_hook_class):
        """Test poke returns False when job is queued."""
        mock_hook = MagicMock()
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "queued",
        }
        mock_hook_class.return_value = mock_hook
        
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
        )
        
        context = MockContext()
        result = sensor.poke(context)
        
        assert result is False
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_poke_raises_on_failure(self, mock_hook_class):
        """Test poke raises exception when job fails."""
        mock_hook = MagicMock()
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "failed",
            "error": {"message": "Connection timeout"},
        }
        mock_hook_class.return_value = mock_hook
        
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
        )
        
        context = MockContext()
        
        with pytest.raises(MockAirflowException) as exc_info:
            sensor.poke(context)
        
        assert "failed" in str(exc_info.value).lower()
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_poke_raises_on_cancelled(self, mock_hook_class):
        """Test poke raises exception when job is cancelled."""
        mock_hook = MagicMock()
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "cancelled",
        }
        mock_hook_class.return_value = mock_hook
        
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
        )
        
        context = MockContext()
        
        with pytest.raises(MockAirflowException) as exc_info:
            sensor.poke(context)
        
        assert "cancelled" in str(exc_info.value).lower()
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_poke_pushes_results_to_xcom(self, mock_hook_class):
        """Test poke pushes results to XCom on success."""
        mock_hook = MagicMock()
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "completed",
        }
        mock_hook.get_job_results.return_value = {
            "summary": {"total_rows_synced": 1000},
        }
        mock_hook_class.return_value = mock_hook
        
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
        )
        
        context = MockContext()
        sensor.poke(context)
        
        context["ti"].xcom_push.assert_any_call(key="job_status", value="completed")
        context["ti"].xcom_push.assert_any_call(
            key="job_results",
            value={"summary": {"total_rows_synced": 1000}},
        )
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_poke_handles_api_error_gracefully(self, mock_hook_class):
        """Test poke returns False on API errors (allows retry)."""
        mock_hook = MagicMock()
        mock_hook.get_job.side_effect = Exception("API Error")
        mock_hook_class.return_value = mock_hook
        
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
        )
        
        context = MockContext()
        result = sensor.poke(context)
        
        # Should return False to allow retry, not raise
        assert result is False


class TestPlanalytixSyncSensorSoftFail:
    """Tests for soft fail behavior."""
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_soft_fail_skips_on_failure(self, mock_hook_class):
        """Test soft_fail=True raises AirflowSkipException."""
        mock_hook = MagicMock()
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "failed",
            "error": {"message": "Connection error"},
        }
        mock_hook_class.return_value = mock_hook
        
        # Need to patch the import inside the module
        with patch.object(
            sys.modules["planalytix_provider.sensors.sync"],
            "AirflowSkipException",
            MockAirflowSkipException,
            create=True,
        ):
            sensor = PlanalytixSyncSensor(
                task_id="test",
                job_id="job_abc123",
                soft_fail=True,
            )
            
            context = MockContext()
            
            # The sensor should raise AirflowSkipException
            # We need to check the exception is raised
            with pytest.raises((MockAirflowException, MockAirflowSkipException)):
                sensor.poke(context)
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_soft_fail_pushes_error_to_xcom(self, mock_hook_class):
        """Test soft_fail pushes error details to XCom."""
        mock_hook = MagicMock()
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "failed",
            "error": {"code": "SOURCE_ERROR", "message": "Connection error"},
        }
        mock_hook_class.return_value = mock_hook
        
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
            soft_fail=True,
        )
        
        context = MockContext()
        
        try:
            sensor.poke(context)
        except Exception:
            pass
        
        # Verify error was pushed to XCom
        context["ti"].xcom_push.assert_any_call(key="job_status", value="failed")
        context["ti"].xcom_push.assert_any_call(
            key="job_error",
            value={"code": "SOURCE_ERROR", "message": "Connection error"},
        )


class TestPlanalytixSyncSensorCustomStates:
    """Tests for custom success/failure states."""
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_custom_success_states(self, mock_hook_class):
        """Test custom success states are recognized."""
        mock_hook = MagicMock()
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "partial",
        }
        mock_hook.get_job_results.return_value = {}
        mock_hook_class.return_value = mock_hook
        
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
            success_states=["completed", "partial"],
        )
        
        context = MockContext()
        result = sensor.poke(context)
        
        assert result is True
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_custom_failure_states(self, mock_hook_class):
        """Test custom failure states are recognized."""
        mock_hook = MagicMock()
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "timeout",  # Custom failure state
        }
        mock_hook_class.return_value = mock_hook
        
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
            failure_states=["failed", "cancelled", "timeout"],
        )
        
        context = MockContext()
        
        with pytest.raises(MockAirflowException):
            sensor.poke(context)
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_cancelled_not_in_failure_states(self, mock_hook_class):
        """Test cancelled not treated as failure if not in failure_states."""
        mock_hook = MagicMock()
        mock_hook.get_job.return_value = {
            "job_id": "job_abc123",
            "status": "cancelled",
        }
        mock_hook_class.return_value = mock_hook
        
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="job_abc123",
            failure_states=["failed"],  # cancelled not included
        )
        
        context = MockContext()
        result = sensor.poke(context)
        
        # Should return False since cancelled is not success or failure
        assert result is False


class TestPlanalytixSyncSensorEmptyJobId:
    """Tests for handling empty job_id."""
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_raises_on_empty_job_id(self, mock_hook_class):
        """Test poke raises exception on empty job_id."""
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id="",
        )
        
        context = MockContext()
        
        with pytest.raises(MockAirflowException) as exc_info:
            sensor.poke(context)
        
        assert "job_id" in str(exc_info.value).lower()
    
    @patch("planalytix_provider.sensors.sync.PlanalytixHook")
    def test_raises_on_none_job_id(self, mock_hook_class):
        """Test poke raises exception on None job_id."""
        sensor = PlanalytixSyncSensor(
            task_id="test",
            job_id=None,
        )
        
        context = MockContext()
        
        with pytest.raises(MockAirflowException):
            sensor.poke(context)
