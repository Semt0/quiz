<script>
  import { onMount, tick } from 'svelte';
  import { fetchSubject, findSubjectMeta } from '../lib/data.js';
  import { filterQuestions } from '../lib/search.js';
  import { assembleSession, recordPracticeAnswer, recordSelfEval, persistSession, clearActiveSession } from '../lib/engine.js';
  import { evaluate, isSelfEval } from '../lib/grading.js';
  import { getCorrectAnswer, formatCorrectAnswer } from '../lib/format.js';
  import { getProgress, saveProgress, clearProgress, toggleFavorite } from '../lib/storage.js';
  import { favorites, settings, masteryCache } from '../lib/store.svelte.js';
  import { renderMath } from '../lib/katex.js';
  import QuestionCard from '../components/QuestionCard.svelte';
  import FilterBar from '../components/FilterBar.svelte';
  import Icon from '../components/Icon.svelte';

  let { route, navigate } = $props();
  let sid = $derived(route.params.id);

  let meta = $state(null);
  let questions = $state([]);
  let loading = $state(true);
  let error = $state(null);

  let filter = $state({ text: '', chapter: '', difficulty: '', type: '' });
  let filtered = $derived(filterQuestions(questions, filter));

  // practice session state
  let session = $state(null); // { questionIds, answers, shown, optionMaps, recorded, selfEval }
  let qIndex = $state(0);

  let chapters = $derived(meta?.chapters?.map((c) => c.name) || []);

  onMount(async () => {
    try {
      meta = await findSubjectMeta(sid);
      if (!meta) { error = new Error('未找到科目'); loading = false; return; }
      questions = await fetchSubject(sid);
      // restore or create practice session over the filtered set
      startPractice(true);
    } catch (e) {
      error = e;
    } finally {
      loading = false;
    }
  });

  function startPractice(restore = false) {
    const list = filtered.length ? filtered : questions;
    let sess = assembleSession({
      subjectId: sid,
      questions: list,
      mode: 'practice',
      filters: { ...filter },
      count: 0,
      shuffleQuestions: settings.data.shuffleQuestions,
      shuffleOptions: settings.data.shuffleOptions,
      durationLimitMs: null,
    });
    if (restore) {
      const prog = getProgress(sid);
      sess.answers = prog.answers || {};
      sess.shown = prog.shown || {};
    } else {
      sess.answers = {};
      sess.shown = {};
    }
    session = sess;
    qIndex = 0;
  }

  // when filter changes, restart practice over new set (keep answers)
  let lastFilterKey = '';
  $effect(() => {
    const key = JSON.stringify(filter);
    if (!loading && questions.length && key !== lastFilterKey) {
      lastFilterKey = key;
      startPractice(true);
    }
  });

  let currentQ = $derived(session ? questions.find((q) => q.id === session.questionIds[qIndex]) : null);
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
  let shown = $derived(session?.shown?.[currentQ?.id]);
  let resultState = $derived.by(() => {
    if (!shown || !currentQ) return null;
    if (isSelfEval(currentQ)) return 'neutral';
    const ok = evaluate(currentQ, userAns, currentOptionMap);
    return ok ? 'correct' : 'incorrect';
  });

  let fav = $derived(currentQ ? favorites.set.has(`${sid}:${currentQ.id}`) : false);
  let flagged = $derived(!!session?.flags?.[currentQ?.id]);
  let selfEvalDone = $derived(session?.recorded?.[currentQ?.id] === true && isSelfEval(currentQ));
  let selfEvalValue = $derived(session?.selfEval?.[currentQ?.id]);

  function setAnswer(val) {
    if (!session || !currentQ) return;
    session.answers[currentQ.id] = val;
    saveProgress(sid, { answers: session.answers, shown: session.shown });
  }

  function check() {
    if (!session || !currentQ) return;
    session.shown[currentQ.id] = true;
    if (!isSelfEval(currentQ)) {
      recordPracticeAnswer(session, currentQ, userAns);
    }
    saveProgress(sid, { answers: session.answers, shown: session.shown });
    session = { ...session };
    masteryCache.refresh(sid);
    tick().then(() => renderMathNow());
  }

  function selfEval(ok) {
    if (!session || !currentQ) return;
    recordSelfEval(session, currentQ, ok, userAns);
    saveProgress(sid, { answers: session.answers, shown: session.shown });
    session = { ...session };
    masteryCache.refresh(sid);
  }

  function go(delta) {
    const next = qIndex + delta;
    if (next < 0 || next >= (session?.questionIds.length || 0)) return;
    qIndex = next;
    tick().then(() => renderMathNow());
  }

  function renderMathNow() {
    const el = document.querySelector('.qcard');
    if (el) renderMath(el);
  }

  function toggleFav() {
    if (!currentQ) return;
    favorites.toggle(sid, currentQ.id);
  }
  function toggleFlag() {
    if (!session || !currentQ) return;
    session.flags[currentQ.id] = !session.flags[currentQ.id];
    session = { ...session };
  }

  function resetProgress() {
    if (!confirm('确定清空本科目的练习进度吗？此操作不可撤销。')) return;
    clearProgress(sid);
    startPractice(false);
    masteryCache.refresh(sid);
  }

  function startExam() {
    navigate(`/exam/${sid}`);
  }

  // keyboard navigation
  function onKey(e) {
    if (!session || e.target.matches('input, textarea, select')) return;
    if (e.key === 'ArrowLeft' || e.key === 'k') go(-1);
    else if (e.key === 'ArrowRight' || e.key === 'j') go(1);
    else if (e.key === 'Enter' && !shown) check();
  }
  onMount(() => { window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey); });

  let correctDisplay = $derived(currentQ && shown ? formatCorrectAnswer(currentQ, currentOptionMap) : '');
</script>

<svelte:head><title>{meta?.name ?? '科目'} · 复习题库</title></svelte:head>

{#if loading}
  <div class="empty-state"><p>加载题目中…</p></div>
{:else if error}
  <div class="card" style="border-color: var(--bad);"><p style="color:var(--bad)">{error.message}</p></div>
{:else}
  <div class="subj-head">
    <div>
      <h1 style="margin-bottom:0.2rem">{meta.name}</h1>
      <p class="muted text-sm">共 {questions.length} 题 · 已练 {Object.keys(getProgress(sid).shown || {}).length} 题</p>
    </div>
    <div class="row">
      <button class="btn btn-ghost btn-sm" onclick={resetProgress}><Icon name="trash" size={15} /> 清空进度</button>
      <button class="btn btn-primary" onclick={startExam}><Icon name="exam" size={16} /> 开始测验</button>
    </div>
  </div>

  <FilterBar {questions} {chapters} bind:value={filter} onchange={(v) => (filter = v)} />

  {#if session && session.questionIds.length}
    {@const total = session.questionIds.length}
    <div class="progress-row">
      <div class="progress-bar"><div class="progress-fill" style="width:{Math.round(((qIndex + 1) / total) * 100)}%"></div></div>
      <span class="text-sm muted">{qIndex + 1} / {total}</span>
    </div>

    {#if decorated}
      <QuestionCard
        q={decorated}
        index={qIndex}
        {total}
        selectedAnswer={userAns}
        {resultState}
        mode="practice"
        favorite={fav}
        {flagged}
        onanswer={setAnswer}
        oncheck={check}
        onselfeval={selfEval}
        ontogglefavorite={toggleFav}
        ontoggleflag={toggleFlag}
        correctAnswerDisplay={correctDisplay}
        explanation={currentQ.explanation}
        keywords={currentQ.keywords}
        selfEvalValue={selfEvalValue}
        selfEvalDone={selfEvalDone}
      />
    {/if}

    <div class="nav-row">
      <button class="btn" onclick={() => go(-1)} disabled={qIndex === 0}><Icon name="arrowLeft" size={16} /> 上一题</button>
      <span class="muted text-sm only-sm">第 {qIndex + 1} / {total} 题</span>
      <button class="btn btn-primary" onclick={() => go(1)} disabled={qIndex >= total - 1}>下一题 <Icon name="arrowRight" size={16} /></button>
    </div>
    <p class="muted text-sm text-center mt-3">键盘 ← → 翻题，Enter 确认答案</p>
  {:else}
    <div class="empty-state"><p>该筛选条件下暂无题目~</p></div>
  {/if}
{/if}

<style>
  .subj-head { display: flex; justify-content: space-between; align-items: flex-end; gap: var(--s-3); margin-bottom: var(--s-4); flex-wrap: wrap; }
  .progress-row { display: flex; align-items: center; gap: var(--s-3); margin: var(--s-4) 0; }
  .progress-bar { flex: 1; height: 6px; background: var(--bg-soft); border-radius: var(--r-pill); overflow: hidden; }
  .progress-fill { height: 100%; background: var(--brand-grad); border-radius: var(--r-pill); transition: width 0.3s ease; }
  .nav-row { display: flex; justify-content: space-between; align-items: center; gap: var(--s-3); margin-top: var(--s-2); }
</style>
