use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use device_query::{DeviceQuery, DeviceState};
use rand::Rng;
use serde::{Deserialize, Serialize};
use windows::Win32::Foundation::{HWND, POINT};
use windows::Win32::UI::Input::KeyboardAndMouse::{
    SendInput, INPUT, INPUT_MOUSE, MOUSEINPUT, MOUSEEVENTF_MOVE,
};
use windows::Win32::UI::WindowsAndMessaging::{
    GetForegroundWindow, GetWindowThreadProcessId,
};
use windows::Win32::System::ProcessStatus::GetModuleBaseNameW;
use windows::Win32::System::Threading::{OpenProcess, PROCESS_QUERY_INFORMATION, PROCESS_VM_READ};

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Weapon {
    name: String,
    #[serde(default)]
    k: f64,
    #[serde(default)]
    shots: usize,
    #[serde(default)]
    delay_ms: f64,
    #[serde(default)]
    mult: f64,
    deltas: Vec<Vec<f64>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Config {
    #[serde(default)]
    weapon: Option<String>,
    #[serde(default = "def_true")]
    enabled: bool,
    #[serde(default = "def_true")]
    foreground_only: bool,
    #[serde(default = "def_cs2")]
    target_exe: String,
    #[serde(default = "def_true")]
    humanize: bool,
    #[serde(default)]
    jitter_x: f64,
    #[serde(default)]
    jitter_y: f64,
    #[serde(default = "def_true")]
    smoothing: bool,
    #[serde(default = "def_08")]
    smooth_factor: f64,
    #[serde(default = "def_true")]
    toggle_mode: bool,
}

fn def_true() -> bool { true }
fn def_cs2() -> String { "cs2.exe".to_string() }
fn def_08() -> f64 { 0.8 }

impl Default for Config {
    fn default() -> Self {
        Self {
            weapon: None,
            enabled: true,
            foreground_only: true,
            target_exe: "cs2.exe".to_string(),
            humanize: true,
            jitter_x: 0.4,
            jitter_y: 0.4,
            smoothing: true,
            smooth_factor: 0.8,
            toggle_mode: false,
        }
    }
}

#[derive(Clone)]
struct State {
    weapons: HashMap<String, Weapon>,
    current: Option<String>,
    firing: bool,
    enabled: bool,
    foreground_only: bool,
    target_exe: String,
    humanize: bool,
    jitter_x: f64,
    jitter_y: f64,
    smoothing: bool,
    smooth_factor: f64,
    toggle_mode: bool,
    last_pos: (f64, f64),
}

fn get_foreground_exe() -> String {
    unsafe {
        let hwnd: HWND = GetForegroundWindow();
        if hwnd.is_invalid() { return String::new(); }
        let mut pid: u32 = 0;
        GetWindowThreadProcessId(hwnd, Some(&mut pid));
        if pid == 0 { return String::new(); }
        let handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, false, pid);
        if handle.is_err() { return String::new(); }
        let handle = handle.unwrap();
        let mut buf = [0u16; 512];
        let len = GetModuleBaseNameW(handle, None, &mut buf);
        let _ = windows::Win32::Foundation::CloseHandle(handle);
        if len == 0 { return String::new(); }
        String::from_utf16_lossy(&buf[..len as usize]).to_lowercase()
    }
}

fn send_mouse_rel(dx: i32, dy: i32) {
    unsafe {
        let mi = MOUSEINPUT {
            dx,
            dy,
            mouseData: 0,
            dwFlags: MOUSEEVENTF_MOVE,
            time: 0,
            dwExtraInfo: 0,
        };
        let mut input = INPUT {
            r#type: windows::Win32::UI::Input::KeyboardAndMouse::INPUT_MOUSE,
            Anonymous: windows::Win32::UI::Input::KeyboardAndMouse::INPUT_0 { mi },
        };
        SendInput(&[input], std::mem::size_of::<INPUT>() as i32);
    }
}

fn load_weapons() -> HashMap<String, Weapon> {
    let mut map = HashMap::new();
    if let Ok(s) = fs::read_to_string("weapons.json") {
        if let Ok(m) = serde_json::from_str::<HashMap<String, Weapon>>(&s) {
            return m;
        }
    }
    if let Ok(s) = fs::read_to_string("pattern.json") {
        if let Ok(w) = serde_json::from_str::<Weapon>(&s) {
            map.insert("current".to_string(), w);
            return map;
        }
    }
    map
}

fn load_config() -> Config {
    if let Ok(s) = fs::read_to_string("macro_config.json") {
        if let Ok(c) = serde_json::from_str::<Config>(&s) {
            return c;
        }
    }
    Config::default()
}

fn save_config(c: &Config) {
    if let Ok(s) = serde_json::to_string_pretty(c) {
        let _ = fs::write("macro_config.json", s);
    }
}

fn main() {
    // GUI + logic will be added next; this is scaffold
    let _weapons = load_weapons();
    let _cfg = load_config();
}
