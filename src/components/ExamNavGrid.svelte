<script>
  // Exam question navigation grid: shows status of each question.
  // items = [{ index, answered, flagged, current, correct?, state? }]
  let { items = [], onselect } = $props();
</script>

<div class="navgrid" role="navigation" aria-label="题目导航">
  {#each items as it (it.index)}
    <button
      class="cell"
      class:current={it.current}
      class:answered={it.answered}
      class:flagged={it.flagged}
      class:correct={it.state === 'correct'}
      class:incorrect={it.state === 'incorrect'}
      onclick={() => onselect?.(it.index)}
      aria-label="第 {it.index + 1} 题{it.answered ? '（已答）' : '（未答）'}{it.flagged ? '（已标记）' : ''}"
      aria-current={it.current ? 'true' : undefined}
    >
      {it.index + 1}
      {#if it.flagged}<span class="flag-dot"></span>{/if}
    </button>
  {/each}
</div>

<style>
  .navgrid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(36px, 1fr));
    gap: 0.4rem;
  }
  .cell {
    position: relative;
    aspect-ratio: 1;
    display: flex; align-items: center; justify-content: center;
    border-radius: var(--r-sm);
    border: 1.5px solid var(--border);
    background: var(--bg-elev);
    color: var(--fg-soft);
    font-size: var(--fs-sm); font-weight: 600;
    transition: all var(--motion);
    cursor: pointer;
  }
  .cell:hover { border-color: var(--brand); color: var(--fg); }
  .cell.answered { background: var(--info-bg); border-color: color-mix(in srgb, var(--brand) 50%, var(--border)); color: var(--brand); }
  .cell.current { border-color: var(--brand); box-shadow: 0 0 0 2px color-mix(in srgb, var(--brand) 30%, transparent); color: var(--brand); transform: scale(1.05); }
  .cell.correct { background: var(--ok-bg); border-color: var(--ok); color: var(--ok); }
  .cell.incorrect { background: var(--bad-bg); border-color: var(--bad); color: var(--bad); }
  .flag-dot {
    position: absolute; top: 2px; right: 2px;
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--warn);
  }
</style>
