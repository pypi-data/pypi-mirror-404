# ruff: noqa: ARG001
import asyncio
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from terminaluse.types.event import Event
from terminaluse.lib.types.acp import RPCMethod
from terminaluse.lib.types.task_context import TaskContext
from terminaluse.lib.sdk.fastacp.base.base_acp_server import BaseACPServer


class TestBaseACPServerInitialization:
    """Test BaseACPServer initialization and setup"""

    def test_base_acp_server_init(self):
        """Test BaseACPServer initialization sets up routes correctly"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            server = BaseACPServer()

            # Check that FastAPI routes are set up
            routes = [route.path for route in server.routes]  # type: ignore[attr-defined]
            assert "/healthz" in routes
            assert "/api" in routes

            # Check that handlers dict is initialized
            assert hasattr(server, "_handlers")
            assert isinstance(server._handlers, dict)

    def test_base_acp_server_create_classmethod(self):
        """Test BaseACPServer.create() class method"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            server = BaseACPServer.create()

            assert isinstance(server, BaseACPServer)
            assert hasattr(server, "_handlers")

    def test_lifespan_function_setup(self):
        """Test that lifespan function is properly configured"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            server = BaseACPServer()

            # Check that lifespan is configured
            assert server.router.lifespan_context is not None


class TestHealthCheckEndpoint:
    """Test health check endpoint functionality"""

    def test_health_check_endpoint(self, base_acp_server):
        """Test GET /healthz endpoint returns correct response"""
        client = TestClient(base_acp_server)

        response = client.get("/healthz")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_health_check_content_type(self, base_acp_server):
        """Test health check returns JSON content type"""
        client = TestClient(base_acp_server)

        response = client.get("/healthz")

        assert response.headers["content-type"] == "application/json"


class TestJSONRPCEndpointCore:
    """Test core JSON-RPC endpoint functionality"""

    def test_jsonrpc_endpoint_exists(self, base_acp_server):
        """Test POST /api endpoint exists"""
        client = TestClient(base_acp_server)

        # Send a basic request to check endpoint exists
        response = client.post("/api", json={})

        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_jsonrpc_malformed_request(self, base_acp_server):
        """Test JSON-RPC endpoint handles malformed requests"""
        client = TestClient(base_acp_server)

        # Send malformed JSON
        response = client.post("/api", json={"invalid": "request"})

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["jsonrpc"] == "2.0"

    def test_jsonrpc_method_not_found(self, base_acp_server):
        """Test JSON-RPC method not found error"""
        client = TestClient(base_acp_server)

        request = {
            "jsonrpc": "2.0",
            "method": "nonexistent/method",
            "params": {},
            "id": "test-1",
        }

        response = client.post("/api", json=request)

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found
        assert data["id"] == "test-1"

    def test_jsonrpc_valid_request_structure(self, base_acp_server):
        """Test JSON-RPC request parsing with valid structure"""
        client = TestClient(base_acp_server)

        # Add a mock handler for testing
        async def mock_handler(params):
            return {"status": "success"}

        base_acp_server._handlers[RPCMethod.EVENT_SEND] = mock_handler

        request = {
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
                    "id": "test-task",
                    "namespace_id": "ns-123",
                    "filesystem_id": "fs-123",
                    "status": "RUNNING",
                },
                "event": {
                    "id": "event-123",
                    "agent_id": "test-agent",
                    "task_id": "test-task",
                    "sequence_id": 1,
                    "created_at": "2023-01-01T00:00:00Z",
                    "content": {
                        "type": "text",
                        "author": "user",
                        "content": "test message",
                    },
                },
            },
            "id": "test-1",
        }

        response = client.post("/api", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-1"
        # Should return immediate acknowledgment
        assert data["result"]["status"] == "processing"


class TestHandlerRegistration:
    """Test handler registration and management"""

    def test_on_event_decorator(self):
        """Test on_event decorator registration"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            server = BaseACPServer()

            @server.on_event
            async def test_handler(ctx: TaskContext, event: Event):
                return {"test": "response"}

            # Check handler is registered
            assert RPCMethod.EVENT_SEND in server._handlers
            assert server._handlers[RPCMethod.EVENT_SEND] is not None

    def test_on_cancel_decorator(self):
        """Test on_cancel decorator registration"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            server = BaseACPServer()

            @server.on_cancel
            async def test_handler(ctx: TaskContext):
                return {"test": "response"}

            # Check handler is registered
            assert RPCMethod.TASK_CANCEL in server._handlers
            assert server._handlers[RPCMethod.TASK_CANCEL] is not None

    def test_on_create_decorator(self):
        """Test on_create decorator registration"""
        with patch.dict("os.environ", {"TERMINALUSE_BASE_URL": ""}):
            server = BaseACPServer()

            @server.on_create
            async def test_handler(ctx: TaskContext, params: dict[str, Any]):
                return {"test": "response"}

            # Check handler is registered
            assert RPCMethod.TASK_CREATE in server._handlers
            assert server._handlers[RPCMethod.TASK_CREATE] is not None


class TestBackgroundProcessing:
    """Test background processing functionality"""

    @pytest.mark.asyncio
    async def test_notification_processing(self, async_base_acp_server):
        """Test notification processing (requests with no ID)"""
        # Add a mock handler
        handler_called = False
        received_params = None

        async def mock_handler(params):
            nonlocal handler_called, received_params
            handler_called = True
            received_params = params
            return {"status": "processed"}

        async_base_acp_server._handlers[RPCMethod.EVENT_SEND] = mock_handler

        client = TestClient(async_base_acp_server)

        request = {
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
                    "id": "test-task",
                    "namespace_id": "ns-123",
                    "filesystem_id": "fs-123",
                    "status": "RUNNING",
                },
                "event": {
                    "id": "event-123",
                    "agent_id": "test-agent",
                    "task_id": "test-task",
                    "sequence_id": 1,
                    "created_at": "2023-01-01T00:00:00Z",
                    "content": {
                        "type": "text",
                        "author": "user",
                        "content": "test message",
                    },
                },
            },
            # No ID = notification
        }

        response = client.post("/api", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] is None  # Notification response

        # Give background task time to execute
        await asyncio.sleep(0.1)

        # Handler should have been called
        assert handler_called is True
        assert received_params is not None

    @pytest.mark.asyncio
    async def test_request_processing_with_id(self, async_base_acp_server):
        """Test request processing with ID returns immediate acknowledgment"""

        # Add a mock handler
        async def mock_handler(params):
            return {"status": "processed"}

        async_base_acp_server._handlers[RPCMethod.TASK_CANCEL] = mock_handler

        client = TestClient(async_base_acp_server)

        request = {
            "jsonrpc": "2.0",
            "method": "task/cancel",
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
                    "id": "test-task-123",
                    "namespace_id": "ns-123",
                    "filesystem_id": "fs-123",
                    "status": "RUNNING",
                },
            },
            "id": "test-request-1",
        }

        response = client.post("/api", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-request-1"
        assert data["result"]["status"] == "processing"  # Immediate acknowledgment


class TestAsyncRPCMethods:
    """Test RPC methods that return processing status (async behavior)"""

    def test_create_task_async_response(self, base_acp_server):
        """Test that TASK_CREATE method returns processing status (async behavior)"""
        client = TestClient(base_acp_server)

        # Add a mock handler for init task
        async def mock_init_handler(params):
            return {
                "task_id": params.task.id,
                "status": "initialized",
            }

        base_acp_server._handlers[RPCMethod.TASK_CREATE] = mock_init_handler

        request = {
            "jsonrpc": "2.0",
            "method": "task/create",
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
                    "id": "test-task-456",
                    "namespace_id": "ns-123",
                    "filesystem_id": "fs-123",
                    "status": "RUNNING",
                },
            },
            "id": "test-init-1",
        }

        response = client.post("/api", json=request)

        assert response.status_code == 200
        data = response.json()

        # Verify JSON-RPC structure
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-init-1"
        assert "result" in data
        assert data.get("error") is None

        # Verify it returns async "processing" status (not the handler's result)
        result = data["result"]
        assert result["status"] == "processing"

        # Verify it's NOT the handler's actual result
        assert result.get("status") != "initialized"


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_invalid_json_request(self, base_acp_server):
        """Test handling of invalid JSON in request body"""
        client = TestClient(base_acp_server)

        # Send invalid JSON
        response = client.post("/api", content="invalid json", headers={"Content-Type": "application/json"})

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["jsonrpc"] == "2.0"

    def test_missing_required_fields(self, base_acp_server):
        """Test handling of requests missing required JSON-RPC fields"""
        client = TestClient(base_acp_server)

        # Missing method field
        request = {"jsonrpc": "2.0", "params": {}, "id": "test-1"}

        response = client.post("/api", json=request)

        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    def test_invalid_method_enum(self, base_acp_server):
        """Test handling of invalid method names"""
        client = TestClient(base_acp_server)

        request = {
            "jsonrpc": "2.0",
            "method": "invalid/method/name",
            "params": {},
            "id": "test-1",
        }

        response = client.post("/api", json=request)

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found

    @pytest.mark.asyncio
    async def test_handler_exception_handling(self, async_base_acp_server):
        """Test that handler exceptions are properly handled"""

        # Add a handler that raises an exception
        async def failing_handler(params):
            raise ValueError("Test exception")

        async_base_acp_server._handlers[RPCMethod.EVENT_SEND] = failing_handler

        client = TestClient(async_base_acp_server)

        request = {
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
                    "id": "test-task",
                    "namespace_id": "ns-123",
                    "filesystem_id": "fs-123",
                    "status": "RUNNING",
                },
                "event": {
                    "id": "event-123",
                    "agent_id": "test-agent",
                    "task_id": "test-task",
                    "sequence_id": 1,
                    "created_at": "2023-01-01T00:00:00Z",
                    "content": {
                        "type": "text",
                        "author": "user",
                        "content": "test message",
                    },
                },
            },
            "id": "test-1",
        }

        response = client.post("/api", json=request)

        # Should still return immediate acknowledgment
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["status"] == "processing"

        # Give background task time to fail
        await asyncio.sleep(0.1)
        # Exception should be logged but not crash the server
