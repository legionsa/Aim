import json
import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import pyautogui

pyautogui.FAILSAFE = True  # sling mouse to top-left corner to abort instantly

BASE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE, 'pattern.json')


class Macro:
    def __init__(self):
        self.deltas = []
        self.shots = 30
        self.k = 1.0
        self.mtime = 0
        self.running = False
        self.stop = False
        self.thread = None
        self.load()

    def load(self):
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.deltas = [tuple(d) for d in data.get('deltas', [])]
            self.shots = int(data.get('shots', len(self.deltas)))
            self.k = float(data.get('k', 1.0))
            self.mtime = os.path.getmtime(JSON_PATH)
            return True, None
        except Exception as e:
            return False, str(e)

    def check_reload(self):
        try:
            mt = os.path.getmtime(JSON_PATH)
            if mt != self.mtime:
                ok, err = self.load()
                return ok, err
        except Exception as e:
            return False, str(e)
        return True, None

    def run(self, shots_override=None, delay_ms=60, start_delay_ms=300, mult=1.0):
        self.stop = False
        self.running = True
        time.sleep(start_delay_ms / 1000.0)

        ok, err = self.load()
        if not ok:
            self.running = False
            return err

        n = shots_override if shots_override else self.shots
        n = min(n, len(self.deltas))

        while not self.stop:
            for i in range(n):
                if self.stop:
                    break
                ok, err = self.check_reload()
                dx, dy = self.deltas[i]
                pyautogui.moveRel(
                    -dx * self.k * mult,
                    -dy * self.k * mult,
                    duration=0,
                )
                time.sleep(delay_ms / 1000.0)
            if self.stop:
                break

        self.running = False
        return None

    def start(self, shots, delay_ms, start_delay_ms, mult):
        if self.running:
            return 'already running'
        self.stop = False
        self.thread = threading.Thread(
            target=self.run,
            args=(shots, delay_ms, start_delay_ms, mult),
            daemon=True,
        )
        self.thread.start()
        return None

    def stop_macro(self):
        self.stop = True


class App:
    def __init__(self, root):
        self.root = root
        self.root.title('JSON Mouse Macro')
        self.root.geometry('420x360')
        self.macro = Macro()

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill='both', expand=True)

        ttk.Label(frm, text=f'Pattern file: {JSON_PATH}').pack(anchor='w', pady=(0, 8))

        row = ttk.Frame(frm)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text='shots:').pack(side='left')
        self.var_shots = tk.StringVar(value='30')
        ttk.Entry(row, textvariable=self.var_shots, width=6).pack(side='left', padx=4)

        row = ttk.Frame(frm)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text='delay ms/shot:').pack(side='left')
        self.var_delay = tk.StringVar(value='60')
        ttk.Entry(row, textvariable=self.var_delay, width=6).pack(side='left', padx=4)

        row = ttk.Frame(frm)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text='start delay ms:').pack(side='left')
        self.var_start = tk.StringVar(value='300')
        ttk.Entry(row, textvariable=self.var_start, width=6).pack(side='left', padx=4)

        row = ttk.Frame(frm)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text='scale mult:').pack(side='left')
        self.var_mult = tk.StringVar(value='1.0')
        ttk.Entry(row, textvariable=self.var_mult, width=6).pack(side='left', padx=4)

        btns = ttk.Frame(frm)
        btns.pack(fill='x', pady=12)
        self.btn_start = ttk.Button(btns, text='Start (F6)', command=self.do_start)
        self.btn_start.pack(side='left', expand=True, fill='x', padx=2)
        self.btn_stop = ttk.Button(btns, text='Stop (F7)', command=self.do_stop, state='disabled')
        self.btn_stop.pack(side='left', expand=True, fill='x', padx=2)
        ttk.Button(btns, text='Reload JSON', command=self.do_reload).pack(side='left', expand=True, fill='x', padx=2)

        self.lbl_status = ttk.Label(frm, text='idle', foreground='#8b949e')
        self.lbl_status.pack(anchor='w', pady=(8, 0))

        self.lbl_info = ttk.Label(frm, text='', foreground='#79c0ff')
        self.lbl_info.pack(anchor='w', pady=(2, 0))

        ttk.Label(
            frm,
            text='Abort: sling mouse to top-left corner (pyautogui failsafe).\nEdit pattern.json then click Reload JSON.',
            foreground='#8b949e',
            justify='left',
        ).pack(anchor='w', pady=(10, 0))

        root.bind('<F6>', lambda e: self.do_start())
        root.bind('<F7>', lambda e: self.do_stop())
        root.protocol('WM_DELETE_WINDOW', self.on_close)
        root.after(500, self.do_start)
        self.poll()

    def get_vals(self):
        try:
            shots = int(self.var_shots.get())
        except Exception:
            shots = 30
        try:
            delay = float(self.var_delay.get())
        except Exception:
            delay = 60.0
        try:
            start = float(self.var_start.get())
        except Exception:
            start = 300.0
        try:
            mult = float(self.var_mult.get())
        except Exception:
            mult = 1.0
        return shots, delay, start, mult

    def do_start(self):
        shots, delay, start, mult = self.get_vals()
        err = self.macro.start(shots, delay, start, mult)
        if err:
            self.lbl_status.config(text=err, foreground='#ff7b72')
            return
        self.btn_start.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.lbl_status.config(text='running...', foreground='#3fb950')
        self.lbl_info.config(text=f'deltas={len(self.macro.deltas)} shots={shots} k={self.macro.k} mult={mult}')

    def do_stop(self):
        self.macro.stop_macro()
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')
        self.lbl_status.config(text='stopped', foreground='#8b949e')

    def do_reload(self):
        ok, err = self.macro.load()
        if ok:
            self.lbl_status.config(text='reloaded', foreground='#3fb950')
            self.lbl_info.config(text=f'deltas={len(self.macro.deltas)} shots={self.macro.shots} k={self.macro.k}')
        else:
            self.lbl_status.config(text=f'load error: {err}', foreground='#ff7b72')

    def poll(self):
        if self.macro.running and not self.btn_stop.instate(['disabled']):
            pass
        if not self.macro.running and self.btn_start.instate(['disabled']):
            self.btn_start.config(state='normal')
            self.btn_stop.config(state='disabled')
            self.lbl_status.config(text='idle', foreground='#8b949e')
        self.root.after(300, self.poll)

    def on_close(self):
        self.macro.stop_macro()
        self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
