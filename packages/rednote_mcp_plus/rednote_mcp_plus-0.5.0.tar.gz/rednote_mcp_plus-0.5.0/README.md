# RedNote-MCP-Plus

<p align="center"><img src= "logo.png" width="600"/></p>



[![English](https://img.shields.io/badge/English-Click-yellow)](docs/README.en.md)
[![简体中文](https://img.shields.io/badge/简体中文-点击查看-orange)](README.md)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![PyPI version](https://badge.fury.io/py/rednote_mcp_plus.svg)](https://badge.fury.io/py/rednote_mcp_plus)

⚙️ MCP server with a more comprehensive suite of tools for RedNote(XiaoHongShu, xhs).

```
brew install uv
pip install playwright
playwright install
```

## MCP Server Config

```
{
  "mcpServers": {
    "RedNote_MCP_Plus": {
      "command": "uvx",
      "args": [
        "rednote_mcp_plus"
      ]
    }
  }
}
```

## MCP Inspector

```
brew install node
npx @modelcontextprotocol/inspector uvx rednote_mcp_plus
```