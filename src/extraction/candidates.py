"""Step 2: find candidate pages and lines for each indicator in each report."""
import sys, os, json, re
from paths import REPORTS, WORK
ROOT = REPORTS
CACHE = os.path.join(WORK, 'cache')
OUT = os.path.join(WORK, 'candidates')

KEYWORDS = {
    'GHG_S1': [r'scope\s*1\b', r'direct (ghg|greenhouse|co2|emissions)', r'emissioni dirette', r'305-1', r'\bE1-6\b', r'direkte'],
    'GHG_S2': [r'scope\s*2\b', r'indirect (ghg|greenhouse|co2|energy)', r'emissioni indirette', r'location[- ]based', r'market[- ]based', r'305-2'],
    'GHG_S3': [r'scope\s*3\b', r'other indirect', r'305-3'],
    'EN_TOT': [r'total energy consum', r'energy consum', r'consum[io] (di )?energ', r'consumi energetici', r'302-1', r'\bE1-5\b', r'energy use'],
    'EN_ELEC': [r'electricity consum', r'electricity (purchased|used|consumed)', r'purchased electricity', r'energia elettrica', r'stromverbrauch'],
    'WA_CONS': [r'water consum', r'water withdraw', r'water abstract', r'withdrawn water', r'prelievi idrici', r'consumi idrici', r'303-[35]', r'\bE3-4\b'],
    'E-WST-GEN': [r'total waste', r'waste generat', r'waste produced', r'rifiuti prodotti', r'rifiuti', r'306-[23]', r'\bE5-5\b', r'\bwaste\b'],
}
NUM = re.compile(r'\d[\d.,\s]{2,}\d')

def load(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(l) for l in f]

def norm(s):
    return re.sub(r'\s+', ' ', s).strip()

def run(comp, top=3, max_lines=22):
    os.makedirs(OUT, exist_ok=True)
    result = {}
    txt_out = []
    for fn in sorted(os.listdir(os.path.join(CACHE, comp))):
        pages = load(os.path.join(CACHE, comp, fn))
        rep = fn[:-6]
        result[rep] = {}
        txt_out.append(f'\n######## {rep} ({len(pages)} pages)')
        for ind, pats in KEYWORDS.items():
            rx = re.compile('|'.join(pats), re.I)
            scored = []
            for p in pages:
                lines = p['text'].splitlines()
                hits = [i for i, l in enumerate(lines) if rx.search(l)]
                if not hits:
                    continue
                nums = sum(1 for i in hits for l in lines[i:i+4] if NUM.search(l))
                scored.append((len(hits) * 2 + nums, p['page'], lines, hits))
            scored.sort(key=lambda x: -x[0])
            result[rep][ind] = []
            txt_out.append(f'== {ind}')
            for score, pg, lines, hits in scored[:top]:
                keep, seen = [], set()
                for i in hits:
                    for j in range(i, min(i + 4, len(lines))):
                        if j not in seen and norm(lines[j]):
                            seen.add(j); keep.append(norm(lines[j]))
                keep = keep[:max_lines]
                result[rep][ind].append({'page': pg, 'score': score, 'lines': keep})
                txt_out.append(f'-- p{pg}: ' + ' | '.join(keep))
    json.dump(result, open(os.path.join(OUT, comp + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    open(os.path.join(OUT, comp + '.txt'), 'w', encoding='utf-8').write('\n'.join(txt_out))
    print(comp, 'done', sum(len(v) for v in result.values()))

if __name__ == '__main__':
    for c in sys.argv[1:]:
        run(c)
