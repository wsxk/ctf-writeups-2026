"""Resume a large public HTTP file using bounded, verified byte ranges."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import requests,json,time,hashlib,zipfile

def fetch(url,dst,size,workers=6):
    dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists() and dst.stat().st_size==size:return {'status':'downloaded','bytes':size,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()}
    part=dst.with_name(dst.name+'.part');prefix=part.stat().st_size if part.exists() else 0
    chunks=dst.with_name(dst.name+'.chunks');chunks.mkdir(exist_ok=True)
    ranges=[(start,min(start+2097152,size)-1) for start in range(prefix,size,2097152)]
    def one(pair):
        start,end=pair;p=chunks/f'{start:012d}-{end:012d}'
        if p.exists() and p.stat().st_size==end-start+1:return p
        for attempt in range(4):
            try:
                with requests.get(url,headers={'Range':f'bytes={start}-{end}'},timeout=(10,35)) as r:
                    r.raise_for_status()
                    if r.status_code!=206 or r.headers.get('Content-Range')!=f'bytes {start}-{end}/{size}':raise ValueError('Unexpected range response')
                    data=r.content
                if len(data)!=end-start+1:raise ValueError('Incomplete range')
                p.write_bytes(data);return p
            except Exception:
                if attempt==3:raise
                time.sleep(1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs=[pool.submit(one,x) for x in ranges]
        for i,f in enumerate(as_completed(futs),1):f.result();print('range',i,'/',len(ranges),'complete',flush=True)
    temp=dst.with_name(dst.name+'.assembling')
    with temp.open('wb') as out:
        if prefix:
            with part.open('rb') as src:
                while block:=src.read(1048576):out.write(block)
        for start,end in ranges:
            with (chunks/f'{start:012d}-{end:012d}').open('rb') as src:
                while block:=src.read(1048576):out.write(block)
    if temp.stat().st_size!=size:raise ValueError('Final size mismatch')
    if dst.suffix=='.zip':
        with zipfile.ZipFile(temp) as z:
            bad=z.testzip()
            if bad:raise ValueError('ZIP CRC mismatch: '+bad)
    temp.replace(dst)
    # Only this exact downloader's temporary files are removed, never recursive directories.
    if part.exists():part.unlink()
    for start,end in ranges:(chunks/f'{start:012d}-{end:012d}').unlink()
    if not list(chunks.iterdir()):chunks.rmdir()
    return {'status':'downloaded','bytes':size,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()}

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    url='https://raw.githubusercontent.com/SycloverTeam/SCTF-2026/HEAD/Reverse/GuardMaster/GuardMaster.zip'
    result=fetch(url,root/'android/SCTF_2026/GuardMaster/attachments/GuardMaster.zip',80146867)
    (root/'sources/reverse_guardmaster_retry.json').write_text(json.dumps({'url':url,**result},indent=2),encoding='utf-8')
    print(result,flush=True)
