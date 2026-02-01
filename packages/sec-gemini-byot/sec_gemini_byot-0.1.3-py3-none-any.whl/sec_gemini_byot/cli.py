import asyncio
import logging
import argparse
import socket
from rich.logging import RichHandler
import grpc
import tenacity

from . import byot
from . import default_mcp

# Constants.
DEFAULT_HUB_URL = "https://bringyourowntool-hub-171354917004.us-central1.run.app"

# Set up logging.
logging.getLogger("grpc").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)


# Tenacity here deals with reconnecting to the hub if it goes down temporarely.
@tenacity.retry(
    retry=tenacity.retry_if_exception_type((grpc.RpcError, OSError)),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
)
async def main():
    # Parse arguments.
    parser = argparse.ArgumentParser(
        description="Sec-Gemini Bring-Your-Own-Tool Client"
    )
    parser.add_argument(
        "--name",
        default=socket.gethostname(),
        help="Name of this client (default: hostname)",
    )
    parser.add_argument(
        "--api-key", help="Sec-GeminiAPI Key for authentication", required=True
    )
    parser.add_argument(
        "--hub", default=DEFAULT_HUB_URL, help="Hub address (host:port)"
    )
    parser.add_argument(
        "--use-default-mcp",
        default=True,
        action="store_true",
        help="Use the default MCP",
    )
    parser.add_argument(
        "--additional-mcps",
        default=[],
        nargs="+",
        help="Additional MCPS as urls or file paths",
    )
    args = parser.parse_args()
    # Compile the list of mcps to use.
    mcps = [*([default_mcp.mcp] if args.use_default_mcp else []), *args.additional_mcps]
    # And run the client.
    logging.info("Starting client...")
    if args.use_default_mcp:
        logging.info("Using default MCP")
    try:
        await byot.run_client(args.api_key, args.name, args.hub, mcps)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, I'm done.")


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
