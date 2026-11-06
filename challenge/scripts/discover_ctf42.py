"""Collect a reproducible public index. Does not execute downloaded challenges."""
import concurrent.futures as cf
import json, re, time
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'sources'
SOURCES.mkdir(parents=True, exist_ok=True)
BASE = 'https://ctf42.online'
QUERY = BASE + '/challenges/?year_min=2026&year_max=2026&category=pwn&category=rev&category=hardware&category=mobile&has_writeup=1'

def get(url):
    for n in range(3):
        try:
            r = requests.get(url, timeout=40)
            r.raise_for_status()
            return r
        except Exception:
            if n == 2: raise
            time.sleep(n+1)

def listing(page):
    r = get(QUERY + '&page=' + str(page))
    (SOURCES / f'ctf42_list_{page}.html').write_bytes(r.content)
    s = BeautifulSoup(r.content, 'html.parser')
    rows = []
    for tr in s.select('tbody tr'):
        td = tr.find_all('td', recursive=False)
        if len(td) < 5: continue
        a = td[0].find('a')
        b = td[1].find('a')
        rows.append(dict(title=a.get_text(strip=True), url=urljoin(BASE,a['href']),
                         edition_title=b.get_text(strip=True), edition_url=urljoin(BASE,b['href']),
                         original_category=td[3].get_text(strip=True), tags=[x.get_text(strip=True).lstrip('#') for x in td[0].select('.tag')]))
    return rows, s.get_text(' ', strip=True)

def edition(url):
    s = BeautifulSoup(get(url).content, 'html.parser')
    ids = [re.search(r'ctftime.org/event/(\d+)',a['href']).group(1) for a in s.select('a[href]') if re.search(r'ctftime.org/event/(\d+)',a['href'])]
    return url, ids

def detail(row):
    try:
        r = get(row['url'])
        s = BeautifulSoup(r.content, 'html.parser')
        dest = SOURCES / 'ctf42_details' / (row['url'].replace(BASE+'/ctfs/','').strip('/').replace('/','__')+'.html')
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(r.content)
        row['detail_snapshot'] = dest.relative_to(ROOT).as_posix()
        links=[]
        mode=None
        for el in s.find_all(['h2','a']):
            if el.name == 'h2': mode=el.get_text(strip=True)
            elif mode == 'Writeups' and el.get('href') and el['href'].startswith('http'):
                links.append(el['href'])
        row['writeup_urls'] = list(dict.fromkeys(links))
        row['handout_urls'] = [a['href'] for a in s.select('a[href]') if 'Handout files' in a.get_text()]
        row['download_urls'] = [urljoin(BASE,a['href']) for a in s.select('a[href]') if 'folder.zip' in a['href']]
        row['status'] = 'indexed'
    except Exception as e: row['status']=str(e)
    return row

if __name__ == '__main__':
    rows, txt = listing(1)
    pages=int(re.search(r'Page 1 of (\d+)',txt).group(1))
    with cf.ThreadPoolExecutor(max_workers=5) as pool:
        for r,_ in pool.map(listing,range(2,pages+1)): rows.extend(r)
    events=json.loads((ROOT.parent/'CTF competion'/'2026_CTF比赛数据.json').read_text(encoding='utf-8'))['events']
    known={str(e['ctftime_id']):e for e in events if e.get('ctftime_id')}
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        editions=dict(pool.map(edition,sorted({r['edition_url'] for r in rows})))
    for row in rows:
        ids=[i for i in editions[row['edition_url']] if i in known]
        if len(ids)==1:
            e=known[ids[0]]
            row.update(event_id=e['record_id'],event_title=e['title'],event_status=e['status'])
        else: row['event_match']='unresolved: '+str(editions[row['edition_url']])
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        rows=list(pool.map(detail,rows))
    (SOURCES/'ctf42_index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(total=len(rows),matched=sum('event_id' in r for r in rows),editions=len(editions)),ensure_ascii=False))
    print('Unmatched:',[(r['edition_title'],r.get('event_match')) for r in rows if 'event_id' not in r])
