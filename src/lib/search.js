/* =========================================================================
   search.js — client-side question filtering (debounced usage is up to caller).
   ========================================================================= */

/** Normalize for search matching. */
function searchNorm(s) {
  return String(s || '').toLowerCase();
}

/**
 * Filter questions by text/chapter/difficulty/type.
 * @param {Question[]} questions
 * @param {object} f  { text, chapter, difficulty, type }
 * @returns {Question[]}
 */
export function filterQuestions(questions, f = {}) {
  const text = searchNorm(f.text || '').trim();
  return questions.filter((q) => {
    if (f.chapter && q.chapter !== f.chapter) return false;
    if (f.difficulty && q.difficulty !== f.difficulty) return false;
    if (f.type && q.type !== f.type) return false;
    if (text) {
      const hay = [
        q.question,
        ...(q.options || []),
        q.explanation,
        ...(q.keywords || []),
        q.id,
      ]
        .map(searchNorm)
        .join('  ');
      if (!hay.includes(text)) return false;
    }
    return true;
  });
}

/** Debounce helper. */
export function debounce(fn, ms = 200) {
  let t = null;
  return function (...args) {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), ms);
  };
}
