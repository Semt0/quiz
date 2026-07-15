<script>
  import { renderInlineMarkdown } from '../lib/markdown.js';
  import { renderMath } from '../lib/katex.js';
  import { typeLabel, difficultyLabel, DIFFICULTY_CHIP, formatCorrectAnswer } from '../lib/format.js';
  import Icon from './Icon.svelte';

  // For wrong-book / favorites review display
  let { q, subjectId, onpractice, onremove } = $props();
  let el;
  $effect(() => { void q.id; if (el) Promise.resolve().then(() => renderMath(el)); });
</script>

<div class="rcard card" bind:this={el}>
  <div class="rhead">
    <span class="chip">{typeLabel(q.type)}</span>
    <span class="chip {DIFFICULTY_CHIP[q.difficulty] || ''}">{difficultyLabel(q.difficulty)}</span>
    {#if q.chapter}<span class="muted text-sm">{q.chapter}</span>{/if}
    <span class="muted text-sm mono">{q.id}</span>
  </div>
  <div class="rq">{@html renderInlineMarkdown(q.question)}</div>
  {#if q.type !== 'short_answer' || q.answer}
    <div class="ra">正确答案：<span class="ok">{@html renderInlineMarkdown(formatCorrectAnswer(q, null))}</span></div>
  {/if}
  {#if q.explanation}
    <div class="rexp muted">{@html renderInlineMarkdown(q.explanation)}</div>
  {/if}
  {#if onpractice || onremove}
    <div class="ractions">
      {#if onpractice}<button class="btn btn-primary btn-sm" onclick={() => onpractice(q)}>练习此题</button>{/if}
      {#if onremove}<button class="btn btn-ghost btn-sm" onclick={() => onremove(q)}><Icon name="trash" size={14} /> 移除</button>{/if}
    </div>
  {/if}
</div>

<style>
  .rcard { padding: var(--s-4); margin-bottom: var(--s-3); }
  .rhead { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; margin-bottom: var(--s-2); }
  .rhead .mono { margin-left: auto; }
  .rq { font-size: var(--fs-base); line-height: 1.65; margin-bottom: var(--s-2); color: var(--fg); }
  .ra { font-size: var(--fs-sm); margin-bottom: var(--s-2); color: var(--fg-soft); }
  .ra .ok { color: var(--ok); font-weight: 600; }
  .rexp { font-size: var(--fs-sm); line-height: 1.6; }
  .ractions { margin-top: var(--s-2); display: flex; gap: 0.5rem; justify-content: flex-end; }
</style>
