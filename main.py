import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import time
import sys
import queue
import datetime
from event import run_mirror,run_daily
from monitor import WindowMonitor

log_queue = queue.Queue()


class QueueRedirector:
    def __init__(self, queue, max_lines=100):
        self.queue = queue
        self.max_lines = max_lines
        self.lines = []

    def write(self, message):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        for line in message.splitlines():
            if not line.strip():
                continue
            log_line = timestamp + line
            self.lines.append(log_line)
            # 限制最大日志行数
            if len(self.lines) > self.max_lines:
                self.lines = self.lines[-self.max_lines:]
            self.queue.put(log_line + "\n")  # 放入 GUI 消费队列




class MainPanel:
    def __init__(self,root) -> None:
        self.root = root
        self.thread = None
        self.stop_event = None
        # 设置 UI
        self.root.geometry("520x340")
        self.root.minsize(520, 340)
        self.root.minsize(520, 340)
        self.root.maxsize(800, 600)


        # 下拉选项框（任务类型选择）
        self.task_label = tk.Label(root, text="选择任务类型:")
        self.task_label.pack(pady=(10, 0))

        self.task_var = tk.StringVar()
        self.task_dropdown = ttk.Combobox(root, textvariable=self.task_var, state="readonly", width=30)
        self.task_dropdown['values'] = ("自动镜牢",'日常')
        self.task_dropdown.current(0)
        self.task_dropdown.pack(pady=5)

        self.start_button = tk.Button(root, text="开始", command=self.start_worker, width=30)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="停止", command=self.stop_worker, width=30,state=tk.DISABLED)
        self.stop_button.pack(pady=5)
        self.log_text = scrolledtext.ScrolledText(root, width=60, height=10, state=tk.DISABLED)
        self.log_text.pack(padx=10,pady=10,fill=tk.BOTH, expand=True)

        # 重定向 stdout 和 stderr
        sys.stdout = QueueRedirector(log_queue, max_lines=2000)
        sys.stderr = QueueRedirector(log_queue, max_lines=2000)
        self.root.after(10, self.process_log)


    def process_log(self):
        try:
            while True:
                msg = log_queue.get_nowait()
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, msg)
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.root.after(10, self.process_log)

    def check_stop(self):
        if self.monitor.stop_done:
            print('------------已中断-----------')
            self.reset_ui()
        else:
            self.root.after(10, self.check_stop)  # 让 Tkinter 继续执行，而不是 `sleep()`

    def start_worker(self):

        if self.thread is None or not self.thread.is_alive():
            self.stop_event = threading.Event()
            m = WindowMonitor(self.stop_event)
            task = self.task_var.get()
            if task == '自动镜牢':
                work = run_mirror
            elif task == '日常':
                work = run_daily
            else:
                print(f'不支持的任务类型:{task}')
                return False
            self.monitor = m
            self.thread = threading.Thread(target=work,kwargs={'monitor':m}, daemon=True)
            self.thread.start()
            print("--------------启动--------------")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.task_dropdown.config(state=tk.DISABLED)
            self.check_stop()
        else:
            print("线程已在运行中")


    def stop_worker(self):
        if self.stop_event:
            self.stop_event.set()
            self.stop_button.config(state=tk.DISABLED)
            print("--------------停止--------------")
            print("正在中断，请等待...")
        # self.check_stop()  # 启动检查
    def reset_ui(self):
        """重置 UI 控件状态"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.task_dropdown.config(state="readonly")





if __name__ == '__main__':
    # 创建 Tkinter 应用
    root = tk.Tk()
    root.title("limbus自动镜牢脚本")

    main_panel = MainPanel(root)
    root.mainloop()













