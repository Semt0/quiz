/* =========================================================================
   katex.js — lazy KaTeX loader. Renders math inside an element.
   KaTeX is a separate chunk, only loaded when a question renders.
   ========================================================================= */

let katexModulePromise = null;

function loadKatex() {
  if (!katexModulePromise) {
    katexModulePromise = Promise.all([
      import('katex'),
      import('katex/dist/contrib/auto-render.js'),
    ]).then(([katexMod, autoRenderMod]) => {
      // import the CSS once
      import('katex/dist/katex.min.css');
      return {
        katex: katexMod.default,
        renderMathInElement: autoRenderMod.default.renderMathInElement,
      };
    });
  }
  return katexModulePromise;
}

const DELIMITERS = [
  { left: '$$', right: '$$', display: true },
  { left: '\\[', right: '\\]', display: true },
  { left: '\\(', right: '\\)', display: false },
  { left: '$', right: '$', display: false },
];

const IGNORED_CLASSES = ['katex-ignore'];

/** Render math in the given element. Returns a promise. */
export function renderMath(element) {
  if (!element) return Promise.resolve();
  return loadKatex().then(({ renderMathInElement }) => {
    try {
      renderMathInElement(element, {
        delimiters: DELIMITERS,
        ignoredClasses: IGNORED_CLASSES,
        throwOnError: false,
      });
    } catch {
      /* gracefully ignore */
    }
  });
}

/** Preload KaTeX (e.g. when navigating toward a question page). */
export function preloadKatex() {
  return loadKatex();
}
