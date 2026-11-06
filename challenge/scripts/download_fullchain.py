"""Stream the public SUCTF 2026 fullchain attachment; no code is executed."""
import hashlib,json,pathlib,shutil,time
import requests
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
DEST=ROOT/'pwn'/'SUCTF_2026'/'SU_fullchian'/'attachments'/'attachment.7z'
LOG=ROOT/'sources'/'pwn_fullchain_download.json'
URL='https://drive.google.com/uc?export=download&id=11VEeW4RE1fLuppTl5M0qms8pmntZx2Av'
def log(data):LOG.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(data,ensure_ascii=False),flush=True)
def main():
    free=shutil.disk_usage(DEST.parent).free
    assert free>30_000_000_000,'Insufficient disk space'
    session=requests.Session()
    r=session.get(URL,timeout=30);r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser');form=soup.find('form')
    if not form:raise ValueError('No public download confirmation form found')
    params={i['name']:i.get('value','') for i in form.select('input[name]')}
    partial=DEST.with_suffix('.7z.part');offset=partial.stat().st_size if partial.exists() else 0
    headers={'Range':f'bytes={offset}-'} if offset else {}
    log({'status':'connecting','free_disk_bytes':free,'source_url':URL,'bytes_downloaded':offset})
    r=session.get(form['action'],params=params,headers=headers,stream=True,timeout=(30,180));r.raise_for_status()
    content_type=r.headers.get('Content-Type','');expected=int(r.headers.get('Content-Length','0'))
    if 'html' in content_type.lower():
        text=r.text
        raise ValueError('Received HTML instead of archive: '+BeautifulSoup(text,'html.parser').get_text(' ',strip=True)[:500])
    mode='ab' if offset and r.status_code==206 else 'wb'
    if mode=='wb':offset=0
    total=offset;start=time.monotonic();last=start
    state={'status':'downloading','content_type':content_type,'response_length_bytes':expected,'total_expected_bytes':expected+offset if expected else None,'free_disk_bytes':free,'source_url':URL,'final_url':r.url,'path':str(DEST.relative_to(ROOT))}
    log(state)
    with partial.open(mode) as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            if not chunk:continue
            if total==0 and not chunk.startswith(b'7z\xbc\xaf\x27\x1c'):raise ValueError('Invalid 7z magic')
            f.write(chunk);total+=len(chunk);now=time.monotonic()
            if now-last>=30:
                log({**state,'bytes_downloaded':total,'bytes_per_second':int((total-offset)/(now-start))});last=now
    if expected and total!=expected+offset:raise ValueError(f'Incomplete archive {total} != {expected+offset}')
    h=hashlib.sha256()
    with partial.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    partial.replace(DEST)
    log({**state,'status':'complete','bytes_downloaded':total,'sha256':h.hexdigest(),'elapsed_seconds':time.monotonic()-start})
if __name__=='__main__':
    try:main()
    except Exception as ex:
        prior=json.loads(LOG.read_text(encoding='utf8')) if LOG.exists() else {}
        log({**prior,'status':'failed','error':str(ex)})
        raise
