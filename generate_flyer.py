import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_flyer():
    W, H = 1200, 1200
    # Create base RGBA canvas
    img = Image.new("RGBA", (W, H), (11, 15, 25, 255))
    draw = ImageDraw.Draw(img)

    # 1. Gradient Background
    for y in range(H):
        ratio = y / H
        if ratio < 0.55:
            local = ratio / 0.55
            r = int(12 + (20 - 12) * local)
            g = int(16 + (30 - 16) * local)
            b = int(28 + (50 - 28) * local)
        else:
            local = (ratio - 0.55) / 0.45
            r = int(20 + (10 - 20) * local)
            g = int(30 + (14 - 30) * local)
            b = int(50 + (24 - 50) * local)
        draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    # Glow overlay layer
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    # Red accent glow top-left
    glow_draw.ellipse([(-100, -100), (450, 450)], fill=(197, 48, 48, 45))
    # Cyan accent glow top-right
    glow_draw.ellipse([(W - 450, -80), (W + 150, 500)], fill=(0, 180, 216, 40))
    # Blue accent glow center-bottom
    glow_draw.ellipse([(W//2 - 400, H - 380), (W//2 + 400, H + 100)], fill=(43, 108, 176, 50))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Fonts loader
    def get_font(name_variant, size):
        font_dir = "C:/Windows/Fonts"
        candidates = {
            "black": ["seguibl.ttf", "arialbd.ttf"],
            "bold": ["segoeuib.ttf", "arialbd.ttf"],
            "semibold": ["seguisb.ttf", "segoeuib.ttf"],
            "regular": ["segoeui.ttf", "arial.ttf"],
            "light": ["segoeuil.ttf", "arial.ttf"]
        }
        for fname in candidates.get(name_variant, ["segoeui.ttf"]):
            p = os.path.join(font_dir, fname)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    font_badge = get_font("bold", 17)
    font_title = get_font("black", 50)
    font_sub = get_font("semibold", 21)
    font_card_title = get_font("bold", 22)
    font_card_desc = get_font("regular", 15)
    font_footer_bold = get_font("bold", 18)
    font_footer_regular = get_font("regular", 16)
    font_tag = get_font("bold", 15)
    font_tbl_header = get_font("bold", 11)
    font_tbl_cell = get_font("semibold", 11)
    font_tbl_sm = get_font("regular", 10)

    # Vector Drawing Helpers
    def draw_lightning(d, cx, cy, size, color):
        s = size
        pts = [
            (cx - s*0.15, cy - s*0.5),
            (cx + s*0.35, cy - s*0.5),
            (cx - s*0.05, cy - s*0.05),
            (cx + s*0.45, cy - s*0.05),
            (cx - s*0.35, cy + s*0.5),
            (cx - s*0.05, cy + s*0.1),
            (cx - s*0.35, cy + s*0.1)
        ]
        d.polygon(pts, fill=color)

    def draw_play(d, cx, cy, size, color):
        s = size
        pts = [
            (cx - s*0.3, cy - s*0.4),
            (cx + s*0.42, cy),
            (cx - s*0.3, cy + s*0.4)
        ]
        d.polygon(pts, fill=color)

    def draw_shield(d, cx, cy, size, color):
        s = size
        pts = [
            (cx - s*0.35, cy - s*0.42),
            (cx + s*0.35, cy - s*0.42),
            (cx + s*0.35, cy + s*0.06),
            (cx, cy + s*0.46),
            (cx - s*0.35, cy + s*0.06)
        ]
        d.polygon(pts, fill=color)
        d.line([(cx - s*0.16, cy - s*0.02), (cx - s*0.04, cy + s*0.12), (cx + s*0.18, cy - s*0.14)], fill=(255, 255, 255), width=max(2, int(s*0.1)))

    def draw_chart(d, cx, cy, size, color):
        s = size
        # 3 bars
        d.rectangle([cx - s*0.36, cy + s*0.05, cx - s*0.16, cy + s*0.4], fill=color)
        d.rectangle([cx - s*0.10, cy - s*0.18, cx + s*0.10, cy + s*0.4], fill=color)
        d.rectangle([cx + s*0.16, cy - s*0.40, cx + s*0.36, cy + s*0.4], fill=color)

    def draw_bell(d, cx, cy, size, color):
        s = size
        # Bell body
        d.ellipse([cx - s*0.28, cy - s*0.38, cx + s*0.28, cy + s*0.2], fill=color)
        d.rectangle([cx - s*0.38, cy + s*0.05, cx + s*0.38, cy + s*0.25], fill=color)
        d.ellipse([cx - s*0.1, cy + s*0.25, cx + s*0.1, cy + s*0.42], fill=color)

    def draw_split(d, cx, cy, size, color):
        s = size
        # Two arrows pointing outward
        # Left arrow
        d.polygon([(cx - s*0.42, cy), (cx - s*0.12, cy - s*0.3), (cx - s*0.12, cy + s*0.3)], fill=color)
        # Right arrow
        d.polygon([(cx + s*0.42, cy), (cx + s*0.12, cy - s*0.3), (cx + s*0.12, cy + s*0.3)], fill=color)
        # Center divider
        d.rectangle([cx - s*0.05, cy - s*0.38, cx + s*0.05, cy + s*0.38], fill=(255, 255, 255, 180))

    # Load Official Logo
    logo_path = "assets/logo_srpcom.png"
    logo_img = None
    if os.path.exists(logo_path):
        logo_img = Image.open(logo_path).convert("RGBA")
        logo_img = logo_img.resize((96, 96), Image.Resampling.LANCZOS)

    # --- TOP HEADER SECTION ---
    # Top Version Badge Pill
    pill_text = "APLIKASI WINDOWS  •  ALTERNATIF IDM TERBAIK  •  VERSI 1.3.3 TERBARU"
    bbox = font_badge.getbbox(pill_text)
    pw = bbox[2] - bbox[0] + 55
    ph = 36
    px = (W - pw) // 2
    py = 32
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=18, fill=(22, 32, 54, 235), outline=(0, 180, 216, 190), width=1)
    # Draw mini vector lightning in badge
    draw_lightning(draw, px + 22, py + 18, 16, (0, 220, 255))
    draw.text((px + 38, py + 7), pill_text, font=font_badge, fill=(0, 220, 255))

    # Header Title Area
    header_y = 86
    if logo_img:
        img.paste(logo_img, (60, header_y + 4), logo_img)
        title_x = 175
    else:
        title_x = 60

    # Title with subtle 3D drop shadow
    draw.text((title_x + 2, header_y + 2), "SRPCOM DOWNLOAD MANAGER", font=font_title, fill=(0, 0, 0, 180))
    draw.text((title_x, header_y), "SRPCOM DOWNLOAD MANAGER", font=font_title, fill=(255, 255, 255))

    # Subtitle
    sub_text = "Akselerasi Download Multi-Thread Hingga 32 Koneksi & YouTube Video Grabber"
    draw.text((title_x, header_y + 62), sub_text, font=font_sub, fill=(160, 180, 205))

    # --- MIDDLE SECTION: APP SCREENSHOT PREVIEW WITH LIVE DOWNLOAD ROWS ---
    preview_y = 202
    preview_path = "assets/tangkapan_layar_1280x800.png"
    if os.path.exists(preview_path):
        preview_raw = Image.open(preview_path).convert("RGBA")
        raw_w, raw_h = preview_raw.size
        # Draw mock active download rows directly onto preview_raw before resizing!
        p_draw = ImageDraw.Draw(preview_raw)
        
        # Table area in 1280x800:
        # Table Header: y ~ 140
        # Rows start at y = 170, row_height = 48
        rows_data = [
            (
                "Yeni Inka X Yesa Oktavia - MIMPI MANIS.mp4",
                "561.8 MB",
                "Downloading",
                "#3182CE",
                0.72,
                "72.4%",
                "8.45 MB/s",
                "00:18",
                "pause",
                "#DD6B20"
            ),
            (
                "Windows_11_Enterprise_24H2_x64.iso",
                "4.82 GB",
                "Downloading",
                "#3182CE",
                0.48,
                "48.1%",
                "14.20 MB/s",
                "02:45",
                "pause",
                "#DD6B20"
            ),
            (
                "Yeni Inka - HIDUPKU SEPI TANPAMU.mp4",
                "52.4 MB",
                "Completed",
                "#38A169",
                1.0,
                "100.0%",
                "-",
                "-",
                "folder",
                "#4A5568"
            ),
            (
                "DJ DENOK KONSER NDX AKA FULL SONG.mp4",
                "37.1 MB",
                "Completed",
                "#38A169",
                1.0,
                "100.0%",
                "-",
                "-",
                "folder",
                "#4A5568"
            )
        ]

        # Draw rows on preview_raw
        row_x = 180
        row_w = raw_w - row_x - 30
        row_start_y = 175
        r_height = 50
        
        p_font_bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
        p_font_reg = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)

        for i, (fname, fsize, status, st_color, pct_val, pct_txt, speed, eta, btn_type, btn_color) in enumerate(rows_data):
            ry = row_start_y + i * (r_height + 6)
            # Row bg
            bg_c = (38, 44, 56, 255) if i % 2 == 0 else (32, 38, 50, 255)
            p_draw.rounded_rectangle([row_x, ry, row_x + row_w, ry + r_height], radius=6, fill=bg_c)

            # File name (guaranteed safe width)
            p_draw.text((row_x + 15, ry + 16), fname, font=p_font_bold, fill=(240, 245, 255))

            # Size
            p_draw.text((row_x + 440, ry + 16), fsize, font=p_font_reg, fill=(190, 200, 215))

            # Status
            p_draw.text((row_x + 540, ry + 16), status, font=p_font_bold, fill=st_color)

            # Progress Bar & %
            bar_x = row_x + 655
            bar_y = ry + 20
            bar_w = 120
            bar_h = 10
            p_draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=5, fill=(50, 58, 75))
            fill_w = int(bar_w * pct_val)
            p_draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], radius=5, fill=st_color)
            p_draw.text((bar_x + bar_w + 10, ry + 16), pct_txt, font=p_font_bold, fill=(240, 245, 255))

            # Speed
            p_draw.text((row_x + 850, ry + 16), speed, font=p_font_bold if speed != "-" else p_font_reg, fill=(0, 210, 255) if speed != "-" else (160, 170, 185))

            # ETA
            p_draw.text((row_x + 940, ry + 16), eta, font=p_font_reg, fill=(190, 200, 215))

            # Quick Action Button (Vector icon)
            btn_x = row_x + row_w - 45
            p_draw.rounded_rectangle([btn_x, ry + 10, btn_x + 32, ry + 40], radius=6, fill=btn_color)
            bcx, bcy = btn_x + 16, ry + 25
            if btn_type == "pause":
                p_draw.rectangle([bcx - 5, bcy - 6, bcx - 2, bcy + 6], fill=(255, 255, 255))
                p_draw.rectangle([bcx + 2, bcy - 6, bcx + 5, bcy + 6], fill=(255, 255, 255))
            else:
                # Folder icon vector
                p_draw.rectangle([bcx - 7, bcy - 3, bcx + 7, bcy + 6], fill=(255, 255, 255))
                p_draw.polygon([(bcx - 7, bcy - 3), (bcx - 3, bcy - 6), (bcx + 2, bcy - 6), (bcx + 4, bcy - 3)], fill=(255, 255, 255))

        # Target preview size in flyer
        pw, ph = 760, 440
        preview_resized = preview_raw.resize((pw, ph), Image.Resampling.LANCZOS)

        # Make rounded corners on preview
        mask = Image.new("L", (pw, ph), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, pw, ph], radius=14, fill=255)

        card_x = (W - pw) // 2
        card_y = preview_y

        # Drop shadow behind screenshot
        shadow = Image.new("RGBA", (pw + 60, ph + 60), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow)
        s_draw.rounded_rectangle([15, 15, pw + 45, ph + 45], radius=16, fill=(0, 0, 0, 190))
        shadow = shadow.filter(ImageFilter.GaussianBlur(14))
        img.paste(shadow, (card_x - 30, card_y - 30), shadow)
        draw = ImageDraw.Draw(img)

        # Outer glow border
        draw.rounded_rectangle([card_x - 3, card_y - 3, card_x + pw + 3, card_y + ph + 3], radius=16, outline=(49, 130, 206, 220), width=3)
        img.paste(preview_resized, (card_x, card_y), mask)

        # Side Floating Feature Badges over/beside screenshot (No missing glyphs!)
        left_tags = [
            ("32 Multi-Threads", "#C53030", "#FFEAEA", "lightning"),
            ("YouTube 1080p / MP3", "#2B6CB0", "#EBF8FF", "play"),
            ("Anti-403 Cookies", "#2F855A", "#F0FFF4", "shield")
        ]
        tag_y = card_y + 40
        for tag_text, bg_col, text_col, icon_type in left_tags:
            tbox = font_tag.getbbox(tag_text)
            tw = tbox[2] - tbox[0] + 50
            th = 40
            draw.rounded_rectangle([32, tag_y, 32 + tw, tag_y + th], radius=10, fill=(18, 24, 38, 245), outline=bg_col, width=2)
            # Draw vector icon inside pill
            if icon_type == "lightning":
                draw_lightning(draw, 48, tag_y + 20, 14, bg_col)
            elif icon_type == "play":
                draw_play(draw, 48, tag_y + 20, 14, bg_col)
            elif icon_type == "shield":
                draw_shield(draw, 48, tag_y + 20, 14, bg_col)
            draw.text((62, tag_y + 9), tag_text, font=font_tag, fill=text_col)
            tag_y += 62

        right_tags = [
            ("Dynamic Chunk Splitting", "#805AD5", "#FAF5FF", "split"),
            ("IDM-Style Topmost Popup", "#D69E2E", "#FFFFF0", "bell"),
            ("Real-time Speed Graph", "#00B4D8", "#E6FFFA", "chart")
        ]
        tag_y = card_y + 40
        for tag_text, bg_col, text_col, icon_type in right_tags:
            tbox = font_tag.getbbox(tag_text)
            tw = tbox[2] - tbox[0] + 50
            th = 40
            tx = W - 32 - tw
            draw.rounded_rectangle([tx, tag_y, tx + tw, tag_y + th], radius=10, fill=(18, 24, 38, 245), outline=bg_col, width=2)
            if icon_type == "split":
                draw_split(draw, tx + 16, tag_y + 20, 14, bg_col)
            elif icon_type == "bell":
                draw_bell(draw, tx + 16, tag_y + 20, 14, bg_col)
            elif icon_type == "chart":
                draw_chart(draw, tx + 16, tag_y + 20, 14, bg_col)
            draw.text((tx + 30, tag_y + 9), tag_text, font=font_tag, fill=text_col)
            tag_y += 62

    # --- FEATURE CARDS SECTION (2 Columns x 3 Rows) ---
    features = [
        (
            "Multi-Thread Max 32 Segmen",
            "Membagi file hingga 32 koneksi simultan (HTTP Range). Mengoptimalkan unduhan hingga 5x lipat lebih cepat.",
            "#3182CE",
            "lightning"
        ),
        (
            "YouTube & Web Video Grabber",
            "Tombol download melayang di Chrome & Edge. Unduh 1080p, 720p HD MP4, atau ekstrak audio MP3 bebas error.",
            "#E53E3E",
            "play"
        ),
        (
            "Dynamic Chunk Splitting",
            "Algoritma cerdas IDM: thread menganggur mencuri sisa byte dari thread lambat agar ngebut hingga detik akhir.",
            "#805AD5",
            "split"
        ),
        (
            "IDM-Style Topmost Pop-up",
            "Tangkap link download otomatis! Jendela dialog langsung melompat ke depan layar saat klik link atau copy URL.",
            "#DD6B20",
            "bell"
        ),
        (
            "Anti-403 & Cookies Bypass",
            "Oper cookies & user-agent browser otomatis. Bebas dari error Forbidden 403 di berbagai situs hosting file.",
            "#38A169",
            "shield"
        ),
        (
            "Speed History Visualizer",
            "Pantau kurva fluktuasi kecepatan internet secara visual dan inspeksi progres tiap thread segmen real-time.",
            "#00B4D8",
            "chart"
        )
    ]

    grid_y = 675
    card_w = 525
    card_h = 100
    gap_x = 30
    gap_y = 16
    start_x = (W - (card_w * 2 + gap_x)) // 2

    for idx, (ftitle, fdesc, accent_color, icon_type) in enumerate(features):
        col = idx % 2
        row = idx // 2
        cx = start_x + col * (card_w + gap_x)
        cy = grid_y + row * (card_h + gap_y)

        # Card container with glassmorphic border
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=12, fill=(18, 25, 42, 235), outline=(42, 58, 90, 220), width=1)
        # Left accent stripe
        draw.rounded_rectangle([cx, cy, cx + 6, cy + card_h], radius=3, fill=accent_color)

        # Icon Circle
        icon_cx = cx + 36
        icon_cy = cy + 34
        draw.ellipse([icon_cx - 18, icon_cy - 18, icon_cx + 18, icon_cy + 18], fill=(28, 38, 64, 255), outline=accent_color, width=2)
        
        # Render clean vector icon
        if icon_type == "lightning":
            draw_lightning(draw, icon_cx, icon_cy, 18, accent_color)
        elif icon_type == "play":
            draw_play(draw, icon_cx, icon_cy, 18, accent_color)
        elif icon_type == "split":
            draw_split(draw, icon_cx, icon_cy, 18, accent_color)
        elif icon_type == "bell":
            draw_bell(draw, icon_cx, icon_cy, 18, accent_color)
        elif icon_type == "shield":
            draw_shield(draw, icon_cx, icon_cy, 18, accent_color)
        elif icon_type == "chart":
            draw_chart(draw, icon_cx, icon_cy, 18, accent_color)

        # Card Title
        draw.text((cx + 66, cy + 12), ftitle, font=font_card_title, fill=(255, 255, 255))

        # Card Description (wrapped)
        words = fdesc.split(" ")
        lines = []
        cur_line = ""
        for w in words:
            test_line = cur_line + (" " if cur_line else "") + w
            if font_card_desc.getlength(test_line) <= (card_w - 78):
                cur_line = test_line
            else:
                lines.append(cur_line)
                cur_line = w
        if cur_line:
            lines.append(cur_line)

        desc_y = cy + 44
        for l in lines[:2]:
            draw.text((cx + 66, desc_y), l, font=font_card_desc, fill=(170, 185, 205))
            desc_y += 22

    # --- BOTTOM FOOTER / CTA BAR ---
    footer_y = 1045
    draw.line([(60, footer_y), (W - 60, footer_y)], fill=(45, 62, 95, 255), width=2)

    # Free & Portable Banner (wider, no text overflow!)
    banner_w = 600
    banner_h = 34
    bx = (W - banner_w) // 2
    by = footer_y - 17
    draw.rounded_rectangle([bx, by, bx + banner_w, by + banner_h], radius=17, fill=(197, 48, 48, 255), outline=(255, 255, 255, 220), width=1)
    banner_txt = "100% GRATIS  •  TANPA SERIAL / CRACK  •  PORTABLE & INSTALLER"
    bt_bbox = font_tag.getbbox(banner_txt)
    btw = bt_bbox[2] - bt_bbox[0]
    draw_lightning(draw, bx + (banner_w - btw)//2 - 14, by + 17, 13, (255, 255, 255))
    draw.text((bx + (banner_w - btw)//2, by + 7), banner_txt, font=font_tag, fill=(255, 255, 255))

    # Contacts & Links
    info_y = footer_y + 32
    # Left column: Telegram Developer & Community
    draw.text((60, info_y), "Kontak Developer:", font=font_footer_bold, fill=(0, 210, 255))
    draw.text((235, info_y), "t.me/srpcomadmin", font=font_footer_bold, fill=(255, 255, 255))

    draw.text((60, info_y + 34), "Gabung Komunitas:", font=font_footer_bold, fill=(0, 210, 255))
    draw.text((250, info_y + 34), "t.me/srpcomgroup", font=font_footer_bold, fill=(255, 255, 255))

    # Right column: GitHub Release Link & OS support
    draw.text((W - 550, info_y), "Unduh Versi Terbaru (GitHub):", font=font_footer_bold, fill=(0, 210, 255))
    draw.text((W - 550, info_y + 30), "github.com/srpcom/srpcom-download-manager", font=font_footer_regular, fill=(255, 255, 255))
    draw.text((W - 550, info_y + 58), "Kompatibel: Windows 10 & Windows 11 (64-bit)", font=get_font("semibold", 14), fill=(160, 178, 205))

    # Convert to RGB and save as ultra-high-quality JPG
    rgb_img = Image.new("RGB", (W, H), (11, 15, 25))
    rgb_img.paste(img, mask=img.split()[3])
    output_path = "flyer_srpcom_download_manager.jpg"
    rgb_img.save(output_path, "JPEG", quality=96, optimize=True)
    print(f"Flyer successfully regenerated at: {output_path}")

if __name__ == "__main__":
    create_flyer()
