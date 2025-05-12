# 04 MCP ツール統合

このドキュントは、`plan-and-act-infer` プロジェクトにおける Model Context Protocol (MCP) を介したツール統合、特に Playwright MCP との連携について説明します。

## 4.1. 概要

本プロジェクトの Executor (エグゼキューター) は、エージェントがブラウザ操作などの高度なタスクを実行できるようにするため、MCP を介して外部ツールと連携します。
主要な技術スタックとして、ローカルで動作する **Playwright MCP Server** と、LangGraph との連携を担う **`langchain-mcp-adapters`** ライブラリを利用します。

## 4.2. アーキテクチャ

```mermaid
graph TD
    subgraph Executor (LangGraph Agent - MCP Client)
        A[LangGraph Core]
        B[Tool Invocation Logic]
        C[langchain-mcp-adapters:MultiServerMCPClient]
    end

    subgraph Playwright MCP Server (Local Process or SubProcess)
        D[microsoft/playwright-mcp]
        E[Browser Instance]
    end

    A --> B;
    B --> C;
    C -- MCP over SSE/Stdio --> D;
    D -- Controls --> E;
    E -- Observes --> D;
    D -- Tool Results --> C;
```

-   **Executor (MCP Client)**:
    -   `src/plan_and_act/core/executor.py` で実装されます。
    -   LangGraph の一部として動作し、計画されたステップを実行するために MCP ツールを呼び出します。
    -   `langchain-mcp-adapters` の `MultiServerMCPClient` を使用して、Playwright MCP Server に接続し、ツールを利用可能な LangChain `Tool` オブジェクトとして取得します。
-   **Playwright MCP Server (MCP Server)**:
    -   `microsoft/playwright-mcp` を使用します。起動方法には主に以下の2つの選択肢があります。
        1.  ローカルマシン上で別途プロセスとして起動し、SSE (Server-Sent Events) で Executor と通信する。
        2.  Executor の Python プロセスからサブプロセスとして起動され、Stdio (標準入出力) で通信する。
    -   ブラウザ操作のための各種ツール（ページのナビゲーション、要素のクリック、スナップショット取得など）を MCP 経由で提供します。
-   **`langchain-mcp-adapters`**:
    -   Executor と Playwright MCP Server 間の通信を仲介します。
    -   MCP サーバーのツール定義を LangChain/LangGraph が利用しやすい形式に変換します。
    -   `MultiServerMCPClient` は、単一または複数の MCP サーバーへの接続を管理できるため、将来的に他の MCP ツールサーバーを追加する際にも柔軟に対応できます。

## 4.3. Playwright MCP との連携・実装フロー

### 4.3.1. Playwright MCP Server の準備と Executor との接続

Executor が Playwright の機能を利用できるように、Playwright MCP Server を準備し、Executor から接続します。

#### 4.3.1.1. 方法1: サーバーを別途起動し SSE で接続

この方法では、Playwright MCP Server を手動または別のスクリプトで起動し、Executor はそのサーバーの SSE エンドポイントに接続します。
デバッグやサーバープロセスを独立して管理したい場合に適しています。

-   **Playwright MCP Server のインストール (初回のみ)**:
    ```bash
    npm install -g @playwright/mcp
    ```
-   **サーバー起動 (ターミナルで実行)**:
    ポート番号 `8931` (任意) で Server-Sent Events (SSE) トランスポートを有効にして起動する例です。
    ```bash
    playwright-mcp --port 8931
    # または npx @playwright/mcp@latest --port 8931
    ```
    -   `--headless` オプションでヘッドレスモードでブラウザを起動できます。
    -   詳細は `playwright-mcp --help` で確認できます。

-   **Executor (MCP Client) の設定 (SSE接続)**:
    `configs/settings.yaml` や環境変数でサーバーURLを管理します。
    ```python
    # (例) src/plan_and_act/utils/mcp_tools.py などに実装想定
    from langchain_mcp_adapters.client import MultiServerMCPClient
    # ... (他のimport)

    # 設定ファイルや環境変数から取得
    PLAYWRIGHT_MCP_SSE_URL = "http://localhost:8931/sse"

    async def load_tools_via_sse() -> List[BaseTool]:
        client_config = {
            "playwright_sse": {  # 任意のサーバー名
                "url": PLAYWRIGHT_MCP_SSE_URL,
                "transport": "sse"
            }
        }
        async with MultiServerMCPClient(client_config) as mcp_client:
            tools = mcp_client.get_tools(server_name="playwright_sse")
        return tools
    ```

#### 4.3.1.2. 方法2: サブプロセスとして Stdio で起動・接続

この方法では、Executor (Pythonプロセス) が `langchain-mcp-adapters` を介して Playwright MCP Server をサブプロセスとして起動し、Stdio (標準入出力) で通信します。
サーバープロセスを Python コード内で完結させたい場合に便利です。

-   **前提条件**:
    -   `npx` コマンドが実行環境のPATHに設定されていること。
    -   Node.js がインストールされていること。
    -   `@playwright/mcp` がグローバルまたはプロジェクトの `node_modules` にインストールされていること (通常は`npx`が自動処理)。

-   **Executor (MCP Client) の設定 (Stdio接続)**:
    `MultiServerMCPClient` の設定で `transport: "stdio"` とし、`command` と `args` を指定します。
    ```python
    # (例) src/plan_and_act/utils/mcp_tools.py などに実装想定
    from langchain_mcp_adapters.client import MultiServerMCPClient
    # ... (他のimport)

    async def load_tools_via_stdio() -> List[BaseTool]:
        client_config = {
            "playwright_stdio": {  # 任意のサーバー名
                "command": "npx",
                "args": ["@playwright/mcp@latest", "--headless"], # 必要に応じて引数を調整
                "transport": "stdio",
                # "cwd": "/path/to/working_directory", # 必要に応じて作業ディレクトリを指定
            }
        }
        async with MultiServerMCPClient(client_config) as mcp_client:
            tools = mcp_client.get_tools(server_name="playwright_stdio")
        return tools
    ```
    -   `args` には Playwright MCP のコマンドラインオプション (例: `--browser firefox`) を追加できます。
    -   `StdioServerParameters` を直接利用するより、`MultiServerMCPClient` のこの形式が推奨されます。

### 4.3.2. ツールのロードと利用 (共通)

上記いずれかの方法で `MultiServerMCPClient` を設定した後、ツールは同様にロード・利用できます。

```python
# (続き) ...
# Executorは上記いずれかの関数で取得したツールリストをLangGraphエージェントに渡して使用する
# playwright_tools = await load_tools_via_sse() # または await load_tools_via_stdio()
# agent = create_agent(model, playwright_tools)
```

### 4.3.3. Playwright MCP の主なツール (共通)

ロードされた Playwright MCP ツールは、LangGraph エージェント内で他の LangChain ツールと同様に呼び出すことができます。
-   Playwright MCP が提供する主なツール例 (詳細は `microsoft/playwright-mcp` のドキュメント参照):
    -   `browser_navigate`: 指定されたURLに遷移
    -   `browser_snapshot`: 現在のページのアクセシビリティスナップショットを取得
    -   `browser_click`: スナップショット内の参照(ref)に基づいて要素をクリック
    -   `browser_type`: スナップショット内の参照(ref)に基づいて要素にテキストを入力
    -   `browser_scroll_page`: ページをスクロール
    -   など多数。

## 4.4. 開発・運用上の考慮事項

-   **サーバープロセスの管理**:
    -   **SSE接続の場合**: Playwright MCP Server の起動・停止は、Executor の Python プロセスとは独立して管理が必要です。
    -   **Stdio接続の場合**: サーバープロセスは Python プロセスの子プロセスとして管理されますが、リソースリークやゾンビプロセスが発生しないよう注意が必要です。
-   **ログとデバッグ**:
    -   **Stdio接続の場合**: サブプロセスである Playwright MCP Server のログは Python 側からは直接見えにくいことがあります。問題発生時は、一時的に方法1（SSE接続）に切り替えてサーバー単体でログを確認する方がデバッグしやすい場合があります。
-   **環境依存性**:
    -   **Stdio接続で `npx` を使う場合**: `npx` コマンドと Node.js が実行環境に正しくインストールされ、PATHが通っている必要があります。
-   **エラーハンドリング**: ネットワークの問題 (SSE時) やブラウザ操作中の予期せぬエラー（要素が見つからない、ページがロードできない等）に対する堅牢なエラーハンドリングを Executor 側に実装する必要があります。`ToolException` の適切な利用などが考えられます。
-   **設定の外部化**: MCP サーバーの URL (SSE時)、ポート番号、コマンド引数 (Stdio時)、タイムアウト設定などは、`configs/settings.yaml` や環境変数を通じて外部から設定できるようにし、コードへのハードコーディングを避けます。
-   **非同期処理**: `langchain-mcp-adapters` のクライアント操作やツール実行は非同期 (`async/await`) で行われるため、Executor や LangGraph のフローも非同期に対応している必要があります。
-   **Playwright の知識**: Playwright MCP のツールを効果的に利用するためには、Playwright 自体の基本的な動作（セレクタ、ページ操作、スナップショットの概念など）の理解が役立ちます。
