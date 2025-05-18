# Plan-and-Act Infer

Plan-and-Act 推論エージェントのリファレンス実装です。

---

## 📦 Getting Started（ローカル開発環境のセットアップ）

以下の手順では **[uv](https://github.com/astral-sh/uv) ≥ 0.2.0** を使用して Python 仮想環境を構築し、依存関係を固定・インストールします。

```bash
# 0. (未導入の場合) uv をインストール
pip install --upgrade uv

# 1. リポジトリを clone
git clone git@github.com:Hajime-Y/plan-and-act-infer.git
cd plan-and-act-infer

# 2. 仮想環境を作成し有効化
uv venv           # .venv/ を作成
source .venv/bin/activate

# 3. 依存関係をロックファイルに従ってインストール
uv sync           # pyproject.toml と uv.lock からインストール

# 4. (依存追加が必要な場合) パッケージを追加してロック更新
uv add <package>  # 例: uv add "langgraph>=0.0.36"
uv sync           # lock を更新

# 5. テストの実行
pytest -q
```

> 🚫 **禁止事項**: `uv pip install ...` は使用しないでください。常に `uv add` → `uv sync` のフローで依存を管理します。

---

## 🗂️ プロジェクト構成

```
plan-and-act-infer/
├── src/
│   └── plan_and_act/
│       ├── core/                # Planner / Executor / Memory / Tools (雛形)
│       │   ├── agent_base.py
│       │   ├── memory.py
│       │   └── tools.py
│       ├── graphs/              # LangGraph 推論フロー（雛形）
│       │   └── inference_graph.py
│       ├── mcp/                 # MCP クライアント関連（雛形）
│       ├── cli/                 # Typer CLI（雛形）
│       │   └── run.py
│       └── utils/               # 共通ユーティリティ（未実装）
├── configs/
│   └── settings.yaml            # アプリケーション設定
├── tests/                       # pytest テスト
│   ├── conftest.py
│   └── test_dummy.py
├── .env.example                 # 環境変数のサンプル
└── ...
```

---

## 🤝 Contributing

開発フローやコーディング規約については `.cursor/rules/` 以下の各ガイドおよび GitHub Issues を参照してください。

---

## License

MIT License  © 2025 Hajime Yagi 