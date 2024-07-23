import tkinter as tk
from tkinter import ttk
import threading
import time
import logging

class ProgressGUI:
    def __init__(self, total_tasks):
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
        elapsed_time = time.time() - self.start_time
        hours, rem = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)
        self.elapsed_time_var.set(f"Elapsed time: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")
        self.root.after(1000, self.update_timer)  # Schedule the timer to update every second

    def update_progress(self):
        self.progress_var.set(self.completed_tasks)
        self.progress_label.config(text=f"Task completed: {self.completed_tasks}/{self.total_tasks}")
        self.root.update_idletasks()

    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def increment_progress(self):
        logging.debug("Incrementing progress")
        self.completed_tasks += 1
        self.root.after(0, self.update_progress)

    def run(self, target, args):
        # Run the target function in a separate thread
        threading.Thread(target=target, args=args).start()
        # Start the tkinter main loop
        self.root.mainloop()

    def quit(self):
        self.root.quit()
