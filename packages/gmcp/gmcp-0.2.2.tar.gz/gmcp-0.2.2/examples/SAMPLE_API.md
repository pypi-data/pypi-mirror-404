# gmcp Quickstart Guide

Get started with gmcp in 5 minutes!

## Step 1: Install gmcp

```bash
# Navigate to the gmcp directory
cd /Users/gaurav/Desktop/HELLO

# Install in development mode
pip install -e .
```

## Step 2: Start a FastAPI Server

We've included a sample API for testing. Open a new terminal:

```bash
# Install FastAPI and uvicorn
pip install fastapi uvicorn

# Run the sample server
python examples/sample_api.py
```

The server will start on `http://localhost:5000`. You can view the API docs at `http://localhost:5000/docs`.

## Step 3: Test gmcp Manually

In another terminal, test gmcp to verify it can discover tools:

```bash
gmcp --list-tools http://localhost:5000
```

You should see output like:
```
✅ Successfully connected to http://localhost:5000
📦 Discovered 11 tools:

  • root
    Welcome message.

  • list_users
    Get a list of all users.

  • get_user_users_user_id_get
    Retrieve a specific user by their ID.
    Parameters: user_id

  ...and more
```

This confirms gmcp can connect to your FastAPI server and discover all endpoints.

## Step 4: Configure Claude Code

Add gmcp to your Claude Code MCP settings:

```bash
# Edit (or create) the MCP settings file
code ~/.claude/mcp_settings.json
```

Add this configuration:

```json
{
  "mcpServers": {
    "sample-api": {
      "command": "gmcp",
      "args": ["http://localhost:5000"]
    }
  }
}
```

## Step 5: Use in Claude Code

Restart Claude Code, then try:

```
List all users from the sample API
```

or

```
Create a new user named "Charlie" with email "charlie@example.com"
```

Claude will automatically use the MCP tools exposed by gmcp!

## What's Happening?

1. **gmcp** connects to your FastAPI server
2. Fetches the OpenAPI schema from `/openapi.json`
3. Converts each endpoint into an MCP tool
4. When Claude calls a tool, gmcp makes the HTTP request to FastAPI
5. Results are returned to Claude

## Sample API Endpoints

The sample API includes:

**Users:**
- `GET /users` - List all users
- `GET /users/{user_id}` - Get user by ID
- `POST /users` - Create user
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user

**Todos:**
- `GET /todos` - List all todos (with optional `completed` filter)
- `GET /todos/{todo_id}` - Get todo by ID
- `POST /todos` - Create todo
- `PATCH /todos/{todo_id}` - Toggle todo completion
- `DELETE /todos/{todo_id}` - Delete todo

## Next Steps

### Use with Your Own API

Simply point gmcp to your FastAPI server:

```bash
gmcp http://your-api-server:port
```

### Deploy in Production

You can run gmcp against production APIs:

```json
{
  "mcpServers": {
    "production-api": {
      "command": "gmcp",
      "args": ["https://api.yourcompany.com"]
    }
  }
}
```

### Add Authentication (Coming Soon)

Future versions will support:
- API key headers
- Bearer tokens
- OAuth flows

## Troubleshooting

### gmcp command not found

Make sure you installed the package:
```bash
pip install -e .
```

### Can't connect to FastAPI server

Verify the server is running:
```bash
curl http://localhost:5000/openapi.json
```

### Getting "Invalid JSON" errors

If you see JSON-RPC errors when running `gmcp` without flags, this is normal. gmcp is an MCP server that uses stdio for communication. Use `gmcp --list-tools <url>` for testing, or configure it in Claude Code's MCP settings to use it properly.

### No tools discovered

Check that your FastAPI app has OpenAPI enabled (it's enabled by default).

## Need Help?

Check the main [README.md](README.md) for more details!
