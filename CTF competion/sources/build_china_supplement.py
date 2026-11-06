import json
from pathlib import Path

events=[]
def add(title,start,end,precision,fmt,mode,url,notes='',official=None,level='主办方/承办高校公告',**kw):
    events.append(dict(title=title,start=start,end=end,timezone='Asia/Shanghai',date_precision=precision,format=fmt,mode=mode,source_url=url,official_url=official or url,source_level=level,notes=notes,**kw))

q='https://www.qiangwangbei.com/'
add('第十届“强网杯”全国网络安全挑战赛·线上赛','2026-10-31','2026-11-01','day','CTF 解题','线上',q,'官网仅公布日期；勿与第九届强网拟态防御挑战赛混同。')
add('第十届“强网杯”全国网络安全挑战赛·线下赛','2026-11-28','2026-11-29','day','网络安全实战挑战','线下',q,'线上赛前32队晋级；官网未公布小时。')
q='https://cs.cumt.edu.cn/__local/4/15/86/627C179CC81AB86DD5BA81407D2_5C5FA905_147FE.pdf?e=.pdf'
add('SparkCTF v26 高校寒假联谊赛·训练赛','2026-01-19','2026-02-28','day','Jeopardy / 个人训练赛','线上',q,'高校联谊赛；具体时刻未公开。','https://ctf.cumt.edu.cn/')
add('SparkCTF v26 高校寒假联谊赛·决赛','2026-03-07','2026-03-08','day','Jeopardy / 个人赛','线上',q,'具体时刻以赛事群通知为准。','https://ctf.cumt.edu.cn/')
add('Spark CTF 2026 网络安全大赛·校内个人赛','2026-09-28 09:00','2026-11-01 18:00','minute','Jeopardy / 个人赛','线上','https://is.cumt.edu.cn/a0/dc/c12998a696540/page.htm','校内赛道限中国矿业大学2025、2026级本科生。','https://spark.bxs.team/')
add('合肥师范学院 NUCTF 2026 新生赛','2026-08-31 10:00','2026-09-02 17:00','minute','Jeopardy / 个人赛','线上','https://jsjxy.hfnu.edu.cn/info/1723/36791.htm','面向该校2026级新生。')
q='https://seusus.com/susctf-2026/'
add('SUSCTF 2026·主赛道（东南大学虎踞龙蟠杯）','2026-10-16 18:00','2026-10-18 22:00','minute','Jeopardy / 个人赛','线上',q,'东南大学第七届大学生网络安全挑战赛。','https://ctf.seusus.com/')
add('SUSCTF 2026·新生赛道','2026-09-21 13:00','2026-10-04 22:00','minute','Jeopardy / 个人赛','线上',q,'限校内大一、大二。','https://ctf.seusus.com/')
q='https://ctf.scnu.edu.cn/'
add('XSWCTF 2026 联合招新赛 / 华南师范大学第十届网络安全技术竞赛·线上赛','2026-11-07 21:00','2026-11-08 21:00','minute','Jeopardy / 团队赛','线上',q,'官网标题为第十届，简介仍写第九届；按标题记录，参赛资格以各校赛道规则为准。')
add('华南师范大学第十届网络安全技术竞赛新生赛·线下决赛','2026-11-22 09:00','2026-11-22 17:00','minute','CTF 快速解题','线下',q,'线上有效队伍前50%晋级；报名及热身赛未单独计数。')
q='https://zh.jnu.edu.cn/2026/0919/c42461a863378/page.htm'
add('暨南大学珠海校区第六届“日月盾杯”·线上赛','2026-10-10 09:00','2026-10-20 18:00','minute','CTF / 团队赛','线上',q,'珠海校区大一、大二学生；每队1–3人。')
add('暨南大学珠海校区第六届“日月盾杯”·线下赛','2026-10-26 13:00','2026-10-26 18:00','minute','CTF / 团队赛','线下',q,'地点：综合教学楼实C404。')
add('天津商业大学第一届网络安全夺旗赛','2026-11-11 12:30','2026-11-11 16:30','minute','理论 + CTF / 团队赛','地点待通知','https://www.tjcu.edu.cn/info/1080/30369.htm','限本校本科生、研究生；报名11月6日17:00截止。')
q='https://nic.imut.edu.cn/info/1014/3921.htm'
add('内蒙古工业大学2026网络安全技能竞赛·初赛','2026-10-17','2026-10-17','day','理论 + CTF','线下',q,'每队3人；限本校在读学生。')
add('内蒙古工业大学2026网络安全技能竞赛·决赛','2026-10-18','2026-10-18','day','Attack-Defense / AWD','线下',q,'具体场地与时刻由赛事群公布。')
add('第二届“正中”杯淄博师专网络安全竞赛 ZSCTF 2026','2026-09-16 18:00','2026-09-16 21:00','minute','理论 + CTF / 个人赛','线上','https://nic.zbnc.edu.cn/info/1183/1932.htm','设学生组、教工组，合并记为一场。')
add('中南民族大学2026研究生网络安全创新大赛校内赛·实网对抗','2026-11-22','2026-11-22','day','CTF 动态积分','线上','https://www.scuec.edu.cn/jky/info/1167/5984.htm','校内赛事，勿与全国赛10月24日初赛合并。')
add('第四届湖北大学网络安全创新大赛·CTF解题赛','2026-11',None,'month','理论 + Jeopardy','线上','https://cybersec.hubu.edu.cn/info/1215/3753.htm','仅公布2026年11月，具体日时由赛事群通知。')
add('2026京津冀大学生信息安全网络攻防大赛·线上初赛','2026-09-13','2026-09-13','day','理论 + CTF','线上','https://www.tjise.edu.cn/info/1008/5580.htm','京津冀本科生；决赛10月11日为渗透测试和应急响应，不在CTF补充清单重复列出。','https://www.datacon.org.cn/2026TJISE')
q='https://jwc.xjtu.edu.cn/info/1172/10031.htm'
add('ISCC 2026 破阵夺旗赛·区域赛','2026-05-09 08:00','2026-05-15 20:00','minute','Jeopardy / 个人赛','线上',q,'统一区域赛日程；有地区组委会的赛区可能自行安排，截止不晚于5月15日20:00。','https://www.isclab.org.cn/')
add('ISCC 2026 破阵夺旗赛·全国总决赛','2026-05-16 08:00','2026-05-18 20:00','minute','Jeopardy / 个人赛','线上',q,'第23届信息安全与对抗技术竞赛。','https://www.isclab.org.cn/')
add('第四届上海理工大学信息安全竞赛暨校队选拔赛','2026-04-19 13:00','2026-04-19 17:00','minute','Jeopardy / 个人赛','线下','https://cec.usst.edu.cn/2026/0331/c6750a358926/page.htm','地点：军工路580号计算中心506；全校学生。')
add('重庆工程学院网络工程与信息安全系教师CTF竞赛','2026-05-27 14:00','2026-05-27 15:30','minute','Jeopardy / 个人赛','线下','https://zdh.cqie.edu.cn/html/15/content/26/05/77527.shtml','内部教师赛；有官方赛后报道。')
add('南京邮电大学通达学院计算机工程学院CTF网络安全竞赛','2026-05-29',None,'day','Jeopardy','线下','https://www.nytdc.edu.cn/jsjgcxy/2026/0602/c961a50294/page.htm','官方报道仅说明5月29日晚；地点扬教2217，未公布结束时间。')
add('重庆科技大学第一届“薪火计划”工控互联网安全竞赛·CTF赛段','2026-04-26',None,'day','CTF + 工控场景渗透','线下','https://znxy.cqust.edu.cn/info/1004/6217.htm','上午CTF，下午工控渗透；9:00为开幕式，不当作CTF精确开赛时刻。')
add('四川化工职业技术学院第三届“极客杯”CTF网络安全挑战赛·决赛','2026-05-14 10:30','2026-05-14 15:30','minute','CTF / 团队赛','线下','https://twxx.sccc.edu.cn/info/1012/4282.htm','包含四川化工职业技术学院、泸州职业技术学院队伍。')
add('第二届“长江青锋杯”高校网络安全技能竞赛','2026-06-25','2026-06-26','day','CTF / 团队赛','线下','https://wlgc.whit.edu.cn/info/1020/2368.htm','参赛高校官方赛后报道给出活动日程；实际竞技时长5小时，具体时段未披露。',level='参赛高校官方报道')
q='https://zjkjjs.zjgsu.edu.cn/post/8178f233-4e48-481a-8f10-cbc02a9c9b34/'
add('第九届浙江省大学生网络与信息安全竞赛·创新实践挑战赛预赛','2026-11-07','2026-11-07','day','Jeopardy','指定考点线上答题',q,'限浙江及长三角其他地区高校本科、专科学生；每队3人。','https://nisc.dasctf.com/')
add('第九届浙江省大学生网络与信息安全竞赛·创新实践挑战赛决赛','2026-11-14','2026-11-14','day','综合攻防 / AI应用解题','线下',q,'浙江理工大学；仅记录实践赛道，不包括知识、作品赛。','https://nisc.dasctf.com/')
q='https://grd.bit.edu.cn/pygz/cxpy/tzgg_cxpy/23608f4cf26643d7a20c79eaca362b9f.htm'
add('“华为杯”第五届中国研究生网络安全创新大赛·实网对抗初赛','2026-10-24','2026-10-24','day','Jeopardy','线上',q,'全国研究生赛事；非作品赛或揭榜挑战赛。','https://cpipc.acge.org.cn/cw/hp/2c90800c8093eef401809d33b36f0652')
add('“华为杯”第五届中国研究生网络安全创新大赛·实网对抗决赛','2026-12-26','2026-12-27','day','AWD Plus + 靶场综合渗透','线下',q,'暂定哈尔滨市南岗区；以最终决赛通知为准。','https://cpipc.acge.org.cn/cw/hp/2c90800c8093eef401809d33b36f0652',schedule_status='暂定')
q='https://thuctf.tsinghua.edu.cn/harmonyctf/posts'
add('第二届 OpenHarmony CTF 智能漏洞挖掘赛·决赛线上提交','2026-10-15 09:00','2026-10-19 09:00','minute','Capture The Flaw / 漏洞挖掘','线上',q,'初赛前20队晋级；官网搜索索引可核验，动态页正文直接访问不可读。')
add('第二届 OpenHarmony CTF 智能漏洞挖掘赛·现场决赛','2026-12',None,'month','Capture The Flaw / 漏洞挖掘','线下',q,'官网公告索引仅给出12月，具体日期待定。')
q='https://hhb.whcsa.org.cn/'
add('2026“黄鹤杯”网络安全人才创新大赛·线上初赛','2026-07',None,'month','Jeopardy','线上',q,'官网仅公布月份；学生组和职业组各4小时。')
add('2026“黄鹤杯”网络安全人才创新大赛·线下决赛','2026-10',None,'month','AWD Plus + 实物漏洞挖掘','线下',q,'官网仅公布月份；武汉。')
add('东华理工大学“核动力杯”网络安全大赛·CTF夺旗赛道','2026-09-20','2026-09-28','day','Jeopardy','线上','https://nic.ecut.edu.cn/25/50/c4904a140624/page.htm','仅记录CTF赛道，不将创意作品、护校众测日程计为CTF。')

# Public competition listing is the same official data used by the CTFy front end.
from datetime import datetime,timedelta,timezone
def cn(t):
    return datetime.fromisoformat(t.replace('Z','+00:00')).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')
for item in json.loads(Path(__file__).with_name('ctfy_competitions_raw.json').read_text(encoding='utf-8'))['items']:
    name=item.get('title_i18n',{}).get('zh-CN','')
    if name.startswith('TPCTF 2026'):
        sessions=[{'start':cn(s['starts_at']),'end':cn(s['ends_at'])} for s in item.get('sessions',[])]
        if '人机协同团队' in name:
            note='非连续开放；官方session为11月15日、22日各10:00–20:00。'
        elif '智能体团队' in name:
            note='非连续开放；官方session为11月15日、21日、22日各10:00–20:00。'
        else:
            note='仅人机协同赛段，11月15–20日每日10:00–20:00；北大平台后续智能体攻防具体时间待定。官方中英文简介旧日期不同，采用当前start/end和session。'
        add(name+'·人机协同赛段' if '校内赛' in name else name,cn(item['starts_at']),cn(item['ends_at']),'minute','CTF / AI安全','线上','https://ctfy.tsinghua.edu.cn/api/v1/competitions?offset=0&limit=100',note,'https://ctfy.tsinghua.edu.cn/',level='主办方官方公开API',sessions=sessions,platform_event_id=item['id'])

out={
 'retrieved_date':'2026-11-06',
 'events':events,
 'coverage_notes':[
  '本文件为国内官方公告与高校公告补充，不声称完整覆盖中国所有校赛、企业内部赛和未公开赛程。初赛、决赛、独立赛道按阶段记录。',
  '北京时间统一为Asia/Shanghai；day表示只核验到日期，month表示只核验到月份；null为未公布，不补零点。',
  '强网杯与强网拟态防御赛事名称不同，即使线上日期相同也不得合并。',
  'Hello-CTFtime 当前CN.json为空；README旧路径Achieve/CN_CTF.json已失效；实际路径Achieve/CN_archive.json包含118条档案，其中4条日期涉及2026。原始文件已另存。',
  '公开搜索NSSCTF、CTFHub、DASCTF和虎符未得到可靠可穷尽的2026全年表；不能据此推断不存在赛事。',
  '未计入赛事名含2026但实际于2025举办的校内选拔赛；未将培训、报名、颁奖、知识竞答和作品评审单列为CTF。',
  '第十七届广东技术师范大学网络攻防邀请赛公告内部日期冲突：一处初赛5月23日/决赛5月30日，另一处5月16日/5月23日，均暂定；列入待核实而非确定日程。'
 ],
 'unresolved':[
  {'title':'第十七届广东技术师范大学大学生科技学术季网络攻防邀请赛','source_url':'https://scs.gpnu.edu.cn/info/1097/3419.htm','reason':'公告日期自相矛盾，均注明暂定；应向赛事方核实。'},
  {'title':'中国地质大学（北京）第一届校园网络安全夺旗赛','source_url':'https://nic.cugb.edu.cn/c/2026-06-16/854792.shtml','reason':'官方报道确认举行且6月15日颁奖，但未公开可核验的竞赛起止日期；不以颁奖日期代替比赛日期。'}
 ]
}
Path(__file__).with_name('china_supplement.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Wrote',len(events),'events')
