"""Recover unavailable handouts from the public CTF archive, without execution."""
import json,concurrent.futures
from collect_specialized import ROOT,save,finish,LOG

def augment(rel,sourcepath,names,shared=False,partial=False):
    d=ROOT/rel;m=json.loads((d/'metadata.json').read_text(encoding='utf-8'));m['_dir']=d
    url='https://github.com/sajjadium/ctf-archives/tree/main/'+sourcepath
    m['source_urls'].append(url)
    for name in names:save(m,'https://raw.githubusercontent.com/sajjadium/ctf-archives/main/'+sourcepath+'/'+name,'attachments/'+name)
    m['notes']+=' 后续补充：已从 sajjadium/ctf-archives 下载镜像题目资料，见 attachments；此前缺失记录仅描述初次检索状态。'
    if shared:m['notes']+=' 此阶段与 Suspicious device 1 共用 SD 卡附件；在线云服务/数据库未在归档中提供。'
    if partial:m['notes']+=' 原题依赖在线服务，归档只有连接脚本，未包含服务端环境，因此不能完整离线复现。'
    finish(m)
    if shared or partial:
        p=d/'metadata.json';mm=json.loads(p.read_text(encoding='utf-8'));mm['attachment_status']='partial';p.write_text(json.dumps(mm,ensure_ascii=False,indent=2),encoding='utf-8')
        q=d/'README.md';q.write_text(q.read_text(encoding='utf-8').replace('附件：downloaded','附件：partial'),encoding='utf-8')

jobs=[
 ('android/Securinets CTF Quals 2026/Backdrop','ctfs/Securinets/2026/Quals/mobile/Backdrop',['README.md','backdrop.zip'],False,False),
 ('iot/NDIAS_2026/Tiny crackme','ctfs/NDIASAutomotiveIoT/2026/rev/Tiny_crackme',['README.md','dist-tiny_crackme.zip'],False,False),
 ('车联网/NDIAS_2026/I Saw Our Time Pass','ctfs/NDIASAutomotiveIoT/2026/misc/I_Saw_Our_Time_Pass',['README.md','dist-I_saw_our_time_pass.zip'],False,False),
 ('车联网/NDIAS_2026/RAMN ECU D','ctfs/NDIASAutomotiveIoT/2026/crypto/RAMN_ECU_D',['README.md','dist-ramn_ecu_d.zip'],False,False),
 ('车联网/NDIAS_2026/VIN Hunter','ctfs/NDIASAutomotiveIoT/2026/misc/VIN_Hunter',['README.md','connect.sh'],False,True),
 ('iot/NDIAS_2026/Suspicious device 1','ctfs/NDIASAutomotiveIoT/2026/misc/Suspicious_device_1',['README.md','dist-suspicious_device.zip'],False,True),
]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda args:augment(*args),jobs))
for i in [2,3]:augment('iot/NDIAS_2026/Suspicious device '+str(i),'ctfs/NDIASAutomotiveIoT/2026/misc/Suspicious_device_1',['dist-suspicious_device.zip'],True,True)
(ROOT/'sources/specialized_mirror_search.json').write_text(json.dumps({'records':LOG,'scope':'Public CTF archive mirror; historical endpoint scripts not executed.'},ensure_ascii=False,indent=2),encoding='utf-8')
