"""Second pass: for each company-year, fetch pages ranked 2-4 for indicator groups that are still mostly unclear."""
import sys, os, json, re, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_packs as bp
ps = bp.ps
GROUP_OF = {'GHG_S1': 'GHG', 'GHG_S2': 'GHG', 'GHG_S2_MB': 'GHG', 'GHG_S3': 'GHG', 'EN_TOT': 'ENERGY', 'EN_ELEC': 'ENERGY',
            'EN_REN_PCT': 'ENERGY', 'WA_WD': 'WATER', 'WA_CONS': 'WATER', 'E-WST-GEN': 'WASTE', 'E-WST-HAZ': 'WASTE',
            'S-EMP': 'SOCIAL', 'S-WOMEN-PCT': 'SOCIAL', 'S-LTIFR': 'SAFETY', 'S-FATAL': 'SAFETY', 'G-BOARD-SIZE': 'GOV',
            'G-BOARD-IND-PCT': 'GOV', 'G-BOARD-WOMEN-PCT': 'GOV', 'FIN_REV': 'FIN'}
def missing_groups(csv_path):
    tally = collections.defaultdict(lambda: [0, 0])
    for r in csv.DictReader(open(csv_path, encoding='utf-8-sig')):
        g = GROUP_OF.get(r['indicator_code'])
        if not g: continue
        k = (r['data_year'], g); tally[k][1] += 1
        tally[k][0] += r['disclosure_status'] != 'reported'
    out = collections.defaultdict(list)
    for (y, g), (miss, n) in tally.items():
        if miss / n >= 0.5: out[y].append(g)
    return out
def build(comp, csv_path, ranks=(2, 3, 4), cap=2200, window=35):
    need = missing_groups(csv_path)
    files = sorted(f for f in os.listdir(os.path.join(bp.CACHE, comp)) if f.endswith('.jsonl'))
    by_year = collections.defaultdict(list)
    for f in files:
        m = bp.YEAR.search(f); by_year[str(int(m.group(1))) if m else 'unknown'].append(f)
    out = []
    for y, groups in sorted(need.items()):
        fl = by_year.get(y) or (by_year.get('unknown') if y == '2022' and comp == 'Stellantis' else None)
        if not fl: continue
        pages = []
        for f in fl:
            for l in open(os.path.join(bp.CACHE, comp, f), encoding='utf-8'):
                p = json.loads(l); pages.append((f[:-6], p['page'], p['text']))
        yy = int(y) if y.isdigit() else None
        sc = [(d, pg, ps.page_scores(t, yy), t) for d, pg, t in pages]
        out.append(f'\n######## {comp} | year {y} | follow-up for: {",".join(sorted(groups))}')
        seen = set()
        for g in sorted(groups):
            ranked = sorted(sc, key=lambda x: -x[2].get(g, 0))
            for rk in ranks:
                if rk - 1 >= len(ranked) or ranked[rk - 1][2].get(g, 0) <= 0: continue
                d, pg, s, t = ranked[rk - 1]
                if (d, pg) in seen: continue
                seen.add((d, pg))
                txt = ' | '.join(ps.table_lines(t, window, [g]))[:cap]
                if txt: out.append(f'-- {d} p{pg} [{g}]: {txt}')
    os.makedirs(os.path.join(bp.WORK, 'packs19_fu'), exist_ok=True)
    path = os.path.join(bp.WORK, 'packs19_fu', comp + '.txt')
    open(path, 'w', encoding='utf-8').write('\n'.join(out))
    return os.path.getsize(path)
if __name__ == '__main__':
    comp, csv_path = sys.argv[1], sys.argv[2]
    print(comp, round(build(comp, csv_path) / 1024), 'KB')
