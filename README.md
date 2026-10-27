# ⚡ SRPCOM Download Manager (SDM)

Aplikasi Download Manager modern dan cepat untuk Windows dengan kemampuan multi-thread segmented downloading, penangkapan link video YouTube/Browser otomatis, integrasi Chrome Extension (seperti IDM), pengaturan kecepatan, dan tampilan antarmuka modern Dark Mode berlogo resmi **SRPCOM**.

---

## 🌟 Fitur Utama

1. **🚀 Multi-Thread Segmented Download (1-32 Threads)**:
   - Membagi file menjadi beberapa segmen unduhan simultan menggunakan HTTP Range request untuk memaksimalkan kecepatan koneksi internet.
2. **🎬 YouTube & Browser Video Downloader**:
   - Terintegrasi langsung dengan browser melalui **SRPCOM Extension**.
   - Muncul tombol panel melayang *"Download Video ini"* di atas video yang sedang diputar di YouTube dan web streaming.
   - Pilihan format/kualitas: Best Quality, 1080p Full HD, 720p HD, 480p SD, 360p, dan Audio Saja (MP3).
   - Deteksi judul video otomatis & bersih tanpa simbol terlarang Windows.
3. **🔔 Pop-up Langsung Layaknya IDM**:
   - Mengadopsi sistem IDM: saat link video atau file tertangkap, jendela SDM langsung melompat ke posisi paling atas (*TopMost & Foreground*) tepat di tengah layar di depan browser.
   - Pintasan keyboard: tekan `Enter` untuk langsung *Download Now*, atau `Esc` untuk *Cancel*.
4. **📁 Memory Folder per Kategori**:
   - Mengingat folder penyimpanan terakhir per kategori (misal: Video disimpan di `D:\Videos`, Musik di `D:\Music`).
5. **⏸️ Pause & Resume**:
   - Dapat menjeda dan melanjutkan unduhan kapan saja tanpa perlu mengunduh ulang dari 0%.
6. **🚦 Speed Limiter & Queue Concurrency**:
   - Batasi kecepatan download global (*Unlimited*, 256 KB/s s/d 10 MB/s).
   - Pengaturan antrean download otomatis jika mengunduh banyak file bersamaan.
7. **👁️ Segment Visualizer (Details)**:
   - Lihat status dan progres setiap bagian koneksi / thread secara visual dan *real-time*.
8. **🌐 Chrome / Edge Extension**:
   - Ekstensi browser siap pasang (`srpcom_extension.zip` & direktori ekstensi) untuk menangkap link unduhan otomatis.

---

## 📥 Download File Rilis (Release)

Silakan download versi terbaru dari menu **[Releases](https://github.com/syamsul18782/srpcom-download-manager/releases)**:

- **`SRPCOM_Setup.exe`** (~81 MB) — Installer satu klik (membuat shortcut Desktop & Start Menu, terdaftar di Windows Apps).
- **`SRPCOM Download Manager.exe`** (~37 MB) — Versi Portable tanpa perlu install, langsung klik & jalan.
- **`srpcom_extension.zip`** — Ekstensi browser Chrome / Edge.

---

## 🛠️ Menjalankan dari Source Code

### Prasyarat:
- Python 3.10+
- FFmpeg (tersedia di PATH Windows)

### Langkah:
```bash
# Clone repository
git clone https://github.com/syamsul18782/srpcom-download-manager.git
cd srpcom-download-manager

# Buat virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependensi
pip install -r requirements.txt

# Jalankan aplikasi
python main.py
```

---

## 📜 Lisensi
Dikembangkan oleh **SRPCOM** © 2026. Hak cipta dilindungi.
