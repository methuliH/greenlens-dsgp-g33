"""Method A: rule-based extraction (keywords + number + unit patterns). No AI involved."""
import sys, os, json, re, csv
from paths import REPORTS, WORK
ROOT = REPORTS
CAND = os.path.join(WORK, 'candidates')
OUT = os.path.join(WORK, 'results')

LABEL = {
    'GHG_S1': r'scope\s*1\b|direct (ghg|greenhouse gas|co2) emissions|emissioni dirette',
    'GHG_S2': r'scope\s*2\b|indirect energy|emissioni indirette',
    'GHG_S3': r'scope\s*3\b',
    'EN_TOT': r'total energy consumption|energy consumption|consumi energetici|consumo (totale )?di energia',
    'EN_ELEC': r'electricity consumption|electricity consumed|purchased electricity|consumi di energia elettrica',
    'WA_CONS': r'water consumption|water withdrawal|total water|prelievi idrici|consumi idrici',
    'E-WST-GEN': r'total waste|waste generated|waste produced|rifiuti prodotti|totale rifiuti',
}
UNITS = [  # (regex, unit, factor to target unit)
    (r'\bmt\s*co2|million (tonnes|t)\b|mio\.? t\b|\bmtco2', 'MtCO2e', 1e6),
    (r'\bkt\s*co2|thousand (tonnes|t)\b|\b(kt|1,000 t|1\.000 t|000 t)\b', 'ktCO2e', 1e3),
    (r't\s*co2|tco2|tonnes? co2|tons? co2|\bt\b', 'tCO2e', 1),
]
ENERGY_UNITS = [(r'\btwh\b', 3.6e6), (r'\bgwh\b', 3.6e3), (r'\bmwh\b', 3.6), (r'\bkwh\b', 0.0036),
                (r'\bpj\b', 1e6), (r'\btj\b', 1e3), (r'\bgj\b', 1), (r'\btoe\b', 41.868)]
WATER_UNITS = [(r'\bmillion m3|\bmm3|\bmio\.? m3|hm3', 1e6), (r'megalit|\bml\b', 1e3), (r'thousand m3|1,000 m3|\'000 m3', 1e3), (r'm3|m³|cubic', 1)]
NUM = re.compile(r'(?<![\w.,])(\d{1,3}(?:[ .,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)(?![\w])')

def parse_num(s):
    s = s.strip()
    if re.fullmatch(r'\d{1,3}([ .,]\d{3})+', s):
        return float(re.sub(r'[ .,]', '', s))
    m = re.fullmatch(r'(\d{1,3}(?:([ .,])\d{3})+)([.,])(\d+)', s)
    if m and m.group(2) != m.group(3):
        return float(re.sub(r'[ .,]', '', m.group(1)) + '.' + m.group(4))
    return float(s.replace(',', '.')) if s.count(',') + s.count('.') <= 1 else None

def plausible(v, s):
    if v is None or v < 10: return False
    if 1990 <= v <= 2035 and re.fullmatch(r'\d{4}', s): return False
    return True

def pick(ind, lines, year):
    rx = re.compile(LABEL[ind], re.I)
    for i, l in enumerate(lines):
        if not rx.search(l):
            continue
        window = ' '.join(lines[i:i + 4])
        for m in NUM.finditer(window[rx.search(window).end():]):
            v = parse_num(m.group(1))
            if plausible(v, m.group(1)):
                return v, m.group(1), window[:300]
    return None

def convert(ind, v, ctx):
    c = ctx.lower()
    if ind.startswith('GHG'):
        for rx, u, f in UNITS:
            if re.search(rx, c): return v * f, 'tCO2e', u
        return v, 'tCO2e', 'assumed t'
    if ind == 'EN_TOT':
        for rx, f in ENERGY_UNITS:
            if re.search(rx, c): return v * f, 'GJ', rx.strip('\\b')
        return v, 'GJ', 'assumed GJ'
    if ind == 'EN_ELEC':
        for rx, f in ENERGY_UNITS:
            if re.search(rx, c): return v * f / 0.0036, 'kWh', rx.strip('\\b')
        return v, 'kWh', 'assumed kWh'
    if ind == 'WA_CONS':
        for rx, f in WATER_UNITS:
            if re.search(rx, c): return v * f, 'm3', rx
        return v, 'm3', 'assumed m3'
    if 'thousand' in c or re.search(r'\bkt\b', c): return v * 1e3, 'MT', 'kt'
    return v, 'MT', 't'

FIELDS = ['company', 'data_year', 'indicator_code', 'disclosure_status', 'value_numeric', 'unit', 'source_value_text',
          'source_unit', 'measurement_basis', 'boundary', 'pdf_page', 'source_file', 'source_url', 'source_excerpt',
          'verification_status', 'needs_review', 'extraction_method', 'note']

def run(comp):
    os.makedirs(OUT, exist_ok=True)
    cand = json.load(open(os.path.join(CAND, comp + '.json'), encoding='utf-8'))
    rows = []
    for rep, inds in cand.items():
        ym = re.search(r'(?<!\d)(20[0-2]\d)(?!\d)', rep); year = int(ym.group(1)) if ym else ''
        for ind in LABEL:
            hit = None
            for c in inds.get(ind, []):
                r = pick(ind, c['lines'], year)
                if r: hit = (c['page'], *r); break
            base = dict(company=comp, data_year=year, indicator_code=ind, source_file=rep + '.pdf',
                        verification_status='Rule-based, not human-checked', needs_review=1, extraction_method='rule_based',
                        measurement_basis='', boundary='', source_url='')
            if hit:
                pg, v, raw, ctx = hit
                val, unit, su = convert(ind, v, ctx)
                rows.append({**base, 'disclosure_status': 'reported', 'value_numeric': round(val, 3), 'unit': unit,
                             'source_value_text': raw, 'source_unit': su, 'pdf_page': pg, 'source_excerpt': ctx, 'note': ''})
            else:
                rows.append({**base, 'disclosure_status': 'not_reported', 'value_numeric': '', 'unit': '', 'source_value_text': '',
                             'source_unit': '', 'pdf_page': '', 'source_excerpt': '', 'note': 'No rule match'})
    with open(os.path.join(OUT, f'{comp}_rule_based.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, FIELDS); w.writeheader(); w.writerows(rows)
    print(comp, sum(r['disclosure_status'] == 'reported' for r in rows), '/', len(rows), 'found')

if __name__ == '__main__':
    for c in sys.argv[1:]: run(c)
