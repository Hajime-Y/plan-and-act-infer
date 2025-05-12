from typing import Any, List, Optional, Tuple, TypedDict


class PlanAndActState(TypedDict, total=False):
    """
    Plan-and-Act エージェントの実行状態を管理する TypedDict。

    Attributes:
        goal: ユーザーからの初期タスク指示 (変更されない想定)。
        plan: Planner によって生成された計画ステップのリスト。
        current_step_index: 現在実行中の計画ステップのインデックス。
        observation: Executor が直近のステップで得た観測結果 (MCPツールの戻り値など)。
        feedback: Executor の観測結果を Planner が解釈しやすい形に整形したもの (成功/失敗/抽出情報など)。
        history: (実行ステップ, 観測/フィードバック) の履歴タプルリスト。
        needs_replan: Planner による再計画が必要かを示すフラグ。
        is_finished: タスクが完了したかを示すフラグ。
        error: エラー発生時にエラーメッセージを保持。
    """

    goal: str
    plan: List[str]
    current_step_index: int
    observation: Any
    feedback: str
    history: List[Tuple[str, str]]
    needs_replan: bool
    is_finished: bool
    error: Optional[str] 