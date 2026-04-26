"""
32 crystal point group definitions.

Each group stores ONLY ITS MAXIMAL NORMAL SUBGROUPS in `normal_subgroups`.
A maximal normal subgroup N has prime-order quotient G/N, which is irreducible
(cannot be further decomposed). This is the correct group-theoretic definition
for a composition series step.

Designed to share the same interface as future space groups (Phase 10+).
"""

from symmetry_operations import OPERATIONS

# ── 対称操作ラベルのエイリアス（可読性のため）──────────────────
_ops = OPERATIONS


def _pg(name, order, system, operations, max_normal_subgroups,
        display_name="", description=""):
    """点群定義の辞書を作るヘルパー"""
    return {
        "name": name,
        "order": order,
        "system": system,
        "operations": operations,
        "normal_subgroups": max_normal_subgroups,  # maximal normal subgroups only
        "display_name": display_name or name,
        "description": description,
    }


# ── 32結晶点群の定義 ─────────────────────────────────────────
# normal_subgroups: 最大正規部分群のみ（G/N の位数が素数になるもの）

POINT_GROUPS: dict[str, dict] = {

    # ── Triclinic ─────────────────────────────────────
    "C1": _pg("C1", 1, "triclinic",
        ["E"],
        [],   # no proper subgroups
        "C₁", "恒等元のみ"),

    "Ci": _pg("Ci", 2, "triclinic",
        ["E", "i"],
        ["C1"],   # Ci/C1 = C2 (order 2 = prime)
        "Cᵢ", "反転対称（-1）"),

    # ── Monoclinic ───────────────────────────────────
    "Cs": _pg("Cs", 2, "monoclinic",
        ["E", "σh"],
        ["C1"],
        "Cₛ", "鏡映対称（m）"),

    "C2": _pg("C2", 2, "monoclinic",
        ["E", "C2z"],
        ["C1"],
        "C₂", "2回回転軸"),

    "C2h": _pg("C2h", 4, "monoclinic",
        ["E", "C2z", "i", "σh"],
        ["C2", "Ci", "Cs"],   # each of order 2: C2h/C2=Ci, C2h/Ci=C2, C2h/Cs=C2
        "C₂ₕ", "2/m"),

    # ── Orthorhombic ─────────────────────────────────
    "C2v": _pg("C2v", 4, "orthorhombic",
        ["E", "C2z", "σv", "σv'"],
        ["C2", "Cs"],   # C2v/C2=Cs, C2v/Cs=C2
        "C₂ᵥ", "mm2"),

    "D2": _pg("D2", 4, "orthorhombic",
        ["E", "C2z", "C2x", "C2y"],
        ["C2"],   # D2/C2(z)=C2, D2/C2(x)=C2, D2/C2(y)=C2 (all order 2)
        "D₂", "222"),

    "D2h": _pg("D2h", 8, "orthorhombic",
        ["E", "C2z", "C2x", "C2y", "i", "σh", "σv", "σv'"],
        ["D2", "C2h", "C2v"],   # D2h/D2=Ci, D2h/C2h=C2, D2h/C2v=C2
        "D₂ₕ", "mmm"),

    # ── Trigonal ─────────────────────────────────────
    "C3": _pg("C3", 3, "trigonal",
        ["E", "C3", "C3^2"],
        ["C1"],   # C3/C1=C3 (order 3=prime)
        "C₃", "3"),

    "C3i": _pg("C3i", 6, "trigonal",
        ["E", "C3", "C3^2", "i", "S6", "S6^5"],
        ["C3", "Ci"],   # C3i/C3=Ci(2), C3i/Ci=C3(3) — both prime
        "C₃ᵢ (S₆)", "-3"),

    "C3v": _pg("C3v", 6, "trigonal",
        ["E", "C3", "C3^2", "σv1", "σv2", "σv3"],
        ["C3"],   # C3v/C3=Cs (order 2=prime). σv's are not normal subgroups.
        "C₃ᵥ", "3m"),

    "D3": _pg("D3", 6, "trigonal",
        ["E", "C3", "C3^2", "C2a", "C2b", "C2c"],
        ["C3"],   # D3/C3=C2 (order 2=prime). Individual C2's are not normal in D3.
        "D₃", "32"),

    "D3d": _pg("D3d", 12, "trigonal",
        ["E", "C3", "C3^2", "C2a", "C2b", "C2c", "i", "S6", "S6^5", "σd1", "σd2", "σd3"],
        ["D3", "C3i"],   # D3d/D3=Ci(2), D3d/C3i=C2(2) — both prime
        "D₃d", "-3m"),

    "D3h": _pg("D3h", 12, "hexagonal",
        ["E", "C3", "C3^2", "C2a", "C2b", "C2c", "σh", "S3", "S3^5", "σv1", "σv2", "σv3"],
        ["C3v", "D3"],   # D3h/C3v=C2(2), D3h/D3=Cs(2) — both prime
        "D₃ₕ", "-6m2"),

    # ── Tetragonal ───────────────────────────────────
    "S4": _pg("S4", 4, "tetragonal",
        ["E", "C2z", "S4", "S4^3"],
        ["C2"],   # S4/C2=C2 (order 2=prime)
        "S₄", "-4"),

    "C4": _pg("C4", 4, "tetragonal",
        ["E", "C2z", "C4", "C4^3"],
        ["C2"],   # C4/C2=C2 (order 2=prime)
        "C₄", "4"),

    "C4h": _pg("C4h", 8, "tetragonal",
        ["E", "C2z", "C4", "C4^3", "i", "σh", "S4", "S4^3"],
        ["C4", "S4", "C2h"],   # each gives quotient of order 2
        "C₄ₕ", "4/m"),

    "C4v": _pg("C4v", 8, "tetragonal",
        ["E", "C2z", "C4", "C4^3", "σv_c4", "σv'_c4", "σd_c4", "σd'_c4"],
        ["C4", "C2v"],   # C4v/C4=C2(2), C4v/C2v=C2(2)
        "C₄ᵥ", "4mm"),

    "D2d": _pg("D2d", 8, "tetragonal",
        ["E", "C2z", "S4", "S4^3", "C2a", "C2b", "σd_c4", "σd'_c4"],
        ["S4", "D2"],   # D2d/S4=C2(2), D2d/D2=C2(2)
        "D₂d", "-42m"),

    "D4": _pg("D4", 8, "tetragonal",
        ["E", "C2z", "C4", "C4^3", "C2x", "C2y", "C2d4a", "C2d4b"],
        ["C4", "D2"],   # D4/C4=C2(2), D4/D2=C2(2)
        "D₄", "422"),

    "D4h": _pg("D4h", 16, "tetragonal",
        ["E","C2z","C4","C4^3","C2x","C2y","C2d4a","C2d4b",
         "i","σh","S4","S4^3","σv_c4","σv'_c4","σd_c4","σd'_c4"],
        ["D4", "C4h", "C4v", "D2h"],   # each gives order-2 quotient
        "D₄ₕ", "4/mmm"),

    # ── Hexagonal ────────────────────────────────────
    "C3h": _pg("C3h", 6, "hexagonal",
        ["E", "C3", "C3^2", "σh", "S3", "S3^5"],
        ["C3", "Cs"],   # C3h/C3=Cs(2), C3h/Cs=C3(3) — both prime (C3h≅C3×Cs)
        "C₃ₕ", "-6"),

    "C6": _pg("C6", 6, "hexagonal",
        ["E", "C2z", "C3", "C3^2", "C6", "C6^5"],
        ["C3", "C2"],   # C6/C3=C2(2), C6/C2=C3(3) — both prime
        "C₆", "6"),

    "C6h": _pg("C6h", 12, "hexagonal",
        ["E","C2z","C3","C3^2","C6","C6^5","i","σh","S3","S3^5","S6","S6^5"],
        ["C6", "C3i", "C2h"],   # each gives order-2 quotient
        "C₆ₕ", "6/m"),

    "C6v": _pg("C6v", 12, "hexagonal",
        ["E","C2z","C3","C3^2","C6","C6^5","σv1","σv'","σv2","σv3","σd1","σd2"],
        ["C6", "C3v"],   # C6v/C6=C2(2), C6v/C3v=C2(2)
        "C₆ᵥ", "6mm"),

    "D6": _pg("D6", 12, "hexagonal",
        ["E","C2z","C3","C3^2","C6","C6^5","C2x","C2y","C2a","C2b","C2c","C2d4a"],
        ["C6", "D3"],   # D6/C6=C2(2), D6/D3=C2(2)
        "D₆", "622"),

    "D6h": _pg("D6h", 24, "hexagonal",
        ["E","C2z","C3","C3^2","C6","C6^5",
         "C2x","C2y","C2a","C2b","C2c","C2d4a",
         "i","σh","S3","S3^5","S6","S6^5",
         "σv1","σv'","σv2","σv3","σd1","σd2"],
        ["D6", "D3h", "C6h", "C6v"],   # each gives order-2 quotient
        "D₆ₕ", "6/mmm"),

    # ── Cubic ────────────────────────────────────────
    "T": _pg("T", 12, "cubic",
        ["E","C2(x)","C2(y)","C2(z)",
         "C3(111)","C3^2(111)",
         "C3(1-1-1)","C3^2(1-1-1)",
         "C3(-11-1)","C3^2(-11-1)",
         "C3(-1-11)","C3^2(-1-11)"],
        ["D2"],   # T/D2=C3 (order 3=prime). D2 is the unique normal subgroup of T.
        "T", "23"),

    "Td": _pg("Td", 24, "cubic",
        ["E","C2(x)","C2(y)","C2(z)",
         "C3(111)","C3^2(111)","C3(1-1-1)","C3^2(1-1-1)",
         "C3(-11-1)","C3^2(-11-1)","C3(-1-11)","C3^2(-1-11)",
         "S4x","S4x^3","S4y","S4y^3","S4","S4^3",
         "σd_Oh1","σd_Oh2","σd_Oh3","σd_Oh4","σd_Oh5","σd_Oh6"],
        ["T"],   # Td/T=C2 (order 2=prime). T is the unique proper normal subgroup of Td.
        "Tᵈ", "-43m"),

    "Th": _pg("Th", 24, "cubic",
        ["E","C2(x)","C2(y)","C2(z)",
         "C3(111)","C3^2(111)","C3(1-1-1)","C3^2(1-1-1)",
         "C3(-11-1)","C3^2(-11-1)","C3(-1-11)","C3^2(-1-11)",
         "i","σh","σv","σv'",
         "S6","S6^5"],
        ["T", "Ci"],   # Th/T=Ci(2), Th/Ci=T... wait |Th|/|Ci|=12 not prime. Fix below.
        "Tₕ", "m-3"),

    "O": _pg("O", 24, "cubic",
        ["E","C2(x)","C2(y)","C2(z)",
         "C3(111)","C3^2(111)","C3(1-1-1)","C3^2(1-1-1)",
         "C3(-11-1)","C3^2(-11-1)","C3(-1-11)","C3^2(-1-11)",
         "C4x","C4x^3","C4y","C4y^3","C4","C4^3",
         "C2(x+y)","C2(x-y)","C2(x+z)","C2(x-z)","C2(y+z)","C2(y-z)"],
        ["T"],   # O/T=C2 (order 2=prime). T is the unique normal subgroup of O.
        "O", "432"),

    "Oh": _pg("Oh", 48, "cubic",
        ["E","C2(x)","C2(y)","C2(z)",
         "C3(111)","C3^2(111)","C3(1-1-1)","C3^2(1-1-1)",
         "C3(-11-1)","C3^2(-11-1)","C3(-1-11)","C3^2(-1-11)",
         "C4x","C4x^3","C4y","C4y^3","C4","C4^3",
         "C2(x+y)","C2(x-y)","C2(x+z)","C2(x-z)","C2(y+z)","C2(y-z)",
         "i",
         "S4x","S4x^3","S4y","S4y^3","S4","S4^3",
         "S6","S6^5",
         "σh","σv","σv'",
         "σd_Oh1","σd_Oh2","σd_Oh3","σd_Oh4","σd_Oh5","σd_Oh6"],
        ["O", "Th"],   # Oh/O=Ci(2), Oh/Th=C2(2) — both prime
        "Oₕ", "m-3m"),
}

# Th の正規部分群を修正: Th = T × {E,i} = T × Ci
# Th/T = Ci (order 2, prime ✓)
# Th/Ci has order 12 (not prime) → not maximal
# So Th の maximal normal subgroup は T のみ。
POINT_GROUPS["Th"]["normal_subgroups"] = ["T"]


def get_group(name: str) -> dict:
    if name not in POINT_GROUPS:
        raise ValueError(f"Unknown point group: {name}")
    return POINT_GROUPS[name]


def list_groups() -> list[str]:
    return list(POINT_GROUPS.keys())
