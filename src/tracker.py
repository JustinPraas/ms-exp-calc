import collections
import time
from datetime import datetime, date, timedelta

from image_processing import get_level_and_exp_now

# How long do you want to store data (recommended = 2 < x < 10
MEASURE_AVERAGE_OVER_X_MINUTES = 5

MEASURE_EVERY_X_SECONDS = 2

# The deque length, based on the above values, such that the values in the list is the data of the past X minutes
DEQUE_LENGTH = (60 * MEASURE_AVERAGE_OVER_X_MINUTES // MEASURE_EVERY_X_SECONDS)

EXP_TABLE = [15, 34, 57, 92, 135, 272, 391, 555, 709, 1077, 1493, 1934, 2611, 3477, 5043, 6667, 7786, 9941, 11760,
             13337, 16841, 20909, 25410, 29990, 34899, 40910, 48139, 55317, 64738, 74952, 79557, 85336, 91492, 97437,
             104636, 118227, 137992, 154988, 177760, 198651, 227424, 253870, 285773, 325662, 366800, 397337, 434911,
             477010, 512009, 562577, 577760, 589113, 613449, 628768, 639773, 671780, 701992, 733880, 767841, 798336,
             839417, 899722, 946337, 987521, 1024991, 1076228, 1175761, 1235770, 1291138, 1320752, 1335331, 1384486,
             1412227, 1436852, 1454545, 1476537, 1502423, 1576900, 1693575, 1780089, 1947133, 2098871, 2377532, 2557792,
             2892300, 3238000, 3576291, 3886526, 4213662, 4541008, 4811520, 5181622, 5564300, 5931007, 6172700, 6547392,
             6999386, 7315380, 7749374, 8103368, 8555337, 9195123, 9709909, 10064696, 10619482, 11174268, 11929054,
             12683841, 13177823, 13840548, 14603273, 15365997, 16328722, 17191447, 18154172, 19016896, 20079621,
             21142346, 22555071, 23557795, 25487793, 27100972, 28763151, 30507331, 32380510, 34353689, 36470868,
             38700047, 40820228, 43058406, 45387587, 47806765, 50515945, 53275121, 55994302, 59233481, 62462660,
             65791849, 69221028, 73350203, 76512050, 79736261, 82990470, 86624681, 89918892, 93813107, 97587318,
             101501522, 105015733, 109939946, 116176411, 122335980, 129255300, 136117050, 142897652, 151353909,
             159431170, 168677206, 177886501, 187025723, 198612204, 209446513, 220790085, 232449103, 245861777,
             259333200, 275369910, 292130769, 311876510, 333515724, 355822658, 380500631, 415133603, 451020072,
             488416009, 519995053, 563210971, 605577799, 654210077, 697310500, 747390727, 798611377, 856456260,
             930344518, 1001546969, 1083550805, 1180743580, 1286875962, 1324216724, 1414799800, 1536209309, 1648150007,
             1734387871, 1877820714, 1948648833, 1995795693, 2037898648, 2091069705, 2147483647]


class Tracker:
    def __init__(self):
        self.session_exp = 0
        self.session_start = datetime.now()
        self.session_avg_per_hour = 0
        self.avg_per_hour = 0
        self.level = 0
        self.level_up_at = datetime.max

        self.previous_exp = -1
        self.diff_exp_list = collections.deque(maxlen=DEQUE_LENGTH)

        self.paused = False

    def start(self):
        while True:
            while not self.paused:
                try:
                    (level, exp) = get_level_and_exp_now()
                    self.process_exp(exp)
                    self.avg_per_hour = self.calculate_avg_exp_hour()

                    self.level = level
                    self.level_up_at = self.calculate_level_up_at(level, exp)
                except Exception as e:
                    print("Exception", e)
                time.sleep(MEASURE_EVERY_X_SECONDS)
            time.sleep(MEASURE_EVERY_X_SECONDS)

    def set_pause(self):
        self.paused = True

    def set_unpause(self):
        self.paused = False

    def process_exp(self, exp):
        if self.previous_exp == -1:
            self.previous_exp = exp
            return

        diff_exp = exp - self.previous_exp

        if diff_exp < 0:
            previous_exp_diff = self.diff_exp_list[len(self.diff_exp_list) - 1]
            self.diff_exp_list.append(previous_exp_diff)
            self.session_exp += previous_exp_diff
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
        timediff = datetime.combine(date.today(), datetime.now().time()) - datetime.combine(date.today(),
                                                                                            self.session_start.time())
        print(timediff.seconds)
        average_exp_per_second = self.session_exp / max(timediff.seconds, 1)
        return max(0, int(average_exp_per_second * 60 * 60))

    ''' datetime.time '''
    def calculate_level_up_at(self, level, current_exp):
        exp_to_level_up = EXP_TABLE[level - 1]
        exp_to_go = exp_to_level_up - current_exp

        try:
            hours_to_go = exp_to_go / self.avg_per_hour
            seconds_to_go = int(hours_to_go * 3600)
        except:
            print("Not receiving any exp so it will infinite time to level up")
            return datetime.max
        final_time = datetime.now() + timedelta(0,seconds_to_go)
        return final_time
