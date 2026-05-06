import os

def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if '\\"' in content:
            # We want to replace \ " with just "
            # BUT we only want to do this if it's a syntax error.
            # It's safest to replace all \"\"\" with """ and \" with " where appropriate.
            # Actually, just replacing \\" with " is risky if there are actual escaped quotes in strings.
            # Let's use a simpler replace. The issue was introduced by a copy-paste tool error.
            new_content = content.replace('\\"', '"')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed {filepath}")
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

files_to_check = [
    r"src/shared_memory/common/utils.py",
    r"src/shared_memory/core/logic.py",
    r"src/shared_memory/common/config.py",
    r"src/shared_memory/api/server.py",
    r"src/shared_memory/infra/llm.py",
]

for f in files_to_check:
    fix_file(f)
