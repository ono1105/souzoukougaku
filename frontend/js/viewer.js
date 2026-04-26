/**
 * CrystalViewer — Three.js 3D ビューア
 *
 * Phase 6 変更点:
 *   - _atomMeshes / _bondMeshes を個別にトラック
 *   - DecompositionAnimator を統合
 *   - playDecompositionAnimation(opTypes, onComplete, speedFactor) を追加
 *   - _startLoop に animator.update(dt) を追加
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { getColor, getRadius } from './element_data.js';
import {
  createSymmetryObjects,
  highlightByOpTypes,
  hideAllSymmetryObjects,
  showAllSymmetryObjects,
  updateSymmetryAnimations,
} from './symmetry_elements.js';
import { computeTargetPositions, DecompositionAnimator } from './animator.js';

export class CrystalViewer {
  constructor(container) {
    this.container      = container;
    this._structureGroup = new THREE.Group();
    this._symmetryGroup  = new THREE.Group();
    this._symObjects     = [];
    this._symElements    = [];
    this._atomMeshes     = [];   // ← Phase 6: 個別トラック
    this._bondMeshes     = [];   // ← Phase 6: 個別トラック
    this._moleculeSize   = 3.0;
    this._clock          = new THREE.Clock();
    this._animator       = new DecompositionAnimator();  // ← Phase 6

    this._initRenderer();
    this._initScene();
    this._initCamera();
    this._initLights();
    this._initControls();
    this._startLoop();
    this._handleResize();
  }

  // ── 初期化 ─────────────────────────────────────────────────

  _initRenderer() {
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setClearColor(0x0d0d1a, 1);
    this.renderer.shadowMap.enabled = false;
    const { width, height } = this.container.getBoundingClientRect();
    this.renderer.setSize(width || 800, height || 600);
    this.container.appendChild(this.renderer.domElement);
  }

  _initScene() {
    this.scene = new THREE.Scene();
    this.scene.add(this._structureGroup);
    this.scene.add(this._symmetryGroup);
  }

  _initCamera() {
    const { width, height } = this.container.getBoundingClientRect();
    this.camera = new THREE.PerspectiveCamera(
      45, (width || 800) / (height || 600), 0.01, 500
    );
    this.camera.position.set(0, 0, 8);
  }

  _initLights() {
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.45));
    const main = new THREE.DirectionalLight(0xffffff, 1.1);
    main.position.set(5, 8, 6);
    this.scene.add(main);
    const fill = new THREE.DirectionalLight(0x8899cc, 0.4);
    fill.position.set(-5, -3, -4);
    this.scene.add(fill);
  }

  _initControls() {
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance   = 0.5;
    this.controls.maxDistance   = 100;
    this.controls.enablePan     = true;
    this.controls.rotateSpeed   = 0.8;
    this.controls.zoomSpeed     = 1.2;
  }

  _startLoop() {
    this._clock.start();
    const animate = () => {
      requestAnimationFrame(animate);
      const dt = Math.min(this._clock.getDelta(), 0.1);
      this.controls.update();
      updateSymmetryAnimations(this._symObjects, dt);
      this._animator.update(dt);                     // ← Phase 6
      this.renderer.render(this.scene, this.camera);
    };
    animate();
  }

  _handleResize() {
    const ro = new ResizeObserver(() => this.resize());
    ro.observe(this.container);
  }

  resize() {
    const { width, height } = this.container.getBoundingClientRect();
    if (width === 0 || height === 0) return;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  // ── 構造ロード ─────────────────────────────────────────────

  loadStructure(structData) {
    // 実行中のアニメーションをキャンセル
    this._animator.cancel();

    this._clearStructure();
    const atoms = structData.atoms ?? [];
    const bonds = structData.bonds ?? [];

    const posMap = {};
    atoms.forEach(a => { posMap[a.id] = a.position; });

    // 原子球
    const geoCache = {};
    atoms.forEach(atom => {
      const r = getRadius(atom.element);
      if (!geoCache[r]) geoCache[r] = new THREE.SphereGeometry(r, 24, 16);
      const mat  = new THREE.MeshStandardMaterial({
        color: getColor(atom.element),
        roughness: 0.55,
        metalness: 0.10,
      });
      const mesh = new THREE.Mesh(geoCache[r], mat);
      mesh.position.set(...atom.position);
      mesh.userData = { atomId: atom.id, element: atom.element };
      this._structureGroup.add(mesh);
      this._atomMeshes.push(mesh);  // ← Phase 6
    });

    // 結合シリンダー
    const bondMat = new THREE.MeshStandardMaterial({
      color: 0x999999, roughness: 0.8, metalness: 0.0
    });
    bonds.forEach(bond => {
      const aPos = posMap[bond.from];
      const bPos = posMap[bond.to];
      if (!aPos || !bPos) return;
      const mesh = this._makeBond(aPos, bPos, bondMat);
      this._structureGroup.add(mesh);
      this._bondMeshes.push(mesh);  // ← Phase 6
    });

    this._fitCamera();

    const elements = structData.symmetry_elements ?? [];
    this.setSymmetryElements(elements);
  }

  _makeBond(aPos, bPos, mat) {
    const start = new THREE.Vector3(...aPos);
    const end   = new THREE.Vector3(...bPos);
    const dir   = end.clone().sub(start);
    const len   = dir.length();
    const mid   = start.clone().add(dir.clone().multiplyScalar(0.5));
    const geo   = new THREE.CylinderGeometry(0.045, 0.045, len, 8);
    const mesh  = new THREE.Mesh(geo, mat.clone());
    mesh.position.copy(mid);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
    return mesh;
  }

  _fitCamera() {
    const box = new THREE.Box3().setFromObject(this._structureGroup);
    if (box.isEmpty()) return;

    const center = box.getCenter(new THREE.Vector3());
    const size   = box.getSize(new THREE.Vector3());
    this._moleculeSize = size.length();

    const maxDim = Math.max(size.x, size.y, size.z, 0.1);
    const fovRad = this.camera.fov * (Math.PI / 180);
    const dist   = (maxDim / 2) / Math.tan(fovRad / 2) * 2.8;

    this.camera.position.set(center.x, center.y, center.z + dist);
    this.camera.near = dist / 200;
    this.camera.far  = dist * 50;
    this.camera.updateProjectionMatrix();
    this.controls.target.copy(center);
    this.controls.update();
  }

  _clearStructure() {
    this._structureGroup.clear();
    this._symmetryGroup.clear();
    this._symObjects  = [];
    this._symElements = [];
    this._atomMeshes  = [];  // ← Phase 6
    this._bondMeshes  = [];  // ← Phase 6
  }

  // ── 対称要素 API ───────────────────────────────────────────

  setSymmetryElements(elements) {
    this._symmetryGroup.clear();
    this._symElements = elements;
    this._symObjects  = createSymmetryObjects(elements, this._moleculeSize);
    this._symObjects.forEach(obj => this._symmetryGroup.add(obj));
  }

  highlightSymmetryByOpTypes(opTypes) {
    highlightByOpTypes(this._symObjects, this._symElements, opTypes);
  }

  hideAllSymmetry() {
    hideAllSymmetryObjects(this._symObjects);
  }

  showAllSymmetry() {
    showAllSymmetryObjects(this._symObjects);
  }

  // ── Phase 6: 分解アニメーション ────────────────────────────

  /**
   * 商群適用アニメーションを再生する。
   *
   * @param {string[]}  opTypes      - 商群の op_types（例: ["mirror"]）
   * @param {Function}  onComplete   - アニメーション完了後に呼ぶコールバック
   * @param {number}    speedFactor  - 速度係数（0.5=遅い, 1.0=普通, 2.0=速い）
   */
  playDecompositionAnimation(opTypes, onComplete, speedFactor = 1.0) {
    // 対応する対称要素を検索
    const elemIndex = this._symElements.findIndex(e => opTypes.includes(e.type));

    if (elemIndex < 0 || this._atomMeshes.length === 0) {
      // 対応する対称要素がない、または原子がない → スキップしてすぐ完了
      hideAllSymmetryObjects(this._symObjects);
      onComplete?.();
      return;
    }

    const element = this._symElements[elemIndex];
    const targets = computeTargetPositions(this._atomMeshes, element);

    // 対称要素をハイライト
    this.highlightSymmetryByOpTypes(opTypes);

    this._animator.play(
      this._atomMeshes,
      this._bondMeshes,
      targets,
      this._symObjects,
      onComplete,
      speedFactor,
    );
  }

  get isAnimating() {
    return this._animator.isActive;
  }

  setAnimationSpeed(factor) {
    this._animator.setSpeed(factor);
  }

  // ── その他 ────────────────────────────────────────────────

  resetCamera() { this._fitCamera(); }

  dispose() {
    this.renderer.dispose();
    this.controls.dispose();
  }
}
