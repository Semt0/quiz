import { mount } from 'svelte';
import './app.css';
import App from './components/App.svelte';
import { startRouter } from './lib/router.js';
import { initStorage } from './lib/storage.js';
import { fetchManifest, makeQuestionFinder } from './lib/data.js';
import { evaluate } from './lib/grading.js';
import { manifest as manifestStore } from './lib/store.svelte.js';

async function bootstrap() {
  try {
    const m = await fetchManifest();
    manifestStore.data = m;
    const subjects = m.subjects.map((s) => ({ id: s.id, name: s.name }));
    const allQidsBySid = m.allQids;
    const findQuestion = await makeQuestionFinder(m);
    initStorage({ manifestSubjects: subjects, allQidsBySid, findQuestion, evaluate });
  } catch (e) {
    console.error('[quiz] 初始化失败：', e);
    // Still mount the app so the error UI can render.
  }
  startRouter();
  mount(App, { target: document.getElementById('app') });
}

bootstrap();
