import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


def get_config_paths():
    """Detect potential MCP configuration file paths across platforms."""
    home = Path.home()
    appdata = os.environ.get("APPDATA")
    
    paths = {}
    
    # Windows
    if appdata:
        paths.update({
            "Claude Desktop (Windows)": Path(appdata) / "Claude" / "claude_desktop_config.json",
            "Cursor (Cline/Roo) [Windows]": Path(appdata) / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            "VS Code (Cloud Code) [Windows]": Path(appdata) / "Code" / "User" / "mcp.json",
        })
    
    # macOS
    macos_support = home / "Library" / "Application Support"
    if macos_support.exists():
        paths.update({
            "Claude Desktop (macOS)": macos_support / "Claude" / "claude_desktop_config.json",
            "Cursor (Cline/Roo) [macOS]": macos_support / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            "VS Code (Cloud Code) [macOS]": macos_support / "Code" / "User" / "mcp.json",
        })
        
    # Linux / Generic
    paths.update({
        "Antigravity (Central)": home / ".gemini" / "antigravity" / "mcp_config.json",
        "Gemini CLI": home / ".gemini" / "settings.json",
    })
    
    return paths


def get_prompt_files() -> list[Path]:
    """Identify system prompt files to inject instructions into."""
    cwd = Path.cwd()
    home = Path.home()

    return [
        home / ".gemini" / "GEMINI.md",
        cwd / ".gemini" / "GEMINI.md",
        cwd / ".cursorrules",
        cwd / ".clinerules",
    ]


def get_server_command(transport: str = "stdio", port: int = 8377):
    """Determine the best command to run the Ripen server."""
    
    # Check if 'ripen' is in PATH (PyPI installed)
    import shutil
    ripen_path = shutil.which("ripen")
    
    if ripen_path:
        cmd = ["ripen"]
    else:
        # Fallback to uvx
        cmd = ["uvx", "ripen"]
        
    if transport == "sse":
        cmd.extend(["--sse", "--port", str(port)])
    
    return cmd


RIPEN_INSTRUCTION = """
# RIPEN MEMORY SERVER INSTRUCTION
You have access to Ripen MCP (the evolution of SharedMemoryServer).
- Use it to maintain project-wide entities, relations, and factual observations.
- Always call `read_memory(query=...)` at the start of a task to gather relevant context.
- Use `save_memory` to persist important architectural roles, technical decisions, and multi-step progress.
- Knowledge 'ripens' over time based on access frequency and importance.
"""


def register_single_mcp(config_paths, server_name, mcp_config, dry_run=False):
    """Register a single MCP server in all detected configuration files."""
    print(f"\n--- Registering {server_name} ---")
    for name, path in config_paths.items():
        if not path.parent.exists():
            continue

        try:
            config = {}
            if path.exists():
                try:
                    with open(path, encoding="utf-8") as f:
                        config = json.load(f)
                except json.JSONDecodeError:
                    print(f"  [WARN] {name}: Failed to parse {path}. Skipping.")
                    continue

            # Standard mcpServers
            if "mcpServers" not in config:
                config["mcpServers"] = {}
            
            config["mcpServers"][server_name] = mcp_config

            if not dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                print(f"  [SUCCESS] Updated {name}")
            else:
                print(f"  [DRY RUN] Would update {name}")

        except Exception as e:
            sys.stderr.write(f"  [ERROR] Failed to update {name}: {e}\n")


def register_mcp(dry_run=False, transport="stdio", port=8377):
    config_paths = get_config_paths()
    server_name = "ripen"

    cmd = get_server_command(transport, port)
    
    mcp_config = {
        "command": cmd[0],
        "args": cmd[1:],
        "env": {}
    }

    # Pass API key if present in current environment
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if api_key:
        mcp_config["env"]["GOOGLE_API_KEY"] = api_key

    register_single_mcp(config_paths, server_name, mcp_config, dry_run=dry_run)

    print(f"\n--- System Prompt Integration ---")
    prompt_files = get_prompt_files()
    for p in prompt_files:
        if not p.parent.exists() and not dry_run:
            continue

        try:
            content = ""
            if p.exists():
                with open(p, encoding="utf-8") as f:
                    content = f.read()

            if "RIPEN_MEMORY_SERVER_INSTRUCTION" in content:
                print(f"  [SKIP] {p.name}: Instructions already present.")
                continue

            new_content = content.strip() + "\n\n" + RIPEN_INSTRUCTION.strip() + "\n"

            if not dry_run:
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"  [SUCCESS] Updated {p.name}")
            else:
                print(f"  [DRY RUN] Would update {p.name}")
        except Exception as e:
            sys.stderr.write(f"  [ERROR] Failed to update {p.name}: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description=("Register Ripen as an MCP tool and update system prompts.")
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done.")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], help="Default transport.")
    parser.add_argument("--port", type=int, default=8377, help="SSE port.")
    
    args = parser.parse_args()
    register_mcp(dry_run=args.dry_run, transport=args.transport, port=args.port)


if __name__ == "__main__":
    main()
