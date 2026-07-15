<script>
  import { subscribe, navigate } from '../lib/router.js';
  import Header from './Header.svelte';
  import Home from '../pages/Home.svelte';
  import Subject from '../pages/Subject.svelte';
  import Exam from '../pages/Exam.svelte';
  import Results from '../pages/Results.svelte';
  import Dashboard from '../pages/Dashboard.svelte';
  import WrongBook from '../pages/WrongBook.svelte';
  import Favorites from '../pages/Favorites.svelte';
  import Settings from '../pages/Settings.svelte';

  let route = $state(null);

  $effect(() => {
    return subscribe((r) => { route = r; });
  });

  const pages = {
    Home, Subject, Exam, Results, Dashboard, WrongBook, Favorites, Settings,
  };

  let Current = $derived(route ? pages[route.page] || Home : Home);

  // Scroll to top on route change
  $effect(() => {
    if (route) window.scrollTo({ top: 0, behavior: 'instant' });
  });
</script>

<Header />

<main class="page container">
  {#if route}
    {#key route.name + JSON.stringify(route.params)}
      <svelte:component this={Current} {route} navigate={navigate} />
    {/key}
  {:else}
    <div class="empty-state">
      <p>加载中…</p>
    </div>
  {/if}
</main>

<footer class="footer no-print">
  <div class="container row between">
    <span class="muted text-sm">© 2026 Semt0 · 独立复习题库</span>
    <span class="muted text-sm">数据本地存储，不会上传</span>
  </div>
</footer>

<style>
  .footer {
    border-top: 1px solid var(--border);
    padding: var(--s-4) 0;
    margin-top: auto;
  }
</style>
