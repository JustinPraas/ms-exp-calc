from datetime import time

from image_processing import get_exp_now


class Tracker:
    def __init__(self):
        self.session_exp = 0
        self.avgPerHour = 0
        self.level = 0

        self.paused = True

    def start(self):
        while True:
            while not self.paused:
                try:
                    print(get_exp_now())
                except Exception as e:
                    print("Caught exception")
                    print(e)
                time.sleep(1)
