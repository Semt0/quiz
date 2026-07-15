/* =========================================================================
   format.js — labels & answer formatting (ported from old quiz.js)
   ========================================================================= */

export const TYPE_LABELS = {
  single_choice: '单选',
  multiple_choice: '多选',
  true_false: '判断',
  fill_blank: '填空',
  short_answer: '简答',
};

export const DIFFICULTY_LABELS = {
  core: '核心',
  advanced: '进阶',
  exam: '考试',
};

export const DIFFICULTY_CHIP = {
  core: 'chip-ok',
  advanced: 'chip-warn',
  exam: 'chip-bad',
};

export function typeLabel(t) {
  return TYPE_LABELS[t] || t;
}
export function difficultyLabel(d) {
  return DIFFICULTY_LABELS[d] || d;
}

/** Normalize text for fill_blank comparison: lowercase, strip whitespace & common punctuation. */
export function normalizeText(s) {
  return String(s)
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[，,。.;；:：、]/g, '');
}

/**
 * Get the effective correct answer for a question, accounting for option shuffle.
 * `optionMap` = { newIdx: origIdx } for that question (or null if no shuffle).
 */
export function getCorrectAnswer(q, optionMap) {
  const ans = q.answer;
  if (optionMap && (q.type === 'single_choice' || q.type === 'multiple_choice')) {
    if (q.type === 'single_choice') {
      for (const k in optionMap) {
        if (optionMap[k] === ans) return parseInt(k, 10);
      }
      return ans;
    }
    // multiple
    const arr = Array.isArray(ans) ? ans : [ans];
    return arr.map((origIdx) => {
      for (const k in optionMap) {
        if (optionMap[k] === origIdx) return parseInt(k, 10);
      }
      return origIdx;
    });
  }
  return ans;
}

/** Format the correct answer for display in results/wrong-book. */
export function formatCorrectAnswer(q, optionMap) {
  const ans = getCorrectAnswer(q, optionMap);
  if (q.type === 'single_choice') {
    if (ans == null || !q.options) return '';
    return `${String.fromCharCode(65 + ans)}. ${q.options[ans] ?? ''}`;
  }
  if (q.type === 'multiple_choice') {
    const arr = Array.isArray(ans) ? ans : [ans];
    return arr.map((idx) => String.fromCharCode(65 + idx)).join('、');
  }
  if (q.type === 'true_false') {
    return ans ? '正确' : '错误';
  }
  if (q.type === 'fill_blank') {
    return Array.isArray(ans) ? ans.join(' / ') : String(ans ?? '');
  }
  return String(ans ?? '');
}
