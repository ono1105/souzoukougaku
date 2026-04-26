/**
 * 対称要素の 3D 表示オブジェクト生成
 *
 * createSymmetryObjects(elements, size) → THREE.Group[]
 *   各 Group を scene に add/remove して表示・非表示を切り替える。
 *
 * 表示スタイル（SPEC準拠）:
 *   mirror   → 青い半透明の板
 *   rotation → オレンジの輝く線＋矢印
 *   inversion→ 白い小球
 */

import * as THREE from 'three';

const MIRROR_COLOR    = 0x4499ff;
const ROTATION_COLOR  = 0xff9944;
const INVERSION_COLOR = 0xffffff;
const ROTIN_COLOR     = 0xcc88ff;

// ── ユーティリティ ────────────────────────────────────────────

/** デフォルト上方向 (0,1,0) からターゲットベクトルへの回転を mesh に適用 */
function alignYToVector(mesh, target) {
  const up = new THREE.Vector3(0, 1, 0);
  const dir = new THREE.Vector3(...target).normalize();
  if (dir.lengthSq() < 1e-10) return;
  // 平行または反平行のエッジケース
  if (Math.abs(up.dot(dir) + 1) < 1e-6) {
    mesh.quaternion.setFromAxisAngle(new THREE.Vector3(1, 0, 0), Math.PI);
  } else {
    mesh.quaternion.setFromUnitVectors(up, dir);
  }
}

/** デフォルト法線 (0,0,1) からターゲット法線へ Plane を回転 */
function alignNormalToVector(mesh, normal) {
  const defaultN = new THREE.Vector3(0, 0, 1);
  const target = new THREE.Vector3(...normal).normalize();
  if (target.lengthSq() < 1e-10) return;
  if (Math.abs(defaultN.dot(target) + 1) < 1e-6) {
    mesh.quaternion.setFromAxisAngle(new THREE.Vector3(1, 0, 0), Math.PI);
  } else {
    mesh.quaternion.setFromUnitVectors(defaultN, target);
  }
}

// ── 鏡映面 ───────────────────────────────────────────────────

function createMirrorPlane(normal, size) {
  const group = new THREE.Group();

  // 半透明の板
  const planeGeo = new THREE.PlaneGeometry(size, size);
  const planeMat = new THREE.MeshBasicMaterial({
    color: MIRROR_COLOR,
    transparent: true,
    opacity: 0.22,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const plane = new THREE.Mesh(planeGeo, planeMat);
  alignNormalToVector(plane, normal);
  group.add(plane);

  // 枠線
  const edgeGeo = new THREE.EdgesGeometry(new THREE.PlaneGeometry(size, size));
  const edgeMat = new THREE.LineBasicMaterial({ color: MIRROR_COLOR, opacity: 0.6, transparent: true });
  const edge = new THREE.LineSegments(edgeGeo, edgeMat);
  alignNormalToVector(edge, normal);
  group.add(edge);

  group.visible = false;
  group.userData = { type: 'mirror', normal };
  return group;
}

// ── 回転軸 ───────────────────────────────────────────────────

function createArrowHead(radius, height, color) {
  const geo = new THREE.ConeGeometry(radius, height, 12);
  const mat = new THREE.MeshBasicMaterial({ color });
  return new THREE.Mesh(geo, mat);
}

function createRotationAxis(axis, order, length, color = ROTATION_COLOR) {
  const group = new THREE.Group();
  const halfLen = length / 2;
  const r = 0.03;

  // 軸の線（細いシリンダー）
  const shaftGeo = new THREE.CylinderGeometry(r, r, length, 8);
  const shaftMat = new THREE.MeshBasicMaterial({ color });
  const shaft = new THREE.Mesh(shaftGeo, shaftMat);
  group.add(shaft);

  // 両端の矢印
  const arrowH = 0.18, arrowR = 0.075;
  const topArrow = createArrowHead(arrowR, arrowH, color);
  topArrow.position.y = halfLen + arrowH / 2;
  group.add(topArrow);

  const botArrow = createArrowHead(arrowR, arrowH, color);
  botArrow.rotation.z = Math.PI;
  botArrow.position.y = -(halfLen + arrowH / 2);
  group.add(botArrow);

  // order ラベル（回転位数の表示はPhase 5で拡張、今は色で区別）
  alignYToVector(group, axis);
  group.visible = false;
  group.userData = { type: 'rotation', axis, order };
  return group;
}

// ── 反転中心 ─────────────────────────────────────────────────

function createInversionCenter() {
  const geo = new THREE.SphereGeometry(0.12, 16, 12);
  const mat = new THREE.MeshBasicMaterial({ color: INVERSION_COLOR, opacity: 0.8, transparent: true });
  const mesh = new THREE.Mesh(geo, mat);
  const group = new THREE.Group();
  group.add(mesh);
  group.visible = false;
  group.userData = { type: 'inversion' };
  return group;
}

// ── 回反軸 ───────────────────────────────────────────────────

function createRotoinversionAxis(axis, order, length) {
  // 回反軸は紫色で表示（回転軸と区別）
  return createRotationAxis(axis, order, length, ROTIN_COLOR);
}

// ── 公開 API ─────────────────────────────────────────────────

/**
 * 構造データの symmetry_elements から Three.js Group の配列を生成する。
 * @param {Array}  elements  - crystal_structures.py の symmetry_elements フィールド
 * @param {number} size      - 分子の大きさ（鏡映面・軸の長さのスケール基準）
 * @returns {THREE.Group[]}
 */
export function createSymmetryObjects(elements, size = 3.0) {
  const planeSize = Math.max(size * 1.8, 2.5);
  const axisLen   = Math.max(size * 2.0, 3.0);

  return elements.map(elem => {
    switch (elem.type) {
      case 'mirror':
        return createMirrorPlane(elem.normal, planeSize);
      case 'rotation':
        return createRotationAxis(elem.axis, elem.order, axisLen);
      case 'inversion':
        return createInversionCenter();
      case 'rotoinversion':
        return createRotoinversionAxis(elem.axis, elem.order, axisLen);
      default:
        return new THREE.Group(); // unknown type → empty group
    }
  });
}

/**
 * op_types（["mirror"], ["rotation"] など）から
 * 対応する symmetry objects を表示する。
 */
export function highlightByOpTypes(symObjects, elements, opTypes) {
  symObjects.forEach((obj, i) => {
    const elem = elements[i];
    obj.visible = opTypes.includes(elem?.type);
  });
}

export function hideAllSymmetryObjects(symObjects) {
  symObjects.forEach(obj => { obj.visible = false; });
}
