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
    const { cases, question_lists, uploads = [], list_drafts = [] } = await response.json();
    let selected = cases.find((c) => !c.signed) || cases[0];
    const decided = (c) => {
      const draft = readCaseDraft(c.draft_key);
      return c.question_ids.filter((id) => OUTCOME_LABEL[draft.outcomes?.[id]]).length;
    };
    const status = (c) => c.signed
      ? `✓ ${c.signed.decision} · ${fmtDate(c.signed.signed_at.slice(0, 10))}`
      : `${decided(c)} of ${c.question_ids.length} decided`;
    const group = (title, members) => `<section class="case-group" aria-label="${title}" data-testid="home-group">
      <h2>${title} <span class="sub">(${members.length})</span></h2>
      ${members.length ? members.map((c) => `<button class="case-row" data-case="${esc(c.case_id)}" data-testid="home-case" aria-pressed="${c === selected}">
        <span class="case-row-name">${icon('file')}${esc(c.name)}</span>
        <span>${esc(c.question_list.title)}</span>
        <span>${pageCount(c.pages)} · ${esc(status(c))}</span>
      </button>`).join('') : '<p class="note group-empty">No cases here yet.</p>'}</section>`;
    $('home').innerHTML = `<div class="home-heading"><h1>All cases</h1><p>Choose a file to continue your review.</p></div>
      <div class="home-layout"><nav class="case-list" aria-label="Cases">
        <div class="new-case"><button class="btn-secondary" data-testid="new-case">New case</button></div>
        ${uploads.length ? `<section class="case-group" aria-label="Checks underway"><h2>Uploads (${uploads.length})</h2>${uploads.map((job) => `<a class="case-row" href="/?upload=${encodeURIComponent(job.case_id)}"><span class="case-row-name">${esc(job.name)}</span><span>${job.status === 'failed' ? 'Checks stopped' : 'Checks underway'}</span></a>`).join('')}</section>` : ''}
        ${group('In progress', cases.filter((c) => !c.signed))}
        ${group('Completed', cases.filter((c) => c.signed))}
      </nav><section class="case-summary" id="caseSummary" aria-label="Selected case" data-testid="case-summary"></section></div>
      <section class="question-lists" aria-label="Question lists" data-testid="question-lists">
        <h2>Question lists</h2><button class="btn-secondary" data-new-list data-testid="new-list">New question list</button><p class="inset-note">For the person who maintains the list. Jev suggests these may need a question. A person decides.</p>
        ${list_drafts.map((list) => `<div class="question-list-row"><a class="act" href="/?list=${esc(list.id)}">${esc(list.title)}</a><p class="note">${list.status === 'failed' ? 'Suggestions stopped' : 'Awaiting approval'}</p></div>`).join('')}
        ${question_lists.map((list) => `<div class="question-list-row"><h3>${esc(list.title)}</h3>
          ${list.coverage_count == null ? '<p class="note">Policy coverage has not been checked.</p>' : `<a href="#coverage" class="act" data-coverage="${esc(list.id)}">${list.coverage_count} policy rules no question covers</a>`}
          ${list.generated ? `<p><a class="act" href="/?list=${esc(list.id)}">Review approved questions</a></p>` : ''}</div>`).join('')}
      </section>
      <footer>Synthetic case files. The officer sets every question outcome and decision.</footer>`;
    function summary() {
      if (!selected) {
        $('caseSummary').innerHTML = '<h2>No cases available</h2><p>Cases appear here once their checks are ready.</p>';
        return;
      }
      const c = selected;
      $('serviceDescription').textContent = c.labels.service;
      $('officerLabel').textContent = c.labels.officer;
      const documents = c.documents.map((d) => `<li><span>${icon('file')}${esc(d.doc_title)}</span><span class="sub">Document · Page ${d.page} · ${esc(fmtDate(d.doc_date))}</span></li>`);
      $('caseSummary').innerHTML = `<div class="eyebrow">${c.signed ? 'Completed' : 'In progress'}</div>
        <h2>${esc(c.name)}</h2><p class="home-progress">${esc(status(c))}</p>
        <dl class="home-facts"><dt>Question list</dt><dd>${esc(c.question_list.title)}</dd>
          <dt>File</dt><dd>${pageCount(c.pages)} · ${documents.length} ${documents.length === 1 ? 'document' : 'documents'}</dd></dl>
        <a class="btn-primary" data-testid="open-case" href="${c.signed ? esc(c.signed.html_url) : `/?case=${encodeURIComponent(c.case_id)}`}">${c.signed ? 'View record' : 'Open case'} ${icon('arrow')}</a>
        <section class="home-flags"><h3>Flags at a glance</h3>
          <p data-testid="home-tiers">${c.flags.length} need a look · ${c.worth_a_look.length} worth a look</p>
          <p>${c.required_count} required passages to open</p>
          ${c.flags.length ? `<ul>${c.flags.map((title) => `<li><span class="task-icon flag" aria-hidden="true">!</span> ${esc(title)} · Needs a look</li>`).join('')}</ul>` : ''}
          ${c.worth_a_look.length ? `<ul>${c.worth_a_look.map((title) => `<li><span class="task-icon worth" aria-hidden="true">○</span> ${esc(title)} · Worth a look</li>`).join('')}</ul>` : ''}
          <p class="note inset-note">Needs a look: a problem in the notes or the file. Worth a look: pages the AI did not use. You decide every outcome.</p></section>
        <section class="home-documents"><h3>Documents (${documents.length})</h3>
          <ul>${documents.slice(0, 4).join('')}</ul>
          ${documents.length > 4 ? `<details><summary>Show all ${documents.length} documents</summary><ul>${documents.slice(4).join('')}</ul></details>` : ''}</section>`;
      document.querySelectorAll('[data-case]').forEach((row) => row.setAttribute('aria-pressed', String(row.dataset.case === c.case_id)));
    }
    $('home').addEventListener('click', (event) => {
      if (event.target.closest('[data-new-list]')) { showNewList(); return; }
      const coverage = event.target.closest('[data-coverage]');
      if (coverage) {
        event.preventDefault();
        showListCoverage(coverage.dataset.coverage);
        return;
      }
      if (event.target.closest('[data-testid="new-case"]')) {
        showNewCase(question_lists);
        return;
      }
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

// List maintenance opens policies independently of the case opening clock and draft storage.
async function showListCoverage(listId) {
  const dialog = $('coverage');
  dialog.innerHTML = '<div class="dlg"><div class="dlg-head"><h2 id="coverageTitle">Question-list coverage</h2><button class="act" data-coverage-close>Close</button></div><p role="status">Loading suggestions…</p></div>';
  dialog.showModal();
  try {
    const response = await fetch(`/api/question-lists/${encodeURIComponent(listId)}/coverage`);
    if (!response.ok) throw new Error();
    const data = await response.json();
    dialog.innerHTML = `<div class="dlg"><div class="dlg-head"><h2 id="coverageTitle">${esc(data.title)}</h2><button class="act" data-coverage-close>Close</button></div>
      <p>Jev suggests these may need a question. A person decides.</p>
      <p class="note">${data.n_reported} policy rules no question covers · ${data.n_scanned} paragraphs scanned · ${esc(fmtDate(data.date))}</p>
      ${data.suggestions.length ? `<ol class="coverage-suggestions">${data.suggestions.map((s) => `<li data-testid="coverage-suggestion"><h3>${esc(s.section)}</h3><blockquote>${esc(s.excerpt)}…</blockquote>
        <p class="note">Rule score ${s.scores.rule} / 4 · Question coverage ${s.scores.coverage} / 4</p>
        <a href="#policy" class="act" data-list-policy="${esc(s.passage_id)}" data-list="${esc(listId)}" data-section="${esc(s.section)}">Open full policy paragraph</a>
        ${data.generated ? `<p><button class="btn-secondary" data-suggest-rule="${esc(s.passage_id)}" data-list="${esc(listId)}">Suggest a question for this</button></p>` : ''}</li>`).join('')}</ol>` : '<p>No uncovered rules were suggested. This does not prove the question list is complete.</p>'}</div>`;
  } catch {
    dialog.querySelector('[role="status"]').outerHTML = '<p role="alert">The suggestions could not be loaded. Close and try again.</p>';
  }
}

document.addEventListener('click', async (event) => {
  if (event.target.closest('[data-coverage-close]')) $('coverage').close();
  if (event.target.closest('[data-list-policy-close]')) $('coveragePolicy').close();
  const link = event.target.closest('[data-list-policy]');
  if (!link) return;
  event.preventDefault();
  const dialog = $('coveragePolicy');
  dialog.innerHTML = `<div class="dlg"><div class="dlg-head"><h2>${esc(link.dataset.section)}</h2><button class="act" data-list-policy-close>Back to suggestions</button></div><div class="policy-text" role="status">Reading the pinned policy file…</div></div>`;
  dialog.showModal();
  try {
    const response = await fetch(`/api/question-lists/${encodeURIComponent(link.dataset.list)}/passages/${encodeURIComponent(link.dataset.listPolicy)}`);
    if (!response.ok) throw new Error();
    const data = await response.json();
    dialog.querySelector('.policy-text').textContent = data.text;
  } catch {
    dialog.querySelector('.policy-text').innerHTML = '<p role="alert">The pinned policy file could not be read on this machine.</p>';
  }
});
