<script>
  import { onMount, tick } from 'svelte';
  import { fetchSubject, findSubjectMeta } from '../lib/data.js';
  import { isSelfEval } from '../lib/grading.js';
  import { getCorrectAnswer, formatCorrectAnswer } from '../lib/format.js';
  import { renderMath } from '../lib/katex.js';
  import { navigate } from '../lib/router.js';
  import { addHistory } from '../lib/storage.js';
  import { wrongCache, masteryCache, history } from '../lib/store.svelte.js';
  import RingProgress from '../components/charts/RingProgress.svelte';
  import QuestionReviewCard from '../components/QuestionReviewCard.svelte';
  import Icon from '../components/Icon.svelte';

  let result = $state(null);
  let meta = $state(null);
  let questions = $state([]);
  let questionMap = $state(new Map());
  let session = $state(null);
  let loading = $state(true);

  // self-eval pending state per qid (only for self-eval short_answer not yet evaluated)
  let selfEvalPend = $state({}); // qid -> bool|null

  onMount(async () => {
    const raw = sessionStorage.getItem('quiz:last-result');
    const sessRaw = sessionStorage.getItem('quiz:last-session');
    if (raw && sessRaw) {
      result = JSON.parse(raw);
      session = JSON.parse(sessRaw);
      try {
        meta = await findSubjectMeta(result.subjectId);
        questions = await fetchSubject(result.subjectId);
        questionMap = new Map(questions.map((q) => [q.id, q]));
        // init pending self-eval map
        const pend = {};
        for (const qid of result.selfEvalIds || []) pend[qid] = null;
        selfEvalPend = pend;
      } catch (e) { console.error(e); }
    }
    loading = false;
    tick().then(() => renderMath(document.querySelector('.results')));
  });

  let autoTotal = $derived.by(() => {
    if (!session || !questionMap) return 0;
    let n = 0;
    for (const qid of session.questionIds) {
      const q = questionMap.get(qid);
      if (q && !isSelfEval(q)) n++;
    }
    return n;
  });

  let wrongQuestions = $derived.by(() => {
    if (!result || !questionMap) return [];
    return result.wrongIds.map((qid) => questionMap.get(qid)).filter(Boolean);
  });
  let selfEvalQuestions = $derived.by(() => {
    if (!result || !questionMap) return [];
    return (result.selfEvalIds || []).map((qid) => questionMap.get(qid)).filter(Boolean);
  });

  let allSelfEvalDone = $derived(Object.values(selfEvalPend).every((v) => v !== null));

  function setSelfEval(qid, ok) {
    const prev = selfEvalPend[qid];
    if (prev === ok) return;
    selfEvalPend = { ...selfEvalPend, [qid]: ok };

    // revert previous effect if it was already resolved
    if (prev !== null) {
      if (prev) result.correct--;
      else result.wrong--;
      result.selfEvalPending++;
    }
    // apply new effect
    if (ok) {
      result.correct++;
    } else {
      result.wrong++;
    }
    result.selfEvalPending--;

    const resolvedCount = Object.values(selfEvalPend).filter((v) => v !== null).length;
    const denom = autoTotal + resolvedCount;
    result.score = denom ? Math.round((result.correct / denom) * 100) : result.score;
    result = { ...result };
  }

  function finalize() {
    // record self-eval answers into mastery/wrong via re-grading
    if (session) {
      // patch session.selfEval
      session.selfEval = { ...(session.selfEval || {}), ...Object.fromEntries(Object.entries(selfEvalPend).map(([k, v]) => [k, v === true])) };
      // re-grade to update mastery/wrong for self-eval items
      // We re-run gradeSession but it would double-count auto-graded; instead, only record self-evals:
      import('../lib/storage.js').then(({ recordMastery, resolveWrong, upsertWrong }) => {
        for (const [qid, ok] of Object.entries(selfEvalPend)) {
          if (ok === null) continue;
          if (!session.recorded[qid]) {
            session.recorded[qid] = true;
            recordMastery(result.subjectId, qid, ok);
            if (ok) resolveWrong(result.subjectId, qid);
            else upsertWrong(result.subjectId, qid, session.answers[qid]);
          }
        }
        // persist the finalized exam history now that all self-evals are resolved
        if (selfEvalQuestions.length > 0) {
          addHistory(result);
        }
        wrongCache.refresh(result.subjectId);
        masteryCache.refresh(result.subjectId);
        history.refresh();
        sessionStorage.removeItem('quiz:last-result');
        sessionStorage.removeItem('quiz:last-session');
        navigate(`/subject/${result.subjectId}`);
      });
    } else {
      sessionStorage.removeItem('quiz:last-result');
      sessionStorage.removeItem('quiz:last-session');
      navigate(`/subject/${result.subjectId}`);
    }
  }

  function retry() {
    sessionStorage.removeItem('quiz:last-result');
    sessionStorage.removeItem('quiz:last-session');
    navigate(`/exam/${result.subjectId}`);
  }
  function wrongOnly() {
    sessionStorage.removeItem('quiz:last-result');
    sessionStorage.removeItem('quiz:last-session');
    navigate(`/exam/${result.subjectId}/wrong`);
  }

  function copySummary() {
    const lines = [
      `📊 ${meta?.name ?? ''} 测验成绩`,
      `得分：${result.score} 分`,
      `自动判分题：答对 ${result.correct - countSelfEvalTrue()} / ${autoTotal}`,
      `错题：${result.wrongIds.length} 题`,
      `用时：${Math.round(result.durationMs / 60000)} 分钟`,
    ];
    navigator.clipboard?.writeText(lines.join('\n'));
    alert('成绩摘要已复制到剪贴板~');
  }
  function countSelfEvalTrue() {
    return Object.values(selfEvalPend).filter((v) => v === true).length;
  }

  function fmtDuration(ms) {
    const m = Math.floor(ms / 60000);
    const s = Math.floor((ms % 60000) / 1000);
    return `${m}分${String(s).padStart(2, '0')}秒`;
  }
</script>

<svelte:head><title>测验结果</title></svelte:head>

{#if loading}
  <div class="empty-state"><p>加载结果中…</p></div>
{:else if !result}
  <div class="empty-state">
    <Icon name="alert" size={36} />
    <p>没有可显示的测验结果。</p>
    <button class="btn btn-primary mt-3" onclick={() => navigate('/')}>返回首页</button>
  </div>
{:else}
  <div class="results">
    <div class="result-hero card">
      <RingProgress value={result.score} size={140} stroke={12} label="{result.score}" sublabel="分" />
      <div class="hero-info">
        <h1 style="margin:0">{meta?.name ?? '测验'} 结果</h1>
        <p class="muted" style="margin:0.2rem 0">
          {#if result.status === 'auto-submitted'}⏱ 已超时自动提交 · {/if}
          用时 {fmtDuration(result.durationMs)}
        </p>
        <div class="result-stats">
          <div class="rs"><span class="rs-num ok">{result.correct - countSelfEvalTrue()}</span><span class="rs-lbl">答对</span></div>
          <div class="rs"><span class="rs-num bad">{result.wrongIds.length}</span><span class="rs-lbl">答错</span></div>
          <div class="rs"><span class="rs-num">{autoTotal}</span><span class="rs-lbl">自动判分</span></div>
          {#if selfEvalQuestions.length}
            <div class="rs"><span class="rs-num info">{selfEvalQuestions.length}</span><span class="rs-lbl">待自评</span></div>
          {/if}
        </div>
      </div>
    </div>

    <div class="actions no-print">
      <button class="btn" onclick={copySummary}><Icon name="download" size={16} /> 复制成绩</button>
      <button class="btn" onclick={wrongOnly} disabled={result.wrongIds.length === 0}><Icon name="wrong" size={16} /> 只练错题</button>
      <button class="btn btn-primary" onclick={retry}><Icon name="refresh" size={16} /> 重新测验</button>
    </div>

    {#if selfEvalQuestions.length}
      <section class="section">
        <h2>待自评题目 <span class="chip chip-info">{selfEvalQuestions.length}</span></h2>
        <p class="muted text-sm">这些是简答/证明题，系统无法自动判分。请对照参考答案，自评是否答对。</p>
        {#each selfEvalQuestions as q (q.id)}
          <div class="card selfeval-card">
            <QuestionReviewCard {q} subjectId={result.subjectId} />
            <div class="se-actions">
              <span class="soft text-sm">你答对了吗？</span>
              <button class="btn btn-success btn-sm" class:active={selfEvalPend[q.id] === true} onclick={() => setSelfEval(q.id, true)}>我答对了</button>
              <button class="btn btn-sm" class:active={selfEvalPend[q.id] === false} onclick={() => setSelfEval(q.id, false)}>还需练习</button>
            </div>
          </div>
        {/each}
        <button class="btn btn-primary btn-block mt-3" onclick={finalize} disabled={!allSelfEvalDone}>
          {allSelfEvalDone ? '完成并记录' : `还需自评 ${Object.values(selfEvalPend).filter((v) => v === null).length} 题`}
        </button>
      </section>
    {/if}

    {#if wrongQuestions.length}
      <section class="section">
        <h2>错题回顾 <span class="chip chip-bad">{wrongQuestions.length}</span></h2>
        {#each wrongQuestions as q (q.id)}
          <QuestionReviewCard {q} subjectId={result.subjectId} onpractice={(qq) => { sessionStorage.removeItem('quiz:last-result'); navigate(`/subject/${result.subjectId}`); }} />
        {/each}
      </section>
    {/if}

    {#if !wrongQuestions.length && !selfEvalQuestions.length}
      <div class="card text-center mt-4">
        <p style="font-size:var(--fs-lg); margin:0">🎉 全部答对，太棒啦~</p>
        <p class="muted">继续保持，复习才能巩固记忆哦。</p>
      </div>
    {/if}
  </div>
{/if}

<style>
  .result-hero { display: flex; align-items: center; gap: var(--s-5); padding: var(--s-5); margin-bottom: var(--s-4); flex-wrap: wrap; }
  .hero-info { flex: 1; min-width: 200px; }
  .result-stats { display: flex; gap: var(--s-5); margin-top: var(--s-3); flex-wrap: wrap; }
  .rs { display: flex; flex-direction: column; }
  .rs-num { font-size: var(--fs-xl); font-weight: 800; line-height: 1; }
  .rs-num.ok { color: var(--ok); }
  .rs-num.bad { color: var(--bad); }
  .rs-num.info { color: var(--info); }
  .rs-lbl { font-size: var(--fs-sm); color: var(--fg-mute); margin-top: 0.2rem; }

  .actions { display: flex; gap: var(--s-2); justify-content: center; margin-bottom: var(--s-5); flex-wrap: wrap; }
  .section { margin-top: var(--s-5); }
  .selfeval-card { padding: 0; overflow: hidden; }
  .selfeval-card :global(.rcard) { box-shadow: none; border: none; border-radius: 0; }
  .se-actions { display: flex; align-items: center; gap: 0.5rem; padding: var(--s-3) var(--s-4); border-top: 1px solid var(--border); background: var(--bg-soft); flex-wrap: wrap; }
  .se-actions .btn.active { outline: 2px solid var(--brand); }
</style>
