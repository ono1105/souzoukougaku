"""
フェーズ2のテスト: DecompositionSession と Flask API
"""

import sys
sys.path.insert(0, ".")

from decomposition import (
    DecompositionSession, create_session, get_session, delete_session,
    list_available_groups,
)


# ── DecompositionSession テスト ───────────────────────────────

def test_session_c3v_full():
    """C3v → C3 → C1 の完全分解"""
    session = DecompositionSession("C3v")
    assert session.initial_group_name == "C3v"
    assert session.current_group.name == "C3v"
    assert not session.is_complete

    qs = session.get_available_quotients()
    assert len(qs) == 1
    assert qs[0]["normal_subgroup"] == "C3"

    step1 = session.apply("C3")
    assert step1.from_group == "C3v"
    assert step1.to_group == "C3"
    assert step1.quotient_symbol == "Cs"
    assert session.current_group.name == "C3"
    assert not session.is_complete

    step2 = session.apply("C1")
    assert step2.from_group == "C3"
    assert step2.to_group == "C1"
    assert step2.quotient_symbol == "C3"
    assert session.is_complete

    assert session.composition_factors == ["Cs", "C3"]
    assert session.decomposition_path == ["C3v", "C3", "C1"]
    assert len(session.history) == 2
    print("[OK] C3v full decomposition: factors =", session.composition_factors)


def test_session_c2h_branch():
    """C2h の3通りの分解経路"""
    for ns in ["C2", "Ci", "Cs"]:
        session = DecompositionSession("C2h")
        step = session.apply(ns)
        assert step.from_group == "C2h"
        assert step.to_group == ns
        assert not session.is_complete
        print(f"  C2h→{ns}: quotient={step.quotient_symbol}")
    print("[OK] C2h の3通り分岐確認")


def test_session_oh_deep():
    """Oh の完全分解（Oh→O→T→D2→C2→C1）"""
    session = DecompositionSession("Oh")
    path = []
    for ns in ["O", "T", "D2", "C2", "C1"]:
        qs = session.get_available_quotients()
        ns_names = [q["normal_subgroup"] for q in qs]
        assert ns in ns_names, f"Expected {ns} in {ns_names}"
        step = session.apply(ns)
        path.append(step.quotient_symbol)

    assert session.is_complete
    print("[OK] Oh full decomposition: factors =", path)
    print("     path =", session.decomposition_path)


def test_session_invalid_apply():
    """無効な正規部分群を指定するとエラー"""
    session = DecompositionSession("C3v")
    try:
        session.apply("D2h")  # C3v の正規部分群でない
        assert False, "例外が発生すべき"
    except ValueError as e:
        print(f"[OK] 無効な apply でエラー: {e}")


def test_session_apply_when_complete():
    """C1 に到達後に apply するとエラー"""
    session = DecompositionSession("C1")
    assert session.is_complete
    try:
        session.apply("C1")
        assert False, "例外が発生すべき"
    except RuntimeError as e:
        print(f"[OK] 完了後の apply でエラー: {e}")


def test_session_reset():
    """リセットで初期状態に戻る"""
    session = DecompositionSession("C3v")
    session.apply("C3")
    session.apply("C1")
    assert session.is_complete
    session.reset()
    assert session.current_group.name == "C3v"
    assert not session.is_complete
    assert session.history == []
    assert session.composition_factors == []
    print("[OK] リセット確認")


def test_session_to_dict():
    """to_dict の構造確認"""
    session = DecompositionSession("C3v")
    session.apply("C3")
    d = session.to_dict()
    assert d["initial_group"] == "C3v"
    assert d["step_count"] == 1
    assert len(d["history"]) == 1
    assert d["composition_factors"] == ["Cs"]
    assert d["is_complete"] == False
    assert "available_quotients" in d
    assert "current_group" in d
    print("[OK] to_dict 構造確認")


def test_session_store():
    """セッションストアの CRUD"""
    sid, session = create_session("C2v")
    assert sid
    retrieved = get_session(sid)
    assert retrieved is session
    delete_session(sid)
    try:
        get_session(sid)
        assert False
    except KeyError:
        pass
    print("[OK] セッションストア CRUD 確認")


def test_list_groups():
    """list_available_groups の構造確認"""
    groups = list_available_groups()
    assert len(groups) == 32
    names = {g["name"] for g in groups}
    assert "C3v" in names
    assert "Oh" in names
    for g in groups:
        assert "name" in g and "order" in g and "system" in g
    print(f"[OK] list_available_groups: {len(groups)} groups")


# ── Flask API テスト ──────────────────────────────────────────

def test_flask_api():
    """Flask テストクライアントでエンドポイントを確認"""
    import json
    from api import app
    client = app.test_client()

    # Health
    r = client.get("/api/health")
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data["status"] == "ok"
    assert data["groups"] == 32
    print("[OK] GET /api/health")

    # List groups
    r = client.get("/api/groups")
    assert r.status_code == 200
    groups = json.loads(r.data)
    assert len(groups) == 32
    print("[OK] GET /api/groups")

    # Get group detail
    r = client.get("/api/groups/C3v")
    assert r.status_code == 200
    g = json.loads(r.data)
    assert g["name"] == "C3v"
    assert g["order"] == 6
    print("[OK] GET /api/groups/C3v")

    # Unknown group
    r = client.get("/api/groups/UNKNOWN")
    assert r.status_code == 404
    print("[OK] GET /api/groups/UNKNOWN → 404")

    # Create session
    r = client.post("/api/sessions",
                    data=json.dumps({"group": "C3v"}),
                    content_type="application/json")
    assert r.status_code == 201
    session_data = json.loads(r.data)
    sid = session_data["session_id"]
    assert session_data["initial_group"] == "C3v"
    assert not session_data["is_complete"]
    print(f"[OK] POST /api/sessions → session_id={sid[:8]}...")

    # Get session
    r = client.get(f"/api/sessions/{sid}")
    assert r.status_code == 200
    print("[OK] GET /api/sessions/{id}")

    # Get quotients
    r = client.get(f"/api/sessions/{sid}/quotients")
    assert r.status_code == 200
    qs = json.loads(r.data)
    assert qs["current_group"] == "C3v"
    assert len(qs["quotients"]) == 1
    assert qs["quotients"][0]["normal_subgroup"] == "C3"
    print("[OK] GET /api/sessions/{id}/quotients")

    # Apply quotient
    r = client.post(f"/api/sessions/{sid}/apply",
                    data=json.dumps({"normal_subgroup": "C3"}),
                    content_type="application/json")
    assert r.status_code == 200
    result = json.loads(r.data)
    assert result["step"]["from_group"] == "C3v"
    assert result["step"]["to_group"] == "C3"
    assert result["session"]["current_group"]["name"] == "C3"
    print("[OK] POST /api/sessions/{id}/apply")

    # Apply invalid
    r = client.post(f"/api/sessions/{sid}/apply",
                    data=json.dumps({"normal_subgroup": "D2h"}),
                    content_type="application/json")
    assert r.status_code == 400
    print("[OK] POST /api/sessions/{id}/apply (invalid) → 400")

    # Reset
    r = client.post(f"/api/sessions/{sid}/reset")
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data["current_group"]["name"] == "C3v"
    assert data["step_count"] == 0
    print("[OK] POST /api/sessions/{id}/reset")

    # Delete
    r = client.delete(f"/api/sessions/{sid}")
    assert r.status_code == 204
    r = client.get(f"/api/sessions/{sid}")
    assert r.status_code == 404
    print("[OK] DELETE /api/sessions/{id}")


if __name__ == "__main__":
    test_session_c3v_full()
    test_session_c2h_branch()
    test_session_oh_deep()
    test_session_invalid_apply()
    test_session_apply_when_complete()
    test_session_reset()
    test_session_to_dict()
    test_session_store()
    test_list_groups()
    test_flask_api()
    print("\n=== フェーズ2 全テスト合格 ===")
