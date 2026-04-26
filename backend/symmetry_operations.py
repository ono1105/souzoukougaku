"""
Symmetry operation definitions in Seitz notation: (R | t)
R: 3x3 rotation matrix, t: 3D translation vector (always zero for point groups)

Designed to be forward-compatible with space groups (Phase 10+).
"""

import numpy as np
from typing import Literal

OperationType = Literal["identity", "rotation", "mirror", "inversion", "rotoinversion", "screw", "glide"]


def make_operation(
    rotation: list[list[int]],
    op_type: OperationType,
    order: int = 1,
    axis: list[float] | None = None,
    translation: list[float] | None = None,
    label: str = "",
) -> dict:
    return {
        "rotation": rotation,
        "translation": translation or [0, 0, 0],
        "type": op_type,
        "order": order,
        "axis": axis or [0, 0, 1],
        "label": label,
    }


# ── 基本対称操作 ──────────────────────────────────────────────

E = make_operation([[1,0,0],[0,1,0],[0,0,1]], "identity", 1, [0,0,1], label="E")

# 回転軸 z
C2z = make_operation([[-1,0,0],[0,-1,0],[0,0,1]], "rotation", 2, [0,0,1], label="C2")
C3z = make_operation([[-1,-1,0],[1,0,0],[0,0,1]], "rotation", 3, [0,0,1], label="C3")
# C3z = (1/2)[[−1,−√3,0],[√3,−1,0],[0,0,2]] — 整数近似用にフラグ管理
C3z_exact = {
    "rotation": [[-0.5, -0.8660254, 0],[0.8660254, -0.5, 0],[0, 0, 1]],
    "translation": [0,0,0], "type": "rotation", "order": 3, "axis": [0,0,1], "label": "C3",
}
C3z_inv_exact = {
    "rotation": [[-0.5, 0.8660254, 0],[-0.8660254, -0.5, 0],[0, 0, 1]],
    "translation": [0,0,0], "type": "rotation", "order": 3, "axis": [0,0,1], "label": "C3^2",
}
C4z = make_operation([[0,-1,0],[1,0,0],[0,0,1]], "rotation", 4, [0,0,1], label="C4")
C4z_inv = make_operation([[0,1,0],[-1,0,0],[0,0,1]], "rotation", 4, [0,0,1], label="C4^3")
C6z = {
    "rotation": [[0.5, -0.8660254, 0],[0.8660254, 0.5, 0],[0,0,1]],
    "translation": [0,0,0], "type": "rotation", "order": 6, "axis": [0,0,1], "label": "C6",
}
C6z_inv = {
    "rotation": [[0.5, 0.8660254, 0],[-0.8660254, 0.5, 0],[0,0,1]],
    "translation": [0,0,0], "type": "rotation", "order": 6, "axis": [0,0,1], "label": "C6^5",
}

# 回転軸 x, y（D群用）
C2x = make_operation([[1,0,0],[0,-1,0],[0,0,-1]], "rotation", 2, [1,0,0], label="C2x")
C2y = make_operation([[-1,0,0],[0,1,0],[0,0,-1]], "rotation", 2, [0,1,0], label="C2y")

# D3 用 x軸方向C2 と 対角C2
C2x_d3 = make_operation([[1,0,0],[0,-1,0],[0,0,-1]], "rotation", 2, [1,0,0], label="C2a")
C2_d3b = {
    "rotation": [[-0.5, 0.8660254, 0],[0.8660254, 0.5, 0],[0,0,-1]],
    "translation": [0,0,0], "type": "rotation", "order": 2, "axis": [0.8660254,0.5,0], "label": "C2b",
}
C2_d3c = {
    "rotation": [[-0.5, -0.8660254, 0],[-0.8660254, 0.5, 0],[0,0,-1]],
    "translation": [0,0,0], "type": "rotation", "order": 2, "axis": [-0.8660254,0.5,0], "label": "C2c",
}

# D4/D2 用 C2 (xy対角)
C2_xy = make_operation([[0,1,0],[1,0,0],[0,0,-1]], "rotation", 2, [1,1,0], label="C2'")
C2_xy_neg = make_operation([[0,-1,0],[-1,0,0],[0,0,-1]], "rotation", 2, [1,-1,0], label="C2''")

# 反転
i_op = make_operation([[-1,0,0],[0,-1,0],[0,0,-1]], "inversion", 1, [0,0,0], label="i")

# 鏡映面
sigma_h = make_operation([[1,0,0],[0,1,0],[0,0,-1]], "mirror", 1, [0,0,1], label="σh")
sigma_v = make_operation([[-1,0,0],[0,1,0],[0,0,1]], "mirror", 1, [1,0,0], label="σv")
sigma_v2 = make_operation([[1,0,0],[0,-1,0],[0,0,1]], "mirror", 1, [0,1,0], label="σv'")
sigma_d = make_operation([[0,1,0],[1,0,0],[0,0,1]], "mirror", 1, [1,1,0], label="σd")
sigma_d2 = make_operation([[0,-1,0],[-1,0,0],[0,0,1]], "mirror", 1, [1,-1,0], label="σd'")

# D3v用 σv
sigma_v_d3b = {
    "rotation": [[0.5, 0.8660254, 0],[0.8660254, -0.5, 0],[0,0,1]],
    "translation": [0,0,0], "type": "mirror", "order": 1, "axis": [0.8660254, 0.5, 0], "label": "σv2",
}
sigma_v_d3c = {
    "rotation": [[0.5, -0.8660254, 0],[-0.8660254, -0.5, 0],[0,0,1]],
    "translation": [0,0,0], "type": "mirror", "order": 1, "axis": [-0.8660254, 0.5, 0], "label": "σv3",
}

# 回反軸
S4z = make_operation([[0,1,0],[-1,0,0],[0,0,-1]], "rotoinversion", 4, [0,0,1], label="S4")
S4z_inv = make_operation([[0,-1,0],[1,0,0],[0,0,-1]], "rotoinversion", 4, [0,0,1], label="S4^3")
S6z = {
    "rotation": [[-0.5, 0.8660254, 0],[-0.8660254, -0.5, 0],[0,0,-1]],
    "translation": [0,0,0], "type": "rotoinversion", "order": 6, "axis": [0,0,1], "label": "S6",
}
S6z_inv = {
    "rotation": [[-0.5, -0.8660254, 0],[0.8660254, -0.5, 0],[0,0,-1]],
    "translation": [0,0,0], "type": "rotoinversion", "order": 6, "axis": [0,0,1], "label": "S6^5",
}

# Td / Oh 用 (体対角C3)
C3_111 = {
    "rotation": [[0,0,1],[1,0,0],[0,1,0]],
    "translation": [0,0,0], "type": "rotation", "order": 3, "axis": [1,1,1], "label": "C3(111)",
}
C3_111_inv = {
    "rotation": [[0,1,0],[0,0,1],[1,0,0]],
    "translation": [0,0,0], "type": "rotation", "order": 3, "axis": [1,1,1], "label": "C3^2(111)",
}
C3_1m1m = {
    "rotation": [[0,0,-1],[1,0,0],[0,-1,0]],
    "translation": [0,0,0], "type": "rotation", "order": 3, "axis": [1,-1,-1], "label": "C3(1-1-1)",
}
C3_1m1m_inv = {
    "rotation": [[0,1,0],[0,0,-1],[-1,0,0]],
    "translation": [0,0,0], "type": "rotation", "order": 3, "axis": [1,-1,-1], "label": "C3^2(1-1-1)",
}
C3_m11m = {
    "rotation": [[0,0,1],[-1,0,0],[0,-1,0]],
    "translation": [0,0,0], "type": "rotation", "order": 3, "axis": [-1,1,-1], "label": "C3(-11-1)",
}
C3_m11m_inv = {
    "rotation": [[0,-1,0],[0,0,1],[-1,0,0]],
    "translation": [0,0,0], "type": "rotation", "order": 3, "axis": [-1,1,-1], "label": "C3^2(-11-1)",
}
C3_mm1 = {
    "rotation": [[0,0,-1],[-1,0,0],[0,1,0]],
    "translation": [0,0,0], "type": "rotation", "order": 3, "axis": [-1,-1,1], "label": "C3(-1-11)",
}
C3_mm1_inv = {
    "rotation": [[0,-1,0],[0,0,-1],[1,0,0]],
    "translation": [0,0,0], "type": "rotation", "order": 3, "axis": [-1,-1,1], "label": "C3^2(-1-11)",
}

C2_T_x = make_operation([[1,0,0],[0,-1,0],[0,0,-1]], "rotation", 2, [1,0,0], label="C2(x)")
C2_T_y = make_operation([[-1,0,0],[0,1,0],[0,0,-1]], "rotation", 2, [0,1,0], label="C2(y)")
C2_T_z = make_operation([[-1,0,0],[0,-1,0],[0,0,1]], "rotation", 2, [0,0,1], label="C2(z)")

# Oh用 C4
C4x = make_operation([[1,0,0],[0,0,-1],[0,1,0]], "rotation", 4, [1,0,0], label="C4x")
C4x_inv = make_operation([[1,0,0],[0,0,1],[0,-1,0]], "rotation", 4, [1,0,0], label="C4x^3")
C4y = make_operation([[0,0,1],[0,1,0],[-1,0,0]], "rotation", 4, [0,1,0], label="C4y")
C4y_inv = make_operation([[0,0,-1],[0,1,0],[1,0,0]], "rotation", 4, [0,1,0], label="C4y^3")

# Oh用 C2 (面対角)
C2_Oh_xz = make_operation([[0,0,1],[0,-1,0],[1,0,0]], "rotation", 2, [1,0,1], label="C2(xz)")
C2_Oh_yz = make_operation([[-1,0,0],[0,0,1],[0,1,0]], "rotation", 2, [0,1,1], label="C2(yz)")
C2_Oh_xz_n = make_operation([[0,0,-1],[0,-1,0],[-1,0,0]], "rotation", 2, [1,0,-1], label="C2(x-z)")
C2_Oh_yz_n = make_operation([[-1,0,0],[0,0,-1],[0,-1,0]], "rotation", 2, [0,1,-1], label="C2(y-z)")
C2_Oh_xy_n = make_operation([[0,-1,0],[-1,0,0],[0,0,-1]], "rotation", 2, [1,-1,0], label="C2(x-y)")

# Oh 鏡映面
sigma_xz = make_operation([[1,0,0],[0,-1,0],[0,0,1]], "mirror", 1, [0,1,0], label="σxz")
sigma_yz = make_operation([[-1,0,0],[0,1,0],[0,0,1]], "mirror", 1, [1,0,0], label="σyz")
sigma_xy = make_operation([[1,0,0],[0,1,0],[0,0,-1]], "mirror", 1, [0,0,1], label="σxy")
sigma_Oh_d1 = make_operation([[0,1,0],[1,0,0],[0,0,-1]], "mirror", 1, [1,-1,0], label="σd1")
sigma_Oh_d2 = make_operation([[0,-1,0],[-1,0,0],[0,0,-1]], "mirror", 1, [1,1,0], label="σd2")
sigma_Oh_d3 = make_operation([[0,0,1],[0,-1,0],[1,0,0]], "mirror", 1, [1,0,-1], label="σd3")
sigma_Oh_d4 = make_operation([[0,0,-1],[0,-1,0],[-1,0,0]], "mirror", 1, [1,0,1], label="σd4")
sigma_Oh_d5 = make_operation([[-1,0,0],[0,0,1],[0,1,0]], "mirror", 1, [0,1,-1], label="σd5")
sigma_Oh_d6 = make_operation([[-1,0,0],[0,0,-1],[0,-1,0]], "mirror", 1, [0,1,1], label="σd6")

# Td 用 S4
S4x = make_operation([[1,0,0],[0,0,1],[0,-1,0]], "rotoinversion", 4, [1,0,0], label="S4x")
S4x_inv = make_operation([[1,0,0],[0,0,-1],[0,1,0]], "rotoinversion", 4, [1,0,0], label="S4x^3")
S4y = make_operation([[0,0,-1],[0,1,0],[1,0,0]], "rotoinversion", 4, [0,1,0], label="S4y")
S4y_inv = make_operation([[0,0,1],[0,1,0],[-1,0,0]], "rotoinversion", 4, [0,1,0], label="S4y^3")
