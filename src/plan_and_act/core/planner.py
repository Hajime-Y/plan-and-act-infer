"""
Plan-and-Act フレームワークの Planner コンポーネント

このモジュールは、タスクの計画生成と動的再計画を担当する Planner を実装します。
Planner は、高レベルのタスク目標を実行可能なステップに分解し、
実行結果に基づいて計画を調整します。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


class PlanStep(BaseModel):
    """単一の計画ステップを表すモデル"""
    
    step_number: int = Field(description="ステップ番号（1から始まる連番）")
    reasoning: str = Field(description="このステップが必要な理由・論理的根拠")
    step: str = Field(description="実行すべき高レベルタスクの説明")

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "step_number": self.step_number,
            "reasoning": self.reasoning,
            "step": self.step,
        }


class Plan(BaseModel):
    """計画全体を表すモデル"""
    
    steps: List[PlanStep] = Field(description="計画ステップのリスト")

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "steps": [step.to_dict() for step in self.steps]
        }


# プランナー用のシステムプロンプトテンプレート
PLANNER_SYSTEM_PROMPT = """あなたはタスク計画を専門とするAIアシスタントです。
ユーザーの目標に基づいて、実行可能なステップからなる詳細な計画を作成してください。

重要な原則:
1. 各ステップは独立して実行可能で、明確な成果を持つこと
2. ステップ間の依存関係を考慮し、論理的な順序で配置すること
3. 各ステップは具体的で、実行者が迷わないよう明確に記述すること
4. 必要に応じて、エラーハンドリングや代替案を考慮すること

出力形式:
必ず以下のJSON形式で出力してください。他の形式や説明文は含めないでください。

```json
{
  "steps": [
    {
      "step_number": 1,
      "reasoning": "このステップが必要な理由や戦略的根拠",
      "step": "実行すべき高レベルタスクの明確な説明"
    },
    {
      "step_number": 2,
      "reasoning": "...",
      "step": "..."
    }
  ]
}
```"""

# 再計画用のシステムプロンプトテンプレート
REPLANNING_SYSTEM_PROMPT = """あなたはタスク計画を専門とするAIアシスタントです。
現在の計画の実行状況と観測結果に基づいて、計画を見直し、必要に応じて修正・更新してください。

重要な原則:
1. 既に成功したステップは変更しない
2. 失敗や予期しない結果に対して、適切な代替案を提供する
3. 新しい情報を活用して、より効果的な計画に更新する
4. 目標達成の可能性を最大化する

現在の状況:
- 元の目標: {goal}
- 現在の計画: {current_plan}
- 実行履歴: {history}
- 最新の観測: {observation}

出力形式:
必ず以下のJSON形式で出力してください。他の形式や説明文は含めないでください。

```json
{{
  "steps": [
    {{
      "step_number": 1,
      "reasoning": "このステップが必要な理由（既存ステップの場合は変更理由）",
      "step": "実行すべき高レベルタスクの明確な説明"
    }}
  ]
}}
```"""


class Planner:
    """タスクの計画生成と動的再計画を行うクラス"""
    
    def __init__(self, llm: BaseChatModel):
        """
        Args:
            llm: 使用する言語モデル
        """
        self.llm = llm
        
    def _parse_plan_response(self, response: str) -> Plan:
        """LLMの応答から計画を抽出してPlanオブジェクトに変換"""
        try:
            # JSON部分を抽出（```json ... ```の形式に対応）
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                # 全体をJSONとして扱う
                json_str = response.strip()
            
            # JSONをパース
            data = json.loads(json_str)
            
            # Planオブジェクトに変換
            steps = []
            for step_data in data.get("steps", []):
                step = PlanStep(
                    step_number=step_data["step_number"],
                    reasoning=step_data["reasoning"],
                    step=step_data["step"]
                )
                steps.append(step)
            
            return Plan(steps=steps)
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # パースエラーの場合は空の計画を返す
            # 実際の運用では適切なエラーハンドリングが必要
            return Plan(steps=[])
    
    async def generate_initial_plan(self, goal: str) -> Plan:
        """
        初期計画を生成する
        
        Args:
            goal: ユーザーの目標・タスク
            
        Returns:
            生成された計画
        """
        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=f"目標: {goal}")
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_plan_response(response.content)
    
    async def replan(
        self,
        goal: str,
        current_plan: Plan,
        history: List[Dict[str, Any]],
        observation: str
    ) -> Plan:
        """
        現在の状況に基づいて計画を再生成する
        
        Args:
            goal: 元の目標
            current_plan: 現在の計画
            history: 実行履歴
            observation: 最新の観測結果
            
        Returns:
            更新された計画
        """
        # 現在の計画を文字列化
        current_plan_str = json.dumps(current_plan.to_dict(), ensure_ascii=False, indent=2)
        
        # 履歴を文字列化
        history_str = json.dumps(history, ensure_ascii=False, indent=2)
        
        prompt = REPLANNING_SYSTEM_PROMPT.format(
            goal=goal,
            current_plan=current_plan_str,
            history=history_str,
            observation=observation
        )
        
        messages = [
            SystemMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_plan_response(response.content)
    
    def needs_replan(self, observation: str) -> bool:
        """
        観測結果から再計画が必要かどうかを判定する
        
        Args:
            observation: エグゼキューターからの観測結果
            
        Returns:
            再計画が必要な場合True
        """
        # エラーや失敗を示すキーワードをチェック
        error_indicators = [
            "エラー", "失敗", "見つかりません", "アクセスできません",
            "error", "failed", "not found", "cannot access",
            "exception", "timeout", "unable to", "denied"
        ]
        
        observation_lower = observation.lower()
        return any(indicator in observation_lower for indicator in error_indicators)


def create_planner(llm: BaseChatModel) -> Planner:
    """
    Plannerインスタンスを作成するファクトリメソッド
    
    Args:
        llm: 使用する言語モデル
        
    Returns:
        Plannerインスタンス
    """
    return Planner(llm=llm)


# LangGraphノードとして動作する関数
async def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraphのノードとして動作するプランナー関数
    
    Args:
        state: グラフの状態
        
    Returns:
        更新された状態
    """
    # LLMインスタンスを取得（実際の実装では設定から取得）
    # stateまたは環境からLLMを取得する
    llm = state.get("llm")
    if not llm:
        # デフォルトのLLMを作成（実際の実装では設定ファイルから読み込む）
        try:
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(model="claude-3-sonnet-20241022")
        except ImportError:
            # テスト環境などでAnthropicが利用できない場合のフォールバック
            raise ValueError("LLM instance not found in state and ChatAnthropic not available")
    
    planner = create_planner(llm)
    
    # 初期計画生成か再計画かを判定
    if not state.get("plan") or state.get("needs_replan", False):
        if not state.get("plan"):
            # 初期計画生成
            plan = await planner.generate_initial_plan(state["goal"])
        else:
            # 再計画
            current_plan = Plan(steps=[
                PlanStep(**step) for step in state["plan"]
            ])
            plan = await planner.replan(
                goal=state["goal"],
                current_plan=current_plan,
                history=state.get("history", []),
                observation=state.get("observation", "")
            )
        
        return {
            "plan": [step.to_dict() for step in plan.steps],
            "current_step_idx": state.get("current_step_idx", 0),
            "needs_replan": False
        }
    
    # 計画の変更が不要な場合
    return {
        "plan": state["plan"],
        "needs_replan": False
    } 