// Readmark review screen. Reads /api/view (runs/<case>/view.json), opens one passage at a time,
// logs time in view, keeps the officer's clause outcomes and disputes, and posts the decision
// record. The AI never fills a clause outcome; the officer sets every one.
'use strict';

const I = {
  check: '<path d="M20 6 9 17l-5-5"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  minus: '<path d="M5 12h14"/>',
  file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/>',
  lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
};
const icon = (n, s = 14) => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${I[n]}</svg>`;
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const $ = (id) => document.getElementById(id);

// Three status lists, kept apart: claim checks, clause coverage, the officer's outcome.
const CLAIM_STATUS = {
  supported: ['Supported', 'check', 'st-ok'],
  checker_disagrees: ['Checker disagrees', 'alert', 'st-warn'],
  contradicted: ['Contradicted by another passage', 'alert', 'st-warn'],
  quote_not_found: ['Quote not found', 'x', 'st-bad'],
};
const COVERAGE = {
  no_evidence_in_file: ['No evidence in file', 'minus', 'st-muted'],
  possibly_missed: ['Possibly missed', 'alert', 'st-warn'],
};
const OUTCOMES = [['met', 'Met'], ['not_met', 'Not met'], ['cannot_decide', 'Cannot decide yet']];
const VERDICT = { supports: 'supports', contradicts: 'contradicts', not_enough_information: 'not enough information' };
const POLICY_SHORT = { eligibility: 'Eligibility', priority: 'Priority', identification: 'Identification', dfv: 'DFV', discretion: 'Discretion' };

const S = {
  view: null,
  opened: {},     // passage_id -> {opened_at, seconds}
  current: null,  // {pid, claimIds}: the passage shown and the claims it was opened for
  since: null,    // performance.now() when the open passage became visible
  outcomes: {},   // clause_id -> met | not_met | cannot_decide (officer only)
  disputes: {},   // claim_id -> {reason, at}
  disputing: null,
  bannerOn: false,
  signed: null,
  policyText: {}, // passage_id -> text, or false when the server could not read it
};

// ---- Time in view: only the open passage accrues, and only while the page is visible. ----
function pause() {
  if (S.current && S.since !== null) {
    S.opened[S.current.pid].seconds += (performance.now() - S.since) / 1000;
  }
  S.since = null;
}
function resume() {
  if (S.current && !document.hidden && !S.signed && !$('scrim').classList.contains('open')) S.since = performance.now();
}
function secondsInView(pid) {
  const o = S.opened[pid];
  if (!o) return 0;
  const live = S.current && S.current.pid === pid && S.since !== null ? (performance.now() - S.since) / 1000 : 0;
  return o.seconds + live;
}
document.addEventListener('visibilitychange', () => (document.hidden ? pause() : resume()));

function openPassage(pid, claimIds = []) {
  if (S.signed) return;
  pause();
  if (!S.opened[pid]) S.opened[pid] = { opened_at: new Date().toISOString(), seconds: 0 };
  S.current = { pid, claimIds };
  resume();
  const src = S.view.sources[pid];
  if (src && src.kind === 'policy' && !(pid in S.policyText)) {
    fetch(`/api/passages/${encodeURIComponent(pid)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { S.policyText[pid] = d ? d.text : false; renderPane(); })
      .catch(() => { S.policyText[pid] = false; renderPane(); });
  }
  render();
}

// ---- Labels ----
function shortLabel(pid) {
  const s = S.view.sources[pid];
  if (!s || !s.exists) return pid;
  if (s.kind === 'policy') return `${POLICY_SHORT[pid.split(':')[0]] || s.doc_title} ${s.section ? s.section.split(' ')[0] : `p. ${s.page}`}`;
  return `p. ${s.page} ¶${pid.split(':')[2]}`;
}
function longLabel(pid) {
  const s = S.view.sources[pid];
  if (!s || !s.exists) return `${pid} (not in the file)`;
  if (s.kind === 'policy') return `${s.doc_title} ${s.section || ''} · p. ${s.page}`;
  return `p. ${s.page} ¶${pid.split(':')[2]} · ${s.doc_title}`;
}
const claimById = (id) => S.view.claims.find((c) => c.claim_id === id);
const clauses = () => S.view.clauses.filter((c) => c.clause_id !== 'other');
const requiredIds = () => S.view.required_reading.map((r) => r.passage_id);

function lockState() {
  const passages = requiredIds().filter((pid) => !S.opened[pid]);
  const outcomes = clauses().filter((c) => !S.outcomes[c.clause_id]);
  return { passages, outcomes, locked: passages.length > 0 || outcomes.length > 0 };
}

// ---- Header, gate and banner ----
function renderHeader() {
  const v = S.view;
  $('caseId').textContent = v.case.case_id;
  $('caseSub').innerHTML = `Synthetic file, <span class="mono">${v.case.pages}</span> pages · checked against <span class="mono">${v.policies.length}</span> NT public housing policies`;
  const light = document.documentElement.dataset.theme === 'light';
  $('tags').innerHTML = `<span class="tag">Writer: ${esc(v.models.writer.name === 'claude' ? 'Claude' : v.models.writer.name)} <span class="mono">${esc(v.models.writer.model || '')}</span></span>`
    + `<span class="tag">Checker: ${esc(v.models.checker.name === 'jev' ? 'Jev' : v.models.checker.name)} <span class="mono">${esc(v.models.checker.model || '')}</span></span>`
    + `<button class="ghost" id="theme">${light ? 'Dark mode' : 'Light mode'}</button>`;
  $('theme').onclick = () => {
    document.documentElement.dataset.theme = light ? 'dark' : 'light';
    renderHeader();
  };
}

function renderGate() {
  const req = requiredIds();
  const n = req.filter((pid) => S.opened[pid]).length;
  $('gateCount').textContent = `${n}/${req.length}`;
  $('segs').innerHTML = req.map((pid) => `<i class="${S.opened[pid] ? 'on' : ''}"></i>`).join('');
  const lock = lockState();
  const btn = $('signBtn');
  btn.textContent = S.signed ? 'Signed' : 'Sign decision';
  btn.className = S.signed ? 'btn-secondary' : 'btn-primary';
  btn.dataset.locked = String(lock.locked);
  let html = '';
  if (S.bannerOn && lock.locked && !S.signed) {
    const parts = [];
    if (lock.passages.length) parts.push(`Open the required passages: ${lock.passages.map((p) => esc(shortLabel(p))).join(', ')}. Each one backs a claim whose check failed.`);
    if (lock.outcomes.length) parts.push(`Set your outcome for: ${lock.outcomes.map((c) => esc(c.title)).join(', ')}.`);
    html = `<div class="banner" data-testid="lock-banner">${icon('lock', 16)}<span><strong>Sign-off is locked.</strong> ${parts.join(' ')}</span></div>`;
  }
  $('banner').innerHTML = html;
}

// ---- Left column: required reading, then evidence by clause ----
function renderRequired() {
  const v = S.view;
  const row = (r, kind) => {
    const done = !!S.opened[r.passage_id];
    const reasons = r.reasons.map((x) => CLAIM_STATUS[x][0]).join(', ');
    return `<button class="row req-row" data-testid="${kind}-item" data-pid="${esc(r.passage_id)}" data-claims="${esc(r.claim_ids.join(','))}" aria-pressed="${!!(S.current && S.current.pid === r.passage_id)}">
      <span class="rank mono">${r.rank}</span>
      <span><span class="row-title">${esc(longLabel(r.passage_id))}</span>
        <span class="row-sub">${esc(reasons)} · claim <span class="mono">${esc(r.claim_ids.join(', '))}</span></span></span>
      ${kind === 'req' ? `<span class="req ${done ? 'done' : ''}">${done ? 'Opened' : 'Must open'}</span>` : ''}</button>`;
  };
  let html = `<div class="eyebrow">Required reading, most decisive first · at most <span class="mono">${v.cap}</span></div>`;
  html += v.required_reading.length
    ? `<div class="card">${v.required_reading.map((r) => row(r, 'req')).join('')}</div>`
    : '<div class="card empty-row">No claim failed a check, so nothing is required. You still set every outcome.</div>';
  if (v.suggested_reading.length) {
    html += `<div class="eyebrow sub-eyebrow">Also flagged, suggested</div><div class="card">${v.suggested_reading.map((r) => row(r, 'sug')).join('')}</div>`;
  }
  $('reqSection').innerHTML = html;
}

function citationHtml(claim, c) {
  const bad = !c.quote_found;
  return `<button class="quote ${bad ? 'quote-bad' : ''}" data-pid="${esc(c.passage_id)}" data-claims="${esc(claim.claim_id)}" aria-pressed="${!!(S.current && S.current.pid === c.passage_id && S.current.claimIds.includes(claim.claim_id))}">
    <span class="loc">${esc(shortLabel(c.passage_id))}</span>
    <span class="qtext">“${esc(c.quote)}”</span>
    ${bad ? `<span class="qflag">${icon('x', 12)} not in this passage</span>` : ''}</button>`;
}

// "Quote not found" covers both code checks (Task-00). When every quote was found, the failure is
// a number or date that no quote contains, and the screen says so instead of leaving the label
// next to a highlighted quote unexplained.
function valuesNote(claim) {
  if (!claim.values_missing.length) return '';
  const values = `<span class="mono">${esc(claim.values_missing.join(', '))}</span>`;
  const allFound = claim.citations.length > 0 && claim.citations.every((c) => c.quote_found);
  return allFound ? `Quotes found, but none contains ${values} · ` : `Not in any quote: ${values} · `;
}

function claimHtml(claim) {
  const [label, ic, cls] = CLAIM_STATUS[claim.status];
  const ch = claim.checker;
  const checker = ch && ch.verdict ? `Checker: ${esc(VERDICT[ch.verdict] || ch.verdict)}${ch.probability != null ? ` <span class="mono">${Number(ch.probability).toFixed(2)}</span>` : ''}` : 'Checker: not run';
  const missing = valuesNote(claim);
  const mustOpen = claim.required ? (claim.citations.every((c) => S.opened[c.passage_id]) ? '<span class="req done">Opened</span>' : '<span class="req">Must open</span>') : '';
  const d = S.disputes[claim.claim_id];
  // After sign-off the record is final, so the screen stops taking disputes.
  let dispute = S.signed ? '' : `<button class="ghost" data-dispute="${esc(claim.claim_id)}">${d ? 'Edit dispute' : 'Dispute'}</button>`;
  let disputeBody = d ? `<div class="disputed">${icon('alert', 12)} Disputed: ${esc(d.reason)}</div>` : '';
  if (S.disputing === claim.claim_id) {
    dispute = '';
    disputeBody = `<div class="dispute-form"><label class="field-label" for="dr-${esc(claim.claim_id)}">Why is this claim wrong?</label>
      <textarea id="dr-${esc(claim.claim_id)}" data-testid="dispute-reason">${esc(d ? d.reason : '')}</textarea>
      <div class="helper" id="dh-${esc(claim.claim_id)}">Your reason goes on the decision record.</div>
      <div class="dialog-actions"><button class="btn-secondary" data-dispute-cancel="1">Cancel</button>
      <button class="btn-secondary" data-dispute-save="${esc(claim.claim_id)}">Save dispute</button></div></div>`;
  }
  return `<div class="claim-row" data-claim="${esc(claim.claim_id)}">
    <div class="quotes">${claim.citations.map((c) => citationHtml(claim, c)).join('')}</div>
    <div class="claim-text"><span class="who">AI claim</span> ${esc(claim.claim)}</div>
    <div class="row-foot"><span class="pill ${cls}">${icon(ic, 12)} ${label}</span>
      <span class="muted">${missing}${checker}</span><span class="spacer"></span>${mustOpen}${dispute}</div>
    ${disputeBody}</div>`;
}

function clauseHtml(cl) {
  const claims = cl.claim_ids.map(claimById);
  const policy = cl.policy_sentence
    ? `<div class="policy"><div class="policy-head"><span class="tag">Real NT policy</span>
        <button class="ghost" data-pid="${esc(cl.policy_passage_id)}">Open ${esc(cl.source)}</button></div>
        <p>“${esc(cl.policy_sentence)}”</p>${cl.policy_items.length ? `<ul>${cl.policy_items.map((i) => `<li>${esc(i)}</li>`).join('')}</ul>` : ''}</div>`
    : '';
  const coverage = [];
  if (cl.coverage && !cl.missing.length) {
    const [label, ic, cls] = COVERAGE[cl.coverage];
    coverage.push(`<div class="coverage-row"><span class="pill ${cls}">${icon(ic, 12)} ${label}</span><span>No passage in the file was cited for this clause.</span></div>`);
  }
  for (const m of cl.missing) {
    const [label, ic, cls] = COVERAGE.no_evidence_in_file;
    coverage.push(`<div class="coverage-row"><span class="pill ${cls}">${icon(ic, 12)} ${label}</span><span>${esc(m.statement)}</span></div>`);
  }
  const outcome = cl.clause_id === 'other' ? '' : `<div class="outcome" role="radiogroup" aria-label="Your outcome for ${esc(cl.title)}">
      <span class="eyebrow">Your outcome</span>
      <div class="seg">${OUTCOMES.map(([val, lab]) => `<button role="radio" data-testid="outcome-${esc(cl.clause_id)}-${val}" data-outcome="${val}" data-clause="${esc(cl.clause_id)}" aria-checked="${S.outcomes[cl.clause_id] === val}"${S.signed ? ' disabled' : ''}>${lab}</button>`).join('')}</div>
      ${S.outcomes[cl.clause_id] ? '' : '<span class="muted">Not set</span>'}</div>`;
  return `<section class="group" data-clause="${esc(cl.clause_id)}">
    <div class="eyebrow">${esc(cl.source ? `${cl.source} · ${cl.title}` : cl.title)}</div>
    <div class="card">${policy}
      ${claims.map(claimHtml).join('')}
      ${coverage.join('')}
      ${outcome}</div></section>`;
}

function renderClauses() {
  $('clauses').innerHTML = `<div class="eyebrow section-eyebrow">Evidence by policy clause · quote first, then the AI's claim</div>`
    + S.view.clauses.map(clauseHtml).join('');
}

// ---- Right column: one source passage, or the decision record ----
function highlight(text, quotes) {
  const ranges = [];
  for (const q of quotes) {
    const n = q.replace(/\s+/g, ' ').trim();
    const i = n ? text.indexOf(n) : -1;
    if (i >= 0) ranges.push([i, i + n.length]);
  }
  ranges.sort((a, b) => a[0] - b[0]);
  let out = '';
  let pos = 0;
  for (const [a, b] of ranges) {
    if (b <= pos) continue;
    const start = Math.max(a, pos);
    out += esc(text.slice(pos, start)) + `<mark>${esc(text.slice(start, b))}</mark>`;
    pos = b;
  }
  return out + esc(text.slice(pos));
}

function fmtTime(iso) {
  return new Date(iso).toLocaleTimeString('en-AU', { hour12: false });
}

function recordHtml() {
  const { record, json_url: jsonUrl, html_url: htmlUrl } = S.signed;
  const outcomeLabel = Object.fromEntries(OUTCOMES);
  return `<div class="rec" data-testid="record"><div class="eyebrow">Decision record</div>
    <div class="rec-decision">${esc(record.decision_label)}</div>
    <dl><dt>Reason</dt><dd>${esc(record.reason)}</dd>
      <dt>Signed</dt><dd><span class="mono">${esc(fmtTime(record.signed_at))}</span> by ${esc(record.officer)}</dd>
      <dt>Disputes</dt><dd>${record.disputes.length ? record.disputes.map((d) => `<span class="mono">${esc(d.claim_id)}</span>: ${esc(d.reason)}`).join('<br>') : 'None'}</dd>
      <dt>Models</dt><dd>Writer ${esc(record.models.writer.name)} · checker ${esc(record.models.checker.name)}</dd></dl>
    <div class="eyebrow rec-sub">Clause outcomes, set by you</div>
    <ul>${record.clause_outcomes.map((o) => `<li><span>${esc(o.title)}</span><span>${esc(outcomeLabel[o.outcome])}</span></li>`).join('')}</ul>
    <div class="eyebrow rec-sub">Passages opened before signing</div>
    <ul>${record.passages_opened.map((p) => `<li><span>${esc(p.label)}${p.required ? ' · required' : ''}</span><span class="mono">${esc(fmtTime(p.opened_at))} · ${p.seconds_in_view.toFixed(1)} s</span></li>`).join('')}</ul>
    <p class="muted">${esc(record.note)}</p>
    <div class="exports"><a class="btn-secondary" href="${esc(htmlUrl)}" target="_blank" rel="noopener" data-testid="export-html">Export HTML</a>
      <a class="btn-secondary" href="${esc(jsonUrl)}" download data-testid="export-json">Export JSON</a></div></div>`;
}

function renderPane() {
  const pane = $('pane');
  if (S.signed) { pane.innerHTML = recordHtml(); return; }
  if (!S.current) {
    pane.innerHTML = `<div class="empty"><div class="circle">${icon('file', 40)}</div>Select a quote, a required passage or a policy clause to open it here. Passages open one at a time, and the time each one is in view is recorded.</div>`;
    return;
  }
  const { pid, claimIds } = S.current;
  const s = S.view.sources[pid];
  // Highlight the quotes of the claims the passage was opened for (all of them when opened
  // from a policy clause), and list those claims with their own check results.
  const cites = S.view.claims.flatMap((c) => c.citations.filter((x) => x.passage_id === pid).map((x) => ({ ...x, claim_id: c.claim_id })))
    .filter((x) => !claimIds.length || claimIds.includes(x.claim_id));
  const forClaims = claimIds.map(claimById).filter(Boolean).map((c) => {
    const [label, ic, cls] = CLAIM_STATUS[c.status];
    const miss = valuesNote(c);
    return `<div class="pane-claim"><span class="pill ${cls}">${icon(ic, 12)} ${label}</span>
      <span><span class="who">AI claim <span class="mono">${esc(c.claim_id)}</span></span> ${esc(c.claim)}${miss ? ` <span class="muted">· ${miss.replace(/ · $/, '')}</span>` : ''}</span></div>`;
  }).join('');
  const head = `<div class="pane-head"><div class="eyebrow">Source passage</div></div>`;
  const foot = `<div class="src-foot"><span>Highlighted: the exact quote the claim rests on</span>
    <span data-testid="in-view">Opened <span class="mono">${esc(fmtTime(S.opened[pid].opened_at))}</span> · in view <span class="mono" id="inView">${Math.floor(secondsInView(pid))}</span> s</span></div>`;
  if (!s || !s.exists) {
    pane.innerHTML = `${head}<div class="src"><div class="src-doc">${esc(pid)}</div>
      <div class="passage passage-missing">${icon('x', 14)} This passage id is not in the file, so the claim's quote could not be checked.</div>
      ${cites.map((c) => `<div class="notfound">Quote given: “${esc(c.quote)}”</div>`).join('')}${forClaims}${foot}</div>`;
    return;
  }
  let text = s.text;
  let note = '';
  if (s.kind === 'policy') {
    text = S.policyText[pid];
    if (text === undefined) note = '<div class="muted">Reading the pinned policy PDF…</div>';
    if (text === false) note = '<div class="muted">The policy PDF could not be read on this machine; the quotes are shown alone.</div>';
    if (!text) text = cites.map((c) => c.quote).join(' … ');
  }
  const found = cites.filter((c) => c.quote_found).map((c) => c.quote);
  if (!cites.length) {
    const cl = S.view.clauses.find((c) => c.policy_passage_id === pid);
    if (cl && cl.policy_sentence) found.push(cl.policy_sentence);
  }
  const notFound = cites.filter((c) => !c.quote_found);
  const loc = s.kind === 'policy'
    ? `${esc(s.section || '')} · p. <span class="mono">${s.page}</span> · version <span class="mono">${esc(s.version)}</span>`
    : `p. <span class="mono">${s.page}</span> · ${esc(s.doc_type)} · <span class="mono">${esc(s.doc_date)}</span>`;
  pane.innerHTML = `${head}<div class="src" data-testid="source" data-pid="${esc(pid)}">
    <div class="src-headline"><span class="src-doc">${esc(s.doc_title)}</span><span class="tag">${s.kind === 'policy' ? 'Real NT policy' : 'Synthetic file'}</span></div>
    <div class="sub src-loc">${loc}</div>
    <div class="passage">${highlight(text, found)}</div>${note}
    ${notFound.map((c) => `<div class="notfound">${icon('x', 12)} Quote not found in this passage: “${esc(c.quote)}”</div>`).join('')}
    ${forClaims}${foot}</div>`;
}

function render() {
  renderHeader();
  renderGate();
  renderRequired();
  renderClauses();
  renderPane();
}

// ---- Events (delegated, so re-rendering never loses a handler) ----
document.addEventListener('click', (e) => {
  const t = e.target.closest('button, a');
  // Once signed, outcomes and disputes are on the record; an edit here would never reach it.
  if (!t || !S.view || (S.signed && t.tagName !== 'A')) return;
  if (t.dataset.outcome) {
    S.outcomes[t.dataset.clause] = t.dataset.outcome;
    render();
  } else if (t.dataset.dispute) {
    S.disputing = t.dataset.dispute;
    render();
    const box = $(`dr-${S.disputing}`);
    if (box) box.focus();
  } else if (t.dataset.disputeCancel) {
    S.disputing = null;
    render();
  } else if (t.dataset.disputeSave) {
    const id = t.dataset.disputeSave;
    const reason = $(`dr-${id}`).value.trim();
    if (!reason) {
      $(`dh-${id}`).textContent = 'Write a reason. A dispute without one cannot go on the record.';
      $(`dh-${id}`).className = 'helper err';
      return;
    }
    S.disputes[id] = { reason, at: new Date().toISOString() };
    S.disputing = null;
    render();
  } else if (t.dataset.pid) {
    openPassage(t.dataset.pid, t.dataset.claims ? t.dataset.claims.split(',') : []);
  }
});

$('signBtn').onclick = () => {
  if (S.signed || !S.view) return;
  if (lockState().locked) { S.bannerOn = true; renderGate(); return; }
  $('helper').textContent = 'Write it so the applicant could read and challenge it.';
  $('helper').className = 'helper';
  // The dialog covers the passage, so its time is not time in view.
  pause();
  $('scrim').classList.add('open');
  $('reason').focus();
};
function closeDialog() {
  if (!$('scrim').classList.contains('open')) return;
  $('scrim').classList.remove('open');
  resume();
}
$('cancel').onclick = closeDialog;
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDialog(); });

$('confirm').onclick = async () => {
  const d = document.querySelector('input[name=decision]:checked');
  const reason = $('reason').value.trim();
  const helper = $('helper');
  if (!d || !reason) {
    helper.textContent = 'Choose a decision and write a reason. Both go on the record.';
    helper.className = 'helper err';
    return;
  }
  pause();
  const payload = {
    officer: 'Delegated officer',
    decision: d.value,
    reason,
    clause_outcomes: S.outcomes,
    passages_opened: Object.entries(S.opened).map(([pid, o]) => ({ passage_id: pid, opened_at: o.opened_at, seconds_in_view: Math.round(o.seconds * 10) / 10 })),
    disputes: Object.entries(S.disputes).map(([claimId, x]) => ({ claim_id: claimId, reason: x.reason, at: x.at })),
  };
  let res;
  try {
    res = await fetch('/api/records', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  } catch {
    helper.textContent = 'The record could not be saved. Check that the Readmark server is running and sign again.';
    helper.className = 'helper err';
    return;
  }
  const body = await res.json();
  if (!res.ok) {
    helper.textContent = `Not signed: ${(body.problems || [body.detail || 'unknown error']).join(' ')}`;
    helper.className = 'helper err';
    return;
  }
  S.signed = body;
  $('scrim').classList.remove('open');
  render();
};

setInterval(() => {
  const el = $('inView');
  if (el && S.current) el.textContent = Math.floor(secondsInView(S.current.pid));
}, 1000);

fetch('/api/view')
  .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
  .then((v) => { S.view = v; render(); })
  .catch((err) => {
    $('clauses').innerHTML = `<div class="banner">${icon('alert', 16)}<span>The case view could not be loaded (${esc(err.message)}). Run <span class="mono">python -m readmark run --case stub --replay</span>, then reload.</span></div>`;
  });
