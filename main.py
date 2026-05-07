import tkinter as tk
from tkinter import ttk
import threading
import sys
import queue
import datetime
import time
from event import run_mirror, run_daily
from monitor import WindowMonitor

log_queue = queue.Queue()


class QueueRedirector:
    def __init__(self, queue, max_lines=2000, level="INFO"):
        self.queue = queue
        self.max_lines = max_lines
        self.lines = []
        self.level = level

    def write(self, message):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        for line in message.splitlines():
            if not line.strip():
                continue
            log_line = timestamp + line
            self.lines.append(log_line)
            if len(self.lines) > self.max_lines:
                self.lines = self.lines[-self.max_lines:]
            self.queue.put((log_line + "\n", self.level))

    def flush(self):
        pass

    def isatty(self):
        return False


# --- Color palette (dark theme) ---
BG_COLOR = "#2b2b2b"
PANEL_BG = "#333333"
INPUT_BG = "#3c3c3c"
FG_COLOR = "#e0e0e0"
ACCENT = "#4a9eff"
DANGER = "#ff5555"
LOG_BG = "#1e1e1e"
STATUS_BAR_BG = "#1e1e1e"
SUCCESS_GREEN = "#4ec94e"
WARN_ORANGE = "#ffaa00"
DIM_TEXT = "#888888"


class MainPanel:
    def __init__(self, root) -> None:
        self.root = root
        self.thread = None
        self.stop_event = None
        self.monitor = None
        self.running = False
        self.start_time = None
        self._elapsed_timer_id = None
        self._stop_timer_id = None

        self._init_window()
        self._setup_styles()
        self._build_control_panel()
        self._build_log_panel()
        self._build_status_bar()

        sys.stdout = QueueRedirector(log_queue, max_lines=2000, level="INFO")
        sys.stderr = QueueRedirector(log_queue, max_lines=2000, level="ERROR")

        self.root.bind('<Control-q>', self.stop_worker)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(10, self.process_log)

    # ---- window ----

    def _init_window(self):
        win_w, win_h = 640, 480
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.minsize(560, 420)
        self.root.configure(bg=BG_COLOR)

    def _on_close(self):
        if self.running:
            self.stop_worker()
        self.root.destroy()

    # ---- ttk styles ----

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=BG_COLOR, foreground=FG_COLOR, font=("Microsoft YaHei UI", 9))
        style.configure("Card.TFrame", background=PANEL_BG, relief="flat")
        style.configure("StatusBar.TFrame", background=STATUS_BAR_BG, relief="flat")

        style.configure("Title.TLabel", background=PANEL_BG, foreground=FG_COLOR,
                        font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Normal.TLabel", background=PANEL_BG, foreground=FG_COLOR,
                        font=("Microsoft YaHei UI", 9))
        style.configure("Status.TLabel", background=STATUS_BAR_BG, foreground=DIM_TEXT,
                        font=("Microsoft YaHei UI", 9))
        style.configure("Timer.TLabel", background=STATUS_BAR_BG, foreground=DIM_TEXT,
                        font=("Consolas", 9))

        style.configure("Primary.TButton", background=ACCENT, foreground="#ffffff",
                        borderwidth=0, focuscolor="none",
                        font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", "#5ab4ff"), ("disabled", "#3a3a3a")])

        style.configure("Danger.TButton", background=DANGER, foreground="#ffffff",
                        borderwidth=0, focuscolor="none",
                        font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Danger.TButton", background=[("active", "#ff7777"), ("disabled", "#3a3a3a")])

        style.configure("TCombobox", fieldbackground=INPUT_BG, foreground=FG_COLOR,
                        arrowcolor=FG_COLOR)
        style.map("TCombobox", fieldbackground=[("readonly", INPUT_BG)])

        style.configure("TSeparator", background="#555555")

    # ---- control panel ----

    def _build_control_panel(self):
        """top panel: task picker + start/stop buttons."""
        control = ttk.Frame(self.root, style="Card.TFrame", padding=(12, 10))
        control.pack(fill=tk.X, padx=8, pady=(8, 4))

        # --- task row ---
        task_row = ttk.Frame(control, style="Card.TFrame")
        task_row.pack(fill=tk.X)
        ttk.Label(task_row, text="选择任务类型:", style="Title.TLabel").pack(side=tk.LEFT)
        self.task_var = tk.StringVar()
        self.task_dropdown = ttk.Combobox(task_row, textvariable=self.task_var,
                                          state="readonly", width=24, font=("Microsoft YaHei UI", 9))
        self.task_dropdown['values'] = ("自动镜牢", "日常")
        self.task_dropdown.current(0)
        self.task_dropdown.pack(side=tk.RIGHT)

        # --- button row ---
        btn_row = ttk.Frame(control, style="Card.TFrame")
        btn_row.pack(fill=tk.X, pady=(10, 0))
        self.start_button = ttk.Button(btn_row, text="▶  开始", style="Primary.TButton",
                                       command=self.start_worker)
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.stop_button = ttk.Button(btn_row, text="■  停止", style="Danger.TButton",
                                      command=self.stop_worker, state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    # ---- log panel ----

    def _build_log_panel(self):
        """middle panel: titled log area with colored tags."""
        log_frame = ttk.Frame(self.root, style="Card.TFrame", padding=(12, 8))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # header
        header = ttk.Frame(log_frame, style="Card.TFrame")
        header.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(header, text="运行日志", style="Title.TLabel").pack(side=tk.LEFT)
        self.log_count_var = tk.StringVar(value="0 条")
        ttk.Label(header, textvariable=self.log_count_var,
                  style="Status.TLabel").pack(side=tk.RIGHT)

        # text area with scrollbar
        text_container = ttk.Frame(log_frame, style="Card.TFrame")
        text_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(text_container, bg=LOG_BG, fg="#d0d0d0",
                                font=("Consolas", 9), relief="flat",
                                borderwidth=0, highlightthickness=0,
                                state=tk.DISABLED, yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.configure(command=self.log_text.yview)

        # log level tags
        self.log_text.tag_configure("INFO", foreground="#d0d0d0")
        self.log_text.tag_configure("WARNING", foreground=WARN_ORANGE)
        self.log_text.tag_configure("ERROR", foreground=DANGER)
        self.log_text.tag_configure("SUCCESS", foreground=SUCCESS_GREEN)

        self._log_line_count = 0

    # ---- status bar ----

    def _build_status_bar(self):
        """bottom bar: status dot, state label, separator, elapsed time."""
        bar = ttk.Frame(self.root, style="StatusBar.TFrame", padding=(12, 6))
        bar.pack(side=tk.BOTTOM, fill=tk.X)

        left = ttk.Frame(bar, style="StatusBar.TFrame")
        left.pack(side=tk.LEFT)

        self.status_dot = tk.Canvas(left, width=10, height=10, bg=STATUS_BAR_BG,
                                    highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT, padx=(0, 6))
        self._draw_status_dot(DIM_TEXT)   # idle grey

        self.status_label = ttk.Label(left, text="就绪", style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT)

        right = ttk.Frame(bar, style="StatusBar.TFrame")
        right.pack(side=tk.RIGHT)

        sep = ttk.Separator(right, orient=tk.VERTICAL)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=8)

        self.elapsed_label = ttk.Label(right, text="运行时间: 00:00:00", style="Timer.TLabel")

    def _draw_status_dot(self, color):
        self.status_dot.delete("all")
        self.status_dot.create_oval(1, 1, 9, 9, fill=color, outline=color)

    def _set_status(self, text, dot_color):
        self.status_label.config(text=text)
        self._draw_status_dot(dot_color)

    # ---- elapsed timer ----

    def _start_elapsed_timer(self):
        self.start_time = time.time()
        self.elapsed_label.pack(side=tk.LEFT)
        self._update_elapsed()

    def _update_elapsed(self):
        if self.start_time is None:
            return
        delta = int(time.time() - self.start_time)
        h, r = divmod(delta, 3600)
        m, s = divmod(r, 60)
        self.elapsed_label.config(text=f"运行时间: {h:02d}:{m:02d}:{s:02d}")
        self._elapsed_timer_id = self.root.after(1000, self._update_elapsed)

    def _stop_elapsed_timer(self):
        if self._elapsed_timer_id:
            self.root.after_cancel(self._elapsed_timer_id)
            self._elapsed_timer_id = None
        self.elapsed_label.pack_forget()
        self.start_time = None

    # ---- log processing ----

    def process_log(self):
        try:
            while True:
                msg = log_queue.get_nowait()
                if isinstance(msg, tuple):
                    text, base_level = msg
                else:
                    text, base_level = msg, "INFO"

                # keyword heuristics
                level = self._classify_level(text, base_level)

                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, text, level)
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)

                self._log_line_count += 1
                self.log_count_var.set(f"{self._log_line_count} 条")
        except queue.Empty:
            pass
        self.root.after(10, self.process_log)

    @staticmethod
    def _classify_level(text, base_level):
        if base_level == "ERROR":
            return "ERROR"
        lower = text.lower()
        if any(kw in lower for kw in ["error", "fail", "失败", "错误", "异常"]):
            return "ERROR"
        if any(kw in lower for kw in ["warning", "warn", "警告", "注意"]):
            return "WARNING"
        if any(kw in lower for kw in ["成功", "完成", "启动", "已中断"]):
            return "SUCCESS"
        return "INFO"

    # ---- worker control ----

    def start_worker(self):
        if self.thread is not None and self.thread.is_alive():
            print("线程已在运行中")
            return

        self.stop_event = threading.Event()
        self.monitor = WindowMonitor(self.stop_event)
        task = self.task_var.get()

        if task == "自动镜牢":
            work = run_mirror
        elif task == "日常":
            work = run_daily
        else:
            print(f"不支持的任务类型:{task}")
            return

        self.thread = threading.Thread(target=work, kwargs={'monitor': self.monitor}, daemon=True)
        self.thread.start()
        self.running = True

        print("--------------启动--------------")

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.task_dropdown.config(state=tk.DISABLED)

        self._set_status("运行中", SUCCESS_GREEN)
        self._start_elapsed_timer()
        self._poll_stop()

    def stop_worker(self, event=None):
        if self.stop_event:
            self.stop_event.set()
            self.stop_button.config(state=tk.DISABLED)
            self._set_status("正在停止...", WARN_ORANGE)
            print("--------------停止--------------")
            print("正在中断，请等待...")

    def _poll_stop(self):
        if self.monitor.stop_done:
            print("------------已中断-----------")
            self._reset_ui()
        else:
            self._stop_timer_id = self.root.after(10, self._poll_stop)

    def _reset_ui(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.task_dropdown.config(state="readonly")
        self._set_status("就绪", DIM_TEXT)
        self._stop_elapsed_timer()


if __name__ == '__main__':
    root = tk.Tk()
    root.title("limbus自动镜牢脚本")
    MainPanel(root)
    root.mainloop()
