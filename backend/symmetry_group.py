"""
SymmetryGroup: 点群・空間群を同じインターフェースで扱う抽象クラス。
空間群への拡張（フェーズ10+）を見越した設計。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

GroupType = Literal["point", "space"]


@dataclass
class SymmetryGroup:
    name: str
    group_type: GroupType
    order: int
    system: str
    operations: list[dict]          # Seitz記法の対称操作リスト
    normal_subgroups: list[str]     # 正規部分群名のリスト
    quotient_groups: list[str]      # 既約な商群名のリスト（フェーズ2で計算して設定）
    lattice: dict | None = None     # 点群はNone、空間群は格子定数
    display_name: str = ""
    description: str = ""

    @classmethod
    def from_point_group_def(cls, defn: dict, operations_map: dict) -> "SymmetryGroup":
        """
        point_groups.py の定義辞書と OPERATIONS マップから SymmetryGroup を構築する。
        """
        ops = [operations_map[key] for key in defn["operations"] if key in operations_map]
        return cls(
            name=defn["name"],
            group_type="point",
            order=defn["order"],
            system=defn["system"],
            operations=ops,
            normal_subgroups=defn["normal_subgroups"],
            quotient_groups=[],   # フェーズ2で設定
            lattice=None,
            display_name=defn.get("display_name", defn["name"]),
            description=defn.get("description", ""),
        )

    def get_operation_by_label(self, label: str) -> dict | None:
        for op in self.operations:
            if op.get("label") == label:
                return op
        return None

    def has_operation_type(self, op_type: str) -> bool:
        return any(op["type"] == op_type for op in self.operations)

    def to_dict(self) -> dict:
        """JSON シリアライズ用"""
        return {
            "name": self.name,
            "group_type": self.group_type,
            "order": self.order,
            "system": self.system,
            "operations": self.operations,
            "normal_subgroups": self.normal_subgroups,
            "quotient_groups": self.quotient_groups,
            "lattice": self.lattice,
            "display_name": self.display_name,
            "description": self.description,
        }
