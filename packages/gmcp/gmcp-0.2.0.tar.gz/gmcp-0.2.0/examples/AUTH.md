# gmcp Authentication Guide

gmcp supports multiple authentication methods to work with secured APIs.

## Authentication Methods

### 1. Bearer Token Authentication

Used for APIs that require an `Authorization: Bearer <token>` header.

**Command Line:**
```bash
gmcp --auth-type bearer --auth-token "your-token-here" http://api.example.com
```

**With Environment Variable:**
```bash
export API_TOKEN="your-token-here"
gmcp --auth-type bearer --auth-token '$API_TOKEN' http://api.example.com
```

**Claude Code Configuration:**
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

### 2. API Key Authentication

Used for APIs that require an API key in a custom header (e.g., `X-API-Key`).

**Command Line:**
```bash
# Default header name (X-API-Key)
gmcp --auth-type apikey --auth-token "your-api-key" http://api.example.com

# Custom header name
gmcp --auth-type apikey \
     --auth-token "your-api-key" \
     --auth-header "X-Custom-API-Key" \
     http://api.example.com
```

**With Environment Variable:**
```bash
export API_KEY="your-api-key"
gmcp --auth-type apikey --auth-token 'env:API_KEY' http://api.example.com
```

**Claude Code Configuration:**
```json
{
  "mcpServers": {
    "my-api": {
      "command": "gmcp",
      "args": [
        "http://api.example.com",
        "--auth-type", "apikey",
        "--auth-token", "$API_KEY",
        "--auth-header", "X-API-Key"
      ],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}
```

### 3. Basic Authentication

Used for APIs that require HTTP Basic Authentication.

**Command Line:**
```bash
gmcp --auth-type basic \
     --auth-username "user" \
     --auth-password "pass" \
     http://api.example.com
```

**With Environment Variables:**
```bash
export API_USER="user"
export API_PASS="pass"
gmcp --auth-type basic \
     --auth-username '$API_USER' \
     --auth-password '$API_PASS' \
     http://api.example.com
```

**Claude Code Configuration:**
```json
{
  "mcpServers": {
    "my-api": {
      "command": "gmcp",
      "args": [
        "http://api.example.com",
        "--auth-type", "basic",
        "--auth-username", "$API_USER",
        "--auth-password", "$API_PASS"
      ],
      "env": {
        "API_USER": "username",
        "API_PASS": "password"
      }
    }
  }
}
```

### 4. Custom Headers

Add any custom headers to your requests.

**Command Line:**
```bash
gmcp --auth-headers "X-Custom-Header: value1" \
     --auth-headers "X-Another-Header: value2" \
     http://api.example.com
```

**With Environment Variables:**
```bash
export CUSTOM_VALUE="secret"
gmcp --auth-headers "X-Custom-Header: $CUSTOM_VALUE" http://api.example.com
```

**Claude Code Configuration:**
```json
{
  "mcpServers": {
    "my-api": {
      "command": "gmcp",
      "args": [
        "http://api.example.com",
        "--auth-headers", "X-Custom-Header: $CUSTOM_VALUE"
      ],
      "env": {
        "CUSTOM_VALUE": "secret-value"
      }
    }
  }
}
```

### 5. Combined Authentication

You can combine custom headers with any auth type.

**Example: Bearer token + custom headers**
```bash
gmcp --auth-type bearer \
     --auth-token '$API_TOKEN' \
     --auth-headers "X-Client-ID: my-client" \
     --auth-headers "X-Request-ID: 12345" \
     http://api.example.com
```

## Environment Variable Formats

gmcp supports two formats for referencing environment variables:

1. **Shell-style:** `$VARIABLE_NAME` or `${VARIABLE_NAME}`
2. **Explicit:** `env:VARIABLE_NAME`

**Examples:**
```bash
# All equivalent
--auth-token '$API_TOKEN'
--auth-token '${API_TOKEN}'
--auth-token 'env:API_TOKEN'
```

**Important:** Use single quotes to prevent shell expansion!

## Security Best Practices

### 1. Never Hardcode Secrets

❌ **Bad:**
```json
{
  "args": ["http://api.example.com", "--auth-token", "sk-1234567890"]
}
```

✅ **Good:**
```json
{
  "args": ["http://api.example.com", "--auth-token", "$API_TOKEN"],
  "env": {
    "API_TOKEN": "sk-1234567890"
  }
}
```

### 2. Use Environment Files

Store secrets in `.env` files (and add to `.gitignore`):

```bash
# .env
API_TOKEN=your-secret-token
API_KEY=your-api-key
```

Load in your shell:
```bash
export $(cat .env | xargs)
gmcp --auth-type bearer --auth-token '$API_TOKEN' http://api.example.com
```

### 3. Use System Keychain

On macOS, you can use the keychain:
```bash
# Store secret
security add-generic-password -a gmcp -s api_token -w "your-token"

# Retrieve and use
export API_TOKEN=$(security find-generic-password -a gmcp -s api_token -w)
gmcp --auth-type bearer --auth-token '$API_TOKEN' http://api.example.com
```

## Testing Authentication

Use `--list-tools` to test authentication without starting the server:

```bash
# Test with bearer token
gmcp --list-tools \
     --auth-type bearer \
     --auth-token "your-token" \
     http://api.example.com

# If successful, you'll see the list of tools
# If authentication fails, you'll see an error
```

## Common Scenarios

### GitHub API

```bash
export GITHUB_TOKEN="ghp_your_token"
gmcp --auth-type bearer \
     --auth-token '$GITHUB_TOKEN' \
     --auth-headers "Accept: application/vnd.github+json" \
     https://api.github.com
```

### OpenAI API

```bash
export OPENAI_API_KEY="sk-your-key"
gmcp --auth-type bearer \
     --auth-token '$OPENAI_API_KEY' \
     https://api.openai.com/v1
```

### Custom FastAPI with API Key

```bash
export MY_API_KEY="your-key"
gmcp --auth-type apikey \
     --auth-token '$MY_API_KEY' \
     --auth-header "X-API-Key" \
     http://localhost:5000
```

## Troubleshooting

### "401 Unauthorized" Error

- Check that your token/credentials are correct
- Verify the auth type matches what the API expects
- For API keys, ensure the header name is correct
- Test with curl first:
  ```bash
  curl -H "Authorization: Bearer your-token" http://api.example.com/openapi.json
  ```

### Environment Variable Not Expanding

- Use single quotes: `'$VAR'` not `"$VAR"`
- Or use the explicit format: `'env:VAR'`
- Check the variable is set: `echo $VAR`

### Custom Headers Not Working

- Ensure format is: `"Header-Name: value"`
- Include the colon separator
- Values can use environment variables: `"X-Key: $MY_KEY"`

## Next Steps

- See [QUICKSTART.md](QUICKSTART.md) for basic setup
- See [USAGE.md](USAGE.md) for general usage guide
- See [README.md](README.md) for full documentation
