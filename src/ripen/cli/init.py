import json
import os
import socket
from pathlib import Path
from typing import Any

from ripen.common.utils import get_logger, safe_main_executor

logger = get_logger("init")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    logger.info("""
    \033[1;32m      
    ██████╗ ██╗██████╗ ███████╗███╗   ██╗
    ██╔══██╗██║██╔══██╗██╔════╝████╗  ██║
    ██████╔╝██║██████╔╝█████╗  ██╔██╗ ██║
    ██╔══██╗██║██╔═══╝ ██╔══╝  ██║╚██╗██║
    ██║  ██║██║██║     ███████╗██║ ╚████║
    ╚═╝  ╚═╝╚═╝╚═╝     ╚══════╝╚═╝  ╚═══╝
    \033[0m
    \033[1;36m🧠 Knowledge Hub for AI Agents\033[0m
    ====================================
    """)


def ask_question(question: str, default: Any = None, options: list[str] | None = None) -> str:
    prompt = f"\n\033[1;34m? \033[0m{question}"
    if options:
        prompt += f" ({'/'.join(options)})"
    if default is not None:
        prompt += f" [\033[1;37m{default}\033[0m]"
    prompt += ": "

    while True:
        choice = input(prompt).strip()
        if not choice and default is not None:
            return str(default)
        if options and choice.lower() not in [o.lower() for o in options]:
            logger.info(
                f"\033[1;31m! Invalid choice. Please choose from: {', '.join(options)}\033[0m"
            )
            continue
        if choice:
            return choice


def configure_ripen_home(config: dict, existing_config: dict):
    """Prompts for and resolves the base directory for knowledge storage."""
    default_home = Path.home() / ".ripen"
    ripen_home = ask_question("Where should knowledge be stored?", default=str(default_home))
    config["ripen_home"] = str(Path(ripen_home).absolute())

    ripen_home_path = Path(config["ripen_home"])
    config_file = ripen_home_path / "config.json"
    if config_file.exists():
        try:
            with open(config_file, encoding="utf-8") as f:
                existing_config.update(json.load(f))
            logger.info(f"Loaded existing configuration from {config_file}")
        except Exception as e:
            logger.debug(f"Failed to load existing config.json: {e}")


def configure_llm_provider(config: dict, existing_config: dict):
    """Configures the LLM provider (Gemini / Ollama / None) and its models/keys."""
    logger.info("\n\033[1;33mStep 2: LLM Provider\033[0m (Required for knowledge distillation)")
    default_provider = existing_config.get("llm_provider") or "ollama"
    provider = ask_question(
        "Which LLM provider would you like to use?",
        default=default_provider,
        options=["gemini", "ollama", "none"],
    )
    config["llm_provider"] = provider.lower()

    if provider.lower() == "gemini":
        logger.info("\n\033[1;31m!!! PRIVACY WARNING !!!\033[0m")
        logger.info(
            "Using an external LLM like Gemini will send snippets of your codebase and AI agent "
            "reasoning"
        )
        logger.info(
            "to Google's servers for background knowledge distillation. For strict enterprise "
            "or confidential"
        )
        logger.info("environments, we strongly recommend using a local LLM via Ollama instead.")
        
        default_api_key = existing_config.get("google_api_key") or ""
        masked_default = None
        if default_api_key:
            if len(default_api_key) > 12:
                masked_default = f"{default_api_key[:6]}...{default_api_key[-4:]}"
            else:
                masked_default = "********"

        api_key = ask_question(
            "Enter your GOOGLE_API_KEY (from https://aistudio.google.com/):",
            default=masked_default
        )
        if masked_default and api_key == masked_default:
            config["google_api_key"] = default_api_key
        else:
            config["google_api_key"] = api_key
        if len(api_key) < 20:
            logger.info("\033[1;31m! Warning: That API key looks a bit short.\033[0m")

        default_ai_model = existing_config.get("google_ai_model") or "gemma-4-31b-it"
        gemini_model = ask_question(
            "Which Gemini/Gemma generative model would you like to use?",
            default=default_ai_model
        )
        config["google_ai_model"] = gemini_model
        config["google_compression_model"] = gemini_model

    elif provider.lower() == "ollama":
        default_url = existing_config.get("ollama_base_url") or "http://localhost:11434"
        config["ollama_base_url"] = ask_question(
            "Ollama API URL?", default=default_url
        )
        default_model = existing_config.get("ollama_model") or "gemma4:e2b"
        config["ollama_model"] = ask_question("Ollama Model?", default=default_model)
        logger.info("\n\033[1;33mNote:\033[0m Make sure Ollama is running (`ollama serve`)!")


def configure_embeddings(config: dict, existing_config: dict):
    """Configures the embedding engine (FastEmbed / Gemini) and warns on switching."""
    logger.info("\n\033[1;33mStep 3: Embedding Configuration\033[0m")
    has_api_key = bool(config.get("google_api_key")) or bool(
        os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    )
    
    engine_options = ["fastembed", "gemini"] if has_api_key else ["fastembed"]
    default_engine = existing_config.get("embedding_engine") or "fastembed"
    
    if default_engine == "gemini" and not has_api_key:
        default_engine = "fastembed"
        
    if not has_api_key:
        logger.info(
            "Note: Only local embeddings (fastembed) are available "
            "since no Google API Key is configured."
        )
        config["embedding_engine"] = "fastembed"
    else:
        engine = ask_question(
            "Which embedding engine would you like to use? "
            "(fastembed is local, gemini is cloud API)",
            default=default_engine,
            options=engine_options
        )
        config["embedding_engine"] = engine.lower()
        
        # Check if engine has changed from previous setup
        if (
            existing_config
            and existing_config.get("embedding_engine")
            != config["embedding_engine"]
        ):
            logger.info("\n\033[1;31m⚠️  WARNING: Embedding Engine Change Detected !!!\033[0m")
            logger.info(
                "Changing the embedding engine requires recalculating "
                "(re-indexing) all stored memories."
            )
            logger.info(
                "An automatic re-embedding process will run on the next "
                "server start to update all dimensions."
            )
            
        if config["embedding_engine"] == "gemini":
            default_embed_model = (
                existing_config.get("google_embedding_model") or "models/gemini-embedding-2"
            )
            gemini_embed_model = ask_question(
                "Which Gemini embedding model would you like to use?",
                default=default_embed_model
            )
            config["google_embedding_model"] = gemini_embed_model
            
            if (
                existing_config
                and existing_config.get("google_embedding_model")
                != config["google_embedding_model"]
            ):
                logger.info("\n\033[1;31m⚠️  WARNING: Embedding Model Change Detected !!!\033[0m")
                logger.info(
                    "Changing the embedding model requires recalculating "
                    "(re-indexing) all stored memories."
                )
                logger.info(
                    "An automatic re-embedding process will run on the next "
                    "server start to update all dimensions."
                )


def main():
    clear_screen()
    print_banner()

    logger.info("Welcome to Ripen! Let's get your brain infrastructure set up.")
    logger.info("\n\033[1;33m--- Hub Mode (Setting up a local knowledge server) ---\033[0m")
    
    config = {}
    existing_config = {}

    # 1. Base Directory
    configure_ripen_home(config, existing_config)

    # 2. LLM Provider
    configure_llm_provider(config, existing_config)

    # 3. Embedding Configuration
    configure_embeddings(config, existing_config)

    # 4. Port & Transport
    config["sse_port"] = existing_config.get("sse_port") or 8377
    config["default_transport"] = existing_config.get("default_transport") or "sse"

    # 5. Save Config
    ripen_home_path = Path(config["ripen_home"])
    config_file = ripen_home_path / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    logger.info(f"\n\033[1;32m✅ Configuration saved to {config_file}\033[0m")

    logger.info("\n" + "=" * 40)
    logger.info("\033[1;32m🎉 Hub Setup Complete!\033[0m")
    logger.info("\nTo start your Hub server:")
    logger.info("  \033[1;36mripen\033[0m (or run ripen-hub.exe)")
    
    def get_local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "127.0.0.1"

    local_ip = get_local_ip()
    port = config.get("sse_port") or 8377
    
    logger.info(f"\nClient Connection URL (Local):  \033[1;33mhttp://localhost:{port}/mcp\033[0m")
    if local_ip != "127.0.0.1":
        logger.info(f"Client Connection URL (Remote): \033[1;33mhttp://{local_ip}:{port}/mcp\033[0m")
    
    logger.info("\nTo connect your agents, add this to your client config (e.g., mcp_config.json):")
    
    target_ip = local_ip if local_ip != "127.0.0.1" else "localhost"
    logger.info(f"""
    "ripen": {{
      "command": "npx",
      "args": ["-y", "@sammacbeth/mcp-remote", "http://{target_ip}:{port}/mcp"]
    }}
    """)
    logger.info("=" * 40)


if __name__ == "__main__":
    safe_main_executor(main)()
