<script>
  import { renderInlineMarkdown } from '../lib/markdown.js';
  import { renderMath } from '../lib/katex.js';
  import { typeLabel, difficultyLabel, DIFFICULTY_CHIP } from '../lib/format.js';
  import Icon from './Icon.svelte';

  let {
    q,                    // question object (options already shuffled if applicable)
    index,                // 0-based
    total,
    selectedAnswer,       // current user answer for this q (from session.answers[qid])
    resultState,          // null | 'correct' | 'incorrect' | 'neutral' (practice after check)
    mode,                 // 'practice' | 'exam' | 'wrong'
    favorite,             // bool
    flagged,              // bool
    onanswer,             // (value) => void
    oncheck,              // () => void   (practice mode confirm)
    onselfeval,           // (bool) => void
    ontogglefavorite,     // () => void
    ontoggleflag,         // () => void
    correctAnswerDisplay, // string (shown in result)
    explanation,          // string
    keywords,             // string[]
    selfEvalValue,        // bool | undefined (for short_answer self-eval)
    selfEvalDone,         // bool
  } = $props();

  let bodyEl;

  // Re-render KaTeX whenever the question changes
  $effect(() => {
    // touch q.id to track
    void q.id;
    if (bodyEl) {
      // wait a tick for DOM update
      Promise.resolve().then(() => renderMath(bodyEl));
    }
  });

  function letter(i) { return String.fromCharCode(65 + i); }

  function onSingle(idx) {
    onanswer?.(idx);
  }
  function onMultiple(idx, checked) {
    const cur = Array.isArray(selectedAnswer) ? selectedAnswer.slice() : [];
    const i = cur.indexOf(idx);
    if (checked && i === -1) cur.push(idx);
    if (!checked && i !== -1) cur.splice(i, 1);
    cur.sort((a, b) => a - b);
    onanswer?.(cur);
  }
  function onTF(val) {
    onanswer?.(val);
  }
  function onText(e) {
    onanswer?.(e.target.value);
  }
</script>

<section class="qcard" class:is-correct={resultState==='correct'} class:is-incorrect={resultState==='incorrect'} class:is-neutral={resultState==='neutral'}>
  <header class="qhead">
    <div class="qhead-left">
      <span class="qnum">{index + 1}</span>
      <span class="chip">{typeLabel(q.type)}</span>
      <span class="chip {DIFFICULTY_CHIP[q.difficulty] || ''}">{difficultyLabel(q.difficulty)}</span>
      {#if q.chapter}<span class="qchapter">{q.chapter}</span>{/if}
    </div>
    <div class="qhead-right">
      {#if mode !== 'practice'}
        <button class="flag-btn" class:active={flagged} onclick={ontoggleflag} title={flagged ? '取消标记' : '标记待复查'} aria-label="标记">
          <Icon name={flagged ? 'flagFilled' : 'flag'} size={16} />
        </button>
      {/if}
      <button class="flag-btn" class:active={favorite} onclick={ontogglefavorite} title={favorite ? '取消收藏' : '收藏'} aria-label="收藏">
        <Icon name={favorite ? 'starFilled' : 'star'} size={16} />
      </button>
    </div>
  </header>

  <div class="qbody" bind:this={bodyEl}>
    <div class="qtext">{@html renderInlineMarkdown(q.question)}</div>

    <div class="qinput">
      {#if q.type === 'single_choice'}
        <div class="options" role="radiogroup" aria-label="选项">
          {#each q.options as opt, i (i)}
            <button
              class="option"
              class:selected={selectedAnswer === i}
              class:correct={resultState && i === q._correctIdx}
              class:incorrect={resultState === 'incorrect' && selectedAnswer === i}
              role="radio"
              aria-checked={selectedAnswer === i}
              onclick={() => onSingle(i)}
              disabled={resultState && mode === 'practice'}
            >
              <span class="opt-letter">{letter(i)}</span>
              <span class="opt-text">{@html renderInlineMarkdown(opt)}</span>
            </button>
          {/each}
        </div>
      {:else if q.type === 'multiple_choice'}
        <div class="options" role="group" aria-label="选项（多选）">
          {#each q.options as opt, i (i)}
            {@const checked = Array.isArray(selectedAnswer) && selectedAnswer.includes(i)}
            {@const isCorrectOpt = resultState && q._correctArr?.includes(i)}
            {@const isWrongPick = resultState === 'incorrect' && checked && !q._correctArr?.includes(i)}
            <label class="option option-check" class:selected={checked} class:correct={isCorrectOpt} class:incorrect={isWrongPick}>
              <input type="checkbox" {checked} onchange={(e) => onMultiple(i, e.target.checked)} disabled={resultState && mode === 'practice'} />
              <span class="opt-letter">{letter(i)}</span>
              <span class="opt-text">{@html renderInlineMarkdown(opt)}</span>
            </label>
          {/each}
        </div>
      {:else if q.type === 'true_false'}
        <div class="tf-group" role="radiogroup" aria-label="判断">
          <button class="btn tf-btn" class:selected={selectedAnswer === true} class:correct={resultState && q.answer === true} class:incorrect={resultState === 'incorrect' && selectedAnswer === true} role="radio" aria-checked={selectedAnswer === true} onclick={() => onTF(true)} disabled={resultState && mode === 'practice'}>正确</button>
          <button class="btn tf-btn" class:selected={selectedAnswer === false} class:correct={resultState && q.answer === false} class:incorrect={resultState === 'incorrect' && selectedAnswer === false} role="radio" aria-checked={selectedAnswer === false} onclick={() => onTF(false)} disabled={resultState && mode === 'practice'}>错误</button>
        </div>
      {:else if q.type === 'fill_blank'}
        <input class="input" type="text" placeholder="请输入答案" value={selectedAnswer ?? ''} oninput={onText} disabled={resultState && mode === 'practice'} class:correct={resultState === 'correct'} class:incorrect={resultState === 'incorrect'} />
      {:else if q.type === 'short_answer'}
        <textarea class="textarea" rows="4" placeholder="请输入你的回答" value={selectedAnswer ?? ''} oninput={onText} disabled={resultState && mode === 'practice' && selfEvalDone}></textarea>
      {/if}
    </div>
  </div>

  {#if mode === 'practice' && !resultState}
    <div class="qactions">
      {#if q.type === 'short_answer' && q._selfEval}
        <button class="btn btn-primary" onclick={oncheck}>查看参考答案</button>
      {:else}
        <button class="btn btn-primary" onclick={oncheck} disabled={selectedAnswer === undefined || selectedAnswer === '' || (Array.isArray(selectedAnswer) && selectedAnswer.length === 0)}>确认答案</button>
      {/if}
    </div>
  {/if}

  {#if resultState}
    <div class="qresult" class:correct={resultState==='correct'} class:incorrect={resultState==='incorrect'} class:neutral={resultState==='neutral'} role="status" aria-live="polite">
      {#if resultState === 'neutral'}
        <div class="rstatus neutral">参考答案</div>
      {:else}
        <div class="rstatus" class:ok={resultState==='correct'} class:bad={resultState==='incorrect'}>
          {#if resultState === 'correct'}<Icon name="check" size={16} /> 回答正确{:else}<Icon name="x" size={16} /> 回答错误{/if}
        </div>
      {/if}
      {#if correctAnswerDisplay}
        <div class="rcorrect">正确答案：<span>{@html renderInlineMarkdown(correctAnswerDisplay)}</span></div>
      {/if}
      {#if explanation}
        <div class="rtitle">解析</div>
        <div class="rbody">{@html renderInlineMarkdown(explanation)}</div>
      {/if}
      {#if keywords && keywords.length}
        <div class="rkws">
          <span class="muted text-sm">关键词：</span>
          {#each keywords as k}<span class="chip chip-info">{k}</span>{/each}
        </div>
      {/if}
      {#if q.type === 'short_answer' && q._selfEval}
        <div class="selfeval">
          <span class="soft text-sm">这道题你答对了吗？</span>
          <div class="row">
            <button class="btn btn-success btn-sm" class:active={selfEvalValue === true} onclick={() => onselfeval(true)} disabled={selfEvalDone}>我答对了</button>
            <button class="btn btn-sm" class:active={selfEvalValue === false} onclick={() => onselfeval(false)} disabled={selfEvalDone}>还需练习</button>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</section>

<style>
  .qcard {
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-left: 4px solid var(--brand);
    border-radius: var(--r-md);
    box-shadow: var(--shadow-sm);
    padding: var(--s-4);
    margin-bottom: var(--s-4);
    transition: box-shadow var(--motion), border-color var(--motion);
  }
  .qcard.is-correct { border-left-color: var(--ok); }
  .qcard.is-incorrect { border-left-color: var(--bad); }
  .qcard.is-neutral { border-left-color: var(--info); }

  .qhead { display: flex; align-items: center; justify-content: space-between; gap: var(--s-2); margin-bottom: var(--s-3); flex-wrap: wrap; }
  .qhead-left { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; }
  .qhead-right { display: flex; align-items: center; gap: 0.2rem; }
  .qnum {
    display: inline-flex; align-items: center; justify-content: center;
    width: 1.7rem; height: 1.7rem; border-radius: 50%;
    background: var(--brand-grad); color: #fff; font-size: var(--fs-sm); font-weight: 700;
  }
  .qchapter { font-size: var(--fs-sm); color: var(--fg-mute); }
  .flag-btn {
    display: inline-flex; align-items: center; justify-content: center;
    width: 30px; height: 30px; border-radius: var(--r-sm);
    border: none; background: transparent; color: var(--fg-mute);
    transition: background var(--motion), color var(--motion);
  }
  .flag-btn:hover { background: var(--bg-soft); color: var(--fg); }
  .flag-btn.active { color: var(--warn); }

  .qtext { font-size: var(--fs-md); line-height: 1.75; color: var(--fg); margin-bottom: var(--s-4); }
  .qinput { display: flex; flex-direction: column; gap: 0.5rem; }

  .options { display: flex; flex-direction: column; gap: 0.5rem; }
  .option {
    display: flex; align-items: flex-start; gap: 0.6rem;
    width: 100%; text-align: left;
    padding: 0.7rem 0.9rem;
    border-radius: var(--r-sm);
    border: 1.5px solid var(--border);
    background: var(--bg-elev);
    color: var(--fg);
    font-size: var(--fs-base); line-height: 1.5;
    transition: border-color var(--motion), background var(--motion), box-shadow var(--motion), transform 0.1s;
    cursor: pointer;
  }
  .option:hover:not(:disabled) { border-color: var(--border-strong); background: var(--bg-soft); }
  .option.selected { border-color: var(--brand); background: var(--info-bg); box-shadow: 0 0 0 2px color-mix(in srgb, var(--brand) 20%, transparent); }
  .option.correct { border-color: var(--ok); background: var(--ok-bg); box-shadow: 0 0 0 2px color-mix(in srgb, var(--ok) 25%, transparent); }
  .option.incorrect { border-color: var(--bad); background: var(--bad-bg); box-shadow: 0 0 0 2px color-mix(in srgb, var(--bad) 25%, transparent); }
  .option-check { cursor: pointer; }
  .option-check input { margin-top: 0.18rem; accent-color: var(--brand); width: 1.05rem; height: 1.05rem; flex-shrink: 0; }
  .opt-letter {
    display: inline-flex; align-items: center; justify-content: center;
    width: 1.5rem; height: 1.5rem; border-radius: 50%;
    background: var(--bg-soft); color: var(--fg-soft);
    font-size: var(--fs-sm); font-weight: 700; flex-shrink: 0; margin-top: 0.05rem;
  }
  .option.selected .opt-letter { background: var(--brand); color: #fff; }
  .option.correct .opt-letter { background: var(--ok); color: #fff; }
  .option.incorrect .opt-letter { background: var(--bad); color: #fff; }
  .opt-text { flex: 1; }

  .tf-group { display: flex; gap: 0.6rem; }
  .tf-btn { flex: 1; padding: 0.7rem; font-weight: 500; }
  .tf-btn.selected { border-color: var(--brand); background: var(--info-bg); box-shadow: 0 0 0 2px color-mix(in srgb, var(--brand) 20%, transparent); }
  .tf-btn.correct { border-color: var(--ok); background: var(--ok-bg); }
  .tf-btn.incorrect { border-color: var(--bad); background: var(--bad-bg); }

  .input.correct, .textarea.correct { border-color: var(--ok); }
  .input.incorrect, .textarea.incorrect { border-color: var(--bad); }

  .qactions { margin-top: var(--s-3); display: flex; justify-content: flex-end; }

  .qresult {
    margin-top: var(--s-4); padding: var(--s-4);
    border-radius: var(--r-sm);
    background: var(--bg-soft);
    border: 1px solid var(--border);
    animation: fade-in 0.25s ease both;
  }
  .qresult.correct { border-left: 3px solid var(--ok); }
  .qresult.incorrect { border-left: 3px solid var(--bad); }
  .qresult.neutral { border-left: 3px solid var(--info); }
  .rstatus { font-weight: 700; display: flex; align-items: center; gap: 0.35rem; margin-bottom: var(--s-2); }
  .rstatus.ok { color: var(--ok); }
  .rstatus.bad { color: var(--bad); }
  .rstatus.neutral { color: var(--info); }
  .rcorrect { font-size: var(--fs-sm); color: var(--fg-soft); margin-bottom: var(--s-2); }
  .rcorrect span { color: var(--ok); font-weight: 600; }
  .rtitle { font-size: var(--fs-sm); font-weight: 600; color: var(--fg-soft); margin-bottom: 0.3rem; text-transform: uppercase; letter-spacing: 0.04em; }
  .rbody { font-size: var(--fs-base); line-height: 1.7; color: var(--fg); }
  .rkws { margin-top: var(--s-2); display: flex; flex-wrap: wrap; gap: 0.3rem; align-items: center; }
  .selfeval { margin-top: var(--s-3); padding-top: var(--s-3); border-top: 1px dashed var(--border); display: flex; flex-direction: column; gap: 0.4rem; }
  .selfeval .btn.active { outline: 2px solid var(--brand); }
</style>
