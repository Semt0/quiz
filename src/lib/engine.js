/* =========================================================================
   engine.js — session model, assembly, grading orchestration.
   Runtime state (not persisted directly here; persistence via storage.js).
   ========================================================================= */

import { evaluate, isSelfEval, isAutoGradable } from './grading.js';
import { getCorrectAnswer } from './format.js';
import { recordMastery, upsertWrong, resolveWrong, setActiveSession, getActiveSession, addHistory } from './storage.js';

/** Fisher-Yates shuffle (returns a new array). */
export function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** Build the option shuffle map for a question: { newIdx: origIdx }. */
function buildOptionMap(q) {
  if (!q.options || q.options.length < 2) return null;
  const indices = q.options.map((_, i) => i);
  const shuffled = shuffle(indices);
  const map = {};
  shuffled.forEach((origIdx, newIdx) => {
    map[newIdx] = origIdx;
  });
  return map;
}

/**
 * Assemble a session from a question bank.
 * @param {object} opts
 *   questions: Question[] (full bank for the subject, already loaded)
 *   mode: 'practice' | 'exam' | 'wrong'
 *   filters: { chapter, difficulty, type, qids?(for wrong-only) }
 *   count: number (0 = all)
 *   shuffleQuestions: boolean
 *   shuffleOptions: boolean
 *   durationLimitMs: number | null
 */
export function assembleSession({ subjectId, questions, mode, filters = {}, count = 0, shuffleQuestions = false, shuffleOptions = false, durationLimitMs = null }) {
  let pool = questions.slice();

  // wrong-only: restrict to provided qids
  if (mode === 'wrong' && filters.qids) {
    const set = new Set(filters.qids);
    pool = pool.filter((q) => set.has(q.id));
  } else {
    if (filters.chapter) pool = pool.filter((q) => q.chapter === filters.chapter);
    if (filters.difficulty) pool = pool.filter((q) => q.difficulty === filters.difficulty);
    if (filters.type) pool = pool.filter((q) => q.type === filters.type);
  }

  if (shuffleQuestions) pool = shuffle(pool);

  const n = count > 0 ? Math.min(count, pool.length) : pool.length;
  const selected = pool.slice(0, n);

  const optionMaps = {};
  if (shuffleOptions) {
    for (const q of selected) {
      const m = buildOptionMap(q);
      if (m) optionMaps[q.id] = m;
    }
  }

  const session = {
    id: `s-${Date.now().toString(36)}-${Math.floor(Math.random() * 1e6).toString(36)}`,
    subjectId,
    mode,
    assembledFrom: { filters, count: n, shuffleQuestions, shuffleOptions, durationLimitMs },
    questionIds: selected.map((q) => q.id),
    answers: {},
    flags: {},
    optionMaps,
    recorded: {}, // qid -> bool (mastery already counted this session)
    selfEval: {}, // qid -> bool (for self-eval short_answers)
    startedAt: Date.now(),
    durationLimitMs,
    status: 'in-progress',
  };
  return session;
}

export function persistSession(session) {
  setActiveSession(session);
}

export function clearActiveSession() {
  setActiveSession(null);
}

export function resumeSession() {
  return getActiveSession();
}

/**
 * Grade the full session against the question bank, update mastery/wrong/history.
 * @param {object} session
 * @param {Map<string, object>} questionMap  qid -> question
 * @param {object} opts { mode, onMasteryRecorded? }
 * @returns {object} result { total, correct, wrong, selfEvalCount, score, wrongIds, selfEvalIds, status }
 */
export function gradeSession(session, questionMap, { status = 'submitted' } = {}) {
  const total = session.questionIds.length;
  let correct = 0;
  const wrongIds = [];
  const selfEvalIds = [];
  let autoGradedTotal = 0;

  for (const qid of session.questionIds) {
    const q = questionMap.get(qid);
    if (!q) continue;
    const userAns = session.answers[qid];
    const optionMap = session.optionMaps[qid] || null;

    if (isSelfEval(q)) {
      // self-eval: use session.selfEval[qid] if set, else pending
      if (session.selfEval[qid] === true) {
        correct++;
        recordMastery(session.subjectId, qid, true);
        resolveWrong(session.subjectId, qid);
      } else if (session.selfEval[qid] === false) {
        wrongIds.push(qid);
        recordMastery(session.subjectId, qid, false);
        if (userAns !== undefined && userAns !== null && userAns !== '') {
          upsertWrong(session.subjectId, qid, userAns);
        }
      } else {
        selfEvalIds.push(qid); // pending self-eval
      }
      continue;
    }

    if (!isAutoGradable(q)) continue;

    autoGradedTotal++;
    if (userAns === undefined || userAns === null || userAns === '') {
      wrongIds.push(qid);
      recordMastery(session.subjectId, qid, false);
      continue;
    }
    const isCorrect = evaluate(q, userAns, optionMap);
    if (isCorrect) {
      correct++;
      recordMastery(session.subjectId, qid, true);
      resolveWrong(session.subjectId, qid);
    } else {
      wrongIds.push(qid);
      recordMastery(session.subjectId, qid, false);
      upsertWrong(session.subjectId, qid, userAns);
    }
  }

  // Score = correct / autoGradedTotal (self-eval pending excluded from denominator)
  const denom = autoGradedTotal || 1;
  const score = Math.round((correct / denom) * 100);

  const finishedAt = Date.now();
  const durationMs = finishedAt - session.startedAt;

  const result = {
    sessionId: session.id,
    subjectId: session.subjectId,
    mode: session.mode,
    date: finishedAt,
    total,
    correct,
    wrong: wrongIds.length,
    selfEvalPending: selfEvalIds.length,
    score,
    wrongIds,
    selfEvalIds,
    durationMs,
    durationLimitMs: session.durationLimitMs,
    assembledFrom: session.assembledFrom,
    status,
  };

  if ((session.mode === 'exam' || session.mode === 'wrong') && result.selfEvalPending === 0) {
    addHistory(result);
  }

  session.status = status;
  return result;
}

/**
 * Record a single practice answer (immediate feedback).
 * Used in practice mode on checkAnswer. Updates mastery/wrong once per session.
 */
export function recordPracticeAnswer(session, q, userAns) {
  const qid = q.id;
  const optionMap = session.optionMaps[qid] || null;

  if (isSelfEval(q)) {
    // self-eval: do nothing here; the SelfEval buttons call recordSelfEval
    return null;
  }

  if (session.recorded[qid]) {
    // already counted this session; just re-evaluate for display
    return evaluate(q, userAns, optionMap);
  }

  const isCorrect = evaluate(q, userAns, optionMap);
  session.recorded[qid] = true;
  recordMastery(session.subjectId, qid, isCorrect);
  if (isCorrect) {
    resolveWrong(session.subjectId, qid);
  } else {
    upsertWrong(session.subjectId, qid, userAns);
  }
  return isCorrect;
}

/** Record a self-eval result for a short_answer question. */
export function recordSelfEval(session, q, isCorrect, userAns) {
  const qid = q.id;
  if (session.recorded[qid]) {
    session.selfEval[qid] = isCorrect;
    return;
  }
  session.recorded[qid] = true;
  session.selfEval[qid] = isCorrect;
  recordMastery(session.subjectId, qid, isCorrect);
  if (isCorrect) {
    resolveWrong(session.subjectId, qid);
  } else {
    upsertWrong(session.subjectId, qid, userAns);
  }
}

export { getCorrectAnswer, evaluate, isSelfEval, isAutoGradable };
