#!/usr/bin/env python3
"""Example FastAPI server with API key authentication."""

from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

app = FastAPI(
    title="Secure API",
    description="A FastAPI server with API key authentication for testing gmcp",
    version="1.0.0"
)

# API Key configuration
API_KEY_NAME = "X-API-Key"
API_KEY = "test-key-12345"  # In production, use env vars!

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key from header."""
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


# Protected endpoints
class Message(BaseModel):
    text: str


class MessageResponse(BaseModel):
    id: int
    text: str
    status: str


messages_db = {}
next_message_id = 1


@app.get("/", summary="Public endpoint")
async def root():
    """Public endpoint - no auth required."""
    return {
        "message": "Secure API - Use X-API-Key header for authentication",
        "docs": "/docs"
    }


@app.get("/messages", response_model=list[MessageResponse], summary="List all messages")
async def list_messages(api_key: str = Security(verify_api_key)):
    """Get all messages (requires API key)."""
    return list(messages_db.values())


@app.post("/messages", response_model=MessageResponse, summary="Create a message")
async def create_message(message: Message, api_key: str = Security(verify_api_key)):
    """Create a new message (requires API key)."""
    global next_message_id
    message_id = next_message_id
    next_message_id += 1

    new_message = {
        "id": message_id,
        "text": message.text,
        "status": "active"
    }
    messages_db[message_id] = new_message
    return new_message


@app.get("/messages/{message_id}", response_model=MessageResponse, summary="Get message by ID")
async def get_message(message_id: int, api_key: str = Security(verify_api_key)):
    """Get a specific message (requires API key)."""
    if message_id not in messages_db:
        raise HTTPException(status_code=404, detail="Message not found")
    return messages_db[message_id]


@app.delete("/messages/{message_id}", summary="Delete a message")
async def delete_message(message_id: int, api_key: str = Security(verify_api_key)):
    """Delete a message (requires API key)."""
    if message_id not in messages_db:
        raise HTTPException(status_code=404, detail="Message not found")

    del messages_db[message_id]
    return {"message": f"Message {message_id} deleted"}


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("Starting Secure API with API Key Authentication")
    print("="*60)
    print(f"\nAPI Key: {API_KEY}")
    print(f"Header: {API_KEY_NAME}")
    print("\nTest with gmcp:")
    print(f"  gmcp --list-tools \\")
    print(f"       --auth-type apikey \\")
    print(f"       --auth-token '{API_KEY}' \\")
    print(f"       --auth-header '{API_KEY_NAME}' \\")
    print(f"       http://localhost:5001")
    print("\n" + "="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=5001)
