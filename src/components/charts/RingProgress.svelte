<script>
  let { value = 0, max = 100, size = 120, stroke = 10, label, sublabel, color = 'var(--brand)' } = $props();
  let pct = $derived(max > 0 ? Math.min(1, Math.max(0, value / max)) : 0);
  let radius = $derived((size - stroke) / 2);
  let circ = $derived(2 * Math.PI * radius);
  let dash = $derived(circ * pct);
  let center = $derived(size / 2);
</script>

<div class="ring" style="width:{size}px;height:{size}px" role="img" aria-label="{label}: {value}{max===100?'%':''}">
  <svg width={size} height={size} viewBox="0 0 {size} {size}">
    <circle cx={center} cy={center} r={radius} fill="none" stroke="var(--bg-soft)" stroke-width={stroke} />
    <circle
      cx={center}
      cy={center}
      r={radius}
      fill="none"
      stroke={color}
      stroke-width={stroke}
      stroke-linecap="round"
      stroke-dasharray="{dash} {circ}"
      stroke-dashoffset={circ / 4}
      transform="rotate(-90 {center} {center})"
      style="transition: stroke-dasharray 0.6s ease;"
    />
  </svg>
  <div class="ring-content">
    {#if label}<div class="ring-value">{label}</div>{/if}
    {#if sublabel}<div class="ring-sub">{sublabel}</div>{/if}
  </div>
</div>

<style>
  .ring { position: relative; display: inline-flex; align-items: center; justify-content: center; }
  .ring-content {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
  }
  .ring-value { font-size: 1.6rem; font-weight: 700; color: var(--fg); line-height: 1.1; }
  .ring-sub { font-size: var(--fs-sm); color: var(--fg-mute); margin-top: 0.15rem; }
</style>
