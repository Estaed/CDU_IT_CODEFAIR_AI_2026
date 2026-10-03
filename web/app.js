// Readmark review screen, layout B (Task-07): the clause list on the left, the selected clause and
// its source passage on the right, and a case bar with both counters and the one next action.
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
const WORST_FIRST = ['contradicted', 'quote_not_found', 'checker_disagrees', 'supported'];
const COVERAGE = {
  possibly_missed: ['Possibly missed', 'help', 'warn'],
  no_evidence_in_file: ['No evidence in file', 'slash', 'neutral'],
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
  tab: 'review',     // review | audit
  sel: null,         // a clause_id, or 'signoff'
  opened: {},        // passage_id -> {opened_at, seconds}
  current: null,     // {pid, claimIds}: the one passage in view
  since: null,       // performance.now() when the open passage became visible
  outcomes: {},      // clause_id -> met | not_met | cannot_decide (officer only)
  disputes: {},      // claim_id -> {reason, at}
  disputing: null,
  disputeErr: false,
  pmMore: {},        // clause_id -> the long "possibly missed" list is expanded
  step: 'decide',    // sign-off: decide | check
  decision: null,
  reason: '',
  formErr: '',
  signErr: '',
  signed: null,
  justSet: null,
  policyText: {},    // passage_id -> text, or false when the server could not read it
  intro: !stored(INTRO_KEY),
};

// ---- Time in view: only the open passage accrues, and only while it can be seen ----
function pause() {
  if (S.current && S.since !== null) S.opened[S.current.pid].seconds += (performance.now() - S.since) / 1000;
  S.since = null;
}
function resume() {
  if (S.current && !document.hidden && !S.signed && !$('about').open) S.since = performance.now();
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

function openPassage(pid, claimIds = []) {
  if (S.signed) return;
  pause();
  if (!S.opened[pid]) S.opened[pid] = { opened_at: new Date().toISOString(), seconds: 0 };
  S.current = { pid, claimIds };
  resume();
  const s = src(pid);
  if (s && s.kind === 'policy' && !(pid in S.policyText)) {
    fetch(`/api/passages/${encodeURIComponent(pid)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { S.policyText[pid] = d ? d.text : false; renderPane(); })
      .catch(() => { S.policyText[pid] = false; renderPane(); });
  }
  render();
  $('pane').scrollTop = 0;
}

// ---- The view, read in plain words ----
const src = (pid) => S.view.sources[pid];
const allClaims = () => S.view.claims.concat((S.view.audit && S.view.audit.claims) || []);
const claimById = (id) => allClaims().find((c) => c.claim_id === id);
const clauseById = (id) => S.view.clauses.find((c) => c.clause_id === id);
const decisive = () => S.view.clauses.filter((c) => c.clause_id !== 'other');
const required = () => S.view.required_reading;
const isRequired = (pid) => required().some((r) => r.passage_id === pid);
const readingItem = (pid) => required().concat(S.view.suggested_reading).find((r) => r.passage_id === pid);
const flaggedFor = (cid) => required().filter((r) => r.clause_ids.includes(cid));
// "Other facts" joins the list only when it holds something; it never takes an outcome.
const railClauses = () => S.view.clauses.filter((c) => c.clause_id !== 'other'
  || c.claim_ids.length || c.missing.length || flaggedFor('other').length);

function fmtDate(d) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d || '');
  return m ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}` : String(d || '');
}
const fmtTime = (iso) => new Date(iso).toLocaleTimeString('en-AU', { hour12: false });
const fmtStamp = (iso) => `${new Date(iso).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })}, ${fmtTime(iso)}`;
const clip = (text, n) => (text.length > n ? `${text.slice(0, n).replace(/\s+\S*$/, '')}…` : text);

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
function readingWhy(item, clauseId = null) {
  const parts = item.reasons.map((r) => {
    if (r === 'contradicted') {
      if (!item.claim_ids.length) return 'it disagrees with a passage a claim rests on';
      return pairsWith(item.passage_id).length ? 'a claim rests on it and another passage disagrees with it' : 'a claim that rests on it is contradicted by another passage';
    }
    if (r === 'quote_not_found') return 'a claim that cites it failed the quote check';
    if (r === 'checker_disagrees') return 'the second checker could not confirm the claim it backs';
    if (clauseId) return 'the scan found it relevant to this clause, and no claim uses it';
    const names = item.clause_ids.map((id) => clauseById(id)).filter(Boolean).map((c) => c.title);
    return `the scan found it relevant to ${names.join(', ')}, and no claim uses it`;
  });
  return `${cap(esc(parts.join('; ')))}.`;
}

// ---- Pieces shared by several views ----
function pill(kind, cls, label, testid = '') {
  return `<span class="pill ${cls}"${testid ? ` data-testid="${testid}"` : ''}>${icon(kind)}${esc(label)}</span>`;
}
function statusPill(status, testid = '') {
  const [label, ic, cls] = CLAIM_STATUS[status];
  return pill(ic, cls, label, testid);
}
function passageRow(pid, { why = '', task = false, excerpt = false, testid = 'passage-item' } = {}) {
  const o = S.opened[pid];
  const cur = S.current && S.current.pid === pid;
  const s = src(pid);
  let state = o ? 'Opened' : task ? 'Must open' : 'Open';
  if (cur) state = 'In view';
  return `<li><button class="prow ${o ? 'opened' : ''} ${cur ? 'is-cur' : ''} ${task ? 'task' : ''}" data-act="open" data-arg="${esc(pid)}" data-testid="${testid}" data-pid="${esc(pid)}"${S.signed ? ' disabled' : ''}>
    <span class="pst">${icon(o ? 'check' : task ? 'ring' : 'file')}</span>
    <span class="pmain"><span class="ploc">${esc(cap(loc(pid)))}</span> <span class="pdoc">${esc(docLine(pid))}</span>
      ${excerpt && s && s.text ? `<span class="pex">“${esc(clip(s.text, 150))}”</span>` : ''}
      ${why ? `<span class="pwhy">${why}</span>` : ''}</span>
    <span class="pstate"><span class="ps">${state}${!o && !cur ? icon('arrow') : ''}</span>${o ? `<span class="when mono">${fmtTime(o.opened_at)}</span>` : ''}</span></button></li>`;
}
function quoteHtml(claim, c, testid = 'quote') {
  const cur = S.current && S.current.pid === c.passage_id;
  return `<button class="quote ${c.quote_found ? '' : 'quote-bad'} ${cur ? 'is-cur' : ''}" data-act="open" data-arg="${esc(c.passage_id)}" data-claims="${esc(claim.claim_id)}" data-testid="${testid}" data-pid="${esc(c.passage_id)}"${S.signed ? ' disabled' : ''}>
    <span class="q">“${esc(c.quote)}”</span>
    <span class="cite"><span class="loc">${esc(cap(loc(c.passage_id)))}</span><span>${esc(docLine(c.passage_id))}</span>${kindTag(c.passage_id)}
      ${c.quote_found ? '' : `<span class="qflag">${icon('x')}Not word for word in this passage</span>`}
      ${S.opened[c.passage_id] ? `<span class="tag done">${icon('check')}Opened</span>` : ''}</span></button>`;
}
function segs(flags) {
  return `<span class="segs" aria-hidden="true">${flags.map((on) => `<i class="${on ? 'on' : ''}"></i>`).join('')}</span>`;
}

// ---- Case bar: the file, both counters, the one next action ----
function renderBar() {
  const v = S.view;
  $('caseId').textContent = v.case.case_id;
  const req = required();
  const dec = decisive();
  const nOpen = req.filter((r) => S.opened[r.passage_id]).length;
  const nSet = dec.filter((c) => S.outcomes[c.clause_id]).length;
  $('counters').innerHTML = `
    <div class="counter" data-testid="outcome-counter"><span class="ct">Outcomes <b class="mono" id="outcomeCount">${nSet}</b> of ${num(dec.length)}</span>${segs(dec.map((c) => !!S.outcomes[c.clause_id]))}</div>
    <div class="counter" data-testid="passage-counter"><span class="ct">Flagged passages <b class="mono" id="passageCount">${nOpen}</b> of ${num(req.length)} opened</span>${req.length ? segs(req.map((r) => !!S.opened[r.passage_id])) : ''}</div>`;
  const n = nextAction();
  let label;
  let hint;
  if (n.kind === 'passage') { label = `Open ${loc(n.pid)}`; hint = `Next step in ${n.clause.clause_id === 'other' ? 'Other facts' : n.clause.title}`; }
  else if (n.kind === 'outcome') { label = 'Set your outcome'; hint = `Next step in ${n.clause.title}`; }
  else if (n.kind === 'sign') { label = 'Sign decision'; hint = 'Next step · everything is ready'; }
  else { label = 'View the record'; hint = 'Decision signed'; }
  const target = n.kind === 'passage' ? `passage:${n.pid}` : n.kind === 'outcome' ? `outcome:${n.clause.clause_id}` : n.kind;
  $('next').innerHTML = `<div class="next-step"><span class="eyebrow" data-testid="next-hint">${esc(hint)}</span>
      <button class="btn-primary" data-act="next" data-testid="next-action" data-next="${esc(target)}">${n.kind === 'sign' ? icon('pen') : ''}${esc(label)}${n.kind === 'sign' ? '' : icon('arrow')}</button></div>
    ${n.kind === 'sign' || n.kind === 'record' ? '' : `<button class="btn-secondary" data-act="sign" data-testid="sign-btn">${icon('pen')}Sign decision</button>`}`;
}

function renderJob() {
  const v = S.view;
  $('job').innerHTML = `<b>Your job:</b> decide this application. Open each flagged passage, set all ${num(decisive().length)} clause outcomes, then sign.`;
  $('themeBtn').textContent = document.documentElement.dataset.theme === 'light' ? 'Dark mode' : 'Light mode';
  document.title = `Readmark · Applicant file ${v.case.case_id}`;
}

// ---- First-run panel, recallable with "How this works" ----
function introExamples() {
  const claims = S.view.claims;
  const firstReq = required().find((r) => r.claim_ids.length);
  const flagged = (firstReq && claimById(firstReq.claim_ids[0])) || claims.find((c) => c.status !== 'supported');
  const supported = (flagged && claims.find((c) => c.status === 'supported' && c.clause_id === flagged.clause_id && c.citations.length))
    || claims.find((c) => c.status === 'supported' && c.citations.length);
  return [supported, flagged].filter(Boolean).map((c) => {
    const q = c.citations[0];
    return `<div class="ex">
      ${q ? `<blockquote class="q">“${esc(q.quote)}”</blockquote><div class="cite"><span class="loc">${esc(cap(loc(q.passage_id)))}</span><span>${esc(docLine(q.passage_id))}</span></div>` : ''}
      <div class="claimline"><span class="tag ai">AI claim</span><span>${esc(c.claim)}</span></div>
      <div class="statusline"><span class="list-label">Claim check</span>${statusPill(c.status)}</div>
      <p class="why">${claimReason(c)}</p></div>`;
  }).join('');
}
function renderIntro() {
  const box = $('intro');
  if (!S.intro || !S.view) { box.innerHTML = ''; box.hidden = true; return; }
  const v = S.view;
  box.hidden = false;
  box.innerHTML = `<div class="intro" data-testid="intro">
    <div class="intro-head"><div><div class="eyebrow">How this works</div>
      <h2>The AI drafts, the checks flag, <span class="accent">you</span> decide.</h2></div>
      <button class="btn-secondary" data-act="intro-close" data-testid="intro-dismiss">Got it</button></div>
    <ol class="intro-steps">
      <li><b>What the AI did</b><span>Read the ${num(v.case.pages)}-page file and ${num(v.policies.length)} NT policies, and wrote short claims per clause, each quoting the words it relied on.</span></li>
      <li><b>What the checks did</b><span>Code found every quote in its passage. A second model re-checked each claim, compared passages that may disagree and looked for passages no claim uses. At most ${num(v.cap)} are flagged for you.</span></li>
      <li><b>What you decide</b><span>An outcome for each of the ${num(decisive().length)} clauses, then the decision. The AI never sets either, and “no evidence in file” never means “not met”.</span></li>
    </ol>
    <div class="eyebrow ex-h">Two claims from this file: one the checks passed, one they flagged</div>
    <div class="ex-grid">${introExamples()}</div>
    <p class="intro-foot">${icon('arrow')}Your next step is always the button at the top right, under “Next step”. Work through the clauses in any order.</p>
  </div>`;
}

function renderTabs() {
  const a = S.view.audit;
  const flagged = a ? a.sentences.filter((s) => !['supported', 'none'].includes(sentenceStatus(s))).length : 0;
  $('tabs').innerHTML = `<button role="tab" aria-selected="${S.tab === 'review'}" data-act="tab" data-arg="review" data-testid="tab-review">Review by clause <span class="n">${num(decisive().length)} clauses</span></button>
    <button role="tab" aria-selected="${S.tab === 'audit'}" data-act="tab" data-arg="audit" data-testid="audit-tab">Summary under audit <span class="n ${flagged ? 'warn' : ''}">${a ? `${flagged ? icon('alert') : ''}${num(flagged)} of ${num(a.sentences.length)} sentences flagged` : 'none audited'}</span></button>`;
}

// ---- Left: one row per clause, then sign-off ----
function renderRail() {
  const rows = railClauses().map((cl) => {
    const st = clauseState(cl);
    const id = cl.clause_id;
    const sel = S.tab === 'review' && S.sel === id;
    let outcome = '<span class="rs">No outcome needed</span>';
    if (st.needsOutcome) {
      outcome = st.outcome
        ? `<span class="rs done">${icon('check')}Outcome: ${esc(OUTCOME_LABEL[st.outcome])}</span>`
        : `<span class="rs todo">${icon('ring')}Outcome not set</span>`;
    }
    let flagged = '<span class="rs">Nothing flagged</span>';
    if (st.flagged.length) {
      flagged = st.opened === st.flagged.length
        ? `<span class="rs done">${icon('check')}Flagged all opened</span>`
        : `<span class="rs todo">${icon('ring')}Flagged ${num(st.opened)} of ${num(st.flagged.length)} opened</span>`;
    }
    return `<button class="rrow ${sel ? 'is-sel' : ''} ${S.justSet === id ? 'just' : ''}" data-act="clause" data-arg="${esc(id)}" data-testid="clause-row" data-clause="${esc(id)}" aria-current="${sel ? 'true' : 'false'}">
      <span class="rname"><span>${esc(id === 'other' ? 'Other facts' : cl.title)}<span class="rsrc">, ${esc(cl.source || 'not on the checklist')}</span></span></span>
      <span class="rstat">${outcome}${flagged}</span></button>`;
  }).join('');
  const sel = S.tab === 'review' && S.sel === 'signoff';
  let sign;
  if (S.signed) sign = `<span class="rs done">${icon('lock')}Signed, record locked</span>`;
  else if (ready()) sign = `<span class="rs todo">${icon('check')}Ready: check your answers and sign</span>`;
  else sign = `<span class="rs">${icon('lock')}Cannot start yet: ${num(missingItems().length)} to finish</span>`;
  $('rail').innerHTML = `<div class="eyebrow rail-h">Clauses · work in any order</div><div class="rail-list">${rows}</div>
    <div class="rail-list"><button class="rrow signrow ${sel ? 'is-sel' : ''}" data-act="signoff" data-testid="signoff-row" aria-current="${sel ? 'true' : 'false'}">
      <span class="rname">${icon('pen')}Sign off</span><span class="rstat">${sign}</span></button></div>`;
}

// ---- Right: the selected clause ----
function claimItem(claim) {
  const id = claim.claim_id;
  const d = S.disputes[id];
  const quotes = claim.citations.map((c) => quoteHtml(claim, c)).join('')
    || `<div class="noquote">${icon('searchx')}No quote given</div>`;
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

function pairHtml(p) {
  return `<div class="pair" data-testid="pair">
    <p class="pair-say"><b>${esc(cap(loc(p.a)))}</b>${whenOf(p.a)} and <b>${esc(loc(p.b))}</b>${whenOf(p.b)} disagree. Read both; a later record may supersede an earlier one.</p>
    <ul class="plist">${passageRow(p.a, { excerpt: true, task: isRequired(p.a), testid: 'pair-item' })}${passageRow(p.b, { excerpt: true, task: isRequired(p.b), testid: 'pair-item' })}</ul></div>`;
}

function nextClauseButton(cl) {
  const list = railClauses();
  const next = list[list.findIndex((c) => c.clause_id === cl.clause_id) + 1];
  return next
    ? `<button class="btn-secondary" data-act="clause" data-arg="${esc(next.clause_id)}" data-testid="next-clause" aria-label="Next clause: ${esc(clauseName(next))}">Next clause${icon('arrow')}</button>`
    : `<button class="btn-secondary" data-act="signoff" data-testid="next-clause">Go to sign-off${icon('arrow')}</button>`;
}

function clauseView(cl) {
  const id = cl.clause_id;
  const isOther = id === 'other';
  const st = clauseState(cl);
  const claims = cl.claim_ids.map(claimById).filter(Boolean);
  const head = `<div class="d-head">
    <div class="eyebrow">${isOther ? 'Not on the checklist' : `${icon('landmark')}${esc(cl.source || '')}`}</div>
    <h2 data-testid="clause-title">${esc(isOther ? 'Other facts the AI noted' : cl.title)}</h2>
    <p class="decides">${isOther ? 'Facts that bear on the case but that no checklist clause names. No outcome is needed here.' : `<b>What you decide:</b> ${esc(cl.decides)}`}</p></div>`;
  const pp = cl.policy_passage_id;
  const policy = cl.policy_sentence ? `<div class="policy">
      <div class="policy-h">${kindTag(pp)}<span class="loc">${esc(cap(loc(pp)))}</span><span class="spacer"></span>
        <button class="act" data-act="open" data-arg="${esc(pp)}" data-testid="open-policy"${S.signed ? ' disabled' : ''}>Open the policy passage${icon('arrow')}</button></div>
      <blockquote class="q">“${esc(cl.policy_sentence)}”</blockquote>
      ${cl.policy_items.length ? `<ul class="pitems">${cl.policy_items.map((i) => `<li>${esc(i)}</li>`).join('')}</ul>` : ''}</div>` : '';
  const flagged = st.flagged.length ? `<section class="block flagged" data-testid="flagged">
      <div class="sec-h"><span>Open before you sign</span><span>${num(st.opened)} of ${num(st.flagged.length)} opened</span></div>
      <ul class="plist">${st.flagged.map((r) => passageRow(r.passage_id, { why: readingWhy(r, id), task: true, testid: 'flagged-item' })).join('')}</ul></section>`
    : `<p class="note">${icon('check')}Nothing in this clause is flagged. Read the evidence and ${isOther ? 'move on' : 'set your outcome'}.</p>`;
  const pairs = cl.contradictions.length ? `<section class="block" data-testid="pairs">
      <div class="sec-h"><span>${icon('arrows')}Passages that disagree</span><span>${num(cl.contradictions.length)} ${cl.contradictions.length === 1 ? 'pair' : 'pairs'}</span></div>
      ${cl.contradictions.map(pairHtml).join('')}
      <p class="note">A claim that rests on either passage is marked “Contradicted by another passage”. That says the two records disagree; it does not say the claim misquotes its passage.</p></section>` : '';
  const evidence = claims.length ? `<section class="block">
      <div class="sec-h"><span>Evidence · the quote first, then the AI's claim</span><span>${num(claims.length)} ${claims.length === 1 ? 'claim' : 'claims'}</span></div>
      <div class="items">${claims.map(claimItem).join('')}</div></section>`
    : '<p class="note">The AI wrote no claim for this clause.</p>';
  const gapRows = cl.missing.map((m) => `<div class="gap-row">${pill('slash', 'neutral', COVERAGE.no_evidence_in_file[0])}<span>${esc(m.statement)}</span></div>`);
  if (!gapRows.length && cl.coverage === 'no_evidence_in_file') gapRows.push(`<div class="gap-row">${pill('slash', 'neutral', COVERAGE.no_evidence_in_file[0])}<span>No passage in the file is cited for this clause.</span></div>`);
  const gaps = gapRows.length ? `<section class="block" data-testid="gaps"><div class="sec-h"><span>Looked for and not found</span></div>
      <div class="gaps">${gapRows.join('')}</div>
      <p class="note">No evidence in the file is not the same as “not met”.</p></section>` : '';
  const flaggedIds = new Set(st.flagged.map((r) => r.passage_id));
  const pm = cl.possibly_missed.filter((p) => !flaggedIds.has(p.passage_id));
  const shown = S.pmMore[id] ? pm : pm.slice(0, 3);
  const inFlagged = cl.possibly_missed.length - pm.length;
  const missed = cl.possibly_missed.length ? `<section class="block" data-testid="possibly-missed">
      <div class="sec-h"><span>${pill(COVERAGE.possibly_missed[1], COVERAGE.possibly_missed[2], COVERAGE.possibly_missed[0])}</span><span>${num(cl.possibly_missed.length)} ${cl.possibly_missed.length === 1 ? 'passage' : 'passages'}</span></div>
      <p class="note">The scan found ${cl.possibly_missed.length === 1 ? 'this passage' : 'these passages'} relevant to this clause, and no claim uses ${cl.possibly_missed.length === 1 ? 'it' : 'them'}. Most relevant first${inFlagged ? `; ${num(inFlagged)} ${inFlagged === 1 ? 'is' : 'are'} flagged above` : ''}. Opening the rest is optional.</p>
      ${shown.length ? `<ul class="plist">${shown.map((p) => passageRow(p.passage_id, { excerpt: true, testid: 'missed-item' })).join('')}</ul>` : ''}
      ${pm.length > 3 ? `<button class="act more" data-act="pm-more" data-arg="${esc(id)}" data-testid="pm-more">${S.pmMore[id] ? 'Show fewer' : `Show ${num(pm.length - 3)} more`}</button>` : ''}</section>` : '';
  const o = st.outcome;
  const outbar = isOther
    ? `<div class="outbar"><div class="oc-row"><span class="oc-label">No outcome is needed here.</span><span class="spacer"></span>${nextClauseButton(cl)}</div></div>`
    : `<div class="outbar" data-testid="outcome-bar">
      <div class="oc-label">Your outcome for ${esc(cl.title)}: <span class="state ${o ? '' : 'unset'}" data-testid="outcome-state">${o ? esc(OUTCOME_LABEL[o]) : 'not set'}</span></div>
      <div class="oc-row"><div class="chips" role="radiogroup" aria-label="Your outcome for ${esc(cl.title)}">${OUTCOMES.map(([val, lab, ic]) => `<button class="chip" role="radio" aria-checked="${o === val}" data-act="outcome" data-arg="${esc(id)}" data-val="${val}" data-outcome="${val}" data-testid="outcome-${esc(id)}-${val}"${S.signed ? ' disabled' : ''}>${icon(ic)}${lab}</button>`).join('')}</div>
      <span class="spacer"></span>${nextClauseButton(cl)}</div></div>`;
  return `<div class="clause" data-testid="clause-detail" data-clause="${esc(id)}">${head}${policy}${flagged}${pairs}${evidence}${gaps}${missed}</div>${outbar}`;
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
      <p class="lead">Finish ${items.length === 1 ? 'this clause' : `these ${num(items.length)} clauses`} first. Each one opens when you select it.</p>
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
    <textarea id="reason" data-testid="reason" placeholder="Why this decision, in your words. Name the clauses and pages you relied on.">${esc(S.reason)}</textarea>
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
    return `<div class="cya-row"><dt>${esc(cl ? clauseName(cl) : 'Claim')}</dt><dd><span class="tag ai">AI claim</span> “${esc(c ? c.claim : '')}”<br><b>Your reason:</b> ${esc(d.reason)}</dd><dd class="cya-act">${cl ? change('clause', cl.clause_id, 'dispute') : ''}</dd></div>`;
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
    <div class="sec-h"><span>Clause outcomes, set by you</span></div><dl class="cya">${outcomes}</dl>
    <div class="sec-h"><span>Disputed claims</span><span>${num(Object.keys(S.disputes).length)}</span></div><dl class="cya">${disputes}</dl>
    <div class="sec-h"><span>Flagged passages</span></div>
    <p class="note">${nReq ? `All ${num(nReq)} opened.` : 'Nothing was flagged.'} Opening a passage is recorded; it does not prove it was read.</p>
    ${S.signErr ? `<div class="helper err" data-testid="sign-error">${icon('alert')}${esc(S.signErr)}</div>` : ''}
    <div class="dlg-actions"><button class="btn-secondary" data-act="change-decision">Back</button>
      <button class="btn-primary" data-act="confirm" data-testid="confirm-sign">${icon('pen')}Sign decision</button></div>
  </section>`;
}
function recordView() {
  const { record, json_url: jsonUrl, html_url: htmlUrl } = S.signed;
  const opened = record.passages_opened.map((p) => `<tr><td>${esc(p.label)}<div class="sub">${p.required ? 'Required' : 'Optional'}</div></td>
      <td class="r mono">${esc(fmtTime(p.opened_at))}</td><td class="r mono">${p.seconds_in_view.toFixed(1)} s</td></tr>`).join('')
    || '<tr><td colspan="3">None</td></tr>';
  const disputes = record.disputes.map((d) => `<li><div class="c">${icon('flag')}${esc(d.clause || '')}</div><span class="tag ai">AI claim</span> “${esc(d.claim || '')}”<div><b>Your reason:</b> ${esc(d.reason)}</div></li>`).join('');
  return `<section class="rec" data-testid="record">
    <div class="rec-head"><h2>${icon('lock')}Decision record</h2><span class="tag done">${icon('check')}Signed</span></div>
    <div class="rec-dec">${esc(record.decision_label)}</div>
    <dl class="rec-dl"><dt>File</dt><dd>Applicant file ${esc(record.case_id)}</dd>
      <dt>Reason</dt><dd><div class="rec-reason">${esc(record.reason)}</div></dd>
      <dt>Signed</dt><dd>${num(esc(fmtStamp(record.signed_at)))} by ${esc(record.officer)}</dd></dl>
    <h4>Clause outcomes, set by you</h4>
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

// ---- "Summary under audit" tab (Task-06's audit block) ----
function sentenceStatus(s) {
  const claims = (s.claim_ids || []).map(claimById).filter(Boolean);
  if (!claims.length) return 'none';
  return WORST_FIRST.find((st) => claims.some((c) => c.status === st)) || 'supported';
}
function auditView() {
  const a = S.view.audit;
  if (!a) {
    return `<section class="audit-empty" data-testid="audit-empty"><div class="circle">${icon('file')}</div>
      <h3>No summary was audited for this file</h3>
      <p>When a plain AI summary of this file is put under audit, each of its sentences appears here with how it fared against the file, and the facts it left out are listed.</p></section>`;
  }
  const sents = a.sentences.map((s, i) => ({ ...s, n: i + 1, st: sentenceStatus(s) }));
  const para = sents.map((s) => {
    const [, ic, cls] = CLAIM_STATUS[s.st];
    return `<span class="smark ${cls}">${icon(ic)}${s.n}</span><span class="s s-${s.st}">${esc(s.text)}</span>`;
  }).join(' ');
  const counts = {};
  sents.forEach((s) => { counts[s.st] = (counts[s.st] || 0) + 1; });
  const tally = Object.keys(CLAIM_STATUS).filter((k) => counts[k]).map((k) => `<span>${esc(CLAIM_STATUS[k][0])} ${num(counts[k])}</span>`).join('');
  const rows = sents.map((s) => {
    const claims = (s.claim_ids || []).map(claimById).filter(Boolean);
    const body = claims.length
      ? claims.map((c) => `<div class="evid">${claims.length > 1 ? `<div class="claimline"><span class="tag ai">Claim</span><span>${esc(c.claim)}</span>${statusPill(c.status)}</div>` : ''}
          ${c.citations.map((x) => quoteHtml(c, x, 'audit-cite')).join('') || `<div class="noquote">${icon('searchx')}No passage in the file backs it</div>`}
          <p class="why">${claimReason(c)}</p></div>`).join('')
      : '<p class="why">This sentence states nothing the checks can test against the file.</p>';
    return `<li class="sent" data-testid="audit-sentence" data-status="${s.st}"><span class="sent-n mono">${s.n}</span><div>
      <div class="sent-ai"><span class="tag ai">AI summary</span><span>${esc(s.text)}</span></div>
      <div class="statusline"><span class="list-label">Claim check</span>${statusPill(s.st, 'sentence-status')}</div>
      ${body}</div></li>`;
  }).join('');
  const omitted = (a.omitted || []).map((o) => {
    const c = claimById(o.claim_id);
    const cl = clauseById(o.clause_id);
    return `<li class="omit" data-testid="omitted"><div class="eyebrow">${esc(cl ? clauseName(cl) : 'Evidence map')}</div>
      ${c ? `<div class="claimline"><span class="tag ai">AI claim</span><span>${esc(c.claim)}</span></div>${c.citations.map((x) => quoteHtml(c, x, 'audit-cite')).join('')}` : '<p class="why">A supported fact from the evidence map.</p>'}</li>`;
  }).join('');
  return `<section class="audit" data-testid="audit">
      <div class="eyebrow">Summary under audit</div>
      <h2>Each sentence of a plain AI summary, checked against the file</h2>
      <p class="prov">${icon('info')}<span>A general-purpose AI was given this file and the one line “${esc(a.prompt)}”${a.created ? ` on ${esc(fmtDate(a.created))}` : ''}. Readmark did not write the summary and makes no recommendation. Use it to see what a quick summary gets wrong; decide from the evidence.</span></p>
      <div class="ai-doc"><div class="ai-doc-h"><span class="tag ai">AI summary</span>As received, unedited</div><div class="ai-para">${para}</div></div>
      <div class="tally"><span>Sentences ${num(sents.length)}</span>${tally}<span>Left out ${num((a.omitted || []).length)}</span></div>
    </section>
    <div class="sec-h"><span>Sentence by sentence</span></div>
    <ol class="sent-list">${rows}</ol>
    <div class="sec-h"><span>Left out of the summary</span><span>${num((a.omitted || []).length)}</span></div>
    ${omitted ? `<p class="note">Supported facts on decisive clauses that the summary never states.</p><ul class="omit-list">${omitted}</ul>` : '<p class="note">The summary left out no supported fact on a decisive clause.</p>'}`;
}

// ---- Source pane: one passage at a time ----
function highlight(text, quotes) {
  const ranges = [];
  for (const q of quotes) {
    const n = q.replace(/\s+/g, ' ').trim();
    const i = n ? text.indexOf(n) : -1;
    if (i >= 0) ranges.push([i, i + n.length]);
  }
  ranges.sort((x, y) => x[0] - y[0]);
  let out = '';
  let pos = 0;
  for (const [a, b] of ranges) {
    if (b <= pos) continue;
    const start = Math.max(a, pos);
    out += `${esc(text.slice(pos, start))}<mark>${esc(text.slice(start, b))}</mark>`;
    pos = b;
  }
  return out + esc(text.slice(pos));
}
function renderPane() {
  const pane = $('pane');
  pane.classList.toggle('is-open', !!S.current);
  if (S.signed) {
    pane.innerHTML = `<div class="empty"><div class="circle">${icon('lock')}</div><h3>Decision signed</h3>
      <p>The record is final: passages no longer open, and outcomes and disputes are locked.</p></div>`;
    return;
  }
  if (!S.current) {
    pane.innerHTML = `<div class="empty" data-testid="pane-empty"><div class="circle">${icon('file')}</div><h3>No passage open</h3>
      <p>Select a quote or a flagged passage. It opens here, one at a time, with the quoted words highlighted. Each opening is timed and goes into the decision record.</p></div>`;
    return;
  }
  const { pid, claimIds } = S.current;
  const s = src(pid);
  const here = claimIds.length
    ? claimIds.map(claimById).filter(Boolean)
    : S.view.claims.filter((c) => c.citations.some((x) => x.passage_id === pid));
  const cites = here.flatMap((c) => c.citations.filter((x) => x.passage_id === pid));
  const head = `<div class="pane-head"><span class="eyebrow">Source passage</span>
    <button class="icon-btn" data-act="close-pane" data-testid="close-pane" aria-label="Close the passage">${icon('x')}</button></div>`;
  const log = `<div class="v-log" data-testid="in-view">${icon('clock')}Opened ${num(esc(fmtTime(S.opened[pid].opened_at)))} · in view <span class="mono" id="inView">${Math.floor(secondsInView(pid))}</span> s</div>`;
  if (!s || !s.exists) {
    pane.innerHTML = `${head}<div class="viewer" data-testid="source" data-pid="${esc(pid)}">
      <div class="v-page v-missing">${icon('x')}This passage is not in the file, so the claim's quote could not be checked.</div>
      ${cites.map((c) => `<div class="notfound">Quote given: “${esc(c.quote)}”</div>`).join('')}${log}</div>`;
    return;
  }
  let text = s.text;
  let note = '';
  if (s.kind === 'policy') {
    text = S.policyText[pid];
    if (text === undefined) note = '<p class="note">Reading the pinned policy PDF…</p>';
    if (text === false) note = '<p class="note">The policy PDF could not be read on this machine; the quotes are shown alone.</p>';
    if (!text) text = cites.map((c) => c.quote).join(' … ');
  }
  const found = cites.filter((c) => c.quote_found).map((c) => c.quote);
  if (!cites.length) {
    const cl = S.view.clauses.find((c) => c.policy_passage_id === pid);
    if (cl && cl.policy_sentence) found.push(cl.policy_sentence);
  }
  const item = readingItem(pid);
  const flag = item ? `<div class="v-flag">${isRequired(pid) ? `<span class="tag done">${icon('check')}Flagged · opened</span>` : '<span class="tag">Suggested</span>'}<span>${readingWhy(item)}</span></div>` : '';
  const pairs = pairsWith(pid).map((p) => {
    const other = p.a === pid ? p.b : p.a;
    return `<div class="contra">${icon('arrows')}<span class="spacer">This passage disagrees with <b>${esc(loc(other))}</b>, ${relation(other, pid)}${whenOf(other)}.</span>
      <button class="act" data-act="open" data-arg="${esc(other)}" data-testid="open-other">Open it${icon('arrow')}</button></div>`;
  }).join('');
  const claimList = here.map((c) => `<li>${statusPill(c.status)}<span><span class="tag ai">${S.view.claims.includes(c) ? 'AI claim' : 'AI summary'}</span> ${esc(c.claim)}</span></li>`).join('');
  const where = s.kind === 'policy' ? `${cap(loc(pid))} · version ${s.version}` : `${cap(loc(pid))} · ${String(s.doc_type || '').replace(/-/g, ' ')} · ${fmtDate(s.doc_date)}`;
  pane.innerHTML = `${head}<div class="viewer" data-testid="source" data-pid="${esc(pid)}">
    <div class="v-doc"><div><div class="v-title">${esc(s.doc_title)}</div><div class="v-loc">${esc(where)}</div></div>${kindTag(pid)}</div>
    ${flag}
    <div class="v-page">${highlight(text, found)}</div>${note}
    ${found.length ? `<div class="v-key"><span class="sw"></span>Highlighted: the exact words ${cites.length ? 'a claim quotes' : 'the clause quotes'}</div>` : ''}
    ${cites.filter((c) => !c.quote_found).map((c) => `<div class="notfound">${icon('x')}Quote not found in this passage: “${esc(c.quote)}”</div>`).join('')}
    ${pairs}
    ${claimList ? `<div class="sec-h"><span>Claims that rest on this passage</span></div><ul class="pclaims">${claimList}</ul>` : ''}
    ${log}</div>`;
}

// ---- About these checks: the only place model ids appear ----
function renderAbout() {
  const v = S.view;
  const a = v.audit;
  const m = (x) => `${esc(cap(x.name))} <span class="mono">${esc(x.model || 'no model id')}</span>`;
  const key = (kind, cls, label, text) => `<li>${pill(kind, cls, label)}<span>${text}</span></li>`;
  $('about').innerHTML = `<div class="dlg">
    <div class="dlg-head"><h2 id="aboutTitle">About these checks</h2><button class="icon-btn" data-act="about-close" aria-label="Close">${icon('x')}</button></div>
    <div class="sec-h"><span>Models</span></div>
    <dl class="about-dl"><dt>Writer</dt><dd>${m(v.models.writer)}. Drafted each claim with the exact words it relied on.</dd>
      <dt>Checker</dt><dd>${m(v.models.checker)}. Re-checked each claim, compared passages that may disagree, and scanned the file for relevant passages no claim uses.</dd>
      ${a ? `<dt>Summary under audit</dt><dd><span class="mono">${esc(a.model)}</span>, given “${esc(a.prompt)}”${a.created ? ` on ${esc(fmtDate(a.created))}` : ''}.</dd>` : ''}</dl>
    <div class="sec-h"><span>What each status means</span></div>
    <ul class="key">
      ${key('check', 'ok', 'Supported', 'Every quote is word for word in its passage, its figures and dates appear in a quote, and the second checker agrees.')}
      ${key('arrows', 'warn', 'Contradicted by another passage', 'The claim rests on a passage that another passage disagrees with. The quote may be accurate; the two records conflict.')}
      ${key('neq', 'warn', 'Checker disagrees', 'The second checker could not confirm that the quoted passage says what the claim says.')}
      ${key('searchx', 'bad', 'Quote not found', 'A quote is not in its passage, a figure or date is in no quote, or the claim gives no quote.')}
      ${key('help', 'warn', 'Possibly missed', 'The scan found a passage relevant to the clause that no claim uses.')}
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
  renderTabs();
  renderRail();
  $('detail').innerHTML = S.tab === 'audit' ? auditView() : S.sel === 'signoff' ? signoffView() : clauseView(clauseById(S.sel) || railClauses()[0]);
  renderPane();
  syncBarHeight();
  S.justSet = null;
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
  closePassage();
  S.sel = id;
  S.tab = 'review';
  S.disputing = null;
  render();
  scrollToWork();
}
function selectSignoff() {
  closePassage();
  S.sel = 'signoff';
  S.tab = 'review';
  S.disputing = null;
  S.signErr = '';
  render();
  scrollToWork();
}
function doNext() {
  const n = nextAction();
  if (n.kind === 'passage') {
    if (S.tab !== 'review' || S.sel !== n.clause.clause_id) selectClause(n.clause.clause_id);
    openPassage(n.pid, []);
  } else if (n.kind === 'outcome') {
    if (S.tab !== 'review' || S.sel !== n.clause.clause_id) selectClause(n.clause.clause_id);
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
  S.tab = 'review';
  render();
  scrollToWork();
}

// ---- Events (delegated, so re-rendering never loses a handler) ----
// Once signed, outcomes, disputes and openings are on the record; only looking around remains.
const AFTER_SIGN = new Set(['clause', 'signoff', 'sign', 'next', 'tab', 'theme', 'intro-open', 'intro-close', 'about-open', 'about-close', 'pm-more']);
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
    case 'close-pane': closePassage(); render(); break;
    case 'outcome':
      S.outcomes[arg] = t.dataset.val;
      S.justSet = arg;
      render();
      break;
    case 'tab': S.tab = arg; S.disputing = null; render(); break;
    case 'pm-more': S.pmMore[arg] = !S.pmMore[arg]; render(); break;
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
    case 'theme':
      document.documentElement.dataset.theme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
      renderJob();
      break;
    default: break;
  }
});
document.addEventListener('input', (e) => { if (e.target.id === 'reason') S.reason = e.target.value; });
document.addEventListener('change', (e) => { if (e.target.name === 'decision') S.decision = e.target.value; });
$('about').addEventListener('close', resume);

setInterval(() => {
  const el = $('inView');
  if (el && S.current) el.textContent = Math.floor(secondsInView(S.current.pid));
}, 1000);

// Loading state: skeleton rows shaped like the clause list and the clause.
$('rail').innerHTML = Array.from({ length: 6 }, () => '<div class="skel rrow-skel"></div>').join('');
$('detail').innerHTML = '<div class="skel skel-head"></div><div class="skel skel-body"></div>';

fetch('/api/view')
  .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
  .then((v) => {
    S.view = v;
    S.sel = railClauses().length ? railClauses()[0].clause_id : 'signoff';
    renderAbout();
    render();
  })
  .catch((err) => {
    $('rail').innerHTML = '';
    $('job').textContent = 'The case could not be loaded.';
    $('detail').innerHTML = `<div class="banner" data-testid="load-error">${icon('alert')}<span>The case view could not be loaded (${esc(err.message)}). Run <span class="mono">python -m readmark run --case &lt;case&gt; --replay</span>, then reload this page.</span></div>`;
  });
