# autots-mcp

Convenience package to install AutoTS with MCP (Model Context Protocol) dependencies.

## Installation

```bash
pip install autots-mcp
```

## Usage

After installation, you can use AutoTS with MCP support:

```python
from autots import AutoTS

# Use AutoTS as normal
model = AutoTS()
```

The MCP server can be invoked via:

```bash
autots-mcp
```

## About

This is a convenience wrapper package that has no code of its own. It simply declares `autots[mcp]` as a dependency to make installation easier in environments where optional dependency paths are not easy or not allowed.

For full AutoTS documentation, visit: https://github.com/winedarksea/AutoTS

## MCP Server
```json
{
  "mcpServers": {
    "autots": {
      "command": "autots-mcp"
    }
  }
}
```
mcp-name: io.github.winedarksea/AutoTS
