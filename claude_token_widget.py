# Claude Token Widget — optimize edilmiş masaüstü widget
import tkinter as tk
import json, os, ctypes, ctypes.wintypes, winreg, sys

# ── Win32 sabitleri ──────────────────────────────────────────────────────────
GWL_STYLE        = -16
GWL_EXSTYLE      = -20
WS_CAPTION       = 0x00C00000
WS_THICKFRAME    = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_APPWINDOW  = 0x00040000
HWND_BOTTOM      = 1
SWP_FLAGS        = 0x0002 | 0x0001 | 0x0010 | 0x0008  # NOMOVE|NOSIZE|NOACTIVATE|NOREDRAW
DWMWA_CORNER     = 33
DWMWCP_ROUND     = 2

# ── Dosya yolları ─────────────────────────────────────────────────────────────
BASE       = os.path.join(os.path.expanduser("~"), ".claude")
STATS_FILE = os.path.join(BASE, "token_stats.json")
POS_FILE   = os.path.join(BASE, "token_widget_pos.json")

# ── Zamanlayıcılar ───────────────────────────────────────────────────────────
REFRESH_MS     = 2500   # veri yenileme
BOTTOM_MS      = 2000   # alt katman kilidi (daha seyrek = daha az titreme)
COVER_MS       = 1200   # kapsanma kontrolü
ALPHA_STEP_MS  = 25     # solma animasyonu adımı

# ── Boyutlar ─────────────────────────────────────────────────────────────────
W, H       = 290, 100
GAUGE      = 76
ARC_W      = 10
MARGIN     = 12

# ── Renkler ──────────────────────────────────────────────────────────────────
BG     = "#1a1a2e"
ACCENT = "#0f3460"
TEXT   = "#eaeaea"
SUB    = "#556070"
OK     = "#4ade80"
WARN   = "#facc15"
DANGER = "#f87171"
ARC_BG = "#1e2a3a"

# ── Yardımcılar ───────────────────────────────────────────────────────────────
def fmt(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}k"
    return str(n)

def load_pos():
    try:
        with open(POS_FILE) as f: return json.load(f)
    except Exception: return {"x": 60, "y": 60}

def save_pos(x, y):
    try:
        with open(POS_FILE, "w") as f: json.dump({"x": x, "y": y}, f)
    except Exception: pass

def startup_register():
    """Windows başlangıcına ekle."""
    exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(exe):
        exe = sys.executable
    cmd = f'"{exe}" "{os.path.abspath(__file__)}"'
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ClaudeTokenWidget", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
    except Exception: pass

def startup_registered():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "ClaudeTokenWidget")
        winreg.CloseKey(key)
        return True
    except Exception: return False


class Widget:
    def __init__(self):
        self._hwnd         = None
        self._dx = self._dy = 0
        self._last_pct     = -1.0   # gereksiz canvas yeniden çizimini önle
        self._last_tok     = ""
        self._alpha_now    = 0.0
        self._alpha_target = 0.93

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-alpha", 0.0)   # başlangıçta görünmez, sonra açılır
        root.configure(bg=BG)
        root.geometry(f"{W}x{H}")
        self.root = root

        self._build()

        pos = load_pos()
        root.geometry(f"{W}x{H}+{pos['x']}+{pos['y']}")
        root.update_idletasks()

        root.after(150, self._win32_init)
        root.after(200, self._fade_in)
        self._bind_drag()
        self._tick_data()
        root.mainloop()

    # ── Arayüz ───────────────────────────────────────────────────────────────
    def _build(self):
        # Sol — gauge canvas
        self.cv = tk.Canvas(self.root, width=GAUGE, height=GAUGE,
                            bg=BG, highlightthickness=0)
        self.cv.place(x=MARGIN, y=(H - GAUGE) // 2)

        # Sağ — metin
        rx = MARGIN + GAUGE + 12
        rw = W - rx - MARGIN

        self.lbl_tok = tk.Label(self.root, text="—",
                                font=("Segoe UI", 26, "bold"),
                                bg=BG, fg=OK, anchor="w")
        self.lbl_tok.place(x=rx, y=16, width=rw - 22)

        self.lbl_sub = tk.Label(self.root, text="kalan token",
                                font=("Segoe UI", 8),
                                bg=BG, fg=SUB, anchor="w")
        self.lbl_sub.place(x=rx + 2, y=58)

        self.lbl_model = tk.Label(self.root, text="",
                                  font=("Segoe UI", 7),
                                  bg=BG, fg=ACCENT, anchor="w")
        self.lbl_model.place(x=rx + 2, y=74)

        # Kapat
        tk.Button(self.root, text="✕", font=("Segoe UI", 8), bd=0,
                  cursor="hand2", bg=BG, fg=SUB,
                  activebackground=BG, activeforeground="#e94560",
                  command=self.root.destroy
                  ).place(x=W - 22, y=6)

        # İlk boş gauge
        self._draw_gauge(0.0, OK)

    def _draw_gauge(self, pct, color):
        c   = self.cv
        c.delete("all")
        s   = GAUGE
        pad = ARC_W // 2 + 2
        x0, y0, x1, y1 = pad, pad, s - pad, s - pad

        c.create_arc(x0, y0, x1, y1, start=0, extent=359.9,
                     style="arc", outline=ARC_BG, width=ARC_W)

        if pct > 0:
            c.create_arc(x0, y0, x1, y1,
                         start=90, extent=-max(pct * 359.9, 1),
                         style="arc", outline=color, width=ARC_W)

        cx = cy = s // 2
        c.create_text(cx, cy - 7, text=f"{pct*100:.0f}%",
                      fill=color, font=("Segoe UI", 13, "bold"), anchor="center")
        c.create_text(cx, cy + 9, text="dolu",
                      fill=SUB, font=("Segoe UI", 7), anchor="center")

    # ── Win32 ────────────────────────────────────────────────────────────────
    def _win32_init(self):
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        self._hwnd = hwnd or self.root.winfo_id()

        ex = ctypes.windll.user32.GetWindowLongW(self._hwnd, GWL_EXSTYLE)
        ex = (ex | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE) & ~WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(self._hwnd, GWL_EXSTYLE, ex)

        try:
            pref = ctypes.c_int(DWMWCP_ROUND)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                self._hwnd, DWMWA_CORNER, ctypes.byref(pref), ctypes.sizeof(pref))
        except Exception:
            self._round_region()

        self._send_bottom()
        self._tick_bottom()
        self._tick_cover()

        # İlk çalıştırmada başlangıca ekle
        if not startup_registered():
            startup_register()

    def _round_region(self):
        try:
            r = 18
            rgn = ctypes.windll.gdi32.CreateRoundRectRgn(
                0, 0, W + 1, H + 1, r * 2, r * 2)
            ctypes.windll.user32.SetWindowRgn(self._hwnd, rgn, True)
        except Exception: pass

    def _send_bottom(self):
        if self._hwnd:
            ctypes.windll.user32.SetWindowPos(
                self._hwnd, HWND_BOTTOM, 0, 0, 0, 0, SWP_FLAGS)

    def _tick_bottom(self):
        self._send_bottom()
        self.root.after(BOTTOM_MS, self._tick_bottom)

    # ── Kapsanma ─────────────────────────────────────────────────────────────
    def _tick_cover(self):
        covered = self._is_covered()
        self._alpha_target = 0.06 if covered else 0.93
        self._animate_alpha()
        self.root.after(COVER_MS, self._tick_cover)

    def _is_covered(self):
        # Sadece aktif ön plan penceresi widget'ın üzerindeyse solar
        fg = ctypes.windll.user32.GetForegroundWindow()
        if not fg or fg == self._hwnd:
            return False

        # Masaüstü / shell pencerelerini atla
        buf = ctypes.create_unicode_buffer(64)
        ctypes.windll.user32.GetClassNameW(fg, buf, 64)
        if buf.value in ("Progman", "WorkerW", "Shell_TrayWnd", ""):
            return False

        # Ön plan penceresinin widget merkezini kapatıp kapatmadığını kontrol et
        cx = self.root.winfo_x() + W // 2
        cy = self.root.winfo_y() + H // 2
        rc = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(fg, ctypes.byref(rc))
        return rc.left <= cx <= rc.right and rc.top <= cy <= rc.bottom

    # ── Smooth alpha ─────────────────────────────────────────────────────────
    def _animate_alpha(self):
        diff = self._alpha_target - self._alpha_now
        if abs(diff) < 0.015:
            self._alpha_now = self._alpha_target
            self.root.attributes("-alpha", self._alpha_now)
            return
        self._alpha_now += diff * 0.18   # yavaş yakınsama
        self.root.attributes("-alpha", round(self._alpha_now, 3))
        self.root.after(ALPHA_STEP_MS, self._animate_alpha)

    def _fade_in(self):
        self._alpha_target = 0.93
        self._animate_alpha()

    # ── Sürükle ──────────────────────────────────────────────────────────────
    def _bind_drag(self):
        self.root.bind("<Button-1>",        self._ds)
        self.root.bind("<B1-Motion>",       self._dm)
        self.root.bind("<ButtonRelease-1>", self._de)

    def _ds(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _dm(self, e):
        nx = e.x_root - self._dx
        ny = e.y_root - self._dy
        self.root.geometry(f"+{nx}+{ny}")

    def _de(self, e):
        save_pos(self.root.winfo_x(), self.root.winfo_y())

    # ── Veri ─────────────────────────────────────────────────────────────────
    def _tick_data(self):
        self._load_stats()
        self.root.after(REFRESH_MS, self._tick_data)

    def _load_stats(self):
        if not os.path.exists(STATS_FILE): return
        try:
            with open(STATS_FILE, encoding="utf-8") as f:
                s = json.load(f)
        except Exception: return

        pct_used = s.get("pct", 0) / 100
        remain   = s.get("remaining", 0)
        color    = OK if pct_used < 0.6 else (WARN if pct_used < 0.85 else DANGER)
        tok_str  = fmt(remain)

        # Sadece değişince yeniden çiz — titreme önleme
        if abs(pct_used - self._last_pct) > 0.001:
            self._last_pct = pct_used
            self._draw_gauge(pct_used, color)

        if tok_str != self._last_tok:
            self._last_tok = tok_str
            self.lbl_tok.config(text=tok_str, fg=color)

        model = s.get("model", "").replace("claude-", "")
        self.lbl_model.config(text=model)


if __name__ == "__main__":
    Widget()
