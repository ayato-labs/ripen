import aiofiles
import os
from shared_memory.common.utils import get_bank_dir, log_info, log_error, GlobalLock, sanitize_filename
import shutil
from typing import Dict, Any, Set

BANK_FILES = {
    "projectBrief.md": "Core requirements and goals.",
    "productContext.md": "Why this project exists and its scope.",
    "activeContext.md": "What we are working on now and recent decisions.",
    "systemPatterns.md": "Architecture, design patterns, and technical decisions.",
    "techContext.md": "Tech stack, dependencies, and some constraints.",
    "progress.md": "Status, roadmap, and what's next.",
    "decisionLog.md": "Record of significant technical choices.",
}

async def update_access(filename: str):
    \"\"\"Updates the last_accessed metadata for a bank file.\"\"\"
    # In a real implementation, this would update a separate metadata store
    # for bank files, similar to the main database entities.
    pass

async def read_bank_files(query: str | None = None) -> Dict[str, str]:
    \"\"\"
    Reads memory bank files from the data/bank directory.
    If a query is provided, it performs a simple keyword search across the files.
    If no query is provided, it returns a summary of available files (metadata only)
    to prevent massive data dumps to the LLM context.
    \"\"\"
    bank_dir = get_bank_dir()
    bank_data = {}
    
    if not os.path.exists(bank_dir):
        log_info(f"Bank directory not found: {bank_dir}")
        return {}

    try:
        found_files: Set[str] = set()
        
        # 1. Handle search query if present
        if query:
            for filename in os.listdir(bank_dir):
                path = os.path.join(bank_dir, filename)
                if os.path.isfile(path):
                    try:
                        async with aiofiles.open(path, encoding="utf-8") as f:
                            content = await f.read()
                            # Search in content
                            if (query.lower() in content.lower() or 
                        query.lower() in filename.lower()):
                                bank_data[filename] = content
                                found_files.add(filename)
                                await update_access(filename)
                    except Exception as e:
                        log_error(f"Error reading bank file {filename}", e)
        
        # 2. If no query or no matches, return a summary (Metadata-only mode)
        # This prevents the LLM from receiving the entire bank content at once.
        if not bank_data:
            summary = ["### Memory Bank Summary (No query provided)"]
            summary.append("To view specific contents, provide a query.")
            summary.append("")
            summary.append("| Filename | Description | Last Modified |")
            summary.append("| :--- | :--- | :--- |")
            
            for filename in os.listdir(bank_dir):
                path = os.path.join(bank_dir, filename)
                if os.path.isfile(path):
                    mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
                    desc = BANK_FILES.get(filename, "Custom repository documentation")
                    summary.append(f"| {filename} | {desc} | {mtime} |")
            
            bank_data["summary.md"] = \"\n\".join(summary)

        return bank_data

    except Exception as e:
        log_error("Failed to read memory bank", e)
        return {"error": str(e)}

async def write_bank_file(filename: str, content: str):
    \"\"\"Writes or updates a file in the memory bank.\"\"\"
    bank_dir = get_bank_dir()
    os.makedirs(bank_dir, exist_ok=True)
    
    # Enforce safe filename and .md extension
    safe_name = sanitize_filename(filename)
    path = os.path.join(bank_dir, safe_name)
    
    async with GlobalLock(f"bank_{safe_name}"):
        try:
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(content)
            log_info(f"Updated bank file: {safe_name}")
        except Exception as e:
            log_error(f"Failed to write bank file {safe_name}", e)
            raise
