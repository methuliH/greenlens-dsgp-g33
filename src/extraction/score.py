"""Compare a method's CSV with the team's existing manual extraction (reference)."""
import csv, sys, os
from paths import REPORTS, WORK
ROOT = REPORTS
def load(p):
    return {(r['data_year'], r['indicator_code']): r for r in csv.DictReader(open(p, encoding='utf-8-sig'))}
def val(r):
    try: return float(r['value_numeric'])
    except: return None
def score(comp, method, tol=0.02):
    ref = load(os.path.join(ROOT, comp, f'{comp}_indicators_extracted.csv'))
    got = load(os.path.join(WORK, 'results', f'{comp}_{method}.csv'))
    tp = fp = fn = agree_missing = 0; per = {}; mism = []
    for k, r in ref.items():
        g = got.get(k); rv = val(r); gv = val(g) if g else None
        ind = k[1]; per.setdefault(ind, [0, 0, 0])
        ref_has = r['disclosure_status'] == 'reported' and rv is not None
        if gv is not None:
            if ref_has and abs(gv - rv) <= tol * max(abs(rv), 1):
                tp += 1; per[ind][0] += 1
            else:
                fp += 1; per[ind][1] += 1; mism.append((k, rv, gv, r['disclosure_status']))
        elif ref_has:
            fn += 1; per[ind][2] += 1
        else:
            agree_missing += 1
    p = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * p * rc / (p + rc) if p + rc else 0
    print(f'{comp} {method}: values given={tp+fp} correct={tp} wrong={fp} missed={fn} | precision={p:.0%} recall={rc:.0%} F1={f1:.0%}')
    for ind, (a, b, c) in per.items(): print(f'   {ind:10s} correct {a:2d} wrong {b:2d} missed {c:2d}')
    return mism
if __name__ == '__main__':
    comp, method = sys.argv[1], sys.argv[2]
    m = score(comp, method)
    if len(sys.argv) > 3:
        for k, rv, gv, st in m: print('   MISMATCH', k, 'ref', rv, st, '| got', gv)
