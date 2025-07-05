# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## Project Overview

MarkItDown is a Python utility for converting various file formats to Markdown for use with LLMs and
text analysis pipelines. The project is structured as a monorepo with three packages:

- **markitdown**: Main library for file-to-markdown conversion
- **markitdown-mcp**: MCP (Model Context Protocol) server wrapper
- **markitdown-sample-plugin**: Example plugin demonstrating the plugin architecture

## Development Commands

### Building

```bash
# Install Hatch (required build tool)
pip install hatch

# Build individual packages
cd packages/markitdown && hatch build
cd packages/markitdown-mcp && hatch build
cd packages/markitdown-sample-plugin && hatch build

# Docker build
docker build -t markitdown:latest .
```

### Testing

```bash
# Run tests for main package
cd packages/markitdown
hatch test

# Run tests for a specific test file
hatch test tests/test_markitdown.py

# Run a specific test
hatch test tests/test_markitdown.py::TestMarkItDown::test_convert_pdf
```

### Type Checking

```bash
# Type check main package
cd packages/markitdown
hatch run types:check

# Type check MCP server
cd packages/markitdown-mcp
hatch run types:check
```

### Linting

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run linting on all files
pre-commit run --all-files
```

### Development Setup

```bash
# Install markitdown with all optional dependencies
cd packages/markitdown
pip install -e ".[all]"

# Install MCP server
cd packages/markitdown-mcp
pip install -e .

# Install sample plugin
cd packages/markitdown-sample-plugin
pip install -e .
```

## Supported File Types

### Document Formats

- **PDF** (.pdf) - Plain text extraction
- **Microsoft Word** (.docx) - Preserves headings and tables
- **Microsoft Excel** (.xlsx, .xls) - Converts spreadsheets to markdown tables
- **Microsoft PowerPoint** (.pptx) - Extracts slides with headings, tables, and image alt text
- **EPUB** (.epub) - E-book format conversion
- **Outlook Messages** (.msg) - Extracts email headers and body

### Web Content

- **HTML** (.html, .htm) - General HTML to markdown
- **Wikipedia Pages** - Special handling for Wikipedia articles
- **Bing Search Results** - Extracts organic search results
- **YouTube Videos** - Extracts title, description, and transcripts
- **RSS/Atom Feeds** (.rss, .atom, .xml) - Converts feeds to markdown

### Code & Text Files

- **Plain Text** (.txt, .text)
- **Markdown** (.md, .markdown)
- **JSON** (.json)
- **XML** (.xml)
- **YAML** (.yaml, .yml)
- **TOML** (.toml)
- **Source Code**: Python (.py), JavaScript (.js, .mjs, .ts, .tsx, .jsx), C/C++ (.c, .h, .cpp,
  .hpp), C# (.cs), F# (.fs), Java (.java), Go (.go), Rust (.rs), Ruby (.rb), R (.r), PHP (.php),
  Visual Basic (.vb), Objective-C (.m), Lua (.lua), SQL (.sql), Shell scripts (.sh, .ps1, .bat)
- **Stylesheets** (.css, .scss)

### Data Formats

- **CSV** (.csv) - Converts to markdown tables
- **Jupyter Notebooks** (.ipynb) - Preserves code cells and markdown

### Media Files

- **Images** (.jpg, .jpeg, .png) - Extracts metadata and generates descriptions (with LLM)
- **Audio** (.wav, .mp3, .m4a, .mp4) - Extracts metadata and transcribes speech

### Archive Files

- **ZIP** (.zip) - Extracts and converts all contained files

### Optional Advanced Support

- **Azure Document Intelligence** - When configured, provides enhanced extraction for:
  - Complex PDFs with tables and forms
  - Images with text (OCR)
  - Documents with advanced layouts
  - Supports: .docx, .pptx, .xlsx, .pdf, .jpg, .jpeg, .png, .bmp, .tiff

## Architecture

### Package Structure

- Each package has its own `pyproject.toml` with independent versioning
- Shared dependencies are managed through optional feature groups
- Plugin system allows extending conversion capabilities

### Key Components

**DocumentConverter Base Class** (packages/markitdown/src/markitdown/\_converters.py)

- Abstract base for all converters
- Reads from file-like streams (no temporary files)
- Returns DocumentConverterResult with text_content and metadata

**MarkItDown Class** (packages/markitdown/src/markitdown/**init**.py)

- Main API entry point
- Manages converter registration and selection
- Handles plugin loading when enabled

**MCP Server** (packages/markitdown-mcp/)

- Wraps markitdown functionality for MCP protocol
- Supports STDIO and HTTP/SSE transports
- Enables plugin system via MARKITDOWN_ENABLE_PLUGINS env var

### Converter Architecture

- Each file type has a dedicated converter class
- Converters are registered with the MarkItDown instance
- MIME type detection determines which converter to use
- Fallback to PlainTextConverter for unknown types

### Plugin System

- Plugins are Python packages with entry point: `markitdown.converters`
- Disabled by default, enable with `enable_plugins=True` or `--use-plugins`
- Sample plugin demonstrates pattern for custom converters

## Docker and MCP Setup

### Docker Configuration

- Base image: `python:3.13-slim-bullseye`
- System dependencies: ffmpeg, exiftool
- Runs as non-root user (configurable via USERID/GROUPID build args)
- Environment variables set EXIFTOOL_PATH and FFMPEG_PATH

### MCP Server Architecture

**FastMCP v2 Implementation:**

- Migrated from vanilla MCP SDK to FastMCP v2 (jlowin/fastmcp)
- Uses FastMCP v2.9.0+ with MCP SDK 1.9.4 internally
- Properly handles 'initialized' notification in protocol handshake
- Single tool exposed: `convert_to_markdown(uri: str) -> str`
- Supports plugin system via `MARKITDOWN_ENABLE_PLUGINS` environment variable

**Dependencies:**

```toml
dependencies = [
  "fastmcp>=0.1.0",
  "markitdown[all]>=0.1.1,<0.2.0",
]
```

### MCP Server Docker

**Build Context:**

- Dockerfile located at: `packages/markitdown-mcp/Dockerfile`
- Must be built from repository root: `docker build -f packages/markitdown-mcp/Dockerfile -t
mcp/markitdown:latest .`
- Uses `COPY . /app` expecting full repository structure

**Working Configuration:**

- Image name: `mcp/markitdown:latest`
- Transport: STDIO (default)
- Volume mount: `/Users/stuartsaunders:/workdir` (absolute path required for Claude Desktop/Cursor)
- Labels: `mcp.service=markitdown`, `mcp.client=<client-name>`
- Environment: `MCP_TRANSPORT=stdio`

**Docker Labels for Multi-Client Support:**

- `mcp.service=markitdown` - Identifies the service type
- `mcp.client=claude-code|cursor|claude-desktop` - Identifies which client spawned the container
- Enables targeted cleanup and monitoring

### MCP Server Testing

**JSON-RPC Protocol Test Sequence:**

```bash
# Test complete MCP handshake
cat > /tmp/mcp_test_input.txt << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF

# Run test sequence
docker run -i --rm -v "$PWD:/workdir" mcp/markitdown:latest < /tmp/mcp_test_input.txt
```

**Expected Responses:**

1. **Initialize Response:** Returns server capabilities and info
2. **Tools List Response:** Returns single tool `convert_to_markdown` with schema
3. **No errors:** Server should handle 'initialized' notification without issues

**Individual Tool Testing:**

```bash
# Test convert_to_markdown tool
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"convert_to_markdown","arguments":{"uri":"file:///workdir/README.md"}}}' | docker run -i --rm -v "$PWD:/workdir" mcp/markitdown:latest
```

### Troubleshooting

**Common Issues:**

1. **"Invalid request parameters" for tools/list:**

   - Issue: Using vanilla MCP SDK instead of FastMCP v2
   - Solution: Ensure `fastmcp>=0.1.0` dependency and FastMCP v2 implementation

2. **"Connection closed" errors:**

   - Issue: Volume mount path problems or environment variable expansion
   - Solution: Use absolute paths like `/Users/stuartsaunders:/workdir`

3. **Docker image not found:**

   - Issue: Image built in different Docker context (OrbStack vs Docker Desktop)
   - Solution: Check active context with `docker context ls` and rebuild if needed

4. **"initialized" notification errors:**
   - Issue: Server doesn't handle MCP protocol handshake correctly
   - Solution: FastMCP v2 resolves this - vanilla MCP SDK requires custom handling

**Debug Commands:**

```bash
# Check running MCP containers
docker ps --filter "label=mcp.service=markitdown"

# View container logs
docker logs <container-id>

# Test Docker image directly
docker run --rm mcp/markitdown:latest --help

# Verify FastMCP version in container
docker run --rm mcp/markitdown:latest python -c "import fastmcp; print(fastmcp.__version__)"
```

## Testing Approach

- Tests use pytest framework via hatch
- Test files mirror source structure in `tests/` directory
- Mock external dependencies where appropriate
- Test data files in `tests/test_files/`
- Coverage tracking excludes type stubs and test files

## Code Style

- Python 3.10+ required (supports up to 3.13)
- Black formatter (v23.7.0) enforced via pre-commit
- Type hints encouraged, checked with mypy
- Follow existing patterns for new converters
