"""Synchronize completed manifests and assemble the official split MusicPlayer ZIP."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'sources/reverse_progress_snapshot.json';report=json.loads(p.read_text(encoding='utf-8'))
assert report['pending_files']==0,'Unfinished source downloads remain'
rows=report['entries'];j=next(x for x in rows if x['title']=='SU_MvsicPlayer')
base=ROOT/j['directory'];folder=base/'attachments/attachments';out=folder/'SU_MusicPlayer.zip'
expected=(folder/'SU_MusicPlayer.zip.sha256').read_text(encoding='utf-8').split()[0]
parts=[folder/('SU_MusicPlayer.zip.part-'+s) for s in ['aa','ab','ac']]
if not out.exists():
    tmp=out.with_name(out.name+'.assembling')
    with tmp.open('wb') as dst:
        for part in parts:
            with part.open('rb') as src:
                while block:=src.read(1048576):dst.write(block)
    tmp.replace(out)
data=out.read_bytes();actual=hashlib.sha256(data).hexdigest();assert actual==expected,'Official SHA-256 mismatch'
with zipfile.ZipFile(out) as z:
    bad=z.testzip();assert bad is None,'ZIP CRC mismatch';members=len(z.infolist())
derived={'local':'attachments/attachments/SU_MusicPlayer.zip','status':'assembled_and_verified','bytes':len(data),'sha256':actual,'source_files':['attachments/attachments/'+x.name for x in parts],'official_sha256_matches':True,'zip_members':members,'zip_crc_ok':True}
j['derived_files']=[derived]
j['notes']+=' 已将3个分片按字节拼接为attachments/attachments/SU_MusicPlayer.zip，与官方SHA-256完全一致且ZIP CRC通过；未执行仓库restore脚本。'
(base/'metadata.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
readme=base/'README.md';text=readme.read_text(encoding='utf-8')
if '已将3个分片' not in text:readme.write_text(text+'\n'+j['notes'].split(' 已将3个分片')[-1].join(['已将3个分片','\n']),encoding='utf-8')
report['derived_file_count']=1;report['derived_bytes']=len(data);report['complete']=True
p.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for name,entries in [('reverse_search.json',rows[:45]),('reverse_extra_search.json',rows[45:60]),('reverse_nctf_more_search.json',rows[60:])]:
    (ROOT/'sources'/name).write_text(json.dumps({'date':'2026-11-06','complete':True,'scope':'Reviewed 2026 catalog events, all selected attachments and public solutions downloaded; sources retained per file','entries':entries},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'sources/reverse_joined_archive_validation.json').write_text(json.dumps(derived,ensure_ascii=False,indent=2),encoding='utf-8')
print({'source_files':report['downloaded_files'],'pending_files':report['pending_files'],'derived':derived})
