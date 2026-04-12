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
        self.geometry("160x100")
        self.configure(bg="#1e1e1e") # Dark gray/black background
        self.attributes('-topmost', True) # Keep on top like a widget
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

        # App icon (transparent PNG)
        try:
            self._icon_img = tk.PhotoImage(file=resource_path("InTIMEsication_logo.png"))
            self.iconphoto(True, self._icon_img)
        except Exception:
            pass
        
        # UI Elements
        # Drag handle / Header
        self.header = tk.Frame(self, bg="#333333", height=20, cursor="fleur")
        self.header.pack(fill=tk.X, side=tk.TOP)
        self.header.bind("<ButtonPress-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)
        
        # Close button in header
        self.close_btn = tk.Label(self.header, text="X", bg="#333333", fg="white", font=("Arial", 10, "bold"))
        self.close_btn.pack(side=tk.RIGHT, padx=5)
        self.close_btn.bind("<Button-1>", lambda e: self.quit_app())
        
        # History button in header
        self.hist_btn = tk.Label(self.header, text="H", bg="#333333", fg="white", font=("Arial", 10, "bold"))
        self.hist_btn.pack(side=tk.LEFT, padx=5)
        self.hist_btn.bind("<Button-1>", lambda e: self.show_history())

        # About button in header
        self.about_btn = tk.Label(self.header, text="i", bg="#333333", fg="white", font=("Arial", 10, "bold"))
        self.about_btn.pack(side=tk.LEFT, padx=5)
        self.about_btn.bind("<Button-1>", lambda e: self.show_about())

        # Theme button in header
        self.theme_btn = tk.Label(self.header, text="☀", bg="#333333", fg="white", font=("Arial", 10, "bold"))
        self.theme_btn.pack(side=tk.LEFT, padx=5)
        self.theme_btn.bind("<Button-1>", lambda e: self.toggle_theme())
        
        # Opacity button in header
        self.op_btn = tk.Label(self.header, text="○", bg="#333333", fg="white", font=("Arial", 10, "bold"))
        self.op_btn.pack(side=tk.LEFT, padx=5)
        self.op_btn.bind("<Button-1>", lambda e: self.toggle_opacity_slider())

        self.overrideredirect(True) # Remove windows borders
        
        # Time Display
        self.time_label = tk.Label(self, text="00:00:00", font=("Consolas", 24), bg="#1e1e1e", fg="#00ff00")
        self.time_label.pack(pady=5)
        
        # Controls Frame
        self.controls = tk.Frame(self, bg="#1e1e1e")
        self.controls.pack(pady=2)
        
        # Buttons
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TButton', background='#333333', foreground='white', borderwidth=1)
        style.map('TButton', background=[('active', '#555555')])

        self.play_btn = tk.Button(self.controls, text="▶", bg="#333333", fg="white", bd=0, command=self.play, width=4)
        self.play_btn.grid(row=0, column=0, padx=5)
        
        self.pause_btn = tk.Button(self.controls, text="⏸", bg="#333333", fg="white", bd=0, command=self.pause, width=4, state=tk.DISABLED)
        self.pause_btn.grid(row=0, column=1, padx=5)
        
        self.stop_btn = tk.Button(self.controls, text="■", bg="#333333", fg="white", bd=0, command=self.stop, width=4, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=5)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        if hasattr(self, "op_win") and self.op_win.winfo_exists():
            self.op_win.destroy()
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def toggle_theme(self):
        self.is_light_mode = not self.is_light_mode
        if self.is_light_mode:
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            header_bg = "#dddddd"
            header_fg = "#000000"
            btn_bg = "#e0e0e0"
            self.theme_btn.config(text="☾")
        else:
            bg_color = "#1e1e1e"
            fg_color = "white"
            header_bg = "#333333"
            header_fg = "white"
            btn_bg = "#333333"
            self.theme_btn.config(text="☀")

        self.configure(bg=bg_color)
        self.header.configure(bg=header_bg)
        self.close_btn.configure(bg=header_bg, fg=header_fg)
        self.hist_btn.configure(bg=header_bg, fg=header_fg)
        self.about_btn.configure(bg=header_bg, fg=header_fg)
        self.theme_btn.configure(bg=header_bg, fg=header_fg)
        self.op_btn.configure(bg=header_bg, fg=header_fg)
        
        self.time_label.configure(bg=bg_color)
        if not self.is_running and not self.is_paused:
            self.time_label.configure(fg=fg_color)
        elif self.is_running and not self.is_paused:
            self.time_label.configure(fg="#008800" if self.is_light_mode else "#00ff00")
        elif self.is_paused:
            self.time_label.configure(fg="#d2691e" if self.is_light_mode else "#ffff00")
            
        self.controls.configure(bg=bg_color)
        self.play_btn.configure(bg=btn_bg, fg=fg_color)
        self.pause_btn.configure(bg=btn_bg, fg=fg_color)
        self.stop_btn.configure(bg=btn_bg, fg=fg_color)

    def toggle_opacity_slider(self):
        if hasattr(self, "op_win") and self.op_win.winfo_exists():
            self.op_win.destroy()
            return
            
        self.op_win = tk.Toplevel(self)
        self.op_win.overrideredirect(True)
        self.op_win.attributes('-topmost', True)
        self.op_win.configure(bg=self.header.cget("bg"))
        
        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height()
        self.op_win.geometry(f"160x30+{x}+{y}")
        
        slider = tk.Scale(self.op_win, from_=0.1, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, 
                          showvalue=0, command=self.change_opacity, bg=self.header.cget("bg"), 
                          bd=0, highlightthickness=0)
        slider.set(self.attributes('-alpha'))
        slider.pack(fill=tk.X, padx=10, pady=5)

    def change_opacity(self, val):
        self.attributes('-alpha', float(val))

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

    def play(self):
        if not self.is_running:
            # Start new session
            self.is_running = True
            self.is_paused = False
            self.elapsed_seconds = 0
            self.start_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.update_display()
            self.update_timer()
        elif self.is_paused:
            # Resume session
            self.is_paused = False
        
        self.play_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        run_color = "#008800" if getattr(self, "is_light_mode", False) else "#00ff00"
        self.time_label.config(fg=run_color) # Green when running

    def pause(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.play_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            pause_color = "#d2691e" if getattr(self, "is_light_mode", False) else "#ffff00"
            self.time_label.config(fg=pause_color) # Yellow when paused

    def stop(self):
        if self.is_running:
            # Save session
            session_duration = self.elapsed_seconds
            self.save_session(self.start_date_str, session_duration)
            
            self.is_running = False
            self.is_paused = False
            if self.timer_job:
                self.after_cancel(self.timer_job)
                self.timer_job = None
                
            self.elapsed_seconds = 0
            self.update_display()
            
            self.play_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            if self.is_light_mode:
                self.time_label.config(fg="#000000")
            else:
                self.time_label.config(fg="#ffffff")

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

        label = tk.Label(hist_win, text="Session History", fg="white", bg="#2d2d2d", font=("Arial", 14))
        label.pack(pady=10)

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
        
        # InTIMEsication (жирными чуть крупнее)
        tk.Label(about_win, text="InTIMEsication", fg="black", bg="#EDEBE7", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        
        # The most contagious time tracker in the wild (курсив)
        tk.Label(about_win, text="The most contagious time tracker in the wild", fg="#505050", bg="#EDEBE7", font=("Arial", 10, "italic")).pack(pady=0)
        
        # Version 1.0.5
        tk.Label(about_win, text="Version 1.0.5", fg="black", bg="#EDEBE7", font=("Arial", 10)).pack(pady=10)
        
        # All rights reserved
        tk.Label(about_win, text="All rights reserved", fg="black", bg="#EDEBE7", font=("Arial", 10)).pack(pady=5)
        
        # Purely coded, naturally spread by Staffilocode
        tk.Label(about_win, text="Purely coded, naturally spread by Staffilocode", fg="black", bg="#EDEBE7", font=("Arial", 10)).pack(pady=5)
        
        # Staffilocode — coding that spreads.
        frame = tk.Frame(about_win, bg="#EDEBE7")
        frame.pack(pady=5)
        tk.Label(frame, text="Staffilocode", fg="black", bg="#EDEBE7", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        tk.Label(frame, text="— coding that spreads.", fg="black", bg="#EDEBE7", font=("Arial", 10, "italic")).pack(side=tk.LEFT)

        # Logo image
        logo_path = resource_path("logo.png")
        if os.path.exists(logo_path):
            try:
                self.logo_img = tk.PhotoImage(file=logo_path)
                # If image is very large, subsample it by 4
                if self.logo_img.width() > 200:
                    sub_factor = self.logo_img.width() // 150
                    self.logo_img = self.logo_img.subsample(sub_factor, sub_factor)
                tk.Label(about_win, image=self.logo_img, bg="#EDEBE7").pack(pady=10)
            except Exception as e:
                tk.Label(about_win, text=f"[Logo Error: {e}]", fg="red", bg="#EDEBE7").pack(pady=10)
        else:
            tk.Label(about_win, text="[logo.png not found]", fg="gray", bg="#EDEBE7").pack(pady=10)

        # GitHub link
        github_frame = tk.Frame(about_win, bg="#EDEBE7", cursor="hand2")
        github_frame.pack(pady=(0, 15))
        try:
            gh_pil = Image.open(resource_path("github_logo.png")).resize((24, 24), Image.LANCZOS)
            self._github_img = ImageTk.PhotoImage(gh_pil)
            gh_icon = tk.Label(github_frame, image=self._github_img, bg="#EDEBE7", cursor="hand2")
            gh_icon.pack(side=tk.LEFT, padx=(0, 5))
        except Exception:
            pass
        gh_link = tk.Label(github_frame, text="github.com/StaffiloCode", fg="#0066cc", bg="#EDEBE7",
                           font=("Arial", 10, "underline"), cursor="hand2")
        gh_link.pack(side=tk.LEFT)
        for widget in github_frame.winfo_children():
            widget.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/StaffiloCode"))
        github_frame.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/StaffiloCode"))

    def quit_app(self):
        if self.is_running:
            self.stop()
        self.destroy()

if __name__ == "__main__":
    
    mutex_name = "Global\\TimeTrackerAppMutex"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()
    
    if last_error == 183: # ERROR_ALREADY_EXISTS
        hwnd = ctypes.windll.user32.FindWindowW(None, "Time Tracker")
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9) # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    else:
        app = TimeTrackerWidget()
        app.mainloop()
