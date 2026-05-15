import argparse
import csv
import logging
import re
import time
from dataclasses import asdict, dataclass
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)
HEADERS = {"User-Agent": "Mozilla/5.0"}
START_YEAR = 2022

FL_MARKETS = [
    "Florida", "Miami", "Tampa", "Orlando", "Jacksonville", "Fort Lauderdale",
    "Boca Raton", "West Palm Beach", "Palm Beach", "St. Petersburg", "Sarasota",
]

STEALTH_TERMS = [
    "emerged from stealth", "comes out of stealth", "came out of stealth",
    "out of stealth", "launched from stealth", "stealth startup",
]

FUNDING_TERMS = [
    "raised", "funding round", "seed round", "series a", "series b", "series c",
    "venture funding", "capital raise", "valuation",
]

TRUSTED_DOMAINS = [
    "businesswire.com", "prnewswire.com", "globenewswire.com", "techcrunch.com",
    "axios.com", "reuters.com", "venturebeat.com", "refreshmiami.com",
]

AMOUNT_RE = re.compile(
    r"(?:US\$|USD\s*)?\$\s?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\s?"
    r"(billion|million|m|bn|b)?\b",
    re.I,
)
YEAR_RE = re.compile(r"\b(20\d{2})\b")
ROUND_RE = re.compile(r"\b(pre-seed|seed|series\s+[a-k]|growth|strategic|venture|debt)\b", re.I)
COMPANY_SPLIT_RE = re.compile(
    r"\s+(?:raises?|raised|lands?|landed|secures?|secured|closes?|closed|announces?|announced|emerges?|emerged|launches?|launched)\b",
    re.I,
)


@dataclass
class FundingRound:
    company_guess: str
    amount_usd_millions: float
    year: int
    round_type: str
    florida_signal: str
    stealth_signal: str
    stealth_confirmed: bool
    source_confidence: str
    source_domain: str
    title: str
    snippet: str
    url: str
    discovery_query: str


def amount_to_millions(text):
    match = AMOUNT_RE.search(text)
    if not match:
        return None
    value = float(match.group(1).replace(",", ""))
    unit = (match.group(2) or "").lower()
    if unit in ["billion", "bn", "b"]:
        return round(value * 1000, 2)
    return round(value, 2)


def extract_year(text, start_year=START_YEAR):
    years = [int(year) for year in YEAR_RE.findall(text)]
    years = [year for year in years if year >= start_year]
    return min(years) if years else None


def source_domain(url):
    return urlparse(url).netloc.lower().replace("www.", "")


def source_confidence(url, text):
    domain = source_domain(url)
    if any(domain.endswith(d) for d in TRUSTED_DOMAINS):
        return "high"
    if "linkedin.com" in domain or "crunchbase.com" in domain or "pitchbook.com" in domain:
        return "medium"
    if "press release" in text.lower() or "announces" in text.lower():
        return "medium"
    return "low"


def detect_terms(text, terms):
    lower = text.lower()
    return "; ".join(term for term in terms if term.lower() in lower)


def detect_florida(text):
    lower = text.lower()
    return "; ".join(market for market in FL_MARKETS if market.lower() in lower)


def round_type(text):
    match = ROUND_RE.search(text)
    return match.group(1).title() if match else "Unknown"


def guess_company(title):
    cleaned = title.strip().split(" | ")[0].split(" - ")[0]
    return COMPANY_SPLIT_RE.split(cleaned, maxsplit=1)[0].strip(" :–—-")[:120]


def build_queries():
    queries = []
    for market in FL_MARKETS:
        queries.extend([
            f'{market} startup raised funding since 2022',
            f'{market} startup "Series A" raised',
            f'{market} startup "Series B" raised',
            f'{market} AI startup raised funding',
            f'{market} fintech startup raised funding',
            f'{market} cybersecurity startup raised funding',
            f'{market} company raised "million" funding',
            f'site:linkedin.com/posts {market} startup raised funding',
            f'site:linkedin.com/posts {market} founder announced funding',
        ])
        for term in STEALTH_TERMS:
            queries.append(f'{market} startup "{term}" raised')
            queries.append(f'site:linkedin.com/posts {market} "{term}" funding')
    queries.extend([
        'site:businesswire.com Florida startup raised funding 2022',
        'site:prnewswire.com Florida startup raised funding 2023',
        'site:globenewswire.com Florida startup raised funding 2024',
        'site:techcrunch.com Miami startup raised funding',
        'site:axios.com Miami startup raised funding',
        'site:refreshmiami.com Miami startup raised funding',
    ])
    return list(dict.fromkeys(queries))


def scrape_duckduckgo(query, pages=4, sleep_seconds=1):
    results = []
    for page in range(pages):
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}&s={page * 30}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=25)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.warning("Search request failed for %r page %s: %s", query, page + 1, exc)
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.select(".result"):
            title_el = item.select_one(".result__a")
            snippet_el = item.select_one(".result__snippet")
            if not title_el:
                continue
            results.append({
                "title": title_el.get_text(" ", strip=True),
                "snippet": snippet_el.get_text(" ", strip=True) if snippet_el else "",
                "url": title_el.get("href", ""),
                "query": query,
            })
        time.sleep(sleep_seconds)
    return results


def parse_result(result, start_year=START_YEAR):
    title = result["title"]
    snippet = result["snippet"]
    url = result["url"]
    query = result["query"]
    text = f"{title} {snippet} {query}"

    amount = amount_to_millions(text)
    year = extract_year(text, start_year)
    florida_signal = detect_florida(text)
    stealth_signal = detect_terms(text, STEALTH_TERMS)

    if amount is None or year is None or not florida_signal:
        return None
    if not detect_terms(text, FUNDING_TERMS):
        return None

    return FundingRound(
        company_guess=guess_company(title),
        amount_usd_millions=amount,
        year=year,
        round_type=round_type(text),
        florida_signal=florida_signal,
        stealth_signal=stealth_signal,
        stealth_confirmed=bool(stealth_signal),
        source_confidence=source_confidence(url, text),
        source_domain=source_domain(url),
        title=title,
        snippet=snippet,
        url=url,
        discovery_query=query,
    )


def dedupe(rows):
    confidence_rank = {"high": 3, "medium": 2, "low": 1}
    best = {}
    for row in rows:
        key = (row.company_guess.lower(), row.amount_usd_millions, row.year)
        score = confidence_rank.get(row.source_confidence, 0) + int(row.stealth_confirmed)
        existing = best.get(key)
        existing_score = -1 if existing is None else confidence_rank.get(existing.source_confidence, 0) + int(existing.stealth_confirmed)
        if score > existing_score:
            best[key] = row
    return sorted(best.values(), key=lambda row: (row.amount_usd_millions, row.year), reverse=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=4)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--start-year", type=int, default=START_YEAR)
    parser.add_argument("--output", default="florida_startup_funding_rounds_top100.csv")
    parser.add_argument("--stealth-only", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    rows = []
    queries = build_queries()
    for idx, query in enumerate(queries, 1):
        LOGGER.info("[%s/%s] %s", idx, len(queries), query)
        for result in scrape_duckduckgo(query, pages=args.pages):
            row = parse_result(result, start_year=args.start_year)
            if row:
                rows.append(row)

    rows = dedupe(rows)
    if args.stealth_only:
        rows = [row for row in rows if row.stealth_confirmed]
    rows = rows[:args.limit]

    fieldnames = list(FundingRound.__dataclass_fields__.keys())
    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    LOGGER.info("Wrote %s rows to %s", len(rows), args.output)


if __name__ == "__main__":
    main()
