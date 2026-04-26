"""
Symmetry operation definitions in Seitz notation: (R | t)
R: 3x3 rotation matrix, t: 3D translation vector (always zero for point groups)

All rotation matrices use right-hand counterclockwise convention.
Designed to be forward-compatible with space groups (Phase 10+).

Verification convention:
  C_n = rotation by (2π/n) counterclockwise around the stated axis
  σ(plane) = reflection through the plane (Householder: I - 2*n*n^T where n is plane normal)
  S_n = C_n · σ_h (Schoenflies: rotate by 2π/n then reflect through xy-plane)
  i = inversion = -I
"""

from typing import Literal

OperationType = Literal["identity", "rotation", "mirror", "inversion", "rotoinversion", "screw", "glide"]


def _op(rotation, op_type: OperationType, order: int = 1,
        axis=None, translation=None, label: str = "") -> dict:
    return {
        "rotation": rotation,
        "translation": translation or [0.0, 0.0, 0.0],
        "type": op_type,
        "order": order,
        "axis": axis or [0.0, 0.0, 1.0],
        "label": label,
    }


# ── 恒等操作 ─────────────────────────────────────────────────
E = _op([[1,0,0],[0,1,0],[0,0,1]], "identity", 1, [0,0,1], label="E")

# ── 2回回転軸 ─────────────────────────────────────────────────
C2z = _op([[-1,0,0],[0,-1,0],[0,0,1]],   "rotation", 2, [0,0,1], label="C2z")
C2x = _op([[1,0,0],[0,-1,0],[0,0,-1]],   "rotation", 2, [1,0,0], label="C2x")
C2y = _op([[-1,0,0],[0,1,0],[0,0,-1]],   "rotation", 2, [0,1,0], label="C2y")
# D3 用: C2 at 0°, 120°, 240° from x in xy-plane
C2_d3a = _op([[1,0,0],[0,-1,0],[0,0,-1]],                        "rotation", 2, [1,0,0],              label="C2a")
C2_d3b = _op([[-0.5,-0.8660254,0],[-0.8660254,0.5,0],[0,0,-1]],  "rotation", 2, [-0.5,0.8660254,0],   label="C2b")
C2_d3c = _op([[-0.5,0.8660254,0],[0.8660254,0.5,0],[0,0,-1]],    "rotation", 2, [-0.5,-0.8660254,0],  label="C2c")
# D4 用: 追加の C2 (対角)
C2_d4a = _op([[0,1,0],[1,0,0],[0,0,-1]],  "rotation", 2, [1,1,0],  label="C2d4a")   # at 45°
C2_d4b = _op([[0,-1,0],[-1,0,0],[0,0,-1]],"rotation", 2, [1,-1,0], label="C2d4b")  # at 135°

# ── 3回回転軸 (z) ──────────────────────────────────────────────
# C3: rotate 120° CCW around z
C3z  = _op([[-0.5,-0.8660254,0],[0.8660254,-0.5,0],[0,0,1]], "rotation", 3, [0,0,1], label="C3")
C3z2 = _op([[-0.5,0.8660254,0],[-0.8660254,-0.5,0],[0,0,1]], "rotation", 3, [0,0,1], label="C3^2")

# ── 4回回転軸 (z) ──────────────────────────────────────────────
C4z  = _op([[0,-1,0],[1,0,0],[0,0,1]],  "rotation", 4, [0,0,1], label="C4")
C4z3 = _op([[0,1,0],[-1,0,0],[0,0,1]],  "rotation", 4, [0,0,1], label="C4^3")
C4x  = _op([[1,0,0],[0,0,-1],[0,1,0]],  "rotation", 4, [1,0,0], label="C4x")
C4x3 = _op([[1,0,0],[0,0,1],[0,-1,0]],  "rotation", 4, [1,0,0], label="C4x^3")
C4y  = _op([[0,0,1],[0,1,0],[-1,0,0]],  "rotation", 4, [0,1,0], label="C4y")
C4y3 = _op([[0,0,-1],[0,1,0],[1,0,0]],  "rotation", 4, [0,1,0], label="C4y^3")

# ── 6回回転軸 (z) ──────────────────────────────────────────────
C6z  = _op([[0.5,-0.8660254,0],[0.8660254,0.5,0],[0,0,1]],  "rotation", 6, [0,0,1], label="C6")
C6z5 = _op([[0.5,0.8660254,0],[-0.8660254,0.5,0],[0,0,1]],  "rotation", 6, [0,0,1], label="C6^5")

# ── T/O 群用 体対角C3 ─────────────────────────────────────────
C3_111  = _op([[0,0,1],[1,0,0],[0,1,0]],  "rotation", 3, [1,1,1],    label="C3(111)")
C3_111b = _op([[0,1,0],[0,0,1],[1,0,0]],  "rotation", 3, [1,1,1],    label="C3^2(111)")
C3_p1mm = _op([[0,0,-1],[1,0,0],[0,-1,0]],"rotation", 3, [1,-1,-1],  label="C3(1-1-1)")
C3_p1mb = _op([[0,1,0],[0,0,-1],[-1,0,0]],"rotation", 3, [1,-1,-1],  label="C3^2(1-1-1)")
C3_m1pm = _op([[0,0,1],[-1,0,0],[0,-1,0]],"rotation", 3, [-1,1,-1],  label="C3(-11-1)")
C3_m1pb = _op([[0,-1,0],[0,0,1],[-1,0,0]],"rotation", 3, [-1,1,-1],  label="C3^2(-11-1)")
C3_mm1  = _op([[0,0,-1],[-1,0,0],[0,1,0]],"rotation", 3, [-1,-1,1],  label="C3(-1-11)")
C3_mm1b = _op([[0,-1,0],[0,0,-1],[1,0,0]],"rotation", 3, [-1,-1,1],  label="C3^2(-1-11)")
# T/O 群用 C2 (xyz 軸, 覚えやすいラベル付き)
C2_Tx = _op([[1,0,0],[0,-1,0],[0,0,-1]],  "rotation", 2, [1,0,0], label="C2(x)")
C2_Ty = _op([[-1,0,0],[0,1,0],[0,0,-1]],  "rotation", 2, [0,1,0], label="C2(y)")
C2_Tz = _op([[-1,0,0],[0,-1,0],[0,0,1]],  "rotation", 2, [0,0,1], label="C2(z)")
# O 群用 面対角 C2
C2_Oh_xpy = _op([[0,1,0],[1,0,0],[0,0,-1]],  "rotation", 2, [1,1,0],  label="C2(x+y)")
C2_Oh_xmy = _op([[0,-1,0],[-1,0,0],[0,0,-1]],"rotation", 2, [1,-1,0], label="C2(x-y)")
C2_Oh_xpz = _op([[0,0,1],[0,-1,0],[1,0,0]],  "rotation", 2, [1,0,1],  label="C2(x+z)")
C2_Oh_xmz = _op([[0,0,-1],[0,-1,0],[-1,0,0]],"rotation", 2, [1,0,-1], label="C2(x-z)")
C2_Oh_ypz = _op([[-1,0,0],[0,0,1],[0,1,0]],  "rotation", 2, [0,1,1],  label="C2(y+z)")
C2_Oh_ymz = _op([[-1,0,0],[0,0,-1],[0,-1,0]],"rotation", 2, [0,1,-1], label="C2(y-z)")

# ── 反転 ───────────────────────────────────────────────────────
i_op = _op([[-1,0,0],[0,-1,0],[0,0,-1]], "inversion", 1, [0,0,0], label="i")

# ── 鏡映面 ─────────────────────────────────────────────────────
# 面の法線ベクトルで指定。axis には面の法線を入れる。
sigma_h  = _op([[1,0,0],[0,1,0],[0,0,-1]],  "mirror", 1, [0,0,1], label="σh")   # xy平面
sigma_xz = _op([[1,0,0],[0,-1,0],[0,0,1]],  "mirror", 1, [0,1,0], label="σv")   # xz平面 (法線=y)
sigma_yz = _op([[-1,0,0],[0,1,0],[0,0,1]],  "mirror", 1, [1,0,0], label="σv'")  # yz平面 (法線=x)
# D3v 用 σv: 60°刻みで3枚
# σv at 0° (xz plane): same as sigma_xz = [[1,0,0],[0,-1,0],[0,0,1]]
sigma_v_d3a = _op([[1,0,0],[0,-1,0],[0,0,1]],                        "mirror", 1, [0,1,0],            label="σv1")
sigma_v_d3b = _op([[-0.5,-0.8660254,0],[-0.8660254,0.5,0],[0,0,1]],  "mirror", 1, [0.8660254,-0.5,0], label="σv2")
sigma_v_d3c = _op([[-0.5,0.8660254,0],[0.8660254,0.5,0],[0,0,1]],    "mirror", 1, [0.8660254,0.5,0],  label="σv3")
# D3d 用 σd (45° からD3のC2軸の間)
sigma_d_d3a = _op([[0.5,0.8660254,0],[0.8660254,-0.5,0],[0,0,1]],    "mirror", 1, [-0.8660254,0.5,0], label="σd1")
sigma_d_d3b = _op([[0.5,-0.8660254,0],[-0.8660254,-0.5,0],[0,0,1]],  "mirror", 1, [0.8660254,0.5,0],  label="σd2")
sigma_d_d3c = _op([[-1,0,0],[0,1,0],[0,0,1]],                        "mirror", 1, [1,0,0],            label="σd3")
# D4 / C4v 用 σv, σd
sigma_v_c4a = _op([[1,0,0],[0,-1,0],[0,0,1]],  "mirror", 1, [0,1,0],   label="σv")   # xz
sigma_v_c4b = _op([[-1,0,0],[0,1,0],[0,0,1]],  "mirror", 1, [1,0,0],   label="σv'")  # yz
sigma_d_c4a = _op([[0,1,0],[1,0,0],[0,0,1]],   "mirror", 1, [1,-1,0],  label="σd")   # 45°面
sigma_d_c4b = _op([[0,-1,0],[-1,0,0],[0,0,1]], "mirror", 1, [1,1,0],   label="σd'")  # 135°面
# Oh 用 σd (面対角の鏡映面、法線が[1,1,0]等)
sigma_Oh_d1 = _op([[0,1,0],[1,0,0],[0,0,1]],   "mirror", 1, [1,-1,0],  label="σd(xy)")
sigma_Oh_d2 = _op([[0,-1,0],[-1,0,0],[0,0,1]], "mirror", 1, [1,1,0],   label="σd(-xy)")
sigma_Oh_d3 = _op([[1,0,0],[0,0,1],[0,1,0]],   "mirror", 1, [0,1,-1],  label="σd(yz)")
sigma_Oh_d4 = _op([[1,0,0],[0,0,-1],[0,-1,0]], "mirror", 1, [0,1,1],   label="σd(-yz)")
sigma_Oh_d5 = _op([[0,0,1],[0,1,0],[1,0,0]],   "mirror", 1, [1,0,-1],  label="σd(xz)")
sigma_Oh_d6 = _op([[0,0,-1],[0,1,0],[-1,0,0]], "mirror", 1, [1,0,1],   label="σd(-xz)")

# ── 回反軸 (S_n = C_n · σ_h) ─────────────────────────────────
# S3 = C3 · σh: rotate 120° then reflect in xy.
S3z  = _op([[-0.5,-0.8660254,0],[0.8660254,-0.5,0],[0,0,-1]],  "rotoinversion", 3, [0,0,1], label="S3")
S3z5 = _op([[-0.5,0.8660254,0],[-0.8660254,-0.5,0],[0,0,-1]],  "rotoinversion", 3, [0,0,1], label="S3^5")

# S4 = C4 · σh: rotate 90° then reflect in xy.
S4z  = _op([[0,-1,0],[1,0,0],[0,0,-1]],  "rotoinversion", 4, [0,0,1], label="S4")
S4z3 = _op([[0,1,0],[-1,0,0],[0,0,-1]],  "rotoinversion", 4, [0,0,1], label="S4^3")
S4x  = _op([[1,0,0],[0,0,1],[0,-1,0]],   "rotoinversion", 4, [1,0,0], label="S4x")
S4x3 = _op([[1,0,0],[0,0,-1],[0,1,0]],   "rotoinversion", 4, [1,0,0], label="S4x^3")
S4y  = _op([[0,0,-1],[0,1,0],[1,0,0]],   "rotoinversion", 4, [0,1,0], label="S4y")
S4y3 = _op([[0,0,1],[0,1,0],[-1,0,0]],   "rotoinversion", 4, [0,1,0], label="S4y^3")

# S6 = C6 · σh: rotate 60° then reflect in xy.
# Verified: S6^3 = i ✓
S6z  = _op([[0.5,-0.8660254,0],[0.8660254,0.5,0],[0,0,-1]],  "rotoinversion", 6, [0,0,1], label="S6")
S6z5 = _op([[0.5,0.8660254,0],[-0.8660254,0.5,0],[0,0,-1]],  "rotoinversion", 6, [0,0,1], label="S6^5")


# ── ラベル付き辞書（point_groups.py のキー参照用）───────────────
OPERATIONS: dict[str, dict] = {
    "E":    E,
    "C2z":  C2z,  "C2x": C2x,  "C2y": C2y,
    "C2a":  C2_d3a,  "C2b": C2_d3b,  "C2c": C2_d3c,
    "C2d4a": C2_d4a,  "C2d4b": C2_d4b,
    "C3":   C3z,  "C3^2": C3z2,
    "C4":   C4z,  "C4^3": C4z3,
    "C4x":  C4x,  "C4x^3": C4x3,
    "C4y":  C4y,  "C4y^3": C4y3,
    "C6":   C6z,  "C6^5": C6z5,
    "C3(111)":  C3_111,   "C3^2(111)":  C3_111b,
    "C3(1-1-1)":C3_p1mm,  "C3^2(1-1-1)":C3_p1mb,
    "C3(-11-1)":C3_m1pm,  "C3^2(-11-1)":C3_m1pb,
    "C3(-1-11)":C3_mm1,   "C3^2(-1-11)":C3_mm1b,
    "C2(x)": C2_Tx,  "C2(y)": C2_Ty,  "C2(z)": C2_Tz,
    "C2(x+y)": C2_Oh_xpy,  "C2(x-y)": C2_Oh_xmy,
    "C2(x+z)": C2_Oh_xpz,  "C2(x-z)": C2_Oh_xmz,
    "C2(y+z)": C2_Oh_ypz,  "C2(y-z)": C2_Oh_ymz,
    "i":    i_op,
    "σh":   sigma_h,
    "σv":   sigma_xz,   "σv'":  sigma_yz,
    "σv1":  sigma_v_d3a, "σv2": sigma_v_d3b,  "σv3": sigma_v_d3c,
    "σd1":  sigma_d_d3a, "σd2": sigma_d_d3b,  "σd3": sigma_d_d3c,
    "σv_c4":  sigma_v_c4a,  "σv'_c4": sigma_v_c4b,
    "σd_c4":  sigma_d_c4a,  "σd'_c4": sigma_d_c4b,
    "σd_Oh1": sigma_Oh_d1,  "σd_Oh2": sigma_Oh_d2,
    "σd_Oh3": sigma_Oh_d3,  "σd_Oh4": sigma_Oh_d4,
    "σd_Oh5": sigma_Oh_d5,  "σd_Oh6": sigma_Oh_d6,
    "S3":   S3z,  "S3^5": S3z5,
    "S4":   S4z,  "S4^3": S4z3,
    "S4x":  S4x,  "S4x^3": S4x3,
    "S4y":  S4y,  "S4y^3": S4y3,
    "S6":   S6z,  "S6^5": S6z5,
}
