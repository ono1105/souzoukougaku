"""
32 crystal point group definitions.
Each group stores its symmetry operations in Seitz notation (R | t), t=0 for point groups.
Designed to share the same interface as future space groups (Phase 10+).
"""

from symmetry_operations import (
    E, C2z, C2x, C2y, C3z_exact, C3z_inv_exact, C4z, C4z_inv, C6z, C6z_inv,
    C2x_d3, C2_d3b, C2_d3c, C2_xy, C2_xy_neg,
    i_op, sigma_h, sigma_v, sigma_v2, sigma_d, sigma_d2,
    sigma_v_d3b, sigma_v_d3c,
    S4z, S4z_inv, S6z, S6z_inv,
    C3_111, C3_111_inv, C3_1m1m, C3_1m1m_inv,
    C3_m11m, C3_m11m_inv, C3_mm1, C3_mm1_inv,
    C2_T_x, C2_T_y, C2_T_z,
    C4x, C4x_inv, C4y, C4y_inv,
    C2_Oh_xz, C2_Oh_yz, C2_Oh_xz_n, C2_Oh_yz_n, C2_Oh_xy_n,
    sigma_xz, sigma_yz, sigma_xy,
    sigma_Oh_d1, sigma_Oh_d2, sigma_Oh_d3, sigma_Oh_d4, sigma_Oh_d5, sigma_Oh_d6,
    S4x, S4x_inv, S4y, S4y_inv,
)


# ── 生の対称操作セット（ラベル付き辞書）───────────────────────

OPERATIONS: dict[str, dict] = {
    "E":        E,
    "C2":       C2z,
    "C2x":      C2x,
    "C2y":      C2y,
    "C2'":      C2_xy,
    "C2''":     C2_xy_neg,
    "C2a":      C2x_d3,
    "C2b":      C2_d3b,
    "C2c":      C2_d3c,
    "C3":       C3z_exact,
    "C3^2":     C3z_inv_exact,
    "C4":       C4z,
    "C4^3":     C4z_inv,
    "C6":       C6z,
    "C6^5":     C6z_inv,
    "i":        i_op,
    "σh":       sigma_h,
    "σv":       sigma_v,
    "σv'":      sigma_v2,
    "σv2":      sigma_v_d3b,
    "σv3":      sigma_v_d3c,
    "σd":       sigma_d,
    "σd'":      sigma_d2,
    "S4":       S4z,
    "S4^3":     S4z_inv,
    "S6":       S6z,
    "S6^5":     S6z_inv,
    "C3(111)":  C3_111,   "C3^2(111)":  C3_111_inv,
    "C3(1-1-1)":C3_1m1m,  "C3^2(1-1-1)":C3_1m1m_inv,
    "C3(-11-1)":C3_m11m,  "C3^2(-11-1)":C3_m11m_inv,
    "C3(-1-11)":C3_mm1,   "C3^2(-1-11)":C3_mm1_inv,
    "C2(x)":    C2_T_x,  "C2(y)":  C2_T_y,  "C2(z)":  C2_T_z,
    "C4x":      C4x,  "C4x^3": C4x_inv,
    "C4y":      C4y,  "C4y^3": C4y_inv,
    "C2(xz)":   C2_Oh_xz, "C2(yz)":  C2_Oh_yz,
    "C2(x-z)":  C2_Oh_xz_n, "C2(y-z)": C2_Oh_yz_n,
    "C2(x-y)":  C2_Oh_xy_n,
    "σxz":      sigma_xz, "σyz": sigma_yz, "σxy": sigma_xy,
    "σd1":      sigma_Oh_d1, "σd2": sigma_Oh_d2,
    "σd3":      sigma_Oh_d3, "σd4": sigma_Oh_d4,
    "σd5":      sigma_Oh_d5, "σd6": sigma_Oh_d6,
    "S4x":      S4x, "S4x^3": S4x_inv,
    "S4y":      S4y, "S4y^3": S4y_inv,
}


# ── 32結晶点群の定義 ───────────────────────────────────────────
# 各点群は次の情報を持つ:
#   name          : 点群名（シェーンフリース記号）
#   order         : 群の位数（対称操作の数）
#   operations    : 対称操作ラベルのリスト（OPERATIONS への参照キー）
#   system        : 結晶系
#   normal_subgroups : 正規部分群名のリスト（E と自身を含む）
#   composition_series: 組成列の例（1通り）

POINT_GROUPS: dict[str, dict] = {

    # ── Triclinic ──────────────────────────────────────────────
    "C1": {
        "name": "C1", "order": 1, "system": "triclinic",
        "operations": ["E"],
        "normal_subgroups": ["C1"],
        "composition_series": [["C1"]],
        "display_name": "C₁",
        "description": "恒等元のみ",
    },
    "Ci": {
        "name": "Ci", "order": 2, "system": "triclinic",
        "operations": ["E", "i"],
        "normal_subgroups": ["C1", "Ci"],
        "composition_series": [["Ci", "C1"]],
        "display_name": "Cᵢ",
        "description": "反転対称",
    },

    # ── Monoclinic ─────────────────────────────────────────────
    "Cs": {
        "name": "Cs", "order": 2, "system": "monoclinic",
        "operations": ["E", "σh"],
        "normal_subgroups": ["C1", "Cs"],
        "composition_series": [["Cs", "C1"]],
        "display_name": "Cₛ",
        "description": "鏡映対称",
    },
    "C2": {
        "name": "C2", "order": 2, "system": "monoclinic",
        "operations": ["E", "C2"],
        "normal_subgroups": ["C1", "C2"],
        "composition_series": [["C2", "C1"]],
        "display_name": "C₂",
        "description": "2回回転軸",
    },
    "C2h": {
        "name": "C2h", "order": 4, "system": "monoclinic",
        "operations": ["E", "C2", "i", "σh"],
        "normal_subgroups": ["C1", "C2", "Ci", "Cs", "C2h"],
        "composition_series": [
            ["C2h", "C2", "C1"],
            ["C2h", "Ci", "C1"],
            ["C2h", "Cs", "C1"],
        ],
        "display_name": "C₂ₕ",
        "description": "2回回転軸＋水平鏡映面",
    },
    "C2v": {
        "name": "C2v", "order": 4, "system": "orthorhombic",
        "operations": ["E", "C2", "σv", "σv'"],
        "normal_subgroups": ["C1", "C2", "Cs", "C2v"],
        "composition_series": [
            ["C2v", "C2", "C1"],
            ["C2v", "Cs", "C1"],
        ],
        "display_name": "C₂ᵥ",
        "description": "2回回転軸＋2つの鏡映面",
    },

    # ── Orthorhombic ───────────────────────────────────────────
    "D2": {
        "name": "D2", "order": 4, "system": "orthorhombic",
        "operations": ["E", "C2", "C2x", "C2y"],
        "normal_subgroups": ["C1", "C2", "D2"],
        "composition_series": [["D2", "C2", "C1"]],
        "display_name": "D₂",
        "description": "3つの直交する2回回転軸",
    },
    "D2h": {
        "name": "D2h", "order": 8, "system": "orthorhombic",
        "operations": ["E", "C2", "C2x", "C2y", "i", "σh", "σv", "σv'"],
        "normal_subgroups": ["C1", "C2", "Ci", "Cs", "C2h", "C2v", "D2", "D2h"],
        "composition_series": [
            ["D2h", "D2", "C2", "C1"],
            ["D2h", "C2h", "C2", "C1"],
            ["D2h", "C2v", "C2", "C1"],
        ],
        "display_name": "D₂ₕ",
        "description": "mmm",
    },

    # ── Trigonal ───────────────────────────────────────────────
    "C3": {
        "name": "C3", "order": 3, "system": "trigonal",
        "operations": ["E", "C3", "C3^2"],
        "normal_subgroups": ["C1", "C3"],
        "composition_series": [["C3", "C1"]],
        "display_name": "C₃",
        "description": "3回回転軸",
    },
    "C3i": {
        "name": "C3i", "order": 6, "system": "trigonal",
        "operations": ["E", "C3", "C3^2", "i", "S6", "S6^5"],
        "normal_subgroups": ["C1", "C3", "Ci", "C3i"],
        "composition_series": [
            ["C3i", "C3", "C1"],
            ["C3i", "Ci", "C1"],
        ],
        "display_name": "C₃ᵢ (S₆)",
        "description": "3回回転＋反転（S6）",
    },
    "C3v": {
        "name": "C3v", "order": 6, "system": "trigonal",
        "operations": ["E", "C3", "C3^2", "σv", "σv2", "σv3"],
        "normal_subgroups": ["C1", "C3", "C3v"],
        "composition_series": [["C3v", "C3", "C1"]],
        "display_name": "C₃ᵥ",
        "description": "3回回転軸＋3つの鏡映面",
    },
    "D3": {
        "name": "D3", "order": 6, "system": "trigonal",
        "operations": ["E", "C3", "C3^2", "C2a", "C2b", "C2c"],
        "normal_subgroups": ["C1", "C3", "D3"],
        "composition_series": [["D3", "C3", "C1"]],
        "display_name": "D₃",
        "description": "3回回転軸＋3つの2回回転軸",
    },
    "D3d": {
        "name": "D3d", "order": 12, "system": "trigonal",
        "operations": ["E", "C3", "C3^2", "C2a", "C2b", "C2c", "i", "S6", "S6^5", "σd", "σd'", "σd2"],
        "normal_subgroups": ["C1", "C3", "Ci", "D3", "C3i", "D3d"],
        "composition_series": [
            ["D3d", "D3", "C3", "C1"],
            ["D3d", "C3i", "C3", "C1"],
        ],
        "display_name": "D₃d",
        "description": "3回回転＋2回回転＋斜面",
    },
    "D3h": {
        "name": "D3h", "order": 12, "system": "hexagonal",
        "operations": ["E", "C3", "C3^2", "C2a", "C2b", "C2c", "σh", "σv", "σv2", "σv3", "S4", "S4^3"],
        "normal_subgroups": ["C1", "C3", "Cs", "C3v", "D3", "D3h"],
        "composition_series": [
            ["D3h", "C3v", "C3", "C1"],
            ["D3h", "D3", "C3", "C1"],
        ],
        "display_name": "D₃ₕ",
        "description": "3回回転＋水平鏡映面＋鏡映面",
    },

    # ── Tetragonal ─────────────────────────────────────────────
    "S4": {
        "name": "S4", "order": 4, "system": "tetragonal",
        "operations": ["E", "C2", "S4", "S4^3"],
        "normal_subgroups": ["C1", "C2", "S4"],
        "composition_series": [["S4", "C2", "C1"]],
        "display_name": "S₄",
        "description": "4回回反軸",
    },
    "C4": {
        "name": "C4", "order": 4, "system": "tetragonal",
        "operations": ["E", "C2", "C4", "C4^3"],
        "normal_subgroups": ["C1", "C2", "C4"],
        "composition_series": [["C4", "C2", "C1"]],
        "display_name": "C₄",
        "description": "4回回転軸",
    },
    "C4h": {
        "name": "C4h", "order": 8, "system": "tetragonal",
        "operations": ["E", "C2", "C4", "C4^3", "i", "σh", "S4", "S4^3"],
        "normal_subgroups": ["C1", "C2", "Ci", "Cs", "C4", "S4", "C2h", "C4h"],
        "composition_series": [
            ["C4h", "C4", "C2", "C1"],
            ["C4h", "S4", "C2", "C1"],
            ["C4h", "C2h", "C2", "C1"],
        ],
        "display_name": "C₄ₕ",
        "description": "4回回転軸＋水平鏡映面",
    },
    "C4v": {
        "name": "C4v", "order": 8, "system": "tetragonal",
        "operations": ["E", "C2", "C4", "C4^3", "σv", "σv'", "σd", "σd'"],
        "normal_subgroups": ["C1", "C2", "C4", "C2v", "C4v"],
        "composition_series": [
            ["C4v", "C4", "C2", "C1"],
            ["C4v", "C2v", "C2", "C1"],
        ],
        "display_name": "C₄ᵥ",
        "description": "4回回転軸＋4つの鏡映面",
    },
    "D4": {
        "name": "D4", "order": 8, "system": "tetragonal",
        "operations": ["E", "C2", "C4", "C4^3", "C2x", "C2y", "C2'", "C2''"],
        "normal_subgroups": ["C1", "C2", "C4", "D2", "D4"],
        "composition_series": [
            ["D4", "C4", "C2", "C1"],
            ["D4", "D2", "C2", "C1"],
        ],
        "display_name": "D₄",
        "description": "4回回転軸＋4つの2回回転軸",
    },
    "D4h": {
        "name": "D4h", "order": 16, "system": "tetragonal",
        "operations": [
            "E", "C2", "C4", "C4^3", "C2x", "C2y", "C2'", "C2''",
            "i", "σh", "S4", "S4^3", "σv", "σv'", "σd", "σd'",
        ],
        "normal_subgroups": [
            "C1", "C2", "Ci", "Cs", "C4", "S4", "C2h", "C2v", "D2", "C4h", "C4v", "D4", "D2h", "D4h",
        ],
        "composition_series": [
            ["D4h", "D4", "C4", "C2", "C1"],
            ["D4h", "D2h", "D2", "C2", "C1"],
        ],
        "display_name": "D₄ₕ",
        "description": "4/mmm",
    },

    # ── Hexagonal ─────────────────────────────────────────────
    "C6": {
        "name": "C6", "order": 6, "system": "hexagonal",
        "operations": ["E", "C2", "C3", "C3^2", "C6", "C6^5"],
        "normal_subgroups": ["C1", "C2", "C3", "C6"],
        "composition_series": [
            ["C6", "C3", "C1"],
            ["C6", "C2", "C1"],
        ],
        "display_name": "C₆",
        "description": "6回回転軸",
    },
    "C6h": {
        "name": "C6h", "order": 12, "system": "hexagonal",
        "operations": ["E", "C2", "C3", "C3^2", "C6", "C6^5", "i", "σh", "S6", "S6^5", "S4", "S4^3"],
        "normal_subgroups": ["C1", "C2", "C3", "Ci", "Cs", "C6", "C2h", "C3i", "C6h"],
        "composition_series": [
            ["C6h", "C6", "C3", "C1"],
            ["C6h", "C3i", "C3", "C1"],
            ["C6h", "C2h", "C2", "C1"],
        ],
        "display_name": "C₆ₕ",
        "description": "6/m",
    },
    "C6v": {
        "name": "C6v", "order": 12, "system": "hexagonal",
        "operations": ["E", "C2", "C3", "C3^2", "C6", "C6^5",
                       "σv", "σv'", "σv2", "σv3", "σd", "σd'"],
        "normal_subgroups": ["C1", "C2", "C3", "C3v", "C6", "C6v"],
        "composition_series": [
            ["C6v", "C6", "C3", "C1"],
            ["C6v", "C3v", "C3", "C1"],
        ],
        "display_name": "C₆ᵥ",
        "description": "6mm",
    },
    "D6": {
        "name": "D6", "order": 12, "system": "hexagonal",
        "operations": ["E", "C2", "C3", "C3^2", "C6", "C6^5",
                       "C2x", "C2y", "C2a", "C2b", "C2c", "C2(z)"],
        "normal_subgroups": ["C1", "C2", "C3", "D3", "C6", "D6"],
        "composition_series": [
            ["D6", "C6", "C3", "C1"],
            ["D6", "D3", "C3", "C1"],
        ],
        "display_name": "D₆",
        "description": "622",
    },
    "D6h": {
        "name": "D6h", "order": 24, "system": "hexagonal",
        "operations": [
            "E", "C2", "C3", "C3^2", "C6", "C6^5",
            "C2x", "C2y", "C2a", "C2b", "C2c", "C2(z)",
            "i", "σh", "S6", "S6^5", "S4", "S4^3",
            "σv", "σv'", "σv2", "σv3", "σd", "σd'",
        ],
        "normal_subgroups": [
            "C1", "C2", "C3", "Ci", "Cs", "C6", "C2h", "C3i", "C3v", "D3", "D3h", "C6h", "C6v", "D6", "D6h",
        ],
        "composition_series": [
            ["D6h", "D6", "C6", "C3", "C1"],
            ["D6h", "D3h", "D3", "C3", "C1"],
        ],
        "display_name": "D₆ₕ",
        "description": "6/mmm",
    },

    # ── Cubic ─────────────────────────────────────────────────
    "T": {
        "name": "T", "order": 12, "system": "cubic",
        "operations": [
            "E", "C2(x)", "C2(y)", "C2(z)",
            "C3(111)", "C3^2(111)",
            "C3(1-1-1)", "C3^2(1-1-1)",
            "C3(-11-1)", "C3^2(-11-1)",
            "C3(-1-11)", "C3^2(-1-11)",
        ],
        "normal_subgroups": ["C1", "D2", "T"],
        "composition_series": [["T", "D2", "C2", "C1"]],
        "display_name": "T",
        "description": "四面体群の回転部分",
    },
    "Td": {
        "name": "Td", "order": 24, "system": "cubic",
        "operations": [
            "E", "C2(x)", "C2(y)", "C2(z)",
            "C3(111)", "C3^2(111)",
            "C3(1-1-1)", "C3^2(1-1-1)",
            "C3(-11-1)", "C3^2(-11-1)",
            "C3(-1-11)", "C3^2(-1-11)",
            "S4x", "S4x^3", "S4y", "S4y^3", "S4", "S4^3",
            "σd1", "σd2", "σd3", "σd4", "σd5", "σd6",
        ],
        "normal_subgroups": ["C1", "D2", "T", "Td"],
        "composition_series": [["Td", "T", "D2", "C2", "C1"]],
        "display_name": "Tᵈ",
        "description": "四面体対称群（-43m）",
    },
    "Th": {
        "name": "Th", "order": 24, "system": "cubic",
        "operations": [
            "E", "C2(x)", "C2(y)", "C2(z)",
            "C3(111)", "C3^2(111)",
            "C3(1-1-1)", "C3^2(1-1-1)",
            "C3(-11-1)", "C3^2(-11-1)",
            "C3(-1-11)", "C3^2(-1-11)",
            "i", "σxz", "σyz", "σxy",
            "S6", "S6^5",
        ] + [  # i * C3 = S6
        ],
        "normal_subgroups": ["C1", "D2", "Ci", "T", "Th"],
        "composition_series": [
            ["Th", "T", "D2", "C2", "C1"],
            ["Th", "Ci", "C1"],
        ],
        "display_name": "Tₕ",
        "description": "m3",
    },
    "O": {
        "name": "O", "order": 24, "system": "cubic",
        "operations": [
            "E", "C2(x)", "C2(y)", "C2(z)",
            "C3(111)", "C3^2(111)",
            "C3(1-1-1)", "C3^2(1-1-1)",
            "C3(-11-1)", "C3^2(-11-1)",
            "C3(-1-11)", "C3^2(-1-11)",
            "C4x", "C4x^3", "C4y", "C4y^3", "C4", "C4^3",
            "C2'", "C2''", "C2(xz)", "C2(yz)", "C2(x-z)", "C2(y-z)",
        ],
        "normal_subgroups": ["C1", "D2", "T", "O"],
        "composition_series": [["O", "T", "D2", "C2", "C1"]],
        "display_name": "O",
        "description": "八面体群の回転部分",
    },
    "Oh": {
        "name": "Oh", "order": 48, "system": "cubic",
        "operations": [
            "E", "C2(x)", "C2(y)", "C2(z)",
            "C3(111)", "C3^2(111)",
            "C3(1-1-1)", "C3^2(1-1-1)",
            "C3(-11-1)", "C3^2(-11-1)",
            "C3(-1-11)", "C3^2(-1-11)",
            "C4x", "C4x^3", "C4y", "C4y^3", "C4", "C4^3",
            "C2'", "C2''", "C2(xz)", "C2(yz)", "C2(x-z)", "C2(y-z)",
            "i", "σxz", "σyz", "σxy",
            "S4x", "S4x^3", "S4y", "S4y^3", "S4", "S4^3",
            "S6", "S6^5",
            "σd1", "σd2", "σd3", "σd4", "σd5", "σd6",
        ],
        "normal_subgroups": ["C1", "D2", "Ci", "T", "Th", "O", "Oh"],
        "composition_series": [
            ["Oh", "O", "T", "D2", "C2", "C1"],
            ["Oh", "Th", "T", "D2", "C2", "C1"],
        ],
        "display_name": "Oₕ",
        "description": "m3m（最高対称群）",
    },
}


def get_group(name: str) -> dict:
    """点群名から定義を取得する"""
    if name not in POINT_GROUPS:
        raise ValueError(f"Unknown point group: {name}")
    return POINT_GROUPS[name]


def list_groups() -> list[str]:
    """実装済み点群名の一覧を返す"""
    return list(POINT_GROUPS.keys())
