#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use eframe::egui;
use std::process::Command;
use sysinfo::{System, ProcessRefreshKind};

#[derive(Default)]
struct XS2Optimizer {
    selected_tab: usize,
    system: System,
    ping_log: String,
    gamemode_active: bool,
}

impl eframe::App for XS2Optimizer {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::TopBottomPanel::top("top_panel").show(ctx, |ui| {
            ui.horizontal(|ui| {
                ui.heading("XS2 Optimizer");
                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    ui.label("Gaming Suite");
                });
            });
        });

        egui::SidePanel::left("side_panel").min_width(150.0).show(ctx, |ui| {
            ui.add_space(10.0);
            if ui.selectable_label(self.selected_tab == 0, "Kill Ping").clicked() {
                self.selected_tab = 0;
            }
            if ui.selectable_label(self.selected_tab == 1, "Game Mode").clicked() {
                self.selected_tab = 1;
            }
            if ui.selectable_label(self.selected_tab == 2, "CS2 Visuals").clicked() {
                self.selected_tab = 2;
            }
            if ui.selectable_label(self.selected_tab == 3, "Info").clicked() {
                self.selected_tab = 3;
            }
        });

        egui::CentralPanel::default().show(ctx, |ui| {
            match self.selected_tab {
                0 => self.show_ping_tab(ui),
                1 => self.show_gamemode_tab(ui),
                2 => self.show_cs2_tab(ui),
                3 => self.show_info_tab(ui),
                _ => {}
            }
        });

        ctx.request_repaint_after(std::time::Duration::from_secs(2));
    }
}

impl XS2Optimizer {
    fn new(_cc: &eframe::CreationContext<'_>) -> Self {
        let mut system = System::new_all();
        system.refresh_processes_specifics(ProcessRefreshKind::new());
        Self {
            selected_tab: 0,
            system,
            ping_log: String::new(),
            gamemode_active: false,
        }
    }

    fn show_ping_tab(&mut self, ui: &mut egui::Ui) {
        ui.heading("Network Latency Optimizer");
        ui.label("Reduce ping & optimize network stack");
        ui.add_space(10.0);

        ui.group(|ui| {
            ui.label(egui::RichText::new("Quick Actions").strong());
            ui.add_space(5.0);
            if ui.button("Test Ping (8.8.8.8)").clicked() {
                self.run_ping_test();
            }
            if ui.button("Flush DNS Cache").clicked() {
                let _ = Command::new("ipconfig").args(["/flushdns"]).spawn();
                self.ping_log.push_str(&format!("[{}] DNS cache flushed\n", chrono_time()));
            }
            if ui.button("Reset Winsock + TCP/IP").clicked() {
                let _ = Command::new("netsh").args(["winsock", "reset"]).spawn();
                let _ = Command::new("netsh").args(["int", "ip", "reset"]).spawn();
                self.ping_log.push_str(&format!("[{}] Network stack reset (restart recommended)\n", chrono_time()));
            }
        });

        ui.add_space(10.0);
        ui.group(|ui| {
            ui.label(egui::RichText::new("Output Log").strong());
            egui::ScrollArea::vertical().max_height(250.0).show(ui, |ui| {
                ui.add(egui::TextEdit::multiline(&mut self.ping_log)
                    .code_editor()
                    .desired_width(f32::INFINITY)
                    .desired_rows(12));
            });
            if ui.button("Clear Log").clicked() {
                self.ping_log.clear();
            }
        });
        ui.label(egui::RichText::new("Run as Administrator for full effect").color(egui::Color32::RED));
    }

    fn run_ping_test(&mut self) {
        self.ping_log.push_str(&format!("[{}] Testing ping...\n", chrono_time()));
        if let Ok(output) = Command::new("ping").args(["-n", "4", "8.8.8.8"]).output() {
            let s = String::from_utf8_lossy(&output.stdout);
            self.ping_log.push_str(&s);
            self.ping_log.push('\n');
        }
    }

    fn show_gamemode_tab(&mut self, ui: &mut egui::Ui) {
        ui.heading("Game Mode - Free Up RAM");
        ui.label("Kill memory hungry apps while gaming");
        ui.add_space(10.0);

        self.system.refresh_memory();
        ui.group(|ui| {
            ui.label(egui::RichText::new("System Resources").strong());
            ui.label(format!("RAM: {} GB / {} GB", 
                self.system.used_memory() / 1024 / 1024 / 1024,
                self.system.total_memory() / 1024 / 1024 / 1024));
        });

        ui.add_space(10.0);
        ui.group(|ui| {
            ui.label(egui::RichText::new("Control").strong());
            if !self.gamemode_active {
                if ui.button("ENABLE GAME MODE").clicked() {
                    self.enable_game_mode();
                    self.gamemode_active = true;
                }
            } else {
                if ui.button("DISABLE GAME MODE").clicked() {
                    self.gamemode_active = false;
                }
                ui.label(egui::RichText::new("ACTIVE").color(egui::Color32::GREEN));
            }
        });

        ui.add_space(10.0);
        ui.group(|ui| {
            ui.label(egui::RichText::new("Apps To Kill").strong());
            egui::ScrollArea::vertical().max_height(200.0).show(ui, |ui| {
                let apps = ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "discord.exe", 
                           "spotify.exe", "steamwebhelper.exe", "teams.exe", "slack.exe", "zoom.exe",
                           "whatsapp.exe", "telegram.exe", "obs64.exe", "streamlabs.exe", 
                           "dropbox.exe", "onedrive.exe", "wallpaperengine.exe", "rainmeter.exe"];
                for app in apps {
                    ui.label(format!("• {}", app));
                }
            });
        });
        ui.label(egui::RichText::new("Closed apps must be reopened manually").color(egui::Color32::YELLOW));
    }

    fn enable_game_mode(&mut self) {
        let targets = ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "discord.exe", 
                      "spotify.exe", "steamwebhelper.exe", "teams.exe", "slack.exe", "zoom.exe",
                      "whatsapp.exe", "telegram.exe", "obs64.exe", "streamlabs.exe", 
                      "dropbox.exe", "onedrive.exe", "wallpaperengine.exe", "rainmeter.exe"];
        self.system.refresh_processes_specifics(ProcessRefreshKind::new());
        for (_pid, process) in self.system.processes() {
            let name = process.name().to_lowercase();
            for t in &targets {
                if name == t.to_lowercase() && !name.contains("xs2") {
                    let _ = Command::new("taskkill").args(["/F", "/IM", process.name()]).spawn();
                    break;
                }
            }
        }
    }

    fn show_cs2_tab(&mut self, ui: &mut egui::Ui) {
        ui.heading("CS2 Visual Optimizer");
        ui.label("Better enemy visibility & contrast");
        ui.add_space(10.0);

        egui::CollapsingHeader::new("In-Game Video Settings")
            .default_open(true)
            .show(ui, |ui| {
                let settings = [
                    ("Resolution", "Native (1920x1080)", "Best clarity"),
                    ("Display Mode", "Fullscreen", "Less input lag"),
                    ("Refresh Rate", "Max", "Smoother"),
                    ("V-Sync", "Disabled", "Less input lag"),
                    ("Brightness", "90-100%", ""),
                    ("Contrast", "110-120%", "Higher = easier to spot"),
                    ("Color Mode", "Computer Monitor", "More vibrant"),
                    ("Boost Player Contrast", "ENABLED", "MOST IMPORTANT"),
                    ("Motion Blur", "Disabled", "Cleaner"),
                    ("Shadows", "Low/Very Low", "Better visibility"),
                    ("Effects", "Low", "Better visibility"),
                    ("Anti-Aliasing", "Off", "Better performance/clarity"),
                ];
                for (s, v, n) in settings {
                    ui.horizontal(|ui| {
                        ui.label(format!("• {}:", s));
                        ui.label(egui::RichText::new(v).color(egui::Color32::from_rgb(46, 125, 50)));
                        if !n.is_empty() {
                            ui.label(egui::RichText::new(format!("({})", n)).color(egui::Color32::GRAY));
                        }
                    });
                }
            });

        egui::CollapsingHeader::new("Enemy Colors")
            .default_open(true)
            .show(ui, |ui| {
                ui.label("Recommended: cl_color 1 (Yellow) - Best for most maps");
                ui.label("Try different values 0-4 to find what works best");
            });

        egui::CollapsingHeader::new("GPU Settings")
            .default_open(false)
            .show(ui, |ui| {
                ui.label(egui::RichText::new("NVIDIA").strong());
                ui.label("• Image Sharpening: On");
                ui.label("• Digital Vibrance: +10 to +15");
                ui.label("• Low Latency Mode: On/Ultra");
                ui.label("• Power Management: Prefer Maximum Performance");
                ui.add_space(5.0);
                ui.label(egui::RichText::new("AMD").strong());
                ui.label("• Radeon Image Sharpening: On");
                ui.label("• Radeon Anti-Lag: Enabled");
                ui.label("• Radeon Chill: Disabled");
            });
    }

    fn show_info_tab(&mut self, ui: &mut egui::Ui) {
        ui.heading("XS2 Optimizer");
        ui.label("Gaming Optimization Suite for CS2 & FPS Games");
        ui.add_space(10.0);
        ui.separator();
        ui.add_space(10.0);
        ui.label(egui::RichText::new("Features").strong());
        ui.label("• Kill Ping - Network latency reduction");
        ui.label("• Game Mode - Free up RAM by killing background apps");
        ui.label("• CS2 Visuals - Better enemy visibility settings");
        ui.add_space(10.0);
        ui.separator();
        ui.add_space(10.0);
        ui.label(egui::RichText::new("Tips").strong());
        ui.label("1. Enable Game Mode before launching CS2");
        ui.label("2. Run as Administrator for network optimizations");
        ui.label("3. Enable Boost Player Contrast in CS2 video settings");
        ui.label("4. Use Yellow enemy color (cl_color 1)");
    }
}

fn chrono_time() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();
    format!("{}", now.as_secs() % 86400)
}

fn main() -> eframe::Result<()> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([620.0, 680.0])
            .with_min_inner_size([580.0, 640.0])
            .with_title("XS2 Optimizer"),
        ..Default::default()
    };
    eframe::run_native(
        "XS2 Optimizer",
        options,
        Box::new(|cc| Ok(Box::new(XS2Optimizer::new(cc)))),
    )
}
