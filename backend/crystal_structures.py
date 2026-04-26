"""
フェーズ3：結晶構造データ

将来の空間群・CIF形式読み込みを見越した内部フォーマットで定義する。

内部フォーマット:
{
  "id":               str,         # 一意な識別子
  "mode":             "real"|"abstract",
  "point_group":      str,
  "name":             str,         # 表示名
  "formula":          str,         # 化学式（Unicode添字）
  "coordinate_system":"cartesian", # 点群は常に cartesian（空間群は"fractional"も可）
  "length_unit":      "angstrom",
  "atoms": [
    {
      "id":       str,             # 例 "N1"
      "element":  str,             # 元素記号（抽象配置は "A","B","C"）
      "label":    str,             # 表示ラベル
      "position": [x, y, z],      # 直交座標 (Å)
      "orbit":    str,             # 軌道名（将来のWyckoff位置用）
    }
  ],
  "bonds": [{"from": str, "to": str}],  # 結合（atom.id 参照）
  "symmetry_elements": [               # Phase 4/5 の可視化用
    {"type": "rotation", "order": n, "axis": [ax,ay,az]},
    {"type": "mirror",   "normal": [nx,ny,nz]},
    {"type": "inversion"},
    {"type": "rotoinversion", "order": n, "axis": [ax,ay,az]},
  ],
  "cell": None,  # 点群はNone; 将来: {"a":..,"b":..,"c":..,"alpha":..,"beta":..,"gamma":..}
}
"""

import math

# ── 元素の CPK カラーと表示半径 ──────────────────────────────

ELEMENT_PROPS: dict[str, dict] = {
    "H":  {"color": "#FFFFFF", "radius": 0.31},
    "C":  {"color": "#404040", "radius": 0.77},
    "N":  {"color": "#3050F8", "radius": 0.75},
    "O":  {"color": "#FF0D0D", "radius": 0.73},
    "F":  {"color": "#90E050", "radius": 0.71},
    "S":  {"color": "#FFFF30", "radius": 1.02},
    "Cl": {"color": "#1FF01F", "radius": 0.99},
    "P":  {"color": "#FF8000", "radius": 1.06},
    "B":  {"color": "#FFB5B5", "radius": 0.82},
    "Xe": {"color": "#429EB0", "radius": 1.36},
    "Pt": {"color": "#D4AF37", "radius": 1.39},
    "Fe": {"color": "#E06633", "radius": 1.26},
    # 抽象配置用「元素」（実際には形状・色を区別するためのラベル）
    "A":  {"color": "#FF8C00", "radius": 0.8},  # orange
    "B":  {"color": "#00CED1", "radius": 0.8},  # dark turquoise
    "C_":{"color": "#FF1493", "radius": 0.8},  # deep pink
    "D":  {"color": "#32CD32", "radius": 0.8},  # lime green
    "X":  {"color": "#9B59B6", "radius": 0.6},  # purple (center atom)
}


# ── 座標生成ヘルパー ──────────────────────────────────────────

def ring(n: int, r: float, z: float = 0.0, offset_deg: float = 0.0) -> list[list[float]]:
    """n 個の原子を xy 平面の半径 r の円上に等間隔で配置"""
    result = []
    for k in range(n):
        angle = math.radians(360 * k / n + offset_deg)
        result.append([r * math.cos(angle), r * math.sin(angle), z])
    return result


def tetrahedral(r: float) -> list[list[float]]:
    """正四面体の4頂点（中心は原点）"""
    s = r / math.sqrt(3)
    return [[s, s, s], [s, -s, -s], [-s, s, -s], [-s, -s, s]]


def octahedral(r: float) -> list[list[float]]:
    """正八面体の6頂点"""
    return [[r,0,0],[-r,0,0],[0,r,0],[0,-r,0],[0,0,r],[0,0,-r]]


def _atom(aid: str, element: str, pos: list[float], orbit: str = "a") -> dict:
    return {"id": aid, "element": element, "label": aid, "position": pos, "orbit": orbit}


def _bond(a: str, b: str) -> dict:
    return {"from": a, "to": b}


def _sym_rot(order: int, axis: list[float]) -> dict:
    return {"type": "rotation", "order": order, "axis": axis}


def _sym_mirror(normal: list[float]) -> dict:
    return {"type": "mirror", "normal": normal}


def _sym_inv() -> dict:
    return {"type": "inversion"}


def _sym_rotin(order: int, axis: list[float]) -> dict:
    return {"type": "rotoinversion", "order": order, "axis": axis}


def _structure(sid, mode, pg, name, formula, atoms, bonds=None, sym_elements=None):
    return {
        "id": sid,
        "mode": mode,
        "point_group": pg,
        "name": name,
        "formula": formula,
        "coordinate_system": "cartesian",
        "length_unit": "angstrom",
        "atoms": atoms,
        "bonds": bonds or [],
        "symmetry_elements": sym_elements or [],
        "cell": None,
    }


# ═══════════════════════════════════════════════════════════════
# 実在分子モード
# ═══════════════════════════════════════════════════════════════

def _nh3():
    """NH₃ (C3v): N-H = 1.012 Å, H-N-H = 107°"""
    r_nh = 1.012
    # sinα² = 2/3*(1 - cos(107°)) / 1 = ...
    cos_hnh = math.cos(math.radians(107.0))
    sin2a = (1 - cos_hnh) * 2 / 3
    sin_a = math.sqrt(sin2a)
    cos_a = math.sqrt(1 - sin2a)
    hs = ring(3, r_nh * sin_a, -r_nh * cos_a)
    atoms = [
        _atom("N1", "N", [0.0, 0.0, 0.0], "a"),
        _atom("H1", "H", hs[0], "b"),
        _atom("H2", "H", hs[1], "b"),
        _atom("H3", "H", hs[2], "b"),
    ]
    bonds = [_bond("N1","H1"), _bond("N1","H2"), _bond("N1","H3")]
    sym = [_sym_rot(3,[0,0,1]),
           _sym_mirror([1,0,0]), _sym_mirror([-0.5,0.866,0]), _sym_mirror([-0.5,-0.866,0])]
    return _structure("nh3", "real", "C3v", "アンモニア", "NH₃", atoms, bonds, sym)


def _h2o():
    """H₂O (C2v): O-H = 0.958 Å, H-O-H = 104.5°"""
    r_oh = 0.958
    half = math.radians(104.5 / 2)
    hx = r_oh * math.sin(half)
    hz = r_oh * math.cos(half)
    atoms = [
        _atom("O1", "O", [0.0, 0.0, 0.0], "a"),
        _atom("H1", "H", [ hx, 0.0, hz], "b"),
        _atom("H2", "H", [-hx, 0.0, hz], "b"),
    ]
    bonds = [_bond("O1","H1"), _bond("O1","H2")]
    sym = [_sym_rot(2,[0,0,1]),
           _sym_mirror([0,1,0]),  # xz 面
           _sym_mirror([1,0,0])]  # yz 面
    return _structure("h2o", "real", "C2v", "水", "H₂O", atoms, bonds, sym)


def _ch4():
    """CH₄ (Td): C-H = 1.085 Å, 正四面体"""
    hs = tetrahedral(1.085)
    atoms = [_atom("C1","C",[0,0,0],"a")] + [_atom(f"H{i+1}","H",p,"b") for i,p in enumerate(hs)]
    bonds = [_bond("C1",f"H{i+1}") for i in range(4)]
    body_diags = [[1,1,1],[-1,-1,1],[-1,1,-1],[1,-1,-1]]
    sym = ([_sym_rot(3,d) for d in body_diags] +
           [_sym_rot(2,[1,0,0]),_sym_rot(2,[0,1,0]),_sym_rot(2,[0,0,1])] +
           [_sym_mirror([1,1,0]),_sym_mirror([1,-1,0]),
            _sym_mirror([1,0,1]),_sym_mirror([1,0,-1]),
            _sym_mirror([0,1,1]),_sym_mirror([0,1,-1])])
    return _structure("ch4", "real", "Td", "メタン", "CH₄", atoms, bonds, sym)


def _sf6():
    """SF₆ (Oh): S-F = 1.564 Å, 正八面体"""
    fs = octahedral(1.564)
    atoms = [_atom("S1","S",[0,0,0],"a")] + [_atom(f"F{i+1}","F",p,"b") for i,p in enumerate(fs)]
    bonds = [_bond("S1",f"F{i+1}") for i in range(6)]
    sym = ([_sym_rot(4,[1,0,0]),_sym_rot(4,[0,1,0]),_sym_rot(4,[0,0,1])] +
           [_sym_rot(3,d) for d in [[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]]] +
           [_sym_mirror([1,0,0]),_sym_mirror([0,1,0]),_sym_mirror([0,0,1])] +
           [_sym_inv()])
    return _structure("sf6", "real", "Oh", "六フッ化硫黄", "SF₆", atoms, bonds, sym)


def _c6h6():
    """C₆H₆ (D6h): C-C = 1.395 Å, C-H = 1.085 Å"""
    rc, rh = 1.395, 1.395 + 1.085
    cs = ring(6, rc)
    hs = ring(6, rh)
    atoms = [_atom(f"C{i+1}","C",p,"a") for i,p in enumerate(cs)]
    atoms += [_atom(f"H{i+1}","H",p,"b") for i,p in enumerate(hs)]
    bonds = [_bond(f"C{i+1}", f"C{(i+1)%6+1}") for i in range(6)]
    bonds += [_bond(f"C{i+1}", f"H{i+1}") for i in range(6)]
    sym = ([_sym_rot(6,[0,0,1]),
            _sym_mirror([0,0,1]),   # σh
            _sym_mirror([1,0,0]),   # σv (例)
            _sym_inv()])
    return _structure("c6h6", "real", "D6h", "ベンゼン", "C₆H₆", atoms, bonds, sym)


def _h2o2():
    """H₂O₂ (C2): 2回回転軸"""
    r_oo, r_oh = 1.47, 0.96
    atoms = [
        _atom("O1","O",[-r_oo/2, 0, 0],"a"),
        _atom("O2","O",[ r_oo/2, 0, 0],"a"),
        _atom("H1","H",[-r_oo/2, 0.66, 0.65],"b"),
        _atom("H2","H",[ r_oo/2,-0.66,-0.65],"b"),
    ]
    bonds = [_bond("O1","O2"),_bond("O1","H1"),_bond("O2","H2")]
    return _structure("h2o2","real","C2","過酸化水素","H₂O₂",atoms,bonds,[_sym_rot(2,[0,0,1])])


def _ethylene():
    """C₂H₄ (D2h): エチレン"""
    r_cc, r_ch = 1.34, 1.08
    hx = r_ch * math.sin(math.radians(60))
    hz = r_ch * math.cos(math.radians(60))
    atoms = [
        _atom("C1","C",[-r_cc/2,0,0],"a"), _atom("C2","C",[r_cc/2,0,0],"a"),
        _atom("H1","H",[-r_cc/2-hx, 0, hz],"b"), _atom("H2","H",[-r_cc/2-hx, 0,-hz],"b"),
        _atom("H3","H",[ r_cc/2+hx, 0, hz],"b"), _atom("H4","H",[ r_cc/2+hx, 0,-hz],"b"),
    ]
    bonds = [_bond("C1","C2"),_bond("C1","H1"),_bond("C1","H2"),
             _bond("C2","H3"),_bond("C2","H4")]
    sym = [_sym_rot(2,[0,0,1]),_sym_rot(2,[1,0,0]),_sym_rot(2,[0,1,0]),
           _sym_mirror([0,0,1]),_sym_mirror([0,1,0]),_sym_mirror([1,0,0]),_sym_inv()]
    return _structure("ethylene","real","D2h","エチレン","C₂H₄",atoms,bonds,sym)


def _bf3():
    """BF₃ (D3h): 正三角形平面"""
    r_bf = 1.31
    fs = ring(3, r_bf)
    atoms = [_atom("B1","B",[0,0,0],"a")] + [_atom(f"F{i+1}","F",p,"b") for i,p in enumerate(fs)]
    bonds = [_bond("B1",f"F{i+1}") for i in range(3)]
    sym = [_sym_rot(3,[0,0,1]),
           _sym_mirror([0,0,1]),
           _sym_mirror([1,0,0]),_sym_mirror([-0.5,0.866,0]),_sym_mirror([-0.5,-0.866,0])]
    return _structure("bf3","real","D3h","三フッ化ホウ素","BF₃",atoms,bonds,sym)


def _staggered_ethane():
    """C₂H₆ staggered (D3d): Newman投影で60°ずらし"""
    r_cc, r_ch = 1.54, 1.09
    alpha = math.acos(-1/3) / 2  # テトラ角の半分
    hs_top = ring(3, r_ch * math.sin(alpha),  r_cc/2 + r_ch*math.cos(alpha))
    hs_bot = ring(3, r_ch * math.sin(alpha), -r_cc/2 - r_ch*math.cos(alpha), 60)
    atoms = [
        _atom("C1","C",[0,0, r_cc/2],"a"),
        _atom("C2","C",[0,0,-r_cc/2],"a"),
    ]
    atoms += [_atom(f"H{i+1}","H",p,"b") for i,p in enumerate(hs_top)]
    atoms += [_atom(f"H{i+4}","H",p,"b") for i,p in enumerate(hs_bot)]
    bonds = [_bond("C1","C2")]
    bonds += [_bond("C1",f"H{i+1}") for i in range(3)]
    bonds += [_bond("C2",f"H{i+4}") for i in range(3)]
    sym = [_sym_rot(3,[0,0,1]),_sym_inv(),_sym_rotin(6,[0,0,1])]
    return _structure("ethane_d3d","real","D3d","エタン（ねじれ形）","C₂H₆",atoms,bonds,sym)


def _allene():
    """C₃H₄ (D2d): アレン"""
    r_cc, r_ch = 1.31, 1.08
    hs_top = ring(2, r_ch, r_cc)
    hs_bot = ring(2, r_ch, -r_cc, 90)
    atoms = [
        _atom("C1","C",[0,0,r_cc],"a"), _atom("C2","C",[0,0,0],"a"), _atom("C3","C",[0,0,-r_cc],"a"),
        _atom("H1","H",hs_top[0],"b"), _atom("H2","H",hs_top[1],"b"),
        _atom("H3","H",hs_bot[0],"b"), _atom("H4","H",hs_bot[1],"b"),
    ]
    bonds = [_bond("C1","C2"),_bond("C2","C3"),
             _bond("C1","H1"),_bond("C1","H2"),_bond("C3","H3"),_bond("C3","H4")]
    sym = [_sym_rot(2,[0,0,1]),_sym_rotin(4,[0,0,1]),
           _sym_mirror([1,1,0]),_sym_mirror([1,-1,0])]
    return _structure("allene","real","D2d","アレン","C₃H₄",atoms,bonds,sym)


def _xef4():
    """XeF₄ (D4h): 平面四配位"""
    r_xef = 1.95
    fs = ring(4, r_xef)
    atoms = [_atom("Xe1","Xe",[0,0,0],"a")] + [_atom(f"F{i+1}","F",p,"b") for i,p in enumerate(fs)]
    bonds = [_bond("Xe1",f"F{i+1}") for i in range(4)]
    sym = [_sym_rot(4,[0,0,1]),
           _sym_mirror([0,0,1]),_sym_mirror([0,1,0]),_sym_mirror([1,0,0]),
           _sym_mirror([1,1,0]),_sym_mirror([1,-1,0]),_sym_inv()]
    return _structure("xef4","real","D4h","四フッ化キセノン","XeF₄",atoms,bonds,sym)


# ═══════════════════════════════════════════════════════════════
# 架空配置モード（全32点群）
# ═══════════════════════════════════════════════════════════════
#
# 命名規則:
#   中心原子 = element "X" (purple)
#   主軌道   = element "A" (orange)
#   副軌道   = element "B" (turquoise)
#   第3軌道  = element "C_" (pink)
#

def _abs(pg, name, atoms, bonds=None, sym_elements=None):
    return _structure(f"abs_{pg.lower()}", "abstract", pg, name, "", atoms, bonds, sym_elements)


def _abstract_all() -> dict[str, dict]:
    structs = {}

    # ── C1: 4 atoms at asymmetric positions ──────────────────
    structs["C1"] = _abs("C1", "恒等群（C₁）", [
        _atom("A1","A",[0.0,0.0,0.0],"a"),
    ], sym_elements=[])

    # ── Ci: inversion pair ────────────────────────────────────
    structs["Ci"] = _abs("Ci", "反転群（Cᵢ）", [
        _atom("A1","A",[ 0.9, 0.5, 0.4],"a"),
        _atom("A2","A",[-0.9,-0.5,-0.4],"a"),
    ], sym_elements=[_sym_inv()])

    # ── Cs: mirror in xz-plane (normal = y) ──────────────────
    structs["Cs"] = _abs("Cs", "鏡映群（Cₛ）", [
        _atom("A1","A",[0.8, 0.8,0.3],"a"),
        _atom("A2","A",[0.8,-0.8,0.3],"a"),
        _atom("B1","B",[0.0, 0.0,0.9],"b"),
    ], [_bond("B1","A1"),_bond("B1","A2")],
    [_sym_mirror([0,1,0])])

    # ── C2: C2 around z ──────────────────────────────────────
    structs["C2"] = _abs("C2", "2回回転群（C₂）", [
        _atom("A1","A",[ 0.8, 0.4, 0.5],"a"),
        _atom("A2","A",[-0.8,-0.4, 0.5],"a"),
    ], sym_elements=[_sym_rot(2,[0,0,1])])

    # ── C2h ──────────────────────────────────────────────────
    structs["C2h"] = _abs("C2h", "2/m", [
        _atom("A1","A",[ 0.9, 0.4, 0.5],"a"),
        _atom("A2","A",[-0.9,-0.4, 0.5],"a"),
        _atom("A3","A",[-0.9,-0.4,-0.5],"a"),
        _atom("A4","A",[ 0.9, 0.4,-0.5],"a"),
    ], sym_elements=[_sym_rot(2,[0,0,1]),_sym_mirror([0,0,1]),_sym_inv()])

    # ── C2v: B on C2, two A's symmetric about mirror ─────────
    structs["C2v"] = _abs("C2v", "mm2", [
        _atom("X1","X",[0.0, 0.0, 0.0],"a"),
        _atom("A1","A",[ 0.9, 0.0, 0.7],"b"),
        _atom("A2","A",[-0.9, 0.0, 0.7],"b"),
    ], [_bond("X1","A1"),_bond("X1","A2")],
    [_sym_rot(2,[0,0,1]),_sym_mirror([0,1,0]),_sym_mirror([1,0,0])])

    # ── D2 ────────────────────────────────────────────────────
    structs["D2"] = _abs("D2", "222", [
        _atom("A1","A",[ 0.9, 0.5, 0.4],"a"),
        _atom("A2","A",[-0.9,-0.5, 0.4],"a"),
        _atom("A3","A",[ 0.9,-0.5,-0.4],"a"),
        _atom("A4","A",[-0.9, 0.5,-0.4],"a"),
    ], sym_elements=[_sym_rot(2,[0,0,1]),_sym_rot(2,[1,0,0]),_sym_rot(2,[0,1,0])])

    # ── D2h ───────────────────────────────────────────────────
    structs["D2h"] = _abs("D2h", "mmm", [
        _atom("A1","A",[ 0.9, 0.5, 0.0],"a"),
        _atom("A2","A",[-0.9, 0.5, 0.0],"a"),
        _atom("A3","A",[-0.9,-0.5, 0.0],"a"),
        _atom("A4","A",[ 0.9,-0.5, 0.0],"a"),
    ], [_bond("A1","A2"),_bond("A2","A3"),_bond("A3","A4"),_bond("A4","A1")],
    [_sym_rot(2,[0,0,1]),_sym_rot(2,[1,0,0]),_sym_rot(2,[0,1,0]),
     _sym_mirror([0,0,1]),_sym_mirror([1,0,0]),_sym_mirror([0,1,0]),_sym_inv()])

    # ── C3: 3-fold ring ───────────────────────────────────────
    ps = ring(3, 1.0, 0.0)
    structs["C3"] = _abs("C3", "3", [
        _atom(f"A{i+1}","A",p,"a") for i,p in enumerate(ps)
    ], sym_elements=[_sym_rot(3,[0,0,1])])

    # ── C3i: 3 above + 3 below (inversion) ───────────────────
    pt = ring(3, 1.0,  0.5)
    pb = ring(3, 1.0, -0.5)
    structs["C3i"] = _abs("C3i", "-3", [
        _atom(f"A{i+1}","A",p,"a") for i,p in enumerate(pt)
    ] + [
        _atom(f"A{i+4}","A",p,"a") for i,p in enumerate(pb)
    ], sym_elements=[_sym_rot(3,[0,0,1]),_sym_inv(),_sym_rotin(6,[0,0,1])])

    # ── C3v: center + triangle (NH₃-like) ────────────────────
    hs = ring(3, 1.0, -0.4)
    structs["C3v"] = _abs("C3v", "3m", [
        _atom("X1","X",[0.0,0.0,0.0],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(hs)],
    [_bond("X1",f"A{i+1}") for i in range(3)],
    [_sym_rot(3,[0,0,1]),
     _sym_mirror([1,0,0]),_sym_mirror([-0.5,0.866,0]),_sym_mirror([-0.5,-0.866,0])])

    # ── D3: 3 top + 3 bottom staggered ───────────────────────
    pt = ring(3, 1.0,  0.5,  0)
    pb = ring(3, 1.0, -0.5, 60)
    structs["D3"] = _abs("D3", "32", [
        _atom(f"A{i+1}","A",p,"a") for i,p in enumerate(pt)
    ] + [
        _atom(f"B{i+1}","B",p,"b") for i,p in enumerate(pb)
    ], sym_elements=[_sym_rot(3,[0,0,1]),
                     _sym_rot(2,[1,0,0]),_sym_rot(2,[-0.5,0.866,0]),_sym_rot(2,[-0.5,-0.866,0])])

    # ── D3d: staggered octahedra / eclipsed C3 ───────────────
    pt = ring(3, 1.0,  0.6,  0)
    pb = ring(3, 1.0, -0.6, 60)
    structs["D3d"] = _abs("D3d", "-3m", [
        _atom("X1","X",[0,0,0],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(pt)]
      + [_atom(f"A{i+4}","A",p,"b") for i,p in enumerate(pb)],
    [_bond("X1",f"A{i+1}") for i in range(6)],
    [_sym_rot(3,[0,0,1]),_sym_inv(),_sym_rotin(6,[0,0,1]),
     _sym_mirror([1,0,0]),_sym_mirror([-0.5,0.866,0]),_sym_mirror([-0.5,-0.866,0])])

    # ── D3h: center + triangle in plane ──────────────────────
    ps = ring(3, 1.2, 0.0)
    structs["D3h"] = _abs("D3h", "-6m2", [
        _atom("X1","X",[0,0,0],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(ps)],
    [_bond("X1",f"A{i+1}") for i in range(3)],
    [_sym_rot(3,[0,0,1]),_sym_mirror([0,0,1]),
     _sym_mirror([1,0,0]),_sym_mirror([-0.5,0.866,0]),_sym_mirror([-0.5,-0.866,0])])

    # ── S4: pinwheel (S4 axis) ────────────────────────────────
    structs["S4"] = _abs("S4", "-4", [
        _atom("A1","A",[ 1.0, 0.0, 0.5],"a"),
        _atom("A2","A",[ 0.0, 1.0,-0.5],"a"),
        _atom("A3","A",[-1.0, 0.0, 0.5],"a"),
        _atom("A4","A",[ 0.0,-1.0,-0.5],"a"),
    ], sym_elements=[_sym_rot(2,[0,0,1]),_sym_rotin(4,[0,0,1])])

    # ── C4: 4-fold ring ───────────────────────────────────────
    ps = ring(4, 1.0, 0.0)
    structs["C4"] = _abs("C4", "4", [
        _atom(f"A{i+1}","A",p,"a") for i,p in enumerate(ps)
    ], sym_elements=[_sym_rot(4,[0,0,1])])

    # ── C4h ──────────────────────────────────────────────────
    pt = ring(4, 1.0,  0.4)
    pb = ring(4, 1.0, -0.4)
    structs["C4h"] = _abs("C4h", "4/m", [
        _atom(f"A{i+1}","A",p,"a") for i,p in enumerate(pt)
    ] + [
        _atom(f"A{i+5}","A",p,"a") for i,p in enumerate(pb)
    ], sym_elements=[_sym_rot(4,[0,0,1]),_sym_mirror([0,0,1]),_sym_inv()])

    # ── C4v: center + square ─────────────────────────────────
    ps = ring(4, 1.2, 0.0)
    structs["C4v"] = _abs("C4v", "4mm", [
        _atom("X1","X",[0,0,0.8],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(ps)],
    [_bond("X1",f"A{i+1}") for i in range(4)],
    [_sym_rot(4,[0,0,1]),_sym_mirror([1,0,0]),_sym_mirror([0,1,0]),
     _sym_mirror([1,1,0]),_sym_mirror([1,-1,0])])

    # ── D2d: allene-like ──────────────────────────────────────
    structs["D2d"] = _abs("D2d", "-42m", [
        _atom("X1","X",[0,0,0],"a"),
        _atom("A1","A",[ 1.1, 0.0, 0.7],"b"),
        _atom("A2","A",[-1.1, 0.0, 0.7],"b"),
        _atom("A3","A",[ 0.0, 1.1,-0.7],"b"),
        _atom("A4","A",[ 0.0,-1.1,-0.7],"b"),
    ], [_bond("X1",f"A{i+1}") for i in range(4)],
    [_sym_rot(2,[0,0,1]),_sym_rotin(4,[0,0,1]),
     _sym_mirror([1,1,0]),_sym_mirror([1,-1,0])])

    # ── D4: square + extra C2 ─────────────────────────────────
    inner = ring(4, 0.8,  0.4)
    outer = ring(4, 1.2, -0.4, 45)
    structs["D4"] = _abs("D4", "422", [
        _atom(f"A{i+1}","A",p,"a") for i,p in enumerate(inner)
    ] + [
        _atom(f"B{i+1}","B",p,"b") for i,p in enumerate(outer)
    ], sym_elements=[_sym_rot(4,[0,0,1]),
                     _sym_rot(2,[1,0,0]),_sym_rot(2,[0,1,0]),
                     _sym_rot(2,[1,1,0]),_sym_rot(2,[1,-1,0])])

    # ── D4h: square planar ────────────────────────────────────
    ps = ring(4, 1.5, 0.0)
    structs["D4h"] = _abs("D4h", "4/mmm", [
        _atom("X1","X",[0,0,0],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(ps)],
    [_bond("X1",f"A{i+1}") for i in range(4)],
    [_sym_rot(4,[0,0,1]),_sym_mirror([0,0,1]),
     _sym_mirror([1,0,0]),_sym_mirror([0,1,0]),
     _sym_mirror([1,1,0]),_sym_mirror([1,-1,0]),_sym_inv()])

    # ── C3h: triangle in plane ────────────────────────────────
    ps = ring(3, 1.2, 0.0)
    structs["C3h"] = _abs("C3h", "-6", [
        _atom("X1","X",[0,0,0],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(ps)],
    [_bond("X1",f"A{i+1}") for i in range(3)],
    [_sym_rot(3,[0,0,1]),_sym_mirror([0,0,1]),_sym_rotin(6,[0,0,1])])

    # ── C6: hexagonal ring ────────────────────────────────────
    ps = ring(6, 1.2, 0.0)
    structs["C6"] = _abs("C6", "6", [
        _atom(f"A{i+1}","A",p,"a") for i,p in enumerate(ps)
    ] + [_bond(f"A{i+1}",f"A{i%6+1}") for i in range(6)],  # wrong, fix below
    sym_elements=[_sym_rot(6,[0,0,1])])
    # rebuild bonds properly
    ps6 = ring(6, 1.2, 0.0)
    structs["C6"] = _abs("C6", "6", [
        _atom(f"A{i+1}","A",p,"a") for i,p in enumerate(ps6)
    ], [_bond(f"A{i+1}",f"A{i%6+2 if i<5 else 1}") for i in range(6)],
    [_sym_rot(6,[0,0,1])])

    # ── C6h ──────────────────────────────────────────────────
    pt = ring(6, 1.2,  0.3)
    pb = ring(6, 1.2, -0.3)
    structs["C6h"] = _abs("C6h", "6/m", [
        _atom(f"A{i+1}","A",p,"a") for i,p in enumerate(pt)
    ] + [
        _atom(f"A{i+7}","A",p,"a") for i,p in enumerate(pb)
    ], sym_elements=[_sym_rot(6,[0,0,1]),_sym_mirror([0,0,1]),_sym_inv()])

    # ── C6v: center + hexagon ─────────────────────────────────
    ps = ring(6, 1.4, 0.0)
    structs["C6v"] = _abs("C6v", "6mm", [
        _atom("X1","X",[0,0,1.0],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(ps)],
    [_bond("X1",f"A{i+1}") for i in range(6)],
    [_sym_rot(6,[0,0,1]),_sym_mirror([1,0,0]),_sym_mirror([0,1,0]),
     _sym_mirror([1,1,0]),_sym_mirror([1,-1,0])])

    # ── D6: hexagon + 6 C2 ────────────────────────────────────
    inner = ring(6, 0.8, 0.4)
    outer = ring(6, 1.4,-0.4, 30)
    structs["D6"] = _abs("D6", "622", [
        _atom(f"A{i+1}","A",p,"a") for i,p in enumerate(inner)
    ] + [
        _atom(f"B{i+1}","B",p,"b") for i,p in enumerate(outer)
    ], sym_elements=[_sym_rot(6,[0,0,1]),
                     _sym_rot(2,[1,0,0]),_sym_rot(2,[0,1,0])])

    # ── D6h: benzene-like ─────────────────────────────────────
    c_pos = ring(6, 1.2, 0.0)
    h_pos = ring(6, 2.1, 0.0)
    structs["D6h"] = _abs("D6h", "6/mmm", [
        _atom(f"A{i+1}","A",p,"a") for i,p in enumerate(c_pos)
    ] + [
        _atom(f"B{i+1}","B",p,"b") for i,p in enumerate(h_pos)
    ], [_bond(f"A{i+1}",f"A{i%6+2 if i<5 else 1}") for i in range(6)]
      +[_bond(f"A{i+1}",f"B{i+1}") for i in range(6)],
    [_sym_rot(6,[0,0,1]),_sym_mirror([0,0,1]),_sym_inv()])

    # ── T: 4 body-diagonal C3 axes ───────────────────────────
    vs = tetrahedral(1.2)
    structs["T"] = _abs("T", "23", [
        _atom("X1","X",[0,0,0],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(vs)],
    [_bond("X1",f"A{i+1}") for i in range(4)],
    [_sym_rot(3,[1,1,1]),_sym_rot(3,[-1,-1,1]),_sym_rot(3,[-1,1,-1]),_sym_rot(3,[1,-1,-1]),
     _sym_rot(2,[1,0,0]),_sym_rot(2,[0,1,0]),_sym_rot(2,[0,0,1])])

    # ── Td: tetrahedron (CH₄-like) ────────────────────────────
    vs = tetrahedral(1.3)
    structs["Td"] = _abs("Td", "-43m", [
        _atom("X1","X",[0,0,0],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(vs)],
    [_bond("X1",f"A{i+1}") for i in range(4)],
    [_sym_rot(3,[1,1,1]),_sym_rot(3,[-1,-1,1]),
     _sym_rotin(4,[1,0,0]),_sym_rotin(4,[0,1,0]),_sym_rotin(4,[0,0,1]),
     _sym_mirror([1,1,0]),_sym_mirror([1,-1,0]),
     _sym_mirror([1,0,1]),_sym_mirror([1,0,-1]),
     _sym_mirror([0,1,1]),_sym_mirror([0,1,-1])])

    # ── Th: T + inversion ────────────────────────────────────
    vs = tetrahedral(1.2)
    structs["Th"] = _abs("Th", "m-3", [
        _atom("X1","X",[0,0,0],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(vs)]
      + [_atom(f"A{i+5}","A",[-p[0],-p[1],-p[2]],"b") for i,p in enumerate(vs)],
    [_bond("X1",f"A{i+1}") for i in range(4)]
   +[_bond("X1",f"A{i+5}") for i in range(4)],
    [_sym_rot(3,[1,1,1]),_sym_inv(),_sym_mirror([1,0,0]),_sym_mirror([0,1,0]),_sym_mirror([0,0,1])])

    # ── O: octahedral rotation ────────────────────────────────
    oct_v = octahedral(1.3)
    structs["O"] = _abs("O", "432", [
        _atom("X1","X",[0,0,0],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(oct_v)],
    [_bond("X1",f"A{i+1}") for i in range(6)],
    [_sym_rot(4,[1,0,0]),_sym_rot(4,[0,1,0]),_sym_rot(4,[0,0,1]),
     _sym_rot(3,[1,1,1]),_sym_rot(3,[-1,-1,1]),_sym_rot(3,[-1,1,-1]),_sym_rot(3,[1,-1,-1])])

    # ── Oh: octahedron (SF₆-like) ─────────────────────────────
    oct_v = octahedral(1.4)
    structs["Oh"] = _abs("Oh", "m-3m", [
        _atom("X1","X",[0,0,0],"a"),
    ] + [_atom(f"A{i+1}","A",p,"b") for i,p in enumerate(oct_v)],
    [_bond("X1",f"A{i+1}") for i in range(6)],
    [_sym_rot(4,[1,0,0]),_sym_rot(4,[0,1,0]),_sym_rot(4,[0,0,1]),
     _sym_rot(3,[1,1,1]),_sym_inv(),
     _sym_mirror([1,0,0]),_sym_mirror([0,1,0]),_sym_mirror([0,0,1])])

    return structs


# ═══════════════════════════════════════════════════════════════
# レジストリと取得 API
# ═══════════════════════════════════════════════════════════════

# 実在分子の登録
REAL_STRUCTURES: dict[str, dict] = {
    "C3v": _nh3(),
    "C2v": _h2o(),
    "Td":  _ch4(),
    "Oh":  _sf6(),
    "D6h": _c6h6(),
    "C2":  _h2o2(),
    "D2h": _ethylene(),
    "D3h": _bf3(),
    "D3d": _staggered_ethane(),
    "D2d": _allene(),
    "D4h": _xef4(),
}

# 架空配置の登録（全32群）
ABSTRACT_STRUCTURES: dict[str, dict] = _abstract_all()

# 架空モードで実在構造を使える点群にはそちらを優先してもよいが、
# abstract モードは純粋に教科書的な配置を使う。
# 実在モードで実在分子がない点群は abstract で代替する。


def get_structure(point_group: str, mode: str = "abstract") -> dict:
    """
    指定した点群とモードの構造データを返す。
    mode="real" で実在分子がない場合は abstract にフォールバック。
    """
    if mode == "real":
        if point_group in REAL_STRUCTURES:
            return REAL_STRUCTURES[point_group]
        # フォールバック
        if point_group in ABSTRACT_STRUCTURES:
            return ABSTRACT_STRUCTURES[point_group]
        raise ValueError(f"No structure found for {point_group}")
    else:
        if point_group in ABSTRACT_STRUCTURES:
            return ABSTRACT_STRUCTURES[point_group]
        raise ValueError(f"No abstract structure for {point_group}")


def list_structures(mode: str | None = None) -> list[dict]:
    """全構造のサマリーリストを返す（API 用）"""
    results = []
    if mode in (None, "real"):
        for pg, s in REAL_STRUCTURES.items():
            results.append({
                "id": s["id"], "mode": "real",
                "point_group": pg,
                "name": s["name"], "formula": s["formula"],
                "atom_count": len(s["atoms"]),
            })
    if mode in (None, "abstract"):
        for pg, s in ABSTRACT_STRUCTURES.items():
            results.append({
                "id": s["id"], "mode": "abstract",
                "point_group": pg,
                "name": s["name"], "formula": s["formula"],
                "atom_count": len(s["atoms"]),
            })
    return results
