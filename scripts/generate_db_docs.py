import sys
import os
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from shared_memory.infra.schema import TABLES, CURRENT_SCHEMA_VERSION

def generate_markdown():
    lines = [
        "# Database Schema Documentation",
        f"\n**Current Schema Version: {CURRENT_SCHEMA_VERSION}**",
        "\nThis document is automatically generated from `src/shared_memory/infra/schema.py`. **Do not edit manually.**",
        "\n## Table of Contents"
    ]
    
    # TOC
    for table_name in TABLES:
        lines.append(f"- [{table_name}](#{table_name})")
    
    for table_name, table in TABLES.items():
        lines.append(f"\n<a id='{table_name}'></a>")
        lines.append(f"## Table: `{table_name}`")
        lines.append(f"\n{table.description}")
        lines.append("\n| Column | Type | PK | Default | Description |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        
        for col in table.columns:
            pk = "✅" if col.is_primary_key else ""
            default = f"`{col.default}`" if col.default else "-"
            lines.append(f"| `{col.name}` | `{col.type}` | {pk} | {default} | {col.description} |")
        
        if table.indices:
            lines.append("\n**Indices:**")
            for idx in table.indices:
                unique = " (Unique)" if idx.is_unique else ""
                lines.append(f"- `{idx.name}`: `{', '.join(idx.columns)}`{unique}")
    
    return "\n".join(lines)

if __name__ == "__main__":
    output_path = Path("docs/db_schema.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = generate_markdown()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Documentation successfully generated at {output_path}")
