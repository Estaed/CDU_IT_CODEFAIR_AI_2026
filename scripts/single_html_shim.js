// Single-file test build (scripts/single_html.py): the screen's API requests are answered from
// the server's answers captured at build time. Word search and signing run here, ported from
// readmark/serve.py and readmark/record; anything that needs the AI or a saved file says so.
(() => {
  const DATA = window.READMARK_SNAPSHOT;
  const OFFLINE = 'This single-file test build only opens the two showcase cases. Uploads, new question lists and meaning search need the full Readmark app.';
  const reply = (status, body) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
  const answer = (path, cid) => DATA.answers[cid ? `${path}?case=${cid}` : path]?.body;
  const realFetch = window.fetch.bind(window);

  window.fetch = async (input, init = {}) => {
    const url = new URL(typeof input === 'string' ? input : String(input.url || input), location.href);
    // On file:// a root path keeps the drive letter (file:///C:/api/view), so find /api/.
    const at = url.pathname.indexOf('/api/');
    if (at < 0) return realFetch(input, init);
    const path = url.pathname.slice(at);
    const cid = url.searchParams.get('case');
    const method = (init.method || 'GET').toUpperCase();
    if (method === 'POST' && path === '/api/records') return sign(cid, JSON.parse(init.body));
    if (method !== 'GET') return reply(503, { detail: OFFLINE });
    if (path === '/api/search') return reply(200, search(cid, url.searchParams.get('q') || '', url.searchParams.get('meaning') === 'true'));
    if (/^\/api\/(passages|question-lists\/[^/]+\/passages)\//.test(path)) return reply(DATA.policy_closed.status, DATA.policy_closed.body);
    const hit = DATA.answers[cid ? `${path}?case=${cid}` : path];
    return hit ? reply(hit.status, hit.body) : reply(503, { detail: OFFLINE });
  };

  const casePassages = (cid) => answer('/api/case-pages', cid).pages.flatMap((p) => p.passages);

  // ---- Word search: serve.word_ranges, result and grouped. Policy pages are not in this build.
  const W = '\\p{L}\\p{N}_';
  function wordRanges(text, query) {
    const words = query.match(new RegExp(`[${W}]+`, 'gu'));
    if (!words) return [];
    const body = words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('\\s+');
    return [...text.matchAll(new RegExp(`(?<![${W}])${body}(?![${W}])`, 'giu'))].map((m) => [m.index, m.index + m[0].length]);
  }
  function result(p, ranges) {
    const text = p.text;
    let start = Math.max(0, (ranges.length ? ranges[0][0] : 0) - 65);
    if (start && !/\s/.test(text[start - 1])) {
      const boundary = text.indexOf(' ', start);
      if (boundary !== -1 && boundary < ranges[0][0]) start = boundary + 1;
    }
    const end = Math.min(text.length, Math.max(start + 200, ranges.length ? ranges[0][1] : 0));
    const marks = ranges.filter(([a, b]) => a < end && b > start).map(([a, b]) => [Math.max(a, start) - start, Math.min(b, end) - start]);
    return {
      passage_id: p.passage_id, kind: p.source, exists: true,
      document: p.doc_id || p.policy || `${p.doc_title}:${p.doc_date}`,
      doc_title: p.doc_title || 'Case file', doc_date: p.doc_date ?? null, page: p.page,
      doc_page: 'doc_page' in p ? p.doc_page : p.page,
      snippet: text.slice(start, end), before: start > 0, after: end < text.length,
      ranges: marks, match_ranges: ranges, label: 'found by words', score: null,
    };
  }
  function search(cid, q, meaning) {
    const query = q.trim();
    if (!query) return { mode: 'word search', groups: [], calls: 0, seconds: 0 };
    const groups = new Map();
    casePassages(cid).map((p) => [p, wordRanges(p.text, query)]).filter(([, r]) => r.length)
      .forEach(([p, r], i) => {
        const item = result(p, r);
        const key = `${item.kind}\u0000${item.document}`;
        if (!groups.has(key)) groups.set(key, { title: item.doc_title, kind: item.kind, results: [] });
        groups.get(key).results.push({ ...item, rank: i + 1 });
      });
    return { mode: meaning ? 'word search (offline)' : 'word search', groups: [...groups.values()], calls: 0, seconds: 0, policies_available: false };
  }

  // ---- Signing: record.validate and record.build. The record lives in this tab only.
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const OUTCOMES = { met: 'Met', not_met: 'Not met', cannot_decide: 'Cannot decide yet' };
  const day = (iso) => /^\d{4}-\d{2}-\d{2}$/.test(iso || '') ? `${+iso.slice(8)} ${MONTHS[+iso.slice(5, 7) - 1]} ${iso.slice(0, 4)}` : String(iso || '');
  function sourceLabel(s) {
    if (!s.exists) return 'A passage that is not in the file';
    if (s.kind === 'policy') {
      const section = (s.section || '').trim();
      return `${s.doc_title}${section ? ` ${section}` : ''}, page ${s.page}`;
    }
    return `Page ${s.page}, paragraph ${s.passage_id.split(':').pop()} · ${s.doc_title} (${day(s.doc_date)})`;
  }
  const clauseLabel = (c) => c.clause_id === 'other' ? 'Background facts (no decision needed)' : c.source ? `${c.title}, ${c.source}` : c.title;
  function noteResult(claim, view) {
    if (claim.status === 'quote_not_found') return 'Quote not found in the file';
    if (claim.status === 'contradicted') {
      const pages = [...new Set(claim.contradicted_by.map((pid) => view.sources[pid].page))];
      return pages.length === 1 ? `Page ${pages[0]} says the opposite` : `Pages ${pages.join(', ')} say the opposite`;
    }
    if (claim.status === 'checker_disagrees') return 'The second reader is not sure';
    return claim.status === 'supported' ? 'Found in the file ✓' : 'Nothing to check';
  }
  const page = (pid) => pid.slice(0, pid.lastIndexOf(':'));

  function sign(cid, payload) {
    const view = answer('/api/view', cid);
    const spec = answer('/api/question-list', cid);
    const seconds = DATA.answers['/api/settings'].body.opened_seconds;
    // Search can open case passages the view does not cite; add them as the server does.
    const sources = { ...view.sources };
    const opened = payload.passages_opened || [];
    for (const p of casePassages(cid)) {
      if (!sources[p.passage_id] && opened.some((o) => o.passage_id === p.passage_id)) {
        const { text, ...meta } = p;
        sources[p.passage_id] = { ...meta, kind: p.source, exists: true };
      }
    }
    const problems = [];
    if (!(payload.decision in spec.decisions)) problems.push('Choose a decision.');
    if (!String(payload.reason || '').trim()) problems.push('Write a reason.');
    const outcomes = payload.clause_outcomes || {};
    for (const c of view.clauses) if (c.clause_id !== 'other' && !(outcomes[c.clause_id] in OUTCOMES)) problems.push(`Set an outcome for ${c.title}.`);
    for (const p of opened) {
      if (!sources[p.passage_id]) problems.push(`Unknown passage ${p.passage_id}.`);
      else if (typeof p.seconds_in_view !== 'number' || !Number.isFinite(p.seconds_in_view) || p.seconds_in_view < seconds || !p.opened_at) {
        problems.push(`Open ${sourceLabel(sources[p.passage_id])} for at least ${seconds} seconds in view.`);
      }
    }
    const openedPages = new Set(opened.filter((p) => sources[p.passage_id]).map((p) => page(p.passage_id)));
    for (const item of view.required_reading) {
      if (!openedPages.has(page(item.passage_id))) problems.push(`Open required page ${sourceLabel(sources[item.passage_id]).toLowerCase()}.`);
    }
    const claims = Object.fromEntries(view.claims.map((c) => [c.claim_id, c]));
    for (const d of payload.disputes || []) if (!claims[d.claim_id] || !String(d.reason || '').trim()) problems.push('Each dispute needs a known claim and a reason.');
    if (problems.length) return reply(422, { problems });

    const now = new Date();
    const off = -now.getTimezoneOffset();
    const two = (n) => String(Math.floor(Math.abs(n))).padStart(2, '0');
    const signedAt = new Date(now.getTime() + off * 60000).toISOString().slice(0, 19) + (off >= 0 ? '+' : '-') + two(off / 60) + ':' + two(off % 60);
    const tag = [...crypto.getRandomValues(new Uint8Array(3))].map((b) => b.toString(16).padStart(2, '0')).join('');
    const required = new Set(view.required_reading.map((i) => page(i.passage_id)));
    const clauses = Object.fromEntries(view.clauses.map((c) => [c.clause_id, c]));
    const record = {
      record_id: `${view.case.case_id}-${signedAt.replace(/\D/g, '').slice(0, 14)}-${tag}`,
      case_id: view.case.case_id,
      labels: spec.labels, decisions: spec.decisions,
      integrity: {
        case_sha256: view.case.sha256,
        case_note: 'SHA-256 of the synthetic case file used for these checks.',
        view_note: 'Signed in the single-file test build: this record is kept in this browser tab only and is not saved.',
      },
      signed_at: signedAt,
      officer: String(payload.officer || spec.labels.officer),
      decision: payload.decision,
      reason: String(payload.reason).trim(),
      clause_outcomes: view.clauses.filter((c) => c.clause_id !== 'other').map((c) => ({ clause_id: c.clause_id, title: c.title, outcome: outcomes[c.clause_id] })),
      passages_opened: opened.map((p) => ({
        passage_id: p.passage_id, label: sourceLabel(sources[p.passage_id]), required: required.has(page(p.passage_id)),
        opened_at: String(p.opened_at), seconds_in_view: Math.round(p.seconds_in_view * 10) / 10,
      })),
      disputes: (payload.disputes || []).map((d) => {
        const claim = claims[d.claim_id];
        return {
          claim_id: d.claim_id, claim: claim.claim, clause_id: claim.clause_id, clause: clauseLabel(clauses[claim.clause_id]),
          check_result: noteResult(claim, view),
          citations: claim.citations.map((q) => ({ ...q, label: sourceLabel(sources[q.passage_id]) })),
          reason: String(d.reason).trim(), at: String(d.at || ''),
        };
      }),
      models: view.models,
      note: `A page counts as opened after a passage on it has ${seconds} seconds in view, accumulated across visits. The viewed passage is recorded; it does not prove the whole page was read.`,
    };
    // record.for_export: the officer-facing JSON uses question names and note text.
    const { clause_outcomes: outs, passages_opened: pages, disputes, decision, ...rest } = record;
    const exported = {
      ...rest,
      case_name: `${record.labels.case_noun} ${record.case_id}`,
      decision: record.decisions[decision],
      answers_label: 'Your answers to the questions',
      question_answers: outs.map((o) => ({ question: o.title, answer: OUTCOMES[o.outcome] })),
      passages_opened: pages.map(({ passage_id: _, ...p }) => p),
      disputes: disputes.map((d) => ({
        note: d.claim, question: d.clause, check_result: d.check_result, reason: d.reason, at: d.at,
        quotes: d.citations.map((q) => ({ quote: q.quote, source: q.label, check_result: q.quote_found ? 'Found in the file ✓' : 'Quote not found in the file' })),
      })),
    };
    const jsonUrl = URL.createObjectURL(new Blob([JSON.stringify(exported, null, 2)], { type: 'application/json' }));
    return reply(200, { record, json_url: jsonUrl, html_url: '#export-html' });
  }

  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href]');
    if (!link) return;
    const href = link.getAttribute('href');
    if (href === '#export-html') {
      // The standalone record is the signed record as shown on screen, with the same styles.
      e.preventDefault();
      const record = document.querySelector('[data-testid="record"]').cloneNode(true);
      record.querySelector('.exports')?.remove();
      const doc = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Decision record</title><style>${document.querySelector('style').textContent}</style></head><body class="doc"><main class="wrap">${record.outerHTML}</main></body></html>`;
      window.open(URL.createObjectURL(new Blob([doc], { type: 'text/html' })), '_blank');
    } else if (href.startsWith('/?')) {
      // Links written for the server's root become this file's own address.
      e.preventDefault();
      location.search = href.slice(1);
    }
  }, true);

  document.addEventListener('DOMContentLoaded', () => {
    const note = document.createElement('p');
    note.setAttribute('role', 'note');
    note.style.cssText = 'margin:0;padding:8px 32px;background:var(--warning-bg);font-size:14px';
    note.textContent = 'Test build in one file: the two showcase cases from their saved results, offline. Full policy pages, uploads, new question lists and meaning search need the full app. A signed record stays in this tab only.';
    document.body.prepend(note);
  });
})();
