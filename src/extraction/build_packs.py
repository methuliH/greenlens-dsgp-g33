"""Company-year reading packs for the 19-indicator LLM extraction (all documents of a year pooled)."""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import page_select as ps
ROOT = ps.ROOT; WORK = ps.WORK; CACHE = ps.CACHE
EXTRA = {
    'SOCIAL': (r'total (number of )?employees|headcount|workforce|number of employees|women in (the )?workforce|female employees|dipendenti|% women|share of women|gender',
               r'\d'),
    'SAFETY': (r'lost[- ]time injur|ltifr|ltir|lost time accident|injury frequency|fatalit|frequency rate|infortuni|work-related injur',
               r'\d'),
    'GOV':    (r'board of directors|supervisory board|independent (directors|members)|board members|board diversity|women on the board|consiglio di amministrazione|independence',
               r'\d'),
    'FIN':    (r'revenue|net sales|turnover|ricavi|umsatz|sales revenue',
               r'(eur|€|million|billion|bn|m\b)'),
}
ps.GROUPS.update(EXTRA)
YEAR = re.compile(r'(?<!\d)(20[0-2]\d)(?!\d)')

def build(comp, cap=2500, window=35):
    out = []
    files = sorted(f for f in os.listdir(os.path.join(CACHE, comp)) if f.endswith('.jsonl'))
    by_year = {}
    for f in files:
        m = YEAR.search(f)
        by_year.setdefault(int(m.group(1)) if m else 0, []).append(f)
    for y in sorted(by_year):
        pages = []
        for f in by_year[y]:
            for l in open(os.path.join(CACHE, comp, f), encoding='utf-8'):
                p = json.loads(l); pages.append((f[:-6], p['page'], p['text']))
        sc = [(doc, pg, ps.page_scores(t, y or None), t) for doc, pg, t in pages]
        chosen = {}
        for g in ps.GROUPS:
            best = max(sc, key=lambda x: x[2].get(g, 0))
            if best[2].get(g, 0) > 0:
                chosen.setdefault((best[0], best[1]), (best[3], []))[1].append(g)
        out.append(f'\n######## {comp} | year {y or "unknown"} | documents: {"; ".join(d[:-6] for d in by_year[y])}')
        for (doc, pg) in sorted(chosen):
            t, gs = chosen[(doc, pg)]
            txt = ' | '.join(ps.table_lines(t, window, gs))[:cap]
            if txt: out.append(f'-- {doc} p{pg} [{",".join(gs)}]: {txt}')
    os.makedirs(os.path.join(WORK, 'packs19'), exist_ok=True)
    path = os.path.join(WORK, 'packs19', comp + '.txt')
    open(path, 'w', encoding='utf-8').write('\n'.join(out))
    return os.path.getsize(path), len(by_year)

if __name__ == '__main__':
    tot = 0
    for c in sys.argv[1:]:
        s, n = build(c); tot += s
        print(f'{c}: {n} years, {s/1024:.0f} KB')
    print(f'TOTAL {tot/1024:.0f} KB ~ {tot/4/1000:.0f}k tokens')
