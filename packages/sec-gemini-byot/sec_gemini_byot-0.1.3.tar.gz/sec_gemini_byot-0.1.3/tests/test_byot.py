import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import json
import sys
import os

# Ensure we can import modules from the src and parent directory
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sec_gemini_byot import byot
from sec_gemini_byot import byot_api_pb2


class TestByot(unittest.IsolatedAsyncioTestCase):
    async def test_handle_list_tools(self):
        # Setup mock MCP client
        mock_client = MagicMock()

        # Mock tool structure - FastMCP tools usually have a model_dump method
        tool1 = MagicMock()
        tool1.model_dump.return_value = {"name": "tool1", "description": "test tool 1"}

        tool2 = MagicMock()
        tool2.model_dump.return_value = {"name": "tool2", "description": "test tool 2"}

        mock_client.list_tools = AsyncMock(return_value=[tool1, tool2])

        mcp_clients = [mock_client]

        # execution
        result_json = await byot._handle_list_tools(mcp_clients)

        # verification
        result = json.loads(result_json)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "tool1")
        self.assertEqual(result[1]["name"], "tool2")

    async def test_handle_call_tool_success(self):
        mock_client = MagicMock()
        tool = MagicMock()
        tool.name = "my_tool"
        tool.model_dump.return_value = {"name": "my_tool"}
        mock_client.list_tools = AsyncMock(return_value=[tool])

        # Mock result
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "content": [{"type": "text", "text": "result"}]
        }
        # Simulate result not having dict method to hit the first if branch
        del mock_result.dict

        mock_client.call_tool = AsyncMock(return_value=mock_result)

        mcp_clients = [mock_client]

        job = MagicMock()
        job.request_data = json.dumps(
            {"name": "my_tool", "arguments": {"arg1": "val1"}}
        )

        result_json = await byot._handle_call_tool(job, mcp_clients)

        result = json.loads(result_json)
        self.assertEqual(result["content"][0]["text"], "result")
        mock_client.call_tool.assert_called_with(
            "my_tool", {"arg1": "val1"}, raise_on_error=False
        )

    async def test_handle_call_tool_not_found(self):
        mock_client = MagicMock()
        mock_client.list_tools = AsyncMock(return_value=[])
        mcp_clients = [mock_client]

        job = MagicMock()
        job.request_data = json.dumps({"name": "missing_tool", "arguments": {}})

        result = await byot._handle_call_tool(job, mcp_clients)
        self.assertIn("Error: Tool missing_tool not found", result)

    async def test_process_jobs_list_tools(self):
        mock_stream = MagicMock()
        # Mock async iterator for stream

        job_request = MagicMock()
        job_request.job_id = "job1"
        job_request.request_type = byot_api_pb2.RequestType.LIST_TOOLS

        msg = MagicMock()
        msg.job_request = job_request

        # Setup async iterator to return one message then stop
        m = AsyncMock()
        m.__aiter__.return_value = [msg]
        mock_stream = m

        mock_client = MagicMock()
        mock_client.list_tools = AsyncMock(return_value=[])
        mcp_clients = [mock_client]

        mock_stream.write = AsyncMock()

        await byot._process_jobs(mock_stream, mcp_clients)

        mock_stream.write.assert_called_once()
        call_args = mock_stream.write.call_args[0][0]
        self.assertEqual(call_args.job_result.job_id, "job1")
        self.assertEqual(call_args.job_result.content, "[]")

    async def test_process_jobs_ping(self):
        job_request = MagicMock()
        job_request.job_id = "job_ping"
        job_request.request_type = byot_api_pb2.RequestType.PING

        msg = MagicMock()
        msg.job_request = job_request

        mock_stream = AsyncMock()
        mock_stream.__aiter__.return_value = [msg]
        mock_stream.write = AsyncMock()

        await byot._process_jobs(mock_stream, [])

        mock_stream.write.assert_called_once()
        call_args = mock_stream.write.call_args[0][0]
        self.assertEqual(call_args.job_result.content, "pong")

    async def test_process_jobs_error(self):
        job_request = MagicMock()
        job_request.job_id = "job_error"
        job_request.request_type = byot_api_pb2.RequestType.CALL_TOOL
        # request_data missing will cause json.loads to fail (if we don't mock it)
        # But wait, job is a mock, job.request_data is a mock. json.loads(mock) will fail?
        # json.loads expects string, bytes or bytearray.
        # Let's make it fail by having job.request_data be invalid json string
        job_request.request_data = "{invalid_json"

        msg = MagicMock()
        msg.job_request = job_request

        mock_stream = AsyncMock()
        mock_stream.__aiter__.return_value = [msg]
        mock_stream.write = AsyncMock()

        await byot._process_jobs(mock_stream, [])

        mock_stream.write.assert_called_once()
        call_args = mock_stream.write.call_args[0][0]
        self.assertIn("Error executing tool", call_args.job_result.content)

    @patch("grpc.aio.secure_channel")
    @patch("grpc.aio.insecure_channel")
    @patch("grpc.ssl_channel_credentials")
    @patch("fastmcp.Client")
    async def test_run_client_secure(
        self, mock_fastmcp, mock_ssl_creds, mock_insecure, mock_secure
    ):
        # Setup mocks
        mock_secure.return_value.__aenter__.return_value = MagicMock()
        mock_fastmcp.return_value.__aenter__.return_value = MagicMock()

        # We need to mock the stub and the stream to avoid actual network calls or further errors
        with patch(
            "sec_gemini_byot.byot_api_pb2_grpc.BringYourOwnToolsHubStub"
        ) as mock_stub:
            mock_stream = AsyncMock()
            mock_stream.__aiter__.return_value = []  # Empty stream
            mock_stub.return_value.Connect.return_value = mock_stream

            await byot.run_client("key", "name", "https://hub.com", [])

        mock_secure.assert_called_once_with("hub.com", mock_ssl_creds.return_value)
        mock_insecure.assert_not_called()

    @patch("grpc.aio.secure_channel")
    @patch("grpc.aio.insecure_channel")
    @patch("fastmcp.Client")
    async def test_run_client_insecure_http(
        self, mock_fastmcp, mock_insecure, mock_secure
    ):
        mock_insecure.return_value.__aenter__.return_value = MagicMock()
        mock_fastmcp.return_value.__aenter__.return_value = MagicMock()

        with patch(
            "sec_gemini_byot.byot_api_pb2_grpc.BringYourOwnToolsHubStub"
        ) as mock_stub:
            mock_stream = AsyncMock()
            mock_stream.__aiter__.return_value = []
            mock_stub.return_value.Connect.return_value = mock_stream

            await byot.run_client("key", "name", "http://localhost:50051", [])

        mock_insecure.assert_called_once_with("localhost:50051")
        mock_secure.assert_not_called()

    @patch("grpc.aio.secure_channel")
    @patch("grpc.aio.insecure_channel")
    @patch("fastmcp.Client")
    async def test_run_client_insecure_default(
        self, mock_fastmcp, mock_insecure, mock_secure
    ):
        mock_insecure.return_value.__aenter__.return_value = MagicMock()
        mock_fastmcp.return_value.__aenter__.return_value = MagicMock()

        with patch(
            "sec_gemini_byot.byot_api_pb2_grpc.BringYourOwnToolsHubStub"
        ) as mock_stub:
            mock_stream = AsyncMock()
            mock_stream.__aiter__.return_value = []
            mock_stub.return_value.Connect.return_value = mock_stream

            await byot.run_client("key", "name", "localhost:50051", [])

        mock_insecure.assert_called_once_with("localhost:50051")
        mock_secure.assert_not_called()


if __name__ == "__main__":
    unittest.main()
