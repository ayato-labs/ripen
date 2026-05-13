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
    candidates = []
    env_url = os.environ.get("RIPEN_HUB_URL")
    if env_url:
        candidates.append(env_url)
    if team_url and team_url not in candidates:
        candidates.append(team_url)
    
    local_url = "http://localhost:8377"
    if local_url not in candidates:
        candidates.append(local_url)

    logger.info(f"Starting Adaptive Discovery. Candidates: {candidates}")
    
    for hub_url in candidates:
        logger.info(f"Attempting to connect to Hub: {hub_url}...")
        try:
            # 1. Establish connection with a strict timeout
            # We use a wrapper to separate connection phase from stream phase
            async with sse_client(f"{hub_url.rstrip('/')}/sse") as (read_stream, write_stream):
                logger.info(f"Successfully connected to Hub: {hub_url}")
                
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
                                data = json.loads(line)
                                msg_obj = JSONRPCMessage.model_validate(data)
                                session_msg = SessionMessage(message=msg_obj)
                                
                                # Send to hub (no global timeout here, let it run)
                                await write_stream.send(session_msg)
                            except json.JSONDecodeError:
                                logger.error(f"Invalid JSON from stdio: {line.strip()}")
                            except Exception as e:
                                logger.error(f"Validation/Forward error: {e}")
                    except Exception as e:
                        logger.error(f"Stdio-to-Hub bridge failed: {e}")

                # Run both directions until one of them closes
                await asyncio.gather(
                    forward_from_hub_to_stdio(),
                    forward_from_stdio_to_hub()
                )
                logger.info(f"Connection to {hub_url} closed naturally.")
                return 

        except Exception as e:
            logger.warning(f"Connection attempt failed for {hub_url}: {e}")
            continue

    logger.error("All Hub candidates exhausted. Please ensure a Ripen Hub is running.")
    sys.exit(1)
