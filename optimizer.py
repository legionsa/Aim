import json
import os
import time
import threading
import psutil
import ctypes
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict
import winreg

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, 'optimizer_config.json')

# Common memory hogs to kill in game mode
MEMORY_HOGS = [
    'chrome.exe', 'msedge.exe', 'firefox.exe', 'opera.exe', 'brave.exe', 'vivaldi.exe',
    'discord.exe', 'spotify.exe', 'steamwebhelper.exe', 'teams.exe', 'slack.exe',
    'zoom.exe', 'skype.exe', 'whatsapp.exe', 'telegram.exe', 'obs64.exe', 'streamlabs.exe',
    'dropbox.exe', 'onedrive.exe', 'googledrivesync.exe', 'icloud.exe',
    'adobecrashreporter.exe', 'creativecloud.exe', 'photoshop.exe', 'lightroom.exe',
    'wallpaperengine.exe', 'rainmeter.exe', 'f.lux.exe', 'nightlight'
]

class Optimizer:
    def __init__(self):
        self.config = self.load_config()
        self.game_mode = False
        
    def load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {
            'kill_on_gamemode': MEMORY_HOGS.copy(),
            'auto_kill': [],
            'network_optimized': False
        }
    
    def save_config(self):
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass
    
    def get_memory_usage(self):
        mem = psutil.virtual_memory()
        return {
            'total': mem.total // (1024**3),
            'used': mem.used // (1024**3),
            'percent': mem.percent,
            'available': mem.available // (1024**3)
        }
    
    def kill_memory_hogs(self):
        killed = []
        for proc in psutil.process_iter(['name', 'pid', 'memory_info']):
            try:
                name = proc.info['name'].lower()
                if name in [x.lower() for x in MEMORY_HOGS]:
                    if name in ['csrss.exe', 'winlogon.exe', 'services.exe', 'lsass.exe']:
                        continue
                    proc.terminate()
                    killed.append(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return killed
    
    def optimize_network(self):
        results = []
        try:
            subprocess.run(['ipconfig', '/flushdns'], shell=True, capture_output=True)
            results.append('DNS flushed')
            subprocess.run(['netsh', 'winsock', 'reset'], shell=True, capture_output=True)
            results.append('Winsock reset')
            subprocess.run(['netsh', 'int', 'ip', 'reset'], shell=True, capture_output=True)
            results.append('TCP/IP reset')
            results.append('Network stack optimized')
            self.config['network_optimized'] = True
            self.save_config()
        except Exception as e:
            results.append(f'Error: {e}')
        return results
    
    def set_game_mode(self, enable=True):
        self.game_mode = enable
        if enable:
            killed = self.kill_memory_hogs()
            return {'status': 'enabled', 'killed': killed}
        return {'status': 'disabled'}


class CS2Settings:
    @staticmethod
    def get_visibility_recommendations():
        return {
            'video_settings': {
                'brightness': '90-100%',
                'contrast': '110-120%',
                'color_mode': 'Computer Monitor',
                'vibrance': 'If available, +10 to +15',
                'gamma': '2.2 or 2.4',
                'anti_aliasing': 'Off or Low (performance)',
                'shadows': 'Low/Very Low',
                'effects': 'Low/Very Low',
                'post_processing': 'Low',
                'motion_blur': 'Disabled',
                'ambient_occlusion': 'Disabled'
            },
            'color_settings': {
                'enemy_color': 'Yellow/Orange or Cyan (easier to spot)',
                'teammate_color': 'Blue',
                'recommended': [
                    'Use colorblind mode if helps (Protanopia/Deuteranopia can improve contrast)',
                    'Yellow is often best for visibility against most maps',
                    'Avoid red/pink if colorblind or prefer cyan'
                ]
            },
            'radar_settings': {
                'radar_scale': '0.4 - 0.6',
                'radar_rotate': 'Yes',
                'radar_always_centered': 'No'
            },
            'console_commands': [
                'cl_color 1  // Try different values (0-4)',
                'r_drawtracers_firstperson 0',
                'mat_monitorgamma_tv_enabled 0',
                'mat_queue_mode 2  // Multi-threaded',
                'fps_max 0  // Unlimited or cap based on monitor',
                'cl_hud_color 5  // Custom HUD color'
            ]
        }
