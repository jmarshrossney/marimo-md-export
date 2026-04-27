document$.subscribe(function() {
  const tocInner = document.querySelector('.md-sidebar--secondary .md-sidebar__inner');
  if (!tocInner || tocInner.querySelector('.marimo-open-btn')) return;

  const stripped = window.location.pathname.replace(/\/$/, '');
  const lastSlash = stripped.lastIndexOf('/');
  const basename = stripped.slice(lastSlash + 1).replace(/\.html$/, '');
  const dir = stripped.slice(0, lastSlash + 1);
  const notebookUrl = dir + basename + '-notebook.html';

  fetch(notebookUrl, { method: 'HEAD' }).then(function(response) {
    if (!response.ok) return;

    const config = JSON.parse(document.getElementById('__config').textContent);
    const svgUrl = config.base + '/_static/img/marimo.svg';

    const div = document.createElement('div');
    div.style.padding = '0.8em 0.6em 1.6em';
    div.innerHTML =
      '<a href="' + notebookUrl + '" class="marimo-open-btn" style="'
      + 'display:flex;flex-direction:column;align-items:center;gap:0.6em;'
      + 'border:1.5px solid var(--md-default-fg-color);border-radius:8px;'
      + 'padding:0.8em 0.6em;text-decoration:none;color:var(--md-default-fg-color);'
      + 'font-size:0.75rem;font-weight:700;text-align:center">'
      + '<img src="' + svgUrl + '" alt="Marimo" style="width:85%">'
      + 'Open as Marimo Notebook'
      + '</a>';
    tocInner.prepend(div);
  });
});

