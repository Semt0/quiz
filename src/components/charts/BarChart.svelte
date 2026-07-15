<script>
  // Horizontal bars: data = [{ label, value, max?, color? }]
  let { data = [], height = 180, valueLabel } = $props();
  let maxVal = $derived(Math.max(1, ...data.map((d) => d.max ?? d.value)));
</script>

<div class="bars" style="--h:{height}px">
  {#each data as d (d.label)}
    <div class="bar-row">
      <div class="bar-label" title={d.label}>{d.label}</div>
      <div class="bar-track">
        <div
          class="bar-fill"
          style="width:{Math.round(((d.max ?? d.value) / maxVal) * 100)}%; background:{d.color || 'var(--brand-grad)'}"
        ></div>
        {#if d.value !== undefined && d.max !== undefined && d.max > 0}
          <div class="bar-marker" style="left:{Math.round((d.value / d.max) * 100)}%"></div>
        {/if}
      </div>
      <div class="bar-val">{valueLabel ? valueLabel(d) : (d.max !== undefined ? `${d.value}/${d.max}` : d.value)}</div>
    </div>
  {/each}
  {#if data.length === 0}
    <div class="muted text-sm">暂无数据</div>
  {/if}
</div>

<style>
  .bars { display: flex; flex-direction: column; gap: 0.5rem; }
  .bar-row { display: grid; grid-template-columns: minmax(60px, 120px) 1fr auto; gap: 0.6rem; align-items: center; }
  .bar-label {
    font-size: var(--fs-sm);
    color: var(--fg-soft);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .bar-track {
    position: relative;
    height: 10px;
    background: var(--bg-soft);
    border-radius: var(--r-pill);
    overflow: visible;
  }
  .bar-fill {
    height: 100%;
    border-radius: var(--r-pill);
    transition: width 0.5s ease;
  }
  .bar-marker {
    position: absolute;
    top: -3px;
    width: 3px;
    height: 16px;
    background: var(--fg);
    border-radius: 2px;
    opacity: 0.7;
  }
  .bar-val { font-size: var(--fs-sm); color: var(--fg-mute); min-width: 44px; text-align: right; font-variant-numeric: tabular-nums; }
  @media (max-width: 480px) {
    .bar-row { grid-template-columns: 70px 1fr auto; }
  }
</style>
