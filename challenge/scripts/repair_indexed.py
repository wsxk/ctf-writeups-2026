"""Fallback to the public upstream GitHub handout directory after mirror failures."""
import concurrent.futures as cf
import hashlib,json,re,time
from pathlib import Path
from urllib.parse import urlparse,unquote,quote
import requests
from bs4 import BeautifulSoup
from collect_indexed import ROOT,get,writeup,resolve_ctftime

def tree(url):
    r=get(url)
    s=BeautifulSoup(r.content,'html.parser')
    data=s.find('script',{'data-target':'react-app.embeddedData'})
    if not data: raise ValueError('GitHub tree payload unavailable')
    d=json.loads(data.string or data.get_text())['payload']
    route=d.get('codeViewTreeRoute',d)
    return route['tree']['items'],route.get('refInfo',{}).get('currentOid')

def walk(owner,repo,ref,path,depth=0):
    if depth>12: raise ValueError('excessive directory nesting')
    items,commit=tree(f'https://github.com/{owner}/{repo}/tree/{ref}/{quote(path)}')
    result=[]
    for i in items:
        if i['contentType']=='directory': result.extend(walk(owner,repo,commit or ref,i['path'],depth+1))
        elif i['contentType']=='file': result.append((i['path'],commit or ref))
    return result

def repair(path):
    m=json.loads(path.read_text(encoding='utf-8')); folder=path.parent
    report={'path':str(path.relative_to(ROOT)),'title':m['title'],'files':0}
    if m['attachment_status']=='unavailable':
        source=next((u for u in m['source_urls'] if 'github.com/' in u and '/tree/' in u),None)
        if source:
            try:
                parts=unquote(urlparse(source).path).strip('/').split('/')
                owner,repo,_,ref=parts[:4]; sub='/'.join(parts[4:])
                files=walk(owner,repo,ref,sub)
                errors=[]; real=[]
                for f,commit in files:
                    rel=f[len(sub):].lstrip('/')
                    if '..' in Path(rel).parts: raise ValueError('unsafe source path')
                    url=f'https://raw.githubusercontent.com/{owner}/{repo}/{commit}/{quote(f)}'
                    try:
                        r=get(url)
                        if r.content.startswith(b'version https://git-lfs.github.com/spec/v1'): raise ValueError('Git LFS pointer, not file content')
                        dest=folder/'attachments'/'upstream'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(r.content)
                        m['artifacts'].append(dict(path=dest.relative_to(ROOT).as_posix(),url=url,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),kind='attachment'))
                        report['files']+=1
                        if Path(f).name.lower() not in ['readme.md','license','.gitkeep']: real.append(f)
                    except Exception as e: errors.append({'url':url,'error':str(e)})
                m['errors'].extend(errors)
                if real:
                    m['attachment_status']='partial' if errors else 'downloaded'
                    m['notes'].append('镜像下载失败后，已从其标明的GitHub题目源目录下载，固定到提交哈希。')
                    m['attachment_kind']='upstream_files'
            except Exception as e: report['error']=str(e)
    if m['writeup_status']=='unavailable':
        resolved=resolve_ctftime()
        new_urls=[resolved.get(u,u) for u in m['writeup_urls']]
        for i,url in enumerate(new_urls,10):
            if writeup(url,folder/'writeups',m['artifacts'],i): m['writeup_status']='downloaded'
        m['writeup_urls']=new_urls
    path.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    desc=f"# {m['title']}\n\n- 比赛：{m['event_title']}（{m['event_id']}）\n- 分类：{m['category']}；原分类：{m['original_category']}\n- writeup：{m['writeup_status']}\n- 附件：{m['attachment_status']}\n\n"+'\n'.join(m['notes'])+'\n\n## 来源\n\n'+'\n'.join('- '+u for u in m['source_urls']+m['writeup_urls'])+'\n'
    (folder/'README.md').write_text(desc,encoding='utf-8')
    report.update(attachment=m['attachment_status'],writeup=m['writeup_status']);return report

if __name__=='__main__':
    paths=[]
    for p in ROOT.rglob('metadata.json'):
        m=json.loads(p.read_text(encoding='utf-8'))
        if m.get('collector')=='ctf42-public-index' and (m['attachment_status']=='unavailable' or m['writeup_status']=='unavailable'): paths.append(p)
    results=[]
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for r in pool.map(repair,paths): results.append(r);print(json.dumps(r,ensure_ascii=False),flush=True)
    (ROOT/'sources'/'indexed_repair_report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
