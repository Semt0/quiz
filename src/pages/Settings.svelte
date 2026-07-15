<script>
  import { settings } from '../lib/store.svelte.js';
  import { applyReducedMotion } from '../lib/storage.js';
  import Icon from '../components/Icon.svelte';

  function setTheme(theme) {
    settings.update({ theme });
  }

  function setReducedMotion(value) {
    settings.update({ reducedMotion: value });
    applyReducedMotion(value);
  }

  function updateNumber(key, value) {
    const n = parseInt(value, 10);
    settings.update({ [key]: Number.isNaN(n) ? 0 : Math.max(0, n) });
  }

  function updateBool(key, checked) {
    settings.update({ [key]: checked });
  }
</script>

<svelte:head><title>设置 · Semt0's Quiz</title></svelte:head>

<div class="container" style="max-width: 720px; margin-inline: auto; padding-block: var(--s-5)">
  <h1 style="margin-bottom: var(--s-4)"><Icon name="settings" size={28} /> 设置</h1>

  <section class="card settings-card">
    <h2>外观</h2>
    <div class="row">
      <span class="row-title">主题</span>
      <div class="segmented" role="group" aria-label="主题">
        {#each ['auto', 'light', 'dark'] as t}
          <button
            class="btn btn-sm"
            class:active={settings.data.theme === t}
            onclick={() => setTheme(t)}
          >
            {t === 'auto' ? '跟随系统' : t === 'light' ? '浅色' : '深色'}
          </button>
        {/each}
      </div>
    </div>
    <div class="row">
      <label for="reducedMotion">减少动画</label>
      <select
        id="reducedMotion"
        class="select"
        value={settings.data.reducedMotion}
        onchange={(e) => setReducedMotion(e.target.value)}
      >
        <option value="auto">跟随系统</option>
        <option value="on">开启</option>
        <option value="off">关闭</option>
      </select>
    </div>
  </section>

  <section class="card settings-card">
    <h2>练习与测验</h2>
    <div class="row">
      <label for="defaultExamN">默认考试题数（0 = 全部）</label>
      <input
        id="defaultExamN"
        class="input"
        type="number"
        min="0"
        value={settings.data.defaultExamN}
        onchange={(e) => updateNumber('defaultExamN', e.target.value)}
      />
    </div>
    <div class="row row-check">
      <label class="check-label"
        ><input
          type="checkbox"
          checked={settings.data.shuffleQuestions}
          onchange={(e) => updateBool('shuffleQuestions', e.target.checked)}
        />
        <span>练习时默认乱序题目</span>
      </label>
    </div>
    <div class="row row-check">
      <label class="check-label"
        ><input
          type="checkbox"
          checked={settings.data.shuffleOptions}
          onchange={(e) => updateBool('shuffleOptions', e.target.checked)}
        />
        <span>练习时默认乱序选项</span>
      </label>
    </div>
  </section>

  <section class="card settings-card">
    <h2>数据</h2>
    <p class="muted text-sm">
      设置数据保存在浏览器本地。如需跨设备迁移，请使用右上角菜单的「导出/导入进度数据」。
    </p>
  </section>
</div>

<style>
  h1 { display: flex; align-items: center; gap: 0.5rem; }
  .settings-card { padding: var(--s-4); margin-bottom: var(--s-4); }
  .settings-card h2 { margin-top: 0; margin-bottom: var(--s-3); font-size: var(--fs-lg); }
  .row { display: flex; align-items: center; justify-content: space-between; gap: var(--s-3); margin-bottom: var(--s-3); flex-wrap: wrap; }
  .row:last-child { margin-bottom: 0; }
  .row label, .row-title { font-weight: 500; }
  .row input[type="number"] { width: 120px; }
  .segmented { display: inline-flex; gap: 0.25rem; }
  .segmented .btn { border-radius: var(--r-sm); }
  .segmented .btn.active { background: var(--brand); color: #fff; border-color: transparent; }
  .row-check { justify-content: flex-start; }
  .check-label { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-weight: 400 !important; }
  .check-label input { width: 1.1rem; height: 1.1rem; accent-color: var(--brand); }
</style>
