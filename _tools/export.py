# Canvas-Artboards (.dc.html) als statisches HTML für GitHub Pages ausgeben.
# Aufruf aus dem Repo: python3 -I _tools/export.py <Ordner mit den .dc.html aus dem Canvas> . _tools/pages.json
# pages-json: {"Main.dc.html": {"path": "", "title": "...", "desc": "..."}, ...}
import re, sys, json, subprocess, os

proj, repo, pages = sys.argv[1], sys.argv[2], json.loads(open(sys.argv[3]).read())
here = os.path.dirname(os.path.abspath(__file__))

def vals(f):
    return json.loads(subprocess.check_output(['node', os.path.join(here, 'vals.mjs'), f, '{}']))

def get(path, scope):
    cur = scope
    for p in path.split('.'):
        cur = cur.get(p) if isinstance(cur, dict) else None
    return cur

def render(text, scope):
    pat = r'<sc-if value="\{\{\s*([\w.]+)\s*\}\}"[^>]*>((?:(?!<sc-if).)*?)</sc-if>'
    while re.search(pat, text, flags=re.S):
        text = re.sub(pat, lambda m: m.group(2) if get(m.group(1), scope) else '', text, flags=re.S)
    return re.sub(r'\{\{\s*([\w.]+)\s*\}\}', lambda m: '' if get(m.group(1), scope) is None else str(get(m.group(1), scope)), text)

def link(frm, to):
    up = '../' * frm.count('/')
    return (up + to) or './'

# Interaktive App-Ansicht: Häkchen per aria-pressed und CSS, ein Blatt, das JS befüllt.
APP_CSS = '''[hidden]{display:none!important}
.check[aria-pressed="true"] .box{background:#c34112}
.check[aria-pressed="false"] .box svg{display:none}
.check[aria-pressed="true"]+.atodo .atext{text-decoration:line-through;color:#3c3c43}'''
APP_JS = '''<script>
(() => {
  const T = %s;
  const box = document.querySelector('.sheetbox'), sheet = box.querySelector('.asheet');
  let from = null;
  const close = () => { box.hidden = true; if (from) from.focus(); };
  document.querySelectorAll('.check').forEach((b) => b.addEventListener('click', () =>
    b.setAttribute('aria-pressed', b.getAttribute('aria-pressed') === 'true' ? 'false' : 'true')));
  document.querySelectorAll('.atodo').forEach((b, i) => b.addEventListener('click', () => {
    const t = T[i];
    sheet.querySelectorAll('[data-f]').forEach((el) => { el.textContent = t[el.dataset.f]; });
    sheet.querySelector('[data-date]').hidden = !t.date;
    from = b;
    box.hidden = false;
    sheet.querySelector('.sclose').focus();
  }));
  sheet.querySelector('.sclose').addEventListener('click', close);
  box.querySelector('.scrim').addEventListener('click', close);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !box.hidden) close(); });
})();
</script>'''

FONTS = '''@font-face{font-family:"Source Serif 4";font-style:normal;font-weight:200 900;font-display:swap;src:url(%sfonts/source-serif-4-normal.woff2) format("woff2")}
@font-face{font-family:"Source Serif 4";font-style:italic;font-weight:200 900;font-display:swap;src:url(%sfonts/source-serif-4-italic.woff2) format("woff2")}'''

for name, meta in pages.items():
    src = open(os.path.join(proj, name)).read()
    lang = re.search(r'<html lang="(\w+)"', src).group(1)
    v = vals(os.path.join(proj, name))
    body = src.split('<x-dc>')[1].split('</x-dc>')[0]
    helmet = body.split('<helmet>')[1].split('</helmet>')[0]
    helmet = re.sub(r'<link rel="(preconnect|stylesheet)"[^>]*fonts\.(googleapis|gstatic)[^>]*>\n?', '', helmet)
    body = body.split('</helmet>')[1]
    script = ''
    if 'todos' in v:
        body = re.sub(r'<sc-if value="\{\{s\.hasDate\}\}"[^>]*>\s*<div class="srow">(.*?)</div>\s*</sc-if>',
                      r'<div class="srow" data-date>\1</div>', body, flags=re.S)
        body = re.sub(r'<sc-if value="\{\{t\.done\}\}"[^>]*>(.*?)</sc-if>', r'\1', body, flags=re.S)
        body = re.sub(r'<sc-if value="\{\{sheetOpen\}\}"[^>]*>(.*?)</sc-if>', r'<div class="sheetbox" hidden>\1</div>', body, flags=re.S)
        body = re.sub(r'\{\{s\.(\w+)\}\}', r'<span data-f="\1"></span>', body)
        body = re.sub(r'\s*style="\{\{t\.(box|text)Style\}\}"', '', body)
        helmet = helmet.replace('</style>', APP_CSS + '\n</style>')
        keys = ('what', 'who', 'date', 'quote', 'at')
        script = APP_JS % json.dumps([{k: t[k] for k in keys} for t in v['todos']], ensure_ascii=False)
    body = re.sub(r'<sc-for list="\{\{(\w+)\}\}" as="(\w+)"[^>]*>(.*?)</sc-for>',
                  lambda m: ''.join(render(m.group(3), {**v, m.group(2): d}) for d in v[m.group(1)]), body, flags=re.S)
    body = render(body, v)
    body = re.sub(r'\sonClick="[^"]*"', '', body)
    body = re.sub(r'href="([\w-]+\.dc\.html)"', lambda m: 'href="%s"' % link(meta['path'], pages[m.group(1)]['path']), body)
    assert '{{' not in body and 'sc-' not in body and '.dc.html' not in body, name
    pre = '../' * meta['path'].count('/')
    out = f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{meta["title"]}</title>
<meta name="description" content="{meta["desc"]}">
<link rel="icon" href="{pre}img/icon.png">
<style>
{FONTS % (pre, pre)}
</style>
{helmet.strip()}
</head>
<body>
{body.strip()}
{script}
</body>
</html>
'''
    dest = os.path.join(repo, meta['path'], 'index.html')
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, 'w').write(out)
    print(dest)
