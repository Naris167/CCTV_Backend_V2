import tkinter as tk
from tkinter import ttk
import threading
import time
from utils.log_config import logger

class ProgressGUI:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProgressGUI, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        self.initialized = True
        
        self.total_tasks = 0
        self.completed_tasks = 0
        self.root = None
        self.progress_var = None
        self.progress_bar = None
        self.progress_label = None
        self.start_time = None
        self.elapsed_time_var = None
        self.timer_label = None

    def setup(self, total_tasks):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.root = tk.Tk()
        self.root.title("BMA CCTV Scraping Progress")
        self.root.geometry("350x120")

        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(self.root, maximum=self.total_tasks, variable=self.progress_var)
        self.progress_bar.pack(pady=20)

        self.progress_label = tk.Label(self.root, text=f"Task completed: 0/{self.total_tasks}")
        self.progress_label.pack()

        self.start_time = time.time()
        self.elapsed_time_var = tk.StringVar()
        self.elapsed_time_var.set("Elapsed time: 00:00:00")
        self.timer_label = tk.Label(self.root, textvariable=self.elapsed_time_var)
        self.timer_label.pack()

        self.update_timer()

    def update_timer(self):
        if not self.root:
            return
        elapsed_time = time.time() - self.start_time
        hours, rem = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)
        self.elapsed_time_var.set(f"Elapsed time: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")
        self.root.after(1000, self.update_timer)

    def update_progress(self):
        if not self.root:
            return
        self.progress_var.set(self.completed_tasks)
        self.progress_label.config(text=f"Task completed: {self.completed_tasks}/{self.total_tasks}")
        self.root.update_idletasks()

    def increment_progress(self):
        logger.info("Incrementing progress")
        self.completed_tasks += 1
        if self.root:
            self.root.after(0, self.update_progress)

    def run(self, target, args):
        threading.Thread(target=target, args=args).start()
        self.root.mainloop()

    def quit(self):
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None

# Global function to setup and get the ProgressGUI instance
def gui_setup(total_tasks):
    progress_gui = ProgressGUI()
    progress_gui.setup(total_tasks)
    return progress_gui

# Global function to get the existing ProgressGUI instance
def get_progress_gui():
    return ProgressGUI()