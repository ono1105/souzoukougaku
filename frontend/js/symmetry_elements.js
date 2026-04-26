/**
 * 対称要素の 3D 表示オブジェクト生成 + フェード・パルスアニメーション
 *
 * Phase 4 からの変更点:
 *   - 全マテリアルを transparent:true にして opacity をアニメーション制御
 *   - setHighlighted(group, bool) で対象フェードイン/アウトをスケジュール
 *   - updateSymmetryAnimations(groups, dt) をレンダーループから毎フレーム呼ぶ
 *   - ホバー時はパルス（緩やかな輝き）を追加
 *
 * 表示スタイル（SPEC準拠）:
 *   mirror      → 青い半透明の板（強調時: opacity ↑, パルス）
 *   rotation    → オレンジの矢印付き線（強調時: 明るさ ↑, パルス）
 *   inversion   → 白い小球（強調時: パルス）
 *   rotoinversion → 紫の矢印付き線
 */

import * as THREE from 'three';

// ── カラー定数 ─────────────────────────────────────────────────
const MIRROR_COLOR    = 0x4499ff;
const ROTATION_COLOR  = 0xff9944;
const INVERSION_COLOR = 0xffffff;
const ROTIN_COLOR     = 0xcc88ff;

// アニメーション速度
const FADE_IN_SPEED  = 10.0;  // 1/sec → ~100ms でほぼ到達
const FADE_OUT_SPEED =  7.0;  // ~150ms でほぼ到達
const PULSE_SPEED    =  3.0;  // Hz 相当
const PULSE_AMOUNT   =  0.18; // 振れ幅 (0〜1)

// ── ユーティリティ ────────────────────────────────────────────

function alignYToVector(group, target) {
  const up  = new THREE.Vector3(0, 1, 0);
  const dir = new THREE.Vector3(...target).normalize();
  if (dir.lengthSq() < 1e-10) return;
  if (Math.abs(up.dot(dir) + 1) < 1e-6) {
    group.quaternion.setFromAxisAngle(new THREE.Vector3(1, 0, 0), Math.PI);
  } else {
    group.quaternion.setFromUnitVectors(up, dir);
  }
}

function alignNormalToVector(mesh, normal) {
  const defaultN = new THREE.Vector3(0, 0, 1);
  const target   = new THREE.Vector3(...normal).normalize();
  if (target.lengthSq() < 1e-10) return;
  if (Math.abs(defaultN.dot(target) + 1) < 1e-6) {
    mesh.quaternion.setFromAxisAngle(new THREE.Vector3(1, 0, 0), Math.PI);
  } else {
    mesh.quaternion.setFromUnitVectors(defaultN, target);
  }
}

/**
 * マテリアルを登録し、baseOpacity を userData に保存する。
 * 全マテリアルを transparent:true にすることで opacity アニメーションを可能にする。
 */
function _registerMat(mesh, baseOpacity) {
  const mat = mesh.material;
  mat.transparent = true;
  mat.opacity = 0.0;          // 初期は完全透明（フェードインで表示）
  mat.depthWrite = false;
  mesh.userData.baseOpacity = baseOpacity;
}

// ── 鏡映面 ───────────────────────────────────────────────────

function createMirrorPlane(normal, size) {
  const group = new THREE.Group();

  const planeGeo = new THREE.PlaneGeometry(size, size);
  const planeMat = new THREE.MeshBasicMaterial({
    color: MIRROR_COLOR,
    side: THREE.DoubleSide,
  });
  const plane = new THREE.Mesh(planeGeo, planeMat);
  alignNormalToVector(plane, normal);
  _registerMat(plane, 0.28);   // 強調時の最大不透明度
  group.add(plane);

  const edgeGeo = new THREE.EdgesGeometry(new THREE.PlaneGeometry(size, size));
  const edgeMat = new THREE.LineBasicMaterial({ color: MIRROR_COLOR });
  const edge    = new THREE.LineSegments(edgeGeo, edgeMat);
  alignNormalToVector(edge, normal);
  _registerMat(edge, 0.85);
  group.add(edge);

  _initAnim(group, 'mirror');
  return group;
}

// ── 回転軸 ───────────────────────────────────────────────────

function _makeArrowHead(radius, height, color) {
  const geo  = new THREE.ConeGeometry(radius, height, 12);
  const mat  = new THREE.MeshBasicMaterial({ color });
  const mesh = new THREE.Mesh(geo, mat);
  _registerMat(mesh, 1.0);
  return mesh;
}

function createRotationAxis(axis, order, length, color = ROTATION_COLOR) {
  const group   = new THREE.Group();
  const halfLen = length / 2;

  const shaftGeo = new THREE.CylinderGeometry(0.03, 0.03, length, 8);
  const shaftMat = new THREE.MeshBasicMaterial({ color });
  const shaft    = new THREE.Mesh(shaftGeo, shaftMat);
  _registerMat(shaft, 1.0);
  group.add(shaft);

  const arrowH = 0.18, arrowR = 0.075;
  const topArrow = _makeArrowHead(arrowR, arrowH, color);
  topArrow.position.y = halfLen + arrowH / 2;
  group.add(topArrow);

  const botArrow = _makeArrowHead(arrowR, arrowH, color);
  botArrow.rotation.z = Math.PI;
  botArrow.position.y = -(halfLen + arrowH / 2);
  group.add(botArrow);

  alignYToVector(group, axis);
  _initAnim(group, 'rotation');
  return group;
}

// ── 反転中心 ─────────────────────────────────────────────────

function createInversionCenter() {
  const geo  = new THREE.SphereGeometry(0.14, 16, 12);
  const mat  = new THREE.MeshBasicMaterial({ color: INVERSION_COLOR });
  const mesh = new THREE.Mesh(geo, mat);
  _registerMat(mesh, 0.9);

  const group = new THREE.Group();
  group.add(mesh);
  _initAnim(group, 'inversion');
  return group;
}

// ── 回反軸 ───────────────────────────────────────────────────

function createRotoinversionAxis(axis, order, length) {
  const group = createRotationAxis(axis, order, length, ROTIN_COLOR);
  group.userData.elemType = 'rotoinversion';
  return group;
}

// ── アニメーション状態 ────────────────────────────────────────

/**
 * Group に _anim 状態を付与する。
 * _anim = { t, target, phase, elemType }
 *   t      : 現在のフェード値 [0,1]（0=透明、1=最大不透明）
 *   target : 目標フェード値
 *   phase  : パルス位相 (radians)
 *   elemType: 'mirror' | 'rotation' | 'inversion' | 'rotoinversion'
 */
function _initAnim(group, elemType) {
  group.visible = true;  // 常に visible=true、opacity で制御
  group._anim = { t: 0.0, target: 0.0, phase: 0.0, elemType };
  // 全子メッシュの opacity を 0 に設定（_registerMat 済み）
}

// ── 公開 API ─────────────────────────────────────────────────

/**
 * 構造データの symmetry_elements から Three.js Group の配列を生成する。
 */
export function createSymmetryObjects(elements, size = 3.0) {
  const planeSize = Math.max(size * 1.8, 2.5);
  const axisLen   = Math.max(size * 2.0, 3.0);

  return elements.map(elem => {
    switch (elem.type) {
      case 'mirror':        return createMirrorPlane(elem.normal, planeSize);
      case 'rotation':      return createRotationAxis(elem.axis, elem.order, axisLen);
      case 'inversion':     return createInversionCenter();
      case 'rotoinversion': return createRotoinversionAxis(elem.axis, elem.order, axisLen);
      default:              { const g = new THREE.Group(); _initAnim(g, 'unknown'); return g; }
    }
  });
}

/**
 * 指定 group を強調 (highlighted=true) またはフェードアウト (false) にセットする。
 * 実際の描画変化は updateSymmetryAnimations() が毎フレーム反映する。
 */
export function setHighlighted(group, highlighted) {
  if (!group._anim) return;
  group._anim.target = highlighted ? 1.0 : 0.0;
  if (highlighted) group._anim.phase = 0.0; // パルスを先頭からスタート
}

/**
 * op_types 配列に一致する要素を強調し、それ以外をフェードアウトする。
 * Phase 5 のホバーイベントから呼ぶ。
 */
export function highlightByOpTypes(symObjects, elements, opTypes) {
  symObjects.forEach((obj, i) => {
    const match = opTypes.includes(elements[i]?.type);
    setHighlighted(obj, match);
  });
}

/** 全要素をフェードアウトする。 */
export function hideAllSymmetryObjects(symObjects) {
  symObjects.forEach(obj => setHighlighted(obj, false));
}

/** 全要素をフェードインする（デバッグ・テスト用）。 */
export function showAllSymmetryObjects(symObjects) {
  symObjects.forEach(obj => setHighlighted(obj, true));
}

/**
 * レンダーループから毎フレーム呼ぶ。
 * フェード補間 + パルスを全 symObjects に適用する。
 * @param {THREE.Group[]} symObjects
 * @param {number}        dt  - 前フレームからの経過秒
 */
export function updateSymmetryAnimations(symObjects, dt) {
  symObjects.forEach(obj => {
    const anim = obj._anim;
    if (!anim) return;

    // フェード補間（ターゲット方向へ lerp）
    const speed = anim.target > 0 ? FADE_IN_SPEED : FADE_OUT_SPEED;
    anim.t += (anim.target - anim.t) * Math.min(1.0, dt * speed);

    // パルス（ホバー中のみ）
    let pulse = 1.0;
    if (anim.target > 0.5 && anim.t > 0.05) {
      anim.phase += dt * PULSE_SPEED;
      pulse = 1.0 + PULSE_AMOUNT * Math.sin(anim.phase);
    }

    // 子メッシュに opacity 反映
    obj.traverse(child => {
      if (!child.isMesh && child.type !== 'LineSegments') return;
      const mat = child.material;
      if (!mat) return;
      const base = child.userData.baseOpacity ?? 1.0;
      mat.opacity = Math.min(1.0, anim.t * base * pulse);
      // 完全に透明なら描画コストをゼロにしない（opacity 制御で十分）
    });
  });
}
