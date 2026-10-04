// Rulebook maintenance is separate from every case's evidence and opening clock.
const LIST_STEPS = ['Reading the rules', 'Suggesting questions', 'Checking each sentence', 'Ready'];
let returnCaseDraft = null;

async function listRequest(url, payload) {
  const response = await fetch(url, payload === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'The question list could not be saved.');
  return data;
}

function showNewList(caseDraft = null) {
  returnCaseDraft = caseDraft;
  uploadSurface('New question list');
  $('home').innerHTML = `<div class="upload-content"><a class="act" href="/?home=1">All cases</a>
    <h1>New question list</h1><p>Give Readmark the rules. Claude suggests questions; you approve each one.</p>
    <form id="listForm" data-testid="list-form">
      <label class="flabel" for="listName">List name</label><input id="listName" required maxlength="120" data-testid="list-name">
      <label class="flabel" for="listScope">What decisions does this list cover?</label>
      <input id="listScope" required maxlength="1000" aria-describedby="scopeHelp" data-testid="list-scope">
      <p class="helper" id="scopeHelp">One sentence, for example: Decide whether a student qualifies for an assessment extension.</p>
      <details class="list-words"><summary>Screen words (optional)</summary>
        ${[['case_noun', 'What a case is called', 'Applicant file'], ['officer', 'Who decides', 'Delegated officer'],
          ['approve', 'Approve label', 'Approve priority housing'], ['decline', 'Decline label', 'Decline'],
          ['request_information', 'More information label', 'Request more information']].map(([key, title, hint]) =>
          `<label class="flabel" for="word-${key}">${title}</label><input id="word-${key}" maxlength="120" placeholder="${hint}">`).join('')}
      </details>
      <label class="flabel" for="listFiles">Rule files</label><div class="upload-drop" id="listDrop">
        <p>Drop the files here or choose them together.</p><input id="listFiles" type="file" multiple accept=".pdf,.txt" data-testid="list-files">
      </div><p class="helper">PDFs with selectable text or UTF-8 text. Up to 25 MB in total. Scanned rules are not supported.</p>
      <ul class="upload-files" id="listFilesChosen"></ul>
      <p class="err" id="listError" role="alert" hidden></p>
      <button class="btn-primary" type="submit" data-testid="suggest-questions">Suggest questions ${icon('arrow')}</button>
    </form></div>`;
  let files = [];
  const choose = (chosen) => { files = Array.from(chosen); $('listFilesChosen').innerHTML = files.map((f) => `<li>${esc(f.name)}</li>`).join(''); };
  $('listFiles').onchange = (event) => choose(event.target.files);
  $('listDrop').ondragover = (event) => event.preventDefault();
  $('listDrop').ondrop = (event) => { event.preventDefault(); choose(event.dataTransfer.files); };
  $('listForm').onsubmit = async (event) => {
    event.preventDefault();
    const button = event.submitter;
    try {
      if (!files.length || files.some((f) => !/\.(pdf|txt)$/i.test(f.name))) throw new Error('Choose PDF or text rule files.');
      if (files.reduce((sum, f) => sum + f.size, 0) > 25 * 1024 * 1024) throw new Error('Choose files totalling no more than 25 MB.');
      button.disabled = true;
      const encoded = await Promise.all(files.map((file) => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve({ name: file.name, content: reader.result.split(',')[1] });
        reader.onerror = () => reject(new Error('A rule file could not be opened.'));
        reader.readAsDataURL(file);
      })));
      const words = (keys) => Object.fromEntries(keys.map((key) => [key, $(`word-${key}`).value.trim()]).filter(([, value]) => value));
      const result = await listRequest('/api/question-lists', { name: $('listName').value, scope: $('listScope').value,
        labels: words(['case_noun', 'officer']), decisions: words(['approve', 'decline', 'request_information']), files: encoded });
      history.replaceState(null, '', `/?list=${encodeURIComponent(result.list_id)}`);
      showGeneratedList(result.list_id);
    } catch (error) { $('listError').textContent = error.message; $('listError').hidden = false; button.disabled = false; }
  };
}

async function showGeneratedList(listId) {
  uploadSurface('Questions from the rules');
  $('home').innerHTML = `<div class="upload-content list-review"><a class="act" href="/?home=1">All cases</a>
    <h1 id="listTitle">Questions from the rules</h1><p role="status" id="listStatus" data-testid="list-status">Loading suggestions…</p>
    <ol class="upload-steps" id="listSteps" data-testid="list-steps"></ol><div id="listReview"></div></div>`;
  async function poll() {
    if (!$('listStatus')) return;
    try {
      const job = await listRequest(`/api/question-lists/${encodeURIComponent(listId)}/suggestions`);
      if (!$('listStatus')) return;
      $('listTitle').textContent = job.name;
      $('listStatus').textContent = job.status === 'failed' ? job.message : job.steps.at(-1) || 'Rules uploaded';
      $('listSteps').innerHTML = LIST_STEPS.map((step) => `<li><span>${step}</span><span class="upload-step-state">${job.steps.includes(step) ? job.status === 'running' && step === job.steps.at(-1) ? 'In progress' : '✓ Done' : 'Waiting'}</span></li>`).join('');
      if (job.status === 'running') setTimeout(poll, 500);
      else if (job.status === 'ready') renderListReview(listId, job);
    } catch (error) { if ($('listStatus')) $('listStatus').textContent = error.message; }
  }
  await poll();
}

function renderListReview(listId, job) {
  const suggestions = job.suggestions.map((q) => ({ ...q }));
  $('listReview').innerHTML = `<p class="inset-note">Claude suggested these. You decide which questions the officer must answer.</p>
    <p class="note">Approve selects a question for this list. Only Save approved questions makes it available for cases.</p>
    <div id="questionSuggestions" data-testid="question-suggestions"></div>
    <p class="err" role="alert" id="reviewError" hidden></p>
    <p class="note" id="coverageNote" data-testid="coverage-note">${esc(job.coverage_note || '')}</p>
    <button class="btn-primary" id="saveList" data-testid="save-list">Save approved questions</button><div id="listSaved"></div>`;
  const draw = (index = null, focusTarget = null) => {
    $('questionSuggestions').innerHTML = suggestions.map((q, n) => `<section class="question-suggestion" data-testid="question-suggestion" data-index="${n}">
      <h2>${n + 1}. ${esc(q.title)}</h2><p class="suggested-question">${esc(q.decides)}</p>
      <p class="note">${esc(job.policies.find((p) => p.key === q.policy)?.title || q.policy)} · ${esc(q.source)}</p>
      <blockquote class="rule-sentence">${esc(q.sentence)}${(q.items || []).map((item) => `<p>${esc(item)}</p>`).join('')}</blockquote>
      <p>${esc(q.why)}</p><p class="sentence-check${q.sentence_found ? '' : ' err'}" data-testid="sentence-check">${esc(q.check)}</p>
      <p class="note">Suggested by Claude (${esc(q.suggested_by.model)}) on ${esc(q.suggested_by.date)}${q.provenance ? `; approved by a person on ${esc(q.provenance.approved_date)}` : ''}.</p>
      <p class="review-choice" data-testid="review-choice">${q.status === 'approved' ? '✓ Approved for saving' : q.status === 'rejected' ? 'Rejected' : 'Awaiting your choice'}</p>
      <div class="suggestion-actions"><button class="btn-secondary" data-approve${q.sentence_found ? '' : ` disabled aria-describedby="approval-help-${n}"`}>Approve</button>
        <button class="act" data-edit>Edit</button><button class="act" data-reject>Reject</button></div>
      ${q.sentence_found ? '' : `<p class="note" id="approval-help-${n}">Approval unavailable: edit the sentence and check it against the rule first.</p>`}
      <div class="suggestion-editor" hidden>
        ${[['title', 'Title'], ['decides', 'Question'], ['policy', 'Rule file'], ['source', 'Section or page'], ['sentence', 'Verbatim sentence'], ['items', 'Verbatim items (one per line)'], ['why', 'Why it decides the case']].map(([key, label]) =>
          `<label class="flabel" for="edit-${n}-${key}">${label}</label><textarea id="edit-${n}-${key}" data-field="${key}" rows="${key === 'sentence' || key === 'items' ? 3 : 1}">${esc(key === 'items' ? (q.items || []).join('\n') : q[key])}</textarea>`).join('')}
        <button class="btn-secondary" data-check>Check changes</button></div>
    </section>`).join('') || '<p>No questions were suggested. Start again with a different scope or rulebook.</p>';
    if (index !== null && focusTarget) {
      $('questionSuggestions').querySelector(`[data-index="${index}"] ${focusTarget}`)?.focus();
    }
  };
  draw();
  $('questionSuggestions').onclick = async (event) => {
    const row = event.target.closest('[data-index]');
    if (!row) return;
    const index = Number(row.dataset.index);
    const q = suggestions[index];
    if (event.target.closest('[data-edit]')) row.querySelector('.suggestion-editor').hidden = false;
    if (event.target.closest('[data-approve]')) { q.status = 'approved'; draw(index, '[data-approve]'); }
    if (event.target.closest('[data-reject]')) { q.status = 'rejected'; draw(index, '[data-reject]'); }
    if (event.target.closest('[data-check]')) {
      row.querySelectorAll('[data-field]').forEach((input) => { q[input.dataset.field] = input.dataset.field === 'items' ? input.value.split('\n').filter((v) => v.trim()) : input.value; });
      q.status = 'pending';
      try {
        Object.assign(q, await listRequest(`/api/question-lists/${encodeURIComponent(listId)}/check`, q));
        draw(index, q.sentence_found ? '[data-approve]' : '[data-edit]');
      }
      catch (error) { $('reviewError').textContent = error.message; $('reviewError').hidden = false; }
    }
  };
  $('saveList').onclick = async () => {
    // Unsaved text in an open editor must be checked before it can become a question.
    if (Array.from(document.querySelectorAll('.suggestion-editor')).some((editor) => !editor.hidden)) {
      $('reviewError').textContent = 'Use Check changes in each open editor before saving.'; $('reviewError').hidden = false; return;
    }
    try {
      $('saveList').disabled = true;
      const saved = await listRequest(`/api/question-lists/${encodeURIComponent(listId)}/review`, { suggestions });
      $('reviewError').hidden = true;
      $('listSaved').innerHTML = saved.approved_count ? `<p role="status">${saved.approved_count} approved questions saved.</p><button class="btn-secondary" id="useList" data-testid="use-list">${returnCaseDraft ? 'Return to new case' : 'Start a case with this list'}</button><p><button class="act" id="viewCoverage">View rules no question covers</button></p>` : '<p role="status">No questions approved. This list cannot be selected for a case.</p>';
      if (saved.approved_count) {
        $('useList').onclick = async () => {
          const data = await listRequest('/api/cases');
          history.replaceState(null, '', '/?home=1');
          showNewCase(data.question_lists, { ...returnCaseDraft, listId });
        };
        $('viewCoverage').onclick = () => showListCoverage(listId);
        const updateCoverage = async () => {
          if (!$('coverageNote')) return;
          const updated = await listRequest(`/api/question-lists/${encodeURIComponent(listId)}/suggestions`);
          $('coverageNote').textContent = updated.coverage_note;
          if (updated.coverage_note?.startsWith('Checking')) setTimeout(updateCoverage, 500);
        };
        await updateCoverage();
      }
    } catch (error) { $('reviewError').textContent = error.message; $('reviewError').hidden = false; }
    finally { if ($('saveList')) $('saveList').disabled = false; }
  };
}

document.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-suggest-rule]');
  if (!button) return;
  try {
    button.disabled = true;
    await listRequest(`/api/question-lists/${encodeURIComponent(button.dataset.list)}/suggest`, { passage_id: button.dataset.suggestRule });
    $('coverage').close();
    history.replaceState(null, '', `/?list=${encodeURIComponent(button.dataset.list)}`);
    showGeneratedList(button.dataset.list);
  } catch (error) { button.disabled = false; const note = document.createElement('p'); note.setAttribute('role', 'alert'); note.textContent = error.message; button.after(note); }
});
