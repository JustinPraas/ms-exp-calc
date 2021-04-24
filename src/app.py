import threading
from tkinter import *

from src.tracker import Tracker


class App:
    def __init__(self):
        self.tracker = Tracker()

        self.window = Tk()
        self.window.geometry("300x200+800+500")

        self.frame = Frame(self.window, width=600, height=200)
        self.frame.pack()

    def start(self):
        threading.Thread(target=self.tracker.start).start()
        self.window.after(0, self.draw)
        self.window.mainloop()

    def draw(self):
        self.frame.destroy()
        self.frame = Frame(self.window, width=600, height=200)
        self.frame.pack()

        Label(self.frame, text="Session Start: {}".format(self.tracker.session_start.strftime("%H:%M:%S"))).pack()
        Label(self.frame, text="Session exp: {}".format(self.tracker.session_exp)).pack()
        # Label(self.frame, text="Exp/hour (session): {}".format(self.tracker.session_avg_per_hour)).pack()
        Label(self.frame, text="Exp/hour (5min): {}".format(self.tracker.avg_per_hour)).pack()
        Button(self.frame, text="PAUSE" if not self.tracker.paused else "UNPAUSE", command=(self.tracker.set_pause if not self.tracker.paused else self.tracker.set_unpause)).pack()
        self.window.after(1000, self.draw)
