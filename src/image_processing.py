import collections
import pathlib
import time

import cv2
import numpy as np
import win32gui
from PIL import ImageGrab
from pytesseract import pytesseract

tessdata_path = str(pathlib.Path(__file__).parent.parent / 'tessdata').replace("\\", "/")
pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
tessdata_dir_config = '--tessdata-dir ' + tessdata_path

XP_TEXT_START_X = 468
XP_TEXT_WIDTH = 98
XP_TEXT_START_Y = 594
XP_TEXT_HEIGHT = 11
XP_TEXT_CROPBOX = (XP_TEXT_START_X, XP_TEXT_START_Y, XP_TEXT_START_X + XP_TEXT_WIDTH, XP_TEXT_START_Y + XP_TEXT_HEIGHT)
TOP_MOST_CROPBOX_YELLOW_EXP = (XP_TEXT_START_X - 23, XP_TEXT_START_Y + 20, XP_TEXT_START_X - 22, XP_TEXT_START_Y + 21)

TOP_MOST_CHECKER_X = 600
TOP_MOST_CHECKER_Y = 595
TOP_MOST_CROPBOX_CASHSHOP = (TOP_MOST_CHECKER_X, TOP_MOST_CHECKER_Y, TOP_MOST_CHECKER_X + 1, TOP_MOST_CHECKER_Y + 1)

# How long do you want to store data (recommended = 2 < x < 10
MEASURE_AVERAGE_OVER_X_MINUTES = 6

# The deque length, based on the above values, such that the values in the list is the data of the past X minutes
DEQUE_LENGTH = (60 * MEASURE_AVERAGE_OVER_X_MINUTES)

# The experience list (values that are fetched from the screenshots)
expList = collections.deque(maxlen=DEQUE_LENGTH)

# The difference list (diff[1] = exp[1] - exp[0])
diffList = collections.deque(maxlen=DEQUE_LENGTH)


def get_exp_now():
    hwnd_maplestory = get_window()

    while True:
        # Make screenshot
        ss = screenshot(hwnd_maplestory)

        # Process screenshot
        processed_screenshot = process_screenshot(ss)

        # Retrieve exp value
        return get_exp(processed_screenshot)


# Returns the (first) maplestory hwnd
def get_window():
    top_list, win_list = [], []

    def enum_cb(hwnd, _):
        win_list.append((hwnd, win32gui.GetWindowText(hwnd)))

    win32gui.EnumWindows(enum_cb, top_list)

    maple_story = [(hwnd, title) for hwnd, title in win_list if 'maplestory' in title.lower()]
    maple_story = maple_story[0]
    return maple_story[0]


def is_top_most_window(rect):
    # Check topmost
    topmost_check_img_cashshop = ImageGrab.grab(rect).crop(TOP_MOST_CROPBOX_CASHSHOP)
    topmost_check_img_yellow_exp = ImageGrab.grab(rect).crop(TOP_MOST_CROPBOX_YELLOW_EXP)
    img_np_cash = np.array(topmost_check_img_cashshop)[0][0]
    img_np_yellow_exp = np.array(topmost_check_img_yellow_exp)[0][0]

    return (img_np_cash[0] == 204 and img_np_cash[1] == 0 and img_np_cash[2] == 34) and not (
                img_np_yellow_exp[0] == 238 and img_np_yellow_exp[1] == 246 and img_np_yellow_exp[2] == 127)


# Makes a screenshot of the window
def screenshot(hwnd_maplestory):
    # Give time for window to popup
    time.sleep(0.05)

    # Get the rectangle of the window
    rect = win32gui.GetWindowRect(hwnd_maplestory)

    # Cashshop and exp check
    if not (is_top_most_window(rect)):
        raise Exception("Cashshop or yellow exp not visible, aka not topmost")

    # Return screenshot of cropped image (only the experience part) and scale the image by 8 times
    img = ImageGrab.grab(rect).crop(XP_TEXT_CROPBOX).resize((8 * XP_TEXT_WIDTH, 8 * XP_TEXT_HEIGHT))

    return img


# Returns the bounding box of the experience digits WITHOUT the percentage part
def get_end_boundary_x(image):
    color = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2HSV)
    # cv2.imshow("color", color)
    mask1 = cv2.inRange(color, (70, 50, 20), (75, 255, 255))
    mask2 = cv2.inRange(color, (130, 50, 20), (135, 255, 255))

    # Merge the mask and crop the red regions
    mask = cv2.bitwise_or(mask1, mask2)
    # cv2.imshow("mask", mask)
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
    # cv2.imshow("img", gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    # cv2.imshow("thresh", thresh)
    # current_time = str(datetime.now().time()).replace(":", "")
    # path = ""
    # cv2.imwrite(current_time + ".png", thresh)

    return thresh


# Retrieves the experience from the processed screenshots
def get_exp(processed_screenshot):
    exp = pytesseract.image_to_string(processed_screenshot, lang="eng",
                                      config="{} --psm 13 -c tessedit_char_whitelist=0123456789".format(
                                          tessdata_dir_config))
    # print("Received exp data:", exp.strip().replace(" ", ""))
    try:
        # cv2.waitKey(0)
        return int(exp)
    except:
        print("Received malformed exp data.")
        return -1
