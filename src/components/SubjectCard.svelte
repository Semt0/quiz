<script>
  import { navigate } from '../lib/router.js';
  import { renderMath } from '../lib/katex.js';
  import { difficultyLabel } from '../lib/format.js';
  import { getMastery } from '../lib/storage.js';
  import Icon from './Icon.svelte';
  import RingProgress from './charts/RingProgress.svelte';

  let { subject } = $props(); // { id, name, questionCount, difficulty, chapters, types }
  let el;

  $effect(() => { if (el) Promise.resolve().then(() => renderMath(el)); });

  function go() { navigate(`/subject/${subject.id}`); }

  let masteredCount = $derived.by(() => {
    const m = getMastery(subject.id);
    return Object.values(m).filter((e) => e.total > 0).length;
  });
  let masteredRate = $derived.by(() => {
    const m = getMastery(subject.id);
    const entries = Object.values(m).filter((e) => e.total > 0);
    if (!entries.length) return 0;
    const sum = entries.reduce((s, e) => s + e.correct / e.total, 0);
    return Math.round((sum / entries.length) * 100);
  });

  let diff = $derived(subject.difficulty || {});
</script>

<a class="scard card card-hover" href={'#/subject/' + subject.id} onclick={(e) => { e.preventDefault(); go(); }} bind:this={el}>
  <div class="scard-top">
    <div class="scard-title">{subject.name}</div>
    <div class="scard-count">{subject.questionCount} 题</div>
  </div>

  <div class="scard-diff">
    {#if diff.core}<span class="chip chip-ok">核心 {diff.core}</span>{/if}
    {#if diff.advanced}<span class="chip chip-warn">进阶 {diff.advanced}</span>{/if}
    {#if diff.exam}<span class="chip chip-bad">真题 {diff.exam}</span>{/if}
  </div>

  <div class="scard-foot">
    <div class="scard-mastery">
      {#if masteredCount > 0}
        <RingProgress value={masteredRate} size={56} stroke={6} label="{masteredRate}%" sublabel="掌握" />
      {:else}
        <div class="scard-new">
          <Icon name="arrowRight" size={18} />
          <span class="text-sm muted">开始练习</span>
        </div>
      {/if}
    </div>
    <div class="scard-progress text-sm muted">
      已练 {masteredCount} / {subject.questionCount}
    </div>
  </div>
</a>

<style>
  .scard {
    display: flex; flex-direction: column; gap: var(--s-3);
    padding: var(--s-4);
    text-decoration: none; color: var(--fg);
    min-height: 150px;
  }
  .scard:hover { text-decoration: none; }
  .scard-top { display: flex; justify-content: space-between; align-items: flex-start; gap: var(--s-2); }
  .scard-title { font-size: var(--fs-lg); font-weight: 700; color: var(--fg); }
  .scard-count { font-size: var(--fs-sm); color: var(--fg-mute); white-space: nowrap; }
  .scard-diff { display: flex; gap: 0.3rem; flex-wrap: wrap; }
  .scard-foot {
    margin-top: auto;
    display: flex; align-items: center; justify-content: space-between; gap: var(--s-3);
    padding-top: var(--s-3); border-top: 1px solid var(--border);
  }
  .scard-new { display: flex; align-items: center; gap: 0.3rem; color: var(--brand); }
</style>
