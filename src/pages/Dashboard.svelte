<script>
  import { onMount } from 'svelte';
  import { manifest } from '../lib/store.svelte.js';
  import { fetchManifest, fetchSubject } from '../lib/data.js';
  import { getMastery, getHistory, getUnresolvedWrongIds } from '../lib/storage.js';
  import { masteryStats } from '../lib/store.svelte.js';
  import RingProgress from '../components/charts/RingProgress.svelte';
  import BarChart from '../components/charts/BarChart.svelte';
  import RadarChart from '../components/charts/RadarChart.svelte';
  import LineChart from '../components/charts/LineChart.svelte';
  import { TYPE_LABELS, DIFFICULTY_LABELS } from '../lib/format.js';
  import Icon from '../components/Icon.svelte';
  import { navigate } from '../lib/router.js';

  let { route } = $props();
  let subjects = $state([]);
  let loadedQuestions = $state({}); // sid -> questions[]
  let selectedSid = $state(null);
  let history = $state([]);

  onMount(async () => {
    const m = await fetchManifest();
    manifest.data = m;
    subjects = m.subjects;
    selectedSid = route.query.id || subjects[0]?.id || null;
    history = getHistory();
    // load all subjects' questions for stats (small data)
    for (const s of subjects) {
      try { loadedQuestions[s.id] = await fetchSubject(s.id); } catch {}
    }
  });

  let questions = $derived(selectedSid ? loadedQuestions[selectedSid] || [] : []);
  let stats = $derived(selectedSid ? masteryStats(selectedSid, questions) : null);

  let chapterBars = $derived.by(() => {
    if (!stats) return [];
    return Object.entries(stats.byChapter)
      .map(([label, v]) => ({ label, value: v.c, max: v.t }))
      .sort((a, b) => b.max - a.max)
      .slice(0, 10);
  });

  let diffRadar = $derived.by(() => {
    if (!stats) return [];
    return Object.entries(stats.byDifficulty).map(([k, v]) => ({
      label: DIFFICULTY_LABELS[k] || k,
      value: v.t ? v.c : 0,
      max: v.t || 1,
    }));
  });

  let typeRadar = $derived.by(() => {
    if (!stats) return [];
    return Object.entries(stats.byType).map(([k, v]) => ({
      label: TYPE_LABELS[k] || k,
      value: v.t ? v.c : 0,
      max: v.t || 1,
    }));
  });

  let historyPoints = $derived.by(() => {
    return history
      .filter((h) => h.subjectId === selectedSid || !selectedSid)
      .slice(-15)
      .map((h, i) => ({ x: i, y: h.score, label: new Date(h.date).toLocaleDateString() }));
  });

  let overallRate = $derived(stats ? Math.round(stats.rate * 100) : 0);
  let wrongCount = $derived(selectedSid ? getUnresolvedWrongIds(selectedSid).length : 0);

  function select(sid) { selectedSid = sid; }
</script>

<svelte:head><title>学习仪表盘</title></svelte:head>

<h1>学习仪表盘</h1>

{#if subjects.length === 0}
  <div class="empty-state"><p>加载中…</p></div>
{:else}
  <div class="subj-tabs">
    {#each subjects as s (s.id)}
      <button class="tab" class:active={selectedSid === s.id} onclick={() => select(s.id)}>{s.name}</button>
    {/each}
  </div>

  {#if selectedSid && stats}
    <div class="dash-grid">
      <div class="card stat-card">
        <div class="card-title">总体掌握度</div>
        <div class="card-body center-col">
          <RingProgress value={overallRate} size={130} stroke={11} label="{overallRate}%" sublabel="正确率" />
          <div class="muted text-sm mt-3">已练 {stats.answered} / {stats.total} 题</div>
        </div>
      </div>

      <div class="card stat-card">
        <div class="card-title">未解决错题</div>
        <div class="card-body center-col">
          <div class="big-num bad">{wrongCount}</div>
          <div class="muted text-sm">道待回顾</div>
          <button class="btn btn-sm mt-3" onclick={() => navigate(`/exam/${selectedSid}/wrong`)} disabled={wrongCount === 0}><Icon name="wrong" size={14} /> 错题重练</button>
        </div>
      </div>

      <div class="card stat-card wide">
        <div class="card-title">章节掌握度（前 10）</div>
        <div class="card-body">
          <BarChart data={chapterBars} />
        </div>
      </div>

      <div class="card stat-card">
        <div class="card-title">难度掌握度</div>
        <div class="card-body center-col">
          <RadarChart axes={diffRadar} size={220} />
        </div>
      </div>

      <div class="card stat-card">
        <div class="card-title">题型掌握度</div>
        <div class="card-body center-col">
          <RadarChart axes={typeRadar} size={220} />
        </div>
      </div>

      <div class="card stat-card wide">
        <div class="card-title">测验成绩趋势</div>
        <div class="card-body">
          <LineChart points={historyPoints} />
        </div>
      </div>
    </div>

    {#if history.length}
      <section class="section">
        <h2>历史记录</h2>
        <div class="history-list">
          {#each history.slice().reverse().slice(0, 20) as h (h.id)}
            <div class="hist-row card">
              <div class="hist-main">
                <span class="chip {h.score >= 80 ? 'chip-ok' : h.score >= 60 ? 'chip-warn' : 'chip-bad'}">{h.score} 分</span>
                <span class="hist-name">{subjects.find((s) => s.id === h.subjectId)?.name || h.subjectId}</span>
                <span class="muted text-sm">{h.mode === 'wrong' ? '错题重练' : '测验'} · {h.correct}/{h.total}</span>
                {#if h.status === 'auto-submitted'}<span class="chip chip-warn">超时</span>{/if}
              </div>
              <div class="hist-date muted text-sm">{new Date(h.date).toLocaleString()}</div>
            </div>
          {/each}
        </div>
      </section>
    {/if}
  {/if}
{/if}

<style>
  .subj-tabs { display: flex; gap: 0.3rem; margin-bottom: var(--s-4); flex-wrap: wrap; }
  .tab { padding: 0.4rem 0.9rem; border-radius: var(--r-sm); border: 1px solid var(--border); background: var(--bg-elev); color: var(--fg-soft); font-size: var(--fs-base); cursor: pointer; transition: all var(--motion); }
  .tab:hover { background: var(--bg-soft); }
  .tab.active { background: var(--brand-grad); color: #fff; border-color: transparent; }

  .dash-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--s-4); }
  .stat-card.wide { grid-column: span 2; }
  .card-title { font-weight: 600; margin-bottom: var(--s-3); color: var(--fg); }
  .card-body { padding: 0; }
  .center-col { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.3rem; }
  .big-num { font-size: 2.5rem; font-weight: 800; line-height: 1; }
  .big-num.bad { color: var(--bad); }

  .section { margin-top: var(--s-5); }
  .history-list { display: flex; flex-direction: column; gap: 0.5rem; }
  .hist-row { display: flex; justify-content: space-between; align-items: center; padding: var(--s-3) var(--s-4); }
  .hist-main { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
  .hist-name { font-weight: 600; }

  @media (max-width: 640px) {
    .dash-grid { grid-template-columns: 1fr; }
    .stat-card.wide { grid-column: span 1; }
  }
</style>
