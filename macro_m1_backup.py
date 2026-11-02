import json
import os
import time
import threading
import random
import ctypes
import tkinter as tk
from tkinter import ttk

import pyautogui
from pynput import mouse, keyboard

pyautogui.FAILSAFE = True

BASE = os.path.dirname(os.path.abspath(__file__))
WEAPONS_PATH = os.path.join(BASE, 'weapons.json')
PATTERN_PATH = os.path.join(BASE, 'pattern.json')
CONFIG_PATH = os.path.join(BASE, 'macro_config.json')

# SendInput for better compatibility with fullscreen games
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
