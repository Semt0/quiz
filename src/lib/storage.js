/* =========================================================================
   storage.js — versioned localStorage CRUD + migration from v1 (old quiz.js)
   Namespace: quiz:*  |  meta: quiz:meta = { schema, createdAt, migratedFrom }
   ========================================================================= */

const SCHEMA_VERSION = 2;

const KEYS = {
  meta: 'quiz:meta',
  settings: 'quiz:settings',
  favorites: 'quiz:favorites',
  progress: (sid) => `quiz:progress:${sid}`,
  wrong: (sid) => `quiz:wrong:${sid}`,
  mastery: (sid) => `quiz:mastery:${sid}`,
  history: 'quiz:history',
  activeSession: 'quiz:active-session',
};

function safeParse(raw, fallback) {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function read(key, fallback) {
  try {
    return safeParse(localStorage.getItem(key), fallback);
  } catch {
    return fallback;
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

function remove(key) {
  try {
    localStorage.removeItem(key);
  } catch {
    /* ignore */
  }
}

/* ----- Settings ----- */
const DEFAULT_SETTINGS = {
  theme: 'auto',
  shuffleQuestions: false,
  shuffleOptions: false,
  defaultExamN: 0, // 0 = all
  reducedMotion: 'auto',
};

export function getSettings() {
  return { ...DEFAULT_SETTINGS, ...read(KEYS.settings, {}) };
}
export function setSettings(patch) {
  const next = { ...getSettings(), ...patch };
  write(KEYS.settings, next);
  applyTheme(next.theme);
  applyReducedMotion(next.reducedMotion);
  return next;
}

export function applyTheme(theme) {
  const dark =
    theme === 'dark' ||
    (theme === 'auto' &&
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches);
  if (typeof document !== 'undefined') {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  }
}

export function applyReducedMotion(value) {
  let reduced = value === 'on';
  if (value === 'auto' && typeof window !== 'undefined') {
    reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }
  if (typeof document !== 'undefined') {
    document.documentElement.dataset.reducedMotion = reduced ? 'on' : 'off';
  }
}

/* ----- Favorites (global set keyed by subjectId:qid) ----- */
export function getFavorites() {
  const obj = read(KEYS.favorites, {});
  return new Set(Object.keys(obj).filter((k) => obj[k]));
}
export function isFavorite(subjectId, qid) {
  return getFavorites().has(`${subjectId}:${qid}`);
}
export function toggleFavorite(subjectId, qid) {
  const favs = getFavorites();
  const key = `${subjectId}:${qid}`;
  if (favs.has(key)) favs.delete(key);
  else favs.add(key);
  const obj = {};
  favs.forEach((k) => (obj[k] = true));
  write(KEYS.favorites, obj);
  return favs;
}

/* ----- Progress (practice state per subject) ----- */
export function getProgress(sid) {
  return read(KEYS.progress(sid), { answers: {}, shown: {}, updatedAt: 0 });
}
export function saveProgress(sid, data) {
  write(KEYS.progress(sid), { ...data, updatedAt: Date.now() });
}
export function clearProgress(sid) {
  remove(KEYS.progress(sid));
}

/* ----- Wrong book per subject ----- */
export function getWrong(sid) {
  return read(KEYS.wrong(sid), {});
}
export function upsertWrong(sid, qid, userAns, gradingFn) {
  const wrong = getWrong(sid);
  const entry = wrong[qid] || { attempts: 0, lastWrongAt: 0, lastUserAns: null, resolvedAt: null };
  entry.attempts += 1;
  entry.lastWrongAt = Date.now();
  entry.lastUserAns = userAns;
  entry.resolvedAt = null;
  wrong[qid] = entry;
  write(KEYS.wrong(sid), wrong);
  return wrong;
}
export function resolveWrong(sid, qid) {
  const wrong = getWrong(sid);
  if (wrong[qid]) {
    wrong[qid].resolvedAt = Date.now();
    write(KEYS.wrong(sid), wrong);
  }
}
export function getUnresolvedWrongIds(sid) {
  const wrong = getWrong(sid);
  return Object.keys(wrong).filter((qid) => !wrong[qid].resolvedAt);
}

/* ----- Mastery per subject { qid: {correct, total, lastAt} } ----- */
export function getMastery(sid) {
  return read(KEYS.mastery(sid), {});
}
export function recordMastery(sid, qid, isCorrect) {
  const mastery = getMastery(sid);
  const entry = mastery[qid] || { correct: 0, total: 0, lastAt: 0 };
  entry.total += 1;
  if (isCorrect) entry.correct += 1;
  entry.lastAt = Date.now();
  mastery[qid] = entry;
  write(KEYS.mastery(sid), mastery);
  return mastery;
}

/* ----- History (exam sessions) ----- */
export function getHistory() {
  return read(KEYS.history, []);
}
export function addHistory(entry) {
  const history = getHistory();
  history.push(entry);
  // Cap to last 200 sessions
  if (history.length > 200) history.splice(0, history.length - 200);
  write(KEYS.history, history);
  return entry;
}
export function clearHistory() {
  remove(KEYS.history);
}

/* ----- Active session (resume) ----- */
export function getActiveSession() {
  return read(KEYS.activeSession, null);
}
export function setActiveSession(session) {
  if (session === null) {
    remove(KEYS.activeSession);
    return;
  }
  write(KEYS.activeSession, session);
}

/* ----- Orphan pruning: remove qids not in the bank anymore ----- */
export function pruneOrphans(allQidsBySid) {
  let pruned = 0;
  Object.entries(allQidsBySid).forEach(([sid, qids]) => {
    const set = new Set(qids);
    const wrong = getWrong(sid);
    let wChanged = false;
    for (const qid of Object.keys(wrong)) {
      if (!set.has(qid)) { delete wrong[qid]; wChanged = true; pruned++; }
    }
    if (wChanged) write(KEYS.wrong(sid), wrong);

    const mastery = getMastery(sid);
    let mChanged = false;
    for (const qid of Object.keys(mastery)) {
      if (!set.has(qid)) { delete mastery[qid]; mChanged = true; pruned++; }
    }
    if (mChanged) write(KEYS.mastery(sid), mastery);

    const progress = getProgress(sid);
    let pChanged = false;
    for (const qid of Object.keys(progress.answers || {})) {
      if (!set.has(qid)) { delete progress.answers[qid]; pChanged = true; pruned++; }
    }
    for (const qid of Object.keys(progress.shown || {})) {
      if (!set.has(qid)) { delete progress.shown[qid]; pChanged = true; pruned++; }
    }
    if (pChanged) saveProgress(sid, progress);
  });

  const favs = getFavorites();
  let fChanged = false;
  favs.forEach((key) => {
    const [sid, qid] = key.split(':');
    const set = allQidsBySid[sid];
    if (!set || !set.includes(qid)) { favs.delete(key); fChanged = true; pruned++; }
  });
  if (fChanged) {
    const obj = {};
    favs.forEach((k) => (obj[k] = true));
    write(KEYS.favorites, obj);
  }
  return pruned;
}

/* ----- Export / Import ----- */
export function exportAll() {
  const dump = {};
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (k && k.startsWith('quiz:')) dump[k] = read(k, null);
  }
  return dump;
}
export function importAll(dump, { merge = true } = {}) {
  if (!dump || typeof dump !== 'object') return 0;
  let count = 0;
  for (const [k, v] of Object.entries(dump)) {
    if (!k.startsWith('quiz:')) continue;
    if (merge) {
      // last-write-wins per leaf for progress/wrong/mastery/favorites; history concat
      if (k === KEYS.history) {
        const existing = read(k, []);
        const merged = [...existing];
        (v || []).forEach((entry) => {
          if (!merged.some((e) => e.id === entry.id)) merged.push(entry);
        });
        if (merged.length > 200) merged.splice(0, merged.length - 200);
        write(k, merged);
      } else {
        write(k, v);
      }
    } else {
      write(k, v);
    }
    count++;
  }
  return count;
}

/* ----- Migration from v1 (old quiz.js keys: quiz-progress-<slug>) ----- */
// Replicate the old slugifySubject for matching.
function slugifySubjectV1(subject) {
  return String(subject || 'default')
    .trim()
    .replace(/[^\w一-龥]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase() || 'default';
}

/**
 * Migrate v1 quiz-progress-* keys into v2 quiz:progress:<sid>.
 * `manifestSubjects` = [{ id, name }] from manifest.
 * `evaluate` = (question, userAns) => boolean, for seeding wrong/mastery.
 * `findQuestion` = (sid, qid) => question object | null, for re-grading.
 */
export function migrateFromV1(manifestSubjects, findQuestion, evaluate) {
  const migrated = [];
  const sidByName = new Map();
  for (const s of manifestSubjects) {
    sidByName.set(slugifySubjectV1(s.name), s.id);
  }

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (!key || !key.startsWith('quiz-progress-')) continue;
    const oldSlug = key.slice('quiz-progress-'.length);
    const sid = sidByName.get(oldSlug);
    const raw = read(key, null);
    if (!raw || raw.version !== 1) continue;

    if (!sid) {
      // Subject no longer exists; leave the old key intact (don't delete user data).
      console.warn(`[quiz] 未找到 v1 科目 "${oldSlug}"，保留旧数据。`);
      continue;
    }

    const answers = raw.answers || {};
    const shown = raw.shown || {};

    // Write v2 progress
    const existing = getProgress(sid);
    const mergedAnswers = { ...(existing.answers || {}), ...answers };
    const mergedShown = { ...(existing.shown || {}), ...shown };
    saveProgress(sid, { answers: mergedAnswers, shown: mergedShown, filterChapter: raw.filterChapter || '', shuffleOptions: !!raw.shuffleOptions });

    // Seed wrong + mastery from shown answers that evaluated wrong/correct
    for (const qid of Object.keys(shown)) {
      const q = findQuestion(sid, qid);
      if (!q) continue;
      const userAns = answers[qid];
      if (userAns === undefined) continue;
      const isCorrect = evaluate(q, userAns);
      recordMastery(sid, qid, isCorrect);
      if (!isCorrect) {
        upsertWrong(sid, qid, userAns);
      } else {
        resolveWrong(sid, qid);
      }
    }

    remove(key);
    migrated.push(sid);
  }
  return migrated;
}

/* ----- Init: run migration + prune ----- */
export function initStorage({ manifestSubjects, allQidsBySid, findQuestion, evaluate }) {
  const meta = read(KEYS.meta, null);

  if (!meta || meta.schema < SCHEMA_VERSION) {
    if (!meta || meta.schema < 2) {
      try {
        const migrated = migrateFromV1(manifestSubjects, findQuestion, evaluate);
        if (migrated.length) {
          console.info(`[quiz] 已从 v1 迁移 ${migrated.length} 个科目的进度数据。`);
        }
      } catch (e) {
        console.warn('[quiz] v1 迁移失败:', e);
      }
    }
    write(KEYS.meta, { schema: SCHEMA_VERSION, createdAt: meta?.createdAt || Date.now(), migratedFrom: meta?.schema || null });
  }

  // Ensure settings have theme/motion applied
  applyTheme(getSettings().theme);
  applyReducedMotion(getSettings().reducedMotion);

  // Prune orphans silently
  try {
    pruneOrphans(allQidsBySid);
  } catch (e) {
    console.warn('[quiz] 孤儿清理失败:', e);
  }
}

export function resetAll() {
  const toRemove = [];
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (k && k.startsWith('quiz:')) toRemove.push(k);
  }
  toRemove.forEach(remove);
}
