"""MCP (Multi-Cursor Protocol) client helper and tool registry.

本モジュールでは、Executor が利用する Playwright MCP などのツールをロードするための
``MultiServerMCPClient`` 初期化ユーティリティと、ロード済みツールを保持する
``ToolRegistry`` を提供する。実際のツール呼び出しは Executor 実装側で行う想定だが、
ツールの取得とクライアント管理を一箇所に集約することで設定を簡潔にする。
"""

from __future__ import annotations

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

__all__ = [
    "ToolRegistry",
    "create_playwright_client_http",
    "create_playwright_client_stdio",
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


async def create_playwright_client_http(url: str, *, server_name: str = "playwright") -> MultiServerMCPClient:
    """HTTP 経由で Playwright MCP Server に接続する ``MultiServerMCPClient`` を生成する。"""

    client = MultiServerMCPClient()
    await client.add_server(server_name, url, transport="streamable_http")
    return client


async def create_playwright_client_stdio(
    *, server_name: str = "playwright", headless: bool = True
) -> MultiServerMCPClient:
    """Stdio 接続で Playwright MCP Server をサブプロセス起動し、クライアントを生成する。"""

    client = MultiServerMCPClient()
    args: list[str] = ["@playwright/mcp@latest"]
    if headless:
        args.append("--headless")
    await client.add_stdio_server(server_name, command="npx", args=args)
    return client


# ---------------------------------------------------------------------------
# ToolRegistry - keep loaded tools in one place
# ---------------------------------------------------------------------------


class ToolRegistry:  # pylint: disable=too-few-public-methods
    """Executor が利用するツールを登録・取得する窓口クラス。"""

    def __init__(self) -> None:
        self._client: MultiServerMCPClient | None = None
        self._tools: list[BaseTool] | None = None

    # ------------------------------------------------------------------
    # Initialisers
    # ------------------------------------------------------------------
    async def init_via_http(self, url: str) -> None:
        """HTTP 経由で Playwright MCP に接続しツールをロードする。"""

        self._client = await create_playwright_client_http(url)
        self._tools = await self._client.get_tools()

    async def init_via_stdio(self, *, headless: bool = True) -> None:
        """Stdio 経由で Playwright MCP サーバーを起動しツールをロードする。"""

        self._client = await create_playwright_client_stdio(headless=headless)
        self._tools = await self._client.get_tools()

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    @property
    def client(self) -> MultiServerMCPClient:
        """初期化済みの ``MultiServerMCPClient`` を返す。"""

        if self._client is None:
            raise RuntimeError("ToolRegistry is not initialised - call ``init_via_http`` or ``init_via_stdio`` first.")
        return self._client

    @property
    def tools(self) -> list[BaseTool]:
        """ロード済みの LangChain ``Tool`` オブジェクト一覧。"""

        if self._tools is None:
            raise RuntimeError("Tools have not been loaded yet - call an init method first.")
        return self._tools

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def is_initialised(self) -> bool:
        """クライアントとツールがロード済みかを判定する。"""

        return self._client is not None and self._tools is not None

    pass  # pragma: no cover
