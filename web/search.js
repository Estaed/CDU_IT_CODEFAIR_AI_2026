// Search is transient: neither query nor results enter the decision draft or replay cache.
let searchTimer = null;
let searchRequest = null;
let searchHits = [];

function searchMarked(text, ranges) {
  let html = '', cursor = 0;
  ranges.forEach(([start, end]) => {
    html += esc(text.slice(cursor, start)) + `<mark class="search-match" data-testid="search-match">${esc(text.slice(start, end))}</mark>`;
    cursor = end;
  });
  return html + esc(text.slice(cursor));
}

async function searchCase(meaning = false) {
  clearTimeout(searchTimer);
  searchRequest?.abort();
  const controller = new AbortController();
  searchRequest = controller;
  const query = $('caseSearch').value.trim();
  const results = $('searchResults');
  if (!query || !S.view) {
    results.hidden = true;
    results.innerHTML = '';
    $('searchStatus').textContent = '';
    searchHits = [];
    return;
  }
  $('searchStatus').textContent = meaning ? 'Searching by meaning…' : 'Searching words…';
  try {
    const url = new URL(caseApi('/api/search'), location.origin);
    url.searchParams.set('q', query);
    if (meaning) url.searchParams.set('meaning', 'true');
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) throw new Error('Search unavailable');
    const data = await response.json();
    if (searchRequest !== controller) return;
    searchHits = data.groups.flatMap((g) => g.results);
    searchHits.forEach((r) => { S.searchSources[r.passage_id] = r; });
    $('searchStatus').textContent = `${data.mode} · ${searchHits.length} ${searchHits.length === 1 ? 'result' : 'results'}${data.policies_available === false ? ' · Pinned policies unavailable on this machine' : ''}`;
    results.hidden = false;
    results.innerHTML = data.groups.length ? data.groups.map((g) => `<section class="search-document">
      <h2>${esc(g.title)} <span class="note">${g.kind === 'policy' ? 'Policy' : 'Case document'}</span></h2>
      <ul>${g.results.map((r) => `<li><button type="button" class="search-result" data-search-pid="${esc(r.passage_id)}" data-testid="search-result" data-page="${r.page}" data-kind="${r.kind}">
        <span class="search-location">Page ${r.doc_page} · ${esc(r.doc_date ? fmtDate(r.doc_date) : 'Date not recorded')} · ${esc(r.label)}${r.score !== null ? ` · Match ${r.rank}` : ''}</span>
        <span>${r.before ? '… ' : ''}${searchMarked(r.snippet, r.ranges)}${r.after ? ' …' : ''}</span></button></li>`).join('')}</ul></section>`).join('') : '<p>No matches in this case or its policies. Try another word.</p>';
  } catch (error) {
    if (error.name !== 'AbortError' && searchRequest === controller) {
      $('searchStatus').textContent = 'Search could not be loaded. Try again.';
      results.hidden = true;
    }
  }
}

$('caseSearch').addEventListener('input', () => {
  // Invalidate a pending meaning response immediately, before the next debounced request.
  searchRequest?.abort();
  searchRequest = null;
  $('searchResults').hidden = true;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => searchCase(), 250);
});
$('caseSearchForm').addEventListener('submit', (event) => {
  event.preventDefault();
  searchCase(true);
});
$('searchResults').addEventListener('click', (event) => {
  const button = event.target.closest('[data-search-pid]');
  const hit = button && searchHits.find((r) => r.passage_id === button.dataset.searchPid);
  if (!hit || S.signed) return;
  if (S.fullFile) closeFullFile();
  if (hit.kind === 'case') {
    if (S.sel === 'signoff') S.sel = railClauses()[0].clause_id;
    S.fullFile = true;
    openPassage(hit.passage_id, [], false, hit);
    $('fullFile').showModal();
    jumpToPassage(hit.passage_id);
  } else {
    openPassage(hit.passage_id, [], false, hit);
    const source = $('policy').querySelector('[data-testid="source"]');
    source?.scrollIntoView({ block: 'nearest' });
  }
});
