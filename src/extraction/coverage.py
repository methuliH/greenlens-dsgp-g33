"""Check how often the reference value's text appears in a reading pack (i.e. whether the LLM could see it)."""
import csv, os, re, sys
from paths import REPORTS, WORK
ROOT = REPORTS
def packs(path):
    txt = open(path, encoding='utf-8').read()
    parts = re.split(r'\n######## ', txt)
    out = {}
    for p in parts[1:]:
        name, _, body = p.partition('\n')
        y = re.search(r'(?<!\d)(20[0-2]\d)(?!\d)', name)
        out.setdefault(y.group(1) if y else name, '')
        out[y.group(1) if y else name] += body
    return out
def digits(s): return re.sub(r'\D', '', s)
def run(comp, pack):
    ref = list(csv.DictReader(open(os.path.join(ROOT, comp, f'{comp}_indicators_extracted.csv'), encoding='utf-8-sig')))
    pk = packs(pack); size = os.path.getsize(pack)
    hit = tot = 0; miss = []
    for r in ref:
        if r['disclosure_status'] != 'reported' or not r['source_value_text'].strip(): continue
        parts = [digits(x) for x in r['source_value_text'].split('+') if len(digits(x)) >= 3]
        if not parts: continue
        tot += 1
        body = digits(pk.get(r['data_year'], ''))
        if all(d in body for d in parts): hit += 1
        else: miss.append((r['data_year'], r['indicator_code'], r['source_value_text'], r['pdf_page']))
    print(f'{comp} {os.path.basename(os.path.dirname(pack))}: {size/1024:.0f} KB, {size/len(pk)/1024:.1f} KB/report, value visible {hit}/{tot} = {hit/tot:.0%}')
    if len(sys.argv) > 3:
        for m in miss: print('   miss', m)
if __name__ == '__main__': run(sys.argv[1], sys.argv[2])
