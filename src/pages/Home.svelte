<script>
  import { onMount } from 'svelte';
  import { manifest } from '../lib/store.svelte.js';
  import { fetchManifest } from '../lib/data.js';
  import { getHistory, getFavorites } from '../lib/storage.js';
  import SubjectCard from '../components/SubjectCard.svelte';
  import Icon from '../components/Icon.svelte';
  import RingProgress from '../components/charts/RingProgress.svelte';

  let { route, navigate } = $props();

  onMount(() => {
    if (!manifest.data) fetchManifest().then((m) => (manifest.data = m)).catch((e) => (manifest.error = e));
  });

  let subjects = $derived(manifest.data?.subjects || []);
  let totalQ = $derived(subjects.reduce((s, x) => s + x.questionCount, 0));
  let history = $derived(getHistory());
  let favCount = $derived(getFavorites().size);
  let examCount = $derived(history.filter((h) => h.mode === 'exam').length);
  let avgScore = $derived.by(() => {
    const exams = history.filter((h) => h.mode === 'exam');
    if (!exams.length) return 0;
    return Math.round(exams.reduce((s, h) => s + h.score, 0) / exams.length);
  });
</script>

<div class="hero">
  <div class="hero-content">
    <h1>复习题库</h1>
    <p class="hero-sub muted">交互式练习 · 计时测验 · 错题本 · 掌握度统计</p>
    <div class="hero-stats">
      <div class="stat"><div class="stat-num">{subjects.length}</div><div class="stat-label">科目</div></div>
      <div class="stat"><div class="stat-num">{totalQ}</div><div class="stat-label">题目</div></div>
      <div class="stat"><div class="stat-num">{examCount}</div><div class="stat-label">测验</div></div>
      <div class="stat"><div class="stat-num">{favCount}</div><div class="stat-label">收藏</div></div>
    </div>
  </div>
  {#if examCount > 0}
    <div class="hero-ring">
      <RingProgress value={avgScore} size={110} stroke={9} label="{avgScore}%" sublabel="平均分" />
    </div>
  {/if}
</div>

{#if manifest.error}
  <div class="card" style="border-color: var(--bad);">
    <p style="color: var(--bad); margin: 0;">题库数据加载失败：{manifest.error.message}</p>
    <p class="muted text-sm mt-2">请确认已运行 <code>python3 scripts/build_quiz.py</code> 生成 <code>public/data/</code>。</p>
  </div>
{:else if !manifest.data}
  <div class="empty-state"><p>加载题库中…</p></div>
{:else}
  <section class="section">
    <div class="section-head">
      <h2>选择科目</h2>
      <button class="btn btn-ghost btn-sm" onclick={() => navigate('/dashboard')}><Icon name="chart" size={16} /> 掌握度</button>
    </div>
    <div class="subject-grid">
      {#each subjects as s (s.id)}
        <SubjectCard subject={s} />
      {/each}
    </div>
  </section>

  <section class="section">
    <h2>快速入口</h2>
    <div class="quick-grid">
      <a class="quick card card-hover" href="#/wrong" onclick={(e) => { e.preventDefault(); navigate('/wrong'); }}>
        <Icon name="wrong" size={22} />
        <div>
          <div class="quick-title">错题本</div>
          <div class="quick-sub muted text-sm">回顾答错的题目</div>
        </div>
      </a>
      <a class="quick card card-hover" href="#/favorites" onclick={(e) => { e.preventDefault(); navigate('/favorites'); }}>
        <Icon name="star" size={22} />
        <div>
          <div class="quick-title">收藏夹</div>
          <div class="quick-sub muted text-sm">标记的好题</div>
        </div>
      </a>
      <a class="quick card card-hover" href="#/dashboard" onclick={(e) => { e.preventDefault(); navigate('/dashboard'); }}>
        <Icon name="chart" size={22} />
        <div>
          <div class="quick-title">学习仪表盘</div>
          <div class="quick-sub muted text-sm">掌握度与历史</div>
        </div>
      </a>
    </div>
  </section>
{/if}

<style>
  .hero {
    display: flex; justify-content: space-between; align-items: center; gap: var(--s-5);
    padding: var(--s-5) var(--s-4);
    margin-bottom: var(--s-5);
    border-radius: var(--r-lg);
    background: var(--brand-grad);
    color: #fff;
    box-shadow: var(--shadow-md);
    position: relative; overflow: hidden;
  }
  .hero::before {
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(circle at 90% 10%, rgba(255,255,255,0.18), transparent 50%);
  }
  .hero-content { position: relative; z-index: 1; }
  .hero h1 { color: #fff; margin-bottom: 0.3rem; }
  .hero-sub { color: rgba(255,255,255,0.85); margin: 0; }
  .hero-ring { position: relative; z-index: 1; }
  :global(.hero-ring .ring-value), :global(.hero-ring .ring-sub) { color: #fff; }
  :global(.hero-ring svg circle[stroke="var(--bg-soft)"]) { stroke: rgba(255,255,255,0.25); }

  .hero-stats { display: flex; gap: var(--s-5); margin-top: var(--s-4); flex-wrap: wrap; }
  .stat-num { font-size: var(--fs-xl); font-weight: 800; line-height: 1; }
  .stat-label { font-size: var(--fs-sm); color: rgba(255,255,255,0.8); margin-top: 0.2rem; }

  .section { margin-bottom: var(--s-5); }
  .section-head { display: flex; justify-content: space-between; align-items: center; }
  .subject-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--s-4); }

  .quick-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: var(--s-3); }
  .quick { display: flex; align-items: center; gap: var(--s-3); padding: var(--s-4); color: var(--fg); text-decoration: none; }
  .quick:hover { text-decoration: none; }
  .quick :global(svg) { color: var(--brand); flex-shrink: 0; }
  .quick-title { font-weight: 600; }
  .quick-sub { margin-top: 0.1rem; }

  @media (max-width: 600px) {
    .hero { flex-direction: column; align-items: flex-start; padding: var(--s-4); }
    .hero-ring { align-self: center; }
    .hero-stats { gap: var(--s-4); }
  }
</style>
