<script>
  import { settings } from '../lib/store.svelte.js';
  import Icon from './Icon.svelte';

  function cycle() {
    const order = ['auto', 'light', 'dark'];
    const cur = settings.data.theme || 'auto';
    const next = order[(order.indexOf(cur) + 1) % order.length];
    settings.update({ theme: next });
  }

  let icon = $derived(
    (settings.data.theme === 'light') ? 'sun'
    : (settings.data.theme === 'dark') ? 'moon'
    : 'monitor'
  );
  let label = $derived(
    settings.data.theme === 'light' ? '浅色'
    : settings.data.theme === 'dark' ? '深色'
    : '跟随系统'
  );
</script>

<button class="theme-toggle" onclick={cycle} title="主题：{label}" aria-label="切换主题（当前 {label}）">
  <Icon name={icon} size={18} />
  <span class="label">{label}</span>
</button>

<style>
  .theme-toggle {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.6rem;
    border-radius: var(--r-sm);
    border: 1px solid var(--border);
    background: var(--bg-elev);
    color: var(--fg-soft);
    font-size: var(--fs-sm);
    transition: background var(--motion), color var(--motion);
  }
  .theme-toggle:hover { background: var(--bg-soft); color: var(--fg); }
  .label { white-space: nowrap; }
  @media (max-width: 480px) { .label { display: none; } }
</style>
