/* =========================================================================
   data.js — lazy-load manifest + per-subject question JSON.
   All fetches prepend import.meta.env.BASE_URL so dev (/) and prod (/quiz/) both work.
   ========================================================================= */

import { applyTheme, getSettings } from './storage.js';

const BASE = import.meta.env.BASE_URL || '/';

let manifestPromise = null;
const subjectCache = new Map(); // sid -> Promise<questions[]>

export function fetchManifest() {
  if (!manifestPromise) {
    manifestPromise = fetch(`${BASE}data/manifest.json`, { cache: 'no-cache' })
      .then((r) => {
        if (!r.ok) throw new Error(`manifest ${r.status}`);
        return r.json();
      })
      .catch((e) => {
        manifestPromise = null;
        throw e;
      });
  }
  return manifestPromise;
}

export function fetchSubject(sid) {
  if (subjectCache.has(sid)) return subjectCache.get(sid);
  const p = fetchManifest()
    .then((m) => {
      const subj = m.subjects.find((s) => s.id === sid);
      if (!subj) throw new Error(`未知科目 ${sid}`);
      return fetch(`${BASE}${subj.dataFile}`, { cache: 'no-cache' }).then((r) => {
        if (!r.ok) throw new Error(`subject ${r.status}`);
        return r.json();
      });
    })
    .catch((e) => {
      subjectCache.delete(sid);
      throw e;
    });
  subjectCache.set(sid, p);
  return p;
}

export function findSubjectMeta(sid) {
  return fetchManifest().then((m) => m.subjects.find((s) => s.id === sid) || null);
}

/** Build a qid -> question map for a subject (used by migration's findQuestion). */
export async function buildQuestionIndex(sid) {
  const questions = await fetchSubject(sid);
  const map = new Map();
  for (const q of questions) map.set(q.id, q);
  return map;
}

/** findQuestion for storage migration: returns question or null. */
export async function makeQuestionFinder(manifest) {
  const indices = new Map(); // sid -> Map(qid, q)
  async function get(sid) {
    if (!indices.has(sid)) {
      try {
        indices.set(sid, await buildQuestionIndex(sid));
      } catch {
        indices.set(sid, new Map());
      }
    }
    return indices.get(sid);
  }
  return async (sid, qid) => {
    const idx = await get(sid);
    return idx.get(qid) || null;
  };
}

/** Trigger a theme re-apply (e.g. after settings load). */
export function ensureTheme() {
  applyTheme(getSettings().theme);
}
