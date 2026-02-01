# Sec-Gemini Bring-Your-Own-Tool (BYOT) Client

The BYOT client allows you to expose local tools (standard MCP or FastMCP) to Sec-Gemini via a secure gRPC Hub. This enables Sec-Gemini to execute tools directly on your local machine or in your internal environment.

## Quick Start

Run the client directly using `pipx` (no installation required):

```sh
pipx run sec-gemini-byot --api-key <YOUR_API_KEY>
```

> [!TIP]
> **For Googlers**: Use the simple index to solve airlock issues.
> ```sh
> pipx run --index-url=https://pypi.org/simple sec-gemini-byot --api-key <YOUR_API_KEY>
> ```

## Installation

You can install the client using `pip` or `uv`:

```sh
# Using pip
pip install sec-gemini-byot

# Using uv
uv pip install sec-gemini-byot
```

## Usage

### Basic Options

- `--api-key`: **(Required)** Your Sec-Gemini API key for authentication.
- `--name`: The name of this client instance (defaults to your hostname).
- `--hub`: The URL of the BYOT Hub (defaults to the production Hub).

Example:
```sh
sec-gemini-byot --api-key <YOUR_API_KEY> --name "my-local-worker"
```

### Adding Custom Tools

You can connect additional MCP servers by providing their URLs (for HTTP/SSE) or local paths (for stdio):

```sh
sec-gemini-byot --api-key <YOUR_API_KEY> \
  --additional-mcps http://localhost:8080/mcp /path/to/my/tool.py
```

### Developing Your Own Tools

The client uses [FastMCP](https://github.com/jlowin/fastmcp). You can easily define your own tools:

```python
# my_tools.py
from fastmcp import FastMCP

mcp = FastMCP("MyLocalTools")

@mcp.tool()
def read_local_config(name: str) -> str:
    """Reads a local configuration file."""
    return f"Config for {name}: internal-secret-v1"

if __name__ == "__main__":
    mcp.run()
```

Then run the BYOT client pointing to your script:
```sh
sec-gemini-byot --api-key <YOUR_API_KEY> --additional-mcps ./my_tools.py
```

## Troubleshooting

- **Connection Error**: Check your internet connection and ensure the Hub URL is correct. The client will automatically attempt to reconnect using exponential backoff.
- **Authentication Failed**: Double-check your `--api-key`.
- **Tool Not Found**: Ensure that any additional MCP servers are running and accessible.
