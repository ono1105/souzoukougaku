"""
フェーズ3のテスト: crystal_structures.py
"""

import sys, math
sys.path.insert(0, ".")

from crystal_structures import (
    get_structure, list_structures,
    REAL_STRUCTURES, ABSTRACT_STRUCTURES, ELEMENT_PROPS,
)


def test_all_32_abstract():
    """全32点群に架空配置が存在する"""
    from point_groups import list_groups
    groups = list_groups()
    missing = [g for g in groups if g not in ABSTRACT_STRUCTURES]
    assert not missing, f"架空配置が欠落: {missing}"
    print(f"[OK] 全32点群に架空配置あり")


def test_real_molecules_present():
    """主要な実在分子が定義されている"""
    required = {"C3v", "C2v", "Td", "Oh", "D6h"}
    for pg in required:
        assert pg in REAL_STRUCTURES, f"実在分子が欠落: {pg}"
    print(f"[OK] 実在分子 {len(REAL_STRUCTURES)} 種: {list(REAL_STRUCTURES.keys())}")


def test_structure_format(struct: dict, label: str):
    """構造データが必須フィールドを持つか検証"""
    for field in ("id","mode","point_group","name","coordinate_system",
                  "length_unit","atoms","bonds","symmetry_elements","cell"):
        assert field in struct, f"{label}: '{field}' フィールドが欠落"
    for atom in struct["atoms"]:
        for afield in ("id","element","label","position","orbit"):
            assert afield in atom, f"{label}.atoms: '{afield}' が欠落"
        pos = atom["position"]
        assert len(pos) == 3, f"{label}: position は3次元"
    for bond in struct["bonds"]:
        assert "from" in bond and "to" in bond
    assert struct["coordinate_system"] == "cartesian"
    assert struct["length_unit"] == "angstrom"
    assert struct["cell"] is None


def test_all_structures_format():
    """全構造のフォーマット検証"""
    for pg, s in REAL_STRUCTURES.items():
        test_structure_format(s, f"real/{pg}")
    for pg, s in ABSTRACT_STRUCTURES.items():
        test_structure_format(s, f"abstract/{pg}")
    print(f"[OK] 全構造フォーマット検証完了 "
          f"(real:{len(REAL_STRUCTURES)}, abstract:{len(ABSTRACT_STRUCTURES)})")


def test_bond_references():
    """ボンドの参照先が全て実在するアトムIDか確認"""
    problems = []
    for pg, s in {**REAL_STRUCTURES, **ABSTRACT_STRUCTURES}.items():
        atom_ids = {a["id"] for a in s["atoms"]}
        for bond in s["bonds"]:
            if bond["from"] not in atom_ids:
                problems.append(f"{s['id']}: bond.from={bond['from']} が原子リストにない")
            if bond["to"] not in atom_ids:
                problems.append(f"{s['id']}: bond.to={bond['to']} が原子リストにない")
    if problems:
        for p in problems[:5]:
            print(f"  [FAIL] {p}")
    assert not problems, f"ボンド参照エラー: {len(problems)} 件"
    print("[OK] 全ボンド参照が正常")


def test_nh3_geometry():
    """NH₃ の幾何学的正確性（C3v）"""
    s = get_structure("C3v", "real")
    assert s["formula"] == "NH₃"
    atoms = {a["id"]: a["position"] for a in s["atoms"]}
    n = atoms["N1"]
    h1 = atoms["H1"]
    h2 = atoms["H2"]

    def dist(a, b):
        return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))

    def angle(v, c, u):
        """angle at c"""
        a = [v[i]-c[i] for i in range(3)]
        b = [u[i]-c[i] for i in range(3)]
        dot = sum(a[i]*b[i] for i in range(3))
        la = math.sqrt(sum(x**2 for x in a))
        lb = math.sqrt(sum(x**2 for x in b))
        return math.degrees(math.acos(dot / (la*lb)))

    nh_bond = dist(n, h1)
    hnh_angle = angle(h1, n, h2)
    print(f"  NH₃: N-H = {nh_bond:.3f} Å (expect ~1.012)")
    print(f"  NH₃: H-N-H = {hnh_angle:.1f}° (expect ~107°)")
    assert abs(nh_bond - 1.012) < 0.01
    assert abs(hnh_angle - 107.0) < 1.0
    print("[OK] NH₃ 幾何学検証")


def test_sf6_geometry():
    """SF₆ の正八面体確認（Oh）"""
    s = get_structure("Oh", "real")
    atoms = {a["id"]: a["position"] for a in s["atoms"]}
    s_pos = atoms["S1"]
    f_dists = []
    for i in range(1, 7):
        f = atoms[f"F{i}"]
        d = math.sqrt(sum((f[j]-s_pos[j])**2 for j in range(3)))
        f_dists.append(d)
    print(f"  SF₆: S-F distances = {[f'{d:.3f}' for d in f_dists]}")
    for d in f_dists:
        assert abs(d - 1.564) < 0.001
    print("[OK] SF₆ 幾何学検証")


def test_ch4_tetrahedral():
    """CH₄ の正四面体確認（Td）"""
    s = get_structure("Td", "real")
    atoms = {a["id"]: a["position"] for a in s["atoms"]}
    c = atoms["C1"]
    def dist(a, b):
        return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))
    dists = [dist(c, atoms[f"H{i+1}"]) for i in range(4)]
    print(f"  CH₄: C-H distances = {[f'{d:.3f}' for d in dists]}")
    for d in dists:
        assert abs(d - 1.085) < 0.001
    # Check HCH angle ≈ 109.47°
    def angle(v, c, u):
        a = [v[i]-c[i] for i in range(3)]
        b = [u[i]-c[i] for i in range(3)]
        dot = sum(a[i]*b[i] for i in range(3))
        la = math.sqrt(sum(x**2 for x in a))
        lb = math.sqrt(sum(x**2 for x in b))
        return math.degrees(math.acos(max(-1, min(1, dot / (la*lb)))))
    hch = angle(atoms["H1"], c, atoms["H2"])
    print(f"  CH₄: H-C-H = {hch:.1f}° (expect ~109.47°)")
    assert abs(hch - 109.47) < 0.5
    print("[OK] CH₄ 幾何学検証")


def test_get_structure_fallback():
    """実在分子のない点群で real モードを指定すると abstract にフォールバック"""
    # C1 には実在分子なし
    s = get_structure("C1", "real")
    assert s["mode"] == "abstract"
    print(f"[OK] C1/real → abstract にフォールバック")


def test_get_structure_abstract():
    s = get_structure("C3v", "abstract")
    assert s["mode"] == "abstract"
    assert s["point_group"] == "C3v"
    print(f"[OK] get_structure('C3v', 'abstract'): {len(s['atoms'])} atoms")


def test_list_structures():
    all_s = list_structures()
    real_s = list_structures("real")
    abs_s = list_structures("abstract")
    print(f"[OK] list_structures: total={len(all_s)}, real={len(real_s)}, abstract={len(abs_s)}")
    assert len(real_s) == len(REAL_STRUCTURES)
    assert len(abs_s) == len(ABSTRACT_STRUCTURES)
    for entry in real_s:
        assert "id" in entry and "point_group" in entry and "atom_count" in entry


def test_symmetry_elements_present():
    """主要点群に対称要素が定義されている"""
    checks = {
        "C3v": "rotation",
        "Oh":  "inversion",
        "Td":  "mirror",
        "D6h": "inversion",
    }
    for pg, expected_type in checks.items():
        s_real = get_structure(pg, "real")
        types = {e["type"] for e in s_real["symmetry_elements"]}
        assert expected_type in types, f"{pg}: '{expected_type}' 対称要素が欠落"
    print("[OK] 主要点群の対称要素定義確認")


def test_cif_compatible_format():
    """CIF変換に必要なフィールドが揃っているか確認"""
    s = get_structure("C3v", "real")
    # CIFに必要: 元素名, 座標, cell (None for point groups)
    for atom in s["atoms"]:
        assert isinstance(atom["element"], str)
        assert all(isinstance(c, float) for c in atom["position"])
    assert s["cell"] is None
    assert s["coordinate_system"] == "cartesian"
    print("[OK] CIF互換フォーマット確認")


def test_abstract_c3v_structure():
    """C3v の架空配置: 中心原子 + 3つの等距離原子"""
    s = get_structure("C3v", "abstract")
    assert s["point_group"] == "C3v"
    atoms = s["atoms"]
    center = [a for a in atoms if a["orbit"] == "a"]
    orbit_b = [a for a in atoms if a["orbit"] == "b"]
    assert len(center) == 1, f"中心原子は1つのはず: {center}"
    assert len(orbit_b) == 3, f"主軌道は3原子: {orbit_b}"
    # 3原子が等距離
    cx = center[0]["position"]
    dists = [math.sqrt(sum((a["position"][j]-cx[j])**2 for j in range(3))) for a in orbit_b]
    print(f"  C3v abstract: orbit-b distances from center = {[f'{d:.3f}' for d in dists]}")
    assert max(dists) - min(dists) < 0.001, "3原子は中心から等距離のはず"
    print("[OK] C3v 架空配置の3回対称確認")


if __name__ == "__main__":
    test_all_32_abstract()
    test_real_molecules_present()
    test_all_structures_format()
    test_bond_references()
    test_nh3_geometry()
    test_sf6_geometry()
    test_ch4_tetrahedral()
    test_get_structure_fallback()
    test_get_structure_abstract()
    test_list_structures()
    test_symmetry_elements_present()
    test_cif_compatible_format()
    test_abstract_c3v_structure()
    print("\n=== フェーズ3 全テスト合格 ===")
