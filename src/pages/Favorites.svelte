<script>
  import { onMount } from 'svelte';
  import { fetchManifest, fetchSubject } from '../lib/data.js';
  import { getFavorites } from '../lib/storage.js';
  import QuestionReviewCard from '../components/QuestionReviewCard.svelte';
  import { navigate } from '../lib/router.js';
  import Icon from '../components/Icon.svelte';

  let subjects = $state([]);
  let loadedQuestions = $state({}); // sid -> Map(qid, q)
  let favSet = $state(new Set());

  onMount(async () => {
    const m = await fetchManifest();
    subjects = m.subjects;
    favSet = getFavorites();
    for (const s of subjects) {
      try {
        const qs = await fetchSubject(s.id);
        loadedQuestions[s.id] = new Map(qs.map((q) => [q.id, q]));
      } catch {}
    }
  });

  // group favorites by subject
  let grouped = $derived.by(() => {
    const groups = {};
    for (const key of favSet) {
      const [sid, qid] = key.split(':');
      const qmap = loadedQuestions[sid];
      const q = qmap?.get(qid);
      if (!q) continue;
      if (!groups[sid]) groups[sid] = [];
      groups[sid].push(q);
    }
    return groups;
  });

  let total = $derived(Object.values(grouped).reduce((s, arr) => s + arr.length, 0));
</script>

<svelte:head><title>收藏夹</title></svelte:head>

<div class="page-head">
  <div>
    <h1 style="margin:0">收藏夹</h1>
    <p class="muted text-sm" style="margin:0.2rem 0 0">你标记为值得复习的好题</p>
  </div>
</div>

{#if total === 0}
  <div class="empty-state">
    <Icon name="star" size={40} />
    <p>还没有收藏的题目~</p>
    <p class="muted text-sm">在题目卡片上点击星标即可收藏。</p>
    <button class="btn btn-primary mt-3" onclick={() => navigate('/')}>去练习</button>
  </div>
{:else}
  {#each Object.entries(grouped) as [sid, qs] (sid)}
    {@const subj = subjects.find((s) => s.id === sid)}
    <section class="section">
      <h2>{subj?.name || sid} <span class="chip">{qs.length}</span></h2>
      {#each qs as q (q.id)}
        <QuestionReviewCard {q} subjectId={sid} onpractice={() => navigate(`/subject/${sid}`)} />
      {/each}
    </section>
  {/each}
{/if}

<style>
  .page-head { margin-bottom: var(--s-4); }
  .section { margin-bottom: var(--s-5); }
</style>
