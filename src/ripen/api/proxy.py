import asyncio
import os
import sys
import json
from typing import Optional
from mcp.client.sse import sse_client
from mcp.types import JSONRPCMessage
from mcp.shared.session import SessionMessage
from ripen.common.utils import get_logger

logger = get_logger("proxy")

async def run_stdio_proxy(team_url: Optional[str] = None):
    """
    Acts as a transparent bridge between an MCP Client and the Ripen Hub.
    Automatically tries Team Hub first, then falls back to Local Hub.
    """
    # 1. Collect candidates
    candidates = []
    
    # Environment variable has top priority
    env_url = os.environ.get("RIPEN_HUB_URL")
    if env_url:
        candidates.append(env_url)
    
    # Arg provided (usually the Team Hub)
    if team_url and team_url not in candidates:
        candidates.append(team_url)
    
    # Local fallback is always the final resort
    local_url = "http://localhost:8377"
    if local_url not in candidates:
        candidates.append(local_url)

    logger.info(f"Starting Adaptive Discovery. Candidates: {candidates}")
    
    for hub_url in candidates:
        logger.info(f"Attempting to connect to Hub: {hub_url}...")
        try:
            # We use a short timeout for the connection establishment
            async with asyncio.timeout(5.0):
                async with sse_client(f"{hub_url}/sse") as (read_stream, write_stream):
                    logger.info(f"Connected to Hub at {hub_url}")
                    
                    async def forward_from_hub_to_stdio():
                        try:
                            async for message in read_stream:
                                if isinstance(message, Exception):
                                    logger.error(f"Error from Hub stream: {message}")
                                    continue
                                sys.stdout.write(message.message.model_dump_json(by_alias=True, exclude_none=True) + "\n")
                                sys.stdout.flush()
                        except Exception as e:
                            logger.error(f"Hub-to-Stdio bridge failed: {e}")

                    async def forward_from_stdio_to_hub():
                        try:
                            while True:
                                line = await asyncio.get_event_loop().run_in_executor(
                                    None, sys.stdin.readline
                                )
                                if not line:
                                    break
                                
                                try:
                                    from mcp.types import JSONRPCMessage
                                    data = json.loads(line)
                                    msg_obj = JSONRPCMessage.model_validate(data)
                                    session_msg = SessionMessage(message=msg_obj)
                                    
                                    try:
                                        # Use timeout for sending to prevent hang if Hub becomes unresponsive
                                        await asyncio.wait_for(write_stream.send(session_msg), timeout=30.0)
                                    except asyncio.TimeoutError:
                                        logger.error("Forwarding to Hub timed out.")
                                    except Exception as e:
                                        logger.error(f"Error forwarding to Hub: {e}")
                                except json.JSONDecodeError:
                                    logger.error(f"Invalid JSON from stdio: {line.strip()}")
                                except Exception as e:
                                    logger.error(f"Validation error: {e}")
                        except Exception as e:
                            logger.error(f"Stdio-to-Hub bridge failed: {e}")

                    # Connection successful, run the bridge tasks
                    await asyncio.gather(
                        forward_from_hub_to_stdio(),
                        forward_from_stdio_to_hub()
                    )
                    return # Exit when connection is naturally closed
                    
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Connection failed for {hub_url}: {e}. Trying next candidate...")
            continue

    logger.error("All Hub candidates exhausted. Please ensure a Ripen Hub is running.")
    sys.exit(1)
