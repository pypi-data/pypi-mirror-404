"""MCP Server for extracting AI companies and funding information from articles."""

import json
import os
from typing import Any

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize MCP server
server = Server("company-mcp")

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")


def get_openrouter_client() -> OpenAI:
    """Create OpenRouter client."""
    return OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )


async def fetch_article_content(url: str) -> str:
    """Fetch and extract text content from a URL."""
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Get text content
        text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)


def extract_companies_with_llm(content: str) -> list[dict[str, Any]]:
    """Use LLM to extract companies and analyze AI + funding status."""
    client = get_openrouter_client()

    prompt = f"""你是一个专业的信息提取助手。请从以下文章内容中提取所有公司名称，并判断每个公司是否同时满足以下两个条件：
1. 是AI领域的公司（文章中有提及该公司与AI/人工智能相关）
2. 有融资信息（文章中有提及该公司的融资情况）

注意：判断标准仅根据文章中是否有明确说明，不要根据你的知识来判断。

请以JSON格式输出，格式如下：
[
    {{
        "company": "公司名称",
        "reason": "判断理由（说明文章中如何提及该公司的AI属性和融资信息，如果没有则说明）",
        "match": true或false（只有同时满足AI领域+有融资信息才为true）
    }}
]

文章内容：
{content[:15000]}

请直接输出JSON数组，不要输出其他内容。"""

    response = client.chat.completions.create(
        model="xiaomi/mimo-v2-flash",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
    )

    result_text = response.choices[0].message.content.strip()

    # Try to parse JSON from the response
    # Handle cases where the response might have markdown code blocks
    if result_text.startswith("```"):
        lines = result_text.split("\n")
        result_text = "\n".join(lines[1:-1])

    try:
        companies = json.loads(result_text)
        return companies
    except json.JSONDecodeError:
        # Try to find JSON array in the response
        start = result_text.find("[")
        end = result_text.rfind("]") + 1
        if start != -1 and end > start:
            try:
                companies = json.loads(result_text[start:end])
                return companies
            except json.JSONDecodeError:
                pass
        return [{"error": "Failed to parse LLM response", "raw": result_text}]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="extract_companies",
            description="从文章URL中提取所有公司名称，并标记是否为AI领域+有融资的公司",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "文章URL地址"
                    }
                },
                "required": ["url"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name == "extract_companies":
        url = arguments.get("url")
        if not url:
            return [TextContent(type="text", text=json.dumps({"error": "URL is required"}, ensure_ascii=False))]

        try:
            # Fetch article content
            content = await fetch_article_content(url)

            # Extract companies using LLM
            companies = extract_companies_with_llm(content)

            result = {
                "url": url,
                "companies": companies,
                "total_count": len(companies),
                "match_count": sum(1 for c in companies if c.get("match", False))
            }

            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        except httpx.HTTPError as e:
            return [TextContent(type="text", text=json.dumps({"error": f"Failed to fetch URL: {str(e)}"}, ensure_ascii=False))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": f"Error: {str(e)}"}, ensure_ascii=False))]

    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False))]


async def run_server():
    """Run the MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Entry point for the server."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
