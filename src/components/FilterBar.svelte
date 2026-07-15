<script>
  import { filterQuestions } from '../lib/search.js';
  import { debounce } from '../lib/search.js';
  import Icon from './Icon.svelte';

  let {
    questions,
    chapters = [],
    value = { text: '', chapter: '', difficulty: '', type: '' },
    onchange,
  } = $props();

  let local = $state({ ...value });

  const debouncedEmit = debounce((v) => onchange?.(v), 180);

  function patch(p) {
    local = { ...local, ...p };
    debouncedEmit(local);
  }

  let filteredCount = $derived(filterQuestions(questions, local).length);
</script>

<div class="filterbar">
  <div class="search-wrap">
    <Icon name="search" size={16} />
    <input class="search-input" type="search" placeholder="搜索题干 / 选项 / 关键词…" value={local.text} oninput={(e) => patch({ text: e.target.value })} />
  </div>
  <select class="select" value={local.chapter} onchange={(e) => patch({ chapter: e.target.value })}>
    <option value="">全部章节</option>
    {#each chapters as ch}<option value={ch}>{ch}</option>{/each}
  </select>
  <select class="select" value={local.difficulty} onchange={(e) => patch({ difficulty: e.target.value })}>
    <option value="">全部难度</option>
    <option value="core">核心</option>
    <option value="advanced">进阶</option>
    <option value="exam">考试</option>
  </select>
  <select class="select" value={local.type} onchange={(e) => patch({ type: e.target.value })}>
    <option value="">全部题型</option>
    <option value="single_choice">单选</option>
    <option value="multiple_choice">多选</option>
    <option value="true_false">判断</option>
    <option value="fill_blank">填空</option>
    <option value="short_answer">简答</option>
  </select>
  <span class="count chip">{filteredCount} 题</span>
</div>

<style>
  .filterbar { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
  .search-wrap {
    flex: 1; min-width: 180px;
    display: flex; align-items: center; gap: 0.4rem;
    padding: 0.45rem 0.7rem;
    border: 1px solid var(--border);
    border-radius: var(--r-sm);
    background: var(--bg-elev);
    color: var(--fg-mute);
  }
  .search-wrap:focus-within { border-color: var(--brand); box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand) 15%, transparent); }
  .search-input { border: none; background: transparent; outline: none; flex: 1; color: var(--fg); font-size: var(--fs-base); }
  .select { width: auto; min-width: 100px; }
  .count { margin-left: auto; }
  @media (max-width: 600px) {
    .select { flex: 1; min-width: 0; }
    .count { margin-left: 0; }
  }
</style>
