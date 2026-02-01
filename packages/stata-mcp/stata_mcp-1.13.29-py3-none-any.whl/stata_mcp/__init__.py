from importlib.metadata import version

from .cli import main as main
from .mcp_servers import stata_mcp

__version__ = version("stata-mcp")
__author__ = "Song Tan <sepine@statamcp.com>"


__all__ = [
    "stata_mcp",
]


if __name__ == "__main__":
    print(f"Hello Stata-MCP@v{__version__}")
    main()
