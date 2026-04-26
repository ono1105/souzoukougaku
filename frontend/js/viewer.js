/**
 * CrystalViewer — Three.js 3D ビューア
 *
 * 使い方:
 *   const viewer = new CrystalViewer(containerElement);
 *   viewer.loadStructure(structData);          // atoms + bonds を描画
 *   viewer.setSymmetryElements(elements);      // 対称要素をセット（非表示）
 *   viewer.showSymmetryByOpTypes(['mirror']);   // hover 時に表示（Phase 5）
 *   viewer.hideAllSymmetry();                  // 全て非表示
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { getColor, getRadius } from './element_data.js';
import { createSymmetryObjects, highlightByOpTypes, hideAllSymmetryObjects } from './symmetry_elements.js';

export class CrystalViewer {
  constructor(container) {
    this.container = container;
    this._structureGroup   = new THREE.Group();
    this._symmetryGroup    = new THREE.Group();
    this._symObjects       = [];   // THREE.Group[] 対称要素ごと
    this._symElements      = [];   // raw element defs（op_types 参照用）
    this._moleculeSize     = 3.0;

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
    this.camera = new THREE.PerspectiveCamera(45, (width || 800) / (height || 600), 0.01, 500);
    this.camera.position.set(0, 0, 8);
  }

  _initLights() {
    // Ambient: 暗め（対称要素が見えるように）
    const ambient = new THREE.AmbientLight(0xffffff, 0.45);
    this.scene.add(ambient);

    // メインライト（斜め上から）
    const main = new THREE.DirectionalLight(0xffffff, 1.1);
    main.position.set(5, 8, 6);
    this.scene.add(main);

    // フィルライト（反対側から柔らかく）
    const fill = new THREE.DirectionalLight(0x8899cc, 0.4);
    fill.position.set(-5, -3, -4);
    this.scene.add(fill);
  }

  _initControls() {
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 1;
    this.controls.maxDistance = 100;
    this.controls.enablePan = true;
    this.controls.rotateSpeed = 0.8;
    this.controls.zoomSpeed = 1.2;
  }

  _startLoop() {
    const animate = () => {
      requestAnimationFrame(animate);
      this.controls.update();
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
    this._clearStructure();
    const atoms = structData.atoms ?? [];
    const bonds = structData.bonds ?? [];

    // 原子ポジションマップ
    const posMap = {};
    atoms.forEach(a => { posMap[a.id] = a.position; });

    // 原子球
    const atomGeo = {};
    atoms.forEach(atom => {
      const r = getRadius(atom.element);
      if (!atomGeo[r]) atomGeo[r] = new THREE.SphereGeometry(r, 24, 16);
      const mat = new THREE.MeshStandardMaterial({
        color: getColor(atom.element),
        roughness: 0.55,
        metalness: 0.10,
      });
      const mesh = new THREE.Mesh(atomGeo[r], mat);
      mesh.position.set(...atom.position);
      mesh.userData = { atomId: atom.id, element: atom.element };
      this._structureGroup.add(mesh);
    });

    // 結合（細いシリンダー）
    const bondMat = new THREE.MeshStandardMaterial({ color: 0x999999, roughness: 0.8, metalness: 0.0 });
    bonds.forEach(bond => {
      const aPos = posMap[bond.from];
      const bPos = posMap[bond.to];
      if (!aPos || !bPos) return;
      const mesh = this._makeBond(aPos, bPos, bondMat);
      this._structureGroup.add(mesh);
    });

    // カメラフィット
    this._fitCamera();

    // 対称要素（デフォルト非表示でセット）
    const elements = structData.symmetry_elements ?? [];
    this.setSymmetryElements(elements);
  }

  _makeBond(aPos, bPos, mat) {
    const start = new THREE.Vector3(...aPos);
    const end   = new THREE.Vector3(...bPos);
    const dir   = end.clone().sub(start);
    const len   = dir.length();
    const mid   = start.clone().add(dir.clone().multiplyScalar(0.5));

    const geo  = new THREE.CylinderGeometry(0.045, 0.045, len, 8);
    const mesh = new THREE.Mesh(geo, mat);
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
    this._symObjects = [];
    this._symElements = [];
  }

  // ── 対称要素 ───────────────────────────────────────────────

  setSymmetryElements(elements) {
    this._symmetryGroup.clear();
    this._symElements = elements;
    this._symObjects = createSymmetryObjects(elements, this._moleculeSize);
    this._symObjects.forEach(obj => this._symmetryGroup.add(obj));
  }

  /** op_types 配列に一致する対称要素を表示し、それ以外を隠す（Phase 5 のホバー用） */
  showSymmetryByOpTypes(opTypes) {
    highlightByOpTypes(this._symObjects, this._symElements, opTypes);
  }

  hideAllSymmetry() {
    hideAllSymmetryObjects(this._symObjects);
  }

  /** 全ての対称要素を表示する（デバッグ・テスト用） */
  showAllSymmetry() {
    this._symObjects.forEach(obj => { obj.visible = true; });
  }

  // ── カメラリセット ─────────────────────────────────────────

  resetCamera() {
    this._fitCamera();
  }

  // ── クリーンアップ ─────────────────────────────────────────

  dispose() {
    this.renderer.dispose();
    this.controls.dispose();
  }
}
