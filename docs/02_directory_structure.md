# 02 ディレクトリ／ファイル構成

このドキュメントは、`plan-and-act-infer` プロジェクトのディレクトリ構造と、主要なファイルおよびディレクトリの役割について説明します。シンプルさと迅速な開発を念頭に置いた構成となっています。

```
plan_and_act_infer/
├── README.md             # プロジェクト概要、セットアップ、簡単な使い方
├── pyproject.toml        # PEP 621 準拠のプロジェクトメタデータ (uv が利用)
├── uv.lock               # uv が生成するロックファイル (依存関係の固定)
├── .env.example          # 環境変数の雛形 (APIキー等を記述)
├── configs/
│   └── settings.yaml     # アプリケーション設定 (モデル名、温度、MCPエンドポイント、LangGraph設定等)
├── src/
│   └── plan_and_act/
│       ├── __init__.py     # plan_and_act パッケージの初期化
│       ├── core/
│       │   ├── __init__.py
│       │   ├── agent_base.py # Planner, Executor の基底クラスや共通インターフェース定義
│       │   ├── planner.py    # Planner: 思考プロセス、動的再計画ロジックの実装
│       │   ├── executor.py   # Executor: MCP Tools (Playwright等) を利用したアクション実行
│       │   ├── memory.py     # 状態・履歴管理 (対話履歴、行動履歴、観測結果等)
│       │   └── tools.py      # MCP Client のラッパー、Executorが利用するツール群の窓口
│       ├── graphs/
│       │   ├── __init__.py
│       │   └── inference_graph.py # LangGraph を用いた推論フロー (State, Node, Edge) の定義と実行ヘルパー
│       ├── mcp/
│       │   ├── __init__.py
│       │   └── client.py     # langchain-mcp-adapters を利用したMCP Serverへのクライアント実装
│       ├── cli/
│       │   ├── __init__.py
│       │   └── run.py        # Typer を用いたコマンドラインインターフェース (タスク実行等)
│       └── utils/
│           ├── __init__.py
│           └── logging.py    # Rich ライブラリ等を用いたロギングユーティリティ (可読性の高いログ出力)
├── scripts/
│   └── quickstart.sh       # 開発環境のセットアップや簡単な動作確認を自動化するスクリプト
├── tests/                  # Pytest を用いたテストコード
│   ├── core/               # core モジュールに対応するテスト
│   ├── graphs/             # graphs モジュールに対応するテスト
│   └── conftest.py         # Pytest の共通フィクスチャ等
└── docs/
    └── *.md                # 本プロジェクトの開発者向けドキュメント群
```

### namespace 説明

| ディレクトリ      | 役割                                                                                                | 注意点・方針                                                                                                                               |
| ----------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `src/plan_and_act/core/` | エージェントの中核ロジック（Planner, Executor, Memory, Tools）を配置。                              | - `agent_base.py` で Planner/Executor の共通インターフェースを定義し、実装の統一性を図る。<br>- 各コンポーネントは単一責任の原則を意識し、疎結合に設計する。                         |
| `src/plan_and_act/graphs/` | `LangGraph` を用いた推論フロー（DAG）を定義。状態管理(State)、ノード(Node)、エッジ(Edge)の具体的な実装。 | - 基本的に1ファイル1グラフ（例: `inference_graph.py`）。<br>- 状態の遷移、条件分岐（特に動的再計画のトリガー）、ループ処理などをここに集約する。                               |
| `src/plan_and_act/mcp/`  | `langchain-mcp-adapters` を利用したMCPクライアント関連のモジュール。設定読み込みやクライアント初期化処理。  | - **API呼び出しは原則非同期（async）**で実装し、ブロッキングを避ける。<br>- `configs/settings.yaml` からエンドポイント情報を読み込む。                                       |
| `src/plan_and_act/cli/`  | `Typer` を用いたコマンドラインインターフェース。タスクの入力受付、設定ファイルの読み込み、推論実行の起点。 | - `.env` ファイルから環境変数を読み込み、APIキー等を設定に反映させる。<br>- 複数のサブコマンド（例: `run task`, `show config`）を定義可能。                                  |
| `src/plan_and_act/utils/`| プロジェクト全体で利用する共通ユーティリティ（ロギング等）。                                                 | - `logging.py` では、ログレベル、フォーマット、出力先（コンソール、ファイル）を設定可能にする。<br>- Rich等を用いて開発中のデバッグや実行状況の確認を容易にする。                     |
| `configs/`        | アプリケーション全体の設定ファイルを配置。                                                                    | - `settings.yaml` には、LLMのモデル名、APIキーの環境変数名、各種タイムアウト値、MCPツールのエンドポイント、LangGraphのコンフィグ等を記述。センシティブな値は直接書かない。 |
| `scripts/`        | 開発支援用のシェルスクリプト等を配置。                                                                      | - `quickstart.sh` は、依存関係のインストール、必要な環境変数の設定（`.env`のコピー等）、簡単なテスト実行やサンプルタスクの実行までをカバーすることを目指す。        |
| `tests/`          | `pytest` を用いた単体テストおよび結合テスト。モックライブラリを適宜使用。                                    | - CIでの自動実行を前提とし、カバレッジ向上を目指す。<br>- `core` や `graphs` のロジックを中心にテストを作成。<br>- MCP Client のテストでは、HTTPリクエストをモックする。             |

この構成は、プロジェクトの成長に合わせて柔軟に変更可能です。重要なのは、チームメンバー全員が構造を理解し、一貫性を持って開発を進めることです。

