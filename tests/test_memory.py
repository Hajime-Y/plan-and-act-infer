"""Memory クラスのユニットテスト。"""

from plan_and_act.core.memory import Memory, PlanStep


def test_memory_add_and_get_history() -> None:
    """履歴の追加と取得が正しく動作することを検証。"""

    memory = Memory()

    step: PlanStep = {"step_number": 1, "reasoning": "test", "step": "dummy"}
    observation = "ok"

    memory.add_history(step, observation)

    history = memory.get_history()

    assert len(history) == 1
    assert history[0]["step"] == step
    assert history[0]["observation"] == observation
    assert memory.last_observation() == observation
