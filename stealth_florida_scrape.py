import re
import csv
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

HEADERS = {"User-Agent": "Mozilla/5.0"}

QUERIES = [
    'Florida startup emerged from stealth raised',
    'Florida company comes out of stealth funding round',
    'Miami startup emerged from stealth raised',
    'Tampa startup emerged from stealth raised',
    'Orlando startup emerged from stealth raised',
    'Jacksonville startup emerged from stealth raised',
]

AMOUNT_RE = re.compile(r'\$\s?([0-9]+(?:\.[0-9]+)?)\s?(billion|million|m|bn|b)?', re.I)
YEAR_RE = re.compile(r'\b(202[2-6])\b')
FL_WORDS = ['florida', 'miami', 'tampa', 'orlando', 'jacksonville', 'boca raton', 'fort lauderdale', 'palm beach', 'st. petersburg']
STEALTH_WORDS = ['stealth', 'emerged from stealth', 'out of stealth', 'comes out of stealth']


def amount_to_millions(text):
    m = AMOUNT_RE.search(text)
    if not m:
        return None
    val = float(m.group(1))
    unit = (m.group(2) or '').lower()
    if unit in ['billion', 'bn', 'b']:
        return val * 1000
    return val


def scrape_duckduckgo(query, pages=10):
    rows = []
    for p in range(pages):
        s = p * 30
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}&s={s}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, 'html.parser')
            for res in soup.select('.result'):
                title_el = res.select_one('.result__a')
                snippet_el = res.select_one('.result__snippet')
                if not title_el:
                    continue
                title = title_el.get_text(' ', strip=True)
                href = title_el.get('href', '')
                snippet = snippet_el.get_text(' ', strip=True) if snippet_el else ''
                text = f"{title} {snippet}".lower()
                if not any(w in text for w in STEALTH_WORDS):
                    continue
                if not any(w in text for w in FL_WORDS):
                    continue
                yr = YEAR_RE.search(text)
                if not yr:
                    continue
                amt = amount_to_millions(f"{title} {snippet}")
                if amt is None:
                    continue
                company = title.split(' raised ')[0].split(' emerges')[0].split(' emerges')[0].strip()
                rows.append({
                    'company_guess': company,
                    'amount_usd_millions': round(amt, 2),
                    'year': int(yr.group(1)),
                    'query': query,
                    'title': title,
                    'snippet': snippet,
                    'url': href,
                })
        except Exception:
            pass
        time.sleep(1)
    return rows


def dedupe(rows):
    out = []
    seen = set()
    for r in sorted(rows, key=lambda x: x['amount_usd_millions'], reverse=True):
        key = (r['company_guess'].lower(), r['amount_usd_millions'], r['year'])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def main():
    all_rows = []
    for q in QUERIES:
        all_rows.extend(scrape_duckduckgo(q, pages=8))
    rows = [r for r in all_rows if r['year'] >= 2022]
    rows = dedupe(rows)
    rows = sorted(rows, key=lambda x: x['amount_usd_millions'], reverse=True)[:100]

    with open('florida_stealth_rounds_top100.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            'company_guess','amount_usd_millions','year','query','title','snippet','url'])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to florida_stealth_rounds_top100.csv")


if __name__ == '__main__':
    main()
