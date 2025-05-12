from typing import List
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
import logging

logger = logging.getLogger(__name__)

# TODO: 設定値は将来的にYAMLや環境変数から取得する
PLAYWRIGHT_MCP_SSE_URL = "http://localhost:8931/sse"

async def load_playwright_tools(transport: str = "sse") -> List[BaseTool]:
    """
    Playwright MCP Server から利用可能なツールをロードするユーティリティ関数。
    transport: "sse" または "stdio" を指定可能（デフォルトはSSE）。
    Returns:
        List[BaseTool]: 利用可能なLangChainツールのリスト
    """
    if transport == "sse":
        client_config = {
            "playwright_sse": {
                "url": PLAYWRIGHT_MCP_SSE_URL,
                "transport": "sse"
            }
        }
        server_name = "playwright_sse"
    elif transport == "stdio":
        client_config = {
            "playwright_stdio": {
                "command": "npx",
                "args": ["@playwright/mcp@latest", "--headless"],
                "transport": "stdio"
            }
        }
        server_name = "playwright_stdio"
    else:
        raise ValueError(f"Unsupported transport: {transport}")

    try:
        async with MultiServerMCPClient(client_config) as mcp_client:
            tools = await mcp_client.get_tools(server_name=server_name)
        return tools
    except Exception as e:
        logger.error(f"MCPツールのロードに失敗しました: {e}")
        return [] 