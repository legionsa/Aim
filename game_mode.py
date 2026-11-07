import json
import os
import time
import threading
import psutil
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, 'gamemode_config.json')

# Apps to kill for gaming
APPS_TO_KILL = [
    'chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe', 'opera.exe', 'vivaldi.exe',
    'discord.exe', 'spotify.exe', 'musicbee.exe', 'foobar2000.exe',
    'steamwebhelper.exe', 'epicwebhelper.exe',
    'teams.exe', 'slack.exe', 'zoom.exe', 'skype.exe',
    'dropbox.exe', 'onedrive.exe', 'googledrivesync.exe',
    'ms-teams.exe', 'msteams.exe',
    'whatsapp.exe', 'telegram.exe', 'signal.exe',
    'obs64.exe', 'obs32.exe', 'streamlabs.exe', 'xsplit.core.exe',
    'wallpaperengine.exe', 'rainmeter.exe', 'lively.exe',
    'adobecreativecloud.exe', 'creativecloud.exe',
    'battle.net.exe', 'eaapp.exe'
]

class GameMode:
    def __init__(self):
        self.active = False
        self.killed_processes = []
        self.config = self.load_config()
        
    def load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {'custom_list': []}
    
    def save_config(self):
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass
    
    def get_system_info(self):
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        return {
            'memory_total': round(mem.total / (1024**3), 1),
            'memory_used': round(mem.used / (1024**3), 1),
            'memory_percent': mem.percent,
            'cpu_percent': cpu
        }
    
    def enable_game_mode(self):
        killed = []
        all_apps = APPS_TO_KILL + self.config.get('custom_list', [])
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                name = proc.info['name']
                if name.lower() in [x.lower() for x in all_apps]:
                    # Skip if it's our own process
                    if 'game_mode' in name.lower() or 'optimizer' in name.lower() or 'ping' in name.lower():
                        continue
                    proc.kill()
                    killed.append(name)
                    self.killed_processes.append(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        self.active = True
        return killed
    
    def disable_game_mode(self):
        self.active = False
        self.killed_processes = []
        return True


class GameModeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Game Mode - Free Up RAM & Resources')
        self.root.geometry('480x520')
        self.gamemode = GameMode()
        
        frm = ttk.Frame(root, padding=12)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='Game Mode - Resource Optimizer', font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        # System Info
        info_frame = ttk.LabelFrame(frm, text='System Resources', padding=8)
        info_frame.pack(fill='x', pady=5)
        
        self.info_label = ttk.Label(info_frame, text='Loading...')
        self.info_label.pack(anchor='w')
        self.update_info()
        
        # Game Mode Toggle
        toggle_frame = ttk.LabelFrame(frm, text='Game Mode', padding=8)
        toggle_frame.pack(fill='x', pady=5)
        
        self.status_label = ttk.Label(toggle_frame, text='Status: INACTIVE', font=('Arial', 10, 'bold'), foreground='#ff7b72')
        self.status_label.pack(pady=5)
        
        btn_frame = ttk.Frame(toggle_frame)
        btn_frame.pack(fill='x')
        self.enable_btn = ttk.Button(btn_frame, text='ENABLE GAME MODE', command=self.enable)
        self.enable_btn.pack(side='left', expand=True, fill='x', padx=2)
        self.disable_btn = ttk.Button(btn_frame, text='DISABLE', command=self.disable, state='disabled')
        self.disable_btn.pack(side='left', expand=True, fill='x', padx=2)
        
        ttk.Label(toggle_frame, text='This will kill memory-hungry apps to free up RAM', 
                  foreground='#8b949e', font=('Arial', 8)).pack(pady=2)
        
        # Apps List
        apps_frame = ttk.LabelFrame(frm, text='Apps to Kill', padding=8)
        apps_frame.pack(fill='both', expand=True, pady=5)
        
        self.apps_text = tk.Text(apps_frame, height=12, bg='#0d1117', fg='#e6edf3',
                                 font=('Consolas', 8), wrap='word')
        scrollbar = ttk.Scrollbar(apps_frame, orient='vertical', command=self.apps_text.yview)
        self.apps_text.configure(yscrollcommand=scrollbar.set)
        self.apps_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.update_apps_list()
        
        # Log
        log_frame = ttk.LabelFrame(frm, text='Activity Log', padding=8)
        log_frame.pack(fill='x', pady=5)
        self.log_label = ttk.Label(log_frame, text='Ready')
        self.log_label.pack(anchor='w')
        
        ttk.Button(frm, text='Refresh System Info', command=self.update_info).pack(fill='x', pady=2)
        ttk.Label(frm, text='Warning: Only kill apps you don\'t need while gaming', 
                  foreground='#d29922').pack(pady=2)
        
    def update_info(self):
        info = self.gamemode.get_system_info()
        self.info_label.config(text=f"RAM: {info['memory_used']}GB / {info['memory_total']}GB ({info['memory_percent']}%)  |  CPU: {info['cpu_percent']}%")
        self.root.after(3000, self.update_info)
    
    def update_apps_list(self):
        self.apps_text.delete('1.0', tk.END)
        all_apps = APPS_TO_KILL + self.gamemode.config.get('custom_list', [])
        for app in sorted(set(all_apps)):
            self.apps_text.insert(tk.END, f'• {app}\n')
    
    def enable(self):
        if messagebox.askyesno('Enable Game Mode', 'This will close the listed apps.\nAre you sure?'):
            killed = self.gamemode.enable_game_mode()
            self.status_label.config(text=f'Status: ACTIVE', foreground='#3fb950')
            self.enable_btn.config(state='disabled')
            self.disable_btn.config(state='normal')
            if killed:
                self.log_label.config(text=f'Killed: {", ".join(killed[:5])}' + (f' (+{len(killed)-5} more)' if len(killed)>5 else ''))
            else:
                self.log_label.config(text='No apps needed to be killed')
            self.update_info()
    
    def disable(self):
        self.gamemode.disable_game_mode()
        self.status_label.config(text='Status: INACTIVE', foreground='#ff7b72')
        self.enable_btn.config(state='normal')
        self.disable_btn.config(state='disabled')
        self.log_label.config(text='Game Mode disabled (apps must be restarted manually)')
        self.update_info()


if __name__ == '__main__':
    root = tk.Tk()
    app = GameModeGUI(root)
    root.mainloop()
