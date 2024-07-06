import tkinter as tk
from tkinter import ttk
import threading

class ProgressGUI:
    def __init__(self, total_tasks):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.root = tk.Tk()
        self.root.title("Progress")
        self.root.geometry("300x100")

        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(self.root, maximum=self.total_tasks, variable=self.progress_var)
        self.progress_bar.pack(pady=20)

        self.progress_label = tk.Label(self.root, text=f"Task completed: 0/{self.total_tasks}")
        self.progress_label.pack()

    def update_progress(self):
        self.progress_var.set(self.completed_tasks)
        self.progress_label.config(text=f"Task completed: {self.completed_tasks}/{self.total_tasks}")
        self.root.update_idletasks()

    def increment_progress(self):
        with threading.Lock():
            self.completed_tasks += 1
            self.update_progress()

    def run(self, target, args):
        # Run the target function in a separate thread
        threading.Thread(target=target, args=args).start()
        # Start the tkinter main loop
        self.root.mainloop()

    def quit(self):
        self.root.quit()
