"""
フェーズ1のテスト。
"""

import sys, math
sys.path.insert(0, ".")

import numpy as np
from point_groups import POINT_GROUPS, list_groups, get_group
from symmetry_group import SymmetryGroup
from group_theory import get_available_quotients, apply_quotient, apply_operation, build_all_groups


def test_group_count():
    groups = list_groups()
    print(f"[OK] 定義済み点群数: {len(groups)}")
    assert len(groups) == 32, f"32種必要だが {len(groups)} 種しかない"


def test_all_32_present():
    expected = {
        "C1","Ci","Cs","C2","C2h","C2v","D2","D2h",
        "C3","C3i","C3v","D3","D3d","D3h",
        "S4","C4","C4h","C4v","D2d","D4","D4h",
        "C3h","C6","C6h","C6v","D6","D6h",
        "T","Td","Th","O","Oh",
    }
    actual = set(list_groups())
    missing = expected - actual
    extra   = actual - expected
    assert not missing, f"欠落: {missing}"
    assert not extra,   f"余分: {extra}"
    print(f"[OK] 全32点群が定義されている")


def test_c3v_decomposition():
    """C3v → C3 → C1 の分解経路テスト"""
    all_groups = build_all_groups()
    g = all_groups["C3v"]
    print(f"\n[C3v] order={g.order}, max_normal_subgroups={g.normal_subgroups}")

    qs = get_available_quotients(g)
    print(f"  商群候補: {[q['quotient_name']+'(→'+q['normal_subgroup']+')' for q in qs]}")
    assert len(qs) == 1, f"C3v の既約商群は1つのはず: {qs}"
    assert qs[0]["normal_subgroup"] == "C3", "C3v の最大正規部分群は C3"
    assert qs[0]["quotient_order"] == 2, "C3v/C3 の位数は 2"

    g2 = apply_quotient(g, "C3")
    qs2 = get_available_quotients(g2)
    print(f"  C3 → 商群候補: {[q['quotient_name'] for q in qs2]}")
    assert any(q["normal_subgroup"] == "C1" for q in qs2), "C3 → C1 の経路が必要"

    g3 = apply_quotient(g2, "C1")
    qs3 = get_available_quotients(g3)
    assert qs3 == [], f"C1 に到達後は商群なし: {qs3}"
    print("[OK] C3v → C3 → C1 の分解成功")


def test_c2h_decomposition():
    """C2h は 3通りの分解経路を持つ"""
    all_groups = build_all_groups()
    g = all_groups["C2h"]
    qs = get_available_quotients(g)
    ns_names = {q["normal_subgroup"] for q in qs}
    print(f"\n[C2h] 商群候補: {[(q['quotient_name'], q['normal_subgroup']) for q in qs]}")
    assert "C2" in ns_names, "C2h の最大正規部分群に C2 が必要"
    assert "Ci" in ns_names, "C2h の最大正規部分群に Ci が必要"
    assert "Cs" in ns_names, "C2h の最大正規部分群に Cs が必要"
    print("[OK] C2h の3通り分解経路を確認")


def test_oh_decomposition():
    """Oh の最大正規部分群は O と Th"""
    all_groups = build_all_groups()
    g = all_groups["Oh"]
    qs = get_available_quotients(g)
    ns_names = {q["normal_subgroup"] for q in qs}
    print(f"\n[Oh] order={g.order}, 商群候補: {[(q['quotient_name'], q['normal_subgroup']) for q in qs]}")
    assert "O" in ns_names,  "Oh の最大正規部分群に O が必要"
    assert "Th" in ns_names, "Oh の最大正規部分群に Th が必要"
    print("[OK] Oh → {O, Th} の分解確認")


def test_quotient_orders_are_prime():
    """全ての商群の位数が素数であることを確認"""
    PRIMES = {2, 3, 5, 7, 11, 13}
    all_groups = build_all_groups()
    problems = []
    for name, g in all_groups.items():
        for q in get_available_quotients(g):
            if q["quotient_order"] not in PRIMES:
                problems.append(f"{name}/{q['normal_subgroup']} order={q['quotient_order']}")
    if problems:
        print(f"  [FAIL] 素数でない商群: {problems}")
    assert not problems, f"素数でない商群が存在: {problems}"
    print("[OK] 全ての商群の位数が素数")


def test_seitz_format():
    """全対称操作が Seitz 形式を持つことを確認"""
    all_groups = build_all_groups()
    for name, g in all_groups.items():
        for op in g.operations:
            for key in ("rotation", "translation", "type", "axis", "label"):
                assert key in op, f"{name}: operation に '{key}' がない: {op}"
    print(f"[OK] 全点群の全対称操作が Seitz 形式を持つ")


def test_rotation_matrices_are_orthogonal():
    """回転行列が直交行列（det=±1, R^T·R=I）であることを確認"""
    all_groups = build_all_groups()
    problems = []
    for name, g in all_groups.items():
        for op in g.operations:
            R = np.array(op["rotation"], dtype=float)
            det = np.linalg.det(R)
            if abs(abs(det) - 1.0) > 1e-6:
                problems.append(f"{name}/{op['label']}: det={det:.4f}")
            err = np.max(np.abs(R.T @ R - np.eye(3)))
            if err > 1e-6:
                problems.append(f"{name}/{op['label']}: R^T·R≠I (err={err:.2e})")
    if problems:
        for p in problems[:5]:
            print(f"  [FAIL] {p}")
    assert not problems, f"直交行列でない回転行列: {len(problems)} 件"
    print("[OK] 全回転行列が直交行列")


def test_apply_operation():
    """σh (z反転) 操作の座標変換テスト"""
    from symmetry_operations import sigma_h
    coords = [[1.0, 0.5, 2.0], [0.0, 0.0, -1.5]]
    result = apply_operation(coords, sigma_h)
    assert abs(result[0][0] - 1.0) < 1e-9
    assert abs(result[0][2] - (-2.0)) < 1e-9, f"z反転失敗: {result[0][2]}"
    assert abs(result[1][2] - 1.5) < 1e-9
    print(f"[OK] apply_operation (σh): {coords} → {result}")


def test_s6_cube():
    """S6^3 = i を数値確認"""
    from symmetry_operations import S6z, i_op
    import numpy as np
    S = np.array(S6z["rotation"])
    S3 = S @ S @ S
    I = np.array(i_op["rotation"])
    err = np.max(np.abs(S3 - I))
    assert err < 1e-7, f"S6^3 ≠ i (err={err:.2e})"
    print(f"[OK] S6^3 = i (err={err:.2e})")


def test_build_all_groups():
    all_groups = build_all_groups()
    print(f"\n[全32点群サマリー]")
    for name, g in all_groups.items():
        qs = get_available_quotients(g)
        q_str = ", ".join(f"{q['quotient_name']}→{q['normal_subgroup']}" for q in qs) or "（終端）"
        print(f"  {name:6s} ({g.display_name:8s}) order={g.order:2d}  {q_str}")
    print(f"[OK] 全 {len(all_groups)} 点群を構築")


if __name__ == "__main__":
    test_group_count()
    test_all_32_present()
    test_c3v_decomposition()
    test_c2h_decomposition()
    test_oh_decomposition()
    test_quotient_orders_are_prime()
    test_seitz_format()
    test_rotation_matrices_are_orthogonal()
    test_apply_operation()
    test_s6_cube()
    test_build_all_groups()
    print("\n=== フェーズ1 全テスト合格 ===")
