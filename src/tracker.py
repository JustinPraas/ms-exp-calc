import collections
import time
from datetime import datetime, date

from image_processing import get_exp_now

# How long do you want to store data (recommended = 2 < x < 10
MEASURE_AVERAGE_OVER_X_MINUTES = 5

MEASURE_EVERY_X_SECONDS = 2

# The deque length, based on the above values, such that the values in the list is the data of the past X minutes
DEQUE_LENGTH = (60 * MEASURE_AVERAGE_OVER_X_MINUTES // MEASURE_EVERY_X_SECONDS)


class Tracker:
    def __init__(self):
        self.session_exp = 0
        self.session_start = datetime.now()
        self.session_avg_per_hour = 0
        self.avg_per_hour = 0
        self.level = 0

        self.previous_exp = -1
        self.diff_exp_list = collections.deque(maxlen=DEQUE_LENGTH)

        self.paused = False

    def start(self):
        while True:
            while not self.paused:
                try:
                    self.process_exp(get_exp_now())
                    # self.session_avg_per_hour = self.calculate_session_average()
                    self.avg_per_hour = self.calculate_avg_exp_hour()
                except Exception as e:
                    print("Exception", e)
                time.sleep(1)

    def set_pause(self):
        self.paused = True

    def set_unpause(self):
        self.paused = False

    def process_exp(self, exp):
        # print("=Received exp", exp)
        if self.previous_exp == -1:
            # print("==Received first exp", exp)
            self.previous_exp = exp
            return

        diff_exp = exp - self.previous_exp
        # print("=Gained", diff_exp)

        if diff_exp < 0:
            print("==Leveled up")

            previous_exp_diff = self.diff_exp_list[len(self.diff_exp_list)-1]
            self.diff_exp_list.append(previous_exp_diff)
            self.session_exp += previous_exp_diff
            print('==Appending previous exp diff', previous_exp_diff)
        else:
            self.diff_exp_list.append(diff_exp)
            self.session_exp += diff_exp

        self.previous_exp = exp
        return

    def calculate_avg_exp_hour(self):
        if len(self.diff_exp_list) == 0:
            return 0
        else:
            average_exp_per_x_seconds = sum(self.diff_exp_list) / len(self.diff_exp_list)
            average_exp_per_min = average_exp_per_x_seconds * (60 / MEASURE_EVERY_X_SECONDS)
            average_exp_per_hour = average_exp_per_min * 60
            return max(0, int(average_exp_per_hour))

    def calculate_session_average(self):
        timediff = datetime.combine(date.today(), datetime.now().time()) - datetime.combine(date.today(), self.session_start.time())
        print(timediff.seconds)
        average_exp_per_second = self.session_exp / max(timediff.seconds, 1)
        return max(0, int(average_exp_per_second * 60 * 60))
