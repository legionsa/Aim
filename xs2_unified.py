import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import sys
import time
import json
import threading
import psutil
import winreg

BASE = os.path.dirname(os.path.abspath(__file__))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('XS2 Optimizer - Gaming Suite')
        self.geometry('620x680')
        self.minsize(580, 640)
        
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except:
            pass
        
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tabs
        self.ping_tab = ttk.Frame(notebook)
        self.gamemode_tab = ttk.Frame(notebook)
        self.cs2_tab = ttk.Frame(notebook)
        self.info_tab = ttk.Frame(notebook)
        
        notebook.add(self.ping_tab, text='Kill Ping')
        notebook.add(self.gamemode_tab, text='Game Mode')
        notebook.add(self.cs2_tab, text='CS2 Visuals')
        notebook.add(self.info_tab, text='Info')
        
        self.build_ping_tab()
        self.build_gamemode_tab()
        self.build_cs2_tab()
        self.build_info_tab()
        
    def build_ping_tab(self):
        frm = ttk.Frame(self.ping_tab, padding=12)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='Network Latency Optimizer', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        ttk.Label(frm, text='Flush DNS, optimize TCP stack to reduce ping', foreground='#888').pack(anchor='w', pady=(0,10))
        
        status = ttk.LabelFrame(frm, text='Quick Actions', padding=10)
        status.pack(fill='x', pady=5)
        ttk.Button(status, text='Test Ping (8.8.8.8)', command=self.test_ping).pack(fill='x', pady=2)
        ttk.Button(status, text='Flush DNS Cache', command=self.flush_dns).pack(fill='x', pady=2)
        ttk.Button(status, text='Reset Winsock + TCP/IP', command=self.net_reset).pack(fill='x', pady=2)
        ttk.Button(status, text='Apply TCP Optimizations', command=self.tcp_opt).pack(fill='x', pady=2)
        
        logf = ttk.LabelFrame(frm, text='Output Log', padding=10)
        logf.pack(fill='both', expand=True, pady=5)
        self.ping_log = scrolledtext.ScrolledText(logf, height=14, font=('Consolas', 9))
        self.ping_log.pack(fill='both', expand=True)
        ttk.Button(frm, text='Clear Log', command=lambda: self.ping_log.delete('1.0',tk.END)).pack(fill='x', pady=2)
        ttk.Label(frm, text='Run as Administrator for full effect', foreground='#d33').pack()
    
    def log_ping(self, msg):
        self.ping_log.insert(tk.END, f'[{time.strftime("%H:%M:%S")}] {msg}\n')
        self.ping_log.see(tk.END)
        self.update_idletasks()
    
    def test_ping(self):
        self.log_ping('Testing...')
        try:
            out = subprocess.check_output('ping -n 4 8.8.8.8', shell=True, stderr=subprocess.STDOUT, timeout=15)
            self.log_ping(out.decode('cp437', errors='ignore'))
        except Exception as e:
            self.log_ping(str(e))
    
    def flush_dns(self):
        try:
            subprocess.run('ipconfig /flushdns', shell=True)
            self.log_ping('DNS cache flushed')
        except Exception as e:
            self.log_ping(str(e))
    
    def net_reset(self):
        if messagebox.askyesno('Confirm', 'This will reset network stack.\nRestart recommended after.\nContinue?'):
            try:
                for cmd in ['netsh winsock reset','netsh int ip reset','netsh interface ipv4 reset','netsh interface ipv6 reset']:
                    subprocess.run(cmd, shell=True)
                    self.log_ping(f'Ran: {cmd}')
                messagebox.showinfo('Done', 'Done. Restart PC for best results')
            except Exception as e:
                self.log_ping(str(e))
    
    def tcp_opt(self):
        try:
            cmd = 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DeliveryOptimization\\Config" /v DODownloadMode /t REG_DWORD /d 0 /f'
            subprocess.run(cmd, shell=True)
            self.log_ping('TCP/Delivery Optimization adjusted')
            messagebox.showinfo('Done', 'Applied')
        except Exception as e:
            self.log_ping(str(e))
    
    def build_gamemode_tab(self):
        frm = ttk.Frame(self.gamemode_tab, padding=12)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='Game Mode - Free Up RAM', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        ttk.Label(frm, text='Kill memory hungry apps before gaming', foreground='#888').pack(anchor='w', pady=(0,10))
        
        res = ttk.LabelFrame(frm, text='System Resources', padding=10)
        res.pack(fill='x')
        self.res_lbl = ttk.Label(res, text='-')
        self.res_lbl.pack(anchor='w')
        self.update_res()
        
        ctrl = ttk.LabelFrame(frm, text='Control', padding=10)
        ctrl.pack(fill='x', pady=10)
        self.gm_status = ttk.Label(ctrl, text='STATUS: INACTIVE', font=('Segoe UI', 9, 'bold'), foreground='#d33')
        self.gm_status.pack(pady=2)
        bf = ttk.Frame(ctrl)
        bf.pack(fill='x')
        self.btn_enable = ttk.Button(bf, text='ENABLE GAME MODE', command=self.enable_gm)
        self.btn_enable.pack(side='left', expand=True, fill='x', padx=2)
        self.btn_disable = ttk.Button(bf, text='DISABLE', command=self.disable_gm, state='disabled')
        self.btn_disable.pack(side='left', expand=True, fill='x', padx=2)
        
        apps = ttk.LabelFrame(frm, text='Apps To Kill', padding=10)
        apps.pack(fill='both', expand=True, pady=5)
        self.apps_txt = tk.Text(apps, font=('Consolas', 9))
        sb = ttk.Scrollbar(apps, orient='vertical', command=self.apps_txt.yview)
        self.apps_txt.configure(yscrollcommand=sb.set)
        self.apps_txt.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        for a in ['chrome.exe','msedge.exe','firefox.exe','brave.exe','discord.exe','spotify.exe','steamwebhelper.exe','teams.exe','slack.exe','zoom.exe','whatsapp.exe','telegram.exe','obs64.exe','streamlabs.exe','dropbox.exe','onedrive.exe','wallpaperengine.exe','rainmeter.exe']:
            self.apps_txt.insert(tk.END, f'• {a}\n')
        self.apps_txt.config(state='disabled')
        
        self.gm_log = ttk.Label(frm, text='Ready')
        self.gm_log.pack(anchor='w')
        ttk.Label(frm, text='Note: Closed apps must be reopened manually', foreground='#b8860b').pack(anchor='w')
    
    def update_res(self):
        try:
            m = psutil.virtual_memory()
            c = psutil.cpu_percent(interval=0)
            self.res_lbl.config(text=f'RAM: {m.used//(1024**3)}GB / {m.total//(1024**3)}GB ({m.percent}%)    CPU: {c}%')
        except:
            pass
        self.after(2000, self.update_res)
    
    def enable_gm(self):
        if messagebox.askyesno('Game Mode', 'Kill the listed apps?\nUnsaved work may be lost.'):
            killed = []
            targets = ['chrome.exe','msedge.exe','firefox.exe','brave.exe','discord.exe','spotify.exe','steamwebhelper.exe','teams.exe','slack.exe','zoom.exe','whatsapp.exe','telegram.exe','obs64.exe','streamlabs.exe','dropbox.exe','onedrive.exe','wallpaperengine.exe','rainmeter.exe']
            for p in psutil.process_iter(['name']):
                try:
                    n = p.info['name'].lower()
                    if n in [x.lower() for x in targets]:
                        if any(x in n for x in ['xs2','optimizer','python']):
                            continue
                        p.kill()
                        killed.append(p.info['name'])
                except:
                    pass
            self.gm_status.config(text='STATUS: ACTIVE', foreground='#2e7d32')
            self.btn_enable.config(state='disabled')
            self.btn_disable.config(state='normal')
            self.gm_log.config(text=f'Killed {len(killed)} process(es)')
    
    def disable_gm(self):
        self.gm_status.config(text='STATUS: INACTIVE', foreground='#d33')
        self.btn_enable.config(state='normal')
        self.btn_disable.config(state='disabled')
        self.gm_log.config(text='Game Mode disabled - reopen apps manually')
    
    def build_cs2_tab(self):
        frm = ttk.Frame(self.cs2_tab, padding=12)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='CS2 Visual Optimizer - Spot Enemies Easier', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        ttk.Label(frm, text='Settings for better visibility & contrast', foreground='#888').pack(anchor='w', pady=(0,10))
        
        nb = ttk.Notebook(frm)
        nb.pack(fill='both', expand=True)
        
        v = ttk.Frame(nb, padding=10)
        c = ttk.Frame(nb, padding=10)
        cmd = ttk.Frame(nb, padding=10)
        gpu = ttk.Frame(nb, padding=10)
        nb.add(v,text='Video')
        nb.add(c,text='Colors')
        nb.add(cmd,text='Console')
        nb.add(gpu,text='GPU')
        
        # Video
        vf = ttk.LabelFrame(v, text='In-Game Video Settings', padding=10)
        vf.pack(fill='x')
        for s,vv,n in [('Resolution','Native (1920x1080)','Best clarity'),('Display Mode','Fullscreen','Less input lag'),('Refresh Rate','Max','Smoother'),('V-Sync','Disabled','Less input lag'),('Brightness','90-100%','Adjust to preference'),('Contrast','110-120%','Higher = easier to spot'),('Color Mode','Computer Monitor','More vibrant'),('Boost Player Contrast','ENABLED','MOST IMPORTANT'),('Motion Blur','Disabled','Cleaner'),('Shadows','Low/Very Low','Better visibility'),('Effects','Low','Better visibility'),('Anti-Aliasing','Off','Better performance/clarity')]:
            r=ttk.Frame(vf); r.pack(fill='x')
            ttk.Label(r,text=f'• {s}:',width=22).pack(side='left')
            ttk.Label(r,text=vv,foreground='#2e7d32').pack(side='left')
            if n: ttk.Label(r,text=f' ({n})',foreground='#888').pack(side='left')
        
        # Colors
        cf = ttk.LabelFrame(c, text='Enemy Color Recommendations', padding=10)
        cf.pack(fill='x')
        for name,desc,cl in [('Normal','Default','cl_color 0'),('Yellow/Cyan (Recommended)','Best for most maps','cl_color 1 or 2'),('Colorblind - Protanopia','Red-weak','cl_color 2'),('Colorblind - Deuteranopia','Green-weak','cl_color 1'),('Colorblind - Tritanopia','Blue-weak','cl_color 3')]:
            r=ttk.Frame(cf); r.pack(fill='x',pady=1)
            ttk.Label(r,text=f'{name} - {desc}',width=40).pack(side='left')
            ttk.Label(r,text=cl,foreground='#1976d2',font=('Consolas',9)).pack(side='left')
        ttk.Label(c,text='Tip: Try cl_color 1 first - Yellow enemies pop on most CS2 maps',foreground='#b8860b').pack(anchor='w',pady=5)
        
        # Console
        cmf = ttk.LabelFrame(cmd, text='Add to autoexec.cfg', padding=10)
        cmf.pack(fill='x')
        txt = tk.Text(cmf,height=8,font=('Consolas',9))
        txt.pack(fill='x')
        txt.insert('1.0','// XS2 Optimizer - CS2 Autoexec\ncl_color 1\nr_drawtracers_firstperson 0\nmat_queue_mode 2\nfps_max 0\ncl_hud_color 5\n')
        txt.config(state='disabled')
        
        # GPU
        g1 = ttk.LabelFrame(gpu,text='NVIDIA Control Panel',padding=10)
        g1.pack(fill='x')
        for t in ['Image Sharpening: On','Digital Vibrance: +10 to +15','Low Latency Mode: On/Ultra','Power Management: Prefer Maximum Performance','Triple Buffering: Off']:
            ttk.Label(g1,text=f'• {t}').pack(anchor='w')
        g2 = ttk.LabelFrame(gpu,text='AMD Radeon Software',padding=10)
        g2.pack(fill='x',pady=5)
        for t in ['Radeon Image Sharpening: On','Saturate: +5 to +10','Radeon Anti-Lag: Enabled','Radeon Chill: Disabled','Wait for Vertical Refresh: Off']:
            ttk.Label(g2,text=f'• {t}').pack(anchor='w')
    
    def build_info_tab(self):
        frm = ttk.Frame(self.info_tab, padding=12)
        frm.pack(fill='both', expand=True)
        ttk.Label(frm,text='XS2 Optimizer',font=('Segoe UI',14,'bold')).pack()
        ttk.Label(frm,text='Gaming Optimization Suite for CS2 & FPS Games',foreground='#888').pack()
        ttk.Separator(frm,orient='horizontal').pack(fill='x',pady=15)
        ttk.Label(frm,text='Features:',font=('Segoe UI',10,'bold')).pack(anchor='w')
        for f in ['• Kill Ping - Network latency reduction','• Game Mode - Free up RAM by killing background apps','• CS2 Visuals - Better enemy visibility settings']:
            ttk.Label(frm,text=f).pack(anchor='w')
        ttk.Separator(frm,orient='horizontal').pack(fill='x',pady=15)
        ttk.Label(frm,text='Tips:',font=('Segoe UI',10,'bold')).pack(anchor='w')
        for f in ['1. Enable Game Mode before launching CS2','2. Run as Administrator for network optimizations','3. Enable Boost Player Contrast in CS2 video settings','4. Use Yellow enemy color (cl_color 1)']:
            ttk.Label(frm,text=f,wraplength=550).pack(anchor='w')
        ttk.Label(frm,text='\nMade for competitive gaming',foreground='#888').pack(pady=20)

if __name__=='__main__':
    App().mainloop()
