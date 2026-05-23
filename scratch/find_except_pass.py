import os
import re

def find_except_pass(root_dir):
    pattern = re.compile(r'except\s+([^:]+):\s*\n\s*pass')
    # より一般的なもの：コメントがあっても pass するケースなど
    # または except のブロック内で logger も print も raise も yield も return もなく、
    # pass だけで終わっているものを探す
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 除外するディレクトリ
        if any(p in dirpath for p in [".venv", "venv", ".git", "__pycache__", "build", "dist"]):
            continue
        for filename in filenames:
            if not filename.endswith('.py'):
                continue
            
            filepath = os.path.join(dirpath, filename)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # 単純な except ...: \n pass
            matches = list(re.finditer(r'except\s+([^:]+):\s*\r?\n\s*pass', content))
            for m in matches:
                # 行番号の特定
                line_no = content[:m.start()].count('\n') + 1
                print(f"Match: {filepath}:{line_no}")
                print(m.group(0))
                print("-" * 40)

if __name__ == "__main__":
    find_except_pass(r"c:\Users\saiha\My_Service\programing\MCP\Ripen")
