"""
フェーズ2：分解アルゴリズムとステート管理

DecompositionSession がユーザー1セッション分の状態を管理する。
・現在の群
・分解ステップの履歴
・組成因子リスト
・リセット／完了判定
"""

from __future__ import annotations
from dataclasses import dataclass, field
from symmetry_group import SymmetryGroup
from group_theory import get_available_quotients, apply_quotient, build_all_groups

# 起動時に全群を一度だけ構築（再利用）
_ALL_GROUPS: dict[str, SymmetryGroup] = build_all_groups()


@dataclass
class DecompositionStep:
    """1ステップの分解記録"""
    step_index:       int    # 0始まり
    from_group:       str    # 分解前の群名
    to_group:         str    # 分解後の群名（正規部分群 N）
    quotient_symbol:  str    # 商群の記号 (G/N の表示名)
    quotient_name:    str    # 商群の表示名
    description:      str    # 人間向け説明
    op_types:         list[str]  # 関係する対称操作の種類

    def to_dict(self) -> dict:
        return {
            "step_index":      self.step_index,
            "from_group":      self.from_group,
            "to_group":        self.to_group,
            "quotient_symbol": self.quotient_symbol,
            "quotient_name":   self.quotient_name,
            "description":     self.description,
            "op_types":        self.op_types,
        }


class DecompositionSession:
    """
    1ユーザーセッション分の分解状態を管理する。
    apply_quotient() を呼ぶたびに群が更新され、history に記録が積まれる。
    current_group が C1 になると is_complete = True になる。
    """

    def __init__(self, initial_group_name: str):
        if initial_group_name not in _ALL_GROUPS:
            raise ValueError(f"Unknown point group: {initial_group_name}")
        self.initial_group_name: str = initial_group_name
        self.current_group: SymmetryGroup = _ALL_GROUPS[initial_group_name]
        self.history: list[DecompositionStep] = []

    # ── 読み取り専用プロパティ ────────────────────────────────

    @property
    def is_complete(self) -> bool:
        return self.current_group.order == 1  # C1 に到達

    @property
    def composition_factors(self) -> list[str]:
        """これまでに取り除いた商群の記号リスト（組成因子）"""
        return [step.quotient_symbol for step in self.history]

    @property
    def decomposition_path(self) -> list[str]:
        """分解列: ["C3v", "C3", "C1"] のような群名の列"""
        path = [self.initial_group_name]
        for step in self.history:
            path.append(step.to_group)
        return path

    # ── 操作 ─────────────────────────────────────────────────

    def get_available_quotients(self) -> list[dict]:
        """現在の群に対して選べる既約な商群リストを返す"""
        if self.is_complete:
            return []
        return get_available_quotients(self.current_group)

    def apply(self, normal_subgroup_name: str) -> DecompositionStep:
        """
        商群を選んで分解を1ステップ進める。
        normal_subgroup_name: 正規部分群の名前（これが次の群になる）
        戻り値: 実行されたステップの記録
        例外: 無効な正規部分群名を渡すと ValueError
        """
        if self.is_complete:
            raise RuntimeError("Decomposition is already complete (reached C1)")

        # 選べる商群に含まれているか確認
        available = {q["normal_subgroup"]: q for q in self.get_available_quotients()}
        if normal_subgroup_name not in available:
            raise ValueError(
                f"'{normal_subgroup_name}' is not an available normal subgroup of "
                f"'{self.current_group.name}'. Available: {list(available.keys())}"
            )

        q_info = available[normal_subgroup_name]
        step = DecompositionStep(
            step_index=len(self.history),
            from_group=self.current_group.name,
            to_group=normal_subgroup_name,
            quotient_symbol=q_info["quotient_symbol"],
            quotient_name=q_info["quotient_name"],
            description=q_info["description"],
            op_types=q_info["op_types"],
        )
        self.history.append(step)
        self.current_group = _ALL_GROUPS[normal_subgroup_name]
        return step

    def reset(self) -> None:
        """最初の群に戻す"""
        self.current_group = _ALL_GROUPS[self.initial_group_name]
        self.history.clear()

    # ── シリアライズ ──────────────────────────────────────────

    def to_dict(self) -> dict:
        """API レスポンス用の辞書表現"""
        return {
            "initial_group":        self.initial_group_name,
            "current_group":        self.current_group.to_dict(),
            "decomposition_path":   self.decomposition_path,
            "history":              [s.to_dict() for s in self.history],
            "composition_factors":  self.composition_factors,
            "available_quotients":  self.get_available_quotients(),
            "is_complete":          self.is_complete,
            "step_count":           len(self.history),
        }


# ── セッションストア（インメモリ、フェーズ9でDB化可） ──────────

import uuid

_SESSIONS: dict[str, DecompositionSession] = {}


def create_session(group_name: str) -> tuple[str, DecompositionSession]:
    """新しいセッションを作成して (session_id, session) を返す"""
    session_id = str(uuid.uuid4())
    session = DecompositionSession(group_name)
    _SESSIONS[session_id] = session
    return session_id, session


def get_session(session_id: str) -> DecompositionSession:
    if session_id not in _SESSIONS:
        raise KeyError(f"Session not found: {session_id}")
    return _SESSIONS[session_id]


def delete_session(session_id: str) -> None:
    _SESSIONS.pop(session_id, None)


def list_available_groups() -> list[dict]:
    """スタート画面用：選択可能な点群の一覧"""
    return [
        {
            "name":         name,
            "display_name": g.display_name,
            "order":        g.order,
            "system":       g.system,
            "description":  g.description,
        }
        for name, g in _ALL_GROUPS.items()
    ]
