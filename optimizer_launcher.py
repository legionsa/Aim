import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))

class OptimizerLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title('XS2 Aim - Gaming Optimizer Suite')
        self.root.geometry('420x480')
        self.root.resizable(False, False)
        
        frm = ttk.Frame(root, padding=20)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='XS2 Gaming Optimizer', font=('Arial', 14, 'bold')).pack(pady=(0, 5))
        ttk.Label(frm, text='All-in-one gaming optimization tools', 
                  foreground='#8b949e').pack(pady=(0, 20))
        
        # Tools
        tools = [
            ('Kill Ping - Network Optimizer', 'Reduce ping & latency', 'ping_optimizer.py', '#ff6b6b'),
            ('Game Mode - Free RAM', 'Kill memory hogs while gaming', 'game_mode.py', '#4dabf7'),
            ('CS2 Visual Optimizer', 'Better enemy visibility & colors', 'cs2_visuals.py', '#51cf66'),
            ('Recoil Macro (Existing)', 'Mouse1 recoil compensation', 'macro_m1.py', '#ffd43b'),
        ]
        
        for title, desc, script, color in tools:
            frame = ttk.LabelFrame(frm, text='', padding=10)
            frame.pack(fill='x', pady=4)
            ttk.Label(frame, text=title, font=('Arial', 10, 'bold')).pack(anchor='w')
            ttk.Label(frame, text=desc, foreground='#8b949e', font=('Arial', 9)).pack(anchor='w')
            btn = ttk.Button(frame, text='Launch', command=lambda s=script: self.launch(s))
            btn.pack(fill='x', pady=(5, 0))
        
        ttk.Separator(frm, orient='horizontal').pack(fill='x', pady=15)
        
        ttk.Label(frm, text='CS2 Quick Tips:', font=('Arial', 9, 'bold')).pack(anchor='w')
        tips = [
            '• Enable "Boost Player Contrast" in Video Settings',
            '• Use Yellow enemy color for best visibility',
            '• Set brightness 90-100%, contrast 110-120%',
            '• Run Game Mode before launching CS2',
        ]
        for tip in tips:
            ttk.Label(frm, text=tip, foreground='#8b949e', font=('Arial', 8)).pack(anchor='w')
        
        ttk.Label(frm, text='Run as Administrator for best results', 
                  foreground='#f85149', font=('Arial', 8)).pack(pady=(10, 0))
        
    def launch(self, script):
        script_path = os.path.join(BASE, script)
        try:
            if script.endswith('.py'):
                subprocess.Popen([sys.executable, script_path], cwd=BASE)
            else:
                subprocess.Popen([script_path], cwd=BASE)
        except Exception as e:
            tk.messagebox.showerror('Error', f'Failed to launch: {e}')


if __name__ == '__main__':
    import tkinter.messagebox
    root = tk.Tk()
    app = OptimizerLauncher(root)
    root.mainloop()
