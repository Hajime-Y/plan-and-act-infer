"""ToolRegistry 初期化ユーティリティのテスト。"""



from plan_and_act.core import tools as tools_module


class _DummyMCPClient:  # pylint: disable=too-few-public-methods
    """`MultiServerMCPClient` をモックするダミークラス。"""

    def __init__(self) -> None:
        self.add_server_called = False
        self.add_stdio_server_called = False

    async def add_server(self, *args, **kwargs):
        self.add_server_called = True

    async def add_stdio_server(self, *args, **kwargs):
        self.add_stdio_server_called = True

    async def get_tools(self) -> list[str]:
        return ["t1", "t2"]


def test_tool_registry_init_via_http(monkeypatch):
    """HTTP 初期化が正常に動作し、tools が取得できることを確認。"""

    import asyncio

    # `MultiServerMCPClient` をダミーに差し替え
    monkeypatch.setattr(tools_module, "MultiServerMCPClient", _DummyMCPClient)

    async def _run() -> None:
        registry = tools_module.ToolRegistry()
        await registry.init_via_http("http://dummy")

        assert registry.is_initialised()
        assert registry.tools == ["t1", "t2"]

    asyncio.run(_run())


def test_tool_registry_init_via_stdio(monkeypatch):
    """Stdio 初期化が正常に動作することを確認。"""

    import asyncio

    monkeypatch.setattr(tools_module, "MultiServerMCPClient", _DummyMCPClient)

    async def _run() -> None:
        registry = tools_module.ToolRegistry()
        await registry.init_via_stdio()

        assert registry.is_initialised()
        assert registry.tools == ["t1", "t2"]

    asyncio.run(_run())
