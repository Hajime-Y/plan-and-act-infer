"""State management utilities shared across Planner and Executor.

本モジュールでは、LangGraph の State オブジェクトと互換性のある ``TypedDict`` を用いて
状態を表現し、簡易なインメモリストア ``Memory`` を提供する。後続のノード実装では
``Memory`` を介して状態を読み書きする想定である。
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, TypedDict

# ---------------------------------------------------------------------------
# TypedDict definitions (see rule *03-agent-architecture* §3.5.)
# ---------------------------------------------------------------------------


class PlanStep(TypedDict, total=False):
    """単一の計画ステップを表す構造体。"""

    step_number: int  # ステップ番号
    reasoning: str  # そのステップを提案する理由
    step: str  # 実行すべき高レベルタスク


class State(TypedDict, total=False):
    """Planner / Executor 間で共有される状態オブジェクト。"""

    goal: str  # ユーザ要求 (immutable)
    plan: list[PlanStep]  # Planner が生成するステップリスト
    current_step_idx: int  # 現在実行中のステップインデックス
    observation: str  # Executor の返り値 (最新)
    history: list[dict[str, Any]]  # 過去の (step, observation) ログ
    needs_replan: bool  # Planner に戻るべきか
    finished: bool  # すべてのステップが完了


# ---------------------------------------------------------------------------
# Memory implementation
# ---------------------------------------------------------------------------


class Memory:  # pylint: disable=too-few-public-methods
    """エージェント状態・履歴を保持する簡易インメモリストア。"""

    __slots__ = ("_state",)

    def __init__(self, initial_state: State | None | None = None) -> None:
        """インメモリの ``State`` を初期化する。

        Parameters
        ----------
        initial_state : State | None, optional
            初期状態。None の場合は空の状態を生成する。
        """

        # deepcopy して外部のミュータビリティと分離する
        self._state: State = deepcopy(initial_state) if initial_state else {}

        # history キーを常に持たせることで型安全性を担保
        self._state.setdefault("history", [])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def state(self) -> State:
        """現在の ``State`` を返す (可変オブジェクトなので注意)。"""

        return self._state

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """内部状態を空にリセットする。``history`` キーは空リストで保持。"""

        self._state.clear()
        self._state["history"] = []  # type: ignore[index]

    # ------------------------------------------------------------------
    # History helpers
    # ------------------------------------------------------------------
    def add_history(self, step: dict[str, Any], observation: str) -> None:
        """履歴に (step, observation) エントリを追加する。"""

        entry = {
            "step": step,
            "observation": observation,
        }
        self.append_history(entry)

    def append_history(self, entry: dict[str, Any]) -> None:
        """任意の履歴エントリを直接追加する。"""

        self._state.setdefault("history", []).append(entry)  # type: ignore[arg-type]

    def get_history(self) -> list[dict[str, Any]]:
        """履歴全体を取得する (参照渡し)。"""

        return self._state.get("history", [])  # type: ignore[return-value]

    def last_observation(self) -> str | None:
        """直近の ``observation`` を返す。履歴が空の場合は ``None``。"""

        if not self._state.get("history"):
            return None

        return self._state["history"][-1].get("observation")  # type: ignore[index]

# モジュール外部に公開する名前
__all__ = [
    "Memory",
    "PlanStep",
    "State",
]
