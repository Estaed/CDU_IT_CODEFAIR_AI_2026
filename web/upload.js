// A short form and a persisted progress page use the same service layout as case home.
const UPLOAD_STEPS = ['Splitting into passages', 'The AI is reading', 'Checking quotes', 'Second reader', 'Ready'];

function uploadSurface(title) {
  $('casebar').hidden = true;
  $('review').hidden = true;
  $('home').hidden = false;
  document.title = `Readmark · ${title}`;
  $('serviceContext').innerHTML = 'Case review<br>Demonstration service';
  $('serviceDescription').textContent = 'Evidence and decisions';
  $('officerLabel').textContent = 'Officer';
}

function showNewCase(lists) {
  uploadSurface('New case');
  $('home').innerHTML = `<div class="upload-content"><a class="act" href="/?home=1">All cases</a>
    <h1>New case</h1><p>Add the documents for one case, then run the checks.</p>
    <form id="uploadForm" data-testid="upload-form">
      <label class="flabel" for="uploadName">Case name</label>
      <input id="uploadName" name="name" maxlength="120" required autocomplete="off" data-testid="upload-name">
      <label class="flabel" for="uploadList">Question list</label>
      <select id="uploadList" name="question_list" required data-testid="upload-list">${lists.map((list) => `<option value="${esc(list.id)}"${list.id === 'nt-priority-housing' ? ' selected' : ''}>${esc(list.title)}</option>`).join('')}</select>
      <label class="flabel" for="uploadFiles">Documents</label>
      <div class="upload-drop" id="uploadDrop" data-testid="upload-drop">
        <p>Drop the files here or choose them together.</p>
        <input id="uploadFiles" type="file" multiple accept=".pdf,.txt,.md" aria-describedby="uploadHelp" data-testid="upload-files">
      </div>
      <p class="helper" id="uploadHelp">PDFs with selectable text, or UTF-8 text files. Up to 25 MB in total.</p>
      <ul id="uploadFileList" class="upload-files" data-testid="upload-file-list"></ul>
      <p class="note">Use synthetic case documents only. The AI checks the evidence; you decide every outcome.</p>
      <p class="err" id="uploadError" role="alert" hidden data-testid="upload-error"></p>
      <button class="btn-primary" type="submit" data-testid="run-checks">Run checks ${icon('arrow')}</button>
    </form></div>`;
  let files = [];
  function choose(chosen) {
    files = Array.from(chosen);
    $('uploadFileList').innerHTML = files.map((file) => `<li>${esc(file.name)} <span class="sub">(${Math.max(1, Math.round(file.size / 1024))} KB)</span></li>`).join('');
  }
  $('uploadFiles').addEventListener('change', (event) => choose(event.target.files));
  const drop = $('uploadDrop');
  drop.addEventListener('dragover', (event) => { event.preventDefault(); drop.classList.add('dragging'); });
  drop.addEventListener('dragleave', () => drop.classList.remove('dragging'));
  drop.addEventListener('drop', (event) => {
    event.preventDefault();
    drop.classList.remove('dragging');
    choose(event.dataTransfer.files);
  });
  $('uploadForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = event.submitter;
    const error = $('uploadError');
    error.hidden = true;
    if (!files.length || files.some((file) => !/\.(pdf|txt|md)$/i.test(file.name))) {
      error.textContent = 'Choose one or more PDF or text files.';
      error.hidden = false;
      return;
    }
    if (files.reduce((total, file) => total + file.size, 0) > 25 * 1024 * 1024) {
      error.textContent = 'Choose files totalling no more than 25 MB.';
      error.hidden = false;
      return;
    }
    button.disabled = true;
    button.textContent = 'Uploading documents…';
    try {
      const encoded = await Promise.all(files.map((file) => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve({ name: file.name, content: reader.result.split(',')[1] });
        reader.onerror = () => reject(new Error('A selected file could not be opened.'));
        reader.readAsDataURL(file);
      })));
      const response = await fetch('/api/cases', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: $('uploadName').value, question_list: $('uploadList').value, files: encoded }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'The upload could not be saved.');
      history.replaceState(null, '', `/?upload=${encodeURIComponent(result.case_id)}`);
      showUpload(result.case_id);
    } catch (err) {
      error.textContent = err.message === 'Failed to fetch' ? 'The server could not be reached; keep your files and try again.' : err.message;
      error.hidden = false;
      button.disabled = false;
      button.innerHTML = `Run checks ${icon('arrow')}`;
    }
  });
  $('uploadName').focus();
}

async function showUpload(cid) {
  uploadSurface('Checking a new case');
  $('home').innerHTML = `<div class="upload-content"><a class="act" href="/?home=1">All cases</a>
    <h1 id="uploadTitle">Checking a new case</h1>
    <p id="uploadStatus" role="status" aria-live="polite" data-testid="upload-status">Loading progress…</p>
    <ol class="upload-steps" id="uploadSteps" data-testid="upload-steps"></ol>
    <section class="home-documents"><h2>Uploaded documents</h2><ul id="uploadDocuments"></ul></section>
    <p class="err" id="uploadFailure" role="alert" hidden data-testid="upload-failure"></p>
    <div id="uploadAction"></div></div>`;
  async function poll() {
    try {
      const response = await fetch(`/api/uploads/${encodeURIComponent(cid)}`);
      if (!response.ok) throw new Error();
      const job = await response.json();
      $('uploadTitle').textContent = job.name;
      const current = job.steps.at(-1);
      const text = job.status === 'ready' ? 'Ready' : job.status === 'failed' ? 'Checks stopped' : current || 'Documents uploaded';
      if ($('uploadStatus').textContent !== text) $('uploadStatus').textContent = text;
      $('uploadSteps').innerHTML = UPLOAD_STEPS.map((step) => {
        const done = job.steps.includes(step) && (step !== current || job.status === 'ready');
        const state = done ? 'Done' : step === current ? job.status === 'failed' ? 'Stopped' : 'In progress' : 'Waiting';
        return `<li${step === current ? ' aria-current="step"' : ''}><span>${esc(step)}</span><span class="upload-step-state">${done ? '✓ ' : ''}${state}</span></li>`;
      }).join('');
      $('uploadDocuments').innerHTML = job.files.map((name) => `<li>${esc(name)}</li>`).join('');
      if (job.status === 'failed') {
        $('uploadFailure').textContent = job.message;
        $('uploadFailure').hidden = false;
      } else if (job.status === 'ready') {
        $('uploadAction').innerHTML = `<p>The case is now in In progress. You decide every question outcome.</p><a class="btn-primary" href="/?case=${encodeURIComponent(cid)}" data-testid="open-new-case">Open case ${icon('arrow')}</a>`;
      } else {
        setTimeout(poll, 500);
      }
    } catch {
      $('uploadStatus').textContent = 'Progress could not be loaded; reload this page to check again.';
    }
  }
  await poll();
}
