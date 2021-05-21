import threading
from tkinter import *

from tracker import Tracker


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
        Label(self.frame, text="Session duration: {}".format(str(self.tracker.session_duration).split(".")[0])).pack()
        Label(self.frame, text="Session exp: {}".format(self.tracker.session_exp)).pack()
        Label(self.frame, text="Session exp/h: {}".format(self.tracker.session_avg_per_hour)).pack()
        # Label(self.frame, text="Exp/hour (session): {}".format(self.tracker.session_avg_per_hour)).pack()
        Label(self.frame, text="Exp/hour (5min): {}".format(self.tracker.avg_per_hour)).pack()
        Label(self.frame, text="Level up estimated at: {}".format(self.tracker.level_up_at.strftime("%H:%M:%S"))).pack()
        Label(self.frame, text="Made by Bushido").pack()
        self.window.after(1000, self.draw)
