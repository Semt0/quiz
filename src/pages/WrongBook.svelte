<script>
  import { onMount } from 'svelte';
  import { manifest } from '../lib/store.svelte.js';
  import { fetchManifest, fetchSubject } from '../lib/data.js';
  import { getWrong, resolveWrong } from '../lib/storage.js';
  import { wrongCache, masteryCache } from '../lib/store.svelte.js';
  import QuestionReviewCard from '../components/QuestionReviewCard.svelte';
  import { navigate } from '../lib/router.js';
  import Icon from '../components/Icon.svelte';

  let { route } = $props();
  let subjects = $state([]);
  let loadedQuestions = $state({}); // sid -> qid -> question
  let selectedSid = $state(null);
  let showResolved = $state(false);

  onMount(async () => {
    const m = await fetchManifest();
    manifest.data = m;
    subjects = m.subjects;
    selectedSid = route.query.id || subjects[0]?.id || null;
    for (const s of subjects) {
      try {
        const qs = await fetchSubject(s.id);
        const map = new Map(qs.map((q) => [q.id, q]));
        loadedQuestions[s.id] = map;
      } catch {}
    }
  });

  let wrong = $derived(selectedSid ? getWrong(selectedSid) : {});
  let entries = $derived.by(() => {
    if (!selectedSid || !loadedQuestions[selectedSid]) return [];
    const qmap = loadedQuestions[selectedSid];
    return Object.entries(wrong)
      .map(([qid, e]) => ({ qid, entry: e, q: qmap.get(qid) }))
      .filter((x) => x.q)
      .filter((x) => showResolved ? true : !x.entry.resolvedAt)
      .sort((a, b) => (b.entry.lastWrongAt || 0) - (a.entry.lastWrongAt || 0));
  });
  let unresolvedCount = $derived(Object.values(wrong).filter((e) => !e.resolvedAt).length);

  function select(sid) { selectedSid = sid; }
  function practice(q) {
    navigate(`/subject/${selectedSid}`);
  }
  function practiceAll() {
    navigate(`/exam/${selectedSid}/wrong`);
  }
  function removeResolved(qid) {
    if (!confirm('确认将此题标记为已解决（从错题本移出）？')) return;
    resolveWrong(selectedSid, qid);
    wrongCache.refresh(selectedSid);
    masteryCache.refresh(selectedSid);
    wrong = getWrong(selectedSid); // refresh local
  }
</script>

<svelte:head><title>错题本</title></svelte:head>

<div class="page-head">
  <div>
    <h1 style="margin:0">错题本</h1>
    <p class="muted text-sm" style="margin:0.2rem 0 0">练习与测验中答错的题目会自动收录到这里</p>
  </div>
  <div class="row">
    <label class="check"><input type="checkbox" bind:checked={showResolved} /> 显示已解决</label>
    {#if selectedSid && unresolvedCount > 0}
      <button class="btn btn-primary" onclick={practiceAll}><Icon name="wrong" size={16} /> 错题重练 ({unresolvedCount})</button>
    {/if}
  </div>
</div>

{#if subjects.length === 0}
  <div class="empty-state"><p>加载中…</p></div>
{:else}
  <div class="subj-tabs">
    {#each subjects as s (s.id)}
      <button class="tab" class:active={selectedSid === s.id} onclick={() => select(s.id)}>
        {s.name}
        {#if Object.values(getWrong(s.id)).filter((e) => !e.resolvedAt).length}
          <span class="tab-count">{Object.values(getWrong(s.id)).filter((e) => !e.resolvedAt).length}</span>
        {/if}
      </button>
    {/each}
  </div>

  {#if entries.length === 0}
    <div class="empty-state">
      <Icon name="check" size={40} />
      <p>{showResolved ? '没有已解决的错题' : '错题本为空，继续保持~'}</p>
    </div>
  {:else}
    <div class="entries">
      {#each entries as e (e.qid)}
        <QuestionReviewCard q={e.q} subjectId={selectedSid} onpractice={practice} onremove={() => removeResolved(e.qid)} />
      {/each}
    </div>
  {/if}
{/if}

<style>
  .page-head { display: flex; justify-content: space-between; align-items: flex-end; gap: var(--s-3); margin-bottom: var(--s-4); flex-wrap: wrap; }
  .check { display: inline-flex; align-items: center; gap: 0.35rem; font-size: var(--fs-sm); color: var(--fg-soft); cursor: pointer; }
  .check input { accent-color: var(--brand); }
  .subj-tabs { display: flex; gap: 0.3rem; margin-bottom: var(--s-4); flex-wrap: wrap; }
  .tab { padding: 0.4rem 0.9rem; border-radius: var(--r-sm); border: 1px solid var(--border); background: var(--bg-elev); color: var(--fg-soft); font-size: var(--fs-base); cursor: pointer; transition: all var(--motion); display: inline-flex; align-items: center; gap: 0.4rem; }
  .tab:hover { background: var(--bg-soft); }
  .tab.active { background: var(--brand-grad); color: #fff; border-color: transparent; }
  .tab-count { background: var(--bad); color: #fff; font-size: var(--fs-sm); padding: 0 0.4rem; border-radius: var(--r-pill); font-weight: 600; }
  .entries { display: flex; flex-direction: column; gap: 0; }
</style>
