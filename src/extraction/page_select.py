"""Smarter page selection for the LLM step: score pages as data tables, keep only table-like lines."""
import sys, os, json, re
from paths import REPORTS, WORK
ROOT = REPORTS
CACHE = os.path.join(WORK, 'cache')
GROUPS = {
    'GHG':   (r'scope\s*[123]\b|direct (ghg|greenhouse|co2)|emissioni (dirette|indirette|di co2|di gas serra)|gas (a effetto )?serra|ghg emissions|greenhouse gas emissions|305-[123]|E1-6',
              r't\s*co2|tco2|co2\s*e|co2eq|kt|mt\b'),
    'ENERGY':(r'energy consum|consumi energetici|consumo (di )?energ|energia consumata|consumi di energia|own energy|electricity consum|purchased electricity|302-1|E1-5|energia elettrica',
              r'\bmwh\b|\bgwh\b|\btwh\b|\bgj\b|\btj\b|\bpj\b|\btep\b|\btoe\b'),
    'WATER': (r'water (withdraw|consum|abstract)|withdrawn|prelievi idrici|consumi idrici|acqua prelevata|prelievo (di )?acqua|303-[345]|E3-4',
              r'm3|m³|megalit|\bml\b|cubic'),
    'WASTE': (r'(total|hazardous|non-hazardous) waste|waste (generated|produced|quantities)|rifiuti (prodotti|pericolosi|non pericolosi|totali|speciali)|306-[2345]|E5-5',
              r'\bt\b|tonnes|tons'),
}
BIGNUM = re.compile(r'\d{1,3}(?:[.,  ]\d{3})+(?:[.,]\d+)?|\d+[.,]\d+')
GRI_IDX = re.compile(r'(GRI\s*\d{3}|G4-[A-Z]{2}\d+|\b30\d-\d\b)')
def page_scores(text, year):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    low = text.lower()
    nums = len(BIGNUM.findall(text))
    yr = len(re.findall(rf'\b{year}\b|\b{str(year-1)[2:]}/{str(year)[2:]}\b|\b{year-1}/{str(year)[2:]}\b', text)) if year else 0
    gri = len(GRI_IDX.findall(text))
    prose = sum(1 for l in lines if len(l) > 80)
    out = {}
    for g, (lab, unit) in GROUPS.items():
        lh = len(re.findall(lab, low)); uh = len(re.findall(unit, low))
        if lh == 0: out[g] = 0; continue
        out[g] = lh * 3 + min(uh, 15) + min(nums, 40) * 0.5 + min(yr, 5) * 2 - (gri * 1.5 if gri > 6 else 0) - prose * 0.3
    return out
def table_lines(text, window, groups):
    lines = [re.sub(r'\s+', ' ', l).strip() for l in text.splitlines()]
    lines = [l for l in lines if l]
    labs = re.compile('|'.join(GROUPS[g][0] for g in groups), re.I)
    hits = [i for i, l in enumerate(lines) if labs.search(l)]
    keep = set()
    for i in hits:
        keep.update(range(max(0, i - 3), min(len(lines), i + window)))
    out = []
    for i in sorted(keep):
        l = lines[i]
        if len(l) > 90 and not BIGNUM.search(l): continue      # prose sentence without data
        if not re.search(r'\d', l) and len(l) > 60: continue
        out.append(l)
    return out
def build(comp, top=2, window=25, cap=3000, tag='v2'):
    outdir = os.path.join(WORK, 'reading_packs_' + tag); os.makedirs(outdir, exist_ok=True)
    res = []
    for fn in sorted(os.listdir(os.path.join(CACHE, comp))):
        pages = [json.loads(l) for l in open(os.path.join(CACHE, comp, fn), encoding='utf-8')]
        m = re.search(r'(?<!\d)(20[0-2]\d)(?!\d)', fn); year = int(m.group(1)) if m else None
        sc = [(p['page'], page_scores(p['text'], year), p['text']) for p in pages]
        chosen = {}
        for g in GROUPS:
            best = sorted(sc, key=lambda x: -x[1][g])[:top]
            for pg, s, t in best:
                if s[g] > 0: chosen.setdefault(pg, (t, []))[1].append(g)
        res.append(f'\n######## {fn[:-6]}')
        for pg in sorted(chosen):
            t, gs = chosen[pg]
            txt = ' | '.join(table_lines(t, window, gs))[:cap]
            if txt: res.append(f'-- p{pg} [{",".join(gs)}]: {txt}')
    open(os.path.join(outdir, comp + '.txt'), 'w', encoding='utf-8').write('\n'.join(res))
if __name__ == '__main__':
    comp = sys.argv[1]; top, window, cap, tag = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    build(comp, top, window, cap, tag)


def followup(comp, report, groups, ranks=(2, 3), window=40, cap=5000):
    """Second pass: next-best pages, only for the indicator groups still missing in one report."""
    fn = report + '.jsonl'
    pages = [json.loads(l) for l in open(os.path.join(CACHE, comp, fn), encoding='utf-8')]
    m = re.search(r'(?<!\d)(20[0-2]\d)(?!\d)', fn); year = int(m.group(1)) if m else None
    sc = [(p['page'], page_scores(p['text'], year), p['text']) for p in pages]
    out = [f'######## {report} (follow-up: {",".join(groups)})']
    for g in groups:
        best = sorted(sc, key=lambda x: -x[1][g])
        for r in ranks:
            if r - 1 < len(best) and best[r - 1][1][g] > 0:
                pg, s, t = best[r - 1]
                out.append(f'-- p{pg} [{g}]: ' + ' | '.join(table_lines(t, window, [g]))[:cap])
    return '\n'.join(out)
