"""Fetch source snapshots for a personal 2026 CTF calendar (standard library only)."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'sources'
SOURCES.mkdir(parents=True, exist_ok=True)

def fetch(url, filename):
    request = Request(url, headers={'User-Agent': 'Personal-CTF-calendar-research/1.0'})
    with urlopen(request, timeout=60) as response:
        data = response.read()
    (SOURCES / filename).write_bytes(data)
    return {'url': url, 'file': filename, 'fetched_at_utc': datetime.now(timezone.utc).isoformat(), 'bytes': len(data)}

if __name__ == '__main__':
    # Include December 2025 to detect events crossing the year boundary.
    start = int(datetime(2025, 12, 1, tzinfo=timezone.utc).timestamp())
    finish = int(datetime(2027, 1, 2, tzinfo=timezone.utc).timestamp())
    manifest = []
    manifest.append(fetch(f'https://ctftime.org/api/v1/events/?limit=1000&start={start}&finish={finish}', 'ctftime_api_raw.json'))
    manifest.append(fetch('https://ctftime.org/event/list/?year=2026', 'ctftime_2026.html'))
    (SOURCES / 'fetch_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    events = json.loads((SOURCES / 'ctftime_api_raw.json').read_text(encoding='utf-8'))
    print(json.dumps({'fetched': len(events), 'manifest': manifest}, ensure_ascii=False, indent=2))
