"""
群論計算モジュール。
点群・空間群に共通のインターフェースを提供する（空間群はフェーズ10+で拡張）。

主な公開関数:
  get_available_quotients(group) -> list[dict]
  apply_quotient(group, normal_subgroup_name) -> SymmetryGroup
  apply_operation(coords, operation) -> list
  build_all_groups() -> dict[str, SymmetryGroup]
"""

from __future__ import annotations
import numpy as np
from symmetry_group import SymmetryGroup
from point_groups import POINT_GROUPS, OPERATIONS


# ── 商群情報テーブル ─────────────────────────────────────────
# key: (group_name, maximal_normal_subgroup_name)
# value: 商群 G/N の表示情報
#
# 注: N は point_groups.py の normal_subgroups（最大正規部分群のみ）に列挙された
# ものだけが有効。したがって G/N は必ず既約（素数位数）となる。

QUOTIENT_INFO: dict[tuple[str, str], dict] = {
    # ── Triclinic / Monoclinic ───────────────────────
    ("Ci",  "C1"): {"name": "Cᵢ",  "symbol": "Ci",  "op_types": ["inversion"], "description": "反転 (Ci)"},
    ("Cs",  "C1"): {"name": "Cₛ",  "symbol": "Cs",  "op_types": ["mirror"],    "description": "鏡映 (Cs)"},
    ("C2",  "C1"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("C2h", "C2"): {"name": "Cᵢ",  "symbol": "Ci",  "op_types": ["inversion"], "description": "反転 (Ci)"},
    ("C2h", "Ci"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("C2h", "Cs"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("C2v", "C2"): {"name": "Cₛ",  "symbol": "Cs",  "op_types": ["mirror"],    "description": "鏡映 (Cs)"},
    ("C2v", "Cs"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    # ── Orthorhombic ─────────────────────────────────
    ("D2",  "C2"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("D2h", "D2"):  {"name": "Cᵢ",  "symbol": "Ci",  "op_types": ["inversion"], "description": "反転 (Ci)"},
    ("D2h", "C2h"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("D2h", "C2v"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    # ── Trigonal ─────────────────────────────────────
    ("C3",  "C1"): {"name": "C₃",  "symbol": "C3",  "op_types": ["rotation"],  "description": "3回回転 (C3)"},

    ("C3i", "C3"): {"name": "Cᵢ",  "symbol": "Ci",  "op_types": ["inversion"], "description": "反転 (Ci)"},
    ("C3i", "Ci"): {"name": "C₃",  "symbol": "C3",  "op_types": ["rotation"],  "description": "3回回転 (C3)"},

    ("C3v", "C3"): {"name": "Cₛ",  "symbol": "Cs",  "op_types": ["mirror"],    "description": "鏡映 (Cs)"},

    ("D3",  "C3"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("D3d", "D3"):  {"name": "Cᵢ",  "symbol": "Ci",  "op_types": ["inversion"], "description": "反転 (Ci)"},
    ("D3d", "C3i"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("D3h", "C3v"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("D3h", "D3"):  {"name": "Cₛ",  "symbol": "Cs",  "op_types": ["mirror"],    "description": "鏡映 (Cs)"},

    # ── Tetragonal ───────────────────────────────────
    ("S4",  "C2"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("C4",  "C2"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("C4h", "C4"):  {"name": "Cᵢ",  "symbol": "Ci",  "op_types": ["inversion"], "description": "反転 (Ci)"},
    ("C4h", "S4"):  {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("C4h", "C2h"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("C4v", "C4"):  {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("C4v", "C2v"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("D2d", "S4"):  {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("D2d", "D2"):  {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("D4",  "C4"):  {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("D4",  "D2"):  {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("D4h", "D4"):  {"name": "Cᵢ",  "symbol": "Ci",  "op_types": ["inversion"], "description": "反転 (Ci)"},
    ("D4h", "C4h"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("D4h", "C4v"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("D4h", "D2h"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    # ── Hexagonal ────────────────────────────────────
    ("C3h", "C3"): {"name": "Cₛ",  "symbol": "Cs",  "op_types": ["mirror"],    "description": "鏡映 (Cs)"},
    ("C3h", "Cs"): {"name": "C₃",  "symbol": "C3",  "op_types": ["rotation"],  "description": "3回回転 (C3)"},

    ("C6",  "C3"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("C6",  "C2"): {"name": "C₃",  "symbol": "C3",  "op_types": ["rotation"],  "description": "3回回転 (C3)"},

    ("C6h", "C6"):  {"name": "Cᵢ",  "symbol": "Ci",  "op_types": ["inversion"], "description": "反転 (Ci)"},
    ("C6h", "C3i"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("C6h", "C2h"): {"name": "C₃",  "symbol": "C3",  "op_types": ["rotation"],  "description": "3回回転 (C3)"},

    ("C6v", "C6"):  {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("C6v", "C3v"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("D6",  "C6"):  {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("D6",  "D3"):  {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    ("D6h", "D6"):  {"name": "Cᵢ",  "symbol": "Ci",  "op_types": ["inversion"], "description": "反転 (Ci)"},
    ("D6h", "D3h"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("D6h", "C6h"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("D6h", "C6v"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},

    # ── Cubic ────────────────────────────────────────
    ("T",  "D2"): {"name": "C₃",  "symbol": "C3",  "op_types": ["rotation"],  "description": "3回回転 (C3)"},
    ("Td", "T"):  {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("Th", "T"):  {"name": "Cᵢ",  "symbol": "Ci",  "op_types": ["inversion"], "description": "反転 (Ci)"},
    ("O",  "T"):  {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
    ("Oh", "O"):  {"name": "Cᵢ",  "symbol": "Ci",  "op_types": ["inversion"], "description": "反転 (Ci)"},
    ("Oh", "Th"): {"name": "C₂",  "symbol": "C2",  "op_types": ["rotation"],  "description": "2回回転 (C2)"},
}


# ── 公開API ──────────────────────────────────────────────────

def get_available_quotients(group: SymmetryGroup) -> list[dict]:
    """
    現在の群に対して選べる既約な商群を返す。
    normal_subgroups は最大正規部分群のみを持つので、全て既約（素数位数の商群）。

    戻り値: [
      {"quotient_name": ..., "quotient_symbol": ..., "normal_subgroup": ...,
       "description": ..., "op_types": [...], "quotient_order": ...},
      ...
    ]
    """
    if group.order <= 1:
        return []

    results = []
    for ns_name in group.normal_subgroups:
        ns_order = POINT_GROUPS[ns_name]["order"] if ns_name in POINT_GROUPS else 1
        quotient_order = group.order // ns_order

        info = QUOTIENT_INFO.get((group.name, ns_name), {})
        results.append({
            "quotient_name":   info.get("name",   f"C{quotient_order}"),
            "quotient_symbol": info.get("symbol", f"C{quotient_order}"),
            "normal_subgroup": ns_name,
            "description":     info.get("description", f"位数{quotient_order}の商群"),
            "op_types":        info.get("op_types", []),
            "quotient_order":  quotient_order,
        })
    return results


def apply_quotient(group: SymmetryGroup, normal_subgroup_name: str) -> SymmetryGroup:
    """
    商群を選んだとき、対応する正規部分群（=次のステップの群）を返す。
    group.normal_subgroups に含まれない名前を指定するとエラー。
    """
    if normal_subgroup_name not in POINT_GROUPS:
        raise ValueError(f"Unknown normal subgroup: {normal_subgroup_name}")
    if normal_subgroup_name not in group.normal_subgroups:
        raise ValueError(
            f"{normal_subgroup_name} is not a (maximal) normal subgroup of {group.name}"
        )
    defn = POINT_GROUPS[normal_subgroup_name]
    return SymmetryGroup.from_point_group_def(defn, OPERATIONS)


def apply_operation(coords: list[list[float]], operation: dict) -> list[list[float]]:
    """
    座標群に対称操作を適用する（アニメーション用）。
    coords: [[x, y, z], ...] の形式
    operation: Seitz 記法の辞書
    戻り値: 変換後の座標リスト
    """
    R = np.array(operation["rotation"], dtype=float)
    t = np.array(operation["translation"], dtype=float)
    return [(R @ np.array(c, dtype=float) + t).tolist() for c in coords]


def build_all_groups() -> dict[str, SymmetryGroup]:
    """全定義済み点群を SymmetryGroup オブジェクトとして構築して返す。"""
    groups: dict[str, SymmetryGroup] = {}
    for name, defn in POINT_GROUPS.items():
        sg = SymmetryGroup.from_point_group_def(defn, OPERATIONS)
        sg.quotient_groups = [
            q["quotient_symbol"] for q in get_available_quotients(sg)
        ]
        groups[name] = sg
    return groups
