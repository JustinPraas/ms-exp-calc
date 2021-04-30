import pathlib
import time

# TODO exportify project
# TODO prettify window
from datetime import datetime

import cv2
import numpy as np
import win32gui
from PIL import ImageGrab
from pytesseract import pytesseract

tessdata_path = str(pathlib.Path(__file__).parent.parent / 'tessdata').replace("\\", "/")
tessocr_path = str(pathlib.Path(__file__).parent.parent / 'Tesseract-OCR/tesseract.exe').replace("\\", "/")
pytesseract.tesseract_cmd = tessocr_path
tessdata_dir_config = '--tessdata-dir ' + tessdata_path

FULL_SCREEN_RECT = (0, 0, 800, 600)
FULL_SCREEN_HEIGHT_DIFF = 26
FULL_SCREEN_WIDTH_DIFF = 3


XP_TEXT_START_X = 468
XP_TEXT_WIDTH = 98
XP_TEXT_START_Y = 594
XP_TEXT_HEIGHT = 11
XP_TEXT_RECT = (XP_TEXT_START_X, XP_TEXT_START_Y, XP_TEXT_START_X + XP_TEXT_WIDTH, XP_TEXT_START_Y + XP_TEXT_HEIGHT)

LVL_TEXT_START_X = 39
LVL_TEXT_WIDTH = 38
LVL_TEXT_START_Y = 603
LVL_TEXT_HEIGHT = 12
LVL_TEXT_RECT = (LVL_TEXT_START_X, LVL_TEXT_START_Y, LVL_TEXT_START_X + LVL_TEXT_WIDTH, LVL_TEXT_START_Y + LVL_TEXT_HEIGHT)

TOP_MOST_CHECKER_X = 600
TOP_MOST_CHECKER_Y = 595
TOP_MOST_RECT_TOP = (XP_TEXT_START_X, XP_TEXT_START_Y - 1, XP_TEXT_START_X + XP_TEXT_WIDTH, XP_TEXT_START_Y + 5)
TOP_MOST_RECT_BOT = (XP_TEXT_START_X, XP_TEXT_START_Y + XP_TEXT_HEIGHT, XP_TEXT_START_X + XP_TEXT_WIDTH, XP_TEXT_START_Y + XP_TEXT_HEIGHT + 1)


def get_final_rect(rect, full_screen):
    if full_screen:
        return rect[0] - FULL_SCREEN_WIDTH_DIFF, rect[1] - FULL_SCREEN_HEIGHT_DIFF, rect[2] - FULL_SCREEN_WIDTH_DIFF, rect[3] - FULL_SCREEN_HEIGHT_DIFF
    else:
        return rect


def get_level_and_exp_now():
    hwnd_maplestory = get_window()

    # Make screenshot
    ss = screenshot_maple_window(hwnd_maplestory)

    full_screen = is_full_screen(get_maple_window_rectangle(hwnd_maplestory))

    # Process screenshot
    processed_screenshot_exp = process_screenshot_exp(ss, full_screen)
    processed_screenshot_level = process_screenshot_level(ss, full_screen)

    # Retrieve exp value
    return get_level(processed_screenshot_level), get_exp(processed_screenshot_exp)


# Returns the (first) maplestory hwnd
def get_window():
    top_list, win_list = [], []

    def enum_cb(hwnd, _):
        win_list.append((hwnd, win32gui.GetWindowText(hwnd)))

    win32gui.EnumWindows(enum_cb, top_list)

    maple_story = [(hwnd, title) for hwnd, title in win_list if 'maplestory' in title.lower()]
    maple_story = maple_story[0]
    return maple_story[0]


def is_full_screen(rect):
    return rect == FULL_SCREEN_RECT


def is_top_most_window(ss_rect):

    # Check if fullscreen
    full_screen = is_full_screen(ss_rect)

    # Check topmost
    topmost_check_img_top = ImageGrab.grab(ss_rect).crop(get_final_rect(TOP_MOST_RECT_TOP, full_screen))
    topmost_check_img_bot = ImageGrab.grab(ss_rect).crop(get_final_rect(TOP_MOST_RECT_BOT, full_screen))

    img_np_topmost_top = np.array(topmost_check_img_top)[0]
    img_np_topmost_bot = np.array(topmost_check_img_bot)[0]

    for pixel in img_np_topmost_top:
        if not (96 <= pixel[0] <= 102 and 102 <= pixel[1] <= 108 and pixel[2] == 108):
            return False

    for pixel in img_np_topmost_bot:
        if not (45 <= pixel[0] <= 51 and 51 <= pixel[1] <= 57 and 57 <= pixel[2] <= 62):
            return False
    return True


def get_maple_window_rectangle(hwnd_maplestory):
    return win32gui.GetWindowRect(hwnd_maplestory)


# Makes a screenshot of the window
def screenshot_maple_window(hwnd_maplestory):
    # Give time for window to popup
    time.sleep(0.05)

    # Get the rectangle of the window
    rect = get_maple_window_rectangle(hwnd_maplestory)

    # Cashshop and exp check
    if not (is_top_most_window(rect)):
        raise Exception("Cashshop or yellow exp not visible, aka not topmost")

    # Return screenshot of cropped image (only the experience part) and scale the image by 8 times
    img = ImageGrab.grab(rect)
    # img.show()

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
def process_screenshot_exp(screenshot_image, full_screen):

    # Get proper rect and resize
    crop_rect = get_final_rect(XP_TEXT_RECT, full_screen)
    cropped_img = screenshot_image.crop(crop_rect)
    resized_img = cropped_img.resize((8 * XP_TEXT_WIDTH, 8 * XP_TEXT_HEIGHT))

    # Trim off redundant space after text (based on the [ in the exp text)
    x = get_end_boundary_x(resized_img)
    trimmed_img = resized_img.crop((0, 0, x, 8 * XP_TEXT_HEIGHT))

    # Grayify
    gray = cv2.cvtColor(np.array(trimmed_img), cv2.COLOR_BGR2GRAY)
    # cv2.imshow("img", gray)

    # Threshify
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    # cv2.imshow("thresh", thresh)

    # current_time = str(datetime.now().time().microsecond)
    # print(current_time)
    # cv2.imwrite(current_time + ".jpg", thresh)

    return thresh


def process_screenshot_level(screenshot_image, full_screen):
    crop_rect = get_final_rect(LVL_TEXT_RECT, full_screen)
    cropped_img = screenshot_image.crop(crop_rect)
    resized_img = cropped_img.resize((4 * LVL_TEXT_WIDTH, 4 * LVL_TEXT_HEIGHT))
    gray = cv2.cvtColor(np.array(resized_img), cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1]
    return thresh


# Retrieves the experience from the processed screenshots
def get_exp(processed_screenshot):
    exp = pytesseract.image_to_string(processed_screenshot, lang="eng",
                                      config="{} --psm 13 -c tessedit_char_whitelist=0123456789".format(
                                          tessdata_dir_config))
    exp = exp.strip().replace(" ", "")
    # print("Received exp data:", exp.strip().replace(" ", ""))
    try:
        # cv2.waitKey(0)
        if exp == "":
            exp = 0
        return int(exp)
    except Exception as e:
        print("Received malformed exp data.")
        print(e)
        return -1


def get_level(processed_screenshot):
    level = pytesseract.image_to_string(processed_screenshot, lang="eng",
                                        config="{} --psm 13 -c tessedit_char_whitelist=0123456789".format(
                                            tessdata_dir_config))
    level = level.strip().replace(" ", "")
    try:
        # cv2.waitKey(0)
        if level == "":
            level = 0
        return int(level)
    except Exception as e:
        print("Received malformed level data.")
        print(e)
        return -1
