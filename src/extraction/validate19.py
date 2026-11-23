"""Check helper outputs: schema, units, ranges, year-on-year jumps; then combine into one CSV."""
import csv, glob, os, sys, collections
FIELDS = ['company', 'data_year', 'indicator_code', 'disclosure_status', 'value_numeric', 'unit', 'source_value_text',
          'source_unit', 'measurement_basis', 'boundary', 'pdf_page', 'source_file', 'source_url', 'source_excerpt',
          'verification_status', 'needs_review', 'extraction_method', 'note']
UNIT = {'GHG_S1': 'tCO2e', 'GHG_S2': 'tCO2e', 'GHG_S2_MB': 'tCO2e', 'GHG_S3': 'tCO2e', 'EN_TOT': 'GJ', 'EN_ELEC': 'kWh',
        'EN_REN_PCT': '%', 'WA_WD': 'm3', 'WA_CONS': 'm3', 'E-WST-GEN': 'MT', 'E-WST-HAZ': 'MT', 'S-EMP': 'persons',
        'S-WOMEN-PCT': '%', 'S-LTIFR': 'rate', 'S-FATAL': 'persons', 'G-BOARD-SIZE': 'persons', 'G-BOARD-IND-PCT': '%',
        'G-BOARD-WOMEN-PCT': '%', 'FIN_REV': None}
PCT = {k for k, u in UNIT.items() if u == '%'}
src = sys.argv[1]; out = sys.argv[2]
allrows, report = [], []
for f in sorted(glob.glob(os.path.join(src, '*_llm19.csv'))):
    rows = list(csv.DictReader(open(f, encoding='utf-8-sig')))
    comp = os.path.basename(f)[:-10]
    issues = []
    if not rows or list(rows[0].keys()) != FIELDS:
        issues.append('column layout differs')
    by_year = collections.defaultdict(set)
    for r in rows:
        by_year[r['data_year']].add(r['indicator_code'])
        code = r['indicator_code']
        if code not in UNIT: issues.append(f'unknown code {code}'); continue
        if r['disclosure_status'] == 'reported':
            try: v = float(r['value_numeric'])
            except ValueError: issues.append(f"{r['data_year']} {code} non-numeric"); continue
            if UNIT[code] and r['unit'] != UNIT[code]: issues.append(f"{r['data_year']} {code} unit {r['unit']}")
            if code in PCT and not 0 <= v <= 100: issues.append(f"{r['data_year']} {code} pct {v}")
            if v < 0: issues.append(f"{r['data_year']} {code} negative")
    for y, codes in by_year.items():
        if len(codes) != 19: issues.append(f'{y}: {len(codes)} indicators')
    # year-on-year jumps (x5 or /5) flag for review
    series = collections.defaultdict(dict)
    for r in rows:
        if r['disclosure_status'] == 'reported':
            try: series[r['indicator_code']][int(r['data_year'])] = float(r['value_numeric'])
            except ValueError: pass
    jumps = []
    for code, s in series.items():
        ys = sorted(s)
        for a, b in zip(ys, ys[1:]):
            if s[a] > 0 and s[b] > 0 and (s[b] / s[a] > 5 or s[a] / s[b] > 5) and code not in PCT:
                jumps.append(f'{code} {a}->{b}: {s[a]:,.0f} -> {s[b]:,.0f}')
    for r in rows:
        key = f"{r['indicator_code']} "
        if any(j.startswith(key) and (f"->{r['data_year']}:" in j) for j in jumps):
            r['needs_review'] = '1'
            r['note'] = (r['note'] + ' | ' if r['note'] else '') + 'Year-on-year change over 5x; check unit or boundary.'
    rep = collections.Counter(r['indicator_code'] for r in rows if r['disclosure_status'] == 'reported')
    report.append((comp, len(by_year), len(rows), sum(rep.values()), issues[:6], jumps[:6]))
    allrows += rows
with open(out, 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, FIELDS, extrasaction='ignore'); w.writeheader(); w.writerows(allrows)
for comp, ny, nr, nrep, iss, jm in report:
    print(f'{comp}: {ny} years, {nr} rows, {nrep} reported ({nrep/max(nr,1):.0%})')
    for i in iss: print('   ISSUE', i)
    for j in jm: print('   JUMP ', j)
cov = collections.defaultdict(lambda: [0, 0])
for r in allrows:
    cov[r['indicator_code']][1] += 1
    cov[r['indicator_code']][0] += r['disclosure_status'] == 'reported'
print('\nCoverage by indicator:')
for k in UNIT: print(f'  {k:18s} {cov[k][0]:4d}/{cov[k][1]:4d} = {cov[k][0]/max(cov[k][1],1):.0%}')
