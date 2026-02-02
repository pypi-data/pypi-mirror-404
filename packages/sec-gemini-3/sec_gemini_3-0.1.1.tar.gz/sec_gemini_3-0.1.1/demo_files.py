import asyncio
import os
from sec_gemini import SecGemini
import tempfile
import logging


API_KEY = os.environ.get("SEC_GEMINI_API_KEY")
API_HOST = os.environ.get("SEC_GEMINI_API_HOST")


def print_message(msg):
    logging.info("[blue] Message [/blue]")
    logging.info(f" # Title: [green]{msg.get('title')}[/green]")
    logging.info(f"   Content: {msg.get('content')}")
    # logging.info(f"   ID: {msg.get('id')}")
    logging.info(f"   Message Type: {msg.get('message_type')}")
    # logging.info(f"   Mime Type: {msg.get('mime_type')}")
    # logging.info(f"   Render Type: {msg.get('render_type')}")
    # logging.info(f"   Source: {msg.get('source')}")
    logging.info(f"   Source Type: {msg.get('source_type')}")
    # logging.info(f"   Timestamp: {msg.get('timestamp')}")
    logging.info(f"   Snapshot ID: {msg.get('snapshot_id')}")


async def main():
    assert API_KEY, "API_KEY must be set"
    assert API_HOST, "API_HOST must be set"
    logging.info("[bold green]Creating a Sec-Gemini Session[/bold green]")
    client = SecGemini(api_key=API_KEY, host=API_HOST)
    await client.start()
    session = await client.create_session()
    logging.info(f"Session Created: [bold yellow]{session.id}[/bold yellow]")
    logging.info("[bold green]Uploading Files[/bold green]")
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "secret.txt"), "w") as f:
            f.write("The secret it 'friendly potatoes")
        await session.upload_file(file_path=f.name)
    files = await session.list_files()
    for f in files:
        logging.info(f" - File: [yellow]{f.filename} ({f.url})[/yellow]")

    logging.info("[bold green] MCPs [/bold green]")
    mcps = await session.list_mcps()
    for mcp in mcps:
        logging.info(f" - [yellow]{mcp.name}[/yellow] ({mcp.uri}) Status: {mcp.status}")
        if mcp.tools:
            logging.info("     -> Tools:")
            for tool in mcp.tools:
                logging.info(f"       - {tool}")

    logging.info("[bold green] We now send a  prompt [/bold green]")
    # prompt = "Analyze the security of lucainvernizzi.net email settings."
    prompt = "I gave you a file. what's the secret message in it?"
    logging.info(f" Hey, Sec-Gemini, [yellow]{prompt}[/yellow]")
    await session.prompt(prompt)
    logging.info("[bold green] Streaming messages... [/bold green]")
    async for msg in session.stream_messages():
        print_message(msg)
    logging.info("Closing client...")
    await session.delete()
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
