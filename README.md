# Aim Lab — CS2 Edition

Warmup + helper **100% legal** untuk persiapan competitive CS2.
Tidak ada macro, tidak ada inject, tidak baca memory game, tidak overlay ke game.
Semua berjalan sebagai file HTML lokal / di HP sebagai browser kedua.

## File

| File | Fungsi |
|---|---|
| `index.html` | Lab teori recoil: visualisasi `R(n) / D(n) / aim(n)`, export `pattern.json` |
| `trainer.html` | Trainer spray manual — tahan klik + tarik mouse melawan recoil, dapat skor |
| `helper.html` | 11 kartu match helper: sens, round tracker, eco, crosshair, callout, reaction, tilt, warmup, VOD, display |

## Quick Start (5 menit)

1. Buka `trainer.html` → 3x spray 20 shots guide ON, 3x guide OFF. Target avg miss `< 30px`.
2. Buka `helper.html` → kartu 5: preview crosshair → ketik manual di CS2.
3. Kartu 6: cek eco sebelum force. Kartu 10: generate warmup sesuai waktu antrean.
4. Saat match: buka `helper.html` di HP — klik Win/Loss manual, tulis catatan.

## Sensitivitas CS2

- `eDPI = DPI × sens`
- Titik awal umum: 800 DPI × 1.0–1.3 ≈ eDPI 800–1040 (~40–55 cm/360).
- Konversi dari Valorant: `sens_CS2 ≈ sens_Valo × 3.18` (titik awal, fine-tune ±0.02 di Aim_Range / Deathmatch).
- Pakai kartu 1 di `helper.html` untuk hitung, lalu verifikasi 10 flick di range.

## Crosshair (ketik manual di CS2)

Preview dulu di kartu 5 `helper.html`, lalu tempel manual via console (`~`):

```
// contoh baseline pro
cl_crosshaircolor 5
cl_crosshaircolor_r 0; cl_crosshaircolor_g 255; cl_crosshaircolor_b 136
cl_crosshairsize 2; cl_crosshairthickness 1
cl_crosshairgap -2; cl_crosshairdot 0
cl_crosshair_drawoutline 1; cl_crosshair_outlinethickness 1
cl_crosshairalpha 255; cl_crosshairgap_useweaponvalue 0
cl_crosshair_dynamic_splitdist 7
cl_crosshair_dynamic_splitalpha_in 1; cl_crosshair_dynamic_splitalpha_out 0.5
```

Aturan praktis: kecil + gap negatif untuk tap, dot hanya jika nyaman di long-range.

## Display & Enemy Visibility (setting bawaan, legal)

- CS2 Settings → Video → Advanced: Model/Texture detail sesuai FPS, `Boost Player Contrast: Enabled`.
- Monitor fisik: Contrast 60–75, Black Equalizer rendah-sedang, Digital Vibrance +10…30 bertahap.
- Latihan warna musuh di `trainer.html` (slider hue + preset kuning/ungu), lalu samakan pilihan highlight di game.
- Cek 30 detik di map range: musuh jauh/dekat/latar gelap-terang harus terlihat `< 0.3 dtk`.

## Economy MR12 (kartu 6)

- Full-buy ≈ $5500 (rifle + armor + util penuh).
- Loss bonus: 1900 → 2400 → 2900 → 3400 (kalah beruntun).
- Heuristik helper: credit ≥ full-buy → BUY; cukup 60% + momentum → FORCE situasional; kalah ini masih bisa full-buy depan → SAVE; sisanya ECO (stack 1 site, pistol/armor ringan).
- Keputusan final tetap baca musuh: mereka force? OT? Timeout tersedia?

## Callout (kartu 7)

Mirage: A Ramp, Palace, Tetris, Firebox, CT, Jungle, Connector, Top Mid, Underpass, B Apps, Kitchen, Market/Window, Back B, Bench.

Inferno: Banana, Coffins, CT, Arch, Library, Top Mid, Apartments, Pit, Graveyard, Balcony, Long, Short, Back A, Back B.

Latihan: 10 kartu/hari sampai skor ≥ 90% sebelum pindah map.

## Warmup rutin (kartu 10)

- 15 mnt: trainer spray 5 mnt → DM crosshair-only 10 mnt.
- 30 mnt: + spray guide OFF 5 mnt + counter-strafe 5 mnt + reaction 3 mnt + VOD 1 round 5 mnt.
- Jangan buka trainer/helper bersamaan dengan match — pakai sebelum queue.

## Reaction benchmark (kartu 8)

- Pro `< 200 ms`, bagus `< 250 ms`, rata-rata `< 350 ms`.
- Kalau > 300 ms konsisten: cek tidur, kafein, sens terlalu tinggi, atau FPS drop.

## Tilt protocol (kartu 9)

- L1–2: lanjut, catat pola musuh.
- L3: 1 round napas — mute, 1 tugas saja (crosshair placement).
- L4–5: STOP 5 menit — berdiri, air, off-screen. Queue lagi kalau turun ke ≤ 2.

## VOD review (kartu 11)

Per round catat 1+ kategori: aim / crosshair / posisi / util / komunikasi / ekonomi + 1 kalimat perbaikan. Helper otomatis tunjuk pola terbanyak minggu ini — itu fokus latihan berikutnya.

## Legalitas

✅ LEGAL: file HTML ini, setting DPI/sens bawaan, catatan manual, timer, voice, recording (OBS/ShadowPlay), stat tracker resmi.
❌ ILEGAL: recoil macro/script/AHK, triggerbot, aim assist, crosshair overlay eksternal, auto-spray, driver macro gameplay (termasuk macro mouse untuk recoil) — risiko VAC ban permanen.

## Batas proyek

- Pattern recoil di lab/trainer adalah aproksimasi latihan, bukan data recoil asli CS2 (spray CS2 juga punya inaccuracy acak).
- Economy calculator = heuristik, bukan solver optimal.
- Semua data tersimpan di `localStorage` browser — tidak ada server, tidak ada akun.
