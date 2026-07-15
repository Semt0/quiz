<script>
  import Icon from './Icon.svelte';
  let { limitMs = null, startedAt, onexpire, paused = false } = $props();
  let remainingMs = $state(limitMs ? limitMs - (Date.now() - startedAt) : 0);
  let raf;

  function tick() {
    if (limitMs && !paused) {
      remainingMs = limitMs - (Date.now() - startedAt);
      if (remainingMs <= 0) {
        remainingMs = 0;
        cancelAnimationFrame(raf);
        onexpire?.();
        return;
      }
    }
    raf = requestAnimationFrame(tick);
  }

  $effect(() => {
    if (limitMs) {
      raf = requestAnimationFrame(tick);
      return () => cancelAnimationFrame(raf);
    }
  });

  let pct = $derived(limitMs ? Math.max(0, Math.min(1, remainingMs / limitMs)) : 0);
  let mm = $derived(Math.floor(remainingMs / 60000));
  let ss = $derived(Math.floor((remainingMs % 60000) / 1000));
  let display = $derived(`${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`);
  let danger = $derived(remainingMs < 30000);
</script>

{#if limitMs}
  <div class="timer" class:danger role="timer" aria-label="剩余时间 {display}">
    <Icon name="clock" size={16} />
    <span class="t">{display}</span>
    <div class="bar"><div class="bar-fill" style="width:{pct * 100}%"></div></div>
  </div>
{/if}

<style>
  .timer {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.35rem 0.7rem;
    border-radius: var(--r-pill);
    background: var(--bg-elev);
    border: 1px solid var(--border);
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    color: var(--fg);
  }
  .timer.danger { border-color: var(--bad); color: var(--bad); animation: pulse 1s ease infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.6; } }
  .t { min-width: 3rem; text-align: center; }
  .bar { width: 60px; height: 4px; background: var(--bg-soft); border-radius: var(--r-pill); overflow: hidden; }
  .bar-fill { height: 100%; background: var(--brand); transition: width 0.3s linear; }
  .danger .bar-fill { background: var(--bad); }
</style>
