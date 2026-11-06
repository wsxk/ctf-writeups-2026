"""Complete the two NCTF 2026 challenges absent from the official attachment tree."""
import collect_reverse as c
import shutil

def configurations():
    specs=[('VM Encryptor','虚拟化','https://raw.githubusercontent.com/sajjadium/ctf-archives/main/ctfs/NCTF/2026/rev/VM_Encryptor/vm-encryptor-attachment.zip','vm-encryptor-attachment.zip',None),
      ('Pay For 2048','逆向','https://drive.usercontent.google.com/download?id=1tNrpgo4SzocbQCowDM3nIrVEMX4Lfypc&export=download&confirm=t','pay-for-2048-attachment.zip',138125965)]
    for title,cat,url,name,size in specs:
        dirname='NCTF_2026';files=[{'url':url,'local':'attachments/'+name}]
        if size:files[0]['size_expected']=size
        pdfurl='https://raw.githubusercontent.com/X1cT34m/NCTF2026/main/NCTF%202026%20Official%20Writeup.pdf'
        files.append({'url':pdfurl,'local':'writeups/NCTF_2026_Official_Writeup.pdf','size_expected':3769458})
        j=dict(event_id='CTF-3206',event_title=c.EVENTS['CTF-3206']['title'],category=cat,title=title,dirname=dirname,
           source_urls=['https://github.com/X1cT34m/NCTF2026','https://github.com/sajjadium/ctf-archives/tree/main/ctfs/NCTF/2026/rev/'+title.replace(' ','_')],
           files=files,notes='解答为官方91页PDF：Pay For 2048从第70页开始，VM Encryptor从第75页开始。官方附件仓库没有这两题，分别由CTF Archives镜像和该镜像README链接的公开Google Drive下载补齐。仅下载，未运行。')
        c.JOBS.append(j)
        p=c.ROOT/cat/dirname/c.safe(title)/'writeups/NCTF_2026_Official_Writeup.pdf';p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():shutil.copyfile(c.ROOT/'sources/NCTF_2026_Official_Writeup.pdf',p)

if __name__=='__main__':
    c.configurations=configurations
    c.REPORT_FILE='reverse_nctf_more_search.json'
    c.main()
