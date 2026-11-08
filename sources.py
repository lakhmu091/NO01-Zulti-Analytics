import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

HEADERS = {"User-Agent": "NO01-Analytics/1.0 (public results research; contact: configure-your-own)"}

def fetch_public_page(url, timeout=20):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Enter a valid http(s) URL.")
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    if len(response.content) > 8_000_000:
        raise ValueError("Page too large for this starter collector.")
    soup = BeautifulSoup(response.text, "html.parser")
    return response.text, soup.get_text(" ", strip=True)

def extract_candidate_draws(html, selector=None, max_number=45, draw_size=6):
    soup = BeautifulSoup(html, "html.parser")
    nodes = soup.select(selector) if selector else [soup]
    candidates, seen = [], set()
    for node in nodes:
        text = node.get_text(" ", strip=True)
        # Candidate extraction only: numbers must be reviewed before import.
        for match in re.finditer(r"(?<!\d)((?:\d{1,2}\s+){%d}\d{1,2})(?!\d)" % (draw_size - 1), text):
            nums = [int(x) for x in re.findall(r"\d{1,2}", match.group(1))]
            if len(nums) == draw_size and len(set(nums)) == draw_size and min(nums) >= 1 and max(nums) <= max_number:
                key = tuple(sorted(nums))
                if key not in seen:
                    seen.add(key)
                    candidates.append({"draw_date": "", "draw_id": "", "source": "public-page-review-required", "numbers": list(key)})
    return candidates[:200]
