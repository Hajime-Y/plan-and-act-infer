# 05 uv を用いた環境構築手順

**uv ≥ 0.2.0** を前提にしています。

```bash
# 1. uv をインストール（未導入の場合）
pip install uv

# 2. リポジトリをクローン
git clone git@github.com:yourorg/plan_and_act_infer.git
cd plan_and_act_infer

# 3. 依存追加・更新
uv add -d "langgraph>=0.0.36" "langchain>=0.2.1" "langchain-mcp-adapters>=0.1.3" \
       typer>=0.12 python-dotenv rich pytest ruff

# 4. ロックファイルのアップデート
uv sync
```

> ❗ 禁止事項: `uv pip` サブコマンドは使用しないでください。
> `uv add` → `uv sync` が推奨フローです。

## コマンド早見表

| 操作             | コマンド             |
| -------------- | ---------------- |
| 依存追加           | `uv add PACKAGE` |
| lock に従いインストール | `uv sync`        |
| 依存バージョン一括更新    | `uv sync -u`     |
| 仮想環境アクティベート    | `uv venv` (任意)   |
