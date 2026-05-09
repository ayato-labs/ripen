
import asyncio
import inspect
from shared_memory.api.server import save_memory, read_memory

def debug_docstrings():
    for func in [save_memory, read_memory]:
        print(f"Function: {func.__name__}")
        print(f"  Raw doc: {repr(func.__doc__)}")
        print(f"  inspect.getdoc: {repr(inspect.getdoc(func))}")

if __name__ == "__main__":
    debug_docstrings()
