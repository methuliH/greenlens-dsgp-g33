"""Step 1: cache the text of every PDF page as JSON lines (one file per report)."""
import sys, os, json, re, warnings
warnings.filterwarnings('ignore')
import pymupdf

from paths import REPORTS, WORK
ROOT = REPORTS
CACHE = os.path.join(WORK, 'cache')
# duplicates and documents that are not annual/sustainability reports
SKIP = re.compile(r'\(\d\)\.pdf$|press|agm|vote|speech|iso[_ ]?\d|certific|charter|conference|webinar|notice|declaration|'
                  r'credit[_ ]opinion|safety-information|supplier|brochure|award|ecovadis|gold[_ ]medal|presentation|results-of', re.I)

def report_year(name):
    m = re.search(r'(?<!\d)(20[0-2]\d)(?!\d)', name)
    return int(m.group(1)) if m else None

def main(companies):
    for comp in companies:
        folder = os.path.join(ROOT, comp)
        out_dir = os.path.join(CACHE, comp)
        os.makedirs(out_dir, exist_ok=True)
        for fn in sorted(os.listdir(folder)):
            if fn.lower().endswith('.xlsx'):
                out = os.path.join(out_dir, fn[:-5] + '.jsonl')
                if os.path.exists(out): continue
                import openpyxl
                wb = openpyxl.load_workbook(os.path.join(folder, fn), read_only=True, data_only=True)
                with open(out, 'w', encoding='utf-8') as f:
                    for i, ws in enumerate(wb.worksheets, start=1):
                        lines = [' | '.join(str(c) for c in row if c is not None) for row in ws.iter_rows(values_only=True)]
                        f.write(json.dumps({'page': i, 'text': ws.title + '\n' + '\n'.join(l for l in lines if l)}, ensure_ascii=False) + '\n')
                print(comp, fn, 'xlsx', flush=True); continue
            if not fn.lower().endswith('.pdf'):
                continue
            out = os.path.join(out_dir, fn[:-4] + '.jsonl')
            if os.path.exists(out) or SKIP.search(fn):
                continue
            try:
                doc = pymupdf.open(os.path.join(folder, fn))
            except Exception as e:
                print('FAIL', comp, fn, e); continue
            tmp = out + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                for i, page in enumerate(doc, start=1):
                    f.write(json.dumps({'page': i, 'text': page.get_text('text')}, ensure_ascii=False) + '\n')
            os.replace(tmp, out)
            print(comp, fn, len(doc), 'pages', flush=True)

if __name__ == '__main__':
    main(sys.argv[1:])
