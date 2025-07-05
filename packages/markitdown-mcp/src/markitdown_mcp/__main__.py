import os
from fastmcp import FastMCP
from markitdown import MarkItDown

# Initialize FastMCP server
mcp = FastMCP("markitdown")

def check_plugins_enabled() -> bool:
    return os.getenv("MARKITDOWN_ENABLE_PLUGINS", "false").strip().lower() in (
        "true",
        "1",
        "yes",
    )

@mcp.tool
def convert_to_markdown(uri: str) -> str:
    """Convert a resource described by an http:, https:, file: or data: URI to markdown"""
    return MarkItDown(enable_plugins=check_plugins_enabled()).convert_uri(uri).markdown

def main():
    # Run the server (defaults to stdio transport)
    mcp.run()

if __name__ == "__main__":
    main()