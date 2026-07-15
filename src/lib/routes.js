/* =========================================================================
   routes.js — route table + matcher.
   Hash format: #/segment/:param  e.g. #/subject/subject-1
   Also parses a leading query string ?a=b&c=d after the path.
   ========================================================================= */

export const routes = [
  { name: 'home', pattern: '/', page: 'Home' },
  { name: 'subject', pattern: '/subject/:id', page: 'Subject' },
  { name: 'exam', pattern: '/exam/:id', page: 'Exam' },
  { name: 'exam-wrong', pattern: '/exam/:id/wrong', page: 'Exam' },
  { name: 'results', pattern: '/results', page: 'Results' },
  { name: 'dashboard', pattern: '/dashboard', page: 'Dashboard' },
  { name: 'wrong', pattern: '/wrong', page: 'WrongBook' },
  { name: 'favorites', pattern: '/favorites', page: 'Favorites' },
  { name: 'settings', pattern: '/settings', page: 'Settings' },
];

function splitQuery(hash) {
  const qIdx = hash.indexOf('?');
  if (qIdx === -1) return { path: hash, query: {} };
  const path = hash.slice(0, qIdx);
  const query = {};
  const search = hash.slice(qIdx + 1);
  for (const pair of search.split('&')) {
    if (!pair) continue;
    const [k, v] = pair.split('=');
    query[decodeURIComponent(k)] = decodeURIComponent(v || '');
  }
  return { path, query };
}

function normalize(path) {
  if (!path || path === '') return '/';
  if (!path.startsWith('/')) path = '/' + path;
  // collapse trailing slash (except root)
  if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);
  return path;
}

/**
 * Match a hash string to a route. Returns { name, page, params, query } or a fallback home.
 */
export function matchRoute(hash) {
  const { path, query } = splitQuery(hash);
  const norm = normalize(path);

  // Try exact patterns first (longest match), then param patterns.
  // Sort so static segments with more parts are tried first to avoid /exam/:id matching /exam/:id/wrong
  const ordered = routes.slice().sort((a, b) => {
    const ap = a.pattern.split('/').length;
    const bp = b.pattern.split('/').length;
    if (ap !== bp) return bp - ap; // more segments first
    return a.pattern.localeCompare(b.pattern);
  });

  for (const r of ordered) {
    const params = matchPattern(r.pattern, norm);
    if (params !== null) {
      return { name: r.name, page: r.page, params, query };
    }
  }

  return { name: 'home', page: 'Home', params: {}, query };
}

function matchPattern(pattern, path) {
  const pSegs = pattern.split('/').filter(Boolean);
  const pathSegs = path.split('/').filter(Boolean);
  if (pSegs.length !== pathSegs.length) return null;
  const params = {};
  for (let i = 0; i < pSegs.length; i++) {
    const ps = pSegs[i];
    const actual = pathSegs[i];
    if (ps.startsWith(':')) {
      params[ps.slice(1)] = decodeURIComponent(actual);
    } else if (ps !== actual) {
      return null;
    }
  }
  return params;
}
