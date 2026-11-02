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
        self.humanize = True
        self.jitter_x = 0.4
        self.jitter_y = 0.4
        self.foreground_only = True
        self.target_exe = 'cs2.exe'
        self.toggle_mode = False
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
                'toggle_mode': self.toggle_mode
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
            mx = -dx * self.k * mult
            my = -dy * self.k * mult
            if self.humanize:
                mx += random.uniform(-self.jitter_x, self.jitter_x)
                my += random.uniform(-self.jitter_y, self.jitter_y)
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


class App:
    def __init__(self, root):
        self.root = root
        self.root.title('CS2 Mouse1 Recoil Macro - Final')
        self.root.geometry('480x480')
        self.macro = Macro()
        self.thread = None
        self.listener = None
        self.kb_listener = None
        self.tray = None
        self.toggle_state = False

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill='both', expand=True)

        ttk.Label(frm, text='Weapon:').pack(anchor='w')
        self.var_weapon = tk.StringVar()
        self.combo = ttk.Combobox(frm, textvariable=self.var_weapon, state='readonly')
        keys = list(self.macro.weapons.keys())
        self.combo['values'] = [self.macro.weapons[k].get('name', k) for k in keys]
        self.key_map = keys
        if keys and self.macro.current in keys:
            idx = keys.index(self.macro.current)
            self.combo.current(idx)
            self.var_weapon.set(self.macro.weapons[keys[idx]].get('name', keys[idx]))
        elif keys:
            self.combo.current(0)
            self.var_weapon.set(self.macro.weapons[keys[0]].get('name', keys[0]))
        self.combo.bind('<<ComboboxSelected>>', self.on_weapon_change)
        self.combo.pack(fill='x', pady=(0, 8))

        row = ttk.Frame(frm)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text='shots:').pack(side='left')
        self.var_shots = tk.StringVar(value=str(self.macro.shots))
        ttk.Entry(row, textvariable=self.var_shots, width=6).pack(side='left', padx=4)

        row = ttk.Frame(frm)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text='delay ms/shot:').pack(side='left')
        self.var_delay = tk.StringVar(value=str(int(self.macro.delay_ms)))
        ttk.Entry(row, textvariable=self.var_delay, width=6).pack(side='left', padx=4)

        row = ttk.Frame(frm)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text='scale mult:').pack(side='left')
        self.var_mult = tk.StringVar(value='1.0')
        ttk.Entry(row, textvariable=self.var_mult, width=6).pack(side='left', padx=4)

        row = ttk.Frame(frm)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text='DPI:').pack(side='left')
        self.var_dpi = tk.StringVar(value='800')
        ttk.Entry(row, textvariable=self.var_dpi, width=6).pack(side='left', padx=4)
        ttk.Label(row, text='Sens:').pack(side='left')
        self.var_sens = tk.StringVar(value='1.0')
        ttk.Entry(row, textvariable=self.var_sens, width=6).pack(side='left', padx=4)
        ttk.Button(row, text='Calc', command=self.calc_dpi).pack(side='left', padx=4)

        self.var_humanize = tk.BooleanVar(value=self.macro.humanize)
        ttk.Checkbutton(frm, text='Humanize (jitter)', variable=self.var_humanize, command=self.toggle_humanize).pack(anchor='w', pady=2)
        self.var_enabled = tk.BooleanVar(value=self.macro.enabled)
        ttk.Checkbutton(frm, text='Enabled (F8 toggle)', variable=self.var_enabled, command=self.toggle_enabled).pack(anchor='w', pady=2)
        self.var_fg = tk.BooleanVar(value=self.macro.foreground_only)
        ttk.Checkbutton(frm, text='Only when CS2 foreground', variable=self.var_fg, command=self.toggle_fg).pack(anchor='w', pady=2)
        self.var_toggle = tk.BooleanVar(value=self.macro.toggle_mode)
        ttk.Checkbutton(frm, text='Toggle mode (press Mouse1 to toggle)', variable=self.var_toggle, command=self.toggle_toggle).pack(anchor='w', pady=2)

        btnrow = ttk.Frame(frm)
        btnrow.pack(fill='x', pady=(10, 4))
        ttk.Button(btnrow, text='Reload', command=self.do_reload).pack(side='left', expand=True, fill='x', padx=2)
        ttk.Button(btnrow, text='Save Config', command=self.save_all).pack(side='left', expand=True, fill='x', padx=2)
        ttk.Button(btnrow, text='Minimize to Tray', command=self.to_tray).pack(side='left', expand=True, fill='x', padx=2)

        self.lbl_status = ttk.Label(frm, text='Waiting for Mouse1... [F8: toggle | F9: panic]', foreground='#8b949e')
        self.lbl_status.pack(anchor='w', pady=(8, 0))

        self.lbl_info = ttk.Label(frm, text='', foreground='#79c0ff')
        self.lbl_info.pack(anchor='w', pady=(2, 0))

        ttk.Label(
            frm,
            text='Hotkeys: F8=toggle | F9=panic | Num1-7=weapon | F6=show window',
            foreground='#8b949e',
            justify='left',
        ).pack(anchor='w', pady=(10, 0))

        self.update_info()
        self.start_listener()
        self.start_kb()
        root.protocol('WM_DELETE_WINDOW', self.to_tray)
        self.poll()
        self.create_tray()

    def create_tray(self):
        try:
            img = Image.new('RGB', (64, 64), color='#1f6feb')
            d = ImageDraw.Draw(img)
            d.rectangle([16, 8, 48, 56], fill='#3fb950')
            menu = (
                pystray.MenuItem('Show', self.show_win, default=True),
                pystray.MenuItem('Toggle', self.tray_toggle),
                pystray.MenuItem('Exit', self.tray_exit),
            )
            self.tray = pystray.Icon('recoil', img, 'Recoil Macro', menu)
            threading.Thread(target=self.tray.run, daemon=True).start()
        except Exception:
            pass

    def show_win(self, *a):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def to_tray(self):
        self.root.withdraw()

    def tray_toggle(self, *a):
        self.macro.enabled = not self.macro.enabled
        self.var_enabled.set(self.macro.enabled)
        if not self.macro.enabled:
            with self.macro.lock:
                self.macro.firing = False
        self.macro.save_config()

    def tray_exit(self, *a):
        with self.macro.lock:
            self.macro.firing = False
        if self.listener:
            self.listener.stop()
        if self.kb_listener:
            self.kb_listener.stop()
        self.macro.save_config()
        try:
            if self.tray:
                self.tray.stop()
        except Exception:
            pass
        os._exit(0)

    def calc_dpi(self):
        try:
            dpi = float(self.var_dpi.get())
            sens = float(self.var_sens.get())
            edpi = dpi * sens
            self.lbl_status.config(text=f'eDPI {edpi:.0f} - mult auto calc ready', foreground='#79c0ff')
        except Exception:
            pass

    def on_weapon_change(self, event):
        idx = self.combo.current()
        if idx >= 0 and idx < len(self.key_map):
            self.macro.set_weapon(self.key_map[idx])
            self.var_delay.set(str(int(self.macro.delay_ms)))
            self.update_info()

    def toggle_humanize(self):
        self.macro.humanize = self.var_humanize.get()
        self.macro.save_config()

    def toggle_enabled(self):
        self.macro.enabled = self.var_enabled.get()
        if not self.macro.enabled:
            with self.macro.lock:
                self.macro.firing = False
            self.lbl_status.config(text='DISABLED [F8: toggle | F9: panic]', foreground='#ff7b72')
        else:
            self.lbl_status.config(text='Waiting for Mouse1... [F8: toggle | F9: panic]', foreground='#8b949e')
        self.macro.save_config()

    def toggle_fg(self):
        self.macro.foreground_only = self.var_fg.get()
        self.macro.save_config()

    def toggle_toggle(self):
        self.macro.toggle_mode = self.var_toggle.get()
        self.macro.save_config()

    def get_vals(self):
        try:
            shots = int(self.var_shots.get())
        except Exception:
            shots = 30
        try:
            delay = float(self.var_delay.get())
        except Exception:
            delay = self.macro.delay_ms
        try:
            mult = float(self.var_mult.get())
        except Exception:
            mult = 1.0
        return shots, delay, mult

    def update_info(self):
        self.macro.load_current()
        self.lbl_info.config(text=f'deltas={len(self.macro.deltas)} shots={self.macro.shots} k={self.macro.k} delay={int(self.macro.delay_ms)}ms')

    def do_reload(self):
        self.macro.load_weapons()
        keys = list(self.macro.weapons.keys())
        self.key_map = keys
        self.combo['values'] = [self.macro.weapons[k].get('name', k) for k in keys]
        idx = self.combo.current()
        if idx >= 0 and idx < len(keys):
            self.macro.set_weapon(keys[idx])
        self.var_delay.set(str(int(self.macro.delay_ms)))
        self.update_info()
        self.lbl_status.config(text='Reloaded', foreground='#3fb950')
        self.root.after(1000, lambda: self.lbl_status.config(text='Waiting for Mouse1... [F8: toggle | F9: panic]' if self.macro.enabled else 'DISABLED [F8: toggle | F9: panic]', foreground='#8b949e' if self.macro.enabled else '#ff7b72'))

    def save_all(self):
        shots, delay, mult = self.get_vals()
        self.macro.delay_ms = delay
        self.macro.save_config()
        self.lbl_status.config(text='Config saved', foreground='#3fb950')
        self.root.after(1000, lambda: self.lbl_status.config(text='Waiting for Mouse1... [F8: toggle | F9: panic]', foreground='#8b949e'))

    def on_click(self, x, y, button, pressed):
        if not self.macro.enabled:
            return
        if button == mouse.Button.left:
            shots, delay, mult = self.get_vals()
            self.macro.shots = shots
            self.macro.delay_ms = delay
            if self.macro.toggle_mode:
                if pressed:
                    with self.macro.lock:
                        if not self.toggle_state and not self.macro.firing:
                            self.toggle_state = True
                            self.macro.firing = True
                            self.lbl_status.config(text='FIRING (toggle)', foreground='#ff7b72')
                            if not self.macro.running:
                                self.thread = threading.Thread(target=self.macro.fire_loop, args=(delay, mult), daemon=True)
                                self.thread.start()
                        elif self.toggle_state and self.macro.firing:
                            self.toggle_state = False
                            self.macro.firing = False
                            self.lbl_status.config(text='Waiting for Mouse1... [F8: toggle | F9: panic]', foreground='#8b949e')
                return
            with self.macro.lock:
                if pressed and not self.macro.firing:
                    self.macro.firing = True
                    self.lbl_status.config(text='FIRING (hold Mouse1)', foreground='#ff7b72')
                    if not self.macro.running:
                        self.thread = threading.Thread(target=self.macro.fire_loop, args=(delay, mult), daemon=True)
                        self.thread.start()
                elif not pressed and self.macro.firing:
                    self.macro.firing = False
                    self.lbl_status.config(text='Waiting for Mouse1... [F8: toggle | F9: panic]', foreground='#8b949e')

    def start_listener(self):
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.daemon = True
        self.listener.start()

    def on_kb(self, key):
        try:
            if key == keyboard.Key.f8:
                self.macro.enabled = not self.macro.enabled
                self.var_enabled.set(self.macro.enabled)
                if not self.macro.enabled:
                    with self.macro.lock:
                        self.macro.firing = False
                    self.lbl_status.config(text='DISABLED [F8: toggle | F9: panic]', foreground='#ff7b72')
                else:
                    self.lbl_status.config(text='Waiting for Mouse1... [F8: toggle | F9: panic]', foreground='#8b949e')
                self.macro.save_config()
                return
            if key == keyboard.Key.f9:
                with self.macro.lock:
                    self.macro.firing = False
                self.macro.enabled = False
                self.var_enabled.set(False)
                self.lbl_status.config(text='PANIC DISABLED [F8: toggle | F9: panic]', foreground='#ff0000')
                self.macro.save_config()
                return
            if key == keyboard.Key.f6:
                self.show_win()
                return
            if hasattr(key, 'vk'):
                if key.vk == 97:  # NumPad1
                    self.switch_weapon(0)
                elif key.vk == 98:
                    self.switch_weapon(1)
                elif key.vk == 99:
                    self.switch_weapon(2)
                elif key.vk == 100:
                    self.switch_weapon(3)
                elif key.vk == 101:
                    self.switch_weapon(4)
                elif key.vk == 102:
                    self.switch_weapon(5)
                elif key.vk == 103:
                    self.switch_weapon(6)
        except Exception:
            pass

    def switch_weapon(self, idx):
        if idx >= 0 and idx < len(self.key_map):
            self.combo.current(idx)
            self.macro.set_weapon(self.key_map[idx])
            self.var_delay.set(str(int(self.macro.delay_ms)))
            self.update_info()
            self.lbl_status.config(text=f'Switched to {self.combo.get()}', foreground='#3fb950')
            self.root.after(800, lambda: self.lbl_status.config(text='Waiting for Mouse1... [F8: toggle | F9: panic]' if self.macro.enabled else 'DISABLED [F8: toggle | F9: panic]', foreground='#8b949e' if self.macro.enabled else '#ff7b72'))

    def start_kb(self):
        self.kb_listener = keyboard.Listener(on_press=self.on_kb)
        self.kb_listener.daemon = True
        self.kb_listener.start()

    def poll(self):
        self.root.after(200, self.poll)

    def on_close(self):
        with self.macro.lock:
            self.macro.firing = False
        if self.listener:
            self.listener.stop()
        if self.kb_listener:
            self.kb_listener.stop()
        self.macro.save_config()
        try:
            if self.tray:
                self.tray.stop()
        except Exception:
            pass
        os._exit(0)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
