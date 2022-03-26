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

simon_begin_evt = threading.Event()
simon_begin_evt.clear()

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

def simon_main():
    print("simon_main started")

    while (not exit_evt.is_set()):
        while(not simon_begin_evt.is_set()):
            # hold here after win condition met
            pass
        while(simon_begin_evt.is_set()):
            # once meet win condition -> simon_begin_evt.clear()
            pass

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

    global alarm_hour, alarm_minute, alarm_pm, alarm_on

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
        elif (mode == ClockMode.CLOCK and cur_bttn_press == 27):
            # set alarm state if user presses third button
            alarm_on = True if alarm_on == False else False
        elif (mode == ClockMode.ALARM and cur_bttn_press == 22):
            alarm_on = True
            mode = ClockMode.CLOCK
            print(mode)
            clk_face.set_blink(0)

        # handle clock, alarm, and simon says functionality
        if (mode == ClockMode.CLOCK):
            cur_time = datetime.now()
            hr = int(cur_time.hour % 12)
            if hr == 0: hr = 12
            pm = True if cur_time.hour >= 12 else False

            updt_display(hr, cur_time.minute, pm)

            if (alarm_on == True and int(hr) == int(alarm_hour) and int(cur_time.minute) == int(alarm_minute) and pm == alarm_pm and not simon_begin_evt.is_set()):
                mode = ClockMode.SIMON
        elif (mode == ClockMode.ALARM):
            set_alarm(cur_bttn_press)
        elif (mode == ClockMode.SIMON):
            simon_begin_evt.set()
            mode = ClockMode.CLOCK
            print("started simon game")

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

clk_thread = threading.Thread(target=clk_main)
bttn_thread = threading.Thread(target=bttn_main)
simon_thread = threading.Thread(target=simon_main)

clk_thread.start()
bttn_thread.start()
simon_thread.start()
