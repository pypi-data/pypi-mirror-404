# Authentication Examples

Quick examples showing how to use gmcp with different authentication methods.

## Example 1: Testing the Secure API

Start the secure API:
```bash
cd examples
python secure_api.py
```

Test without authentication (will fail):
```bash
gmcp --list-tools http://localhost:5001
# Error: 403 Forbidden
```

Test with correct API key:
```bash
gmcp --list-tools \
     --auth-type apikey \
     --auth-token "test-key-12345" \
     --auth-header "X-API-Key" \
     http://localhost:5001

# ✅ Successfully connected!
# 📦 Discovered 5 tools...
```

## Example 2: Using Environment Variables

Create a `.env` file:
```bash
cat > .env << EOF
API_KEY=test-key-12345
API_HEADER=X-API-Key
EOF
```

Load and use:
```bash
export $(cat .env | xargs)

gmcp --list-tools \
     --auth-type apikey \
     --auth-token '$API_KEY' \
     --auth-header '$API_HEADER' \
     http://localhost:5001
```

## Example 3: Bearer Token (GitHub API Style)

```bash
export GITHUB_TOKEN="your-github-token"

gmcp --list-tools \
     --auth-type bearer \
     --auth-token '$GITHUB_TOKEN' \
     https://api.github.com
```

## Example 4: Basic Authentication

```bash
export API_USER="admin"
export API_PASS="secret"

gmcp --list-tools \
     --auth-type basic \
     --auth-username '$API_USER' \
     --auth-password '$API_PASS' \
     http://localhost:5001
```

## Example 5: Custom Headers Only

```bash
gmcp --list-tools \
     --auth-headers "X-Client-ID: my-app" \
     --auth-headers "X-Version: 1.0" \
     http://localhost:5000
```

## Example 6: Claude Code Configuration

For use with Claude Code, add to `~/.claude/mcp_settings.json`:

```json
{
  "mcpServers": {
    "secure-api": {
      "command": "gmcp",
      "args": [
        "http://localhost:5001",
        "--auth-type", "apikey",
        "--auth-token", "$API_KEY",
        "--auth-header", "X-API-Key"
      ],
      "env": {
        "API_KEY": "test-key-12345"
      }
    }
  }
}
```

Then in Claude Code:
- "List all messages from the secure API"
- "Create a new message saying Hello World"

## Example 7: Multiple APIs with Different Auth

```json
{
  "mcpServers": {
    "public-api": {
      "command": "gmcp",
      "args": ["http://localhost:5000"]
    },
    "secure-api": {
      "command": "gmcp",
      "args": [
        "http://localhost:5001",
        "--auth-type", "apikey",
        "--auth-token", "$API_KEY"
      ],
      "env": {
        "API_KEY": "test-key-12345"
      }
    },
    "github-api": {
      "command": "gmcp",
      "args": [
        "https://api.github.com",
        "--auth-type", "bearer",
        "--auth-token", "$GITHUB_TOKEN"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token"
      }
    }
  }
}
```

Claude can now access all three APIs!

## Troubleshooting

### Test with curl first
```bash
# Test API key
curl -H "X-API-Key: test-key-12345" http://localhost:5001/messages

# Test bearer token
curl -H "Authorization: Bearer your-token" http://api.example.com/data

# Test basic auth
curl -u username:password http://api.example.com/data
```

### Debug environment variables
```bash
echo $API_KEY
# Should print your API key

# If empty, check:
export API_KEY="your-key"
echo $API_KEY
```

### Check gmcp is using auth
```bash
# Run with --list-tools to see connection details
gmcp --list-tools --auth-type bearer --auth-token "test" http://localhost:5001
```
