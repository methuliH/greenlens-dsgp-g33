"""Builds the reading pack for the in-chat LLM step: table-like lines from each report's candidate pages."""
import sys, os, json, re
from paths import REPORTS, WORK
ROOT = REPORTS
CACHE = os.path.join(WORK, 'cache'); CAND = os.path.join(WORK, 'candidates')
OUT = os.path.join(WORK, 'reading_packs')
STRONG = re.compile(r'scope\s*[123]|co2|ghg|greenhouse|energy consum|consumi|electricity|water|idric|waste|rifiuti|emission|emissioni|mwh|gwh|twh|\bgj\b|\btj\b|m3|m³|tonnes|\bt\b', re.I)
def main(comp, per_ind=1, cap=1800):
    os.makedirs(OUT, exist_ok=True)
    cand = json.load(open(os.path.join(CAND, comp + '.json'), encoding='utf-8'))
    out = []
    for rep, inds in cand.items():
        pages = {json.loads(l)['page']: json.loads(l)['text'] for l in open(os.path.join(CACHE, comp, rep + '.jsonl'), encoding='utf-8')}
        chosen = []
        for ind, lst in inds.items():
            for c in lst[:per_ind]:
                if c['page'] not in chosen: chosen.append(c['page'])
        out.append(f'\n######## {rep}')
        for pg in sorted(chosen):
            lines = [re.sub(r'\s+', ' ', l).strip() for l in pages[pg].splitlines()]
            keep = [l for l in lines if l and (len(l) < 70 or STRONG.search(l)) and (re.search(r'\d', l) or STRONG.search(l))]
            txt = ' | '.join(keep)
            if not re.search(r'\d{2,}', txt): continue
            out.append(f'-- p{pg}: ' + txt[:cap])
    open(os.path.join(OUT, comp + '.txt'), 'w', encoding='utf-8').write('\n'.join(out))
    print(comp, sum(len(x) for x in out))
for c in sys.argv[1:]: main(c)
