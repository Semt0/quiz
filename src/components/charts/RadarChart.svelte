<script>
  // Radar chart: axes = [{ label, value, max }]  value/max in 0..1
  let { axes = [], size = 240 } = $props();
  let center = $derived(size / 2);
  let radius = $derived(size / 2 - 36);
  let n = $derived(axes.length);

  function point(angle, r) {
    return [center + r * Math.cos(angle - Math.PI / 2), center + r * Math.sin(angle - Math.PI / 2)];
  }

  let rings = $derived([0.25, 0.5, 0.75, 1]);
  let angles = $derived(axes.map((_, i) => (n > 0 ? (i / n) * 2 * Math.PI : 0)));

  let gridPolys = $derived(
    rings.map((r) =>
      angles.map((a) => point(a, radius * r).join(',')).join(' ')
    )
  );
  let dataPoly = $derived(
    axes.map((ax, i) => point(angles[i], radius * Math.min(1, ax.max ? ax.value / ax.max : 0)).join(',')).join(' ')
  );
  let spokes = $derived(angles.map((a) => point(a, radius).join(',')));
</script>

<div class="radar-wrap">
  {#if n >= 3}
    <svg width={size} height={size} viewBox="0 0 {size} {size}" role="img" aria-label="掌握度雷达图">
      {#each gridPolys as poly}
        <polygon points={poly} fill="none" stroke="var(--border)" stroke-width="1" />
      {/each}
      {#each spokes as sp, i}
        <line x1={center} y1={center} x2={sp.split(',')[0]} y2={sp.split(',')[1]} stroke="var(--border)" stroke-width="1" />
      {/each}
      <polygon points={dataPoly} fill="color-mix(in srgb, var(--brand) 22%, transparent)" stroke="var(--brand)" stroke-width="2" />
      {#each axes as ax, i}
        {@const [lx, ly] = point(angles[i], radius + 16)}
        <text x={lx} y={ly} text-anchor="middle" dominant-baseline="middle" class="axis-label">{ax.label}</text>
      {/each}
    </svg>
  {:else}
    <div class="muted text-sm">至少需要 3 个维度才能绘制雷达图</div>
  {/if}
</div>

<style>
  .radar-wrap { display: flex; justify-content: center; }
  .axis-label { font-size: 10px; fill: var(--fg-soft); }
</style>
