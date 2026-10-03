// Case home shares the review screen's palette, typography and browser draft storage.
function readCaseDraft(key) {
  try {
    const draft = JSON.parse(stored(key) || '{}');
    return draft && typeof draft === 'object' && !Array.isArray(draft) ? draft : {};
  } catch { return {}; }
}

async function showHome() {
  $('casebar').hidden = true;
  $('review').hidden = true;
  $('home').hidden = false;
  document.title = 'Readmark · All cases';
  $('serviceContext').innerHTML = 'Case review<br>Demonstration service';
  $('serviceDescription').textContent = 'Evidence and decisions';
  $('officerLabel').textContent = 'Officer';
  $('home').innerHTML = '<p role="status">Loading cases…</p>';
  try {
    const response = await fetch('/api/cases');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const { cases } = await response.json();
    let selected = cases.find((c) => !c.evaluation && !c.signed) || cases[0];
    const decided = (c) => {
      const draft = readCaseDraft(c.draft_key);
      return c.question_ids.filter((id) => OUTCOME_LABEL[draft.outcomes?.[id]]).length;
    };
    const status = (c) => c.signed
      ? `✓ ${c.signed.decision} · ${fmtDate(c.signed.signed_at.slice(0, 10))}`
      : `${decided(c)} of ${c.question_ids.length} decided`;
    const group = (title, members, evaluation = false) => `<section class="case-group${evaluation ? ' evaluation-group' : ''}" aria-label="${title}" data-testid="home-group">
      <h2>${title} <span class="sub">(${members.length})</span></h2>
      ${members.length ? members.map((c) => `<button class="case-row" data-case="${esc(c.case_id)}" data-testid="home-case" aria-pressed="${c === selected}">
        <span class="case-row-name">${esc(c.name)}</span>
        <span>${esc(c.question_list.title)}</span>
        <span>${c.pages} pages · ${esc(status(c))}</span>
      </button>`).join('') : '<p class="note group-empty">No cases here yet.</p>'}</section>`;
    $('home').innerHTML = `<div class="home-heading"><h1>All cases</h1><p>Choose a file to continue your review.</p></div>
      <div class="home-layout"><nav class="case-list" aria-label="Cases">
        <div class="new-case"><button class="btn-secondary" disabled aria-describedby="newCaseNote" data-testid="new-case">New case</button>
          <p class="note" id="newCaseNote">Coming in this build.</p></div>
        ${group('In progress', cases.filter((c) => !c.evaluation && !c.signed))}
        ${group('Completed', cases.filter((c) => !c.evaluation && c.signed))}
        ${group('Evaluation files', cases.filter((c) => c.evaluation), true)}
      </nav><section class="case-summary" id="caseSummary" aria-label="Selected case" data-testid="case-summary"></section></div>
      <footer>Synthetic case files. The officer sets every question outcome and decision.</footer>`;
    function summary() {
      if (!selected) {
        $('caseSummary').innerHTML = '<h2>No cases available</h2><p>Cases appear here once their checks are ready.</p>';
        return;
      }
      const c = selected;
      $('serviceDescription').textContent = c.labels.service;
      $('officerLabel').textContent = c.labels.officer;
      const documents = c.documents.map((d) => `<li><span>${esc(d.doc_title)}</span><span class="sub">Page ${d.page} · ${esc(fmtDate(d.doc_date))}</span></li>`);
      $('caseSummary').innerHTML = `<div class="eyebrow">${c.evaluation ? 'Evaluation file' : c.signed ? 'Completed' : 'In progress'}</div>
        <h2>${esc(c.name)}</h2><p class="home-progress">${esc(status(c))}</p>
        <dl class="home-facts"><dt>Question list</dt><dd>${esc(c.question_list.title)}</dd>
          <dt>File</dt><dd>${c.pages} pages · ${documents.length} documents</dd></dl>
        <a class="btn-primary" data-testid="open-case" href="${c.signed ? esc(c.signed.html_url) : `/?case=${encodeURIComponent(c.case_id)}`}">${c.signed ? 'View record' : 'Open case'} ${icon('arrow')}</a>
        <section class="home-flags"><h3>Flags at a glance</h3>
          <p data-testid="home-tiers">${c.flags.length} need a look · ${c.worth_a_look.length} worth a look</p>
          <p>${c.required_count} required passages to open</p>
          ${c.flags.length ? `<ul>${c.flags.map((title) => `<li><span class="task-icon flag" aria-hidden="true">!</span> ${esc(title)} · Needs a look</li>`).join('')}</ul>` : ''}
          ${c.worth_a_look.length ? `<ul>${c.worth_a_look.map((title) => `<li><span class="task-icon worth" aria-hidden="true">○</span> ${esc(title)} · Worth a look</li>`).join('')}</ul>` : ''}
          <p class="note">Needs a look: a problem in the notes or the file. Worth a look: pages the AI did not use. You decide every outcome.</p></section>
        <section class="home-documents"><h3>Documents (${documents.length})</h3>
          <ul>${documents.slice(0, 4).join('')}</ul>
          ${documents.length > 4 ? `<details><summary>Show all ${documents.length} documents</summary><ul>${documents.slice(4).join('')}</ul></details>` : ''}</section>`;
      document.querySelectorAll('[data-case]').forEach((row) => row.setAttribute('aria-pressed', String(row.dataset.case === c.case_id)));
    }
    $('home').addEventListener('click', (event) => {
      const row = event.target.closest('[data-case]');
      if (!row) return;
      selected = cases.find((c) => c.case_id === row.dataset.case);
      summary();
    });
    summary();
  } catch (err) {
    $('home').innerHTML = `<h1>All cases</h1><p role="alert">The case list could not be loaded (${esc(err.message)}).</p><a class="act" href="/?home=1">Try again</a>`;
  }
}
