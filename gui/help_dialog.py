import os
import sys
import webbrowser
import customtkinter as ctk
from PIL import Image
from gui.window_utils import center_window, bring_window_to_front

APP_NAME = "SRPCOM Download Manager"
APP_VERSION = "1.3.2"
APP_RELEASE_DATE = "Oktober 2026"

def get_asset_path(filename: str) -> str:
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(base_dir, "assets", filename)
    if os.path.exists(p):
        return p
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", filename)

class HelpAboutDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.title(f"Pusat Bantuan & Tentang - {APP_NAME}")
        self.geometry("720x640")
        self.minsize(660, 560)

        icon_path = get_asset_path("logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self._init_ui()
        center_window(self)
        bring_window_to_front(self)

    def _init_ui(self):
        # 1. Header Card
        header_card = ctk.CTkFrame(self, fg_color=("gray85", "#1A202C"), corner_radius=10)
        header_card.pack(fill="x", padx=16, pady=(16, 10))

        # Logo & App Title Container
        top_row = ctk.CTkFrame(header_card, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=14)

        logo_path = get_asset_path("logo.png")
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                self.ctk_logo = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(54, 54))
                lbl_logo = ctk.CTkLabel(top_row, image=self.ctk_logo, text="")
                lbl_logo.pack(side="left", padx=(0, 14))
            except Exception:
                pass

        text_col = ctk.CTkFrame(top_row, fg_color="transparent")
        text_col.pack(side="left", fill="both", expand=True)

        title_row = ctk.CTkFrame(text_col, fg_color="transparent")
        title_row.pack(fill="x", anchor="w")

        title_lbl = ctk.CTkLabel(
            title_row,
            text=APP_NAME,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#E53E3E"
        )
        title_lbl.pack(side="left", padx=(0, 10))

        # Version Pill Badge
        ver_badge = ctk.CTkFrame(title_row, fg_color="#2B6CB0", corner_radius=6)
        ver_badge.pack(side="left")
        ver_lbl = ctk.CTkLabel(
            ver_badge,
            text=f"v{APP_VERSION} (Terbaru)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white"
        )
        ver_lbl.pack(padx=8, pady=2)

        desc_lbl = ctk.CTkLabel(
            text_col,
            text="Akselerasi Download Cerdas, Dynamic Chunk Splitting & Media Stream Grabber",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        desc_lbl.pack(fill="x", pady=(2, 0))

        # 2. Main Tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        tab_features = self.tabview.add("🌟 Fitur Aplikasi")
        tab_changelog = self.tabview.add("📜 Riwayat Versi")
        tab_contact = self.tabview.add("💬 Kontak & Komunitas")

        self._build_features_tab(tab_features)
        self._build_changelog_tab(tab_changelog)
        self._build_contact_tab(tab_contact)

        # 3. Bottom Close Bar
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=16, pady=(0, 14), side="bottom")

        copy_lbl = ctk.CTkLabel(
            bottom_bar,
            text="© 2026 SRPCOM Technology. All rights reserved.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        copy_lbl.pack(side="left")

        close_btn = ctk.CTkButton(
            bottom_bar,
            text="Tutup",
            width=90,
            height=32,
            fg_color="#4A5568",
            hover_color="#2D3748",
            command=self.destroy
        )
        close_btn.pack(side="right")

    def _build_features_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        features = [
            (
                "⚡ Dynamic Chunk Splitting (Akselerasi Detik Terakhir)",
                "Algoritma cerdas work-stealing bergaya IDM. Ketika salah satu thread selesai lebih awal, ia secara otomatis memotong (split) sisa kuota data dari thread yang paling lambat (minimal >= 1 MB). Seluruh koneksi selalu bekerja 100% paralel hingga byte terakhir selesai diunduh."
            ),
            (
                "🛡️ Anti-403 Forbidden Engine & Sesi Browser",
                "Meneruskan Cookies sesi login, HTTP Referer, dan User-Agent dari browser ke mesin unduhan multi-thread dan yt-dlp. Mencegah error penolakan 403 Forbidden saat mengunduh dari CDN berautentikasi atau cloud storage terproteksi."
            ),
            (
                "📈 Real-Time Speed Graph Visualizer",
                "Dilengkapi kurva grafik kecepatan real-time di jendela Detail Unduhan (Speed History Graph) berwarna neon cyan dengan indikator kecepatan saat ini dan kecepatan transfer puncak (Peak Speed)."
            ),
            (
                "↔️ Kolom Tabel Resizable & Auto-Fit Nama File",
                "Setiap kolom tabel (File Name, Size, Status, Progress, Speed, Time Left, Action) dapat diubah lebarnya dengan cara drag/geser garis pemisah pada header. Nama file panjang terpotong rapi dengan ellipsis (...) dan tooltip lengkap saat diarahkan mouse."
            ),
            (
                "🚀 Pengaturan 32 Segmen Optimal (Max Speed)",
                "Dukungan koneksi paralel 1 hingga 32 threads. Tersedia tombol '⚡ Optimal (Max)' di jendela penambahan tugas untuk langsung memanfaatkan kecepatan unduhan tertinggi."
            ),
            (
                "🎬 Media Streaming & Video Downloader",
                "Ekstraksi dan unduhan paralel stream video dari YouTube, Facebook, Twitter, TikTok, dan ratusan situs lainnya dengan akselerasi multi-fragment simultan (concurrent fragment downloads)."
            ),
            (
                "🌐 Ekstensi Browser Chrome & Edge",
                "Integrasi langsung dengan browser Chromium. Menangkap unduhan secara otomatis dengan satu klik dan tombol download melayang pada video web."
            ),
            (
                "📁 Pengelompokan Kategori & Folder Kustom",
                "Otomatis mengelompokkan unduhan ke dalam kategori Video, Musik, Dokumen, Program, dan Arsip. Dilengkapi fitur 'Ingat folder ini' agar unduhan selanjutnya langsung tersimpan ke lokasi yang Anda inginkan."
            )
        ]

        for title, desc in features:
            card = ctk.CTkFrame(scroll, fg_color=("gray90", "gray17"), corner_radius=8)
            card.pack(fill="x", pady=4, padx=2)

            t_lbl = ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#38BDF8",
                anchor="w"
            )
            t_lbl.pack(fill="x", padx=12, pady=(10, 4))

            d_lbl = ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color=("gray20", "gray80"),
                anchor="w",
                justify="left",
                wraplength=600
            )
            d_lbl.pack(fill="x", padx=12, pady=(0, 10))

    def _build_changelog_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        history = [
            (
                "Versi 1.3.2",
                "29 Oktober 2026",
                "#C53030",
                [
                    "🚀 Auto-Start Windows Booting: Opsi di wizard installer untuk menjalankan SRPCOM Download Manager secara otomatis saat komputer menyala (berjalan di background / minimized siap menangkap unduhan).",
                    "🎬 IDM-Style Floating Video Grabber: Tombol download mengambang khas IDM di pojok kanan atas video YouTube kini terpasang responsif dan tidak lagi tertutup bilah kontrol atas player.",
                    "⚡ Tombol Download di Action Bar YouTube: Tombol baru 'Unduh SDM' disematkan langsung di deretan tombol aksi YouTube (bawah judul video) dengan pilihan resolusi instan (1080p, 720p, 480p, 360p, MP3).",
                    "🧩 Integrasi Ekstensi Browser & SPA Fix: Mendukung deteksi dinamis navigasi YouTube SPA (Single Page Application) dan sinkronisasi ID ekstensi Chrome Web Store & Unpacked."
                ]
            ),
            (
                "Versi 1.3.1",
                "27 Oktober 2026",
                "#2B6CB0",
                [
                    "🎬 YouTube Direct Download Fix: Perbaikan komprehensif pada pengunduhan video dan audio YouTube agar berjalan mulus tanpa error.",
                    "⚡ Otomatisasi FFmpeg & Node.js Engine: Deteksi otomatis FFmpeg dan runtime Node.js di sistem untuk penggabungan video 1080p/720p HD MP4 bebas error.",
                    "🎯 Presisi Format Kualitas: Perbaikan deteksi resolusi combo (Best Quality, 1080p, 720p, 480p, 360p, MP3) dan deteksi judul otomatis.",
                    "🛡️ Thread-Safe GUI & Error Logging: Komunikasi thread-safe antar-mesin dan antarmuka, dilengkapi pencatatan error mendalam di AppData.",
                    "📂 Penyimpanan Data Permanen: Riwayat unduhan dan preferensi disimpan abadi di AppData tanpa terpengaruh folder temporary."
                ]
            ),
            (
                "Versi 1.3.0",
                "27 Oktober 2026",
                "#00B4D8",
                [
                    "📂 Perbaikan Navigasi 'Open Folder': Menjamin Windows Explorer selalu membuka folder target unduhan dan menyorot file secara akurat tanpa pernah salah membuka Desktop.",
                    "📊 Indikator Thread Koneksi Real-time: Dialog Download Detail & Grafik Kecepatan kini secara eksplisit menampilkan jumlah thread aktif yang berjalan (baik untuk Dynamic Chunk Splitting maupun Multi-thread Fragment Video Streaming).",
                    "⚡ Optimasi Refresh Dialog Detail: Memperbaiki loop pembaruan status video stream agar grafik kurva fluktuasi kecepatan terus berjalan dinamis secara real-time.",
                    "🛠️ Stabilitas Installer: Memperbaiki force-close saat instalasi dan memastikan proses uninstaller berjalan bersih dan tanpa file terkunci."
                ]
            ),
            (
                "Versi 1.2.1",
                "27 Oktober 2026",
                "#38A169",
                [
                    "🛠️ Perbaikan Sistem Deteksi Install/Uninstall: Uninstaller mandiri dipindahkan ke folder temporary saat dijalankan sehingga folder program bersih tanpa sisa file lock.",
                    "🔄 Mode Setup Cerdas: File setup kini menampilkan opsi 'Perbarui / Pasang Ulang' atau 'Copot Pemasangan' jika aplikasi sudah terpasang, tidak langsung masuk ke layar uninstall merah.",
                    "❓ Pusat Bantuan & Dialog Tentang Aplikasi: Jendela panduan interaktif baru dengan ulasan seluruh fitur, riwayat pembaruan, dan kontak pengembang.",
                    "💬 Integrasi Komunitas Telegram: Tautan langsung ke Developer (@srpcomadmin) dan Grup Pengguna (@srpcomgroup)."
                ]
            ),
            (
                "Versi 1.2.0",
                "27 Oktober 2026",
                "#3182CE",
                [
                    "↔️ Draggable Resizable Table Columns: Lebar setiap kolom pada tabel download kini dapat diatur secara interaktif dengan drag pada header separator.",
                    "✂️ Auto-fit & Text Ellipsis: Nama file yang sangat panjang tidak lagi merusak tata letak tabel; terpotong rapi dengan '...' dan dilengkapi hover tooltip.",
                    "🚀 Pengaturan 32 Segmen Optimal: Menambahkan kontrol segmen pada toolbar utama dan tombol '⚡ Optimal (Max)' pada dialog penambahan unduhan.",
                    "⚡ Akselerasi Unduhan Video Stream: Mengaktifkan multi-fragment downloads (hingga 32 thread) pada engine video yt-dlp untuk memaksimalkan kecepatan YouTube & streaming."
                ]
            ),
            (
                "Versi 1.1.0",
                "27 Oktober 2026",
                "#805AD5",
                [
                    "🛡️ Anti-403 Forbidden Engine: Ekstensi browser meneruskan Cookie sesi, HTTP Referer, dan User-Agent ke mesin download untuk menembus CDN terlindungi.",
                    "⚡ Dynamic Chunk Splitting: Algoritma work-stealing otomatis yang membagi sisa kuota byte dari thread lambat ke thread yang menganggur.",
                    "📈 Real-time Speed Graph: Grafik kurva kecepatan real-time dengan area arsiran dan indikator kecepatan puncak.",
                    "🧩 Pembaruan Ekstensi Browser v1.2.0: Peningkatan penangkapan stream HTML5 non-YouTube."
                ]
            ),
            (
                "Versi 1.0.0",
                "23 Oktober 2026",
                "#DD6B20",
                [
                    "🚀 Rilis Perdana SRPCOM Download Manager untuk Windows.",
                    "🎨 Antarmuka modern bertema gelap berbasis CustomTkinter.",
                    "📥 Mesin unduhan multi-koneksi paralel dengan HTTP Range header.",
                    "⏸ Fitur Pause, Resume, Speed Limiter, dan manajemen antrean unduhan.",
                    "📦 Installer terintegrasi untuk instalasi desktop yang bersih."
                ]
            )
        ]

        for ver, date, color, items in history:
            card = ctk.CTkFrame(scroll, fg_color=("gray90", "gray17"), corner_radius=8)
            card.pack(fill="x", pady=5, padx=2)

            head_row = ctk.CTkFrame(card, fg_color="transparent")
            head_row.pack(fill="x", padx=12, pady=(10, 6))

            badge = ctk.CTkFrame(head_row, fg_color=color, corner_radius=5)
            badge.pack(side="left")
            b_lbl = ctk.CTkLabel(badge, text=ver, font=ctk.CTkFont(size=11, weight="bold"), text_color="white")
            b_lbl.pack(padx=8, pady=2)

            d_lbl = ctk.CTkLabel(head_row, text=f"Rilis: {date}", font=ctk.CTkFont(size=11), text_color="gray")
            d_lbl.pack(side="right")

            for item in items:
                i_lbl = ctk.CTkLabel(
                    card,
                    text=f"•  {item}",
                    font=ctk.CTkFont(size=11),
                    text_color=("gray20", "gray85"),
                    anchor="w",
                    justify="left",
                    wraplength=600
                )
                i_lbl.pack(fill="x", padx=14, pady=2)
            
            # Bottom spacer in card
            ctk.CTkFrame(card, height=6, fg_color="transparent").pack()

    def _build_contact_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        intro_lbl = ctk.CTkLabel(
            scroll,
            text="Ada pertanyaan, kendala, atau saran pengembangan fitur? Hubungi kami langsung melalui saluran resmi Telegram berikut:",
            font=ctk.CTkFont(size=12),
            text_color=("gray20", "gray85"),
            anchor="w",
            justify="left",
            wraplength=620
        )
        intro_lbl.pack(fill="x", padx=4, pady=(6, 12))

        contacts = [
            (
                "👤 Kontak Developer Resmi",
                "Hubungi langsung admin pengembang untuk bantuan teknis privat, pertanyaan lisensi, atau laporan bug secara langsung.",
                "t.me/srpcomadmin",
                "https://t.me/srpcomadmin",
                "#3182CE",
                "💬 Chat Developer"
            ),
            (
                "👥 Komunitas & Grup Diskusi Telegram",
                "Bergabunglah dengan komunitas pengguna SRPCOM Download Manager untuk berbagi tips, update versi terbaru, dan diskusi bersama.",
                "t.me/srpcomgroup",
                "https://t.me/srpcomgroup",
                "#38A169",
                "🚀 Gabung Grup Telegram"
            ),
            (
                "🌐 Repositori Resmi GitHub",
                "Lihat kode sumber terbuka, unduh rilisan binary terbaru, atau laporkan issue / kontribusi pengembangan di GitHub.",
                "github.com/srpcom/srpcom-download-manager",
                "https://github.com/srpcom/srpcom-download-manager",
                "#805AD5",
                "⭐ Buka GitHub Repository"
            )
        ]

        for title, desc, url_text, full_url, btn_color, btn_text in contacts:
            card = ctk.CTkFrame(scroll, fg_color=("gray90", "gray17"), corner_radius=8)
            card.pack(fill="x", pady=6, padx=2)

            t_lbl = ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#38BDF8",
                anchor="w"
            )
            t_lbl.pack(fill="x", padx=14, pady=(12, 4))

            d_lbl = ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color=("gray20", "gray80"),
                anchor="w",
                justify="left",
                wraplength=600
            )
            d_lbl.pack(fill="x", padx=14, pady=(0, 8))

            link_row = ctk.CTkFrame(card, fg_color="transparent")
            link_row.pack(fill="x", padx=14, pady=(0, 12))

            url_lbl = ctk.CTkLabel(
                link_row,
                text=f"🔗 {url_text}",
                font=ctk.CTkFont(size=12, underline=True),
                text_color="#63B3ED",
                anchor="w",
                cursor="hand2"
            )
            url_lbl.pack(side="left")
            url_lbl.bind("<Button-1>", lambda e, u=full_url: webbrowser.open(u))

            act_btn = ctk.CTkButton(
                link_row,
                text=btn_text,
                width=160,
                height=32,
                fg_color=btn_color,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda u=full_url: webbrowser.open(u)
            )
            act_btn.pack(side="right")
