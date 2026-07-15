<script>
  import { onMount, tick } from 'svelte';
  import { fetchSubject, findSubjectMeta } from '../lib/data.js';
  import { filterQuestions } from '../lib/search.js';
  import { assembleSession, gradeSession, persistSession, clearActiveSession, resumeSession } from '../lib/engine.js';
  import { isSelfEval, isAutoGradable } from '../lib/grading.js';
  import { getCorrectAnswer } from '../lib/format.js';
  import { toggleFavorite } from '../lib/storage.js';
  import { favorites, settings } from '../lib/store.svelte.js';
  import { renderMath } from '../lib/katex.js';
  import { navigate } from '../lib/router.js';
  import QuestionCard from '../components/QuestionCard.svelte';
  import ExamNavGrid from '../components/ExamNavGrid.svelte';
  import Timer from '../components/Timer.svelte';
  import Icon from '../components/Icon.svelte';

  let { route } = $props();
  let sid = $derived(route.params.id);
  let isWrongMode = $derived(route.name === 'exam-wrong');

  let meta = $state(null);
  let questions = $state([]);
  let loading = $state(true);
  let error = $state(null);

  // Phase: 'config' | 'running' | 'submitting'
  let phase = $state('config');
  let session = $state(null);
  let qIndex = $state(0);
  let questionMap = $state(new Map());

  // config form
  let cfg = $state({
    chapter: '',
    difficulty: '',
    type: '',
    count: settings.data.defaultExamN || 0,
    shuffleQuestions: true,
    shuffleOptions: false,
    timed: false,
    minutes: 30,
  });

  onMount(async () => {
    try {
      meta = await findSubjectMeta(sid);
      questions = await fetchSubject(sid);
      questionMap = new Map(questions.map((q) => [q.id, q]));

      // try resume
      const resumed = resumeSession();
      if (resumed && resumed.subjectId === sid && resumed.status === 'in-progress') {
        session = resumed;
        phase = 'running';
        qIndex = 0;
      }
    } catch (e) {
      error = e;
    } finally {
      loading = false;
    }
  });

  let chapters = $derived(meta?.chapters?.map((c) => c.name) || []);
  let availableCount = $derived.by(() => {
    let pool = questions;
    if (isWrongMode) {
      // for wrong mode we don't pre-filter here; handled at start
      return pool.length;
    }
    if (cfg.chapter) pool = pool.filter((q) => q.chapter === cfg.chapter);
    if (cfg.difficulty) pool = pool.filter((q) => q.difficulty === cfg.difficulty);
    if (cfg.type) pool = pool.filter((q) => q.type === cfg.type);
    return pool.length;
  });

  function start() {
    let pool = questions;
    let filters = { ...cfg };
    if (isWrongMode) {
      // use unresolved wrong ids
      import('../lib/storage.js').then(({ getUnresolvedWrongIds }) => {
        const qids = getUnresolvedWrongIds(sid);
        if (qids.length === 0) { alert('错题本为空~'); return; }
        doStart({ qids });
      });
      return;
    }
    doStart(filters);
  }

  function doStart(filters) {
    const count = cfg.count > 0 ? cfg.count : 0;
    const sess = assembleSession({
      subjectId: sid,
      questions,
      mode: isWrongMode ? 'wrong' : 'exam',
      filters,
      count,
      shuffleQuestions: cfg.shuffleQuestions,
      shuffleOptions: cfg.shuffleOptions,
      durationLimitMs: cfg.timed ? cfg.minutes * 60 * 1000 : null,
    });
    if (sess.questionIds.length === 0) {
      alert('没有符合条件的题目，请调整筛选条件。');
      return;
    }
    session = sess;
    phase = 'running';
    qIndex = 0;
    persistSession(session);
    tick().then(renderMathNow);
  }

  let currentQ = $derived(session ? questionMap.get(session.questionIds[qIndex]) : null);
  let currentOptionMap = $derived(session?.optionMaps?.[currentQ?.id] || null);

  function decorateQ(q) {
    if (!q) return q;
    const map = session?.optionMaps?.[q.id] || null;
    const correct = getCorrectAnswer(q, map);
    return {
      ...q,
      _correctIdx: q.type === 'single_choice' ? correct : undefined,
      _correctArr: q.type === 'multiple_choice' ? (Array.isArray(correct) ? correct : [correct]) : undefined,
      _selfEval: isSelfEval(q),
    };
  }
  let decorated = $derived(decorateQ(currentQ));
  let userAns = $derived(session?.answers?.[currentQ?.id]);
  let fav = $derived(currentQ ? favorites.set.has(`${sid}:${currentQ.id}`) : false);
  let flagged = $derived(!!session?.flags?.[currentQ?.id]);

  let navItems = $derived.by(() => {
    if (!session) return [];
    return session.questionIds.map((qid, i) => ({
      index: i,
      answered: session.answers[qid] !== undefined && session.answers[qid] !== '' && !(Array.isArray(session.answers[qid]) && session.answers[qid].length === 0),
      flagged: !!session.flags[qid],
      current: i === qIndex,
    }));
  });

  let answeredCount = $derived(navItems.filter((x) => x.answered).length);
  let flaggedCount = $derived(navItems.filter((x) => x.flagged).length);

  function setAnswer(val) {
    if (!session || !currentQ) return;
    session.answers[currentQ.id] = val;
    session = { ...session };
    persistSession(session);
  }
  function toggleFav() { if (currentQ) favorites.toggle(sid, currentQ.id); }
  function toggleFlag() {
    if (!session || !currentQ) return;
    session.flags[currentQ.id] = !session.flags[currentQ.id];
    session = { ...session };
    persistSession(session);
  }

  function goto(i) {
    if (i < 0 || i >= session.questionIds.length) return;
    qIndex = i;
    tick().then(renderMathNow);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function renderMathNow() {
    const el = document.querySelector('.qcard');
    if (el) renderMath(el);
  }

  function submit(auto = false) {
    if (!auto) {
      const unanswered = navItems.filter((x) => !x.answered).length;
      const msg = unanswered > 0 ? `还有 ${unanswered} 题未作答，确定提交吗？` : '确定提交测验吗？';
      if (!confirm(msg)) return;
    }
    phase = 'submitting';
    const result = gradeSession(session, questionMap, { status: auto ? 'auto-submitted' : 'submitted' });
    // stash session + result for Results page (session needed for self-eval finalize)
    sessionStorage.setItem('quiz:last-session', JSON.stringify(session));
    sessionStorage.setItem('quiz:last-result', JSON.stringify(result));
    clearActiveSession();
    navigate('/results');
  }

  function onexpire() { submit(true); }

  function abandon() {
    if (!confirm('放弃本次测验？已作答的内容不会被记录。')) return;
    clearActiveSession();
    session = null;
    phase = 'config';
  }

  // keyboard
  function onKey(e) {
    if (phase !== 'running' || e.target.matches('input, textarea, select')) return;
    if (e.key === 'ArrowLeft' || e.key === 'k') goto(qIndex - 1);
    else if (e.key === 'ArrowRight' || e.key === 'j') goto(qIndex + 1);
  }
  onMount(() => { window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey); });

  // warn before leaving an in-progress exam
  $effect(() => {
    if (phase === 'running' && session?.status === 'in-progress') {
      const handler = (e) => {
        e.preventDefault();
        e.returnValue = '';
        return '';
      };
      window.addEventListener('beforeunload', handler);
      return () => window.removeEventListener('beforeunload', handler);
    }
  });
</script>

<svelte:head><title>{isWrongMode ? '错题重练' : '测验'} · {meta?.name ?? ''}</title></svelte:head>

{#if loading}
  <div class="empty-state"><p>加载中…</p></div>
{:else if error}
  <div class="card" style="border-color: var(--bad);"><p style="color:var(--bad)">{error.message}</p></div>
{:else if phase === 'config'}
  <div class="config-wrap">
    <h1>{isWrongMode ? '错题重练' : '组卷测验'}</h1>
    <p class="muted">{meta.name}{#if !isWrongMode} · 共 {questions.length} 题{/if}</p>

    {#if isWrongMode}
      <div class="card info-card">
        <Icon name="wrong" size={20} />
        <div>
          <div style="font-weight:600">将针对错题本中未解决的错题进行重练</div>
          <div class="muted text-sm mt-2">每次重练后答对的题会自动标记为已解决。</div>
        </div>
      </div>
    {:else}
      <div class="card config-card">
        <div class="cfg-row">
          <label>章节</label>
          <select class="select" bind:value={cfg.chapter}>
            <option value="">全部章节</option>
            {#each chapters as ch}<option value={ch}>{ch}</option>{/each}
          </select>
        </div>
        <div class="cfg-row">
          <label>难度</label>
          <select class="select" bind:value={cfg.difficulty}>
            <option value="">全部难度</option>
            <option value="core">核心</option>
            <option value="advanced">进阶</option>
            <option value="exam">考试</option>
          </select>
        </div>
        <div class="cfg-row">
          <label>题型</label>
          <select class="select" bind:value={cfg.type}>
            <option value="">全部题型</option>
            <option value="single_choice">单选</option>
            <option value="multiple_choice">多选</option>
            <option value="true_false">判断</option>
            <option value="fill_blank">填空</option>
            <option value="short_answer">简答</option>
          </select>
        </div>
        <div class="cfg-row">
          <label>题量</label>
          <select class="select" bind:value={cfg.count}>
            <option value={0}>全部（{availableCount} 题）</option>
            {#each [5, 10, 15, 20, 30, 50] as n}
              {#if n <= availableCount}<option value={n}>{n} 题</option>{/if}
            {/each}
          </select>
        </div>
        <div class="cfg-row">
          <label>乱序</label>
          <label class="check"><input type="checkbox" bind:checked={cfg.shuffleQuestions} /> 题目乱序</label>
          <label class="check"><input type="checkbox" bind:checked={cfg.shuffleOptions} /> 选项乱序</label>
        </div>
        <div class="cfg-row">
          <label>计时</label>
          <label class="check"><input type="checkbox" bind:checked={cfg.timed} /> 限时作答</label>
          {#if cfg.timed}
            <input class="input" style="width:90px" type="number" min="1" max="180" bind:value={cfg.minutes} /> 分钟
          {/if}
        </div>
      </div>
    {/if}

    <div class="row mt-4">
      <button class="btn btn-ghost" onclick={() => navigate(`/subject/${sid}`)}><Icon name="arrowLeft" size={16} /> 返回</button>
      <button class="btn btn-primary btn-lg" onclick={start}><Icon name="exam" size={18} /> 开始</button>
    </div>
  </div>
{:else if phase === 'running' && session}
  {@const total = session.questionIds.length}
  <div class="exam-bar no-print">
    <div class="exam-bar-left">
      <button class="btn btn-ghost btn-sm" onclick={abandon}><Icon name="arrowLeft" size={15} /> 放弃</button>
      <span class="text-sm muted">{meta.name} · {isWrongMode ? '错题重练' : '测验'}</span>
    </div>
    <div class="exam-bar-right">
      <span class="chip chip-info">已答 {answeredCount}/{total}</span>
      {#if flaggedCount}<span class="chip chip-warn">标记 {flaggedCount}</span>{/if}
      {#if session.durationLimitMs}
        <Timer limitMs={session.durationLimitMs} startedAt={session.startedAt} onexpire={onexpire} />
      {/if}
    </div>
  </div>

  <div class="exam-layout">
    <div class="exam-main">
      <div class="qprogress">
        <div class="progress-bar"><div class="progress-fill" style="width:{Math.round(((qIndex + 1) / total) * 100)}%"></div></div>
        <span class="text-sm muted">第 {qIndex + 1} / {total} 题</span>
      </div>

      {#if decorated}
        <QuestionCard
          q={decorated}
          index={qIndex}
          {total}
          selectedAnswer={userAns}
          resultState={null}
          mode="exam"
          favorite={fav}
          {flagged}
          onanswer={setAnswer}
          ontogglefavorite={toggleFav}
          ontoggleflag={toggleFlag}
        />
      {/if}

      <div class="exam-nav-row">
        <button class="btn" onclick={() => goto(qIndex - 1)} disabled={qIndex === 0}><Icon name="arrowLeft" size={16} /> 上一题</button>
        <button class="btn btn-primary" onclick={() => submit(false)}><Icon name="check" size={16} /> 提交测验</button>
        <button class="btn" onclick={() => goto(qIndex + 1)} disabled={qIndex >= total - 1}>下一题 <Icon name="arrowRight" size={16} /></button>
      </div>
    </div>

    <aside class="exam-side no-print">
      <div class="card">
        <div class="side-title">题目导航</div>
        <ExamNavGrid items={navItems} onselect={goto} />
        <div class="side-legend">
          <span><i class="dot dot-answered"></i> 已答</span>
          <span><i class="dot dot-current"></i> 当前</span>
          <span><i class="dot dot-flag"></i> 标记</span>
        </div>
        <button class="btn btn-primary btn-block mt-3" onclick={() => submit(false)}>提交测验</button>
      </div>
    </aside>
  </div>
{/if}

<style>
  .config-wrap { max-width: 560px; }
  .info-card { display: flex; gap: var(--s-3); align-items: flex-start; color: var(--info); border-color: color-mix(in srgb, var(--info) 40%, var(--border)); background: var(--info-bg); }
  .config-card { display: flex; flex-direction: column; gap: var(--s-3); padding: var(--s-4); }
  .cfg-row { display: flex; align-items: center; gap: var(--s-3); flex-wrap: wrap; }
  .cfg-row > label:first-child { width: 60px; color: var(--fg-soft); font-size: var(--fs-sm); }
  .cfg-row .select { flex: 1; min-width: 160px; }
  .check { display: inline-flex; align-items: center; gap: 0.35rem; font-size: var(--fs-base); color: var(--fg); cursor: pointer; }
  .check input { accent-color: var(--brand); width: 1.05rem; height: 1.05rem; }

  .exam-bar { display: flex; justify-content: space-between; align-items: center; gap: var(--s-3); padding: var(--s-2) 0; margin-bottom: var(--s-3); flex-wrap: wrap; position: sticky; top: var(--header-h); z-index: 10; background: var(--bg); }
  .exam-bar-right { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
  .exam-layout { display: grid; grid-template-columns: 1fr 220px; gap: var(--s-4); align-items: start; }
  .exam-main { min-width: 0; }
  .qprogress { display: flex; align-items: center; gap: var(--s-3); margin-bottom: var(--s-3); }
  .progress-bar { flex: 1; height: 6px; background: var(--bg-soft); border-radius: var(--r-pill); overflow: hidden; }
  .progress-fill { height: 100%; background: var(--brand-grad); border-radius: var(--r-pill); transition: width 0.3s ease; }
  .exam-nav-row { display: flex; justify-content: space-between; align-items: center; gap: var(--s-3); margin-top: var(--s-3); }

  .exam-side { position: sticky; top: calc(var(--header-h) + 50px); }
  .side-title { font-weight: 600; margin-bottom: var(--s-3); font-size: var(--fs-base); }
  .side-legend { display: flex; flex-wrap: wrap; gap: 0.6rem; margin-top: var(--s-3); font-size: var(--fs-sm); color: var(--fg-mute); }
  .side-legend span { display: inline-flex; align-items: center; gap: 0.3rem; }
  .dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
  .dot-answered { background: var(--info-bg); border: 1px solid var(--brand); }
  .dot-current { background: var(--bg-elev); border: 1.5px solid var(--brand); }
  .dot-flag { background: var(--warn); }

  @media (max-width: 760px) {
    .exam-layout { grid-template-columns: 1fr; }
    .exam-side { position: static; order: -1; }
    .exam-side .card { padding: var(--s-3); }
  }
</style>
