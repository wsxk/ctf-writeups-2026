"""Additional reviewed NCTF/SCTF/Thryve 2026 challenges; import shared downloader."""
import collect_reverse as c
import shutil

def configurations():
    for slug,category in [('Alice','逆向'),('BrainfOok','虚拟化'),('GuardMaster','android'),('Zombie_progression','逆向'),('babel_furnace','虚拟化'),('ghost_projection','逆向')]:
        def select(rel,x):
            if rel.lower().startswith(('writeup/','exp/')) or rel=='WP.md':return 'writeups'
            return 'attachments'
        c.add('CTF-3314','SCTF_2026',slug,'SycloverTeam/SCTF-2026','Reverse/'+slug,select,notes='官方2026仓库题目附件和完整writeup。按题目实际内容归类：GuardMaster为APK；BrainfOok及babel_furnace使用自定义VM。')
        c.JOBS[-1]['category']=category
    for slug in ['black-blood','chimera-mirrors','hell','parallax','redline','soul']:
        def select(rel,x):
            if rel=='README.md' or rel.endswith(('.py','.txt','.c','.asm')):return 'writeups'
            return 'attachments'
        c.add('CTF-3330','Thryve_CTF_2026',slug,'hax1ng/thryve-ctf-2026-writeups','rev/'+slug,select,notes='参赛者hax1ng公开仓库，保留文章、solver及其提供的比赛原始二进制/7z包；解法未运行验证。')
        c.JOBS[-1]['category']='虚拟化' if slug in ('chimera-mirrors','parallax','soul') else '逆向'
    for slug,title,category in [('chicken-feet-master','鸡爪流高手','逆向'),('hook-my-secret','Hook My Secret','android'),('no-my-bank','No My Bank!','逆向')]:
        c.add('CTF-3206','NCTF_2026',title,'X1cT34m/NCTF2026','Reverse/'+slug,lambda r,x:'attachments',
            [('https://raw.githubusercontent.com/X1cT34m/NCTF2026/main/NCTF%202026%20Official%20Writeup.pdf','writeups/NCTF_2026_Official_Writeup.pdf')],
            '官方仓库附件，配整场官方解答PDF；请在PDF目录中定位本题。PDF为原始文件，未重新排版。')
        c.JOBS[-1]['category']=category
        target=c.ROOT/category/'NCTF_2026'/c.safe(title)/'writeups/NCTF_2026_Official_Writeup.pdf'
        target.parent.mkdir(parents=True,exist_ok=True)
        source=c.ROOT/'sources/NCTF_2026_Official_Writeup.pdf'
        if source.exists() and not target.exists():shutil.copyfile(source,target)

if __name__=='__main__':
    c.configurations=configurations
    c.REPORT_FILE='reverse_extra_search.json'
    c.main()
