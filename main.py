import threading
import time
import display
from datetime import datetime
import queue
import RPi.GPIO as GPIO
import random
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

LED_0 = 26
LED_1 = 19
LED_2 = 13
LED_3 = 6

BTTN_0 = 10
BTTN_1 = 22
BTTN_2 = 27
BTTN_3 = 17

bttn_to_led_dict = {BTTN_0:LED_0, BTTN_1:LED_1, BTTN_2:LED_2, BTTN_3:LED_3}

alarm_hour = 12
alarm_minute = 0
alarm_pm = False
alarm_on = False
cur_alarm_chg = 0

GPIO.setwarnings(False)

led_arr = [LED_0, LED_1, LED_2, LED_3]
bttn_arr = [BTTN_0, BTTN_1, BTTN_2, BTTN_3]

class ClockMode(Enum):
    CLOCK = 0
    ALARM = 1
    SIMON = 2

def hold_in_alarm():
    while(bttn_q.empty()):
        # need to activate buzzer
        for pin in led_arr:
            GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.25)
        for pin in led_arr:
            GPIO.output(pin, GPIO.LOW)
        time.sleep(0.25)

def clear_bttn_queue():
    while (not bttn_q.empty()):
        bttn_q.get()

def simon_main():
    print("simon_main started")

    for pin in led_arr:
        GPIO.setup(pin, GPIO.OUT)

    while (not exit_evt.is_set()):
        if (simon_begin_evt.is_set()):
            win = False
            pattern = [bttn_arr[random.randint(0, 3)] for _ in range(10)] # generate random pattern of bttn presses
            print(pattern)
            difficulty = random.randint(3,10) # user must play up to a certain number of button presses each time
            print(difficulty)
            cur_level = 1
            cur_speed = 1.0
            user_pattern_q = queue.Queue()

            success = False

            hold_in_alarm()

            clear_bttn_queue()

            time0 = time.time()
            time1 = time.time()

            while(not win):
                # increase speed as difficulty increases
                if (success and cur_level != 0 and cur_level % 2 == 0):
                    cur_speed = cur_speed - 0.075

                # play pattern for user to duplicate
                for cur_led in range(0,cur_level):
                    GPIO.output(bttn_to_led_dict[pattern[cur_led]], GPIO.HIGH)
                    # play sound when buzzer implemented
                    time.sleep(cur_speed)
                    GPIO.output(bttn_to_led_dict[pattern[cur_led]], GPIO.LOW)
                    time.sleep(0.25) #fix timing here

                # clear any accidental button presses
                clear_bttn_queue()

                # get user pattern
                while (bttn_q.qsize() < cur_level):
                    #pass
                    time0 = time.time()
                    if (time0 - time1 > 30):
                        win = True # not actually, breaks us out of loop with begin evt still set -> will restart game
                        break
                # break out of loop if user hasnt interacted in more than 60s
                if (time0 - time1 > 30):
                    break
                time1 = time.time()

                success = True
                # verify user pattern against current pattern
                for pattern_index in range(0, cur_level):
                    user_press = bttn_q.get()
                    cpu_press = pattern[pattern_index]
                    if (user_press != cpu_press):
                        success = False
                        break

                #advance pattern if right, replay if incorrect
                if success:
                    cur_level = cur_level + 1

                if (cur_level > difficulty):
                    win = True
                    simon_begin_evt.clear()
                    #flash leds one after the other - you won!
                    for _ in range(0,3):
                        for pin in led_arr:
                            GPIO.output(pin, GPIO.HIGH)
                            time.sleep(0.125)
                            GPIO.output(pin, GPIO.LOW)
                            time.sleep(0.125)

       # while(not simon_begin_evt.is_set()):
       #     # hold here after win condition met
       #     for pin in led_arr:
       #         GPIO.output(pin, GPIO.HIGH)
       #     time.sleep(1)
       #     for pin in led_arr:
       #         GPIO.output(pin, GPIO.LOW)
       #     time.sleep(1)
       #
       # while(simon_begin_evt.is_set()):
       #
            # once meet win condition -> simon_begin_evt.clear()
       #     pass

def set_alarm(bttn_press):
    global alarm_hour, alarm_minute, alarm_pm, alarm_on, cur_alarm_chg

    # change which aspect of the alarm we are modifying: hours, minutes, or am/pm
    if (bttn_press == BTTN_2):
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

def bttn_queue_pop():
    if (not bttn_q.empty() and not simon_begin_evt.is_set()):
        return bttn_q.get()
    else:
        return -1

def clk_main():
    print("clk_main started")

    global alarm_hour, alarm_minute, alarm_pm, alarm_on

    mode = ClockMode.CLOCK

    cur_bttn_press = -1

    while(not exit_evt.is_set()):

        # let simon thread take care of button presses when playing game; else pop button presses off queue
        if (mode == ClockMode.CLOCK or mode == ClockMode.ALARM):
            cur_bttn_press = bttn_queue_pop()

        # set mode logic
        if (mode == ClockMode.CLOCK and cur_bttn_press == BTTN_1):
            mode = ClockMode.ALARM
            print(mode)
            clk_face.set_blink(1)
        elif (mode == ClockMode.CLOCK and cur_bttn_press == BTTN_2):
            # set alarm state if user presses third button
            alarm_on = True if alarm_on == False else False
        elif (mode == ClockMode.ALARM and cur_bttn_press == BTTN_1):
            alarm_on = True
            mode = ClockMode.CLOCK
            print(mode)
            clk_face.set_blink(0)

        # handle clock, alarm, and simon says functionality
        if (mode == ClockMode.CLOCK):
            #cur_bttn_press = bttn_queue_pop() # get current bttn press
            cur_time = datetime.now()
            hr = int(cur_time.hour % 12)
            if hr == 0: hr = 12
            pm = True if cur_time.hour >= 12 else False

            updt_display(hr, cur_time.minute, pm)

            if (alarm_on == True and int(hr) == int(alarm_hour) and int(cur_time.minute) == int(alarm_minute) and pm == alarm_pm):
                mode = ClockMode.SIMON
                simon_begin_evt.set()
                print("started simon game")
        elif (mode == ClockMode.ALARM):
            set_alarm(cur_bttn_press)
        elif (mode == ClockMode.SIMON):
            cur_time = datetime.now()
            hr = int(cur_time.hour % 12)
            if hr == 0: hr = 12
            pm = True if cur_time.hour >= 12 else False

            updt_display(hr, cur_time.minute, pm)

            if (not simon_begin_evt.is_set() and int(cur_time.minute) != int(alarm_minute)):
                mode = ClockMode.CLOCK

def bttn_main():
    print("bttn_main started")
    GPIO.setmode(GPIO.BCM)

    for pin in [BTTN_0,BTTN_1,BTTN_2,BTTN_3]:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.FALLING, callback=bttn_callbk, bouncetime=100)

    while(not exit_evt.is_set()):
        if (bttn_evt.is_set()):
            bttn_q.put(cur_bttn)
            bttn_evt.clear()

def buzzer_main():
    print("buzzer_main started")
    GPIO.setup(18, GPIO.OUT)
    p = GPIO.PWM(18, 3000)
    while(True):
        time.sleep(1)
        p.start(50)
        time.sleep(1)
        p.stop()

clk_thread = threading.Thread(target=clk_main)
bttn_thread = threading.Thread(target=bttn_main)
simon_thread = threading.Thread(target=simon_main)

clk_thread.start()
bttn_thread.start()
simon_thread.start()

#bzzr_thread = threading.Thread(target=buzzer_main)
#bzzr_thread.start()
