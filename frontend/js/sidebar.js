/**
 * sidebar.js — サイドバー状態管理とレンダリング（フェーズ7）
 *
 * Sidebar クラスがサイドバー全体を管理する。
 * viewer.html はこのクラスを使い、直接 DOM を操作しない。
 *
 * 主な機能:
 *   - 分解の進捗フロー（C3v → C3 → E）
 *   - 商群選択リスト（有効ボタン＋グレーアウト）
 *   - 「適用」ボタン（選択中のみ有効）
 *   - 再クリックで即適用
 *   - 見つけた組成因子の表示
 *   - 完成パネル
 */

// 結晶点群で出現しうる全ての既約商群タイプ
// SPEC: 位数2（C2/Cs/Ci）か位数3（C3）のみ（結晶制限定理）
const ALL_QUOTIENT_SYMBOLS = [
  { symbol: "C₂",  op_type: "rotation",  label: "C₂",  desc: "2回回転" },
  { symbol: "C₃",  op_type: "rotation",  label: "C₃",  desc: "3回回転" },
  { symbol: "Cₛ",  op_type: "mirror",    label: "Cₛ",  desc: "鏡映" },
  { symbol: "Cᵢ",  op_type: "inversion", label: "Cᵢ",  desc: "反転" },
];

export class Sidebar {
  /**
   * @param {object} opts
   * @param {Element}  opts.progressEl      - #progress-path
   * @param {Element}  opts.quotientListEl  - #quotient-list
   * @param {Element}  opts.factorsListEl   - #factors-list
   * @param {Element}  opts.applyBtnEl      - .apply-btn
   * @param {Function} opts.onQuotientSelect(idx) - 商群選択コールバック
   * @param {Function} opts.onApply()              - 適用コールバック
   * @param {Function} opts.onHoverEnter(quotient) - ホバー開始コールバック
   * @param {Function} opts.onHoverLeave(quotient) - ホバー終了コールバック
   */
  constructor(opts) {
    this._progress   = opts.progressEl;
    this._qList      = opts.quotientListEl;
    this._factors    = opts.factorsListEl;
    this._applyBtn   = opts.applyBtnEl;

    this._onSelect   = opts.onQuotientSelect;
    this._onApply    = opts.onApply;
    this._onHoverIn  = opts.onHoverEnter;
    this._onHoverOut = opts.onHoverLeave;

    this._quotients    = [];   // available_quotients from API
    this._selectedIdx  = -1;
    this._isAnimating  = false;
    this._isComplete   = false;

    if (this._applyBtn) {
      this._applyBtn.addEventListener('click', () => this._onApply?.());
    }
  }

  // ── 公開 API ───────────────────────────────────────────────

  /** セッションデータ全体を受け取ってサイドバーを全更新する。 */
  updateFromSession(sessionData) {
    this._quotients   = sessionData.available_quotients ?? [];
    this._selectedIdx = -1;
    this._isComplete  = sessionData.is_complete ?? false;

    this._renderProgress(
      sessionData.decomposition_path ?? [sessionData.initial_group],
    );
    this._renderQuotients();
    this._renderFactors(sessionData);
    this._refreshApplyBtn();
  }

  /** アニメーション中フラグをセット（適用ボタンをロック）。 */
  setAnimating(animating) {
    this._isAnimating = animating;
    this._refreshApplyBtn();
  }

  /**
   * 指定インデックスの商群を選択状態にする。
   * @returns {boolean} 選択に成功したか
   */
  selectIndex(idx) {
    if (idx < 0 || idx >= this._quotients.length) return false;
    this._selectedIdx = idx;
    this._qList.querySelectorAll('.quotient-btn[data-valid="1"]').forEach((btn, i) => {
      btn.classList.toggle('selected', i === idx);
    });
    this._refreshApplyBtn();
    this._onSelect?.(idx);
    return true;
  }

  /** 現在選択中の商群オブジェクトを返す。 */
  getSelected() {
    return this._quotients[this._selectedIdx] ?? null;
  }

  // ── プライベート描画 ───────────────────────────────────────

  _renderProgress(path) {
    if (!this._progress) return;
    this._progress.innerHTML = '';
    path.forEach((gname, i) => {
      if (i > 0) {
        const arrow = document.createElement('span');
        arrow.className = 'path-arrow';
        arrow.textContent = '→';
        this._progress.appendChild(arrow);
      }
      const span = document.createElement('span');
      const isCurrent = (i === path.length - 1);
      const isVisited = !isCurrent && i < path.length - 1;
      span.className = 'path-group' + (isCurrent ? ' current' : isVisited ? ' visited' : '');
      span.textContent = gname;
      span.title = `ステップ ${i + 1}`;
      this._progress.appendChild(span);
    });
  }

  _renderQuotients() {
    if (!this._qList) return;
    this._qList.innerHTML = '';

    if (this._isComplete) {
      const msg = document.createElement('div');
      msg.className = 'empty-msg';
      msg.textContent = '分解完了 (E に到達)';
      this._qList.appendChild(msg);
      return;
    }

    if (this._quotients.length === 0) {
      const msg = document.createElement('div');
      msg.className = 'loading';
      msg.textContent = '読み込み中...';
      this._qList.appendChild(msg);
      return;
    }

    // ── 有効な商群ボタン ─────────────────────────────────
    this._quotients.forEach((q, i) => {
      const btn = this._makeQuotientBtn(q, i, true);
      this._qList.appendChild(btn);
    });

    // ── グレーアウト（使えない操作タイプ）──────────────────
    const usedOps = new Set(this._quotients.map(q => q.op_types?.[0]));
    const disabled = ALL_QUOTIENT_SYMBOLS.filter(t => !usedOps.has(t.op_type));
    if (disabled.length > 0) {
      const sep = document.createElement('div');
      sep.className = 'apply-hint';
      sep.textContent = '── この群では使えない操作 ──';
      this._qList.appendChild(sep);

      disabled.forEach(t => {
        const btn = this._makeDisabledBtn(t);
        this._qList.appendChild(btn);
      });
    }

    // ── 適用ヒント ────────────────────────────────────────
    const hint = document.createElement('div');
    hint.className = 'apply-hint';
    hint.textContent = '選択後 Enter または再クリックで適用';
    this._qList.appendChild(hint);
  }

  _makeQuotientBtn(q, i, valid) {
    const btn = document.createElement('button');
    btn.className = 'quotient-btn';
    btn.dataset.valid = '1';
    btn.dataset.index = i;
    btn.innerHTML = `
      <span class="kbd">${i + 1}</span>
      <span class="q-info">
        <div class="q-name">${q.quotient_name}</div>
        <div class="q-desc">${q.description}</div>
      </span>
      <span class="q-target">→ ${q.normal_subgroup}</span>
    `;
    btn.addEventListener('click', () => {
      if (i === this._selectedIdx) {
        this._onApply?.();          // 再クリックで即適用
      } else {
        this.selectIndex(i);
      }
    });
    btn.addEventListener('mouseenter', () => this._onHoverIn?.(q));
    btn.addEventListener('mouseleave', () => this._onHoverOut?.(q));
    return btn;
  }

  _makeDisabledBtn(type) {
    const btn = document.createElement('button');
    btn.className = 'quotient-btn disabled';
    btn.disabled = true;
    btn.title = 'この操作はこの群では適用できません';
    btn.innerHTML = `
      <span class="kbd">—</span>
      <span class="q-info">
        <div class="q-name">${type.label}</div>
        <div class="q-desc">${type.desc}</div>
      </span>
      <span class="q-target" style="color:var(--text-dim)">利用不可</span>
    `;
    return btn;
  }

  _renderFactors(sessionData) {
    if (!this._factors) return;
    this._factors.innerHTML = '';

    const factors = sessionData.composition_factors ?? [];
    const history = sessionData.history ?? [];

    if (this._isComplete) {
      // 完成パネル
      const panel = document.createElement('div');
      panel.className = 'complete-panel';
      const title = document.createElement('div');
      title.className = 'complete-title';
      title.textContent = `✓ 完成！ 組成因子が判明`;
      panel.appendChild(title);

      const series = document.createElement('div');
      series.className = 'complete-series';
      const initial = sessionData.initial_group;
      const path = sessionData.decomposition_path ?? [];
      series.innerHTML =
        `<b>${initial}</b> = ` +
        factors.map(f => `<b>${f}</b>`).join(' × ') +
        `<br><span style="font-size:10px;color:var(--text-dim)">` +
        path.join(' → ') + `</span>`;
      panel.appendChild(series);
      this._factors.appendChild(panel);
      return;
    }

    if (factors.length === 0) {
      const msg = document.createElement('div');
      msg.className = 'empty-msg';
      msg.textContent = 'まだなし';
      this._factors.appendChild(msg);
      return;
    }

    factors.forEach((f, i) => {
      const tag = document.createElement('div');
      tag.className = 'factor-tag';
      const desc = history[i]?.description ?? '';
      tag.innerHTML = `
        <span class="step-num">${i + 1}</span>
        <span class="factor-name">${f}</span>
        <span class="factor-desc">${desc}</span>
      `;
      tag.title = `ステップ${i+1}: ${desc}`;
      this._factors.appendChild(tag);
    });
  }

  _refreshApplyBtn() {
    if (!this._applyBtn) return;
    const canApply = !this._isAnimating
      && !this._isComplete
      && this._selectedIdx >= 0
      && this._quotients.length > 0;
    this._applyBtn.disabled = !canApply;
    this._applyBtn.textContent = this._isAnimating
      ? 'アニメーション中...'
      : `適用  Enter`;
  }
}
