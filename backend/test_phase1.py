"""
フェーズ1のスモークテスト。
"""

import sys
sys.path.insert(0, ".")

from point_groups import POINT_GROUPS, list_groups, get_group
from symmetry_group import SymmetryGroup
from group_theory import get_available_quotients, apply_quotient, apply_operation, build_all_groups


def test_group_count():
    groups = list_groups()
    print(f"[OK] 定義済み点群数: {len(groups)}")
    assert len(groups) >= 20, f"点群数が少ない: {len(groups)}"


def test_c3v_decomposition():
    """C3v の分解: C3v → C3 → C1"""
    all_groups = build_all_groups()
    g = all_groups["C3v"]
    print(f"\n[C3v] order={g.order}, normal_subgroups={g.normal_subgroups}")

    quotients = get_available_quotients(g)
    print(f"  選べる既約な商群: {[q['quotient_name'] + '(→' + q['normal_subgroup'] + ')' for q in quotients]}")
    assert any(q["normal_subgroup"] == "C3" for q in quotients), "C3v → C3 の分解が見つからない"

    # C3 へ
    g2 = apply_quotient(g, "C3")
    print(f"\n[C3] order={g2.order}")
    quotients2 = get_available_quotients(g2)
    print(f"  選べる既約な商群: {[q['quotient_name'] + '(→' + q['normal_subgroup'] + ')' for q in quotients2]}")
    assert any(q["normal_subgroup"] == "C1" for q in quotients2), "C3 → C1 の分解が見つからない"

    # C1 へ（終了）
    g3 = apply_quotient(g2, "C1")
    print(f"\n[C1] order={g3.order}")
    quotients3 = get_available_quotients(g3)
    print(f"  選べる既約な商群: {quotients3} (空のはず)")
    assert quotients3 == [], f"C1 に到達後も商群が存在する: {quotients3}"
    print("[OK] C3v → C3 → C1 の分解成功")


def test_apply_operation():
    """鏡映操作の座標変換テスト"""
    from symmetry_operations import sigma_h
    coords = [[1.0, 0.5, 1.0], [0.0, 0.0, -1.0]]
    result = apply_operation(coords, sigma_h)
    print(f"\n[apply_operation] σh: {coords} → {result}")
    assert abs(result[0][2] - (-1.0)) < 1e-9, "z成分の符号反転が正しくない"
    assert abs(result[1][2] - 1.0) < 1e-9, "z成分の符号反転が正しくない"
    print("[OK] apply_operation テスト成功")


def test_seitz_format():
    """Seitz記法の構造テスト"""
    all_groups = build_all_groups()
    g = all_groups["Oh"]
    for op in g.operations:
        assert "rotation" in op, f"rotation キーがない: {op}"
        assert "translation" in op, f"translation キーがない: {op}"
        assert "type" in op, f"type キーがない: {op}"
        assert "axis" in op, f"axis キーがない: {op}"
    print(f"[OK] Oh の全対称操作が Seitz 形式: {len(g.operations)}個")


def test_build_all_groups():
    all_groups = build_all_groups()
    print(f"\n[build_all_groups] 構築完了: {len(all_groups)} 点群")
    for name, g in all_groups.items():
        print(f"  {name:6s} order={g.order:2d}  quotients={g.quotient_groups}")
    print("[OK] 全点群の構築成功")


def test_to_dict():
    all_groups = build_all_groups()
    d = all_groups["C3v"].to_dict()
    assert d["name"] == "C3v"
    assert d["group_type"] == "point"
    assert d["lattice"] is None
    print("[OK] to_dict() テスト成功")


if __name__ == "__main__":
    test_group_count()
    test_c3v_decomposition()
    test_apply_operation()
    test_seitz_format()
    test_build_all_groups()
    test_to_dict()
    print("\n=== フェーズ1 全テスト合格 ===")
