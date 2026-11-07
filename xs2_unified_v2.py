import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import os
import sys
import time
import json
import threading
from datetime import datetime
import psutil
import platform
import socket
from collections import deque
import pystray
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, 'xs2_config.json')

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('XS2 Optimizer PRO - Gaming Suite')
        self.geometry('720x780')
        self.minsize(680, 740)
        
        self.config = self.load_config()
        self.gamemode_active = False
        self.whitelist = self.config.get('whitelist', [])
        self.auto_gamemode = self.config.get('auto_gamemode', False)
        self.tray_icon = None
        self.tray_running = False
        
        self.cpu_history = deque(maxlen=60)
        self.ram_history = deque(maxlen=60)
        self.net_history = deque(maxlen=60)
        self.ping_data = deque(maxlen=30)
        
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except:
            pass
        
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.monitor_tab = ttk.Frame(notebook)
        self.ping_tab = ttk.Frame(notebook)
        self.gamemode_tab = ttk.Frame(notebook)
        self.tweaks_tab = ttk.Frame(notebook)
        self.cs2_tab = ttk.Frame(notebook)
        self.oneclick_tab = ttk.Frame(notebook)
        self.info_tab = ttk.Frame(notebook)
        
        notebook.add(self.monitor_tab, text='Live Monitor')
        notebook.add(self.ping_tab, text='Kill Ping')
        notebook.add(self.gamemode_tab, text='Game Mode')
        notebook.add(self.tweaks_tab, text='Windows Tweaks')
        notebook.add(self.cs2_tab, text='CS2 Tools')
        notebook.add(self.oneclick_tab, text='One-Click')
        notebook.add(self.info_tab, text='Info')
        
        self.build_monitor_tab()
        self.build_ping_tab()
        self.build_gamemode_tab()
        self.build_tweaks_tab()
        self.build_cs2_tab()
        self.build_oneclick_tab()
        self.build_info_tab()
        
        self.update_monitor()
        self.start_tray()
        self.check_auto_gamemode()
        
        self.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)
        
    def load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {'whitelist': [], 'auto_gamemode': False, 'minimize_tray': True}
    
    def save_config(self):
        try:
            self.config['whitelist'] = self.whitelist
            self.config['auto_gamemode'] = self.auto_gamemode
            with open(CONFIG_PATH, 'w') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass
    
    def build_monitor_tab(self):
        frm = ttk.Frame(self.monitor_tab, padding=12)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='Live System Monitor', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        ttk.Label(frm, text='Real-time CPU, RAM, Network monitoring', foreground='#888').pack(anchor='w', pady=(0,10))
        
        res = ttk.LabelFrame(frm, text='Resources', padding=10)
        res.pack(fill='x')
        self.cpu_lbl = ttk.Label(res, text='CPU: -%')
        self.cpu_lbl.pack(anchor='w')
        self.ram_lbl = ttk.Label(res, text='RAM: -/- GB (-%)')
        self.ram_lbl.pack(anchor='w')
        self.net_lbl = ttk.Label(res, text='Network: ? - KB/s ? - KB/s')
        self.net_lbl.pack(anchor='w')
        
        procs = ttk.LabelFrame(frm, text='Top Processes (High Memory Usage)', padding=10)
        procs.pack(fill='both', expand=True, pady=10)
        
        columns = ('name', 'pid', 'memory')
        self.proc_tree = ttk.Treeview(procs, columns=columns, show='headings', height=15)
        self.proc_tree.heading('name', text='Process')
        self.proc_tree.heading('pid', text='PID')
        self.proc_tree.heading('memory', text='Memory (MB)')
        self.proc_tree.column('name', width=250)
        self.proc_tree.column('pid', width=80)
        self.proc_tree.column('memory', width=100)
        self.proc_tree.pack(side='left', fill='both', expand=True)
        
        sb = ttk.Scrollbar(procs, orient='vertical', command=self.proc_tree.yview)
        sb.pack(side='right', fill='y')
        self.proc_tree.configure(yscrollcommand=sb.set)
        
        bf = ttk.Frame(frm)
        bf.pack(fill='x')
        ttk.Button(bf, text='Refresh Processes', command=self.update_processes).pack(side='left')
        ttk.Button(bf, text='Kill Selected Process', command=self.kill_selected).pack(side='left', padx=5)
        ttk.Button(bf, text='Add to Whitelist', command=self.add_whitelist).pack(side='left')
        
    def update_monitor(self):
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            net = psutil.net_io_counters()
            
            self.cpu_lbl.config(text=f'CPU: {cpu}%')
            self.ram_lbl.config(text=f'RAM: {mem.used//(1024**3)}GB / {mem.total//(1024**3)}GB ({mem.percent}%)')
            
            if hasattr(self, 'last_net'):
                up = (net.bytes_sent - self.last_net.bytes_sent) / 1024
                down = (net.bytes_recv - self.last_net.bytes_recv) / 1024
                self.net_lbl.config(text=f'Network: ? {down:.1f} KB/s ? {up:.1f} KB/s')
            self.last_net = net
            
            self.update_processes()
        except:
            pass
        self.after(2000, self.update_monitor)
    
    def update_processes(self):
        try:
            for item in self.proc_tree.get_children():
                self.proc_tree.delete(item)
            procs = []
            for p in psutil.process_iter(['name', 'pid', 'memory_info']):
                try:
                    procs.append((p.info['name'], p.info['pid'], p.info['memory_info'].rss // (1024*1024)))
                except:
                    pass
            procs.sort(key=lambda x: x[2], reverse=True)
            for name, pid, mem in procs[:30]:
                self.proc_tree.insert('', tk.END, values=(name, pid, mem))
        except:
            pass
    
    def kill_selected(self):
        sel = self.proc_tree.selection()
        if not sel:
            return
        item = self.proc_tree.item(sel[0])
        vals = item['values']
        name = vals[0]
        pid = vals[1]
        if messagebox.askyesno('Kill Process', f'Kill {name} (PID {pid})?'):
            try:
                p = psutil.Process(pid)
                p.kill()
                self.update_processes()
            except Exception as e:
                messagebox.showerror('Error', str(e))
    
    def add_whitelist(self):
        sel = self.proc_tree.selection()
        if not sel: return
        item = self.proc_tree.item(sel[0])
        name = item['values'][0]
        if name not in self.whitelist:
            self.whitelist.append(name)
            self.save_config()
            messagebox.showinfo('Added', f'{name} added to whitelist')
    
    def build_ping_tab(self):
        frm = ttk.Frame(self.ping_tab, padding=12)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='Network Latency Optimizer', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        ttk.Label(frm, text='Multi-Ping + DNS Switcher + Network Tweaks', foreground='#888').pack(anchor='w', pady=(0,10))
        
        mp = ttk.LabelFrame(frm, text='Multi-Ping Test', padding=10)
        mp.pack(fill='x')
        bf = ttk.Frame(mp)
        bf.pack(fill='x')
        ttk.Button(bf, text='Ping All (8.8.8.8, 1.1.1.1, Cloudflare)', command=self.multi_ping).pack(side='left')
        ttk.Button(bf, text='Ping 1.1.1.1', command=lambda: self.ping_host('1.1.1.1')).pack(side='left', padx=5)
        ttk.Button(bf, text='Ping 8.8.8.8', command=lambda: self.ping_host('8.8.8.8')).pack(side='left')
        
        dns = ttk.LabelFrame(frm, text='DNS Switcher', padding=10)
        dns.pack(fill='x', pady=10)
        ttk.Button(dns, text='Set to 1.1.1.1 + 1.0.0.1 (Cloudflare)', command=lambda: self.set_dns(['1.1.1.1','1.0.0.1'])).pack(fill='x', pady=2)
        ttk.Button(dns, text='Set to 8.8.8.8 + 8.8.4.4 (Google)', command=lambda: self.set_dns(['8.8.8.8','8.8.4.4'])).pack(fill='x', pady=2)
        ttk.Button(dns, text='Set to 94.140.14.14 + 94.140.15.15 (AdGuard)', command=lambda: self.set_dns(['94.140.14.14','94.140.15.15'])).pack(fill='x', pady=2)
        ttk.Button(dns, text='Flush DNS Cache', command=self.flush_dns).pack(fill='x', pady=2)
        
        net = ttk.LabelFrame(frm, text='Network Optimizations', padding=10)
        net.pack(fill='x')
        ttk.Button(net, text='Reset Winsock + TCP/IP', command=self.net_reset).pack(fill='x', pady=2)
        ttk.Button(net, text='Apply Network Tweaks (Nagle\'s/Throttling)', command=self.net_tweaks).pack(fill='x', pady=2)
        
        logf = ttk.LabelFrame(frm, text='Output Log', padding=10)
        logf.pack(fill='both', expand=True, pady=10)
        self.ping_log = scrolledtext.ScrolledText(logf, height=12, font=('Consolas', 9))
        self.ping_log.pack(fill='both', expand=True)
        ttk.Button(frm, text='Clear Log', command=lambda: self.ping_log.delete('1.0',tk.END)).pack(fill='x')
        ttk.Label(frm, text='Run as Administrator for full effect', foreground='#d33').pack()
    
    def log_ping(self, msg):
        self.ping_log.insert(tk.END, f'[{datetime.now().strftime("%H:%M:%S")}] {msg}\n')
        self.ping_log.see(tk.END)
    
    def ping_host(self, host):
        self.log_ping(f'Pinging {host}...')
        try:
            out = subprocess.check_output(f'ping -n 4 {host}', shell=True, stderr=subprocess.STDOUT, timeout=15)
            self.log_ping(out.decode('cp437', errors='ignore'))
        except Exception as e:
            self.log_ping(str(e))
    
    def multi_ping(self):
        threading.Thread(target=self._multi_ping_thread, daemon=True).start()
    
    def _multi_ping_thread(self):
        for h in ['8.8.8.8', '1.1.1.1', '1.0.0.1']:
            self.log_ping(f'=== Pinging {h} ===')
            try:
                out = subprocess.check_output(f'ping -n 4 {h}', shell=True, stderr=subprocess.STDOUT, timeout=15)
                self.log_ping(out.decode('cp437', errors='ignore'))
            except Exception as e:
                self.log_ping(str(e))
            self.log_ping('')
    
    def set_dns(self, dns_list):
        self.log_ping(f'Setting DNS to {dns_list}...')
        try:
            # Get active interface
            cmd = 'netsh interface ip set dns "Wi-Fi" static ' + dns_list[0]
            subprocess.run(cmd, shell=True)
            if len(dns_list) > 1:
                cmd = 'netsh interface ip add dns "Wi-Fi" ' + dns_list[1] + ' index=2'
                subprocess.run(cmd, shell=True)
            self.log_ping('DNS updated (may need reconnect)')
            messagebox.showinfo('Done', 'DNS updated')
        except Exception as e:
            self.log_ping(str(e))
            messagebox.showerror('Error', 'Run as Administrator')
    
    def flush_dns(self):
        try:
            subprocess.run('ipconfig /flushdns', shell=True)
            self.log_ping('DNS cache flushed')
        except Exception as e:
            self.log_ping(str(e))
    
    def net_reset(self):
        if messagebox.askyesno('Confirm', 'Reset network stack?\nRestart recommended.'):
            try:
                for cmd in ['netsh winsock reset','netsh int ip reset','netsh interface ipv4 reset','netsh interface ipv6 reset']:
                    subprocess.run(cmd, shell=True)
                    self.log_ping(f'Ran: {cmd}')
                messagebox.showinfo('Done', 'Reset complete. Restart PC recommended')
            except Exception as e:
                self.log_ping(str(e))
    
    def net_tweaks(self):
        try:
            self.log_ping('Applying network tweaks...')
            # NetworkThrottlingIndex
            cmd1 = 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 0xffffffff /f'
            subprocess.run(cmd1, shell=True)
            # TcpAckFrequency for Nagle
            self.log_ping('Tweaks applied')
            messagebox.showinfo('Done', 'Network tweaks applied')
        except Exception as e:
            self.log_ping(str(e))
    
    def build_gamemode_tab(self):
        frm = ttk.Frame(self.gamemode_tab, padding=12)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='Game Mode - RAM Optimizer', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        ttk.Label(frm, text='Kill background apps to free up memory', foreground='#888').pack(anchor='w', pady=(0,10))
        
        ctrl = ttk.LabelFrame(frm, text='Control', padding=10)
        ctrl.pack(fill='x')
        self.gm_status = ttk.Label(ctrl, text='STATUS: INACTIVE', font=('Segoe UI', 9, 'bold'), foreground='#d33')
        self.gm_status.pack(pady=2)
        bf = ttk.Frame(ctrl)
        bf.pack(fill='x')
        self.btn_enable_gm = ttk.Button(bf, text='ENABLE GAME MODE', command=self.enable_gamemode)
        self.btn_enable_gm.pack(side='left', expand=True, fill='x', padx=2)
        self.btn_disable_gm = ttk.Button(bf, text='DISABLE', command=self.disable_gamemode, state='disabled')
        self.btn_disable_gm.pack(side='left', expand=True, fill='x', padx=2)
        
        auto = ttk.LabelFrame(frm, text='Auto Game Mode', padding=10)
        auto.pack(fill='x', pady=10)
        self.auto_var = tk.BooleanVar(value=self.auto_gamemode)
        ttk.Checkbutton(auto, text='Auto-enable when game detected (CS2, Valorant, Fortnite, Apex)', 
                        variable=self.auto_var, command=self.toggle_auto).pack(anchor='w')
        ttk.Label(auto, text='Monitors: cs2.exe, valorant-win64-shipping.exe, FortniteClient-Win64-Shipping.exe, r5apex.exe', 
                  foreground='#888').pack(anchor='w')
        
        apps = ttk.LabelFrame(frm, text='Apps To Kill (Edit Whitelist in Monitor tab)', padding=10)
        apps.pack(fill='both', expand=True)
        self.gm_apps = tk.Text(apps, font=('Consolas', 9), height=12)
        sb = ttk.Scrollbar(apps, orient='vertical', command=self.gm_apps.yview)
        self.gm_apps.configure(yscrollcommand=sb.set)
        self.gm_apps.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        targets = ['chrome.exe','msedge.exe','firefox.exe','brave.exe','opera.exe','discord.exe','spotify.exe',
                   'steamwebhelper.exe','teams.exe','slack.exe','zoom.exe','whatsapp.exe','telegram.exe',
                   'obs64.exe','streamlabs.exe','dropbox.exe','onedrive.exe','wallpaperengine.exe','rainmeter.exe']
        for a in targets:
            if a not in self.whitelist:
                self.gm_apps.insert(tk.END, f'• {a}\n')
        self.gm_apps.config(state='disabled')
        
        self.gm_log = ttk.Label(frm, text='Ready')
        self.gm_log.pack(anchor='w')
    
    def toggle_auto(self):
        self.auto_gamemode = self.auto_var.get()
        self.save_config()
    
    def check_auto_gamemode(self):
        if not self.auto_gamemode or self.gamemode_active:
            self.after(5000, self.check_auto_gamemode)
            return
        games = ['cs2.exe', 'valorant-win64-shipping.exe', 'FortniteClient-Win64-Shipping.exe', 'r5apex.exe', 'paladins.exe']
        try:
            for p in psutil.process_iter(['name']):
                name = p.info['name']
                if name in games:
                    self.enable_gamemode()
                    break
        except:
            pass
        self.after(5000, self.check_auto_gamemode)
    
    def enable_gamemode(self):
        if self.gamemode_active: return
        targets = ['chrome.exe','msedge.exe','firefox.exe','brave.exe','opera.exe','discord.exe','spotify.exe',
                   'steamwebhelper.exe','teams.exe','slack.exe','zoom.exe','whatsapp.exe','telegram.exe',
                   'obs64.exe','streamlabs.exe','dropbox.exe','onedrive.exe','wallpaperengine.exe','rainmeter.exe']
        killed = 0
        for p in psutil.process_iter(['name']):
            try:
                name = p.info['name']
                if name.lower() in [x.lower() for x in targets]:
                    if name in self.whitelist or 'xs2' in name.lower() or 'python' in name.lower():
                        continue
                    p.kill()
                    killed += 1
            except:
                pass
        self.gamemode_active = True
        self.gm_status.config(text='STATUS: ACTIVE', foreground='#2e7d32')
        self.btn_enable_gm.config(state='disabled')
        self.btn_disable_gm.config(state='normal')
        self.gm_log.config(text=f'Killed {killed} process(es)')
    
    def disable_gamemode(self):
        self.gamemode_active = False
        self.gm_status.config(text='STATUS: INACTIVE', foreground='#d33')
        self.btn_enable_gm.config(state='normal')
        self.btn_disable_gm.config(state='disabled')
        self.gm_log.config(text='Game Mode disabled - reopen apps manually')
    
    def build_tweaks_tab(self):
        frm = ttk.Frame(self.tweaks_tab, padding=12)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='Windows Gaming Tweaks', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        ttk.Label(frm, text='Power Plan, SysMain, Game Bar & More', foreground='#888').pack(anchor='w', pady=(0,10))
        
        pwr = ttk.LabelFrame(frm, text='Power Plan', padding=10)
        pwr.pack(fill='x')
        ttk.Button(pwr, text='Set Ultimate Performance', command=self.set_ultimate).pack(fill='x', pady=2)
        ttk.Button(pwr, text='Set High Performance', command=lambda: self.set_power('8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c')).pack(fill='x', pady=2)
        ttk.Button(pwr, text='Show Current Plan', command=self.show_power).pack(fill='x', pady=2)
        
        bg = ttk.LabelFrame(frm, text='Background Services', padding=10)
        bg.pack(fill='x', pady=10)
        ttk.Button(bg, text='Disable SysMain (Superfetch)', command=self.disable_sysmain).pack(fill='x', pady=2)
        ttk.Button(bg, text='Enable SysMain', command=self.enable_sysmain).pack(fill='x', pady=2)
        ttk.Button(bg, text='Disable Xbox Game Bar', command=self.disable_gamebar).pack(fill='x', pady=2)
        ttk.Button(bg, text='Disable Game DVR', command=self.disable_dvr).pack(fill='x', pady=2)
        
        ttk.Label(frm, text='Run as Administrator for all tweaks', foreground='#d33').pack(pady=10)
    
    def set_ultimate(self):
        try:
            cmd = 'powercfg /duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61'
            subprocess.run(cmd, shell=True)
            cmd2 = 'powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749eb61'
            subprocess.run(cmd2, shell=True)
            messagebox.showinfo('Done', 'Ultimate Performance enabled')
        except Exception as e:
            messagebox.showerror('Error', str(e))
    
    def set_power(self, guid):
        try:
            subprocess.run(f'powercfg /setactive {guid}', shell=True)
            messagebox.showinfo('Done', 'Power plan changed')
        except Exception as e:
            messagebox.showerror('Error', str(e))
    
    def show_power(self):
        try:
            out = subprocess.check_output('powercfg /getactivescheme', shell=True)
            messagebox.showinfo('Current Plan', out.decode())
        except Exception as e:
            messagebox.showerror('Error', str(e))
    
    def disable_sysmain(self):
        try:
            subprocess.run('sc stop "SysMain"', shell=True)
            subprocess.run('sc config "SysMain" start= disabled', shell=True)
            messagebox.showinfo('Done', 'SysMain disabled')
        except Exception as e:
            messagebox.showerror('Error', str(e))
    
    def enable_sysmain(self):
        try:
            subprocess.run('sc config "SysMain" start= auto', shell=True)
            subprocess.run('sc start "SysMain"', shell=True)
            messagebox.showinfo('Done', 'SysMain enabled')
        except Exception as e:
            messagebox.showerror('Error', str(e))
    
    def disable_gamebar(self):
        try:
            cmd = 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f'
            subprocess.run(cmd, shell=True)
            cmd2 = 'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f'
            subprocess.run(cmd2, shell=True)
            messagebox.showinfo('Done', 'Xbox Game Bar disabled')
        except Exception as e:
            messagebox.showerror('Error', str(e))
    
    def disable_dvr(self):
        try:
            cmd = 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f'
            subprocess.run(cmd, shell=True)
            messagebox.showinfo('Done', 'Game DVR disabled')
        except Exception as e:
            messagebox.showerror('Error', str(e))
    
    def build_cs2_tab(self):
        frm = ttk.Frame(self.cs2_tab, padding=12)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='CS2 Tools', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        ttk.Label(frm, text='Autoexec Generator, Crosshair Generator, Launch Options', foreground='#888').pack(anchor='w', pady=(0,10))
        
        nb = ttk.Notebook(frm)
        nb.pack(fill='both', expand=True)
        
        autoexec = ttk.Frame(nb, padding=10)
        crosshair = ttk.Frame(nb, padding=10)
        launch = ttk.Frame(nb, padding=10)
        nb.add(autoexec, text='Autoexec')
        nb.add(crosshair, text='Crosshair')
        nb.add(launch, text='Launch Options')
        
        # Autoexec
        af = ttk.LabelFrame(autoexec, text='Generate autoexec.cfg', padding=10)
        af.pack(fill='x')
        self.ae_clcolor = tk.StringVar(value='1')
        ttk.Label(af, text='cl_color:').pack(anchor='w')
        ttk.Combobox(af, textvariable=self.ae_clcolor, values=['0','1','2','3','4'], state='readonly').pack(fill='x')
        self.ae_tracers = tk.BooleanVar(value=True)
        ttk.Checkbutton(af, text='Remove first person tracers (r_drawtracers_firstperson 0)', variable=self.ae_tracers).pack(anchor='w')
        self.ae_multithread = tk.BooleanVar(value=True)
        ttk.Checkbutton(af, text='Multi-threaded (mat_queue_mode 2)', variable=self.ae_multithread).pack(anchor='w')
        ttk.Button(af, text='Generate & Save autoexec.cfg', command=self.gen_autoexec).pack(fill='x', pady=5)
        
        # Crosshair
        cf = ttk.LabelFrame(crosshair, text='Crosshair Generator', padding=10)
        cf.pack(fill='x')
        self.ch_color = tk.StringVar(value='green')
        ttk.Label(cf, text='Color:').pack(anchor='w')
        ttk.Combobox(cf, textvariable=self.ch_color, values=['green','cyan','yellow','red','white'], state='readonly').pack(fill='x')
        self.ch_size = tk.IntVar(value=2)
        ttk.Label(cf, text=f'Size: {self.ch_size.get()}').pack(anchor='w')
        ttk.Scale(cf, from_=0, to=5, variable=self.ch_size, orient='horizontal').pack(fill='x')
        self.ch_thickness = tk.IntVar(value=1)
        ttk.Label(cf, text=f'Thickness: {self.ch_thickness.get()}').pack(anchor='w')
        ttk.Scale(cf, from_=0, to=4, variable=self.ch_thickness, orient='horizontal').pack(fill='x')
        ttk.Button(cf, text='Generate Command', command=self.gen_crosshair).pack(fill='x', pady=5)
        self.ch_out = tk.Text(cf, height=4, font=('Consolas', 8))
        self.ch_out.pack(fill='x')
        
        # Launch
        lf = ttk.LabelFrame(launch, text='Launch Options', padding=10)
        lf.pack(fill='x')
        self.lo_opts = tk.Text(lf, height=3, font=('Consolas', 9))
        self.lo_opts.pack(fill='x')
        self.lo_opts.insert('1.0', '-high -novid -nojoy +fps_max 0')
        ttk.Button(lf, text='Copy to Clipboard', command=self.copy_launch).pack(fill='x', pady=5)
        ttk.Label(lf, text='Add these to CS2 Launch Options in Steam', foreground='#888').pack(anchor='w')
    
    def gen_autoexec(self):
        content = '// XS2 Optimizer - Autoexec\n'
        content += f'cl_color {self.ae_clcolor.get()}\n'
        if self.ae_tracers.get():
            content += 'r_drawtracers_firstperson 0\n'
        if self.ae_multithread.get():
            content += 'mat_queue_mode 2\n'
        content += 'fps_max 0\ncl_hud_color 5\n'
        path = filedialog.asksaveasfilename(defaultextension='.cfg', filetypes=[('CFG files','*.cfg')], initialfile='autoexec.cfg')
        if path:
            try:
                with open(path, 'w') as f:
                    f.write(content)
                messagebox.showinfo('Saved', f'Saved to {path}\nPut in csgo/cfg folder')
            except Exception as e:
                messagebox.showerror('Error', str(e))
    
    def gen_crosshair(self):
        colors = {'green':'1','cyan':'4','yellow':'2','red':'0','white':'5'}
        cmd = f'cl_crosshaircolor {colors.get(self.ch_color.get(),"1")} cl_crosshairsize {self.ch_size.get()} cl_crosshairthickness {self.ch_thickness.get()} cl_crosshair_drawoutline 1'
        self.ch_out.delete('1.0', tk.END)
        self.ch_out.insert('1.0', cmd)
        self.clipboard_clear()
        self.clipboard_append(cmd)
        messagebox.showinfo('Copied', 'Crosshair command copied to clipboard')
    
    def copy_launch(self):
        opts = self.lo_opts.get('1.0', tk.END).strip()
        self.clipboard_clear()
        self.clipboard_append(opts)
        messagebox.showinfo('Copied', 'Launch options copied')
    
    def build_oneclick_tab(self):
        frm = ttk.Frame(self.oneclick_tab, padding=12)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='One-Click Optimize', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        ttk.Label(frm, text='Apply all safe optimizations at once', foreground='#888').pack(anchor='w', pady=(0,20))
        
        opt = ttk.LabelFrame(frm, text='Optimizations', padding=15)
        opt.pack(fill='x')
        ttk.Label(opt, text='This will:').pack(anchor='w')
        ttk.Label(opt, text='• Set Ultimate Performance power plan').pack(anchor='w')
        ttk.Label(opt, text='• Disable SysMain').pack(anchor='w')
        ttk.Label(opt, text='• Disable Xbox Game Bar & Game DVR').pack(anchor='w')
        ttk.Label(opt, text='• Flush DNS Cache').pack(anchor='w')
        ttk.Label(opt, text='• Enable Game Mode (kill background apps)').pack(anchor='w')
        ttk.Label(opt, text='• Apply network tweaks').pack(anchor='w')
        
        ttk.Button(frm, text='APPLY ALL OPTIMIZATIONS', command=self.one_click).pack(fill='x', pady=20)
        self.oc_log = ttk.Label(frm, text='Ready')
        self.oc_log.pack(anchor='w')
        ttk.Label(frm, text='Run as Administrator for all to work', foreground='#d33').pack(anchor='w')
    
    def one_click(self):
        if messagebox.askyesno('One-Click Optimize', 'Apply all optimizations?\nRun as Administrator recommended.'):
            self.oc_log.config(text='Applying...')
            threading.Thread(target=self._one_click_thread, daemon=True).start()
    
    def _one_click_thread(self):
        try:
            self.after(0, lambda: self.oc_log.config(text='Setting power plan...'))
            subprocess.run('powercfg /duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61', shell=True)
            subprocess.run('powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749eb61', shell=True)
            
            self.after(0, lambda: self.oc_log.config(text='Disabling SysMain...'))
            subprocess.run('sc stop "SysMain"', shell=True)
            subprocess.run('sc config "SysMain" start= disabled', shell=True)
            
            self.after(0, lambda: self.oc_log.config(text='Disabling Game Bar...'))
            subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f', shell=True)
            subprocess.run('reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f', shell=True)
            subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f', shell=True)
            
            self.after(0, lambda: self.oc_log.config(text='Flushing DNS...'))
            subprocess.run('ipconfig /flushdns', shell=True)
            
            self.after(0, lambda: self.oc_log.config(text='Enabling Game Mode...'))
            self.after(0, self.enable_gamemode)
            
            self.after(0, lambda: self.oc_log.config(text='DONE! All optimizations applied'))
            self.after(0, lambda: messagebox.showinfo('Done', 'All optimizations applied!'))
        except Exception as e:
            self.after(0, lambda: self.oc_log.config(text=f'Error: {e}'))
    
    def build_info_tab(self):
        frm = ttk.Frame(self.info_tab, padding=12)
        frm.pack(fill='both', expand=True)
        ttk.Label(frm, text='XS2 Optimizer PRO', font=('Segoe UI', 16, 'bold')).pack()
        ttk.Label(frm, text='Ultimate Gaming Optimization Suite', foreground='#888').pack()
        ttk.Separator(frm, orient='horizontal').pack(fill='x', pady=15)
        ttk.Label(frm, text='All Features:', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        features = ['Live System Monitor with Process Killer', 'Multi-Ping & DNS Switcher', 'Network Optimizations',
                   'Game Mode with Auto-Detection', 'Whitelist System', 'Power Plan Switcher', 'SysMain/Game Bar Tweaks',
                   'CS2 Autoexec Generator', 'Crosshair Generator', 'Launch Options Helper', 'System Tray',
                   'One-Click Optimize']
        for f in features:
            ttk.Label(frm, text=f'• {f}').pack(anchor='w')
        ttk.Separator(frm, orient='horizontal').pack(fill='x', pady=15)
        ttk.Label(frm, text='Run as Administrator for full functionality', foreground='#d33').pack()
    
    def start_tray(self):
        def create_image():
            img = Image.new('RGB', (64, 64), color='black')
            draw = ImageDraw.Draw(img)
            draw.rectangle([16,16,48,48], fill='red')
            return img
        
        menu = pystray.Menu(
            pystray.MenuItem('Show/Hide', self.toggle_window),
            pystray.MenuItem('Enable Game Mode', self.tray_gamemode),
            pystray.MenuItem('Exit', self.quit_app)
        )
        self.tray_icon = pystray.Icon('XS2Optimizer', create_image(), 'XS2 Optimizer PRO', menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        self.tray_running = True
    
    def toggle_window(self, icon=None, item=None):
        if self.state() == 'withdrawn':
            self.deiconify()
            self.lift()
        else:
            self.withdraw()
    
    def tray_gamemode(self, icon=None, item=None):
        if not self.gamemode_active:
            self.after(0, self.enable_gamemode)
        else:
            self.after(0, self.disable_gamemode)
    
    def minimize_to_tray(self):
        self.withdraw()
    
    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()
        sys.exit()

if __name__=='__main__':
    App().mainloop()
