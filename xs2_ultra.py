import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import os, sys, time, json, threading
from datetime import datetime
import psutil
import platform
from collections import deque
import pystray
from PIL import Image, ImageDraw
import keyboard
import winreg

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, 'xs2_config.json')

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('XS2 Optimizer ULTRA')
        self.geometry('780x820')
        self.minsize(740,780)
        self.config = self.load_cfg()
        self.gm=False; self.fm=False; self.whitelist=self.config.get('wl',[])
        self.ping_hist=deque(maxlen=30); self.ping_run=False; self.tray=None
        style=ttk.Style(self)
        try: style.theme_use('clam')
        except: pass
        nb=ttk.Notebook(self); nb.pack(fill='both',expand=True,padx=8,pady=8)
        self.t_hw=ttk.Frame(nb); self.t_mon=ttk.Frame(nb); self.t_pg=ttk.Frame(nb); self.t_pr=ttk.Frame(nb)
        self.t_gm=ttk.Frame(nb); self.t_tw=ttk.Frame(nb); self.t_la=ttk.Frame(nb); self.t_cs=ttk.Frame(nb)
        self.t_oc=ttk.Frame(nb); self.t_ut=ttk.Frame(nb); self.t_in=ttk.Frame(nb)
        for f,t in [(self.t_hw,'Hardware'),(self.t_mon,'Monitor'),(self.t_pg,'Ping Graph'),(self.t_pr,'Priority'),
                    (self.t_gm,'Game Mode'),(self.t_tw,'Tweaks'),(self.t_la,'Launcher'),(self.t_cs,'CS2'),
                    (self.t_oc,'One-Click'),(self.t_ut,'Utility'),(self.t_in,'Info')]: nb.add(f,text=t)
        self.build_hw(); self.build_mon(); self.build_pg(); self.build_pr(); self.build_gm(); self.build_tw()
        self.build_la(); self.build_cs(); self.build_oc(); self.build_ut(); self.build_in()
        self.upd_all(); self.tray_init(); self.reg_hk(); self.auto_chk()
        self.protocol('WM_DELETE_WINDOW',self.hide_tray)
    def load_cfg(self):
        try:
            if os.path.exists(CONFIG): return json.load(open(CONFIG))
        except: pass
        return {'wl':[],'auto':False}
    def save_cfg(self):
        try: json.dump({'wl':self.whitelist,'auto':self.config.get('auto',False)},open(CONFIG,'w'),indent=2)
        except: pass
    def reg_hk(self):
        try: keyboard.add_hotkey('ctrl+shift+g', self.hk_gm)
        except: pass
    def hk_gm(self):
        if not self.gm: self.after(0,self.gm_on); self.noti('Game Mode Enabled')
        else: self.after(0,self.gm_off); self.noti('Game Mode Disabled')
    def noti(self,t,m):
        try:
            if self.tray: self.tray.notify(m,t)
        except: pass
    def build_hw(self):
        f=ttk.Frame(self.t_hw,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Hardware Monitor',font=('Segoe UI',11,'bold')).pack(anchor='w')
        ttk.Label(f,text='CPU/GPU/Memory',foreground='#888').pack(anchor='w',pady=(0,10))
        cf=ttk.LabelFrame(f,text='CPU',padding=10); cf.pack(fill='x')
        self.hw_cpu=ttk.Label(cf,text='Usage: -% | Freq: -MHz'); self.hw_cpu.pack(anchor='w')
        rf=ttk.LabelFrame(f,text='RAM',padding=10); rf.pack(fill='x',pady=8)
        self.hw_ram=ttk.Label(rf,text='-'); self.hw_ram.pack(anchor='w')
        gf=ttk.LabelFrame(f,text='GPU',padding=10); gf.pack(fill='x')
        self.hw_gpu=ttk.Label(gf,text='Usage/Temp: -'); self.hw_gpu.pack(anchor='w')
        ttk.Label(f,text='For temps use OpenHardwareMonitor/HWiNFO64',foreground='#b8860b').pack(pady=8)
    def build_mon(self):
        f=ttk.Frame(self.t_mon,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Live Monitor',font=('Segoe UI',11,'bold')).pack(anchor='w')
        rf=ttk.LabelFrame(f,text='Resources',padding=10); rf.pack(fill='x')
        self.m_cpu=ttk.Label(rf,text='CPU: -%'); self.m_cpu.pack(anchor='w')
        self.m_ram=ttk.Label(rf,text='RAM: -'); self.m_ram.pack(anchor='w')
        self.m_net=ttk.Label(rf,text='NET: -'); self.m_net.pack(anchor='w')
        pf=ttk.LabelFrame(f,text='Processes',padding=10); pf.pack(fill='both',expand=True,pady=8)
        cols=('n','p','m'); self.pt=ttk.Treeview(pf,columns=cols,show='headings')
        for c,t in zip(cols,['Process','PID','MB']): self.pt.heading(c,text=t)
        self.pt.column('n',width=320); self.pt.pack(side='left',fill='both',expand=True)
        sb=ttk.Scrollbar(pf,orient='vertical',command=self.pt.yview); sb.pack(side='right',fill='y'); self.pt.config(yscrollcommand=sb.set)
        bf=ttk.Frame(f); bf.pack(fill='x')
        ttk.Button(bf,text='Refresh',command=self.upd_proc).pack(side='left')
        ttk.Button(bf,text='Kill',command=self.killp).pack(side='left',padx=2)
        ttk.Button(bf,text='High Priority',command=self.prih).pack(side='left')
        ttk.Button(bf,text='Whitelist',command=self.wlp).pack(side='left',padx=2)
    def build_pg(self):
        f=ttk.Frame(self.t_pg,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Ping Graph',font=('Segoe UI',11,'bold')).pack(anchor='w')
        bf=ttk.Frame(f); bf.pack(fill='x')
        ttk.Button(bf,text='Start',command=self.pg_start).pack(side='left')
        ttk.Button(bf,text='Stop',command=self.pg_stop).pack(side='left',padx=2)
        ttk.Button(bf,text='Flush DNS',command=self.dnsf).pack(side='left')
        self.cv=tk.Canvas(f,height=160,bg='#111',highlightthickness=1,highlightbackground='#333'); self.cv.pack(fill='x',pady=8)
        self.cv.create_line(0,80,760,80,fill='#555',dash=(3,3))
        self.pl=ttk.Label(f,text='Ping: - | Avg: -'); self.pl.pack()
        df=ttk.LabelFrame(f,text='DNS',padding=10); df.pack(fill='x',pady=8)
        ttk.Button(df,text='1.1.1.1/1.0.0.1',command=lambda:self.dnss(['1.1.1.1','1.0.0.1'])).pack(fill='x',pady=1)
        ttk.Button(df,text='8.8.8.8/8.8.4.4',command=lambda:self.dnss(['8.8.8.8','8.8.4.4'])).pack(fill='x',pady=1)
        ttk.Button(df,text='Reset Network',command=self.nr).pack(fill='x',pady=1)
    def build_pr(self):
        f=ttk.Frame(self.t_pr,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Priority Manager',font=('Segoe UI',11,'bold')).pack(anchor='w')
        pf=ttk.LabelFrame(f,text='Processes',padding=10); pf.pack(fill='both',expand=True)
        cols=('n','p','pr'); self.prt=ttk.Treeview(pf,columns=cols,show='headings')
        for c,t in zip(cols,['Name','PID','Priority']): self.prt.heading(c,text=t)
        self.prt.pack(fill='both',expand=True)
        bf=ttk.Frame(f); bf.pack(fill='x')
        ttk.Button(bf,text='Refresh',command=self.upd_pr).pack(side='left')
        ttk.Button(bf,text='Above Normal',command=lambda:self.sp(psutil.ABOVE_NORMAL_PRIORITY_CLASS)).pack(side='left',padx=2)
        ttk.Button(bf,text='High',command=lambda:self.sp(psutil.HIGH_PRIORITY_CLASS)).pack(side='left')
        ttk.Button(bf,text='Normal',command=lambda:self.sp(psutil.NORMAL_PRIORITY_CLASS)).pack(side='left',padx=2)
    def build_gm(self):
        f=ttk.Frame(self.t_gm,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Game Mode',font=('Segoe UI',11,'bold')).pack(anchor='w')
        cf=ttk.LabelFrame(f,text='Control',padding=10); cf.pack(fill='x')
        self.gml=ttk.Label(cf,text='STATUS: INACTIVE',font=('Segoe UI',9,'bold'),foreground='#d33'); self.gml.pack()
        bf=ttk.Frame(cf); bf.pack(fill='x')
        self.gb1=ttk.Button(bf,text='ENABLE',command=self.gm_on); self.gb1.pack(side='left',expand=True,fill='x',padx=1)
        self.gb2=ttk.Button(bf,text='DISABLE',command=self.gm_off,state='disabled'); self.gb2.pack(side='left',expand=True,fill='x',padx=1)
        af=ttk.LabelFrame(f,text='Auto',padding=10); af.pack(fill='x',pady=8)
        self.av=tk.BooleanVar(value=self.config.get('auto',False)); ttk.Checkbutton(af,text='Auto-detect CS2/Valorant/Fortnite/Apex',variable=self.av,command=self.tog_auto).pack(anchor='w')
        hf=ttk.LabelFrame(f,text='Hotkey',padding=10); hf.pack(fill='x')
        ttk.Label(hf,text='Ctrl+Shift+G - Toggle from anywhere').pack(anchor='w')
    def build_tw(self):
        f=ttk.Frame(self.t_tw,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Windows Tweaks',font=('Segoe UI',11,'bold')).pack(anchor='w')
        pf=ttk.LabelFrame(f,text='Power',padding=10); pf.pack(fill='x')
        ttk.Button(pf,text='Ultimate Performance',command=self.upow).pack(fill='x',pady=1)
        ttk.Button(pf,text='High Performance',command=lambda:self.spow('8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c')).pack(fill='x',pady=1)
        sf=ttk.LabelFrame(f,text='Services',padding=10); sf.pack(fill='x',pady=8)
        ttk.Button(sf,text='Disable SysMain',command=self.dsys).pack(fill='x',pady=1)
        ttk.Button(sf,text='Disable Game Bar',command=self.dgb).pack(fill='x',pady=1)
        ttk.Button(sf,text='Disable Game DVR',command=self.ddvr).pack(fill='x',pady=1)
        ttk.Label(f,text='Run as Administrator',foreground='#d33').pack(pady=6)
    def build_la(self):
        f=ttk.Frame(self.t_la,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Quick Launcher',font=('Segoe UI',11,'bold')).pack(anchor='w')
        gf=ttk.LabelFrame(f,text='Games',padding=10); gf.pack(fill='x')
        ttk.Button(gf,text='CS2 (Steam)',command=lambda:self.lch('steam://rungameid/730')).pack(fill='x',pady=1)
        ttk.Button(gf,text='Valorant',command=lambda:self.lch('com.epicgames.launcher://apps/602ebecb84f84f87a6d7ed5f5a41d5c0?action=launch')).pack(fill='x',pady=1)
        af=ttk.LabelFrame(f,text='Apps',padding=10); af.pack(fill='x',pady=8)
        ttk.Button(af,text='Steam',command=lambda:self.lch('steam://open/main')).pack(fill='x',pady=1)
        ttk.Button(af,text='Epic Games',command=lambda:self.lch('com.epicgames.launcher://apps')).pack(fill='x',pady=1)
    def build_cs(self):
        f=ttk.Frame(self.t_cs,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='CS2 Tools',font=('Segoe UI',11,'bold')).pack(anchor='w')
        nb2=ttk.Notebook(f); nb2.pack(fill='both',expand=True)
        ta=ttk.Frame(nb2,padding=8); tc=ttk.Frame(nb2,padding=8); tl=ttk.Frame(nb2,padding=8)
        nb2.add(ta,text='Autoexec'); nb2.add(tc,text='Crosshair'); nb2.add(tl,text='Launch')
        fa=ttk.LabelFrame(ta,text='Generate',padding=8); fa.pack(fill='x')
        self.ccol=tk.StringVar(value='1'); ttk.Label(fa,text='cl_color').pack(anchor='w')
        ttk.Combobox(fa,textvariable=self.ccol,values=['0','1','2','3','4'],state='readonly').pack(fill='x')
        ttk.Button(fa,text='Save autoexec.cfg',command=self.gae).pack(fill='x',pady=4)
        fc=ttk.LabelFrame(tc,text='Crosshair',padding=8); fc.pack(fill='x')
        self.chc=tk.StringVar(value='1'); ttk.Combobox(fc,textvariable=self.chc,values=['0','1','2','3','4','5'],state='readonly').pack(fill='x')
        ttk.Button(fc,text='Generate & Copy',command=self.gch).pack(fill='x',pady=4)
        self.cho=tk.Text(fc,height=2,font=('Consolas',8)); self.cho.pack(fill='x')
        fl=ttk.LabelFrame(tl,text='Launch Options',padding=8); fl.pack(fill='x')
        self.lot=tk.Text(fl,height=2,font=('Consolas',9)); self.lot.pack(fill='x'); self.lot.insert('1.0','-high -novid -nojoy +fps_max 0')
        ttk.Button(fl,text='Copy',command=lambda:[self.clipboard_clear(),self.clipboard_append(self.lot.get('1.0',tk.END).strip()),messagebox.showinfo('Copied','Copied')]).pack(fill='x',pady=4)
    def build_oc(self):
        f=ttk.Frame(self.t_oc,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='One-Click & Focus Mode',font=('Segoe UI',11,'bold')).pack(anchor='w')
        ff=ttk.LabelFrame(f,text='FOCUS MODE',padding=12); ff.pack(fill='x')
        ttk.Label(ff,text='Ultimate gaming optimization').pack(anchor='w')
        self.fmb=ttk.Button(ff,text='ACTIVATE FOCUS MODE',command=self.fmon); self.fmb.pack(fill='x',pady=6)
        self.fml=ttk.Label(ff,text=''); self.fml.pack(anchor='w')
        of=ttk.LabelFrame(f,text='One-Click',padding=12); of.pack(fill='x',pady=10)
        ttk.Button(of,text='APPLY ALL OPTIMIZATIONS',command=self.ocall).pack(fill='x')
        self.ocl=ttk.Label(f,text='Ready'); self.ocl.pack(anchor='w',pady=4)
    def build_ut(self):
        f=ttk.Frame(self.t_ut,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Utilities',font=('Segoe UI',11,'bold')).pack(anchor='w')
        bf=ttk.LabelFrame(f,text='Break Timer',padding=10); bf.pack(fill='x')
        ttk.Label(bf,text='Remind every (min):').pack(anchor='w')
        self.bv=tk.StringVar(value='45'); ttk.Combobox(bf,textvariable=self.bv,values=['30','45','60'],state='readonly').pack(fill='x')
        self.btb=ttk.Button(bf,text='Start',command=self.bst); self.btb.pack(fill='x',pady=4)
        self.bl=ttk.Label(bf,text='Stopped'); self.bl.pack(anchor='w')
        sf=ttk.LabelFrame(f,text='Startup',padding=10); sf.pack(fill='x',pady=8)
        ttk.Button(sf,text='Add to Startup (Tray)',command=self.ast).pack(fill='x',pady=1)
        ttk.Button(sf,text='Remove',command=self.rst).pack(fill='x',pady=1)
    def build_in(self):
        f=ttk.Frame(self.t_in,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='XS2 Optimizer ULTRA',font=('Segoe UI',16,'bold')).pack()
        ttk.Label(f,text='All Features Included',foreground='#888').pack()
        ttk.Separator(f,orient='horizontal').pack(fill='x',pady=12)
        feats=['Hardware Monitor','Live Ping Graph','Process Priority Manager','Global Hotkey Ctrl+Shift+G',
               'Auto Game Mode','Quick Launcher','Focus Mode','Break Timer','System Tray','Run on Startup','One-Click']
        for x in feats: ttk.Label(f,text=f'• {x}').pack(anchor='w')
        ttk.Separator(f,orient='horizontal').pack(fill='x',pady=12)
        ttk.Label(f,text='Run as Administrator for full features',foreground='#d33').pack(anchor='w')
    def upd_all(self):
        self.upd_hw(); self.upd_monr(); self.upd_pr(); self.after(2000,self.upd_all)
    def upd_hw(self):
        try:
            self.hw_cpu.config(text=f'Usage: {psutil.cpu_percent(0)}% | Freq: {psutil.cpu_freq().current:.0f}MHz' if psutil.cpu_freq() else f'Usage: {psutil.cpu_percent(0)}%')
            m=psutil.virtual_memory(); self.hw_ram.config(text=f'Used: {m.used//(1024**3)}GB / {m.total//(1024**3)}GB ({m.percent}%)')
        except: pass
    def upd_monr(self):
        try:
            c=psutil.cpu_percent(0); m=psutil.virtual_memory(); self.m_cpu.config(text=f'CPU: {c}%'); self.m_ram.config(text=f'RAM: {m.used//(1024**3)}/{m.total//(1024**3)}GB ({m.percent}%)')
        except: pass
        self.upd_proc()
    def upd_proc(self):
        for i in self.pt.get_children(): self.pt.delete(i)
        procs=[]
        for p in psutil.process_iter(['name','pid','memory_info']):
            try: procs.append((p.info['name'],p.info['pid'],p.info['memory_info'].rss//(1024*1024)))
            except: pass
        procs.sort(key=lambda x:x[2],reverse=True)
        for n,pd,mm in procs[:40]: self.pt.insert('','end',values=(n,pd,mm))
    def killp(self):
        s=self.pt.selection()
        if not s: return
        try: psutil.Process(self.pt.item(s[0])['values'][1]).kill(); self.upd_proc()
        except: pass
    def prih(self): self.sp(psutil.HIGH_PRIORITY_CLASS)
    def wlp(self):
        s=self.pt.selection()
        if not s: return
        n=self.pt.item(s[0])['values'][0]
        if n not in self.whitelist: self.whitelist.append(n); self.save_cfg()
    def pg_start(self): self.ping_run=True; threading.Thread(target=self.pg_loop,daemon=True).start()
    def pg_stop(self): self.ping_run=False
    def pg_loop(self):
        while self.ping_run:
            try:
                o=subprocess.check_output('ping -n 1 8.8.8.8',shell=True,stderr=subprocess.STDOUT,timeout=3)
                s=o.decode('cp437',errors='ignore')
                import re
                m=re.search(r'time[<=](\d+)ms',s,re.I)
                if m:
                    v=int(m.group(1)); self.ping_hist.append(v); self.after(0,lambda x=v:self.pgd(x))
            except: pass
            time.sleep(1)
    def pgd(self,v):
        self.cv.delete('l')
        if not self.ping_hist: return
        w=self.cv.winfo_width() or 760
        h=160
        mx=max(max(self.ping_hist),50)
        pts=[]
        for i,xv in enumerate(self.ping_hist):
            pts.append((i*(w/30), h-(xv/mx*(h-30))-15))
        for i in range(len(pts)-1): self.cv.create_line(pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1],fill='#0f0',tags='l')
        if self.ping_hist: self.pl.config(text=f'Ping: {v}ms | Avg: {sum(self.ping_hist)/len(self.ping_hist):.1f}ms')
    def dnsf(self): subprocess.run('ipconfig /flushdns',shell=True); messagebox.showinfo('Done','Flushed')
    def dnss(self,d):
        try:
            subprocess.run(f'netsh interface ip set dns "Wi-Fi" static {d[0]}',shell=True)
            if len(d)>1: subprocess.run(f'netsh interface ip add dns "Wi-Fi" {d[1]} index=2',shell=True)
            messagebox.showinfo('Done','DNS updated')
        except: messagebox.showerror('Err','Run as Admin')
    def nr(self):
        if messagebox.askyesno('Confirm','Reset?'): [subprocess.run(x,shell=True) for x in ['netsh winsock reset','netsh int ip reset']]; messagebox.showinfo('Done','Restart')
    def upd_pr(self):
        for i in self.prt.get_children(): self.prt.delete(i)
        for p in psutil.process_iter(['name','pid']):
            try: proc=psutil.Process(p.info['pid']); pr=proc.nice(); ps='High' if pr==psutil.HIGH_PRIORITY_CLASS else 'Above' if pr==psutil.ABOVE_NORMAL_PRIORITY_CLASS else 'Normal'; self.prt.insert('','end',values=(p.info['name'],p.info['pid'],ps))
            except: pass
    def sp(self,pri):
        s=self.prt.selection()
        if not s: return
        try: psutil.Process(self.prt.item(s[0])['values'][1]).nice(pri); self.upd_pr()
        except Exception as e: messagebox.showerror('Err',str(e))
    def tog_auto(self): self.config['auto']=self.av.get(); self.save_cfg()
    def auto_chk(self):
        if self.config.get('auto') and not self.gm:
            games=['cs2.exe','valorant-win64-shipping.exe','FortniteClient-Win64-Shipping.exe','r5apex.exe']
            try:
                for p in psutil.process_iter(['name']):
                    if p.info['name'] in games: self.gm_on(); self.noti('Auto Game Mode','Enabled'); break
            except: pass
        self.after(5000,self.auto_chk)
    def gm_on(self):
        if self.gm: return
        tg=['chrome.exe','msedge.exe','firefox.exe','discord.exe','spotify.exe','steamwebhelper.exe','teams.exe','slack.exe','zoom.exe']
        for p in psutil.process_iter(['name']):
            try:
                n=p.info['name']
                if n.lower() in [x.lower() for x in tg] and n not in self.whitelist and 'xs2' not in n.lower(): p.kill()
            except: pass
        self.gm=True; self.gml.config(text='STATUS: ACTIVE',foreground='#2e7d32'); self.gb1.config(state='disabled'); self.gb2.config(state='normal')
    def gm_off(self):
        self.gm=False; self.gml.config(text='STATUS: INACTIVE',foreground='#d33'); self.gb1.config(state='normal'); self.gb2.config(state='disabled')
    def upow(self):
        try: subprocess.run('powercfg /duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61',shell=True); subprocess.run('powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749eb61',shell=True); messagebox.showinfo('Done','Enabled')
        except Exception as e: messagebox.showerror('Err',str(e))
    def spow(self,g):
        try: subprocess.run(f'powercfg /setactive {g}',shell=True); messagebox.showinfo('Done','Changed')
        except: pass
    def dsys(self):
        try: subprocess.run('sc stop "SysMain"',shell=True); subprocess.run('sc config "SysMain" start= disabled',shell=True); messagebox.showinfo('Done','Disabled')
        except: pass
    def dgb(self):
        try: subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f',shell=True); subprocess.run('reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f',shell=True); messagebox.showinfo('Done','Disabled')
        except: pass
    def ddvr(self):
        try: subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f',shell=True); messagebox.showinfo('Done','Disabled')
        except: pass
    def lch(self,u): 
        try: os.startfile(u)
        except: pass
    def gae(self):
        c=f'//XS2\ncl_color {self.ccol.get()}\nr_drawtracers_firstperson 0\nmat_queue_mode 2\nfps_max 0\n'
        p=filedialog.asksaveasfilename(defaultextension='.cfg',initialfile='autoexec.cfg')
        if p: open(p,'w').write(c); messagebox.showinfo('Saved','Saved')
    def gch(self):
        cmd=f'cl_crosshaircolor {self.chc.get()} cl_crosshairsize 2 cl_crosshairthickness 1 cl_crosshair_drawoutline 1'
        self.cho.delete('1.0',tk.END); self.cho.insert('1.0',cmd)
        self.clipboard_clear(); self.clipboard_append(cmd); messagebox.showinfo('Copied','Copied')
    def fmon(self):
        if self.fm: return
        self.fm=True; self.upow(); self.dsys(); self.dgb(); self.ddvr(); self.gm_on(); self.fml.config(text='FOCUS MODE ACTIVE',foreground='#2e7d32'); self.fmb.config(text='DEACTIVATE'); self.noti('Focus Mode','Activated')
    def fmoff(self):
        self.fm=False; self.spow('381b4222-f694-41f0-9685-ff5bb260df2e'); self.gm_off(); self.fml.config(text=''); self.fmb.config(text='ACTIVATE FOCUS MODE',command=self.fmon)
    def ocall(self):
        threading.Thread(target=self.oc_t,daemon=True).start()
    def oc_t(self):
        self.after(0,lambda:self.ocl.config(text='Optimizing...'))
        try:
            subprocess.run('powercfg /duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61',shell=True)
            subprocess.run('powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749eb61',shell=True)
            subprocess.run('sc stop "SysMain"',shell=True); subprocess.run('sc config "SysMain" start= disabled',shell=True)
            subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f',shell=True)
            subprocess.run('ipconfig /flushdns',shell=True)
            self.after(0,self.gm_on)
            self.after(0,lambda:self.ocl.config(text='Done!'))
            self.after(0,lambda:messagebox.showinfo('Done','Applied'))
        except: pass
    def bst(self):
        self.br=self.bv.get(); self.bt=datetime.now(); self.br_run=True; self.btb.config(text='Stop',command=self.bsp); self.bu()
    def bsp(self): self.br_run=False; self.btb.config(text='Start',command=self.bst); self.bl.config(text='Stopped')
    def bu(self):
        if not getattr(self,'br_run',False): return
        el=(datetime.now()-self.bt).total_seconds()/60; rem=int(self.br)-el
        if rem<=0: messagebox.showinfo('Break','Take a break!'); self.bt=datetime.now(); self.bl.config(text=f'Next in {self.br} min')
        else: self.bl.config(text=f'{rem:.0f} min remaining')
        self.after(60000,self.bu)
    def ast(self):
        try:
            k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run',0,winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k,'XS2ULTRA',0,winreg.REG_SZ,f'"{os.path.abspath(sys.argv[0])}"'); winreg.CloseKey(k); messagebox.showinfo('Done','Added')
        except Exception as e: messagebox.showerror('Err',str(e))
    def rst(self):
        try:
            k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run',0,winreg.KEY_SET_VALUE)
            winreg.DeleteValue(k,'XS2ULTRA'); winreg.CloseKey(k); messagebox.showinfo('Done','Removed')
        except Exception as e: messagebox.showerror('Err',str(e))
    def tray_init(self):
        def img():
            im=Image.new('RGB',(64,64),'black'); d=ImageDraw.Draw(im); d.rectangle([16,16,48,48],fill='red'); return im
        m=pystray.Menu(pystray.MenuItem('Show',self.showw),pystray.MenuItem('Toggle GM (Ctrl+Shift+G)',self.tgm),pystray.MenuItem('Focus Mode',self.tfm),pystray.MenuItem('Exit',self.exitp))
        self.tray=pystray.Icon('XS2',img(),'XS2 ULTRA',m); threading.Thread(target=self.tray.run,daemon=True).start()
    def showw(self,i=None,x=None): self.deiconify(); self.lift()
    def hide_tray(self): self.withdraw()
    def tgm(self,i=None,x=None): self.gm_on() if not self.gm else self.gm_off()
    def tfm(self,i=None,x=None): self.fmon() if not self.fm else self.fmoff()
    def exitp(self,i=None,x=None): 
        try: keyboard.unhook_all()
        except: pass
        if self.tray: self.tray.stop()
        self.destroy(); sys.exit()

if __name__=='__main__': App().mainloop()
