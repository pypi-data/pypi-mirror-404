"""
Unit tests for handlers.py automatic job status polling.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from mcp_proxy_adapter.api.handlers import execute_command, _poll_job_status
from mcp_proxy_adapter.core.errors import (
    MethodNotFoundError,
    InternalError,
    ValidationError,
    TimeoutError,
)
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    QueueJobStatus,
    QueueJobResult,
    QueueJobError,
)


class TestExecuteCommandAutoPoll:
    """Test suite for execute_command with automatic polling."""

    @pytest.mark.asyncio
    async def test_execute_command_with_poll_interval_returns_final_result(
        self,
    ) -> None:
        """Test that command with poll_interval returns final result after polling."""
        # Mock command class with use_queue=True
        mock_command_class = MagicMock()
        mock_command_class.use_queue = True
        mock_command_class.run = AsyncMock()

        # Mock registry
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            # Mock queue manager
            with patch(
                "mcp_proxy_adapter.integrations.queuemgr_integration.get_global_queue_manager"
            ) as mock_get_qm:
                mock_queue_manager = AsyncMock()
                mock_get_qm.return_value = mock_queue_manager

                # Mock add_job
                mock_queue_manager.add_job = AsyncMock()

                # Mock get_job_status to simulate job completion
                job_results = [
                    QueueJobResult(
                        job_id="test-job-123",
                        status=QueueJobStatus.PENDING,
                        progress=0,
                        description="Starting",
                    ),
                    QueueJobResult(
                        job_id="test-job-123",
                        status=QueueJobStatus.RUNNING,
                        progress=50,
                        description="Processing",
                    ),
                    QueueJobResult(
                        job_id="test-job-123",
                        status=QueueJobStatus.COMPLETED,
                        progress=100,
                        description="Done",
                        result={"data": "test result"},
                    ),
                ]
                mock_queue_manager.get_job_status = AsyncMock(side_effect=job_results)

                # Mock hooks
                with patch("mcp_proxy_adapter.commands.hooks.hooks") as mock_hooks:
                    mock_hooks.get_auto_import_modules.return_value = []

                    # Mock asyncio.create_task
                    with patch("asyncio.create_task") as mock_create_task:
                        mock_task = MagicMock()
                        mock_create_task.return_value = mock_task

                        # Mock uuid
                        with patch("uuid.uuid4") as mock_uuid:
                            mock_uuid_obj = MagicMock()
                            mock_uuid_obj.__str__ = MagicMock(
                                return_value="test-job-123"
                            )
                            mock_uuid.return_value = mock_uuid_obj

                            # Mock asyncio.sleep to speed up test
                            async def mock_sleep_func(delay):
                                pass
                            
                            with patch("asyncio.sleep", side_effect=mock_sleep_func):
                                # Execute command with poll_interval
                                result = await execute_command(
                                    command_name="test_command",
                                    params={
                                        "param1": "value1",
                                        "poll_interval": 0.1,
                                    },
                                )

                                # Verify result contains final job result
                                assert result["success"] is True
                                assert result["job_id"] == "test-job-123"
                                assert result["status"] == QueueJobStatus.COMPLETED
                                assert result["result"] == {"data": "test result"}
                                assert result["progress"] == 100

                                # Verify add_job was called
                                mock_queue_manager.add_job.assert_called_once()

                                # Verify get_job_status was called multiple times
                                assert mock_queue_manager.get_job_status.call_count >= 2

    @pytest.mark.asyncio
    async def test_execute_command_with_poll_interval_zero_returns_job_id(
        self,
    ) -> None:
        """Test that poll_interval=0 returns job_id (no polling)."""
        # Mock command class with use_queue=True
        mock_command_class = MagicMock()
        mock_command_class.use_queue = True

        # Mock registry
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            # Mock queue manager
            with patch(
                "mcp_proxy_adapter.integrations.queuemgr_integration.get_global_queue_manager"
            ) as mock_get_qm:
                mock_queue_manager = AsyncMock()
                mock_get_qm.return_value = mock_queue_manager

                # Mock add_job
                mock_queue_manager.add_job = AsyncMock()

                # Mock hooks
                with patch("mcp_proxy_adapter.commands.hooks.hooks") as mock_hooks:
                    mock_hooks.get_auto_import_modules.return_value = []

                    # Mock asyncio.create_task
                    with patch("asyncio.create_task") as mock_create_task:
                        mock_task = MagicMock()
                        mock_create_task.return_value = mock_task

                        # Mock uuid
                        with patch("uuid.uuid4") as mock_uuid:
                            mock_uuid_obj = MagicMock()
                            mock_uuid_obj.__str__ = MagicMock(
                                return_value="test-job-123"
                            )
                            mock_uuid.return_value = mock_uuid_obj

                            # Execute command with poll_interval=0
                            result = await execute_command(
                                command_name="test_command",
                                params={"poll_interval": 0},
                            )

                            # Verify result contains job_id (no polling)
                            assert result["success"] is True
                            assert result["job_id"] == "test-job-123"
                            assert result["status"] == "pending"

                            # Verify get_job_status was NOT called (no polling)
                            mock_queue_manager.get_job_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_command_with_invalid_poll_interval_raises_error(
        self,
    ) -> None:
        """Test that invalid poll_interval (< 0) raises ValidationError."""
        # Mock command class with use_queue=True
        mock_command_class = MagicMock()
        mock_command_class.use_queue = True

        # Mock registry
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            # Execute command with invalid poll_interval
            with pytest.raises(ValidationError, match="poll_interval must be >= 0"):
                await execute_command(
                    command_name="test_command",
                    params={"poll_interval": -1},
                )

    @pytest.mark.asyncio
    async def test_execute_command_with_invalid_max_wait_time_raises_error(
        self,
    ) -> None:
        """Test that invalid max_wait_time raises ValidationError."""
        # Mock command class with use_queue=True
        mock_command_class = MagicMock()
        mock_command_class.use_queue = True

        # Mock registry
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            # Execute command with invalid max_wait_time
            with pytest.raises(ValidationError, match="max_wait_time must be"):
                await execute_command(
                    command_name="test_command",
                    params={"poll_interval": 1.0, "max_wait_time": 0},
                )

    @pytest.mark.asyncio
    async def test_poll_job_status_timeout(self) -> None:
        """Test that polling times out when max_wait_time is exceeded."""
        # Mock queue manager
        mock_queue_manager = AsyncMock()

        # Mock get_job_status to always return running
        mock_queue_manager.get_job_status = AsyncMock(
            return_value=QueueJobResult(
                job_id="test-job-123",
                status=QueueJobStatus.RUNNING,
                progress=50,
                description="Still running",
            )
        )

        # Mock logger
        mock_logger = MagicMock()

        # Mock time.time to simulate timeout
        with patch("time.time") as mock_time:
            # Start time
            mock_time.side_effect = [0.0, 0.5, 1.0, 1.5, 2.0]

            # Mock asyncio.sleep
            async def mock_sleep_func(delay):
                pass
            
            with patch("asyncio.sleep", side_effect=mock_sleep_func):
                # Poll with max_wait_time=1.0
                with pytest.raises(TimeoutError, match="Polling timeout"):
                    await _poll_job_status(
                        queue_manager=mock_queue_manager,
                        job_id="test-job-123",
                        command_name="test_command",
                        poll_interval=0.1,
                        max_wait_time=1.0,
                        logger=mock_logger,
                    )

    @pytest.mark.asyncio
    async def test_poll_job_status_completed(self) -> None:
        """Test that polling returns result when job completes."""
        # Mock queue manager
        mock_queue_manager = AsyncMock()

        # Mock get_job_status to return completed
        mock_queue_manager.get_job_status = AsyncMock(
            return_value=QueueJobResult(
                job_id="test-job-123",
                status=QueueJobStatus.COMPLETED,
                progress=100,
                description="Done",
                result={"data": "test result"},
            )
        )

        # Mock logger
        mock_logger = MagicMock()

        # Mock time.time
        with patch("time.time", return_value=0.0):
            # Mock asyncio.sleep
            async def mock_sleep_func(delay):
                pass
            
            with patch("asyncio.sleep", side_effect=mock_sleep_func):
                # Poll
                result = await _poll_job_status(
                    queue_manager=mock_queue_manager,
                    job_id="test-job-123",
                    command_name="test_command",
                    poll_interval=0.1,
                    max_wait_time=None,
                    logger=mock_logger,
                )

                # Verify result
                assert result["success"] is True
                assert result["status"] == QueueJobStatus.COMPLETED
                assert result["result"] == {"data": "test result"}

    @pytest.mark.asyncio
    async def test_poll_job_status_failed(self) -> None:
        """Test that polling returns error when job fails."""
        # Mock queue manager
        mock_queue_manager = AsyncMock()

        # Mock get_job_status to return failed
        mock_queue_manager.get_job_status = AsyncMock(
            return_value=QueueJobResult(
                job_id="test-job-123",
                status=QueueJobStatus.FAILED,
                progress=0,
                description="Error occurred",
                error="Test error",
            )
        )

        # Mock logger
        mock_logger = MagicMock()

        # Mock time.time
        with patch("time.time", return_value=0.0):
            # Mock asyncio.sleep
            async def mock_sleep_func(delay):
                pass
            
            with patch("asyncio.sleep", side_effect=mock_sleep_func):
                # Poll
                result = await _poll_job_status(
                    queue_manager=mock_queue_manager,
                    job_id="test-job-123",
                    command_name="test_command",
                    poll_interval=0.1,
                    max_wait_time=None,
                    logger=mock_logger,
                )

                # Verify result
                assert result["success"] is False
                assert result["status"] == QueueJobStatus.FAILED
                assert result["error"] == "Test error"

    @pytest.mark.asyncio
    async def test_poll_job_status_job_not_found(self) -> None:
        """Test that polling raises error when job is not found."""
        # Mock queue manager
        mock_queue_manager = AsyncMock()

        # Mock get_job_status to raise QueueJobError
        mock_queue_manager.get_job_status = AsyncMock(
            side_effect=QueueJobError("test-job-123", "Job not found")
        )

        # Mock logger
        mock_logger = MagicMock()

        # Mock time.time
        with patch("time.time", return_value=0.0):
            # Mock asyncio.sleep
            async def mock_sleep_func(delay):
                pass
            
            with patch("asyncio.sleep", side_effect=mock_sleep_func):
                # Poll should raise InternalError
                with pytest.raises(InternalError, match="Failed to get job status"):
                    await _poll_job_status(
                        queue_manager=mock_queue_manager,
                        job_id="test-job-123",
                        command_name="test_command",
                        poll_interval=0.1,
                        max_wait_time=None,
                        logger=mock_logger,
                    )

    @pytest.mark.asyncio
    async def test_execute_command_without_poll_interval_returns_job_id(
        self,
    ) -> None:
        """Test that command without poll_interval returns job_id (backward compatibility)."""
        # Mock command class with use_queue=True
        mock_command_class = MagicMock()
        mock_command_class.use_queue = True

        # Mock registry
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            # Mock queue manager
            with patch(
                "mcp_proxy_adapter.integrations.queuemgr_integration.get_global_queue_manager"
            ) as mock_get_qm:
                mock_queue_manager = AsyncMock()
                mock_get_qm.return_value = mock_queue_manager

                # Mock add_job
                mock_queue_manager.add_job = AsyncMock()

                # Mock hooks
                with patch("mcp_proxy_adapter.commands.hooks.hooks") as mock_hooks:
                    mock_hooks.get_auto_import_modules.return_value = []

                    # Mock asyncio.create_task
                    with patch("asyncio.create_task") as mock_create_task:
                        mock_task = MagicMock()
                        mock_create_task.return_value = mock_task

                        # Mock uuid
                        with patch("uuid.uuid4") as mock_uuid:
                            mock_uuid_obj = MagicMock()
                            mock_uuid_obj.__str__ = MagicMock(
                                return_value="test-job-123"
                            )
                            mock_uuid.return_value = mock_uuid_obj

                            # Execute command without poll_interval
                            result = await execute_command(
                                command_name="test_command",
                                params={"param1": "value1"},
                            )

                            # Verify result contains job_id (backward compatibility)
                            assert result["success"] is True
                            assert result["job_id"] == "test-job-123"
                            assert result["status"] == "pending"

                            # Verify add_job was called
                            mock_queue_manager.add_job.assert_called_once()

                            # Verify get_job_status was NOT called (no polling)
                            mock_queue_manager.get_job_status.assert_not_called()

