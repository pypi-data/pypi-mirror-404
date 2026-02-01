# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Company MCP 是一个 MCP 服务器，用于从文章中提取公司信息并判断是否为 AI 领域 + 有融资的公司。使用 OpenRouter 对接 xiaomi/mimo-v2-flash 模型。

## Commands

```bash
# 安装依赖
uv sync

# 运行 Stdio 模式服务器
uv run company-mcp

# 运行 SSE 模式服务器（HTTP）
uv run company-mcp-sse

# 使用 MCP Inspector 测试
npx @modelcontextprotocol/inspector company-mcp

# 构建发布包
python -m build

# 上传到 PyPI
twine upload dist/*
```

## Architecture

```
company_mcp/
├── __init__.py      # Package init
├── server.py        # Stdio transport MCP server (推荐用于 Claude Desktop)
└── sse_server.py    # SSE transport MCP server (HTTP 服务器模式)
```

- `server.py`: 使用 stdio 传输的 MCP 服务器，适合与 Claude Desktop 集成
- `sse_server.py`: 使用 SSE (Server-Sent Events) 传输的 HTTP 服务器，可通过网络访问

## Key Components

- **extract_companies tool**: 核心工具，接收 URL，返回公司列表及 AI+融资判断
- **fetch_article_content()**: 使用 httpx + BeautifulSoup 抓取并解析文章内容
- **extract_companies_with_llm()**: 调用 OpenRouter API 分析文章内容

## Environment Variables

- `OPENROUTER_API_KEY`: OpenRouter API 密钥
- `OPENROUTER_BASE_URL`: OpenRouter API 地址（默认 https://openrouter.ai/api/v1）
- `PORT`: SSE 服务器端口（默认 8000）
