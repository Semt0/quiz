/* =========================================================================
   router.js — minimal hash router.
   subscribe(cb) fires on route change; navigate(to) sets location.hash.
   ========================================================================= */

import { routes, matchRoute } from './routes.js';

let current = null;
const listeners = new Set();

function parse() {
  const hash = location.hash.replace(/^#/, '') || '/';
  return matchRoute(hash);
}

function emit() {
  current = parse();
  for (const cb of listeners) {
    try {
      cb(current);
    } catch (e) {
      console.error('[router] listener error', e);
    }
  }
}

export function subscribe(cb) {
  listeners.add(cb);
  if (!current) emit();
  else cb(current);
  return () => listeners.delete(cb);
}

export function getCurrent() {
  return current || parse();
}

export function navigate(to) {
  const target = to.startsWith('#') ? to : `#${to}`;
  if (location.hash === target) {
    // force re-emit
    emit();
  } else {
    location.hash = target;
  }
}

export function startRouter() {
  window.addEventListener('hashchange', emit);
  if (!location.hash) {
    location.hash = '#/';
  } else {
    emit();
  }
}

export { routes };
