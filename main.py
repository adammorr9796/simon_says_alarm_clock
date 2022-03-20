import threading
import time
import display
from datetime import datetime
import queue
import RPi.GPIO as GPIO
from enum import Enum

exit_evt = threading.Event()
exit_evt.clear()

bttn_evt = threading.Event()
bttn_evt.clear()

clk_face = display.Display(0x70, 1)
clk_face.setup()
clk_face.write_colon(True)

cur_time = datetime.now()
bttn_q = queue.Queue()

bttn_dict = {10:1, 22:2, 27:3, 17:4}

alarm_hour = 12
alarm_minute = 0
alarm_pm = False
alarm_on = False
cur_alarm_chg = 0

BTTN_0 = 0
BTTN_1 = 1
BTTN_2 = 2
BTTN_3 = 3

class ClockMode(Enum):
    CLOCK = 0
    ALARM = 1
    SIMON = 2

def set_alarm(bttn_press):
    global alarm_hour, alarm_minute, alarm_pm, alarm_on, cur_alarm_chg

    # change which aspect of the alarm we are modifying: hours, minutes, or am/pm
    if (bttn_press == 27):
        cur_alarm_chg = cur_alarm_chg + 1

    # allow user to cycle through each alarm aspect as many times as they want
    if (cur_alarm_chg > 2):
        cur_alarm_chg = 0

    if (cur_alarm_chg == 0):
        if (alarm_hour > 12):
            alarm_hour = 1
        if (alarm_hour < 1):
            alarm_hour = 12

        if (bttn_press == 10):
            alarm_hour = alarm_hour + 1
        elif (bttn_press == 17):
            alarm_hour = alarm_hour - 1
    elif (cur_alarm_chg == 1):
        if (alarm_minute > 59):
            alarm_minute = 0
        if (alarm_minute < 0):
            alarm_minute = 59

        if (bttn_press == 10):
            alarm_minute = alarm_minute + 1
        elif (bttn_press == 17):
            alarm_minute = alarm_minute - 1
    elif (cur_alarm_chg == 2):
        if (bttn_press == 10 or bttn_press == 17):
            alarm_pm = True if alarm_pm == False else False

    updt_display(alarm_hour, alarm_minute, alarm_pm)

def updt_display(hour, minute, pm):
    if (hour < 10):
        clk_face.write_digit(0, 0, False)
        clk_face.write_digit(1, hour, False)
    else:
        clk_face.write_digit(0, 1, False)
        clk_face.write_digit(1, hour % 10, False)

    clk_face.write_digit(2, int(minute / 10), False)
    clk_face.write_digit(3, int(minute % 10), pm)

def bttn_callbk(channel):
    global cur_bttn
    cur_bttn = channel
    bttn_evt.set()

def clk_main():
    print("clk_main started")

    mode = ClockMode.CLOCK

    while(not exit_evt.is_set()):

        # check for queued bttn presses
        if (not bttn_q.empty()):
            cur_bttn_press = bttn_q.get()
        else:
            cur_bttn_press = None

        # set mode logic
        if (mode == ClockMode.CLOCK and cur_bttn_press == 22):
            mode = ClockMode.ALARM
            print(mode)
            clk_face.set_blink(1)
        elif (mode == ClockMode.ALARM and cur_bttn_press == 22):
            mode = ClockMode.CLOCK
            print(mode)
            clk_face.set_blink(0)

        # handle clock, alarm, and simon says functionality
        if (mode == ClockMode.CLOCK):
            cur_time = datetime.now()
            hr = int(cur_time.hour % 12)
            if hr == 0: hr = 12
            updt_display(hr, cur_time.minute, True if cur_time.hour >= 12 else False)
        elif (mode == ClockMode.ALARM):
            set_alarm(cur_bttn_press)
        elif (mode == ClockMode.SIMON):
            pass

def bttn_main():
    print("bttn_main started")
    GPIO.setmode(GPIO.BCM)

    for pin in [10,22,27,17]:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.FALLING, callback=bttn_callbk, bouncetime=100)

    while(not exit_evt.is_set()):
        if (bttn_evt.is_set()):
            bttn_q.put(cur_bttn)
            bttn_evt.clear()

       # if (bttn_evt.is_set() and (cur_bttn == 10 or cur_bttn == 22 or cur_bttn == 17)):
       #     bttn_q.put(cur_bttn)
       #     bttn_evt.clear()
       # elif (bttn_evt.is_set() and cur_bttn == 27):
       #     if (MODE == 0):
       #         #if in CLK_MODE
       #         #set_blink(0)
       #         MODE = 1 #set to ALRM_MODE
       #     elif (MODE == 1):
       #         #if in ALRM_MODE
       #         #set_blink(1)
       #         MODE = 0
       #     elif (MODE == 2):
       #         #if in SIMON_MODE
       #         bttn_q.put(27)
       #     bttn_evt.clear()

clk_thread = threading.Thread(target=clk_main)
bttn_thread = threading.Thread(target=bttn_main)

clk_thread.start()
bttn_thread.start()
