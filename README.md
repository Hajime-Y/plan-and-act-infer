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
│       │   ├── planner.py       # ✅ Planner実装
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
│   ├── test_dummy.py
│   ├── test_memory.py
│   ├── test_tools.py
│   └── test_planner.py          # ✅ Plannerテスト
├── .env.example                 # 環境変数のサンプル
└── ...
```

---

## 🏗️ Plan-and-Act アーキテクチャ

### Planner コンポーネント

Planner は、高レベルのタスクを実行可能なステップに分解し、実行結果に基づいて動的に計画を調整する責務を持ちます。

#### 主要機能

1. **初期計画生成**
   - ユーザーの目標を理解し、実行可能なステップのリストを生成
   - 各ステップには、番号、理由付け（reasoning）、具体的なアクションを含む

2. **動的再計画**
   - エグゼキューターからのフィードバックに基づいて計画を評価
   - エラーや予期しない結果に対して代替案を生成
   - 既に成功したステップは保持しつつ、失敗したステップを修正

3. **再計画判定**
   - 観測結果からエラーキーワードを検出し、再計画の必要性を判断
   - エラー、失敗、タイムアウトなどの問題を自動検出

#### データモデル

```python
class PlanStep:
    step_number: int      # ステップ番号
    reasoning: str        # そのステップが必要な理由
    step: str            # 実行すべき高レベルタスク

class Plan:
    steps: List[PlanStep]  # 計画ステップのリスト
```

#### LangGraph統合

Planner は LangGraph のノードとして動作し、以下の状態を管理します：

- **入力**: `goal`（目標）、`history`（実行履歴）、`observation`（最新の観測）
- **出力**: `plan`（計画ステップのリスト）、`needs_replan`（再計画フラグ）

---

## 🤝 Contributing

開発フローやコーディング規約については `.cursor/rules/` 以下の各ガイドおよび GitHub Issues を参照してください。

---

## License

MIT License  © 2025 Hajime Yagi 