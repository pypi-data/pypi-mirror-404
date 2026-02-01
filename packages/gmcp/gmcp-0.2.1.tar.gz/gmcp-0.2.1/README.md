# gmcp - Transform FastAPI to MCP

gmcp automatically converts any FastAPI server into an MCP (Model Context Protocol) server, exposing all API endpoints as tools that Claude can use.

## Features

- 🚀 **Zero Configuration**: Just provide a FastAPI server URL
- 🔄 **Auto-Discovery**: Automatically discovers all endpoints via OpenAPI schema
- 🛠️ **Full Support**: Handles GET, POST, PUT, PATCH, DELETE methods
- 📝 **Schema Aware**: Preserves parameter types, descriptions, and validation
- 🔐 **Authentication**: Supports Bearer tokens, API keys, Basic auth, and custom headers
- 🔒 **Secure**: Environment variable support for sensitive credentials
- ⚡ **Fast**: Efficient async HTTP client built on httpx

## Installation

```bash
# Install in development mode
pip install -e .
```

## Usage

### Basic Usage

**Testing (list available tools):**
```bash
# Test that gmcp can discover tools
gmcp --list-tools http://localhost:5000
```

**Running as MCP server:**

gmcp automatically detects when it's run from an interactive terminal and will show helpful instructions instead of starting the server. To use it as an MCP server, configure it in Claude Code (see below).

If you need to force MCP server mode (e.g., for testing with another MCP client):
```bash
gmcp --force http://localhost:5000
```

### Configure in Claude Code

Add to `~/.claude/mcp_settings.json`:

**Basic (no auth):**
```json
{
  "mcpServers": {
    "my-fastapi-server": {
      "command": "gmcp",
      "args": ["http://localhost:5000"]
    }
  }
}
```

**With Authentication:**
```json
{
  "mcpServers": {
    "my-api": {
      "command": "gmcp",
      "args": [
        "http://api.example.com",
        "--auth-type", "bearer",
        "--auth-token", "$API_TOKEN"
      ],
      "env": {
        "API_TOKEN": "your-token-here"
      }
    }
  }
}
```

See [AUTH.md](AUTH.md) for complete authentication documentation.

### Example

If your FastAPI server has these endpoints:

```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id, "name": "John"}

@app.post("/users")
async def create_user(name: str, email: str):
    return {"id": 123, "name": name, "email": email}
```

gmcp will automatically create MCP tools:
- `get_users_user_id` - Get a user by ID
- `create_users` - Create a new user

Claude can then call these tools directly!

## How It Works

1. **Fetch Schema**: gmcp fetches the OpenAPI schema from `/openapi.json`
2. **Parse Endpoints**: Converts each endpoint into an MCP tool definition
3. **Proxy Requests**: When tools are called, gmcp makes HTTP requests to FastAPI
4. **Return Results**: Responses are formatted and returned to Claude

## Requirements

- Python 3.10+
- A running FastAPI server with OpenAPI enabled (default)

## Development

### Project Structure

```
gmcp/
├── src/
│   └── gmcp/
│       ├── __init__.py
│       └── server.py      # Main MCP server implementation
├── examples/
│   ├── sample_api.py      # Example FastAPI server
│   └── test_gmcp.sh       # Test script
├── pyproject.toml
└── README.md
```

### Testing

See `examples/` directory for a sample FastAPI server and test script.

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes
- [AUTH.md](AUTH.md) - Authentication guide (Bearer, API keys, Basic auth)
- [USAGE.md](USAGE.md) - Detailed usage guide and troubleshooting

## License

MIT
