import json
import os
import time
import threading
import random
import ctypes
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw

import pyautogui
from pynput import mouse, keyboard
import pystray

pyautogui.FAILSAFE = True

BASE = os.path.dirname(os.path.abspath(__file__))
WEAPONS_PATH = os.path.join(BASE, 'weapons.json')
PATTERN_PATH = os.path.join(BASE, 'pattern.json')
CONFIG_PATH = os.path.join(BASE, 'macro_config.json')

PUL = ctypes.POINTER(ctypes.c_ulong)
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]
class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]
MOUSEEVENTF_MOVE = 0x0001

def move_mouse_rel(dx, dy):
    try:
        if dx == 0 and dy == 0:
            return
        inp = INPUT()
        inp.type = 0
        inp.mi.dx = int(dx)
        inp.mi.dy = int(dy)
        inp.mi.mouseData = 0
        inp.mi.dwFlags = MOUSEEVENTF_MOVE
        inp.mi.time = 0
        inp.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    except Exception:
        pyautogui.moveRel(dx, dy, duration=0)

def get_foreground():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid.value)
        buf = ctypes.create_unicode_buffer(512)
        ctypes.windll.psapi.GetModuleBaseNameW(handle, None, buf, 512)
        ctypes.windll.kernel32.CloseHandle(handle)
        return buf.value.lower()
    except Exception:
        return ""


class Macro:
    def __init__(self):
        self.weapons = {}
        self.current = None
        self.deltas = []
        self.shots = 30
        self.k = 1.0
        self.delay_ms = 60
        self.mtime = 0
        self.running = False
        self.firing = False
        self.enabled = True
        self.humanize = False
        self.jitter_x = 0
        self.jitter_y = 0
        self.foreground_only = False
        self.target_exe = 'cs2.exe'
        self.toggle_mode = False
        self.smoothing = True
        self.smooth_factor = 0.8
        self.lock = threading.Lock()
        self.load_config()
        self.load_weapons()

    def load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    c = json.load(f)
                self.enabled = c.get('enabled', True)
                self.humanize = c.get('humanize', False)
                self.jitter_x = float(c.get('jitter_x', 0))
                self.jitter_y = float(c.get('jitter_y', 0))
                self.delay_ms = float(c.get('delay_ms', 60))
                self.current = c.get('weapon', None)
                self.foreground_only = c.get('foreground_only', False)
                self.target_exe = c.get('target_exe', 'cs2.exe')
                self.toggle_mode = c.get('toggle_mode', False)
                self.smoothing = c.get('smoothing', True)
                self.smooth_factor = float(c.get('smooth_factor', 0.8))
        except Exception:
            pass

    def save_config(self):
        try:
            c = {
                'enabled': self.enabled,
                'humanize': self.humanize,
                'jitter_x': self.jitter_x,
                'jitter_y': self.jitter_y,
                'delay_ms': self.delay_ms,
                'weapon': self.current,
                'foreground_only': self.foreground_only,
                'target_exe': self.target_exe,
                'toggle_mode': self.toggle_mode,
                'smoothing': self.smoothing,
                'smooth_factor': self.smooth_factor
            }
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(c, f, indent=2)
        except Exception:
            pass

    def load_weapons(self):
        try:
            if os.path.exists(WEAPONS_PATH):
                with open(WEAPONS_PATH, 'r', encoding='utf-8') as f:
                    self.weapons = json.load(f)
            elif os.path.exists(PATTERN_PATH):
                with open(PATTERN_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'deltas' in data:
                        self.weapons = {'current': data}
                        self.weapons['current']['name'] = data.get('pattern', 'custom')
                    else:
                        self.weapons = data
            if self.weapons and not self.current:
                self.current = list(self.weapons.keys())[0]
            elif self.weapons and self.current not in self.weapons:
                self.current = list(self.weapons.keys())[0]
            if self.current in self.weapons:
                self.load_current()
            self.mtime = max([os.path.getmtime(WEAPONS_PATH) if os.path.exists(WEAPONS_PATH) else 0,
                             os.path.getmtime(PATTERN_PATH) if os.path.exists(PATTERN_PATH) else 0])
            return True, None
        except Exception as e:
            return False, str(e)

    def load_current(self):
        if not self.current or self.current not in self.weapons:
            return
        w = self.weapons[self.current]
        self.deltas = [tuple(d) for d in w.get('deltas', [])]
        self.shots = int(w.get('shots', len(self.deltas)))
        self.k = float(w.get('k', 1.0))
        if 'delay_ms' in w:
            self.delay_ms = float(w['delay_ms'])
        if 'mult' in w:
            # store per-weapon mult, applied in fire_loop via weapon_mult
            self.weapon_mult = float(w['mult'])
        else:
            self.weapon_mult = 1.0

    def set_weapon(self, key):
        if key in self.weapons:
            self.current = key
            self.load_current()
            self.save_config()

    def fire_loop(self, delay_ms, mult):
        self.running = True
        self.load_current()
        n = min(self.shots, len(self.deltas))
        idx = 0
        last = time.perf_counter()
        interval = delay_ms / 1000.0
        prev_x = prev_y = 0
        while True:
            with self.lock:
                if not self.firing or not self.enabled:
                    break
            if self.foreground_only:
                fg = get_foreground()
                if self.target_exe.lower() not in fg:
                    time.sleep(0.001)
                    continue
            dx, dy = self.deltas[idx]
            mx = -dx * self.k * mult * getattr(self, 'weapon_mult', 1.0)
            my = -dy * self.k * mult * getattr(self, 'weapon_mult', 1.0)
            if self.humanize and self.jitter_x > 0:
                mx += random.uniform(-self.jitter_x, self.jitter_x)
                my += random.uniform(-self.jitter_y, self.jitter_y)
            if self.smoothing and self.smooth_factor > 0:
                mx = prev_x * self.smooth_factor + mx * (1 - self.smooth_factor)
                my = prev_y * self.smooth_factor + my * (1 - self.smooth_factor)
                prev_x, prev_y = mx, my
            d = interval + random.uniform(-0.002, 0.002)
            if d < 0.001:
                d = interval
            move_mouse_rel(mx, my)
            idx = (idx + 1) % n
            last += d
            sleep_time = last - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                last = time.perf_counter()
        self.running = False
