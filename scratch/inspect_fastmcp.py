
import inspect
from fastmcp import FastMCP

def inspect_fastmcp():
    print("FastMCP.__init__ signature:")
    print(inspect.signature(FastMCP.__init__))
    print("\nFastMCP.tool signature:")
    print(inspect.signature(FastMCP.tool))

if __name__ == "__main__":
    inspect_fastmcp()
