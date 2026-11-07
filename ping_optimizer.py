import json
import os
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, 'ping_config.json')

class PingOptimizer:
    def __init__(self):
        self.config = self.load_config()
        self.monitoring = False
        
    def load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {
            'auto_optimize': True,
            'target_latency': 50
        }
    
    def save_config(self):
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass
    
    def ping_test(self, host='8.8.8.8'):
        try:
            result = subprocess.run(['ping', '-n', '4', host], shell=True, 
                                  capture_output=True, text=True, timeout=10)
            output = result.stdout
            # Parse average
            for line in output.split('\n'):
                if 'Average' in line or 'rata-rata' in line.lower():
                    return output
            return output
        except Exception as e:
            return f'Error: {e}'
    
    def flush_dns(self):
        try:
            subprocess.run(['ipconfig', '/flushdns'], shell=True, capture_output=True)
            return 'DNS cache flushed'
        except Exception as e:
            return f'Error: {e}'
    
    def reset_network(self):
        try:
            commands = [
                ['netsh', 'winsock', 'reset'],
                ['netsh', 'int', 'ip', 'reset'],
                ['netsh', 'interface', 'ipv4', 'reset'],
                ['netsh', 'interface', 'ipv6', 'reset']
            ]
            for cmd in commands:
                subprocess.run(cmd, shell=True, capture_output=True)
            return 'Network stack reset (restart required)'
        except Exception as e:
            return f'Error: {e}'
    
    def optimize_tcp(self):
        try:
            # Disable Windows Update Delivery Optimization (can cause lag)
            cmd = 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DeliveryOptimization\\Config" /v DODownloadMode /t REG_DWORD /d 0 /f'
            subprocess.run(cmd, shell=True, capture_output=True)
            return 'TCP optimizations applied'
        except Exception as e:
            return f'Error: {e}'


class PingOptimizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Kill Ping - Network Optimizer')
        self.root.geometry('520x580')
        self.optimizer = PingOptimizer()
        
        frm = ttk.Frame(root, padding=12)
        frm.pack(fill='both', expand=True)
        
        ttk.Label(frm, text='Kill Ping - Network Latency Optimizer', font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        # Status
        status_frame = ttk.LabelFrame(frm, text='Network Status', padding=8)
        status_frame.pack(fill='x', pady=5)
        
        ttk.Button(status_frame, text='Test Ping (Google DNS)', command=self.test_ping).pack(fill='x', pady=2)
        ttk.Button(status_frame, text='Flush DNS Cache', command=self.flush_dns).pack(fill='x', pady=2)
        
        # Optimization
        opt_frame = ttk.LabelFrame(frm, text='Optimizations', padding=8)
        opt_frame.pack(fill='x', pady=5)
        
        ttk.Label(opt_frame, text='Apply these to reduce latency:', foreground='#8b949e').pack(anchor='w')
        ttk.Button(opt_frame, text='Optimize Network Stack', command=self.optimize_network).pack(fill='x', pady=2)
        ttk.Button(opt_frame, text='Apply TCP Optimizations', command=self.optimize_tcp).pack(fill='x', pady=2)
        ttk.Button(opt_frame, text='Full Reset (Requires Restart)', command=self.full_reset).pack(fill='x', pady=2)
        
        # Output
        output_frame = ttk.LabelFrame(frm, text='Log', padding=8)
        output_frame.pack(fill='both', expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(output_frame, height=15, bg='#0d1117', fg='#e6edf3',
                                                  insertbackground='#e6edf3', font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True)
        
        ttk.Button(frm, text='Clear Log', command=self.clear_log).pack(fill='x', pady=2)
        ttk.Label(frm, text='Note: Run as Administrator for full optimizations', 
                  foreground='#f85149').pack(pady=5)
        
    def log(self, msg):
        self.log_text.insert(tk.END, f'[{time.strftime("%H:%M:%S")}] {msg}\n')
        self.log_text.see(tk.END)
        self.root.update()
    
    def test_ping(self):
        self.log('Testing ping to 8.8.8.8...')
        result = self.optimizer.ping_test()
        self.log(result)
    
    def flush_dns(self):
        self.log(self.optimizer.flush_dns())
    
    def optimize_network(self):
        self.log('Optimizing network...')
        results = self.optimizer.optimize_network()
        for r in results:
            self.log(r)
        messagebox.showinfo('Done', 'Network optimizations applied')
    
    def optimize_tcp(self):
        self.log(self.optimizer.optimize_tcp())
        messagebox.showinfo('Done', 'TCP optimizations applied')
    
    def full_reset(self):
        if messagebox.askyesno('Confirm', 'This will reset network stack. Computer needs restart.\nContinue?'):
            self.log(self.optimizer.reset_network())
            messagebox.showinfo('Restart Required', 'Please restart your computer for changes to take effect')
    
    def clear_log(self):
        self.log_text.delete('1.0', tk.END)


if __name__ == '__main__':
    root = tk.Tk()
    app = PingOptimizerGUI(root)
    root.mainloop()
