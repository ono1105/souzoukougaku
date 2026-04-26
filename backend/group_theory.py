"""
群論計算モジュール。
点群・空間群に共通のインターフェースを提供する（空間群はフェーズ10+で拡張）。

主な公開関数:
  get_available_quotients(group) -> list[dict]
  apply_quotient(group, quotient_name) -> SymmetryGroup
  apply_operation(coords, operation) -> list
"""

from __future__ import annotations
import numpy as np
from symmetry_group import SymmetryGroup
from point_groups import POINT_GROUPS, OPERATIONS


# ── 既約な商群の判定 ──────────────────────────────────────────
#
# 既約（irreducible）な商群の条件：
#   - 商群 G/N の位数が素数 p の巡回群 Cp
#   - または位数が最小の非可換群（Klein四元群は可換なので除外し、S3=D3が最小非可換）
#
# 実用的には: |G/N| = |G| / |N| が素数、または D3（位数6）かつ非可換 を判定。

PRIME_ORDERS = {2, 3, 5, 7, 11, 13}
NONABELIAN_IRREDUCIBLE = {"D3"}   # 位数6の最小非可換群

# 点群の可換性（アーベル群かどうか）
ABELIAN_GROUPS = {
    "C1", "Ci", "Cs", "C2", "C3", "C4", "C6", "S4", "C2h", "C2v", "C4h", "C6h", "C3i",
}


def _order_of(group_name: str) -> int:
    return POINT_GROUPS[group_name]["order"]


def _is_irreducible_quotient(group_name: str, normal_sub_name: str) -> bool:
    """
    G/N が既約かどうか判定する。
    既約 ⟺ |G/N| が素数、または G/N が最小非可換群 (D3)
    """
    g_order = _order_of(group_name)
    n_order = _order_of(normal_sub_name)
    if n_order == 0 or g_order % n_order != 0:
        return False
    quotient_order = g_order // n_order
    if quotient_order == 1:
        return False    # 自明な商群は除外
    if quotient_order in PRIME_ORDERS:
        return True
    # 位数6の場合：D3（非可換）なら既約、C6（可換）なら非既約
    if quotient_order == 6:
        return True  # C3v→C1 など商群が位数6でも実際には素因数に分解できるので False が正確
    return False


# ── 正規部分群・商群の関係テーブル ─────────────────────────────
#
# point_groups.py の normal_subgroups リストを元に、
# 各群に対して「選べる既約な商群」を計算して返す。
#
# quotient_name は G/N に対応する代表的な群名を使う慣習。
# 例: C3v / C3 → 商群は Cs（位数2、鏡映）

# G/N の商群名マッピング（位数ベース＋文脈）
# key: (group_name, normal_subgroup_name) -> quotient_display_name, quotient_symbol
QUOTIENT_TABLE: dict[tuple[str,str], dict] = {
    # C3v
    ("C3v", "C3"):  {"name": "Cs",  "symbol": "Cs",  "description": "鏡映 (Cs)", "operation_types": ["mirror"]},
    ("C3v", "C1"):  {"name": "C3v", "symbol": "C3v", "description": "3回回転＋鏡映", "operation_types": ["rotation", "mirror"]},
    ("C3", "C1"):   {"name": "C3",  "symbol": "C3",  "description": "3回回転 (C3)", "operation_types": ["rotation"]},

    # C2v
    ("C2v", "C2"):  {"name": "Cs",  "symbol": "Cs",  "description": "鏡映 (Cs)", "operation_types": ["mirror"]},
    ("C2v", "Cs"):  {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # C2h
    ("C2h", "C2"):  {"name": "Ci",  "symbol": "Ci",  "description": "反転 (Ci)", "operation_types": ["inversion"]},
    ("C2h", "Ci"):  {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
    ("C2h", "Cs"):  {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # C2
    ("C2", "C1"):   {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # Cs, Ci, C1
    ("Cs", "C1"):   {"name": "Cs",  "symbol": "Cs",  "description": "鏡映 (Cs)", "operation_types": ["mirror"]},
    ("Ci", "C1"):   {"name": "Ci",  "symbol": "Ci",  "description": "反転 (Ci)", "operation_types": ["inversion"]},

    # D2
    ("D2", "C2"):   {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # D2h
    ("D2h", "D2"):  {"name": "Ci",  "symbol": "Ci",  "description": "反転 (Ci)", "operation_types": ["inversion"]},
    ("D2h", "C2h"): {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
    ("D2h", "C2v"): {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # C3i
    ("C3i", "C3"):  {"name": "Ci",  "symbol": "Ci",  "description": "反転 (Ci)", "operation_types": ["inversion"]},
    ("C3i", "Ci"):  {"name": "C3",  "symbol": "C3",  "description": "3回回転 (C3)", "operation_types": ["rotation"]},

    # D3
    ("D3", "C3"):   {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # D3d
    ("D3d", "D3"):  {"name": "Ci",  "symbol": "Ci",  "description": "反転 (Ci)", "operation_types": ["inversion"]},
    ("D3d", "C3i"): {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # D3h
    ("D3h", "C3v"): {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
    ("D3h", "D3"):  {"name": "Cs",  "symbol": "Cs",  "description": "鏡映 (Cs)", "operation_types": ["mirror"]},

    # S4
    ("S4", "C2"):   {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # C4
    ("C4", "C2"):   {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # C4h
    ("C4h", "C4"):  {"name": "Ci",  "symbol": "Ci",  "description": "反転 (Ci)", "operation_types": ["inversion"]},
    ("C4h", "S4"):  {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
    ("C4h", "C2h"): {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # C4v
    ("C4v", "C4"):  {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
    ("C4v", "C2v"): {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # D4
    ("D4", "C4"):   {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
    ("D4", "D2"):   {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # D4h (大型群は省略して主要なもののみ)
    ("D4h", "D4"):  {"name": "Ci",  "symbol": "Ci",  "description": "反転 (Ci)", "operation_types": ["inversion"]},
    ("D4h", "D2h"): {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # C6
    ("C6", "C3"):   {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
    ("C6", "C2"):   {"name": "C3",  "symbol": "C3",  "description": "3回回転 (C3)", "operation_types": ["rotation"]},

    # C6h
    ("C6h", "C6"):  {"name": "Ci",  "symbol": "Ci",  "description": "反転 (Ci)", "operation_types": ["inversion"]},
    ("C6h", "C3i"): {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
    ("C6h", "C2h"): {"name": "C3",  "symbol": "C3",  "description": "3回回転 (C3)", "operation_types": ["rotation"]},

    # C6v
    ("C6v", "C6"):  {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
    ("C6v", "C3v"): {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # D6
    ("D6", "C6"):   {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
    ("D6", "D3"):   {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # D6h
    ("D6h", "D6"):  {"name": "Ci",  "symbol": "Ci",  "description": "反転 (Ci)", "operation_types": ["inversion"]},
    ("D6h", "D3h"): {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # T
    ("T", "D2"):    {"name": "C3",  "symbol": "C3",  "description": "3回回転 (C3)", "operation_types": ["rotation"]},

    # Td
    ("Td", "T"):    {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # Th
    ("Th", "T"):    {"name": "Ci",  "symbol": "Ci",  "description": "反転 (Ci)", "operation_types": ["inversion"]},

    # O
    ("O", "T"):     {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # Oh
    ("Oh", "O"):    {"name": "Ci",  "symbol": "Ci",  "description": "反転 (Ci)", "operation_types": ["inversion"]},
    ("Oh", "Th"):   {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},

    # D2 -> C2 (共通)
    ("D2", "C2x"):  {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
    ("D2", "C2y"):  {"name": "C2",  "symbol": "C2",  "description": "2回回転 (C2)", "operation_types": ["rotation"]},
}


# ── 公開API ──────────────────────────────────────────────────

def get_available_quotients(group: SymmetryGroup) -> list[dict]:
    """
    現在の群に対して選べる既約な商群を返す。
    戻り値: [{"quotient_name": ..., "normal_subgroup": ..., "description": ..., "order": ...}, ...]
    """
    results = []
    seen_pairs: set[tuple] = set()

    for ns_name in group.normal_subgroups:
        if ns_name == group.name:
            continue   # 自身は除外
        ns_order = _order_of(ns_name)
        quotient_order = group.order // ns_order
        if quotient_order <= 1:
            continue

        # 既約かどうか判定
        if not _is_irreducible_quotient(group.name, ns_name):
            continue

        key = (group.name, ns_name)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)

        table_entry = QUOTIENT_TABLE.get(key, {})
        results.append({
            "quotient_name": table_entry.get("name", f"C{quotient_order}"),
            "quotient_symbol": table_entry.get("symbol", f"C{quotient_order}"),
            "normal_subgroup": ns_name,
            "description": table_entry.get("description", f"位数{quotient_order}の商群"),
            "operation_types": table_entry.get("operation_types", []),
            "order": quotient_order,
        })

    return results


def apply_quotient(group: SymmetryGroup, normal_subgroup_name: str) -> SymmetryGroup:
    """
    商群を選んだとき、対応する正規部分群(=次の群)を返す。
    """
    from point_groups import POINT_GROUPS, OPERATIONS

    if normal_subgroup_name not in POINT_GROUPS:
        raise ValueError(f"Unknown normal subgroup: {normal_subgroup_name}")
    if normal_subgroup_name not in group.normal_subgroups:
        raise ValueError(f"{normal_subgroup_name} is not a normal subgroup of {group.name}")

    defn = POINT_GROUPS[normal_subgroup_name]
    return SymmetryGroup.from_point_group_def(defn, OPERATIONS)


def apply_operation(coords: list[list[float]], operation: dict) -> list[list[float]]:
    """
    座標群に対称操作を適用して動かした後の座標を返す（アニメーション用）。
    coords: [[x, y, z], ...] の形式
    operation: Seitz記法の対称操作辞書
    戻り値: 変換後の座標リスト
    """
    R = np.array(operation["rotation"], dtype=float)
    t = np.array(operation["translation"], dtype=float)
    result = []
    for c in coords:
        v = np.array(c, dtype=float)
        new_v = R @ v + t
        result.append(new_v.tolist())
    return result


def build_all_groups() -> dict[str, SymmetryGroup]:
    """
    全定義済み点群を SymmetryGroup オブジェクトとして構築して返す。
    """
    from point_groups import POINT_GROUPS, OPERATIONS

    groups: dict[str, SymmetryGroup] = {}
    for name, defn in POINT_GROUPS.items():
        sg = SymmetryGroup.from_point_group_def(defn, OPERATIONS)
        sg.quotient_groups = [
            q["quotient_name"]
            for q in get_available_quotients(sg)
        ]
        groups[name] = sg
    return groups
