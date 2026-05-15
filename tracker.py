import sys
import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
import os
import ctypes
import webbrowser
from datetime import datetime
from PIL import Image, ImageTk

HISTORY_FILE = "history.json"
POMODORO_WORK_SECONDS = 25 * 60
POMODORO_BREAK_SECONDS = 5 * 60
POMODORO_SNOOZE_SECONDS = 5 * 60

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class TimeTrackerWidget(tk.Tk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Time Tracker")
        self.geometry("240x140")
        self.configure(bg="#1e1e1e")
        self.attributes('-topmost', True)
        self.resizable(False, False)

        # Variables
        self.is_running = False
        self.is_paused = False
        self.is_light_mode = False
        self.start_date_str = None
        self.elapsed_seconds = 0
        self.timer_job = None
        self.hist_win = None
        self.about_win = None

        # Pomodoro state
        self.pomodoro_active = False
        self.pomodoro_phase = "work"  # "work" or "break"
        self.pomodoro_seconds = 0
        self.pomodoro_job = None
        self.pomodoro_notify_win = None

        # App icon
        try:
            self._icon_img = tk.PhotoImage(file=resource_path("InTIMEsication_logo.png"))
            self.iconphoto(True, self._icon_img)
        except Exception:
            pass

        # Header — airy minimalist toolbar
        self._header_bg_dark = "#252526"
        self._header_bg_light = "#f5f5f5"
        self._header_fg_dark = "#cccccc"
        self._header_fg_light = "#505050"
        self._header_hover_dark = "#3a3a3c"
        self._header_hover_light = "#e4e4e4"

        self.header = tk.Frame(self, bg=self._header_bg_dark, height=28, cursor="fleur")
        self.header.pack(fill=tk.X, side=tk.TOP)
        self.header.bind("<ButtonPress-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)

        # Track header buttons for theme/hover handling
        self._header_buttons = []

        icon_font = ("Segoe UI Symbol", 11)

        # Close button (right side, accent on hover) — same font size as other icons
        self.close_btn = self._make_header_button("×", self.quit_app, font=icon_font, accent="#e81123")
        self.close_btn.pack(side=tk.RIGHT, padx=(2, 6), pady=2)

        # Left group: History, About
        self.hist_btn = self._make_header_button("H", self.show_history, font=icon_font)
        self.hist_btn.pack(side=tk.LEFT, padx=(6, 2), pady=2)

        self.about_btn = self._make_header_button("ℹ", self.show_about, font=icon_font)  # ℹ info
        self.about_btn.pack(side=tk.LEFT, padx=2, pady=2)

        # Separator
        self._sep1 = tk.Frame(self.header, bg="#3a3a3c", width=1)
        self._sep1.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=6)

        # Middle group: Theme, Opacity, Pomodoro
        self.theme_btn = self._make_header_button("☼", self.toggle_theme, font=icon_font)  # ☼ sun
        self.theme_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.op_btn = self._make_header_button("○", self.toggle_opacity_slider, font=icon_font)  # ○
        self.op_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.pomodoro_btn = self._make_header_button("◐", self.toggle_pomodoro, font=icon_font)  # ◐ focus disc
        self.pomodoro_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.overrideredirect(True)

        # Main time display (no seconds)
        self.time_label = tk.Label(self, text="00:00:00", font=("Consolas", 22), bg="#1e1e1e", fg="#00ff00")
        self.time_label.pack(pady=(5, 0))

        # Pomodoro mini-timer (hidden by default)
        self.pomo_label = tk.Label(self, text="", font=("Consolas", 11), bg="#1e1e1e", fg="#ff6b6b")
        self.pomo_label.pack(pady=(0, 2))

        # Controls Frame
        self.controls = tk.Frame(self, bg="#1e1e1e")
        self.controls.pack(pady=2)

        style = ttk.Style()
        style.theme_use('default')
        style.configure('TButton', background='#333333', foreground='white', borderwidth=1)
        style.map('TButton', background=[('active', '#555555')])

        self.play_btn = tk.Button(self.controls, text="▶", bg="#2d2d2d", fg="white", bd=0,
                                  activebackground="#3a3a3c", activeforeground="white",
                                  command=self.toggle_play_pause, width=4, cursor="hand2",
                                  font=("Segoe UI Symbol", 10))
        self.play_btn.grid(row=0, column=0, padx=6)

        self.stop_btn = tk.Button(self.controls, text="■", bg="#2d2d2d", fg="white", bd=0,
                                  activebackground="#3a3a3c", activeforeground="white",
                                  command=self.stop, width=4, state=tk.DISABLED, cursor="hand2",
                                  font=("Segoe UI Symbol", 10))
        self.stop_btn.grid(row=0, column=1, padx=6)

    # ── Header buttons ────────────────────────────────────────────────────────

    def _make_header_button(self, text, command, font=None, accent=None):
        """Create an airy header button: hand cursor, hover background, optional accent color on hover."""
        bg = self.header.cget("bg")
        fg = self._header_fg_dark
        btn = tk.Label(
            self.header,
            text=text,
            bg=bg,
            fg=fg,
            font=font or ("Segoe UI Symbol", 11),
            width=2,
            anchor="center",
            pady=2,
            cursor="hand2",
        )
        btn._cmd = command
        btn._accent = accent  # special hover color (e.g. red for close)
        btn.bind("<Button-1>", lambda e, c=command: c())
        btn.bind("<Enter>", lambda e, b=btn: self._on_header_hover(b, True))
        btn.bind("<Leave>", lambda e, b=btn: self._on_header_hover(b, False))
        self._header_buttons.append(btn)
        return btn

    def _on_header_hover(self, btn, entering):
        if entering:
            if btn._accent:
                btn.configure(bg=btn._accent, fg="white")
            else:
                hover = self._header_hover_light if self.is_light_mode else self._header_hover_dark
                btn.configure(bg=hover)
        else:
            btn.configure(bg=self.header.cget("bg"),
                          fg=self._header_fg_light if self.is_light_mode else self._header_fg_dark)
            # Re-apply pomodoro active highlight if needed
            if btn is self.pomodoro_btn and self.pomodoro_active:
                btn.configure(fg="#ff6b6b")

    # ── Movement ──────────────────────────────────────────────────────────────

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        if hasattr(self, "op_win") and self.op_win.winfo_exists():
            self.op_win.destroy()
            self._set_op_btn_active(False)
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    # ── Theme ─────────────────────────────────────────────────────────────────

    def toggle_theme(self):
        self.is_light_mode = not self.is_light_mode
        if self.is_light_mode:
            bg_color = "#fafafa"
            fg_color = "#1a1a1a"
            header_bg = self._header_bg_light
            header_fg = self._header_fg_light
            btn_bg = "#ececec"
            sep_color = "#d0d0d0"
            self.theme_btn.config(text="☽")
        else:
            bg_color = "#1e1e1e"
            fg_color = "white"
            header_bg = self._header_bg_dark
            header_fg = self._header_fg_dark
            btn_bg = "#2d2d2d"
            sep_color = "#3a3a3c"
            self.theme_btn.config(text="☼")

        self.configure(bg=bg_color)
        self.header.configure(bg=header_bg)
        for w in self._header_buttons:
            w.configure(bg=header_bg, fg=header_fg)
        self._sep1.configure(bg=sep_color)
        if self.pomodoro_active:
            self.pomodoro_btn.configure(fg="#ff6b6b")

        self.time_label.configure(bg=bg_color)
        self.pomo_label.configure(bg=bg_color)
        if not self.is_running and not self.is_paused:
            self.time_label.configure(fg=fg_color)
        elif self.is_running and not self.is_paused:
            self.time_label.configure(fg="#008800" if self.is_light_mode else "#00ff00")
        elif self.is_paused:
            self.time_label.configure(fg="#d2691e" if self.is_light_mode else "#ffff00")

        self.controls.configure(bg=bg_color)
        self.play_btn.configure(bg=btn_bg, fg=fg_color)
        self.stop_btn.configure(bg=btn_bg, fg=fg_color)

    # ── Opacity ───────────────────────────────────────────────────────────────

    def toggle_opacity_slider(self):
        if hasattr(self, "op_win") and self.op_win.winfo_exists():
            self.op_win.destroy()
            self._set_op_btn_active(False)
            return

        self._set_op_btn_active(True)

        win_w = self.winfo_width()
        self.op_win = tk.Toplevel(self)
        self.op_win.overrideredirect(True)
        self.op_win.attributes('-topmost', True)
        self.op_win.configure(bg=self.header.cget("bg"))

        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height()
        self.op_win.geometry(f"{win_w}x30+{x}+{y}")

        slider = tk.Scale(self.op_win, from_=0.1, to=1.0, resolution=0.05, orient=tk.HORIZONTAL,
                          showvalue=0, command=self.change_opacity, bg=self.header.cget("bg"),
                          bd=0, highlightthickness=0)
        slider.set(self.attributes('-alpha'))
        slider.pack(fill=tk.X, padx=10, pady=5)

        # Clear active state when slider window itself is destroyed
        op_win_ref = self.op_win
        self.op_win.bind("<Destroy>", lambda e: self._set_op_btn_active(False) if e.widget is op_win_ref else None)

    def _set_op_btn_active(self, active):
        if active:
            # Clearly visible "pressed" state — brighter than hover, no border (border shifts neighbours)
            pressed_bg = "#d0d0d0" if self.is_light_mode else "#5a5a5e"
            self.op_btn.configure(bg=pressed_bg)
        else:
            self.op_btn.configure(bg=self.header.cget("bg"))

    def change_opacity(self, val):
        self.attributes('-alpha', float(val))

    # ── Main timer ────────────────────────────────────────────────────────────

    def update_timer(self):
        if self.is_running and not self.is_paused:
            self.elapsed_seconds += 1
            self.update_display()
        if self.is_running:
            self.timer_job = self.after(1000, self.update_timer)

    def update_display(self):
        hours = self.elapsed_seconds // 3600
        minutes = (self.elapsed_seconds % 3600) // 60
        seconds = self.elapsed_seconds % 60
        self.time_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def toggle_play_pause(self):
        if not self.is_running:
            self.play()
        elif not self.is_paused:
            self.pause()
        else:
            self.play()

    def play(self):
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.elapsed_seconds = 0
            self.start_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.update_display()
            self.update_timer()
            if self.pomodoro_active:
                self._start_pomodoro_phase("work")
        elif self.is_paused:
            self.is_paused = False

        self.play_btn.config(text="❚❚")
        self.stop_btn.config(state=tk.NORMAL)
        run_color = "#008800" if self.is_light_mode else "#00ff00"
        self.time_label.config(fg=run_color)

    def pause(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.play_btn.config(text="▶")
            pause_color = "#d2691e" if self.is_light_mode else "#ffff00"
            self.time_label.config(fg=pause_color)

    def stop(self):
        if self.is_running:
            self.save_session(self.start_date_str, self.elapsed_seconds)

            self.is_running = False
            self.is_paused = False
            if self.timer_job:
                self.after_cancel(self.timer_job)
                self.timer_job = None

            self.elapsed_seconds = 0
            self.update_display()

            self.play_btn.config(text="▶")
            self.stop_btn.config(state=tk.DISABLED)
            self.time_label.config(fg="#000000" if self.is_light_mode else "#ffffff")

            self._stop_pomodoro()

    # ── Pomodoro ──────────────────────────────────────────────────────────────

    def toggle_pomodoro(self):
        if self.pomodoro_active:
            self._stop_pomodoro()
            self.pomodoro_btn.config(
                fg=self._header_fg_light if self.is_light_mode else self._header_fg_dark
            )
        else:
            self.pomodoro_active = True
            self.pomodoro_btn.config(fg="#ff6b6b")
            self.pomo_label.config(text="🍅 --:--")
            if self.is_running and not self.is_paused:
                self._start_pomodoro_phase("work")

    def _stop_pomodoro(self):
        self.pomodoro_active = False
        self.pomodoro_phase = "work"
        self.pomodoro_seconds = 0
        if self.pomodoro_job:
            self.after_cancel(self.pomodoro_job)
            self.pomodoro_job = None
        self.pomo_label.config(text="")
        if self.pomodoro_notify_win and self.pomodoro_notify_win.winfo_exists():
            self.pomodoro_notify_win.destroy()

    def _start_pomodoro_phase(self, phase, seconds=None):
        if self.pomodoro_job:
            self.after_cancel(self.pomodoro_job)
            self.pomodoro_job = None

        self.pomodoro_phase = phase
        if seconds is not None:
            self.pomodoro_seconds = seconds
        elif phase == "work":
            self.pomodoro_seconds = POMODORO_WORK_SECONDS
        else:
            self.pomodoro_seconds = POMODORO_BREAK_SECONDS

        self._update_pomodoro()

    def _update_pomodoro(self):
        if not self.pomodoro_active:
            return
        if self.is_paused or not self.is_running:
            self.pomodoro_job = self.after(1000, self._update_pomodoro)
            return

        if self.pomodoro_seconds <= 0:
            self._pomodoro_phase_ended()
            return

        self.pomodoro_seconds -= 1
        minutes = self.pomodoro_seconds // 60
        seconds = self.pomodoro_seconds % 60

        if self.pomodoro_phase == "work":
            self.pomo_label.config(text=f"🍅 {minutes:02d}:{seconds:02d}", fg="#ff6b6b")
        else:
            self.pomo_label.config(text=f"☕ {minutes:02d}:{seconds:02d}", fg="#4fc3f7")

        self.pomodoro_job = self.after(1000, self._update_pomodoro)

    def _pomodoro_phase_ended(self):
        if self.pomodoro_phase == "work":
            self._show_break_notification()
        else:
            self._show_work_notification()

    def _show_break_notification(self):
        self._play_alert()
        self._close_notify_win()

        win = tk.Toplevel(self)
        self.pomodoro_notify_win = win
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.configure(bg="#1a1a2e")

        w, h = 280, 200
        sx = self.winfo_screenwidth()
        sy = self.winfo_screenheight()
        x = sx - w - 20
        y = sy - h - 60
        win.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(win, text="🍅  Time for a break!", font=("Arial", 14, "bold"),
                 bg="#1a1a2e", fg="white").pack(pady=(18, 4))
        tk.Label(win, text="25 minutes of focus done.\nTake a 5-minute break.",
                 font=("Arial", 10), bg="#1a1a2e", fg="#aaaaaa", justify=tk.CENTER).pack(pady=(0, 12))

        btn_frame = tk.Frame(win, bg="#1a1a2e")
        btn_frame.pack()

        tk.Button(btn_frame, text="☕ Start break", bg="#4fc3f7", fg="#1a1a2e",
                  font=("Arial", 10, "bold"), bd=0, padx=8, pady=4,
                  command=lambda: self._on_start_break(win)).grid(row=0, column=0, padx=5, pady=(0, 6))

        tk.Button(btn_frame, text="⏱ Snooze 5m", bg="#555577", fg="white",
                  font=("Arial", 10), bd=0, padx=8, pady=4,
                  command=lambda: self._on_snooze(win)).grid(row=0, column=1, padx=5, pady=(0, 6))

        tk.Button(btn_frame, text="⏭ Skip", bg="#333344", fg="#aaaaaa",
                  font=("Arial", 10), bd=0, padx=8, pady=4,
                  command=lambda: self._on_skip_break(win)).grid(row=1, column=0, columnspan=2, pady=0)

        # Flash the notification window border
        self._flash_window(win, 3)

    def _show_work_notification(self):
        self._play_alert()
        self._close_notify_win()

        win = tk.Toplevel(self)
        self.pomodoro_notify_win = win
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.configure(bg="#1a2e1a")

        w, h = 300, 160
        sx = self.winfo_screenwidth()
        sy = self.winfo_screenheight()
        x = sx - w - 20
        y = sy - h - 60
        win.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(win, text="💪  Break is over!", font=("Arial", 14, "bold"),
                 bg="#1a2e1a", fg="white").pack(pady=(18, 4))
        tk.Label(win, text="Ready to focus again?",
                 font=("Arial", 10), bg="#1a2e1a", fg="#aaaaaa").pack(pady=(0, 12))

        btn_frame = tk.Frame(win, bg="#1a2e1a")
        btn_frame.pack()

        tk.Button(btn_frame, text="▶ Start focus", bg="#66bb6a", fg="#1a2e1a",
                  font=("Arial", 10, "bold"), bd=0, padx=8, pady=4,
                  command=lambda: self._on_start_work(win)).grid(row=0, column=0, padx=5)

        tk.Button(btn_frame, text="⏱ +5 min break", bg="#555577", fg="white",
                  font=("Arial", 10), bd=0, padx=8, pady=4,
                  command=lambda: self._on_extend_break(win)).grid(row=0, column=1, padx=5)

        self._flash_window(win, 3)

    def _on_start_break(self, win):
        win.destroy()
        self._start_pomodoro_phase("break")

    def _on_snooze(self, win):
        win.destroy()
        self._start_pomodoro_phase("work", POMODORO_SNOOZE_SECONDS)

    def _on_skip_break(self, win):
        win.destroy()
        self._start_pomodoro_phase("work")

    def _on_start_work(self, win):
        win.destroy()
        self._start_pomodoro_phase("work")

    def _on_extend_break(self, win):
        win.destroy()
        self._start_pomodoro_phase("break", POMODORO_SNOOZE_SECONDS)

    def _close_notify_win(self):
        if self.pomodoro_notify_win and self.pomodoro_notify_win.winfo_exists():
            self.pomodoro_notify_win.destroy()

    def _play_alert(self):
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass

    def _flash_window(self, win, times):
        if times <= 0 or not win.winfo_exists():
            return
        current = win.cget("bg")
        flash_color = "#ffffff"
        original = current
        win.configure(bg=flash_color)
        self.after(120, lambda: win.configure(bg=original) if win.winfo_exists() else None)
        self.after(240, lambda: self._flash_window(win, times - 1))

    # ── History ───────────────────────────────────────────────────────────────

    def save_session(self, date_str, duration_seconds):
        history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    history = json.load(f)
            except:
                pass

        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        duration_str = f"{hours}h {minutes}m {seconds}s"

        history.append({
            "date": getattr(self, "start_date_str", date_str),
            "duration_str": duration_str,
            "duration_seconds": duration_seconds
        })

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

    def show_history(self):
        if self.hist_win is not None and self.hist_win.winfo_exists():
            self.hist_win.lift()
            self.hist_win.focus_force()
            return

        self.hist_win = tk.Toplevel(self)
        hist_win = self.hist_win
        hist_win.title("History")
        hist_win.geometry("300x400")
        hist_win.configure(bg="#2d2d2d")

        try:
            hist_win.iconphoto(False, self._icon_img)
        except Exception:
            pass

        tk.Label(hist_win, text="Session History", fg="white", bg="#2d2d2d", font=("Arial", 14)).pack(pady=10)

        clear_btn = tk.Button(hist_win, text="Clear history", bg="#333333", fg="white", bd=0,
                              command=lambda: self.clear_history(text_area))
        clear_btn.pack(side=tk.BOTTOM, pady=(0, 10))

        text_area = tk.Text(hist_win, bg="#1e1e1e", fg="white", font=("Consolas", 10))
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        self._refresh_history(text_area)

    def _refresh_history(self, text_area):
        if self.hist_win is None or not self.hist_win.winfo_exists():
            return

        text_area.config(state=tk.NORMAL)
        text_area.delete(1.0, tk.END)

        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    history = json.load(f)
                for session in reversed(history):
                    text_area.insert(tk.END, f"Start: {session['date']}\nDuration: {session['duration_str']}\n" + "-"*30 + "\n")
            except:
                text_area.insert(tk.END, "Error loading history.")
        else:
            text_area.insert(tk.END, "No history found.")

        text_area.config(state=tk.DISABLED)
        self.hist_win.after(2000, lambda: self._refresh_history(text_area))

    def clear_history(self, text_area):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        self._refresh_history(text_area)

    # ── About ─────────────────────────────────────────────────────────────────

    def show_about(self):
        if self.about_win is not None and self.about_win.winfo_exists():
            self.about_win.lift()
            self.about_win.focus_force()
            return

        self.about_win = tk.Toplevel(self)
        about_win = self.about_win
        about_win.title("About")
        about_win.geometry("320x400")
        about_win.configure(bg="#EDEBE7")

        try:
            about_win.iconphoto(False, self._icon_img)
        except Exception:
            pass

        tk.Label(about_win, text="InTIMEsication", fg="black", bg="#EDEBE7", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        tk.Label(about_win, text="The most contagious time tracker in the wild", fg="#505050", bg="#EDEBE7", font=("Arial", 10, "italic")).pack(pady=0)
        tk.Label(about_win, text="Version 1.1.0", fg="black", bg="#EDEBE7", font=("Arial", 10)).pack(pady=10)
        tk.Label(about_win, text="All rights reserved", fg="black", bg="#EDEBE7", font=("Arial", 10)).pack(pady=5)
        tk.Label(about_win, text="Purely coded, naturally spread by Staffilocode", fg="black", bg="#EDEBE7", font=("Arial", 10)).pack(pady=5)

        frame = tk.Frame(about_win, bg="#EDEBE7")
        frame.pack(pady=5)
        tk.Label(frame, text="Staffilocode", fg="black", bg="#EDEBE7", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        tk.Label(frame, text="— coding that spreads.", fg="black", bg="#EDEBE7", font=("Arial", 10, "italic")).pack(side=tk.LEFT)

        # Website link
        site_link = tk.Label(about_win, text="staffilocode.com", fg="#0066cc", bg="#EDEBE7",
                             font=("Arial", 10, "underline"), cursor="hand2")
        site_link.pack(pady=(5, 0))
        site_link.bind("<Button-1>", lambda e: webbrowser.open("https://staffilocode.com"))

        # Logo
        logo_path = resource_path("logo.png")
        if os.path.exists(logo_path):
            try:
                self.logo_img = tk.PhotoImage(file=logo_path)
                if self.logo_img.width() > 200:
                    sub_factor = self.logo_img.width() // 150
                    self.logo_img = self.logo_img.subsample(sub_factor, sub_factor)
                tk.Label(about_win, image=self.logo_img, bg="#EDEBE7").pack(pady=10)
            except Exception as e:
                tk.Label(about_win, text=f"[Logo Error: {e}]", fg="red", bg="#EDEBE7").pack(pady=10)
        else:
            tk.Label(about_win, text="[logo.png not found]", fg="gray", bg="#EDEBE7").pack(pady=10)

    # ── Quit ──────────────────────────────────────────────────────────────────

    def quit_app(self):
        if self.is_running:
            self.stop()
        self.destroy()

if __name__ == "__main__":

    mutex_name = "Global\\TimeTrackerAppMutex"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == 183:  # ERROR_ALREADY_EXISTS
        hwnd = ctypes.windll.user32.FindWindowW(None, "Time Tracker")
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    else:
        app = TimeTrackerWidget()
        app.mainloop()
