<script>
  import { navigate, getCurrent } from '../lib/router.js';
  import { settings, history } from '../lib/store.svelte.js';
  import { exportAll, importAll } from '../lib/storage.js';
  import ThemeToggle from './ThemeToggle.svelte';
  import Icon from './Icon.svelte';

  let route = $state(getCurrent());
  let menuOpen = $state(false);
  let fileInput;

  const links = [
    { to: '/', icon: 'home', label: '首页', match: 'home' },
    { to: '/dashboard', icon: 'chart', label: '掌握度', match: 'dashboard' },
    { to: '/wrong', icon: 'wrong', label: '错题本', match: 'wrong' },
    { to: '/favorites', icon: 'star', label: '收藏', match: 'favorites' },
  ];

  $effect(() => {
    import('../lib/router.js').then(({ subscribe }) => {
      subscribe((r) => { route = r; });
    });
  });

  function go(to) {
    menuOpen = false;
    navigate(to);
  }

  function doExport() {
    const dump = exportAll();
    const blob = new Blob([JSON.stringify(dump, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quiz-progress-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    menuOpen = false;
  }

  function doImport(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const dump = JSON.parse(reader.result);
        const count = importAll(dump, { merge: true });
        alert(`已导入 ${count} 项数据。刷新页面以生效。`);
        location.reload();
      } catch (err) {
        alert('导入失败：' + err.message);
      }
    };
    reader.readAsText(file);
    menuOpen = false;
  }

  function isActive(match) {
    return route?.name === match;
  }
</script>

<header class="header no-print">
  <div class="container header-inner">
    <a class="brand" href={'#/'} onclick={(e) => { e.preventDefault(); go('/'); }}>
      <span class="brand-mark">Q</span>
      <span class="brand-text">Semt0's Quiz</span>
    </a>

    <nav class="nav-links">
      {#each links as l}
        <a
          href={'#' + l.to}
          class="nav-link"
          class:active={isActive(l.match)}
          onclick={(e) => { e.preventDefault(); go(l.to); }}
        >
          <Icon name={l.icon} size={16} />
          <span>{l.label}</span>
        </a>
      {/each}
    </nav>

    <div class="nav-right">
      <ThemeToggle />
      <button class="icon-btn" onclick={() => (menuOpen = !menuOpen)} aria-label="更多" aria-expanded={menuOpen}>
        <Icon name="menu" size={18} />
      </button>
    </div>
  </div>

  {#if menuOpen}
    <div class="menu-overlay" onclick={() => (menuOpen = false)}></div>
    <div class="menu">
      <button class="menu-item" onclick={() => { menuOpen = false; navigate('/settings'); }}><Icon name="settings" size={16} /> 设置</button>
      <button class="menu-item" onclick={doExport}><Icon name="download" size={16} /> 导出进度数据</button>
      <button class="menu-item" onclick={() => fileInput.click()}><Icon name="upload" size={16} /> 导入进度数据</button>
      <a class="menu-item" href="https://github.com/Semt0/quiz" target="_blank" rel="noopener"><Icon name="github" size={16} /> GitHub 仓库</a>
      <input bind:this={fileInput} type="file" accept="application/json" style="display:none" onchange={doImport} />
    </div>
  {/if}
</header>

<style>
  .header {
    position: sticky;
    top: 0;
    z-index: 50;
    height: var(--header-h);
    background: color-mix(in srgb, var(--bg-elev) 88%, transparent);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
  }
  .header-inner {
    height: 100%;
    display: flex;
    align-items: center;
    gap: var(--s-4);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--fg);
    font-weight: 700;
    text-decoration: none;
  }
  .brand:hover { text-decoration: none; }
  .brand-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 8px;
    background: var(--brand-grad);
    color: #fff;
    font-size: 15px;
    font-weight: 800;
  }
  .brand-text { font-size: var(--fs-md); }

  .nav-links {
    display: none;
    align-items: center;
    gap: 0.25rem;
    margin: 0 auto;
  }
  .nav-link {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.4rem 0.75rem;
    border-radius: var(--r-sm);
    color: var(--fg-soft);
    font-size: var(--fs-base);
    font-weight: 500;
    text-decoration: none;
    transition: background var(--motion), color var(--motion);
  }
  .nav-link:hover { background: var(--bg-soft); color: var(--fg); text-decoration: none; }
  .nav-link.active { background: var(--info-bg); color: var(--brand); }

  .nav-right {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-left: auto;
  }
  .icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: var(--r-sm);
    border: 1px solid var(--border);
    background: var(--bg-elev);
    color: var(--fg-soft);
    transition: background var(--motion);
  }
  .icon-btn:hover { background: var(--bg-soft); color: var(--fg); }

  .menu-overlay {
    position: fixed;
    inset: var(--header-h) 0 0 0;
    z-index: 40;
  }
  .menu {
    position: absolute;
    top: calc(var(--header-h) - 8px);
    right: var(--s-4);
    z-index: 51;
    min-width: 200px;
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    box-shadow: var(--shadow-lg);
    padding: 0.35rem;
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    animation: menu-in 0.15s ease both;
  }
  @keyframes menu-in { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
  .menu-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.55rem 0.7rem;
    border-radius: var(--r-sm);
    background: transparent;
    border: none;
    color: var(--fg);
    font-size: var(--fs-base);
    text-align: left;
    text-decoration: none;
    transition: background var(--motion);
  }
  .menu-item:hover { background: var(--bg-soft); text-decoration: none; }

  @media (min-width: 720px) {
    .nav-links { display: flex; }
    .icon-btn[aria-label="更多"] { display: none; }
  }
</style>
