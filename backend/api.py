"""
Flask REST API — フェーズ2〜3

エンドポイント一覧:
  GET  /api/groups                          利用可能な点群リスト
  GET  /api/groups/<name>                   点群の詳細情報
  GET  /api/structures                      全構造サマリー
  GET  /api/structures/<group>?mode=...     構造データ（atoms/bonds/symmetry_elements）
  POST /api/sessions                        新セッション開始
  GET  /api/sessions/<id>                   セッション状態取得
  GET  /api/sessions/<id>/quotients         現在選べる商群リスト
  POST /api/sessions/<id>/apply             商群を適用（1ステップ進む）
  POST /api/sessions/<id>/reset             初期点群にリセット
  DELETE /api/sessions/<id>                 セッション削除
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from decomposition import (
    create_session, get_session, delete_session,
    list_available_groups, _ALL_GROUPS,
)
from crystal_structures import get_structure, list_structures

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

@app.get('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


def _err(message: str, status: int = 400):
    return jsonify({"error": message}), status


# ── 点群情報 ──────────────────────────────────────────────────

@app.get("/api/groups")
def api_list_groups():
    return jsonify(list_available_groups())


@app.get("/api/groups/<name>")
def api_get_group(name: str):
    if name not in _ALL_GROUPS:
        return _err(f"Unknown point group: {name}", 404)
    return jsonify(_ALL_GROUPS[name].to_dict())


# ── セッション CRUD ───────────────────────────────────────────

@app.post("/api/sessions")
def api_create_session():
    body = request.get_json(silent=True) or {}
    group_name = body.get("group")
    if not group_name:
        return _err("'group' field is required")
    try:
        session_id, session = create_session(group_name)
    except ValueError as e:
        return _err(str(e))
    return jsonify({"session_id": session_id, **session.to_dict()}), 201


@app.get("/api/sessions/<session_id>")
def api_get_session(session_id: str):
    try:
        session = get_session(session_id)
    except KeyError:
        return _err("Session not found", 404)
    return jsonify({"session_id": session_id, **session.to_dict()})


@app.delete("/api/sessions/<session_id>")
def api_delete_session(session_id: str):
    delete_session(session_id)
    return "", 204


# ── 分解操作 ──────────────────────────────────────────────────

@app.get("/api/sessions/<session_id>/quotients")
def api_get_quotients(session_id: str):
    try:
        session = get_session(session_id)
    except KeyError:
        return _err("Session not found", 404)
    return jsonify({
        "current_group": session.current_group.name,
        "quotients":     session.get_available_quotients(),
        "is_complete":   session.is_complete,
    })


@app.post("/api/sessions/<session_id>/apply")
def api_apply_quotient(session_id: str):
    try:
        session = get_session(session_id)
    except KeyError:
        return _err("Session not found", 404)

    body = request.get_json(silent=True) or {}
    normal_subgroup = body.get("normal_subgroup")
    if not normal_subgroup:
        return _err("'normal_subgroup' field is required")

    try:
        step = session.apply(normal_subgroup)
    except (ValueError, RuntimeError) as e:
        return _err(str(e))

    return jsonify({
        "session_id":  session_id,
        "step":        step.to_dict(),
        "session":     session.to_dict(),
    })


@app.post("/api/sessions/<session_id>/reset")
def api_reset_session(session_id: str):
    try:
        session = get_session(session_id)
    except KeyError:
        return _err("Session not found", 404)
    session.reset()
    return jsonify({"session_id": session_id, **session.to_dict()})


# ── 構造データ ────────────────────────────────────────────────

@app.get("/api/structures")
def api_list_structures():
    mode = request.args.get("mode")  # optional: "real" or "abstract"
    return jsonify(list_structures(mode))


@app.get("/api/structures/<group_name>")
def api_get_structure(group_name: str):
    mode = request.args.get("mode", "abstract")
    try:
        return jsonify(get_structure(group_name, mode))
    except ValueError as e:
        return _err(str(e), 404)


# ── ヘルスチェック ─────────────────────────────────────────────

@app.get("/api/health")
def api_health():
    return jsonify({"status": "ok", "groups": len(_ALL_GROUPS)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
