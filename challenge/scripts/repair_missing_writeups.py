"""Stage replacement writeup bodies; does not mutate challenge directories."""
import concurrent.futures as cf
import hashlib,json,pathlib,re,time
import requests
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'sources/writeup_replacements'
JOBS=[
 ('pwn/trx_2026/down_the_line','https://kqx.io/writeups/down_the_line/'),
 ('pwn/trx_2026/krwd','https://kqx.io/writeups/krwd/'),
 ('pwn/trx_2026/triforce','https://kqx.io/writeups/triforce/'),
 ('逆向/trx_2026/faulty_road','https://kqx.io/writeups/faulty_road/'),
 ('逆向/tjctf_2026/rotated','https://dhtson.github.io/blogs/TJCTF-2026-Rev-Rotated/'),
 ('逆向/uiuctf_2026/glyphs','https://cybersecurityelite.com/ctf-writeups/uiuctf-2026-reverse-engineering-writeup/'),
 ('pwn/gpn_2026/Food_Inspector_II','https://raw.githubusercontent.com/hax1ng/GPN-CTF-2026/main/Food%20Inspector%20II/food-inspector-2_writeup.md'),
 ('pwn/gpn_2026/Scanwich_Station','https://raw.githubusercontent.com/hax1ng/GPN-CTF-2026/main/Scanwich%20Station/Scanwich_Station_recipe_writeup.md'),
 ('逆向/kubstu_2026/Ouroboros','https://raw.githubusercontent.com/hax1ng/KubSTU-CTF-2026/main/rev/ouroboros/README.md'),
 ('逆向/kubstu_2026/RISC_V','https://raw.githubusercontent.com/hax1ng/KubSTU-CTF-2026/main/rev/risc-v/README.md'),
 ('pwn/umdctf_2026/bookmaker','https://yhalo.cn/1978/umdctf-2026-pwn-wp-by-yhalo/'),
 ('pwn/trx_2026/house_of_fishing','https://blog.davidherm.es/posts/hof/'),
 ('pwn/trx_2026/slop_allocator','https://blog.rawpayload.com/blog/trx-ctf-2026-slop-allocator-writeup'),
 ('虚拟化/trx_2026/1+1','https://blog.rawpayload.com/blog/trx-ctf-2026-1-plus-1-writeup'),
 ('虚拟化/trx_2026/wandering','https://blog.rawpayload.com/blog/trx-ctf-2026-wandering-writeup'),
 ('逆向/umdctf_2026/nuclear_codes','https://blog.rawpayload.com/blog/umd-ctf-2026-nuclear-codes-writeup'),
 ('逆向/volgactf_2026-quals/Vision','https://blog.sdark.me/vision-volgactf-2026'),
]
def fetch(job):
    target,url=job
    result={'target':target,'url':url,'files':[]}
    try:
        r=requests.get(url,timeout=(12,35));r.raise_for_status();data=r.content
        if not data:raise ValueError('empty response')
        is_md=url.endswith('.md')
        body=r.text if is_md else BeautifulSoup(data,'html.parser')
        if not is_md:
            for el in body(['script','style','nav','footer','header']):el.decompose()
            article=body.find('article') or body.find('main') or body
            text=article.get_text('\n',strip=True)
        else:text=body
        if len(text)<400:raise ValueError('short body: '+text[:100])
        if any(x in text[:600].lower() for x in ['just a moment','access denied','verify you are human']):raise ValueError('challenge/interstitial response')
        out=OUT/re.sub(r'[^a-zA-Z0-9_-]','_',target)
        out.mkdir(parents=True,exist_ok=True)
        def write(name,blob,derived=False):
            p=out/name;p.write_bytes(blob)
            result['files'].append(dict(staged_path=p.relative_to(ROOT).as_posix(),destination='writeups/replacement_'+name,url=url,kind='writeup',bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),derived=derived))
        write('source.md' if is_md else 'source.html',data)
        if not is_md:write('readable.txt',('Source: '+url+'\n\n'+text+'\n').encode('utf8'),True)
        result['text_characters']=len(text);result['status']='downloaded';result['preview']=text[:160]
        if 'kubstu' in target:result['event_id_correction']='CTF-3446'
    except Exception as ex:result.update(status='unavailable',error=str(ex))
    print(result['status'],target,result.get('text_characters',result.get('error')),flush=True)
    return result
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with cf.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(fetch,JOBS))
    (OUT/'mapping.json').write_text(json.dumps({'records':results,'notes':['Staged files only; root must merge metadata and copy files into target/writeups.','KubSTU two entries belong to autumn event CTF-3446.','No downloaded challenge code executed.']},ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
