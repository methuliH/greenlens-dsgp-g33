"""GreenLens: download all report files listed in download_list_all.json.

Run from src/extraction (set GREENLENS_REPORTS first, see paths.py):
    python download_all.py            (all 238 rows: tries every link)
    python download_all.py Orlen      (only the companies you name)

- Saves each file into  <reports folder>\\<Company>\\<file>
- Skips files that already exist, so you can stop and re-run any time.
- Tries the original link first, then a web.archive.org copy.
- Checks each download is a real PDF or XLSX (not an error page).
- Anything that fails goes into failed_links.csv (company, year, file, url)
  so you can open those in a browser and save them by hand.
Only uses the Python standard library.
"""
import csv, json, os, re, sys, time, urllib.request, urllib.error

from paths import REPORTS as ROOT, SOURCES as HERE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 120          # seconds without data before giving up on one link


def safe(name):
    return re.sub(r'[<>:"/\\|?*]', "", name)


def candidates(row):
    urls = []
    for u in (row.get("url"), row.get("fetch_url")):
        if u and u not in urls:
            urls.append(u)
    orig = row.get("url") or ""
    if orig and "web.archive.org" not in orig:
        wb = "https://web.archive.org/web/2026id_/" + orig
        if wb not in urls:
            urls.append(wb)
    return urls


def looks_ok(path):
    if not os.path.exists(path) or os.path.getsize(path) < 10_000:
        return False
    with open(path, "rb") as f:
        head = f.read(8)
    return head.startswith(b"%PDF") or head.startswith(b"PK")


def fetch(url, dest):
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        got, last = 0, time.time()
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            if time.time() - last > 5:
                pct = f" {got*100//total}%" if total else ""
                print(f"      ... {got/1e6:.0f} MB{pct}", flush=True)
                last = time.time()
    if looks_ok(tmp):
        os.replace(tmp, dest)
        return True
    os.remove(tmp)
    return False


def main():
    rows = json.load(open(os.path.join(HERE, "download_list_all.json"), encoding="utf-8"))
    only = set(sys.argv[1:])
    if only:
        rows = [r for r in rows if r["company"] in only]
    failed, done, skipped = [], 0, 0
    for i, r in enumerate(rows, 1):
        folder = os.path.join(ROOT, r["company"])
        os.makedirs(folder, exist_ok=True)
        dest = os.path.join(folder, safe(r["file"]))
        tag = f"[{i}/{len(rows)}] {r['company']} {r['report_year']} {r['doc_type']}"
        if looks_ok(dest):
            skipped += 1
            continue
        print(tag, flush=True)
        ok = False
        for u in candidates(r):
            try:
                if fetch(u, dest):
                    ok = True
                    print(f"   OK  {os.path.getsize(dest)/1e6:.1f} MB  {safe(r['file'])}")
                    break
                print(f"   not a PDF/XLSX from {u[:80]}")
            except (urllib.error.URLError, OSError, ValueError) as e:
                print(f"   fail ({str(e)[:60]}) {u[:80]}")
        if ok:
            done += 1
        else:
            failed.append(r)
    out = os.path.join(HERE, "failed_links.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["company", "report_year", "doc_type", "save_as", "url"])
        for r in failed:
            w.writerow([r["company"], r["report_year"], r["doc_type"],
                        os.path.join(ROOT, r["company"], safe(r["file"])), r["url"]])
    print(f"\nDownloaded {done}, already had {skipped}, failed {len(failed)}.")
    if failed:
        print(f"Failed links (open in a browser, save with the 'save_as' name): {out}")


if __name__ == "__main__":
    main()
