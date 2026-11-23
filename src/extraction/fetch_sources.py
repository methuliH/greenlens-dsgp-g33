"""Probe (size check) or download the approved source list. Usage: fetch_sources.py probe|download list.json"""
import sys, os, json, re, subprocess
from paths import REPORTS, WORK
ROOT = REPORTS
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'
def head(url):
    r = subprocess.run(['curl', '-sIL', '-m', '25', '-A', UA, url], capture_output=True, text=True).stdout
    codes = re.findall(r'^HTTP/\S+ (\d+)', r, re.M); size = re.findall(r'^content-length:\s*(\d+)', r, re.M | re.I)
    ctype = re.findall(r'^content-type:\s*(\S+)', r, re.M | re.I)
    return (codes[-1] if codes else 'ERR'), (int(size[-1]) if size else None), (ctype[-1] if ctype else '')
def wayback(url): return 'https://web.archive.org/web/2026id_/' + url
def name_for(d):
    ext = '.xlsx' if d['url'].lower().split('?')[0].endswith(('.xlsx', '.xls')) else '.pdf'
    yr = d.get('report_year') or (max(d['years_covered']) if d.get('years_covered') else 'undated')
    return f"{d['company']}_{yr}_{d.get('doc_type','report')}_{d.get('language','EN')}_new{ext}"
mode, path = sys.argv[1], sys.argv[2]
docs = json.load(open(path, encoding='utf-8'))
out = []
for d in docs:
    code, size, ctype = head(d['url']); used = d['url']
    if code != '200' or 'html' in ctype:
        c2, s2, t2 = head(wayback(d['url']))
        if c2 == '200' and 'html' not in t2: code, size, ctype, used = c2, s2, t2, wayback(d['url'])
    d.update(status=code, size_mb=round(size / 1e6, 1) if size else None, ctype=ctype, fetch_url=used, file=name_for(d))
    if mode == 'download' and d.get('approved', True) and code == '200' and 'html' not in ctype:
        dest = os.path.join(ROOT, d['company'], d['file'])
        if not os.path.exists(dest):
            subprocess.run(['curl', '-sL', '-m', '170', '-A', UA, '-o', dest, used])
            d['downloaded'] = os.path.exists(dest) and os.path.getsize(dest) > 10000
    out.append(d)
    print(f"{d['company']:18s} {code} {str(d['size_mb'])+' MB':9s} {d['file']}  <- {used[:90]}", flush=True)
json.dump(out, open(path.replace('.json', f'_{mode}.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
