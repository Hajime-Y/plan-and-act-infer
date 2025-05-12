# 06 開発ワークフロー

このドキュメントは、`plan-and-act-infer` プロジェクトにおける開発の進め方、コーディング規約、テスト、リリースなどのワークフローについて説明します。

## 6.1. 基本的な開発フロー

1.  **Issue の確認**: GitHub Issues で担当するタスク（バグ修正、機能追加など）を確認します。
2.  **ブランチの作成**: `main` ブランチから、命名規則に従ったフィーチャーブランチを作成します。
    -   命名規則: `feat/<issue-number>-short-description` (機能追加) または `fix/<issue-number>-short-description` (バグ修正) など。
    -   例: `feat/12-implement-planner-node`
3.  **実装とテスト**: コードを実装し、対応する単体テストや結合テストを作成・実行します。
    -   ローカルでのテスト: `pytest`
    -   コードフォーマット: `ruff format .`
    -   静的解析: `ruff check .`
4.  **コミット**: 変更内容をコミットします。コミットメッセージは分かりやすく記述します (例: `feat: Implement planner node (#12)`)
5.  **Push**: フィーチャーブランチをリモートリポジトリに Push します。
6.  **Pull Request (PR) の作成**: GitHub 上で `main` ブランチに対する Pull Request を作成します。
    -   PR の説明には、Issue 番号、変更内容の概要、テスト内容などを記述します。
    -   レビュアーを指定します。
7.  **CI の確認**: GitHub Actions による自動チェック (フォーマット、静的解析、テスト) がすべて成功することを確認します。
8.  **レビューと修正**: レビュアーからのフィードバックに基づき、コードを修正します。
9.  **マージ**: CI が成功し、レビューで承認されたら、PR を `main` ブランチにマージします。
10. **ブランチの削除**: マージ後、不要になったフィーチャーブランチを削除します。

## 6.2. ローカル開発環境

1.  **リポジトリのクローン**:
    ```bash
    git clone <repository-url>
    cd plan-and-act-infer
    ```
2.  **環境構築**:
    `uv` を使用して仮想環境を作成し、依存関係をインストールします。(詳細は `05_setup_with_uv.md` を参照)
    ```bash
    uv venv # 仮想環境を作成 (.venv)
    uv sync # pyproject.toml と uv.lock に基づき依存関係をインストール
    source .venv/bin/activate # 仮想環境を有効化
    ```
3.  **環境変数の設定**:
    `.env.example` をコピーして `.env` ファイルを作成し、必要な API キー (例: `OPENAI_API_KEY`) や設定値を記述します。
    ```bash
    cp .env.example .env
    # .env ファイルを編集
    ```
    `.env` ファイルは Git 管理対象外です。

## 6.3. コーディング規約と静的解析

-   **フォーマッタ**: `Ruff Formatter` を使用します。
    -   実行: `ruff format .`
-   **リンター**: `Ruff` を使用します。
    -   実行: `ruff check .`
-   **型チェック**: 基本的に型ヒントを付与し、可読性と保守性を高めます。(CIでの静的な型チェックは現状未導入)
-   **推奨**: `pre-commit` フックを設定し、コミット前に自動でフォーマットとチェックを実行することを推奨します。
    ```bash
    # pre-commit のインストール (初回のみ)
    pip install pre-commit
    # フックの設定
    pre-commit install
    ```

## 6.4. CI (GitHub Actions)

Pull Request が作成されると、`.github/workflows/ci.yaml` に定義された以下のチェックが自動的に実行されます。

1.  **依存関係の同期 (`uv sync`)**: `pyproject.toml` と `uv.lock` に基づいて依存関係が正しくインストールできるかを確認します。
2.  **コードフォーマットチェック (`ruff format --check .`)**: コードが Ruff Formatter の規約に従っているかを確認します。
3.  **静的解析 (`ruff check .`)**: Lint ルールに違反していないか、潜在的な問題をチェックします。
4.  **単体・結合テスト (`pytest -q`)**: `tests/` ディレクトリ以下のテストがすべて成功するかを確認します。

これらのチェックがすべて成功しないと、Pull Request はマージできません。

## 6.5. テスト戦略

-   **単体テスト (Unit Tests)**:
    -   **対象**: 個々の関数、クラスメソッド、LangGraph ノードなど、比較的小さな単位。
    -   **方針**: 依存関係をモック化し、特定の入力に対する出力や状態変化が期待通りかを確認します。
    -   **LangGraph ノード**: ノード関数を直接呼び出し、入力となる State の一部やツール実行結果をモックデータとして与え、出力 State の変化や特定の関数の呼び出しを確認します。
    -   **MCP クライアント呼び出し部分**: `pytest-httpx` や `unittest.mock` を使用して、`MultiServerMCPClient` のメソッド呼び出しや HTTP リクエスト/レスポンスをモックします。
-   **結合テスト (Integration Tests)**:
    -   **対象**: 複数のコンポーネントが連携する部分 (例: Planner と Executor の連携、LangGraph の主要なフロー)。
    -   **方針**: 可能な限り実際のコンポーネントを使用しますが、外部 API (LLM, Playwright MCP) などはモック化することが多いです。主要なシナリオが期待通りに動作するかを確認します。
    -   **LangGraph**: 特定の入力 (ゴール) を与え、グラフ全体の実行結果 (最終的な State や特定のノードを経由したかなど) を検証します。
-   **E2E (End-to-End) テスト**:
    -   **対象**: CLI インターフェースなど、ユーザーが直接触れるインターフェース。
    -   **方針**: 実際の CLI コマンドを実行し (`subprocess.run`)、標準出力や終了コード、(もしあれば) 生成されるファイルなどが期待通りかを確認します。Playwright MCP Server も実際に起動した状態で行うことが理想ですが、CI 環境での実行は難しい場合があります。
    -   テスト用 Playwright MCP Server: 簡単なモックサーバーや、実際の Playwright MCP Server をテスト実行時に一時的に起動・停止する仕組みを検討します。

## 6.6. デバッグのヒント

-   **LangGraph**: LangSmith などのトレースツールを利用すると、グラフの実行フロー、各ノードの入出力、ツールの呼び出し状況などを可視化でき、デバッグが容易になります。(LangSmith のセットアップは任意)
-   **Playwright MCP**: Playwright MCP Server をヘッドフルモード (`--headless` なし) で起動し、実際のブラウザ操作を目で確認します。また、`browser_snapshot` の結果を詳細に確認することで、要素の ref や構造を把握できます。
-   **ロギング**: `src/plan_and_act/utils/logging.py` を活用し、要所でログを出力します。特に State の変化やツールの入出力を記録すると役立ちます。
-   **デバッガ**: `pdb` や VSCode のデバッガを使用し、ブレークポイントを設定してステップ実行します。

## 6.7. リリース手順 (任意)

PyPI へのリリースは現時点では必須ではありませんが、行う場合は以下の手順を想定します。

1.  **バージョン更新**: `pyproject.toml` のバージョン番号を更新します (例: `0.1.0` -> `0.2.0`)。
    -   `bump2version` などのツール利用を推奨。
2.  **変更履歴の更新**: `CHANGELOG.md` (未作成の場合は作成) に今回のリリースでの変更点を記述します。
3.  **Git タグの作成**: 更新したバージョンで Git タグを作成します。
    ```bash
    git tag -a v0.2.0 -m "Release version 0.2.0"
    git push origin v0.2.0
    ```
4.  **PyPI への公開**: GitHub Actions などで、タグがプッシュされたことをトリガーにして PyPI へ自動公開するワークフローを設定します。
    -   事前に PyPI のアカウントと API トークンの設定が必要です。

## 6.8. よくある落とし穴と対処法

| 事象                                           | 考えられる原因                                 | 対処法                                                                                                |
| ---------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: plan_and_act` など        | 仮想環境が有効でない / `uv sync` 未実行         | `.venv/bin/activate` を実行後、`uv sync` を実行                                                           |
| MCP ツール実行時にエラーまたはタイムアウト             | MCP Server 未起動 / URL・ポート間違い / timeout 値不足 | Playwright MCP Server が起動しているか確認。`configs/settings.yaml` のURL、ポート、timeout値を確認・調整 | 
| (Stdio接続時) MCP Server が起動しない           | `npx` や Node.js が PATH にない / コマンド引数間違い | Node.js 環境を確認。`MultiServerMCPClient` の `command`, `args` 設定を確認                               |
| Planner が期待通りに動作しない (空応答、ループなど) | プロンプトの不備 / LLM設定 (temperature等) / 記憶の不備 | プロンプトテンプレート、`configs/settings.yaml` の LLM 設定、LangGraph の State (特に history) を確認           |
| Playwright が要素を見つけられない                | Web ページの構造変化 / セレクタや ref の間違い    | `browser_snapshot` で最新のページ構造を確認し、ref や要素指定方法を修正。必要なら Planner の再計画能力を改善 |
| 環境変数 (`.env`) が読み込まれない             | `python-dotenv` 未インストール / 読み込みコード欠如 | `uv sync` を確認。アプリ起動時に `load_dotenv()` が呼ばれているか確認                                    |
| テストがローカルで成功するが CI で失敗する       | 環境差異 (OS, Python バージョン, 依存関係) / テストの副作用 | CI 環境のログを確認。`uv.lock` で依存関係を固定。テストが他のテストに影響を与えていないか確認              |

## 6.9. 相互参照

-   **02_directory_structure.md**: ディレクトリとファイルの構成詳細
-   **03_agent_architecture.md**: エージェント (Planner / Executor) のアーキテクチャ仕様
-   **04_tool_integration_mcp.md**: Playwright MCP との接続・利用方法詳細
-   **05_setup_with_uv.md**: `uv` を用いた開発環境セットアップ手順