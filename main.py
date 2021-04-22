import collections
import time
from datetime import datetime

import numpy as np

from PIL import ImageGrab
import win32gui
import pytesseract
import cv2

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Define the bounding box of the exp digits
XP_TEXT_START_X = 468
XP_TEXT_WIDTH = 98
XP_TEXT_START_Y = 594
XP_TEXT_HEIGHT = 11
XP_TEXT_CROPBOX = (XP_TEXT_START_X, XP_TEXT_START_Y, XP_TEXT_START_X + XP_TEXT_WIDTH, XP_TEXT_START_Y + XP_TEXT_HEIGHT)

# How long do you want to store data (recommended = 2 < x < 10
MEASURE_AVERAGE_OVER_X_MINUTES = 6

# The deque length, based on the above values, such that the values in the list is the data of the past X minutes
DEQUE_LENGTH = (60 * MEASURE_AVERAGE_OVER_X_MINUTES)

# The experience list (values that are fetched from the screenshots)
expList = collections.deque(maxlen=DEQUE_LENGTH)

# The difference list (diff[1] = exp[1] - exp[0])
diffList = collections.deque(maxlen=DEQUE_LENGTH)


# Returns the (first) maplestory hwnd
def get_window():
    top_list, win_list = [], []

    def enum_cb(hwnd, _):
        win_list.append((hwnd, win32gui.GetWindowText(hwnd)))

    win32gui.EnumWindows(enum_cb, top_list)

    maple_story = [(hwnd, title) for hwnd, title in win_list if 'maplestory' in title.lower()]
    maple_story = maple_story[0]
    return maple_story[0]


# Makes a screenshot of the window
def screenshot(hwnd_maplestory):
    # Give time for window to popup
    time.sleep(0.05)

    # Get the rectangle of the window
    rect = win32gui.GetWindowRect(hwnd_maplestory)

    # Return screenshot of cropped image (only the experience part) and scale the image by 3 times
    img = ImageGrab.grab(rect).crop(XP_TEXT_CROPBOX).resize((8 * XP_TEXT_WIDTH, 8 * XP_TEXT_HEIGHT))

    return img


# Returns the bounding box of the experience digits WITHOUT the percentage part
def get_end_boundary_x(image):
    color = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2HSV)
    cv2.imshow("color", color)
    mask1 = cv2.inRange(color, (70, 50, 20), (75, 255, 255))
    mask2 = cv2.inRange(color, (130, 50, 20), (135, 255, 255))

    # Merge the mask and crop the red regions
    mask = cv2.bitwise_or(mask1, mask2)
    cv2.imshow("mask", mask)
    ys, xs = np.nonzero(mask)

    if len(xs) > 0:
        x = min(xs)
        return x - 1
    else:
        return XP_TEXT_WIDTH


# Processes the screenshot
def process_screenshot(screenshot_image):
    x = get_end_boundary_x(screenshot_image)
    gray = cv2.cvtColor(np.array(screenshot_image.crop((0, 0, x, 8 * XP_TEXT_HEIGHT))), cv2.COLOR_BGR2GRAY)
    cv2.imshow("img", gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    cv2.imshow("thresh", thresh)
    # current_time = str(datetime.now().time()).replace(":", "")
    # path = ""
    # cv2.imwrite(current_time + ".png", thresh)

    return thresh


# Retrieves the experience from the processed screenshots
def get_exp(processed_screenshot):
    exp = pytesseract.image_to_string(processed_screenshot, lang="eng", config="--psm 13 -c tessedit_char_whitelist=0123456789")
    print("Received exp data:", exp.strip().replace(" ", ""))
    try:
        cv2.waitKey(0)
        return int(exp)
    except:
        return -1


def is_outlier(value, p25, p75):
    """Check if value is an outlier
    """
    lower = p25 - 1.5 * (p75 - p25)
    upper = p75 + 1.5 * (p75 - p25)
    return value <= lower or value >= upper


def remove_outliers(values):
    """Get outlier indices (if any)
    """
    p75 = np.percentile(values, 75)
    p25 = np.percentile(values, 25)

    non_outliers = []
    for ind, value in enumerate(values):
        if not is_outlier(value, p25, p75):
            non_outliers.append(value)
    return non_outliers


# Processes the newly acquired exp value
def process_exp_diff(new_exp):
    if new_exp < 0:
        print("Received malformed exp, probably because the window is not in focus")
        diffList.append(0)
        return

    expList.append(new_exp)

    # If this is the first received exp
    if len(expList) == 1:
        print("Received first exp: ", new_exp)
    else:
        # If level up, clear list
        if new_exp < min(expList):
            print("Leveled up")
            expList.clear()
            expList.append(new_exp)
        else:
            prev_exp = expList[len(expList) - 2]
            diff_exp = new_exp - prev_exp

            diffList.append(diff_exp)

    without_outliers = remove_outliers(list(diffList)) if len(diffList) > 3 else diffList

    average_exp_per_sec = sum(without_outliers) / max(len(without_outliers), 1)
    average_exp_per_min = average_exp_per_sec * 60
    average_exp_per_hour = average_exp_per_min * 60
    print("Average exp per min:", round(average_exp_per_min), "\t Average exp per hour: ", round(average_exp_per_hour))


def run():
    hwnd_maplestory = get_window()

    while True:
        # Make screenshot
        ss = screenshot(hwnd_maplestory)


        # Process screenshot
        processed_screenshot = process_screenshot(ss)

        # Retrieve exp value
        exp = get_exp(processed_screenshot)

        # Process the experience received and update stats
        process_exp_diff(exp)

        # Sleep for next loop
        time.sleep(1)


if __name__ == '__main__':
    run()
