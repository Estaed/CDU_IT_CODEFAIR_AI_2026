// Government question pages: the original file and officer's outcome inside each question.
// Verified quotes are marked in place; claims and the full file are one click away.
// Reads /api/view (runs/<case>/view.json), opens one passage at a time and logs its time in view,
// keeps the officer's clause outcomes and disputes, and posts the decision record. The AI never
// fills a clause outcome; the officer sets every one. The main screen speaks in plain words: no
// claim ids, no model ids (those sit under "About these checks"), no per-claim probability.
'use strict';

// ---- Lucide icons, outline 1.75 ----
const I = {
  check: '<path d="M20 6 9 17l-5-5"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
  landmark: '<line x1="3" x2="21" y1="22" y2="22"/><line x1="6" x2="6" y1="18" y2="11"/><line x1="10" x2="10" y1="18" y2="11"/><line x1="14" x2="14" y1="18" y2="11"/><line x1="18" x2="18" y1="18" y2="11"/><polygon points="12 2 20 7 4 7"/>',
  flask: '<path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"/><path d="M8.5 2h7"/><path d="M7 16h10"/>',
  flag: '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/>',
  arrow: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  clock: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
  pen: '<path d="M12 20h9"/><path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838a.5.5 0 0 1-.62-.62l.838-2.872a2 2 0 0 1 .506-.854z"/>',
  ring: '<circle cx="12" cy="12" r="7"/>',
  pause: '<circle cx="12" cy="12" r="10"/><line x1="10" x2="10" y1="15" y2="9"/><line x1="14" x2="14" y1="15" y2="9"/>',
  searchx: '<path d="m13.5 8.5-5 5"/><path d="m8.5 8.5 5 5"/><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  arrows: '<path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/>',
  neq: '<line x1="5" x2="19" y1="9" y2="9"/><line x1="5" x2="19" y1="15" y2="15"/><line x1="19" x2="5" y1="5" y2="19"/>',
  help: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
  slash: '<circle cx="12" cy="12" r="10"/><line x1="9" x2="15" y1="15" y2="9"/>',
  minus: '<path d="M5 12h14"/>',
};
const icon = (n) => `<svg class="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${I[n]}</svg>`;
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const $ = (id) => document.getElementById(id);
const num = (n) => `<span class="mono">${n}</span>`;
const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s);

// Three status lists, kept apart: claim checks, clause coverage, the officer's outcome. Each status
// is a word with its own icon, so colour is never the only signal.
const CLAIM_STATUS = {
  supported: ['Supported', 'check', 'ok'],
  contradicted: ['Contradicted by another passage', 'arrows', 'warn'],
  checker_disagrees: ['Checker disagrees', 'neq', 'warn'],
  quote_not_found: ['Quote not found', 'searchx', 'bad'],
  none: ['Nothing to check', 'minus', 'neutral'],
};
const OUTCOMES = [['met', 'Met', 'check'], ['not_met', 'Not met', 'x'], ['cannot_decide', 'Cannot decide yet', 'pause']];
const OUTCOME_LABEL = Object.fromEntries(OUTCOMES.map(([v, l]) => [v, l]));
const DECISIONS = [['approve', 'Approve priority housing'], ['decline', 'Decline'], ['request_information', 'Request more information']];
const DECISION_LABEL = Object.fromEntries(DECISIONS);
const POLICY_SHORT = { eligibility: 'Eligibility', priority: 'Priority', identification: 'Identification', dfv: 'Domestic and family violence', discretion: 'Discretionary decisions' };
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const INTRO_KEY = 'readmark-intro-dismissed';

function stored(key) {
  try { return window.localStorage.getItem(key); } catch { return null; }
}
function store(key, value) {
  try {
    if (value === null) window.localStorage.removeItem(key);
    else window.localStorage.setItem(key, value);
  } catch { /* private mode: the panel simply shows again next time */ }
}

const S = {
  view: null,
  pages: [],         // full synthetic pages from the pinned case file, never the audit block
  annotations: [],  // verified quotes and scan hits, labelled by question
  cleanOpen: false,
  claimOpen: false,
  readerPage: 1,
  tab: null,        // document/page key in the selected question
  morePages: false,
  fullFile: false,
  policyInline: false,
  sel: null,         // a clause_id, or 'signoff'
  opened: {},        // passage_id -> {opened_at, seconds}
  current: null,     // {pid, claimIds}: the one passage in view
  since: null,       // performance.now() when the open passage became visible
  outcomes: {},      // clause_id -> met | not_met | cannot_decide (officer only)
  disputes: {},      // claim_id -> {reason, at}
  disputing: null,
  disputeErr: false,
  step: 'decide',    // sign-off: decide | check
  decision: null,
  reason: '',
  formErr: '',
  signErr: '',
  signed: null,
  policyText: {},    // passage_id -> text, or false when the server could not read it
  intro: !stored(INTRO_KEY),
};

// ---- Time in view: only the open passage accrues, and only while it can be seen ----
function pause() {
  if (S.current && S.since !== null) S.opened[S.current.pid].seconds += (performance.now() - S.since) / 1000;
  S.since = null;
}
function resume() {
  if (S.since === null && passageVisible()) S.since = performance.now();
}
function secondsInView(pid) {
  const o = S.opened[pid];
  if (!o) return 0;
  const live = S.current && S.current.pid === pid && S.since !== null ? (performance.now() - S.since) / 1000 : 0;
  return o.seconds + live;
}
document.addEventListener('visibilitychange', () => (document.hidden ? pause() : resume()));

function closePassage() {
  pause();
  S.current = null;
}

function openPassage(pid, claimIds = [], inline = false) {
  if (S.signed) return;
  pause();
  if ($('policy').open) $('policy').close();
  if ($('comparison').open) $('comparison').close();
  const s = src(pid);
  if (!s || !s.exists) { S.current = null; render(); return; }
  if (!S.opened[pid]) S.opened[pid] = { opened_at: new Date().toISOString(), seconds: 0 };
  S.current = { pid, claimIds };
  S.policyInline = inline && s.kind === 'policy';
  if (!S.fullFile && (s.kind === 'case' || inline)) S.tab = pageKey(s);
  if (s && s.kind === 'policy' && !(pid in S.policyText)) {
    fetch(`/api/passages/${encodeURIComponent(pid)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { S.policyText[pid] = d ? d.text : false; renderPane(); if (S.policyInline) renderReader(); watchPassage(); })
      .catch(() => { S.policyText[pid] = false; renderPane(); if (S.policyInline) renderReader(); });
  }
  render();
  if (s && s.kind === 'policy' && !inline) {
    $('policy').showModal();
    watchPassage();
  } else jumpToPassage(pid, claimIds);
}

// ---- The view, read in plain words ----
const src = (pid) => S.view.sources[pid];
const claimById = (id) => S.view.claims.find((c) => c.claim_id === id);
const clauseById = (id) => S.view.clauses.find((c) => c.clause_id === id);
const decisive = () => S.view.clauses.filter((c) => c.clause_id !== 'other');
const required = () => S.view.required_reading;
const isRequired = (pid) => required().some((r) => r.passage_id === pid);
const flaggedFor = (cid) => required().filter((r) => r.clause_ids.includes(cid));
// "Other facts" joins the list only when it holds something; it never takes an outcome.
const railClauses = () => S.view.clauses.filter((c) => c.clause_id !== 'other'
  || c.claim_ids.length || c.missing.length || flaggedFor('other').length).sort((a, b) => {
  const rank = (c) => flaggedFor(c.clause_id)[0]?.rank ?? (questionFlag(c) ? 100 : 200);
  return rank(a) - rank(b);
});

const shortName = (cl) => cl.clause_id === 'other' ? 'Other facts' : cl.title;

function questionFlag(cl) {
  if (cl.contradictions.length) return 'Two pages disagree';
  const claims = cl.claim_ids.map(claimById).filter(Boolean);
  if (claims.some((c) => c.status === 'quote_not_found')) return 'Quote not found';
  if (cl.missing.length || cl.coverage === 'no_evidence_in_file') {
    return cl.clause_id === 'elig-income' ? 'Income evidence not found' : 'Evidence not found';
  }
  if (claims.some((c) => c.status !== 'supported')) return 'Checker disagrees';
  if (flaggedFor(cl.clause_id).length) return 'Possibly missed evidence';
  return '';
}

function fmtDate(d) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d || '');
  return m ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}` : String(d || '');
}
const fmtTime = (iso) => new Date(iso).toLocaleTimeString('en-AU', { hour12: false });
const fmtStamp = (iso) => `${new Date(iso).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })}, ${fmtTime(iso)}`;

// "page 8, paragraph 3" for the file; "Eligibility §3.4, page 6" for a policy.
function loc(pid) {
  const s = src(pid);
  if (!s || !s.exists) return 'a passage that is not in the file';
  if (s.kind === 'policy') {
    const sec = s.section ? ` ${s.section.split(' ')[0]}` : '';
    return `${POLICY_SHORT[pid.split(':')[0]] || s.doc_title}${sec}, page ${s.page}`;
  }
  return `page ${s.page}, paragraph ${pid.split(':').pop()}`;
}
function docLine(pid) {
  const s = src(pid);
  if (!s || !s.exists) return '';
  if (s.kind === 'policy') return `${s.doc_title}${s.section ? `, ${s.section}` : ''}`;
  return `${s.doc_title} · ${fmtDate(s.doc_date)}`;
}
function kindTag(pid) {
  const s = src(pid);
  if (!s || !s.exists) return '';
  return s.kind === 'policy' ? `<span class="tag">${icon('landmark')}Real NT policy</span>` : `<span class="tag">${icon('flask')}Synthetic file</span>`;
}
const clauseName = (cl) => (cl.clause_id === 'other' ? 'Other facts' : cl.source ? `${cl.title}, ${cl.source}` : cl.title);

function clauseState(cl) {
  const flagged = flaggedFor(cl.clause_id);
  const opened = flagged.filter((r) => S.opened[r.passage_id]).length;
  const needsOutcome = cl.clause_id !== 'other';
  const outcome = S.outcomes[cl.clause_id] || null;
  return { flagged, opened, needsOutcome, outcome, done: opened === flagged.length && (!needsOutcome || !!outcome) };
}
const ready = () => required().every((r) => S.opened[r.passage_id]) && decisive().every((c) => S.outcomes[c.clause_id]);

// The one next action: from the selected clause onward (wrapping), the first clause with work
// left; inside it, its unopened flagged passages (most decisive first), then its outcome.
function nextAction() {
  if (S.signed) return { kind: 'record' };
  const list = railClauses();
  const start = Math.max(0, list.findIndex((c) => c.clause_id === S.sel));
  for (let i = 0; i < list.length; i += 1) {
    const cl = list[(start + i) % list.length];
    const st = clauseState(cl);
    const unopened = st.flagged.find((r) => !S.opened[r.passage_id]);
    if (unopened) return { kind: 'passage', clause: cl, pid: unopened.passage_id };
    if (st.needsOutcome && !st.outcome) return { kind: 'outcome', clause: cl };
  }
  return { kind: 'sign' };
}

// ---- Why, in one plain sentence ----
function pairsWith(pid) {
  return S.view.clauses.flatMap((c) => c.contradictions).filter((p) => p.a === pid || p.b === pid);
}
function relation(other, mine) {
  const a = src(other) && src(other).doc_date;
  const b = mine && src(mine) && src(mine).doc_date;
  if (!a || !b || a === b) return 'another record';
  return a > b ? 'a later record' : 'an earlier record';
}
function whenOf(pid) {
  const s = src(pid);
  return s && s.kind === 'case' && s.doc_date ? ` (${fmtDate(s.doc_date)})` : '';
}
function quoteProblem(claim) {
  if (!claim.citations.length) return 'The claim gives no quote, so nothing in the file backs it.';
  const parts = [];
  if (claim.citations.some((c) => !c.passage_exists)) parts.push('It cites a passage that is not in the file.');
  if (claim.citations.some((c) => c.passage_exists && !c.quote_found)) parts.push('A quote is not word for word in the passage it cites (marked on the quote).');
  if (claim.values_missing.length) {
    const vals = claim.values_missing.map((v) => num(esc(v))).join(', ');
    parts.push(claim.citations.every((c) => c.quote_found)
      ? `Its quotes are in the file, but none contains ${vals}.`
      : `No quote contains ${vals}.`);
  }
  return parts.join(' ');
}
function contradictionReason(claim) {
  const cited = new Set(claim.citations.map((c) => c.passage_id));
  const parts = claim.contradicted_by.map((other) => {
    const pair = pairsWith(other).find((p) => cited.has(p.a === other ? p.b : p.a));
    const mine = pair ? (pair.a === other ? pair.b : pair.a) : null;
    if (!mine) return `${esc(loc(other))}${whenOf(other)} disagrees with a passage this claim quotes`;
    return `${esc(loc(mine))}, which this claim quotes, disagrees with ${esc(loc(other))}, ${relation(other, mine)}${whenOf(other)}`;
  });
  const clean = claim.citations.length && claim.citations.every((c) => c.quote_found) && !claim.values_missing.length;
  const tail = clean ? 'The quote is word for word: the flag means two records disagree, not that this claim is false.' : quoteProblem(claim);
  return `${cap(parts.join('; '))}. ${tail} Open both and decide which one holds.`;
}
function claimReason(claim) {
  const ch = claim.checker;
  if (claim.status === 'supported') {
    return ch && ch.verdict
      ? 'Quoted word for word, figures and dates included, and the second checker agrees.'
      : 'Quoted word for word, figures and dates included. The second checker did not run.';
  }
  if (claim.status === 'checker_disagrees') {
    return ch && ch.verdict === 'contradicts'
      ? 'The quote is in the file, but the second checker reads the passage as saying something else. Open it and judge.'
      : 'The quote is in the file, but the second checker could not confirm that the passage says this. Open it and judge.';
  }
  if (claim.status === 'contradicted') return contradictionReason(claim);
  return `${quoteProblem(claim)} Open the passage and judge.`;
}
// ---- Pieces shared by several views ----
function pill(kind, cls, label, testid = '') {
  return `<span class="pill ${cls}"${testid ? ` data-testid="${testid}"` : ''}>${icon(kind)}${esc(label)}</span>`;
}
function statusPill(status, testid = '') {
  const [label, ic, cls] = CLAIM_STATUS[status];
  return pill(ic, cls, label, testid);
}
function passageRow(pid, { task = false, testid = 'passage-item' } = {}) {
  const o = S.opened[pid];
  const cur = S.current && S.current.pid === pid;
  let state = o ? 'Opened' : task ? 'Must open' : 'Open';
  if (cur) state = 'Opened · in view';
  const s = src(pid);
  const samePage = s?.kind === 'case' && required().filter((r) => src(r.passage_id)?.kind === 'case' && src(r.passage_id).page === s.page).length;
  const label = task && s?.kind === 'case' && samePage === 1 ? `Page ${s.page}` : cap(loc(pid));
  return `<li><button class="prow ${o ? 'opened' : ''} ${cur ? 'is-cur' : ''} ${task ? 'task' : ''}" data-act="open" data-arg="${esc(pid)}" data-testid="${testid}" data-pid="${esc(pid)}"${S.signed ? ' disabled' : ''}>
    <span class="pst">${icon(o ? 'check' : task ? 'ring' : 'file')}</span>
    <span class="pmain"><span class="ploc">${esc(label)}</span></span>
    <span class="pstate"><span class="ps">${state}${!o && !cur ? icon('arrow') : ''}</span></span></button></li>`;
}
function quoteHtml(claim, c, testid = 'quote') {
  const cur = S.current && S.current.pid === c.passage_id;
  return `<button class="quote ${c.quote_found ? '' : 'quote-bad'} ${cur ? 'is-cur' : ''}" data-act="open" data-arg="${esc(c.passage_id)}" data-claims="${esc(claim.claim_id)}" data-testid="${testid}" data-pid="${esc(c.passage_id)}"${S.signed ? ' disabled' : ''}>
    <span class="q">“${esc(c.quote)}”</span>
    <span class="cite"><span class="loc">${esc(cap(loc(c.passage_id)))}</span><span>${esc(docLine(c.passage_id))}</span>${kindTag(c.passage_id)}
      ${c.quote_found ? '' : `<span class="qflag">${icon('x')}Not word for word in this passage</span>`}
      ${S.opened[c.passage_id] ? `<span class="tag done">${icon('check')}Opened</span>` : ''}</span></button>`;
}
// ---- Case bar: the file, both counters, the one next action ----
function renderBar() {
  const v = S.view;
  $('caseId').textContent = v.case.case_id;
  $('caseFacts').textContent = `${v.case.pages} pages · ${v.case.synthetic ? 'synthetic case' : 'applicant file'}`;
  const n = nextAction();
  let label;
  let hint;
  if (n.kind === 'passage') { label = src(n.pid)?.kind === 'case' ? `Open page ${src(n.pid).page}` : `Open ${loc(n.pid)}`; hint = `Next step in ${shortName(n.clause)}`; }
  else if (n.kind === 'outcome') { label = 'Set your outcome'; hint = `Next step in ${n.clause.title}`; }
  else if (n.kind === 'sign') { label = 'Sign decision'; hint = 'Next step · everything is ready'; }
  else { label = 'View the record'; hint = 'Decision signed'; }
  const target = n.kind === 'passage' ? `passage:${n.pid}` : n.kind === 'outcome' ? `outcome:${n.clause.clause_id}` : n.kind;
  $('next').innerHTML = `<span class="sr" data-testid="next-hint">${esc(hint)}</span>
      <button class="btn-primary" data-act="next" data-testid="next-action" data-next="${esc(target)}" title="${esc(hint)}">Next: ${esc(label[0].toLowerCase() + label.slice(1))}${icon('arrow')}</button>
      <button class="btn-secondary" data-act="sign" data-testid="sign-btn">${S.signed ? 'Decision record' : 'Sign decision'}</button>`;
}

function renderJob() {
  const v = S.view;
  $('job').innerHTML = `<b>Your job:</b> decide this application. Open each flagged passage, set all ${num(decisive().length)} question outcomes, then sign.`;
  document.title = `Readmark · Applicant file ${v.case.case_id}`;
}

// ---- First-run panel, recallable with "How this works" ----
function renderIntro() {
  const box = $('intro');
  box.hidden = !S.intro;
  box.innerHTML = S.intro ? `<div class="intro" data-testid="intro">
    <div class="intro-head"><div><div class="eyebrow">How this works</div>
      <h2>Follow the highlights. <span class="accent">You</span> decide.</h2></div>
      <button class="btn-secondary" data-act="intro-close" data-testid="intro-dismiss">Got it</button></div>
    <ol class="intro-steps">
      <li><b>What the AI did</b><span>Matched evidence to the questions. Its claims are behind “AI claims”.</span></li>
      <li><b>What the checks flagged</b><span>Highlighted words sit in the real file. Open the ${num(required().length)} required passages; other highlights are optional.</span></li>
      <li><b>What you decide</b><span>Set all ${num(decisive().length)} outcomes, then sign. Missing evidence never means “not met”.</span></li>
    </ol></div>` : '';
}

// Required flags lead; optional scan hits stay available without expanding the clean questions.
function renderRail() {
  const row = (cl) => {
    const st = clauseState(cl);
    const id = cl.clause_id;
    const sel = S.sel === id;
    const status = st.outcome ? `Decided: ${OUTCOME_LABEL[st.outcome]}` : id === 'other' ? 'No outcome needed' : questionFlag(cl) || 'Looks clean · not decided';
    return `<button class="rrow ${sel ? 'is-sel' : ''}"
      data-act="clause" data-arg="${esc(id)}" data-testid="clause-row" data-clause="${esc(id)}" aria-current="${sel}">
      <span class="task-icon ${questionFlag(cl) && !st.outcome ? 'flag' : ''}">${st.outcome ? '✓' : questionFlag(cl) ? '!' : id === 'other' ? '–' : ''}</span>
      <span><span class="rname">${esc(shortName(cl))}</span>
      <span class="rstat">${esc(status)}${st.flagged.length ? ` · ${st.opened} of ${st.flagged.length} opened` : ''}</span></span></button>`;
  };
  const flagged = railClauses().filter((c) => c.clause_id !== 'other' && questionFlag(c));
  const clean = decisive().filter((c) => !questionFlag(c));
  const other = railClauses().filter((c) => c.clause_id === 'other');
  const sign = S.signed ? 'Signed · record locked' : ready() ? 'Ready to sign' : `${missingItems().length} questions to finish · cannot start yet`;
  const nSet = decisive().filter((c) => S.outcomes[c.clause_id]).length;
  const nOpen = required().filter((r) => S.opened[r.passage_id]).length;
  $('rail').innerHTML = `<h2>Decide these questions</h2><div class="counters" id="counters" aria-live="polite">
    <span data-testid="outcome-counter"><b id="outcomeCount">${nSet}</b> of ${decisive().length} decided</span> ·
    <span data-testid="passage-counter"><b id="passageCount">${nOpen}</b> of ${required().length} required opened</span></div>
    <div class="rail-list">${flagged.map(row).join('')}</div>
    ${clean.length ? `<details class="rail-list clean-group" data-testid="clean-questions"${S.cleanOpen ? ' open' : ''}>
      <summary data-testid="clean-toggle">${clean.length} ${clean.length === 1 ? 'question looks' : 'questions look'} clean
        <span class="sub"> · ${clean.filter((c) => S.outcomes[c.clause_id]).length} decided</span></summary>
      ${clean.map(row).join('')}</details>` : ''}
    ${other.length ? `<details class="rail-list other-group"><summary>Other facts · no outcome needed</summary>${other.map(row).join('')}</details>` : ''}
    <div class="rail-list"><button class="rrow signrow ${S.sel === 'signoff' ? 'is-sel' : ''}" data-act="signoff" data-testid="signoff-row">
      <span class="task-icon">${S.signed ? '✓' : '–'}</span><span><span class="rname">Sign decision</span><span class="rstat">${sign}</span></span></button></div>`;
}

// ---- Right: the selected clause ----
function claimItem(claim) {
  const id = claim.claim_id;
  const d = S.disputes[id];
  const quotes = claim.citations.map((c) => quoteHtml(claim, c)).join('')
    || `<div class="noquote">${icon('searchx')}Quote not found: no quote given</div>`;
  let action = S.signed ? '' : `<button class="act muted" data-act="dispute" data-arg="${esc(id)}" data-testid="dispute-btn">${icon('flag')}Dispute</button>`;
  let body = '';
  if (S.disputing === id && !S.signed) {
    action = '';
    body = `<div class="dispute"><label for="dr-${esc(id)}">Why is this claim wrong? Your reason goes on the decision record.</label>
      <textarea id="dr-${esc(id)}" data-testid="dispute-reason">${esc(d ? d.reason : '')}</textarea>
      ${S.disputeErr ? `<div class="helper err">${icon('alert')}Write a reason. A dispute without one cannot go on the record.</div>` : ''}
      <div class="dlg-actions"><button class="act muted" data-act="dispute-cancel" data-arg="${esc(id)}">Cancel</button>
        <button class="btn-secondary" data-act="dispute-save" data-arg="${esc(id)}" data-testid="dispute-save">Save dispute</button></div></div>`;
  } else if (d) {
    action = '';
    body = `<div class="dispute saved" data-testid="dispute-saved">${icon('flag')}<div class="spacer"><b>Disputed by you</b> at ${num(fmtTime(d.at))}: ${esc(d.reason)}</div>
      ${S.signed ? '' : `<button class="act muted" data-act="dispute" data-arg="${esc(id)}">Edit</button><button class="act muted" data-act="dispute-withdraw" data-arg="${esc(id)}">Withdraw</button>`}</div>`;
  }
  return `<article class="item" data-testid="claim" data-status="${claim.status}">
    <div class="quotes">${quotes}</div>
    <div class="claimline"><span class="tag ai">AI claim</span><span>${esc(claim.claim)}</span></div>
    <div class="statusline"><span class="list-label">Claim check</span>${statusPill(claim.status)}<span class="spacer"></span>${action}</div>
    <p class="why">${claimReason(claim)}</p>${body}</article>`;
}

function clauseView(cl) {
  const id = cl.clause_id;
  const st = clauseState(cl);
  const claims = cl.claim_ids.map(claimById).filter(Boolean);
  const badQuotes = claims.filter((c) => !c.citations.length || c.citations.some((q) => !q.quote_found));
  const gaps = cl.missing.map((m) => `<p>${esc(m.statement)}</p>`).join('')
    || (cl.coverage === 'no_evidence_in_file' ? '<p>No evidence in file.</p>' : '');
  const flagged = st.flagged.length ? `<section class="must" data-testid="flagged">
    <b>Open before you sign</b>
    <ul class="plist">${st.flagged.map((r) => passageRow(r.passage_id, { task: true, testid: 'flagged-item' })).join('')}</ul></section>` : '';
  // Several conflicting paragraphs can share a page pair; offer that comparison once.
  const uniquePairs = new Map();
  cl.contradictions.forEach((p) => {
    const key = [src(p.a).page, src(p.b).page].sort((a, b) => a - b).join(':');
    if (!uniquePairs.has(key)) uniquePairs.set(key, p);
  });
  const pagePairs = [...uniquePairs.values()];
  const pairs = pagePairs.length ? `<div class="comparison-links" data-testid="pairs">
    ${pagePairs.map((p) => `<button class="btn-secondary compare-btn" data-act="compare" data-arg="${esc(p.a)}" data-other="${esc(p.b)}" data-testid="compare-pages"${S.signed ? ' disabled' : ''}>Compare pages ${src(p.a).page} and ${src(p.b).page}${icon('arrows')}</button>`).join('')}
    </div>` : '';
  const o = st.outcome;
  const flag = questionFlag(cl);
  const disagreeingPages = [...new Map(cl.contradictions.flatMap((p) => [p.a, p.b])
    .map((pid) => [src(pid).page, pid])).values()];
  const pageNames = disagreeingPages.map((pid, i) => `${i ? 'page' : 'Page'} ${src(pid).page}${whenOf(pid)}`);
  const warning = pagePairs.length ? `${pageNames.slice(0, -1).join(', ')} and ${pageNames.at(-1)} disagree; open ${pageNames.length === 2 ? 'both' : 'each page'} before you decide.`
    : flag.includes('evidence not found') || flag === 'Evidence not found' ? 'Missing evidence does not mean “not met”; decide whether the file lets you answer this question.'
    : flag === 'Checker disagrees' ? 'The quote is in the file, but the second checker could not confirm the claim; open the passage and judge.'
    : flag === 'Quote not found' ? 'A claim has no verified quote; open its AI claims to see what could not be checked.'
    : flag ? 'The scan found a relevant passage that no claim uses; open it and judge whether it changes this question.' : '';
  const list = railClauses().filter((c) => c.clause_id !== 'other');
  const number = list.findIndex((c) => c.clause_id === id) + 1;
  return `<div class="clause" data-testid="clause-detail" data-clause="${esc(id)}">
    <div class="d-head"><h2 data-testid="clause-title">${esc(shortName(cl))}</h2>
      <span class="sub">${id === 'other' ? 'No outcome needed' : `Question ${number} of ${decisive().length} · ${esc(cl.source || 'Policy question')}`}</span></div>
    ${cl.policy_sentence ? `<blockquote class="policy-inset">“${esc(cl.policy_sentence)}”</blockquote>` : ''}
    ${warning ? `<section class="warning-box" data-testid="question-warning"><span class="task-icon flag">!</span><div class="warning-copy"><div class="warning-heading"><b>${esc(disagreeingPages.length > 2 ? 'Pages in the file disagree' : flag)}</b></div><p>${warning}</p>${pairs}</div></section>` : ''}
    ${badQuotes.length ? `<section class="question-block quote-warning" data-testid="quote-warning">${icon('alert')}Quote not found for ${badQuotes.length} ${badQuotes.length === 1 ? 'claim' : 'claims'}. <button class="act" data-act="claims">Show claims</button></section>` : ''}
    <div class="question-split"><section class="reader" id="reader" aria-label="Applicant file pages"></section>
      <aside class="answer-panel">${id !== 'other' ? `<div class="outbar" data-testid="outcome-bar">
        <fieldset><legend>Is this question met?</legend><div class="opts">${OUTCOMES.map(([val, lab]) => `<label class="outcome-radio"><input type="radio" name="outcome" value="${val}" data-act="outcome" data-arg="${esc(id)}" data-val="${val}" data-outcome="${val}" data-testid="outcome-${esc(id)}-${val}"${o === val ? ' checked' : ''}${S.signed ? ' disabled' : ''}>${lab}</label>`).join('')}</div></fieldset>
        <span class="sr" data-testid="outcome-state">${o ? esc(OUTCOME_LABEL[o]) : 'not set'}</span>
        ${flagged}<button class="btn-primary" data-act="save-next" data-arg="${esc(id)}" data-testid="save-next"${S.signed ? ' disabled' : ''}>Save and next question</button>
        ${S.formErr ? `<p class="helper err" role="alert">${esc(S.formErr)}</p>` : ''}</div>` : '<p class="note">Other facts · no outcome needed.</p>'}</aside></div>
    ${gaps ? `<details class="question-block gaps" data-testid="gaps"><summary>Evidence not found · missing evidence does not mean “not met”</summary>${gaps}</details>` : ''}
    ${cl.policy_sentence ? `<details class="question-block"><summary>The policy question</summary><blockquote class="q">“${esc(cl.policy_sentence)}”</blockquote>
      ${cl.policy_items.length ? `<ul class="pitems">${cl.policy_items.map((i) => `<li>${esc(i)}</li>`).join('')}</ul>` : ''}
      <button class="act" data-act="open" data-arg="${esc(cl.policy_passage_id)}" data-testid="open-policy"${S.signed ? ' disabled' : ''}>Open policy passage${icon('arrow')}</button></details>` : ''}
    <details class="question-block claim-details" data-testid="claim-details"${S.claimOpen ? ' open' : ''}>
      <summary>AI claims · ${num(claims.length)}</summary><div class="items">${claims.map(claimItem).join('') || '<p class="note">No claim given.</p>'}</div></details>
  </div>`;
}

function saveNext(id) {
  if (!S.outcomes[id]) {
    S.formErr = 'Choose an outcome before saving this question.';
    render();
    return;
  }
  S.formErr = '';
  const list = railClauses().filter((c) => c.clause_id !== 'other');
  const start = list.findIndex((c) => c.clause_id === id);
  for (let i = 1; i <= list.length; i += 1) {
    const next = list[(start + i) % list.length];
    if (!S.outcomes[next.clause_id]) { selectClause(next.clause_id); return; }
  }
  selectSignoff();
}

// ---- Sign-off: what is missing, then the decision, then check your answers, then the record ----
function missingItems() {
  return railClauses().map((cl) => {
    const st = clauseState(cl);
    const left = st.flagged.length - st.opened;
    const parts = [];
    if (left) parts.push(`open ${left} flagged ${left === 1 ? 'passage' : 'passages'}`);
    if (st.needsOutcome && !st.outcome) parts.push('set your outcome');
    return parts.length ? { id: cl.clause_id, name: clauseName(cl), what: cap(parts.join(' and ')) } : null;
  }).filter(Boolean);
}
function signoffView() {
  if (S.signed) return recordView();
  if (!ready()) {
    const items = missingItems();
    return `<section class="signoff" data-testid="signoff">
      <div class="eyebrow">Sign off</div>
      <h2>Not ready to sign yet</h2>
      <p class="lead">Finish ${items.length === 1 ? 'this question' : `these ${num(items.length)} questions`} first. Each one opens when you select it.</p>
      <ul class="missing" data-testid="missing-list">${items.map((m) => `<li><button class="mrow" data-act="clause" data-arg="${esc(m.id)}" data-testid="missing-item" data-clause="${esc(m.id)}">
        <span><span class="mname">${esc(m.name)}</span><span class="mwhat">${esc(m.what)}</span></span>${icon('arrow')}</button></li>`).join('')}</ul>
    </section>`;
  }
  if (S.step === 'check') return checkView();
  return `<section class="signoff" data-testid="signoff">
    <div class="eyebrow">Sign off</div>
    <h2>Your decision</h2>
    <p class="lead">Every flagged passage is opened and all ${num(decisive().length)} outcomes are set. The decision and the reason are yours: Readmark makes no recommendation.</p>
    <fieldset><legend>Decision</legend><div class="opts">${DECISIONS.map(([val, lab]) => `<label class="opt"><input type="radio" name="decision" value="${val}" data-testid="decision-${val}"${S.decision === val ? ' checked' : ''}>${lab}</label>`).join('')}</div></fieldset>
    <label class="flabel" for="reason">Reason <span class="rq">Required</span></label>
    <textarea id="reason" data-testid="reason" placeholder="Why this decision, in your words. Name the questions and pages you relied on.">${esc(S.reason)}</textarea>
    <div class="helper ${S.formErr ? 'err' : ''}" data-testid="form-helper">${S.formErr ? `${icon('alert')}${esc(S.formErr)}` : 'Write it so the applicant could read and challenge it.'}</div>
    <div class="dlg-actions"><button class="btn-primary" data-act="continue" data-testid="continue-btn">Check your answers${icon('arrow')}</button></div>
  </section>`;
}
function checkView() {
  const change = (act, arg, what) => `<button class="act" data-act="${act}"${arg ? ` data-arg="${esc(arg)}"` : ''} data-testid="change">Change<span class="sr"> ${esc(what)}</span></button>`;
  const outcomes = decisive().map((cl) => `<div class="cya-row"><dt>${esc(clauseName(cl))}</dt><dd>${esc(OUTCOME_LABEL[S.outcomes[cl.clause_id]])}</dd><dd class="cya-act">${change('clause', cl.clause_id, cl.title)}</dd></div>`).join('');
  const disputes = Object.entries(S.disputes).map(([id, d]) => {
    const c = claimById(id);
    const cl = c && clauseById(c.clause_id);
    return `<div class="cya-row"><dt>${esc(cl ? clauseName(cl) : 'Claim')}</dt><dd>${recordQuotes(c?.citations || [])}<span class="tag ai">AI claim</span> “${esc(c ? c.claim : '')}”<br><b>Your reason:</b> ${esc(d.reason)}</dd><dd class="cya-act">${cl ? change('clause', cl.clause_id, 'dispute') : ''}</dd></div>`;
  }).join('') || '<div class="cya-row"><dt>None</dt><dd>You disputed no AI claim.</dd><dd></dd></div>';
  const nReq = required().length;
  return `<section class="signoff" data-testid="check-answers">
    <div class="eyebrow">Sign off</div>
    <h2>Check your answers before signing</h2>
    <p class="lead">Signing locks the record. Change anything below first.</p>
    <dl class="cya">
      <div class="cya-row"><dt>Decision</dt><dd data-testid="cya-decision">${esc(DECISION_LABEL[S.decision])}</dd><dd class="cya-act">${change('change-decision', '', 'decision')}</dd></div>
      <div class="cya-row"><dt>Reason</dt><dd>${esc(S.reason)}</dd><dd class="cya-act">${change('change-decision', '', 'reason')}</dd></div>
    </dl>
    <div class="sec-h"><span>Question outcomes, set by you</span></div><dl class="cya">${outcomes}</dl>
    <div class="sec-h"><span>Disputed claims</span><span>${num(Object.keys(S.disputes).length)}</span></div><dl class="cya">${disputes}</dl>
    <div class="sec-h"><span>Flagged passages</span></div>
    <p class="note">${nReq ? `All ${num(nReq)} opened.` : 'Nothing was flagged.'} Opening a passage is recorded; it does not prove it was read.</p>
    ${S.signErr ? `<div class="helper err" data-testid="sign-error">${icon('alert')}${esc(S.signErr)}</div>` : ''}
    <div class="dlg-actions"><button class="btn-secondary" data-act="change-decision">Back</button>
      <button class="btn-primary" data-act="confirm" data-testid="confirm-sign">${icon('pen')}Sign decision</button></div>
  </section>`;
}
function recordQuotes(citations) {
  return citations.map((q) => `<blockquote class="record-quote">“${esc(q.quote)}”<div class="sub">${esc(q.label || cap(loc(q.passage_id)))}${q.quote_found ? '' : ' · Quote not found'}</div></blockquote>`).join('')
    || '<p class="note">Quote not found: no quote given.</p>';
}

function recordView() {
  const { record, json_url: jsonUrl, html_url: htmlUrl } = S.signed;
  const opened = record.passages_opened.map((p) => `<tr><td>${esc(p.label)}<div class="sub">${p.required ? 'Required' : 'Optional'}</div></td>
      <td class="r mono">${esc(fmtTime(p.opened_at))}</td><td class="r mono">${p.seconds_in_view.toFixed(1)} s</td></tr>`).join('')
    || '<tr><td colspan="3">None</td></tr>';
  const disputes = record.disputes.map((d) => `<li><div class="c">${icon('flag')}${esc(d.clause || '')}</div>${recordQuotes(d.citations || [])}<span class="tag ai">AI claim</span> “${esc(d.claim || '')}”<div><b>Your reason:</b> ${esc(d.reason)}</div></li>`).join('');
  return `<section class="rec" data-testid="record">
    <div class="rec-head"><h2>${icon('lock')}Decision record</h2><span class="tag done">${icon('check')}Signed</span></div>
    <div class="rec-dec">${esc(DECISION_LABEL[record.decision])}</div>
    <dl class="rec-dl"><dt>File</dt><dd>Applicant file ${esc(record.case_id)}</dd>
      <dt>Reason</dt><dd><div class="rec-reason">${esc(record.reason)}</div></dd>
      <dt>Signed</dt><dd>${num(esc(fmtStamp(record.signed_at)))} by ${esc(record.officer)}</dd></dl>
    <h4>Question outcomes, set by you</h4>
    <table class="rec-t"><tbody>${record.clause_outcomes.map((o) => `<tr><td>${esc(o.title)}</td><td class="r">${esc(OUTCOME_LABEL[o.outcome])}</td></tr>`).join('')}</tbody></table>
    <h4>Passages opened before signing · ${num(record.passages_opened.length)}</h4>
    <table class="rec-t"><thead><tr><th>Passage</th><th class="r">Opened</th><th class="r">In view</th></tr></thead><tbody>${opened}</tbody></table>
    <h4>Disputed claims · ${num(record.disputes.length)}</h4>
    ${disputes ? `<ul class="rec-disp">${disputes}</ul>` : '<p class="note">You disputed no AI claim.</p>'}
    <p class="rec-note">${icon('info')}${esc(record.note)}</p>
    <div class="exports"><a class="btn-secondary" href="${esc(htmlUrl)}" target="_blank" rel="noopener" data-testid="export-html">Export HTML</a>
      <a class="btn-secondary" href="${esc(jsonUrl)}" download data-testid="export-json">Export JSON</a></div>
  </section>`;
}

// ---- The file itself. Only code-verified quotes get a quote highlight. ----
function buildAnnotations() {
  let serial = 0;
  const add = (pid, cid, quote, kind, claimIds = []) => {
    const s = src(pid);
    if (!s || !s.exists || s.kind !== 'case') return;
    const existing = S.annotations.find((a) => a.pid === pid && a.cid === cid && a.quote === quote);
    const flagged = kind === 'quote' ? claimIds.some((id) => claimById(id).status !== 'supported')
      : kind === 'pair' || isRequired(pid);
    if (existing) {
      existing.flagged ||= flagged;
      existing.claimIds = [...new Set(existing.claimIds.concat(claimIds))];
      return;
    }
    S.annotations.push({ id: `evidence-${++serial}`, pid, cid, quote, kind, claimIds, flagged });
  };
  S.view.claims.forEach((c) => c.citations.forEach((q) => {
    if (q.quote_found && q.passage_exists) add(q.passage_id, c.clause_id, q.quote, 'quote', [c.claim_id]);
  }));
  S.view.clauses.forEach((cl) => {
    cl.contradictions.forEach((p) => [p.a, p.b].forEach((pid) => {
      // A verified quote already marks this paragraph. Mark it as part of the pair.
      const existing = S.annotations.filter((a) => a.pid === pid && a.cid === cl.clause_id);
      if (existing.length) existing.forEach((a) => { a.flagged = true; });
      else add(pid, cl.clause_id, null, 'pair');
    }));
    cl.possibly_missed.forEach((p) => add(p.passage_id, cl.clause_id, null, 'missed'));
  });
  required().forEach((r) => r.clause_ids.forEach((cid) => {
    if (!S.annotations.some((a) => a.pid === r.passage_id && a.cid === cid)) add(r.passage_id, cid, null, 'flag');
  }));
  // Mandatory passages in gate rank order, then additional claim flags in file order.
  S.annotations.sort((a, b) => {
    const rank = (x) => required().find((r) => r.passage_id === x.pid)?.rank ?? 100;
    return rank(a) - rank(b) || Number(!a.flagged) - Number(!b.flagged)
      || src(a.pid).page - src(b.pid).page || Number(a.pid.split(':').pop()) - Number(b.pid.split(':').pop());
  });
}

const flagHighlights = () => S.annotations.filter((a) => a.flagged);

function pageParagraph(p) {
  const pageHasQuote = S.annotations.some((a) => a.cid === S.sel && src(a.pid).page === p.page && a.quote);
  const annotations = S.annotations.filter((a) => a.pid === p.passage_id && (S.fullFile
    || (a.cid === S.sel && (a.quote || isRequired(a.pid) || !pageHasQuote))));
  const ranges = annotations.flatMap((a) => {
    if (!a.quote) return [];
    const start = p.text.indexOf(a.quote);
    return start < 0 ? [] : [{ start, end: start + a.quote.length, a }];
  });
  // Split overlaps at every boundary, retaining each quote's labels and claim association.
  const bounds = [...new Set([0, p.text.length, ...ranges.flatMap((r) => [r.start, r.end])])].sort((a, b) => a - b);
  let text = '';
  for (let i = 0; i < bounds.length - 1; i += 1) {
    const start = bounds[i], end = bounds[i + 1];
    const here = ranges.filter((r) => r.start <= start && r.end >= end).map((r) => r.a);
    const words = esc(p.text.slice(start, end));
    text += here.length ? `<mark class="${here.some((a) => a.flagged) ? 'flag-mark' : 'clean-mark'}" data-testid="verified-highlight"
      data-evidence="${here.map((a) => a.id).join(' ')}" data-claims="${[...new Set(here.flatMap((a) => a.claimIds))].join(' ')}"
      data-clauses="${[...new Set(here.map((a) => a.cid))].join(' ')}">${words}</mark>` : words;
  }
  const labels = annotations.map((a) => `<button class="evidence-label ${a.flagged ? 'flag-label' : ''} ${S.current?.annotation === a.id ? 'current-label' : ''}" id="${a.id}"
    data-act="annotation" data-arg="${a.id}" data-testid="highlight-label" data-clause="${esc(a.cid)}" data-pid="${esc(a.pid)}"
    data-flag="${a.flagged}" aria-current="${S.current?.annotation === a.id}"${S.signed ? ' disabled' : ''}>${S.fullFile ? icon(a.flagged ? 'flag' : 'check') : ''}${esc(shortName(clauseById(a.cid)))}
    ${a.kind === 'missed' ? ' · Possibly missed' : a.kind === 'pair' ? ' · Two pages disagree' : S.fullFile && a.flagged ? ' · Check' : ''}
    ${S.fullFile && isRequired(a.pid) ? '<span class="label-required">Required</span>' : ''}</button>`).join('');
  const active = S.current?.pid === p.passage_id;
  return `<div class="file-paragraph ${active ? 'active-passage' : ''} ${annotations.some((a) => !a.quote) ? 'scan-passage' : ''}"
    data-testid="${active ? 'source' : 'file-paragraph'}" data-pid="${esc(p.passage_id)}">
    ${labels ? `<div class="evidence-labels">${labels}</div>` : ''}<p>${text}</p>
    ${active ? `<div class="passage-time" data-testid="in-view">${icon('clock')}Opened · in view <span class="mono" id="inView">${Math.floor(secondsInView(p.passage_id))}</span> s</div>` : ''}</div>`;
}

function pageHtml(page) {
  const p = page.passages[0];
  return `<article class="file-page" data-testid="file-page" data-page="${page.page}">
    <header class="file-page-head">Page ${num(page.page)} · ${esc(p?.doc_title || 'Case file')} · ${esc(fmtDate(p?.doc_date))}</header>
    ${page.passages.map(pageParagraph).join('')}</article>`;
}

const pageKey = (s) => `${s.kind === 'case' ? 'case' : s.passage_id.split(':')[0]}:${s.page}`;

// Required pages first, then cited pages, then scan suggestions in their existing rank order.
// A tab can contain several cited paragraphs; each required paragraph still opens separately.
function questionPages(cl) {
  const groups = [];
  const add = (pid, required = false, cited = false, missed = false) => {
    const s = src(pid);
    if (!s?.exists || s.kind !== 'case') return;
    const key = pageKey(s);
    let group = groups.find((g) => g.key === key);
    if (!group) { group = { key, page: s.page, kind: s.kind, date: s.doc_date, title: s.doc_title, pids: [], required, cited, missed }; groups.push(group); }
    if (!group.pids.includes(pid)) group.pids.push(pid);
    group.required ||= required;
    group.cited ||= cited;
    group.missed ||= missed;
  };
  flaggedFor(cl.clause_id).forEach((r) => add(r.passage_id, true, false, r.reasons.includes('possibly_missed')));
  cl.claim_ids.map(claimById).filter(Boolean).forEach((c) => c.citations.forEach((q) => add(q.passage_id, false, true)));
  cl.possibly_missed.forEach((p) => add(p.passage_id, false, false, true));
  return groups;
}

function tabPassage(group) {
  return group.pids.find((pid) => isRequired(pid) && !S.opened[pid])
    || group.pids.find(isRequired) || group.pids[0];
}

function openPageTab(key) {
  const group = questionPages(clauseById(S.sel)).find((g) => g.key === key);
  if (!group) return;
  S.tab = key;
  S.morePages = false;
  const target = tabPassage(group);
  openPassage(target, [], true);
}

function renderReader() {
  const inlineReader = $('reader');
  const reader = S.fullFile ? $('fullReader') : inlineReader;
  if (!reader) return;
  const scroll = $('fileScroll')?.scrollTop || 0;
  const flags = flagHighlights();
  const index = flags.findIndex((a) => a.pid === S.current?.pid && (!S.current.annotation || a.id === S.current.annotation));
  if (S.sel === 'signoff') { reader.innerHTML = ''; return; }
  const groups = questionPages(clauseById(S.sel));
  const optional = groups.filter((g) => !g.required);
  const visible = groups.filter((g) => g.required).concat(optional.slice(0, 2));
  const more = optional.slice(2);
  const active = groups.find((g) => g.key === S.tab) || groups[0];
  if (active) S.tab = active.key;
  const fullButton = `<button class="act full-link" data-act="full-open" data-testid="open-full-file">Open in full file (${S.pages.length} pages) ↗</button>`;
  const tabs = `<div class="viewer-top"><div class="page-tabs" role="tablist" aria-label="Pages for this question">${visible.map((g) => {
    const opened = g.pids.some((pid) => S.opened[pid]);
    const solelyMissed = g.missed && !g.pids.some((pid) => S.annotations.some((a) => a.pid === pid && a.cid === S.sel && a.quote)) && !clauseById(S.sel).contradictions.some((p) => g.pids.includes(p.a) || g.pids.includes(p.b));
    return `<button role="tab" class="page-tab" aria-selected="${g.key === active?.key}" aria-controls="fileScroll" data-act="page-tab" data-arg="${esc(g.key)}" data-testid="page-tab" data-page="${g.page}" data-kind="${g.kind}"${S.signed ? ' disabled' : ''}>Page ${g.page}${opened ? ' ✓ opened' : ''}<span class="tab-note">${g.date ? esc(fmtDate(g.date).replace(/ \d{4}$/, '')) : 'Date not recorded'}</span>${solelyMissed ? '<span class="tab-note">Possibly missed</span>' : ''}</button>`;
  }).join('')}${more.length ? `<button class="page-tab more-pages" data-act="more-pages" data-testid="more-pages" aria-expanded="${S.morePages}" aria-controls="morePages"${S.signed ? ' disabled' : ''}>More pages (${more.length})${more.includes(active) ? `<span class="tab-note">Page ${active.page} selected</span>` : ''}</button>` : ''}</div>
    ${more.length ? `<div class="more-page-list" id="morePages"${S.morePages ? '' : ' hidden'}>${[
      ["Cited by the AI's claims", more.filter((g) => g.cited)],
      ['Possibly missed', more.filter((g) => !g.cited)],
    ].filter(([, pages]) => pages.length).map(([label, pages]) => `<section><h3>${esc(label)}</h3><ul>${pages.map((g) => `<li><button class="act" data-act="page-tab" data-arg="${esc(g.key)}" data-testid="more-page" aria-current="${g.key === active?.key ? 'page' : 'false'}"${S.signed ? ' disabled' : ''}>Page ${g.page} · ${esc(fmtDate(g.date))} · ${esc(g.title)}${g.pids.some((pid) => S.opened[pid]) ? ' ✓ opened' : ''}</button></li>`).join('')}</ul></section>`).join('')}</div>` : ''}${fullButton}</div>`;
  let content;
  if (S.fullFile) content = S.pages.map(pageHtml).join('');
  else if (!active) content = '<p class="empty-file">Evidence not found. No page is cited for this question. Missing evidence does not mean “not met”.</p>';
  else content = pageHtml(S.pages.find((p) => p.page === active.page));
  if (S.fullFile && inlineReader) inlineReader.innerHTML = '<p class="empty-file">The full applicant file is open.</p>';
  reader.innerHTML = `${S.fullFile ? `<div class="reader-head"><span id="fileContext">Exact quotes marked by question</span></div>
    <div class="file-controls"><button class="act" data-act="previous-flag" data-testid="previous-flag"${S.signed || !flags.length ? ' disabled' : ''}>Previous flag</button>
      <span class="flag-position" data-testid="flag-position">${index < 0 ? `${flags.length} highlights to check` : `Flag ${index + 1} of ${flags.length}`}</span>
      <button class="btn-secondary" data-act="next-flag" data-testid="next-flag"${S.signed || !flags.length ? ' disabled' : ''}>Next flag${icon('arrow')}</button></div>
    <div class="page-controls"><button class="act" data-act="previous-page" aria-label="Previous page"${S.readerPage <= 1 ? ' disabled' : ''}>Previous page</button>
      <label>Page <select id="pageJump" aria-label="Go to page">${S.pages.map((p) => `<option value="${p.page}"${p.page === S.readerPage ? ' selected' : ''}>${p.page}</option>`).join('')}</select> of ${num(S.pages.length)}</label>
      <button class="act" data-act="next-page" aria-label="Next page"${S.readerPage >= S.pages.length ? ' disabled' : ''}>Next page</button></div>` : tabs}
    <div class="file-scroll" id="fileScroll" tabindex="0" ${S.fullFile ? '' : 'role="tabpanel"'} aria-label="Case pages">${content}</div>`;
  if (S.fullFile) $('fileScroll').scrollTop = scroll;
  $('fileScroll').addEventListener('scroll', updateReaderVisibility);
}

function jumpToPassage(pid, claimIds = [], annotationId = null) {
  const label = annotationId && $(annotationId);
  const target = label ? label.closest('.file-paragraph') : document.querySelector(`#fileScroll .file-paragraph[data-pid="${CSS.escape(pid)}"]`);
  if (!target) return;
  const scroller = $('fileScroll');
  const paragraph = target.getBoundingClientRect();
  const viewport = scroller.getBoundingClientRect();
  if (paragraph.top < viewport.top || paragraph.bottom > viewport.bottom) {
    scroller.scrollTop += paragraph.top - viewport.top - 16;
  }
  S.readerPage = src(pid).page;
  if ($('pageJump')) $('pageJump').value = S.readerPage;
  watchPassage();
}

function openAnnotation(id) {
  const a = S.annotations.find((x) => x.id === id);
  if (!a || S.signed) return;
  S.sel = a.cid;
  S.claimOpen = false;
  if (!questionFlag(clauseById(a.cid))) S.cleanOpen = true;
  openPassage(a.pid, a.claimIds);
  S.current.annotation = a.id;
  render();
  jumpToPassage(a.pid, a.claimIds, a.id);
}

function moveFlag(direction) {
  const flags = flagHighlights();
  const index = flags.findIndex((a) => a.pid === S.current?.pid && (!S.current.annotation || a.id === S.current.annotation));
  const next = index < 0 ? (direction > 0 ? 0 : flags.length - 1) : (index + direction + flags.length) % flags.length;
  if (flags[next]) openAnnotation(flags[next].id);
}

function goToPage(n) {
  const page = S.pages.find((p) => p.page === n);
  if (!page) return;
  // Merely browsing a page never checks off any of its required passages.
  closePassage();
  S.readerPage = n;
  render();
  const target = document.querySelector(`#fileScroll [data-page="${n}"]`);
  $('fileScroll').scrollTop += target.getBoundingClientRect().top - $('fileScroll').getBoundingClientRect().top;
}

function openFullFile() {
  pause();
  S.fullFile = true;
  render();
  $('fullFile').showModal();
  if (S.current && src(S.current.pid)?.kind === 'case') jumpToPassage(S.current.pid, S.current.claimIds);
  else goToPage(S.readerPage);
}

function closeFullFile() {
  closePassage();
  S.fullFile = false;
  $('fullFile').close();
  $('fullReader').innerHTML = '';
  render();
}

function comparePages(a, b) {
  closePassage();
  render();
  const pages = [...new Set([src(a).page, src(b).page])].map((n) => S.pages.find((p) => p.page === n));
  $('comparison').innerHTML = `<div class="dlg"><div class="dlg-head"><h2>Pages ${src(a).page} and ${src(b).page} disagree</h2>
    <button class="icon-btn" data-act="compare-close" aria-label="Close comparison">${icon('x')}</button></div>
    <p class="note">Two records disagree. A later record may supersede an earlier one. Select a highlighted passage to open and record it.</p>
    <div class="comparison-pages">${pages.map(pageHtml).join('')}</div></div>`;
  // No duplicate HTML ids; labels in the dialog still refer to the same annotations.
  $('comparison').querySelectorAll('[id]').forEach((e) => e.removeAttribute('id'));
  $('comparison').showModal();
}

function highlight(text, quotes) {
  const ranges = quotes.map((q) => [text.indexOf(q), q.length]).filter(([i]) => i >= 0).sort((a, b) => a[0] - b[0]);
  let out = '', pos = 0;
  for (const [start, length] of ranges) {
    if (start < pos) continue;
    out += esc(text.slice(pos, start)) + `<mark>${esc(text.slice(start, start + length))}</mark>`;
    pos = start + length;
  }
  return out + esc(text.slice(pos));
}

function renderPane() {
  const pid = S.current?.pid;
  const s = pid && src(pid);
  if (!s || s.kind !== 'policy' || S.policyInline) { $('pane').innerHTML = ''; return; }
  const cl = S.view.clauses.find((c) => c.policy_passage_id === pid);
  const cites = S.view.claims.flatMap((c) => c.citations).filter((q) => q.passage_id === pid);
  const text = S.policyText[pid];
  const quotes = cites.filter((q) => q.quote_found).map((q) => q.quote).concat(cl?.policy_sentence || []);
  $('pane').innerHTML = `<div class="dlg"><div class="dlg-head"><h2>${esc(s.doc_title)}</h2>
    <button class="icon-btn" data-act="close-pane" aria-label="Close policy passage">${icon('x')}</button></div>
    <div class="sub">${esc(cap(loc(pid)))}</div><div class="v-page" data-testid="source" data-pid="${esc(pid)}">
    ${text ? highlight(text, quotes) : text === false ? 'The pinned policy PDF could not be read on this machine.' : 'Reading the pinned policy PDF…'}</div>
    <p class="note">Real NT policy · read from the pinned PDF on demand.</p></div>`;
}

let passageObserver = null;
function passageVisible() {
  if (!S.current || document.hidden || S.signed || $('about').open || $('comparison').open) return false;
  const isPolicy = src(S.current.pid)?.kind === 'policy' && !S.policyInline;
  if ($('policy').open !== isPolicy) return false;
  const el = document.querySelector('[data-testid="source"]');
  if (!el) return false;
  const r = el.getBoundingClientRect();
  const container = (isPolicy ? $('policy') : $('fileScroll')).getBoundingClientRect();
  return r.bottom > Math.max(container.top, S.fullFile || isPolicy ? 0 : $('casebar').getBoundingClientRect().bottom)
    && r.top < Math.min(container.bottom, window.innerHeight) && r.width > 0;
}
function updateReaderVisibility() {
  if (passageVisible()) resume(); else pause();
  const scroller = $('fileScroll');
  if (!scroller) return;
  const top = scroller.getBoundingClientRect().top;
  const page = [...scroller.querySelectorAll('.file-page')].find((p) => p.getBoundingClientRect().bottom > top + 24);
  if (page) {
    S.readerPage = Number(page.dataset.page);
    if ($('pageJump')) $('pageJump').value = S.readerPage;
    const p = S.pages.find((x) => x.page === S.readerPage)?.passages[0];
    if ($('fileContext')) $('fileContext').textContent = `${p?.doc_title || 'Case file'} · ${fmtDate(p?.doc_date)}`;
  }
}
function watchPassage() {
  passageObserver?.disconnect();
  const el = document.querySelector('[data-testid="source"]');
  if (el) {
    passageObserver = new IntersectionObserver(updateReaderVisibility, { threshold: [0, 0.1, 1] });
    passageObserver.observe(el);
  }
  updateReaderVisibility();
}
window.addEventListener('scroll', updateReaderVisibility, { passive: true });

// ---- About these checks: the only place model ids appear ----
function renderAbout() {
  const v = S.view;
  const m = (x) => `${esc(cap(x.name))} <span class="mono">${esc(x.model || 'no model id')}</span>`;
  const key = (kind, cls, label, text) => `<li>${pill(kind, cls, label)}<span>${text}</span></li>`;
  $('about').innerHTML = `<div class="dlg">
    <div class="dlg-head"><h2 id="aboutTitle">About these checks</h2><button class="icon-btn" data-act="about-close" aria-label="Close">${icon('x')}</button></div>
    <div class="sec-h"><span>Models</span></div>
    <dl class="about-dl"><dt>Writer</dt><dd>${m(v.models.writer)}. Drafted each claim with the exact words it relied on.</dd>
      <dt>Checker</dt><dd>${m(v.models.checker)}. Re-checked each claim, compared passages that may disagree, and scanned the file for relevant passages no claim uses.</dd></dl>

    <div class="sec-h"><span>What each status means</span></div>
    <ul class="key">
      ${key('check', 'ok', 'Supported', 'Every quote is word for word in its passage, its figures and dates appear in a quote, and the second checker agrees.')}
      ${key('arrows', 'warn', 'Contradicted by another passage', 'The claim rests on a passage that another passage disagrees with. The quote may be accurate; the two records conflict.')}
      ${key('neq', 'warn', 'Checker disagrees', 'The second checker could not confirm that the quoted passage says what the claim says.')}
      ${key('searchx', 'bad', 'Quote not found', 'A quote is not in its passage, a figure or date is in no quote, or the claim gives no quote.')}
      ${key('help', 'warn', 'Possibly missed', 'The scan found a passage relevant to the question that no claim uses.')}
      ${key('slash', 'neutral', 'No evidence in file', 'The AI looked for something and found nothing. That is not “not met”.')}
    </ul>
    <div class="sec-h"><span>Flagged passages</span></div>
    <p class="note">At most ${num(v.cap)} passages are flagged as required, most decisive first; ${num(v.suggested_reading.length)} more are suggested. No score is shown per claim, so a number never stands in for reading the passage.</p>
    <div class="sec-h"><span>Policies checked</span></div>
    <ul class="pol">${v.policies.map((p) => `<li>${esc(p.title)}, version ${num(esc(p.version))}, approved ${esc(fmtDate(p.approved))}</li>`).join('')}</ul>
  </div>`;
}

// ---- Render, keeping keyboard focus where it was ----
function render() {
  const a = document.activeElement;
  const key = a && a.dataset && a.dataset.act ? [a.dataset.act, a.dataset.arg || '', a.dataset.val || ''] : null;
  renderBar();
  renderJob();
  renderIntro();
  renderRail();
  $('work').classList.toggle('signing', S.sel === 'signoff');
  $('detail').innerHTML = S.sel === 'signoff' ? signoffView() : clauseView(clauseById(S.sel) || railClauses()[0]);
  renderReader();
  renderPane();
  syncBarHeight();
  watchPassage();
  if (key) {
    const sel = `[data-act="${key[0]}"]${key[1] ? `[data-arg="${CSS.escape(key[1])}"]` : ''}${key[2] ? `[data-val="${key[2]}"]` : ''}`;
    const el = document.querySelector(sel);
    if (el && el !== document.activeElement) el.focus({ preventScroll: true });
  }
}

function syncBarHeight() {
  document.documentElement.style.setProperty('--bar-h', `${$('casebar').offsetHeight}px`);
}
window.addEventListener('resize', syncBarHeight);

function scrollToWork() {
  const top = $('work').getBoundingClientRect().top + window.scrollY - $('casebar').offsetHeight - 12;
  if (window.scrollY > top) window.scrollTo({ top, behavior: 'auto' });
}
function selectClause(id) {
  if (S.fullFile) closeFullFile();
  closePassage();
  S.sel = id;
  S.tab = null;
  S.morePages = false;
  S.formErr = '';
  S.disputing = null;
  S.claimOpen = false;
  if (!questionFlag(clauseById(id))) S.cleanOpen = true;
  render();
  const first = questionPages(clauseById(id))[0];
  if (first && !S.signed) openPageTab(first.key);
  scrollToWork();
}
function selectSignoff() {
  if (S.fullFile) closeFullFile();
  closePassage();
  S.sel = 'signoff';
  if ($('policy').open) $('policy').close();
  if ($('comparison').open) $('comparison').close();
  S.disputing = null;
  S.signErr = '';
  render();
  scrollToWork();
}
function doNext() {
  const n = nextAction();
  if (n.kind === 'passage') {
    if (S.sel !== n.clause.clause_id) selectClause(n.clause.clause_id);
    openPassage(n.pid, []);
  } else if (n.kind === 'outcome') {
    if (S.sel !== n.clause.clause_id) selectClause(n.clause.clause_id);
    const chip = document.querySelector(`[data-act="outcome"][data-arg="${CSS.escape(n.clause.clause_id)}"]`);
    if (chip) chip.focus();
  } else {
    selectSignoff();
  }
}

async function confirmSign() {
  pause();
  const payload = {
    officer: 'Delegated officer',
    decision: S.decision,
    reason: S.reason.trim(),
    clause_outcomes: S.outcomes,
    passages_opened: Object.entries(S.opened).map(([pid, o]) => ({ passage_id: pid, opened_at: o.opened_at, seconds_in_view: Math.round(o.seconds * 10) / 10 })),
    disputes: Object.entries(S.disputes).map(([claimId, x]) => ({ claim_id: claimId, reason: x.reason, at: x.at })),
  };
  let res;
  try {
    res = await fetch('/api/records', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  } catch {
    S.signErr = 'The record could not be saved. Check that the Readmark server is running and sign again.';
    render();
    return;
  }
  const body = await res.json();
  if (!res.ok) {
    S.signErr = `Not signed: ${(body.problems || [body.detail || 'unknown error']).join(' ')}`;
    render();
    return;
  }
  S.signed = body;
  S.current = null;
  S.sel = 'signoff';
  render();
  scrollToWork();
}

// ---- Events (delegated, so re-rendering never loses a handler) ----
// Once signed, outcomes, disputes and openings are on the record; only looking around remains.
const AFTER_SIGN = new Set(['clause', 'signoff', 'sign', 'next', 'previous-page', 'next-page', 'full-open', 'full-close', 'intro-open', 'intro-close', 'about-open', 'about-close']);
document.addEventListener('click', (e) => {
  const t = e.target.closest('[data-act]');
  if (!t || !S.view) return;
  const act = t.dataset.act;
  const arg = t.dataset.arg;
  if (S.signed && !AFTER_SIGN.has(act)) return;
  switch (act) {
    case 'clause': selectClause(arg); break;
    case 'signoff': case 'sign': selectSignoff(); break;
    case 'next': doNext(); break;
    case 'open': openPassage(arg, t.dataset.claims ? t.dataset.claims.split(',') : []); break;
    case 'page-tab': openPageTab(arg); break;
    case 'more-pages': {
      const scroll = $('fileScroll').scrollTop;
      S.morePages = !S.morePages;
      renderReader();
      $('fileScroll').scrollTop = scroll;
      document.querySelector('[data-testid="more-pages"]').focus();
      watchPassage();
      break;
    }
    case 'full-open': openFullFile(); break;
    case 'full-close': closeFullFile(); break;
    case 'close-pane': closePassage(); $('policy').close(); render(); break;
    case 'annotation': openAnnotation(arg); break;
    case 'next-flag': moveFlag(1); break;
    case 'previous-flag': moveFlag(-1); break;
    case 'previous-page': goToPage(S.readerPage - 1); break;
    case 'next-page': goToPage(S.readerPage + 1); break;
    case 'compare': comparePages(arg, t.dataset.other); break;
    case 'compare-close': $('comparison').close(); break;
    case 'claims': S.claimOpen = true; render(); break;
    case 'outcome':
      S.outcomes[arg] = t.dataset.val;
      S.formErr = '';
      render();
      break;
    case 'save-next': saveNext(arg); break;
    case 'dispute': {
      S.disputing = arg;
      S.disputeErr = false;
      render();
      const box = $(`dr-${arg}`);
      if (box) box.focus();
      break;
    }
    case 'dispute-cancel': S.disputing = null; S.disputeErr = false; render(); break;
    case 'dispute-save': {
      const reason = ($(`dr-${arg}`) || {}).value || '';
      if (!reason.trim()) { S.disputeErr = true; render(); $(`dr-${arg}`).focus(); return; }
      S.disputes[arg] = { reason: reason.trim(), at: new Date().toISOString() };
      S.disputing = null;
      S.disputeErr = false;
      render();
      break;
    }
    case 'dispute-withdraw': delete S.disputes[arg]; render(); break;
    case 'continue':
      if (!S.decision || !S.reason.trim()) {
        S.formErr = 'Choose a decision and write a reason. Both go on the record.';
        render();
        return;
      }
      S.formErr = '';
      S.step = 'check';
      render();
      scrollToWork();
      break;
    case 'change-decision': S.step = 'decide'; S.signErr = ''; render(); break;
    case 'confirm': confirmSign(); break;
    case 'intro-close': S.intro = false; store(INTRO_KEY, '1'); render(); break;
    case 'intro-open':
      S.intro = true;
      store(INTRO_KEY, null);
      render();
      window.scrollTo({ top: Math.max(0, $('intro').getBoundingClientRect().top + window.scrollY - $('casebar').offsetHeight - 12) });
      break;
    case 'about-open': pause(); $('about').showModal(); break;
    case 'about-close': $('about').close(); break;
    default: break;
  }
});
document.addEventListener('input', (e) => { if (e.target.id === 'reason') S.reason = e.target.value; });
document.addEventListener('change', (e) => {
  if (e.target.matches('[data-outcome]') && !S.signed) {
    S.outcomes[e.target.dataset.arg] = e.target.value;
    S.formErr = '';
    render();
  }
  if (e.target.name === 'decision') S.decision = e.target.value;
  if (e.target.id === 'pageJump') goToPage(Number(e.target.value));
});
$('about').addEventListener('close', resume);
$('policy').addEventListener('close', () => { if (!$('policy').open && src(S.current?.pid)?.kind === 'policy') closePassage(); });
$('comparison').addEventListener('close', resume);
$('fullFile').addEventListener('cancel', (e) => { e.preventDefault(); closeFullFile(); });
document.addEventListener('toggle', (e) => {
  if (e.target.matches('[data-testid=clean-questions]')) S.cleanOpen = e.target.open;
  if (e.target.matches('[data-testid=claim-details]')) S.claimOpen = e.target.open;
}, true);

setInterval(() => {
  const el = $('inView');
  if (el && S.current) el.textContent = Math.floor(secondsInView(S.current.pid));
}, 1000);

// Loading state: skeleton rows shaped like the clause list and the clause.
$('rail').innerHTML = Array.from({ length: 6 }, () => '<div class="skel rrow-skel"></div>').join('');
$('detail').innerHTML = '<div class="skel skel-head"></div><div class="skel skel-body"></div>';

// Context has its own request: an unavailable context file cannot block case review.
fetch('/api/context').then((r) => {
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}).then((context) => {
  $('waitContext').innerHTML = `${esc(context.label)} · <a href="${esc(context.source_url)}" target="_blank" rel="noopener">NT open data, Dec 2020</a> · historical, not priority-specific`;
}).catch(() => { $('waitContext').textContent = 'Historical housing context unavailable.'; });

Promise.all(['/api/view', '/api/case-pages'].map((url) => fetch(url)
  .then(async (r) => { if (!r.ok) throw new Error((await r.json()).detail || `HTTP ${r.status}`); return r.json(); })))
  .then(([v, file]) => {
    S.view = v;
    S.pages = file.pages;
    buildAnnotations();
    S.sel = railClauses().length ? railClauses()[0].clause_id : 'signoff';
    renderAbout();
    render();
    const first = S.annotations.find((a) => a.cid === S.sel);
    if (first) jumpToPassage(first.pid, first.claimIds, first.id);
  })
  .catch((err) => {
    $('rail').innerHTML = '';
    $('job').textContent = 'The case could not be loaded.';
    $('detail').innerHTML = `<div class="banner" data-testid="load-error">${icon('alert')}<span>The case view could not be loaded (${esc(err.message)}). Run <span class="mono">python -m readmark run --case &lt;case&gt; --replay</span>, then reload this page.</span></div>`;
  });
