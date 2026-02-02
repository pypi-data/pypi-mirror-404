# Sec-Gemini Python SDK

The Sec-Gemini SDK provides a Pythonic interface to interact with the Sec-Gemini API Hub. It allows you to create sessions, send prompts, upload files, and leverage MCP (Model Context Protocol) tools for security analysis.

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
uv add sec-gemini
```

## Authentication

You need an API key to use the SDK. Set it as an environment variable:

```bash
export SEC_GEMINI_API_KEY="your-api-key"
```

The SDK will automatically pick up this variable.

## Quick Start

Here is a minimal example to connect to the API Hub, create a session, and send a prompt.

```python
import asyncio
import os
from sec_gemini import SecGemini

async def main():
    # Initialize the client (picks up SEC_GEMINI_API_KEY from env)
    client = SecGemini(api_key=os.environ["SEC_GEMINI_API_KEY"])
    await client.start()

    try:
        # Create a new session
        session = await client.create_session()
        print(f"Created Session: {session.id}")

        # Send a prompt
        prompt = "Hello, Sec-Gemini! Can you help me analyze a file?"
        print(f"Sending prompt: {prompt}")
        await session.prompt(prompt)

        # Stream the response
        print("Response:")
        async for msg in session.stream_messages():
            print(f"{msg.role}: {msg.content}")

    finally:
        # Cleanup
        if 'session' in locals():
            await session.delete()
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Core Concepts

### Client (`SecGemini`)

The `SecGemini` class is the main entry point. It manages the connection to the API Hub.

- **`start()`**: Connects to the server.
- **`close()`**: Closes the connection.
- **`sessions()`**: Lists active sessions.

### Session (`Session`)

A `Session` represents a conversation context. It maintains state, history, and associated files.

- **`upload_file(file_path)`**: Uploads a file for analysis.
- **`list_files()`**: Lists files in the session.
- **`prompt(text)`**: Sends a user message.
- **`stream_messages()`**: Yields messages (including tool outputs and assistant responses) as they arrive.
- **`list_mcps()`**: Lists available tools/MCPs for this session.

### Files

You can upload files to a session for the agent to analyze.

```python
# Upload a file
await session.upload_file("path/to/suspicious_log.txt")

# List files
files = await session.list_files()
for f in files:
    print(f"File: {f.filename} ({f.url})")
```

### Tool Confirmation

Some sensitive tools may require user confirmation before execution. You should listen for confirmation requests and respond to them.

```python
# Check if there is a pending confirmation request
confirmation_req = await session.get_confirmation_info()
if confirmation_req:
    print(f"Tool execution requested: {confirmation_req.tool_name}")
    print(f"Args: {confirmation_req.tool_args}")

    # Approve the action
    await session.send_tool_confirmation(
        action_id=confirmation_req.confirmation_id,
        confirmed=True
    )
```

### Reconnecting to Sessions

You can resume work on an existing session by its ID.

```python
# List all sessions
sessions = await client.sessions()
for s in sessions:
    print(f"Found session: {s.id} (Status: {s.status})")

# Resume a specific session (if you have the object or find it)
if sessions:
    session = sessions[0]
    await session.resume() # Ensures it's active

    # Continue conversation
    await session.prompt("Where were we?")
```
