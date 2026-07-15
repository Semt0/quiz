/* =========================================================================
   grading.js — evaluate a single question's user answer.
   Ported from old quiz.js evaluate(). Pure functions, no DOM.
   ========================================================================= */

import { getCorrectAnswer, normalizeText } from './format.js';

/**
 * Evaluate whether the user's answer is correct.
 * @param {object} q  question object
 * @param {any} userAns  the user's answer
 * @param {object|null} optionMap  shuffle map { newIdx: origIdx } or null
 * @returns {boolean|null} true/false, or null if not auto-gradable (short_answer with empty answer)
 */
export function evaluate(q, userAns, optionMap) {
  // short_answer with empty/null answer => self-eval, not auto-gradable
  if (q.type === 'short_answer') {
    const ans = q.answer;
    if (ans === null || ans === undefined || (typeof ans === 'string' && ans.trim() === '')) {
      return null; // self-eval
    }
    // has reference answer -> normalize match
    if (userAns === undefined || userAns === null || userAns === '') return false;
    const answers = Array.isArray(ans) ? ans : [ans];
    const userVal = normalizeText(userAns);
    return answers.some((a) => normalizeText(a) === userVal);
  }

  if (userAns === undefined || userAns === null || userAns === '') return false;
  const correctAns = getCorrectAnswer(q, optionMap);

  if (q.type === 'single_choice' || q.type === 'true_false') {
    return userAns === correctAns;
  }
  if (q.type === 'multiple_choice') {
    const u = Array.isArray(userAns) ? userAns.slice().sort((a, b) => a - b) : [];
    const c = Array.isArray(correctAns) ? correctAns.slice().sort((a, b) => a - b) : [correctAns];
    if (u.length !== c.length) return false;
    return u.every((v, i) => v === c[i]);
  }
  if (q.type === 'fill_blank') {
    const answers = Array.isArray(correctAns) ? correctAns : [correctAns];
    const userVal = normalizeText(userAns);
    return answers.some((a) => normalizeText(a) === userVal);
  }
  return false;
}

/** Whether a question requires self-evaluation (short_answer with no reference answer). */
export function isSelfEval(q) {
  return (
    q.type === 'short_answer' &&
    (q.answer === null ||
      q.answer === undefined ||
      (typeof q.answer === 'string' && q.answer.trim() === ''))
  );
}

/** Whether a question is auto-gradable (has a definite correct answer). */
export function isAutoGradable(q) {
  return !isSelfEval(q);
}
