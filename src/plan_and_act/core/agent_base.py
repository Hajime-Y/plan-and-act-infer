"""Abstract base class definitions for Planner and Executor agents."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AgentBase(ABC):
    """Planner / Executor の共通インターフェース (雛形)。"""

    @abstractmethod
    def run(self, *args, **kwargs):  # noqa: D401,E501, ANN001, D401 - 詳細実装は後続タスクで追加
        """Agent 実行メソッド (実装は後続タスクで追加)。"""

        pass  # pragma: no cover 