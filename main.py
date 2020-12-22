import collections
import time
import numpy as np

from PIL import ImageGrab
import win32gui
import pytesseract
import cv2

# Define the bounding box of the exp digits
XP_TEXT_START_X = 466
XP_TEXT_WIDTH = 100
XP_TEXT_START_Y = 594
XP_TEXT_HEIGHT = 13
XP_TEXT_CROPBOX = (XP_TEXT_START_X, XP_TEXT_START_Y, XP_TEXT_START_X + XP_TEXT_WIDTH, XP_TEXT_START_Y + XP_TEXT_HEIGHT)

# How many seconds between each calculation?
MEASURE_EVERY_X_SECONDS = 1

# How long do you want to store data (recommended = 2 < x < 10
MEASURE_AVERAGE_OVER_X_MINUTES = 2

# The deque length, based on the above values, such that the values in the list is the data of the past X minutes
DEQUE_LENGTH = (60 * MEASURE_AVERAGE_OVER_X_MINUTES) // MEASURE_EVERY_X_SECONDS

# The experience list (values that are fetched from the screenshots)
expList = collections.deque(maxlen=DEQUE_LENGTH)

# The difference list (diff[1] = exp[1] - exp[0])
diffList = collections.deque(maxlen=DEQUE_LENGTH)

# Returns the (first) maplestory hwnd
def getWindow():
    toplist, winlist = [], []

    def enum_cb(hwnd, results):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))

    win32gui.EnumWindows(enum_cb, toplist)

    maplestory = [(hwnd, title) for hwnd, title in winlist if 'maplestory' in title.lower()]
    maplestory = maplestory[0]
    return maplestory[0]


# Makes a screenshot of the window
def screenshot(hwndMaplestory):
    # Give time for window to popup
    time.sleep(0.05)

    # Get the rectangle of the window
    rect = win32gui.GetWindowRect(hwndMaplestory)

    # Return screenshot of cropped image (only the experience part) and scale the image by 3 times
    return ImageGrab.grab(rect).crop(XP_TEXT_CROPBOX).resize((3*XP_TEXT_WIDTH, 3*XP_TEXT_HEIGHT))


# Returns the bounding box of the experience digits WITHOUT the percentage part
def getEndBoundaryX(input):
    color = cv2.cvtColor(np.array(input), cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(color, (70, 50, 20), (75, 255, 255))
    mask2 = cv2.inRange(color, (130, 50, 20), (135, 255, 255))

    # Merge the mask and crop the red regions
    mask = cv2.bitwise_or(mask1, mask2)
    _, xs = np.nonzero(mask)

    if (len(xs) > 0):
        x = xs[0]
        return x - 1
    else:
        return XP_TEXT_WIDTH


# Processes the screenshot
def processScreenshot(input):
    x = getEndBoundaryX(input)
    gray = cv2.cvtColor(np.array(input.crop((0, 0, x, 3*XP_TEXT_HEIGHT))), cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV+ cv2.THRESH_OTSU)[1]
    return thresh


# Retrieves the experience from the processed screenshots
def getExp(processedScreenshot):
    try:
        exp = pytesseract.image_to_string(processedScreenshot, lang="eng", config="-c tessedit_char_whitelist=0123456789(").split("(")[0]
        print("Received exp data: ", int(exp))
        return int(exp)
    except:
        return -1

def reject_outliers(data, m=2.):
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d / mdev if mdev else 0.
    return data[s < m]


# Processes the newly acquired exp value
def processExpDiff(newExp):
    if (newExp < 0):
        print("Received malformed exp, probably because the window is not in focus")
        diffList.append(0)
        return

    expList.append(newExp)

    # If this is the first received exp
    if (len(expList) == 1):
        print("Received first exp: ", newExp)
    else:
        # If level up, clear list
        if (newExp < min(expList)):
            print("Leveled up")
            expList.clear()
            expList.append(newExp)
        else:
            prevExp = expList[len(expList) - 2]
            diffExp = newExp - prevExp

            diffList.append(diffExp)

    averageExpPerUnit = sum(diffList) / max(len(diffList), 1)
    averageExpPerMin = averageExpPerUnit * (60 / MEASURE_EVERY_X_SECONDS)
    averageExpPerHour = averageExpPerMin * 60
    print("Average exp per min:", round(averageExpPerMin), "\t Average exp per hour: ", round(averageExpPerHour))


def run():
    hwndMaplestory = getWindow()

    while(True):

        # Make screenshot
        ss = screenshot(hwndMaplestory)

        # Process screenshot
        processedScreenshot = processScreenshot(ss)

        # Retrieve exp value
        exp = getExp(processedScreenshot)

        # Process the experience received and update stats
        processExpDiff(exp)

        # Sleep for next loop
        time.sleep(MEASURE_EVERY_X_SECONDS)

if __name__ == '__main__':
    run()
