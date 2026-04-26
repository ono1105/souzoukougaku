/**
 * フェーズ6：分解アニメーション
 *
 * 再生順序（SPEC準拠）:
 *   Step1  0.0〜0.3s  対称要素が光って強調（Phase5のhighlight流用）
 *   Step2  0.3〜0.9s  原子が対称操作を実行するように動く
 *   Step3  0.9〜1.2s  対称要素がフェードアウト
 *   Done   1.2s〜     onComplete コールバック
 *
 * アニメーション速度係数 (speedFactor):
 *   0.5 = 遅い（2倍時間）  1.0 = 普通  2.0 = 速い（半分時間）
 */

import * as THREE from 'three';
import { hideAllSymmetryObjects } from './symmetry_elements.js';

// ── タイミング定数 (speedFactor=1 のとき) ───────────────────
const T_HIGHLIGHT = 0.30;  // Step1 持続時間
const T_MOVE      = 0.60;  // Step2 持続時間
const T_FADEOUT   = 0.30;  // Step3 持続時間

// ── イージング ───────────────────────────────────────────────
function easeInOut(t) {
  t = Math.max(0, Math.min(1, t));
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
}

// ── Seitz 操作の適用（JavaScript 側で計算）──────────────────

/**
 * 鏡映: r' = r - 2*(r·n̂)*n̂
 * @param {THREE.Vector3} pos
 * @param {number[]} normal  - [nx, ny, nz]
 */
function applyMirror(pos, normal) {
  const n   = new THREE.Vector3(...normal).normalize();
  const dot = pos.dot(n);
  return pos.clone().addScaledVector(n, -2 * dot);
}

/**
 * 回転: Rodrigues' rotation formula
 * @param {THREE.Vector3} pos
 * @param {number[]} axis   - [ax, ay, az]
 * @param {number}   order  - 回転の位数（角度 = 2π/order）
 */
function applyRotation(pos, axis, order) {
  const k    = new THREE.Vector3(...axis).normalize();
  const angle = (2 * Math.PI) / order;
  const cos  = Math.cos(angle);
  const sin  = Math.sin(angle);
  // r' = r·cos + (k×r)·sin + k·(k·r)·(1-cos)
  return pos.clone()
    .multiplyScalar(cos)
    .addScaledVector(k.clone().cross(pos), sin)
    .addScaledVector(k, k.dot(pos) * (1 - cos));
}

/**
 * 反転: r' = -r
 */
function applyInversion(pos) {
  return pos.clone().negate();
}

/**
 * 回反: まず回転、次に反転
 */
function applyRotoinversion(pos, axis, order) {
  return applyInversion(applyRotation(pos, axis, order));
}

/**
 * 対称要素の定義オブジェクトから各原子の目標座標を計算する。
 * @param {THREE.Mesh[]} atomMeshes
 * @param {object}       symmetryElement  - {type, normal?, axis?, order?}
 * @returns {THREE.Vector3[]}
 */
export function computeTargetPositions(atomMeshes, symmetryElement) {
  return atomMeshes.map(mesh => {
    const pos = mesh.position.clone();
    switch (symmetryElement.type) {
      case 'mirror':
        return applyMirror(pos, symmetryElement.normal);
      case 'rotation':
        return applyRotation(pos, symmetryElement.axis, symmetryElement.order);
      case 'inversion':
        return applyInversion(pos);
      case 'rotoinversion':
        return applyRotoinversion(pos, symmetryElement.axis, symmetryElement.order);
      default:
        return pos.clone();
    }
  });
}

// ── DecompositionAnimator ─────────────────────────────────────

export class DecompositionAnimator {
  constructor() {
    this._active     = false;
    this._time       = 0;
    this._speed      = 1.0;
    this._phase      = 'idle';  // 'highlight' | 'move' | 'fadeout' | 'idle'
    this._atomMeshes = [];
    this._bondMeshes = [];
    this._startPos   = [];
    this._targetPos  = [];
    this._symObjects = [];
    this._onComplete = null;
  }

  /**
   * アニメーションを開始する。
   * @param {THREE.Mesh[]}    atomMeshes      - 動かす原子メッシュ
   * @param {THREE.Mesh[]}    bondMeshes      - アニメーション中に隠す結合メッシュ
   * @param {THREE.Vector3[]} targetPositions - 目標座標（computeTargetPositions の結果）
   * @param {THREE.Group[]}   symObjects      - フェードアウトする対称要素グループ
   * @param {Function}        onComplete      - 完了時コールバック
   * @param {number}          speedFactor     - 速度係数（デフォルト 1.0）
   */
  play(atomMeshes, bondMeshes, targetPositions, symObjects, onComplete, speedFactor = 1.0) {
    this._active     = true;
    this._time       = 0;
    this._speed      = Math.max(0.1, speedFactor);
    this._phase      = 'highlight';
    this._atomMeshes = atomMeshes;
    this._bondMeshes = bondMeshes;
    this._startPos   = atomMeshes.map(m => m.position.clone());
    this._targetPos  = targetPositions;
    this._symObjects = symObjects;
    this._onComplete = onComplete;

    // 結合を非表示にしてアニメーション中は原子の動きに集中させる
    bondMeshes.forEach(m => { m.visible = false; });
  }

  /** レンダーループから毎フレーム呼ぶ。 */
  update(dt) {
    if (!this._active) return;

    this._time += dt * this._speed;

    const t1 = T_HIGHLIGHT;
    const t2 = t1 + T_MOVE;
    const t3 = t2 + T_FADEOUT;

    if (this._time < t1) {
      // Step1: highlight のまま待機（Phase5 のアニメーションに任せる）

    } else if (this._time < t2) {
      // Step2: 原子を動かす
      if (this._phase === 'highlight') {
        this._phase = 'move';
      }
      const progress = (this._time - t1) / T_MOVE;
      const easedT   = easeInOut(progress);
      this._atomMeshes.forEach((mesh, i) => {
        mesh.position.lerpVectors(this._startPos[i], this._targetPos[i], easedT);
      });

    } else if (this._time < t3) {
      // Step3: 対称要素フェードアウト開始（1回だけトリガー）
      if (this._phase === 'move') {
        this._phase = 'fadeout';
        // 原子を最終位置にスナップ
        this._atomMeshes.forEach((mesh, i) => {
          mesh.position.copy(this._targetPos[i]);
        });
        // Phase5 のフェードアウト機構を使う
        hideAllSymmetryObjects(this._symObjects);
      }

    } else {
      // 完了
      this._active = false;
      this._phase  = 'idle';
      this._onComplete?.();
    }
  }

  get isActive() { return this._active; }

  /** アニメーションを即時キャンセルする（他のロード時などに使う）。 */
  cancel() {
    if (!this._active) return;
    this._active = false;
    this._phase  = 'idle';
    this._bondMeshes.forEach(m => { m.visible = true; });
    hideAllSymmetryObjects(this._symObjects);
  }

  /** 速度係数を変更する（slow=0.5, normal=1.0, fast=2.0）。 */
  setSpeed(factor) {
    this._speed = Math.max(0.1, factor);
  }
}
