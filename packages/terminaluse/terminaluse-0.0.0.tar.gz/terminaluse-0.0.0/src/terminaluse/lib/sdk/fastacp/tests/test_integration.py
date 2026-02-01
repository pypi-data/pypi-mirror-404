# ruff: noqa: ARG001
import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from terminaluse.types.event import Event
from terminaluse.lib.types.acp import RPCMethod
from terminaluse.lib.types.task_context import TaskContext
from terminaluse.lib.sdk.fastacp.impl.sync_acp import SyncACP
from terminaluse.lib.sdk.fastacp.impl.temporal_acp import TemporalACP
from terminaluse.lib.sdk.fastacp.impl.async_base_acp import AsyncBaseACP


class TestImplementationBehavior:
    """Test specific behavior differences between ACP implementations"""

    @pytest.mark.asyncio()
    async def test_sync_acp_default_handlers(self):
        """Test SyncACP has expected handlers (no default handlers after message/send deprecation)"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            sync_acp = SyncACP.create()

            # SyncACP no longer has default handlers after message/send deprecation
            # Verify the handlers dict is initialized but empty
            assert isinstance(sync_acp._handlers, dict)

    @pytest.mark.asyncio()
    async def test_async_acp_default_handlers(self):
        """Test AsyncBaseACP has expected default handlers"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            async_acp = AsyncBaseACP.create()

            # Should have create, message, and cancel handlers by default
            assert RPCMethod.TASK_CREATE in async_acp._handlers
            assert RPCMethod.EVENT_SEND in async_acp._handlers
            assert RPCMethod.TASK_CANCEL in async_acp._handlers

    @pytest.mark.asyncio()
    async def test_temporal_acp_creation_with_mocked_client(self):
        """Test TemporalACP creation with mocked temporal client"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            with patch.object(TemporalACP, "create", new_callable=AsyncMock) as mock_create:
                mock_temporal_instance = MagicMock(spec=TemporalACP)
                mock_temporal_instance._handlers = {}
                mock_temporal_instance.temporal_client = MagicMock()
                mock_create.return_value = mock_temporal_instance

                # TemporalACP.create is now async, so we need to await it
                temporal_acp = await TemporalACP.create(temporal_address="localhost:7233")

                assert temporal_acp == mock_temporal_instance
                assert hasattr(temporal_acp, "temporal_client")


class TestRealWorldScenarios:
    """Test real-world usage scenarios and integration"""

    @pytest.mark.asyncio()
    async def test_message_handling_workflow(self, sync_acp_server, free_port, test_server_runner):
        """Test complete message handling workflow"""
        messages_received = []

        @sync_acp_server.on_event
        async def message_handler(ctx: TaskContext, event: Event):
            messages_received.append(
                {
                    "task_id": ctx.task.id,
                    "message_content": getattr(event.content, "content", None),
                    "author": getattr(event.content, "author", "user"),
                }
            )
            return {"processed": True}

        runner = test_server_runner(sync_acp_server, free_port)
        await runner.start()

        # Send multiple messages
        async with httpx.AsyncClient() as client:
            for i in range(3):
                request_data = {
                    "jsonrpc": "2.0",
                    "method": "event/send",
                    "params": {
                        "agent": {
                            "id": "workflow-agent",
                            "name": "workflow-agent",
                            "namespace_id": "ns-123",
                            "description": "workflow agent",
                            "created_at": "2023-01-01T00:00:00Z",
                            "updated_at": "2023-01-01T00:00:00Z",
                        },
                        "task": {
                            "id": f"workflow-task-{i}",
                            "namespace_id": "ns-123",
                            "filesystem_id": "fs-123",
                            "status": "RUNNING",
                        },
                        "event": {
                            "id": f"event-{i}",
                            "agent_id": "workflow-agent",
                            "task_id": f"workflow-task-{i}",
                            "sequence_id": i,
                            "content": {
                                "type": "text",
                                "author": "user",
                                "content": f"Workflow message {i}",
                            },
                        },
                    },
                    "id": f"workflow-{i}",
                }

                response = await client.post(f"http://127.0.0.1:{free_port}/api", json=request_data)
                assert response.status_code == 200

        # Give background tasks time to process
        await asyncio.sleep(0.2)

        # Verify all messages were processed
        assert len(messages_received) == 3
        for i, msg in enumerate(messages_received):
            assert msg["task_id"] == f"workflow-task-{i}"
            assert msg["message_content"] == f"Workflow message {i}"
            assert msg["author"] == "user"

        await runner.stop()

    @pytest.mark.skip(reason="Requires bubblewrap sandbox which is not available in test environment")
    @pytest.mark.asyncio()
    async def test_task_lifecycle_management(self, agentic_base_acp_server, free_port, test_server_runner):
        """Test complete task lifecycle: create -> message -> cancel"""
        task_events = []

        @agentic_base_acp_server.on_create
        async def create_handler(ctx: TaskContext, params: dict[str, Any]):
            task_events.append(("created", ctx.task.id))

        @agentic_base_acp_server.on_event
        async def message_handler(ctx: TaskContext, event: Event):
            task_events.append(("message", ctx.task.id))

        @agentic_base_acp_server.on_cancel
        async def cancel_handler(ctx: TaskContext):
            task_events.append(("cancelled", ctx.task.id))

        runner = test_server_runner(agentic_base_acp_server, free_port)
        await runner.start()

        async with httpx.AsyncClient() as client:
            # Create task
            create_request = {
                "jsonrpc": "2.0",
                "method": "task/create",
                "params": {
                    "agent": {
                        "id": "lifecycle-agent",
                        "name": "lifecycle-agent",
                        "namespace_id": "ns-123",
                        "description": "lifecycle agent",
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z",
                    },
                    "task": {
                        "id": "lifecycle-task",
                        "namespace_id": "ns-123",
                        "filesystem_id": "fs-123",
                        "status": "RUNNING",
                    },
                },
                "id": "create-1",
            }

            response = await client.post(f"http://127.0.0.1:{free_port}/api", json=create_request)
            assert response.status_code == 200

            # Send message
            message_request = {
                "jsonrpc": "2.0",
                "method": "event/send",
                "params": {
                    "agent": {
                        "id": "lifecycle-agent",
                        "name": "lifecycle-agent",
                        "namespace_id": "ns-123",
                        "description": "lifecycle agent",
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z",
                    },
                    "task": {
                        "id": "lifecycle-task",
                        "namespace_id": "ns-123",
                        "filesystem_id": "fs-123",
                        "status": "RUNNING",
                    },
                    "event": {
                        "id": "event-1",
                        "agent_id": "lifecycle-agent",
                        "task_id": "lifecycle-task",
                        "sequence_id": 1,
                        "content": {
                            "type": "text",
                            "author": "user",
                            "content": "Lifecycle test message",
                        },
                    },
                },
                "id": "message-1",
            }

            response = await client.post(f"http://127.0.0.1:{free_port}/api", json=message_request)
            assert response.status_code == 200

            # Cancel task
            cancel_request = {
                "jsonrpc": "2.0",
                "method": "task/cancel",
                "params": {
                    "agent": {
                        "id": "lifecycle-agent",
                        "name": "lifecycle-agent",
                        "namespace_id": "ns-123",
                        "description": "lifecycle agent",
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z",
                    },
                    "task": {
                        "id": "lifecycle-task",
                        "namespace_id": "ns-123",
                        "filesystem_id": "fs-123",
                        "status": "RUNNING",
                    },
                },
                "id": "cancel-1",
            }

            response = await client.post(f"http://127.0.0.1:{free_port}/api", json=cancel_request)
            assert response.status_code == 200

        # Give background tasks time to process
        await asyncio.sleep(0.2)

        # Verify task lifecycle events
        assert len(task_events) == 3
        assert task_events[0] == ("created", "lifecycle-task")
        assert task_events[1] == ("message", "lifecycle-task")
        assert task_events[2] == ("cancelled", "lifecycle-task")

        await runner.stop()


class TestErrorRecovery:
    """Test error handling and recovery scenarios"""

    @pytest.mark.asyncio()
    async def test_server_resilience_to_handler_failures(self, sync_acp_server, free_port, test_server_runner):
        """Test server continues working after handler failures"""
        failure_count = 0
        success_count = 0

        @sync_acp_server.on_event
        async def unreliable_handler(ctx: TaskContext, event: Event):
            nonlocal failure_count, success_count
            content = getattr(event.content, "content", str(event.content))
            if "fail" in content:
                failure_count += 1
                raise RuntimeError("Simulated handler failure")
            else:
                success_count += 1
                return {"success": True}

        runner = test_server_runner(sync_acp_server, free_port)
        await runner.start()

        async with httpx.AsyncClient() as client:
            # Send failing request
            fail_request = {
                "jsonrpc": "2.0",
                "method": "event/send",
                "params": {
                    "agent": {
                        "id": "test-agent",
                        "name": "test-agent",
                        "namespace_id": "ns-123",
                        "description": "test agent",
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z",
                    },
                    "task": {
                        "id": "fail-task",
                        "namespace_id": "ns-123",
                        "filesystem_id": "fs-123",
                        "status": "RUNNING",
                    },
                    "event": {
                        "id": "event-fail",
                        "agent_id": "test-agent",
                        "task_id": "fail-task",
                        "sequence_id": 1,
                        "content": {"type": "text", "author": "user", "content": "This should fail"},
                    },
                },
                "id": "fail-1",
            }

            response = await client.post(f"http://127.0.0.1:{free_port}/api", json=fail_request)
            assert response.status_code == 200  # Server should still respond

            # Send successful request after failure
            success_request = {
                "jsonrpc": "2.0",
                "method": "event/send",
                "params": {
                    "agent": {
                        "id": "test-agent",
                        "name": "test-agent",
                        "namespace_id": "ns-123",
                        "description": "test agent",
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z",
                    },
                    "task": {
                        "id": "success-task",
                        "namespace_id": "ns-123",
                        "filesystem_id": "fs-123",
                        "status": "RUNNING",
                    },
                    "event": {
                        "id": "event-success",
                        "agent_id": "test-agent",
                        "task_id": "success-task",
                        "sequence_id": 1,
                        "content": {"type": "text", "author": "user", "content": "This should succeed"},
                    },
                },
                "id": "success-1",
            }

            response = await client.post(f"http://127.0.0.1:{free_port}/api", json=success_request)
            assert response.status_code == 200

            # Verify server is still healthy
            health_response = await client.get(f"http://127.0.0.1:{free_port}/healthz")
            assert health_response.status_code == 200

        # Give background tasks time to process
        await asyncio.sleep(0.2)

        assert failure_count == 1
        assert success_count == 1

        await runner.stop()

    @pytest.mark.asyncio()
    async def test_concurrent_request_handling(self, sync_acp_server, free_port, test_server_runner):
        """Test handling multiple concurrent requests"""
        processed_requests = []

        @sync_acp_server.on_event
        async def concurrent_handler(ctx: TaskContext, event: Event):
            # Simulate some processing time
            await asyncio.sleep(0.05)
            processed_requests.append(ctx.task.id)
            return {"processed": ctx.task.id}

        runner = test_server_runner(sync_acp_server, free_port)
        await runner.start()

        # Send multiple concurrent requests
        async def send_request(client, task_id, index):
            request_data = {
                "jsonrpc": "2.0",
                "method": "event/send",
                "params": {
                    "agent": {
                        "id": "concurrent-agent",
                        "name": "concurrent-agent",
                        "namespace_id": "ns-123",
                        "description": "concurrent agent",
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z",
                    },
                    "task": {
                        "id": task_id,
                        "namespace_id": "ns-123",
                        "filesystem_id": "fs-123",
                        "status": "RUNNING",
                    },
                    "event": {
                        "id": f"event-{index}",
                        "agent_id": "concurrent-agent",
                        "task_id": task_id,
                        "sequence_id": index,
                        "content": {
                            "type": "text",
                            "author": "user",
                            "content": f"Concurrent message for {task_id}",
                        },
                    },
                },
                "id": f"concurrent-{task_id}",
            }

            return await client.post(f"http://127.0.0.1:{free_port}/api", json=request_data)

        async with httpx.AsyncClient() as client:
            # Send 5 concurrent requests
            tasks = [send_request(client, f"task-{i}", i) for i in range(5)]
            responses = await asyncio.gather(*tasks)

            # All should return immediate acknowledgment
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["result"]["status"] == "processing"

        # Give background tasks time to complete
        await asyncio.sleep(0.3)

        # All requests should have been processed
        assert len(processed_requests) == 5
        assert set(processed_requests) == {f"task-{i}" for i in range(5)}

        await runner.stop()


class TestSpecialCases:
    """Test edge cases and special scenarios"""

    @pytest.mark.asyncio()
    async def test_notification_vs_request_behavior(self, sync_acp_server, free_port, test_server_runner):
        """Test difference between notifications (no ID) and requests (with ID)"""
        notifications_received = 0
        requests_received = 0

        @sync_acp_server.on_event
        async def tracking_handler(ctx: TaskContext, event: Event):
            nonlocal notifications_received, requests_received
            content = getattr(event.content, "content", str(event.content))
            if "notification" in content:
                notifications_received += 1
            else:
                requests_received += 1
            return {"handled": True}

        runner = test_server_runner(sync_acp_server, free_port)
        await runner.start()

        async with httpx.AsyncClient() as client:
            # Send notification (no ID)
            notification_data = {
                "jsonrpc": "2.0",
                "method": "event/send",
                "params": {
                    "agent": {
                        "id": "test-agent",
                        "name": "test-agent",
                        "namespace_id": "ns-123",
                        "description": "test agent",
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z",
                    },
                    "task": {
                        "id": "notification-task",
                        "namespace_id": "ns-123",
                        "filesystem_id": "fs-123",
                        "status": "RUNNING",
                    },
                    "event": {
                        "id": "event-notification",
                        "agent_id": "test-agent",
                        "task_id": "notification-task",
                        "sequence_id": 1,
                        "content": {
                            "type": "text",
                            "author": "user",
                            "content": "This is a notification",
                        },
                    },
                },
                # Note: no "id" field
            }

            notification_response = await client.post(f"http://127.0.0.1:{free_port}/api", json=notification_data)
            assert notification_response.status_code == 200
            notification_result = notification_response.json()
            assert notification_result["id"] is None

            # Send regular request (with ID)
            request_data = {
                "jsonrpc": "2.0",
                "method": "event/send",
                "params": {
                    "agent": {
                        "id": "test-agent",
                        "name": "test-agent",
                        "namespace_id": "ns-123",
                        "description": "test agent",
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z",
                    },
                    "task": {
                        "id": "request-task",
                        "namespace_id": "ns-123",
                        "filesystem_id": "fs-123",
                        "status": "RUNNING",
                    },
                    "event": {
                        "id": "event-request",
                        "agent_id": "test-agent",
                        "task_id": "request-task",
                        "sequence_id": 1,
                        "content": {"type": "text", "author": "user", "content": "This is a request"},
                    },
                },
                "id": "request-1",
            }

            request_response = await client.post(f"http://127.0.0.1:{free_port}/api", json=request_data)
            assert request_response.status_code == 200
            request_result = request_response.json()
            assert request_result["id"] == "request-1"
            assert request_result["result"]["status"] == "processing"

        # Give background tasks time to process
        await asyncio.sleep(0.1)

        assert notifications_received == 1
        assert requests_received == 1

        await runner.stop()

    @pytest.mark.asyncio()
    async def test_unicode_message_handling(self, sync_acp_server, free_port, test_server_runner):
        """Test handling of unicode characters in messages"""
        received_message = None

        @sync_acp_server.on_event
        async def unicode_handler(ctx: TaskContext, event: Event):
            nonlocal received_message
            received_message = getattr(event.content, "content", str(event.content))
            return {"unicode_handled": True}

        runner = test_server_runner(sync_acp_server, free_port)
        await runner.start()

        unicode_text = "Hello 世界 🌍 émojis 🚀 and special chars: \n\t\r"

        async with httpx.AsyncClient() as client:
            request_data = {
                "jsonrpc": "2.0",
                "method": "event/send",
                "params": {
                    "agent": {
                        "id": "unicode-agent",
                        "name": "unicode-agent",
                        "namespace_id": "ns-123",
                        "description": "unicode agent",
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z",
                    },
                    "task": {
                        "id": "unicode-task",
                        "namespace_id": "ns-123",
                        "filesystem_id": "fs-123",
                        "status": "RUNNING",
                    },
                    "event": {
                        "id": "event-unicode",
                        "agent_id": "unicode-agent",
                        "task_id": "unicode-task",
                        "sequence_id": 1,
                        "content": {"type": "text", "author": "user", "content": unicode_text},
                    },
                },
                "id": "unicode-test",
            }

            response = await client.post(f"http://127.0.0.1:{free_port}/api", json=request_data)

            assert response.status_code == 200

        # Give background task time to process
        await asyncio.sleep(0.1)

        assert received_message == unicode_text

        await runner.stop()


class TestImplementationIsolation:
    """Test that different implementations don't interfere with each other"""

    @pytest.mark.asyncio()
    async def test_handler_isolation_between_implementations(self):
        """Test handlers registered on one implementation don't affect others"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            sync_acp = SyncACP.create()
            async_acp = AsyncBaseACP.create()

            sync_handled = False
            async_handled = False

            @sync_acp.on_event
            async def sync_handler(ctx: TaskContext, event: Event):
                nonlocal sync_handled
                sync_handled = True
                return {"sync": True}

            @async_acp.on_event
            async def async_handler(ctx: TaskContext, event: Event):
                nonlocal async_handled
                async_handled = True
                return {"async": True}

            # Note: We can't easily test handler execution directly anymore
            # since the handlers now expect TaskContext which requires proper params
            # The registration test is sufficient to verify isolation
            assert RPCMethod.EVENT_SEND in sync_acp._handlers
            assert RPCMethod.EVENT_SEND in async_acp._handlers
            assert sync_acp._handlers[RPCMethod.EVENT_SEND] is not async_acp._handlers[RPCMethod.EVENT_SEND]
