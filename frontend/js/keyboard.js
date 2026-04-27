/**
 * keyboard.js — キーボード操作コントローラ（フェーズ8）
 *
 * 対応キー（SPEC準拠＋拡張）:
 *   1〜9      商群を選択
 *   Enter     選択中の商群を適用
 *   ↑ / ↓    商群リストを上下に移動
 *   H         ヒント（商群を順番にハイライト・循環）
 *   R         現在の点群をリセット（最初からやり直す）
 *   N         別の点群を選ぶ（点群セレクタにフォーカス）
 *   Escape    対称要素の強調表示をクリア
 *   Space     Enter と同じ（適用）
 */

export class KeyboardController {
  /**
   * @param {object}   opts
   * @param {Sidebar}  opts.sidebar     - サイドバーインスタンス
   * @param {CrystalViewer} opts.viewer - ビューアインスタンス
   * @param {Function} opts.onApply    - Enter / Space 時に呼ぶ関数
   * @param {Function} opts.onReset    - R キー時に呼ぶ関数
   * @param {Function} opts.onSelectGroup - N キー時に呼ぶ関数（点群選択フォーカス）
   */
  constructor({ sidebar, viewer, onApply, onReset, onSelectGroup }) {
    this._sidebar       = sidebar;
    this._viewer        = viewer;
    this._onApply       = onApply;
    this._onReset       = onReset;
    this._onSelectGroup = onSelectGroup;
    this._hintIdx       = 0;   // H キーで循環するカーソル

    document.addEventListener('keydown', e => this._handle(e));
  }

  // ── ハンドラ ─────────────────────────────────────────────

  _handle(e) {
    // フォームコントロール上では無効
    const tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
    if (e.target.isContentEditable) return;

    const key = e.key;

    // 1〜9: 商群選択
    if (key >= '1' && key <= '9') {
      e.preventDefault();
      const idx = parseInt(key) - 1;
      if (this._sidebar.selectIndex(idx)) {
        this._hintIdx = idx + 1;  // H 循環をリセット
      }
      this._flash(key);
      return;
    }

    switch (key) {
      case 'Enter':
      case ' ':
        e.preventDefault();
        this._onApply?.();
        this._flash('Enter');
        break;

      case 'ArrowDown':
      case 'Tab':
        if (key === 'Tab' && e.shiftKey) break;  // Shift+Tab は通常のタブ移動
        e.preventDefault();
        this._moveSelection(+1);
        break;

      case 'ArrowUp':
        e.preventDefault();
        this._moveSelection(-1);
        break;

      case 'h':
      case 'H':
        e.preventDefault();
        this._hint();
        this._flash('H');
        break;

      case 'r':
      case 'R':
        e.preventDefault();
        this._onReset?.();
        this._flash('R');
        break;

      case 'n':
      case 'N':
        e.preventDefault();
        this._onSelectGroup?.();
        this._flash('N');
        break;

      case 'Escape':
        e.preventDefault();
        this._viewer?.hideAllSymmetry();
        // 選択も解除
        this._sidebar?.selectIndex(-1);  // -1 は無効なので実質解除
        break;
    }
  }

  // ── ヒント（H キー）────────────────────────────────────────
  // 選べる商群を 1→2→3→…→1 と循環してハイライトする

  _hint() {
    const len = this._sidebar?._quotients?.length ?? 0;
    if (len === 0) return;
    this._hintIdx = this._hintIdx % len;
    this._sidebar.selectIndex(this._hintIdx);
    this._hintIdx++;
  }

  // ── ↑↓ で商群リストを移動 ────────────────────────────────

  _moveSelection(delta) {
    const len = this._sidebar?._quotients?.length ?? 0;
    if (len === 0) return;
    const cur  = this._sidebar._selectedIdx;
    const next = ((cur + delta) + len) % len;
    this._sidebar.selectIndex(next);
    this._hintIdx = next + 1;
  }

  // ── フッターの KBD を一瞬光らせる ─────────────────────────

  _flash(key) {
    const footer = document.getElementById('footer');
    if (!footer) return;
    footer.querySelectorAll('kbd').forEach(kbd => {
      if (kbd.textContent.trim() === key) {
        kbd.classList.add('active');
        setTimeout(() => kbd.classList.remove('active'), 220);
      }
    });
  }

  /** ヒント循環インデックスをリセット（新しい点群ロード時に呼ぶ）。 */
  resetHint() {
    this._hintIdx = 0;
  }
}
