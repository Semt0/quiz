<script>
  // Line chart: points = [{ x, y, label? }] ; yDomain inferred.
  let { points = [], width = 520, height = 160, yMax } = $props();
  let pad = { l: 28, r: 12, t: 12, b: 22 };
  let innerW = $derived(width - pad.l - pad.r);
  let innerH = $derived(height - pad.t - pad.b);
  let maxY = $derived(yMax ?? Math.max(100, ...points.map((p) => p.y)));
  let xs = $derived(points.map((_, i) => (points.length <= 1 ? innerW / 2 : (i / (points.length - 1)) * innerW)));
  let ys = $derived(points.map((p) => innerH - (p.y / maxY) * innerH));
  let pathD = $derived(points.map((p, i) => `${i === 0 ? 'M' : 'L'}${xs[i].toFixed(1)},${ys[i].toFixed(1)}`).join(' '));
  let areaD = $derived(points.length ? `M${xs[0].toFixed(1)},${innerH} ` + points.map((p, i) => `L${xs[i].toFixed(1)},${ys[i].toFixed(1)}`).join(' ') + ` L${xs[points.length - 1].toFixed(1)},${innerH} Z` : '');
</script>

<div class="line-wrap">
  {#if points.length}
    <svg width="100%" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="折线图">
      <!-- y grid -->
      {#each [0, 0.25, 0.5, 0.75, 1] as t}
        <line x1={pad.l} y1={pad.t + t * innerH} x2={pad.l + innerW} y2={pad.t + t * innerH} stroke="var(--border)" stroke-width="1" />
        <text x={pad.l - 6} y={pad.t + t * innerH + 3} text-anchor="end" class="axis-label">{Math.round(maxY * (1 - t))}</text>
      {/each}
      {#if areaD}
        <path d={areaD} fill="color-mix(in srgb, var(--brand) 14%, transparent)" />
      {/if}
      {#if pathD}
        <path d={pathD} fill="none" stroke="var(--brand)" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" />
      {/if}
      {#each points as p, i}
        <circle cx={pad.l + xs[i]} cy={pad.t + ys[i]} r="3.5" fill="var(--brand)" stroke="var(--bg-elev)" stroke-width="1.5">
          <title>{p.label ?? `#${i + 1}`}: {p.y}</title>
        </circle>
      {/each}
    </svg>
  {:else}
    <div class="muted text-sm">暂无历史记录</div>
  {/if}
</div>

<style>
  .line-wrap { width: 100%; }
  .axis-label { font-size: 10px; fill: var(--fg-mute); }
</style>
