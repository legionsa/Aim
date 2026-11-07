import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

BASE = os.path.dirname(os.path.abspath(__file__))

class CS2VisualOptimizer:
    def __init__(self):
        pass
    
    @staticmethod
    def get_colorblind_presets():
        return {
            'normal': {
                'name': 'Normal',
                'description': 'Default colors',
                'console': ['cl_color 0']
            },
            'protanopia': {
                'name': 'Protanopia (Red-Blind)',
                'description': 'Better for red-green colorblind, use Yellow/Cyan',
                'console': ['cl_color 2', '// Try cl_color 1 or 3 as well'],
                'tips': ['Enemy: Yellow/Orange works best', 'Use high contrast settings']
            },
            'deuteranopia': {
                'name': 'Deuteranopia (Green-Blind)',
                'description': 'Most common colorblind type',
                'console': ['cl_color 1', '// Try cl_color 2'],
                'tips': ['Cyan/Blue enemies can be harder, Yellow recommended']
            },
            'tritanopia': {
                'name': 'Tritanopia (Blue-Blind)',
                'description': 'Blue-yellow colorblind',
                'console': ['cl_color 3'],
                'tips': ['Red/Orange enemies stand out better']
            }
        }
    
    @staticmethod
    def get_video_recommendations():
        return {
            'display': [
                {'setting': 'Resolution', 'value': 'Native (e.g., 1920x1080)', 'note': 'Best clarity'},
                {'setting': 'Display Mode', 'value': 'Fullscreen', 'note': 'Less input lag'},
                {'setting': 'Refresh Rate', 'value': 'Max (240Hz/360Hz)', 'note': 'Smoother'},
                {'setting': 'V-Sync', 'value': 'Disabled', 'note': 'Less input lag'},
            ],
            'advanced_video': [
                {'setting': 'Brightness', 'value': '95%', 'note': 'Adjust to preference'},
                {'setting': 'Contrast', 'value': '115%', 'note': 'Higher helps spot enemies'},
                {'setting': 'Color Mode', 'value': 'Computer Monitor', 'note': 'More vibrant'},
                {'setting': 'Boost Player Contrast', 'value': 'Enabled', 'note': 'IMPORTANT - makes enemies pop'},
                {'setting': 'Wait for Vertical Sync', 'value': 'Disabled', 'note': ''},
                {'setting': 'Current Video Values Preset', 'value': 'Custom', 'note': ''},
            ],
            'effects': [
                {'setting': 'Anti-Aliasing', 'value': 'Off', 'note': '+Performance'},
                {'setting': 'Shadows', 'value': 'Low/Very Low', 'note': '+Performance, clearer'},
                {'setting': 'Model / Texture Detail', 'value': 'Medium/Low', 'note': 'Balance'},
                {'setting': 'Effects Detail', 'value': 'Low', 'note': '+Performance'},
                {'setting': 'Post Processing', 'value': 'Low', 'note': '+Performance'},
                {'setting': 'Motion Blur', 'value': 'Disabled', 'note': 'Clearer'},
                {'setting': 'Ambient Occlusion', 'value': 'Disabled', 'note': '+Performance'},
                {'setting': 'Screen Space Reflections', 'value': 'Off/Low', 'note': '+Performance'},
            ]
        }
    
    @staticmethod
    def get_nvidia_amd_tips():
        return {
            'nvidia': [
                'Image Sharpening: On (if available)',
                'Digital Vibrance: +10 to +15 (very effective)',
                'Low Latency Mode: On/Ultra',
                'Power Management: Prefer Maximum Performance',
                'Ambient Occlusion: Off',
                'Anisotropic Filtering: Application-controlled',
            ],
            'amd': [
                'Radeon Image Sharpening: On',
                'Saturate: +5 to +10',
                'Radeon Anti-Lag: Enabled',
                'Radeon Chill: Disabled',
                'Wait for Vertical Refresh: Off',
                'Power Efficiency Mode: Off',
            ]
        }


class CS2VisualGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('CS2 Visual Optimizer - Better Enemy Visibility')
        self.root.geometry('580x650')
        self.optimizer = CS2VisualOptimizer()
        
        notebook = ttk.Notebook(root)
        notebook.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Tab 1: Video Settings
        tab1 = ttk.Frame(notebook, padding=10)
        notebook.add(tab1, text='Video Settings')
        self.create_video_tab(tab1)
        
        # Tab 2: Colors & Visibility
        tab2 = ttk.Frame(notebook, padding=10)
        notebook.add(tab2, text='Enemy Colors')
        self.create_color_tab(tab2)
        
        # Tab 3: Console Commands
        tab3 = ttk.Frame(notebook, padding=10)
        notebook.add(tab3, text='Console Commands')
        self.create_console_tab(tab3)
        
        # Tab 4: GPU Settings
        tab4 = ttk.Frame(notebook, padding=10)
        notebook.add(tab4, text='GPU Settings')
        self.create_gpu_tab(tab4)
        
    def create_video_tab(self, parent):
        ttk.Label(parent, text='Recommended Video Settings for CS2', 
                  font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 10))
        
        recs = self.optimizer.get_video_recommendations()
        
        for section, items in recs.items():
            frame = ttk.LabelFrame(parent, text=section.replace('_', ' ').title(), padding=8)
            frame.pack(fill='x', pady=4)
            for item in items:
                row = ttk.Frame(frame)
                row.pack(fill='x', pady=1)
                ttk.Label(row, text=f"• {item['setting']}: ", font=('Arial', 9, 'bold')).pack(side='left')
                ttk.Label(row, text=item['value'], foreground='#3fb950').pack(side='left')
                if item['note']:
                    ttk.Label(row, text=f"  ({item['note']})", foreground='#8b949e').pack(side='left')
        
        ttk.Label(parent, text='TIP: Boost Player Contrast is the most important setting for spotting enemies!',
                  foreground='#f85149', wraplength=550).pack(pady=10)
    
    def create_color_tab(self, parent):
        ttk.Label(parent, text='Enemy Color Recommendations', 
                  font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 10))
        
        ttk.Label(parent, text='Find what works best for YOU by testing in training/DM:',
                  foreground='#8b949e').pack(anchor='w')
        
        presets = self.optimizer.get_colorblind_presets()
        
        for key, preset in presets.items():
            frame = ttk.LabelFrame(parent, text=preset['name'], padding=8)
            frame.pack(fill='x', pady=4)
            ttk.Label(frame, text=preset['description']).pack(anchor='w')
            if 'console' in preset:
                for cmd in preset['console']:
                    ttk.Label(frame, text=f'  Console: {cmd}', foreground='#79c0ff', font=('Consolas', 9)).pack(anchor='w')
            if 'tips' in preset:
                for tip in preset['tips']:
                    ttk.Label(frame, text=f'  • {tip}', foreground='#8b949e').pack(anchor='w')
        
        # Color picker preview
        preview_frame = ttk.LabelFrame(parent, text='Color Test', padding=8)
        preview_frame.pack(fill='x', pady=10)
        ttk.Label(preview_frame, text='Test these colors in-game: Yellow, Cyan, Orange, Pink').pack()
        
    def create_console_tab(self, parent):
        ttk.Label(parent, text='Useful Console Commands', 
                  font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 10))
        
        ttk.Label(parent, text='Open console with  or ~ in-game', foreground='#8b949e').pack(anchor='w')
        
        commands = [
            ('cl_color X', 'Change teammate/enemy colors (0-4, try different values)'),
            ('cl_hud_color X', 'Change HUD color (0-10)'),
            ('r_drawtracers_firstperson 0', 'Remove first person tracers (cleaner view)'),
            ('cl_showfps 0', 'Disable FPS counter if not needed'),
            ('net_graph 0', 'Disable net graph'),
            ('mat_queue_mode 2', 'Multi-threaded rendering (performance)'),
            ('fps_max 0', 'Unlimited FPS (or set to your refresh rate)'),
            ('cl_crosshair_sniper_width 1', 'Better sniper crosshair'),
        ]
        
        for cmd, desc in commands:
            frame = ttk.Frame(parent)
            frame.pack(fill='x', pady=2)
            ttk.Label(frame, text=f'{cmd}', foreground='#79c0ff', font=('Consolas', 9)).pack(side='left')
            ttk.Label(frame, text=f' - {desc}', foreground='#8b949e').pack(side='left', padx=5)
        
        # Copy section
        copy_frame = ttk.LabelFrame(parent, text='Quick Copy', padding=8)
        copy_frame.pack(fill='x', pady=10)
        autoexec = '''// Add to autoexec.cfg in cfg folder
cl_color 1
r_drawtracers_firstperson 0
mat_queue_mode 2
cl_hud_color 5'''
        text = tk.Text(copy_frame, height=6, bg='#0d1117', fg='#e6edf3', font=('Consolas', 9))
        text.pack(fill='x')
        text.insert('1.0', autoexec)
        text.config(state='disabled')
        
    def create_gpu_tab(self, parent):
        ttk.Label(parent, text='GPU Control Panel Settings', 
                  font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 10))
        
        tips = self.optimizer.get_nvidia_amd_tips()
        
        nvidia_frame = ttk.LabelFrame(parent, text='NVIDIA Control Panel', padding=8)
        nvidia_frame.pack(fill='x', pady=4)
        for tip in tips['nvidia']:
            ttk.Label(nvidia_frame, text=f'• {tip}').pack(anchor='w')
        
        amd_frame = ttk.LabelFrame(parent, text='AMD Radeon Software', padding=8)
        amd_frame.pack(fill='x', pady=4)
        for tip in tips['amd']:
            ttk.Label(amd_frame, text=f'• {tip}').pack(anchor='w')
        
        ttk.Label(parent, text='Note: These are applied outside CS2 in your GPU control panel',
                  foreground='#8b949e', wraplength=550).pack(pady=10)


if __name__ == '__main__':
    root = tk.Tk()
    app = CS2VisualGUI(root)
    root.mainloop()
