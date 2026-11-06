import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / 'sources'
events = []
notes = []

def event(title, start, end, fmt, mode, source, official=None, note='', level='主办方/高校官方公告', precision=None, **extra):
    e = dict(title=title, start=start, end=end, timezone='Asia/Shanghai', date_precision=precision or ('minute' if start and len(start)>10 else 'day'), format=fmt, mode=mode, source_url=source, official_url=official or source, source_level=level, notes=note)
    e.update(extra)
    events.append(e)

# New Hello-CTF repository: old Hello-CTFtime CN.json is no longer a complete current feed.
feeds=[('CN.json','data'),('CN_archive.json','archive')]
for fn,key in feeds:
    data=json.loads((S/('hello_current_'+fn)).read_text(encoding='utf-8'))[key]['result']
    for e in data:
        title=e['name']
        # Officially checked by the other researcher; exclude stale OpenHarmony date entries.
        if any(x in title for x in ['研究生网络安全创新','OpenHarmony','京津冀','铸网','电信和互联网']):
            continue
        def parse(s):
            d=datetime.strptime(s,'%Y年%m月%d日 %H:%M')
            return d.strftime('%Y-%m-%d') if d.strftime('%H:%M') in ['00:00','23:59'] else d.strftime('%Y-%m-%d %H:%M')
        start,end=parse(e['comp_time_start']),parse(e['comp_time_end'])
        source='https://github.com/ProbiusOfficial/Hello-CTF/blob/main/docs/Event/json/'+fn
        desc=e.get('detail','').replace('\n','；')
        mode='线下' if '线下' in desc else '线上'
        fmt='Jeopardy' if any(x in desc for x in ['Jeopardy','CTF','解题']) else '网络安全竞赛（CTF归属待复核）'
        note='数据来源：Hello-CTF。'+desc+'；社区赛历记录，未将占位的00:00/23:59当作确切比赛时刻。'
        level='社区赛历（Hello-CTF）'
        if '蒙古马杯' in title:
            source=e['link'];level='高校官方公告';fmt='理论+CTF' if '预赛' in title else 'CTF+AWDP'
            note='官方通知已核验；预赛CTF为8小时；决赛8月27–30日包含报到、正式比赛和颁奖，比赛分CTF和AWDP两个竞赛日。'
        if '极客少年' in title:
            source='https://www.csreviews.cn/?p=11161';level='赛事启动报道';fmt='Jeopardy'
            note='小学/中学分组；决赛地点为四川大学网络空间安全学院靶场。'
        if '宁波市第九届' in title:
            source='https://zone.ci/secarticles/wx/565916.html';level='赛事官方通知转载'
            note='来源注明宁波市计算机信息网络安全协会公众号；仅公布日期。';fmt='CTF/安全解题'
        if '西湖论剑' in title:
            source='https://hzdaily.hangzhou.com.cn/hzrb/2026/07/14/article_detail_1_20260714A075.html';level='杭州日报+Hello-CTF'
            note='杭州日报核验8月21日下午线上初赛；13:00–18:00来自Hello-CTF；采用AI Agent解题夺旗，决赛原计划9月底前。'
            fmt='AI Agent CTF'
        if 'BITs2' in title:
            note+='赛事转载页面以图片为主，本次未独立核验图中具体时刻。'
            if '决赛' in title:fmt='CTF决赛，具体赛制待核'
        if '湾区杯' in title:
            fmt='Jeopardy / CTF解题赛'
            note+='澳门网络及数据安全学会7月31日公告明确初赛采用CTF解题赛；9月4日15:30–17:00延期后时间仍来自Hello-CTF。'
            level='Hello-CTF（时间）+协会公告（赛制）'
        event(title,start,end,fmt,mode,source,e['link'],note,level)
        if '湾区杯' in title:
            events[-1]['additional_sources']=['https://www.cdssmacau.com/學會賽事/2026/1122/報名開啟｜2026第二屆灣區盃網路安全大賽等你來戰/']

# Public NSSCTF event index, no account or private data was used.
nss=json.loads((S/'nssctf_public_raw.json').read_text(encoding='utf-8'))
excluded=[]
seen=set()
for page in nss['pages']:
    for e in page['response'].get('data',{}).get('contests',[]):
        if e['id'] in seen:continue
        seen.add(e['id'])
        start=datetime.fromtimestamp(e['start_date']/1000,timezone(timedelta(hours=8)))
        end=datetime.fromtimestamp(e['ends_date']/1000,timezone(timedelta(hours=8)))
        if start.year!=2026:continue
        if e['title'] in ['测试赛','比赛测试'] or e['mode']!=0:
            excluded.append(dict(id=e['id'],title=e['title'],reason='测试占位赛事或非已确认CTF的校园网实战训练'))
            continue
        u=f'https://www.nssctf.cn/contest/{e["id"]}'
        mode='线下' if '线下' in e['title'] else '平台线上（是否要求现场以主办方为准）'
        note='NSSCTF公开赛事列表；依据Unix毫秒时间戳转换为北京时间。校内/限制参赛项目也在公开列表展示，收录不代表允许公众报名。'
        if e['id']==864:note+='公开标题未注明学校，保留原名；与全国初赛并非同一赛事。'
        if e['id']==849:note+='招新训练赛单独保留，非永久开放题库。'
        event(e['title'],start.strftime('%Y-%m-%d %H:%M'),end.strftime('%Y-%m-%d %H:%M'),'CTF',mode,page['url'],u,note,'NSSCTF官方公开API',nssctf_id=e['id'])

event('第十九届全国大学生信息安全竞赛（创新实践能力赛）暨第三届“长城杯”网数智安全大赛（防护赛）·半决赛','2026-03-22','2026-03-22','CTF/综合攻防','线下（六大赛区）','https://www.ciscn.cn/announcement/view/396',note='辽宁、陕西、浙江、广东、湖北、重庆六个赛区同日举行；线上初赛在2025-12-28，不计入2026日期清单。')
event('第三届“长城杯”网数智安全大赛（防护赛）·总决赛','2026-04-28','2026-04-28','综合攻防','线下（福州）','https://ccb.itsec.gov.cn/article/257',note='官方4月29日闭幕报道确认4月28日举办；另有CISCN公告 https://www.ciscn.cn/announcement/view/408 。与9月京津冀蒙“长城杯”为不同赛事。')
event('第十九届全国大学生信息安全竞赛（创新实践能力赛）·全国总决赛','2026-08-29 09:00','2026-08-30 14:00','CTF+综合渗透+AWDP','线下（济南）','https://www.ciscn.cn/announcement/view/418',note='齐鲁工业大学长清校区；实际竞赛窗口8月29日09:00–17:00、8月30日08:00–14:00，中间非连续比赛；此前Build环节8月12–17日，不另计赛事。')
event('第六届“长城杯”网络安全大赛暨京津冀蒙网络安全技能竞赛·初赛','2026-09-13','2026-09-13','CTF+靶场渗透','线上','https://notice.ysu.edu.cn/info/2073/25824.htm','https://endbm.ichunqiu.com/ccb2026','全国在校本科生/研究生；初赛4小时，公告未给具体起止时刻。')
event('第六届“长城杯”网络安全大赛暨京津冀蒙网络安全技能竞赛·决赛','2026-09-18','2026-09-18','人机协同渗透对抗（CTF赛事后续阶段）','线下（北京）','https://notice.ysu.edu.cn/info/2073/25824.htm','https://endbm.ichunqiu.com/ccb2026','决赛6小时；地点原定国联股份数字经济总部；具体开赛时刻未公布。')
event('2026年“羊城杯”网络安全大赛·线上初赛','2026-10-17 10:00','2026-10-17 14:00','网络安全攻防/CTF','线上','https://www.sohu.com/a/1076930511_161795','https://ycb.dasctf.com/','南方都市报9月16日赛事启动报道；本科院校、高职高专、机关事业、企业四组。','媒体报道（南方都市报）')
event('2026年“羊城杯”网络安全大赛·线下决赛','2026-10-31','2026-10-31','AI网络安全挑战+AI Agent解题','线下','https://www.sohu.com/a/1076930511_161795','https://ycb.dasctf.com/','报道标注10月31日为初定日期；本次未核验最终举办情况，不能仅因日期已过认定已举办。','媒体报道（南方都市报）',schedule_status='暂定')
event('第六届极客少年挑战赛·线上初赛','2026-07-30','2026-08-02','Jeopardy','线上','https://www.csreviews.cn/?p=11161',note='小学组/中学组分别两轮，每轮180分钟，选手可参加一轮或两轮并取最高分；具体轮次时刻未列。',level='赛事启动报道')
event('第二届“湾区杯”网络安全大赛·决赛','2026-09-14','2026-09-14','AWDP+人工智能漏洞挖掘','线下（广州）','https://app.myzaker.com/news/article.php?pk=6aa364cf8e9f09634978d4ac','https://race.cinsa.org.cn/','广东省计算机信息网络安全协会邀请函转载已核验；华南理工大学广州国际校区。活动总安排08:30–18:30，议程中实际比赛09:30–16:00，本表按日列示。赛道由公开赛题存档佐证。','主办协会邀请函转载+公开赛题存档',additional_sources=['https://github.com/CTF-Archives/2026-WQB-Finals'])

notes=[
 '本文件补充自Hello-CTF新版主仓库、NSSCTF公开API及官方/高校/媒体公告，非中国所有赛事的完备名单。',
 'NSSCTF默认公开列表共111项，已取完28页，111个唯一ID与total一致。前3页12条2026记录，排除两条测试占位和一项mode20校园网实战训练，保留9条；第4–28页没有额外2026记录。未查询私密比赛，不将默认列表等同于全站所有自定义/团队赛。',
 'Hello-CTF新版CN.json有10条，CN_archive.json有9条；旧Hello-CTFtime仓库另有历史数据。来源均须注明Hello-CTF。',
 'Hello-CTF当前数据中的OpenHarmony初赛/决赛旧时间未采用；研究生全国赛、京津冀初赛已由china_supplement.json覆盖。京津冀决赛为渗透测试+应急响应，未重复列入CTF解题赛清单。',
 '未核验到网鼎杯2026官方明确赛程；高校计划表/采购公告不足以确认正式比赛日期。',
 'CTFHub公开ICS保存为ctfhub_calendar.ics，只有最近100条（其中99条2026），未见中文赛事；ASIS Finals的Z时间比CTFtime早8小时，存在时区标记疑点，故未用于覆盖CTFtime的时间。',
 '铸网2026鲁智杯与电信和互联网行业网络安全管理员职业技能竞赛在Hello-CTF中为pending；未把阶段截止日期或计划月份当成正式比赛时间。',
 '部分赛事仅由社区赛历或通知转载确认，source_level已标记，不能称全部逐条官方核验。'
]
out={'as_of':'2026-11-06','events':events,'excluded_nssctf_entries':excluded,'coverage_notes':notes}
(S/'domestic_calendar.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'events':len(events),'nssctf':sum('nssctf_id' in e for e in events)},ensure_ascii=False))
