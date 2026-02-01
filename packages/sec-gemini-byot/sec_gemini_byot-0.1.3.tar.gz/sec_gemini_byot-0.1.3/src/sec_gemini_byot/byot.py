import asyncio
import contextlib
import grpc
import logging

from . import byot_api_pb2
from . import byot_api_pb2_grpc
import json
import fastmcp


# Set up logging.
logger = logging.getLogger("BYOT Client")


async def _handle_list_tools(mcp_clients) -> str:
    all_tools = []
    for mcp_client in mcp_clients:
        client_tools = await mcp_client.list_tools()
        all_tools.extend([t.model_dump() for t in client_tools])
    return json.dumps(all_tools)


async def _handle_call_tool(job, mcp_clients) -> str:
    request_dict = json.loads(job.request_data)
    logger.info(f"Request Data: {request_dict}")
    tool_name = request_dict.get("name")
    tool_args = request_dict.get("arguments", {})

    for mcp_client in mcp_clients:
        client_tools = await mcp_client.list_tools()
        if any(t.name == tool_name for t in client_tools):
            result = await mcp_client.call_tool(
                tool_name, tool_args, raise_on_error=False
            )
            # Serialize result robustly handles Pydantic v1/v2 or plain objects
            if hasattr(result, "model_dump"):
                r_dict = result.model_dump()
            elif hasattr(result, "dict"):
                r_dict = result.dict()
            else:
                # Fallback for plain objects
                r_dict = {
                    "content": getattr(result, "content", []),
                    "isError": getattr(result, "isError", False),
                    "_meta": getattr(result, "meta", None),
                    "structuredContent": getattr(
                        result,
                        "structuredContent",
                        getattr(result, "structured_content", None),
                    ),
                }

            # Ensure r_dict is json serializable
            return json.dumps(r_dict, default=str)

    return f"Error: Tool {tool_name} not found."


async def _process_jobs(stream, mcp_clients):
    # Listen for jobs.
    async for msg in stream:
        if msg.job_request.job_id:
            job = msg.job_request
            logger.info(
                f"Received Job: {byot_api_pb2.RequestType.Name(job.request_type)}"
            )

            # Execute Tool via FastMCP logic
            result_content = ""
            try:
                match job.request_type:
                    case byot_api_pb2.RequestType.LIST_TOOLS:
                        result_content = await _handle_list_tools(mcp_clients)
                    case byot_api_pb2.RequestType.CALL_TOOL:
                        result_content = await _handle_call_tool(job, mcp_clients)
                    case byot_api_pb2.RequestType.PING:
                        result_content = "pong"
                    case _:
                        result_content = "Error: Unknown request type."
            except Exception as e:
                result_content = f"Error executing tool: {e}"

            # Send Result
            result_msg = byot_api_pb2.ClientMessage(
                job_result=byot_api_pb2.JobResult(
                    job_id=job.job_id, content=str(result_content)
                )
            )
            await stream.write(result_msg)
            logger.info(f"[+] Result sent for {job.job_id}")

        elif msg.pong.msg:
            logger.info(f"[.] Pong: {msg.pong.msg}")


async def run_client(
    api_key: str,
    client_name: str,
    hub_url: str,
    mcp_servers: list[fastmcp.FastMCP | str],
):
    async with contextlib.AsyncExitStack() as stack:
        # Create clients with all MCP servers.
        mcp_clients = []
        for server in mcp_servers:
            client = fastmcp.Client(server)
            await stack.enter_async_context(client)
            mcp_clients.append(client)
        # Connect to the hub.
        if hub_url.startswith("https://"):
            target = hub_url[len("https://") :]
            channel = await stack.enter_async_context(
                grpc.aio.secure_channel(target, grpc.ssl_channel_credentials())  # type: ignore[possibly-missing-attribute]
            )
        else:
            target = hub_url
            if hub_url.startswith("http://"):
                target = hub_url[len("http://") :]
            channel = await stack.enter_async_context(grpc.aio.insecure_channel(target))  # type: ignore[possibly-missing-attribute]
        stub = byot_api_pb2_grpc.BringYourOwnToolsHubStub(channel)
        logger.info(f"Connecting to {hub_url}...")
        try:
            stream = stub.Connect()
            # Send register message.
            logger.info(f"Registering as '{client_name}' with key '{api_key}'...")
            await stream.write(
                byot_api_pb2.ClientMessage(
                    register=byot_api_pb2.Register(api_key=api_key, name=client_name)
                )
            )
            logger.info("Ready!")
            # Listen for jobs.
            await _process_jobs(stream, mcp_clients)

        except grpc.RpcError as e:
            logger.error("Connection error!")
            logger.error(f"gRPC error: {e}")
            raise e
        except asyncio.CancelledError as e:
            logger.error(f"gRPC error: {e}")
            pass
