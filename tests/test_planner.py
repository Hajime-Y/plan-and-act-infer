"""
Planner コンポーネントのユニットテスト
"""

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, BaseMessage

from plan_and_act.core.planner import (
    Plan,
    PlanStep,
    Planner,
    create_planner,
    planner_node,
)


class TestPlanStep:
    """PlanStepクラスのテスト"""
    
    def test_plan_step_creation(self):
        """PlanStepが正しく作成できることを確認"""
        step = PlanStep(
            step_number=1,
            reasoning="最初にウェブサイトにアクセスする必要がある",
            step="指定されたURLにナビゲートする"
        )
        
        assert step.step_number == 1
        assert step.reasoning == "最初にウェブサイトにアクセスする必要がある"
        assert step.step == "指定されたURLにナビゲートする"
    
    def test_plan_step_to_dict(self):
        """PlanStepが正しく辞書に変換できることを確認"""
        step = PlanStep(
            step_number=2,
            reasoning="検索を実行するため",
            step="検索ボックスにキーワードを入力"
        )
        
        expected = {
            "step_number": 2,
            "reasoning": "検索を実行するため",
            "step": "検索ボックスにキーワードを入力"
        }
        
        assert step.to_dict() == expected


class TestPlan:
    """Planクラスのテスト"""
    
    def test_plan_creation(self):
        """Planが正しく作成できることを確認"""
        steps = [
            PlanStep(step_number=1, reasoning="理由1", step="ステップ1"),
            PlanStep(step_number=2, reasoning="理由2", step="ステップ2"),
        ]
        
        plan = Plan(steps=steps)
        assert len(plan.steps) == 2
        assert plan.steps[0].step_number == 1
        assert plan.steps[1].step_number == 2
    
    def test_plan_to_dict(self):
        """Planが正しく辞書に変換できることを確認"""
        steps = [
            PlanStep(step_number=1, reasoning="理由1", step="ステップ1"),
        ]
        
        plan = Plan(steps=steps)
        expected = {
            "steps": [
                {
                    "step_number": 1,
                    "reasoning": "理由1",
                    "step": "ステップ1"
                }
            ]
        }
        
        assert plan.to_dict() == expected


class TestPlanner:
    """Plannerクラスのテスト"""
    
    @pytest.fixture
    def mock_llm(self):
        """モックのLLMを作成"""
        return AsyncMock()
    
    @pytest.fixture
    def planner(self, mock_llm):
        """テスト用のPlannerインスタンスを作成"""
        return Planner(llm=mock_llm)
    
    def test_parse_plan_response_with_json_block(self, planner):
        """JSONブロック形式のレスポンスを正しくパースできることを確認"""
        response = """以下が計画です:
        
```json
{
  "steps": [
    {
      "step_number": 1,
      "reasoning": "最初にページにアクセスする必要がある",
      "step": "https://example.comにナビゲート"
    },
    {
      "step_number": 2,
      "reasoning": "検索を実行するため",
      "step": "検索ボックスにキーワードを入力"
    }
  ]
}
```"""
        
        plan = planner._parse_plan_response(response)
        
        assert len(plan.steps) == 2
        assert plan.steps[0].step_number == 1
        assert plan.steps[0].reasoning == "最初にページにアクセスする必要がある"
        assert plan.steps[1].step_number == 2
    
    def test_parse_plan_response_without_json_block(self, planner):
        """JSONブロックなしのレスポンスを正しくパースできることを確認"""
        response = """{
  "steps": [
    {
      "step_number": 1,
      "reasoning": "理由",
      "step": "アクション"
    }
  ]
}"""
        
        plan = planner._parse_plan_response(response)
        
        assert len(plan.steps) == 1
        assert plan.steps[0].step_number == 1
        assert plan.steps[0].step == "アクション"
    
    def test_parse_plan_response_with_invalid_json(self, planner):
        """無効なJSONの場合、空の計画を返すことを確認"""
        response = "これは無効なJSON"
        
        plan = planner._parse_plan_response(response)
        
        assert len(plan.steps) == 0
    
    @pytest.mark.asyncio
    async def test_generate_initial_plan(self, planner, mock_llm):
        """初期計画生成が正しく動作することを確認"""
        # モックの設定
        mock_response = AIMessage(content="""{
  "steps": [
    {
      "step_number": 1,
      "reasoning": "タスクを開始するため",
      "step": "初期アクション"
    }
  ]
}""")
        mock_llm.ainvoke.return_value = mock_response
        
        # 実行
        plan = await planner.generate_initial_plan("テストゴール")
        
        # 検証
        assert len(plan.steps) == 1
        assert plan.steps[0].step == "初期アクション"
        mock_llm.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_replan(self, planner, mock_llm):
        """再計画が正しく動作することを確認"""
        # 現在の計画
        current_plan = Plan(steps=[
            PlanStep(step_number=1, reasoning="理由1", step="ステップ1")
        ])
        
        # 履歴
        history = [
            {"step": "ステップ1", "observation": "エラーが発生しました"}
        ]
        
        # モックの設定
        mock_response = AIMessage(content="""{
  "steps": [
    {
      "step_number": 1,
      "reasoning": "エラーを回避するため代替案を実行",
      "step": "代替ステップ1"
    },
    {
      "step_number": 2,
      "reasoning": "目標達成のため",
      "step": "新しいステップ2"
    }
  ]
}""")
        mock_llm.ainvoke.return_value = mock_response
        
        # 実行
        new_plan = await planner.replan(
            goal="テストゴール",
            current_plan=current_plan,
            history=history,
            observation="エラーが発生しました"
        )
        
        # 検証
        assert len(new_plan.steps) == 2
        assert new_plan.steps[0].step == "代替ステップ1"
        assert new_plan.steps[1].step == "新しいステップ2"
        mock_llm.ainvoke.assert_called_once()
    
    def test_needs_replan_with_error_keywords(self, planner):
        """エラーキーワードが含まれる場合、再計画が必要と判定されることを確認"""
        error_observations = [
            "エラーが発生しました",
            "操作が失敗しました",
            "ページが見つかりません",
            "アクセスできません",
            "An error occurred",
            "Operation failed",
            "Page not found",
            "Cannot access the resource",
            "Exception raised",
            "Request timeout",
            "Unable to complete",
            "Permission denied",
        ]
        
        for observation in error_observations:
            assert planner.needs_replan(observation) is True
    
    def test_needs_replan_without_error_keywords(self, planner):
        """エラーキーワードが含まれない場合、再計画不要と判定されることを確認"""
        success_observations = [
            "正常に完了しました",
            "ページが表示されました",
            "データを取得しました",
            "Successfully completed",
            "Page loaded",
            "Data retrieved",
        ]
        
        for observation in success_observations:
            assert planner.needs_replan(observation) is False


class TestFactoryAndNode:
    """ファクトリ関数とノード関数のテスト"""
    
    def test_create_planner(self):
        """create_planner関数が正しくインスタンスを作成することを確認"""
        mock_llm = MagicMock()
        planner = create_planner(mock_llm)
        
        assert isinstance(planner, Planner)
        assert planner.llm == mock_llm
    
    @pytest.mark.asyncio
    async def test_planner_node_initial_plan(self):
        """planner_nodeが初期計画を生成することを確認"""
        # モックLLMの設定
        mock_llm = AsyncMock()
        mock_response = AIMessage(content="""{
  "steps": [
    {
      "step_number": 1,
      "reasoning": "開始",
      "step": "初期ステップ"
    }
  ]
}""")
        mock_llm.ainvoke.return_value = mock_response
        
        # 初期状態（計画なし）、LLMをstateに含める
        state = {
            "goal": "テストタスク",
            "plan": None,
            "needs_replan": False,
            "llm": mock_llm  # LLMインスタンスを追加
        }
        
        # 実行
        result = await planner_node(state)
        
        # 検証
        assert "plan" in result
        assert len(result["plan"]) == 1
        assert result["plan"][0]["step"] == "初期ステップ"
        assert result["needs_replan"] is False
    
    @pytest.mark.asyncio
    async def test_planner_node_replan(self):
        """planner_nodeが再計画を実行することを確認"""
        # モックLLMの設定
        mock_llm = AsyncMock()
        mock_response = AIMessage(content="""{
  "steps": [
    {
      "step_number": 1,
      "reasoning": "修正版",
      "step": "修正されたステップ"
    }
  ]
}""")
        mock_llm.ainvoke.return_value = mock_response
        
        # 再計画が必要な状態
        state = {
            "goal": "テストタスク",
            "plan": [{"step_number": 1, "reasoning": "元", "step": "元のステップ"}],
            "needs_replan": True,
            "history": [{"step": "元のステップ", "observation": "エラー"}],
            "observation": "エラーが発生",
            "llm": mock_llm  # LLMインスタンスを追加
        }
        
        # 実行
        result = await planner_node(state)
        
        # 検証
        assert "plan" in result
        assert len(result["plan"]) == 1
        assert result["plan"][0]["step"] == "修正されたステップ"
        assert result["needs_replan"] is False
    
    @pytest.mark.asyncio
    async def test_planner_node_no_change_needed(self):
        """planner_nodeが計画変更不要の場合、既存の計画を返すことを確認"""
        # 計画変更不要な状態
        existing_plan = [
            {"step_number": 1, "reasoning": "既存", "step": "既存ステップ"}
        ]
        state = {
            "goal": "テストタスク",
            "plan": existing_plan,
            "needs_replan": False,
            "llm": AsyncMock()  # 使用されないがstateに含める
        }
        
        # 実行
        result = await planner_node(state)
        
        # 検証
        assert result["plan"] == existing_plan
        assert result["needs_replan"] is False 