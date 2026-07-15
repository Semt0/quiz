/* =========================================================================
   store.svelte.js — Svelte 5 runes-based reactive global stores.
   We use lightweight class instances with $state for cross-component reactivity.
   ========================================================================= */

import { getSettings, getFavorites, getHistory, getWrong, getMastery } from './storage.js';
import { fetchManifest } from './data.js';

// Settings store
class SettingsStore {
  data = $state(getSettings());
  refresh() {
    this.data = getSettings();
  }
  update(patch) {
    // import dynamically to avoid circular
    import('./storage.js').then(({ setSettings }) => {
      this.data = setSettings(patch);
    });
  }
}

class FavoritesStore {
  set = $state(getFavorites());
  refresh() {
    this.set = getFavorites();
  }
  toggle(subjectId, qid) {
    import('./storage.js').then(({ toggleFavorite }) => {
      this.set = toggleFavorite(subjectId, qid);
    });
  }
  has(subjectId, qid) {
    return this.set.has(`${subjectId}:${qid}`);
  }
}

class ManifestStore {
  data = $state(null);
  error = $state(null);
  loading = $state(false);

  async load() {
    if (this.data || this.loading) return;
    this.loading = true;
    try {
      this.data = await fetchManifest();
    } catch (e) {
      this.error = e;
    } finally {
      this.loading = false;
    }
  }
}

class HistoryStore {
  data = $state(getHistory());
  refresh() {
    this.data = getHistory();
  }
}

// Per-subject mastery cache (re-read on demand)
class MasteryCache {
  cache = $state({});
  get(sid) {
    return this.cache[sid] || getMastery(sid);
  }
  refresh(sid) {
    this.cache = { ...this.cache, [sid]: getMastery(sid) };
  }
  refreshAll() {
    this.cache = { ...this.cache };
  }
}

class WrongCache {
  cache = $state({});
  get(sid) {
    return this.cache[sid] || getWrong(sid);
  }
  refresh(sid) {
    this.cache = { ...this.cache, [sid]: getWrong(sid) };
  }
}

export const settings = new SettingsStore();
export const favorites = new FavoritesStore();
export const manifest = new ManifestStore();
export const history = new HistoryStore();
export const masteryCache = new MasteryCache();
export const wrongCache = new WrongCache();

/** Aggregate mastery stats for a subject: { total, correct, rate, byChapter, byDifficulty, byType } */
export function masteryStats(sid, questions) {
  const m = masteryCache.get(sid);
  let answered = 0;
  let correctSum = 0;
  const byChapter = {};
  const byDifficulty = { core: { c: 0, t: 0 }, advanced: { c: 0, t: 0 }, exam: { c: 0, t: 0 } };
  const byType = {};

  for (const q of questions) {
    const entry = m[q.id];
    if (!entry || entry.total === 0) continue;
    answered++;
    correctSum += entry.correct / entry.total;

    const ch = q.chapter || '未分类';
    if (!byChapter[ch]) byChapter[ch] = { c: 0, t: 0 };
    byChapter[ch].c += entry.correct;
    byChapter[ch].t += entry.total;

    if (byDifficulty[q.difficulty]) {
      byDifficulty[q.difficulty].c += entry.correct;
      byDifficulty[q.difficulty].t += entry.total;
    }

    if (!byType[q.type]) byType[q.type] = { c: 0, t: 0 };
    byType[q.type].c += entry.correct;
    byType[q.type].t += entry.total;
  }

  const rate = answered ? correctSum / answered : 0;
  return { answered, total: questions.length, correctSum, rate, byChapter, byDifficulty, byType };
}
