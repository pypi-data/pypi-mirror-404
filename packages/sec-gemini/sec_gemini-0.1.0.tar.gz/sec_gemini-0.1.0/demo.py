import asyncio
import os
from sec_gemini import SecGemini
import tempfile
import logging
from google.protobuf import json_format
from rich.logging import RichHandler


logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger("secgemini")

API_KEY = os.environ.get("SEC_GEMINI_API_KEY")
API_HOST = os.environ.get("SEC_GEMINI_API_HOST")


def approve_tool_calls(session_id, session_status):
    logger.info(
        f"  >>> [orange] Session {session_id} status updated to [bold]{session_status}  <<< [/bold][/orange]"
    )


def print_message(msg):
    logger.info("[blue] Message [/blue]")
    logger.info(f" # Title: [green]{msg.get('title')}[/green]")
    logger.info(f"   Content: {msg.get('content')}")
    # logger.info(f"   ID: {msg.get('id')}")
    logger.info(f"   Message Type: {msg.get('message_type')}")
    # logger.info(f"   Mime Type: {msg.get('mime_type')}")
    # logger.info(f"   Render Type: {msg.get('render_type')}")
    # logger.info(f"   Source: {msg.get('source')}")
    logger.info(f"   Source Type: {msg.get('source_type')}")
    # logger.info(f"   Timestamp: {msg.get('timestamp')}")
    logger.info(f"   Snapshot ID: {msg.get('snapshot_id')}")


async def main():
    assert API_KEY, "API_KEY must be set"
    assert API_HOST, "API_HOST must be set"
    logger.info("[bold green]Creating a Sec-Gemini Session[/bold green]")
    client = SecGemini(api_key=API_KEY, host=API_HOST)
    await client.start()
    session = await client.create_session()
    logger.info(f"Session Created: [bold yellow]{session.id}[/bold yellow]")

    logger.info("[bold green]Uploading Files[/bold green]")
    with tempfile.TemporaryDirectory() as tmpdir:
        for name in ["hello", "world"]:
            with open(os.path.join(tmpdir, f"{name}.txt"), "w") as f:
                f.write(name)
            await session.upload_file(file_path=f.name)
    files = await session.list_files()
    for f in files:
        logger.info(f" - File: [yellow]{f.filename} ({f.url})[/yellow]")
    logger.info("[bold green]Deleting a file[/bold green]")
    for f in files:
        await session.delete_file(filename=f.filename)
        break
    logger.info("[bold green]Listing files (After Delete)[/bold green]")
    files = await session.list_files()
    for f in files:
        logger.info(f" - File: [yellow]{f.filename} ({f.url})[/yellow]")

    logger.info("[bold green] MCPs [/bold green]")
    mcps = await session.list_mcps()
    for mcp in mcps:
        if not mcp.tools:
            continue
        logger.info(f" - [yellow]{mcp.name}[/yellow] ({mcp.uri}) Status: {mcp.status}")
        logger.info("     -> Tools:")
        for tool in mcp.tools:
            logger.info(f"       - {tool}")

    logger.info("[bold green] Skills [/bold green]")
    mcps = await session.list_skills()
    for mcp in mcps:
        if not mcp.skills:
            continue
        logger.info(f" - [yellow]{mcp.name}[/yellow] ({mcp.uri}) Status: {mcp.status}")
        logger.info("     -> Skills:")
        for skill in mcp.skills:
            logger.info(f"       - {skill}")

    logger.info("[bold green] We now send a  prompt [/bold green]")
    # prompt = "Analyze the security of lucainvernizzi.net email settings."
    prompt = "What is the capital of France?"
    logger.info(f" Hey, Sec-Gemini, [yellow]{prompt}[/yellow]")

    await session.set_confirmation_config(True)
    # We need to react when the session is waiting for confirmation.
    session.add_status_callback(approve_tool_calls)
    await session.prompt(prompt)

    logger.info("[bold green] Streaming messages... [/bold green]")
    index = 0
    async for msg in session.stream_messages():
        print_message(msg)
        if index == 5:
            # We will simulate a disconnection.
            logger.info("[bold red] Simulating Disconnection [/bold red]")
            await client.close()
            break
        index += 1

    logger.info("[bold red] Reconnecting... [/bold red]")
    await asyncio.sleep(1)  # Wait a bit
    client = SecGemini(api_key=API_KEY, host=API_HOST)
    await client.start()
    sessions = await client.sessions()
    # Find the session we were using before.
    session = next(s for s in sessions if s.id == session.id)
    logger.info(f"Recovered previous session: {session.id}")

    session.add_status_callback(approve_tool_calls)
    # # Reschedule it (it's not necessary, but you can do it if you want).
    # await session.resume()
    logger.info("[bold green] Streaming messages... [/bold green]")
    async for msg in session.stream_messages():
        print_message(msg)
        if msg.get("message_type") == "MESSAGE_TYPE_TOOL_CONFIRMATION_REQUEST":
            await asyncio.sleep(2)
            logger.info(
                "[bold green] Sec-Gemini is asking for confirmation [/bold green]"
            )
            response = await session.get_confirmation_info()
            logger.info(json_format.MessageToJson(response))
            logger.info("Sending the confirmation now")
            await session.send_tool_confirmation(response.confirmation_info.id, True)
            logger.info("Confirmation sent")

    logger.info("\n[bold red]Cleanup: Deleting all sessions[/bold red]")
    sessions = await client.sessions()
    for s in sessions:
        logger.info(f"Deleting session {s.id}...")
        success = await s.delete()
        if success:
            logger.info(f"[green]Deleted {s.id}[/green]")
        else:
            logger.info(f"[red]Failed to delete {s.id}[/red]")

    logger.info("Closing client...")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
