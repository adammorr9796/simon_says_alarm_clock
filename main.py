import threading
import time
import display
from datetime import datetime
import queue
import RPi.GPIO as GPIO

exit_evt = threading.Event()
exit_evt.clear()

bttn_0_evt = threading.Event()
bttn_1_evt = threading.Event()
bttn_2_evt = threading.Event()
bttn_3_evt = threading.Event()

bttn_0_evt.clear()
bttn_1_evt.clear()
bttn_2_evt.clear()
bttn_3_evt.clear()

clk_face = display.Display(0x70, 1)
clk_face.setup()
clk_face.write_colon(True)

cur_time = datetime.now()
bttn_q = queue.Queue(10)

BTTN_0 = 0
BTTN_1 = 1
BTTN_2 = 2
BTTN_3 = 3

def bttn_callbk_0(channel):
    bttn_0_evt.set()

def bttn_callbk_1(channel):
    bttn_1_evt.set()

def bttn_callbk_2(channel):
    bttn_2_evt.set()

def bttn_callbk_3(channel):
    bttn_3_evt.set()

def clk_main():
    print("clk_main started")

    while(not exit_evt.is_set()):
        cur_time = datetime.now()

        pm = True if cur_time.hour >= 12 else False

        hour = int(cur_time.hour % 12)
        minute = cur_time.minute

        if hour == 0: hour = 12

        if (hour < 10):
            clk_face.write_digit(0, 0, False)
            clk_face.write_digit(1, hour, False)
        else:
            clk_face.write_digit(0, 1, False)
            clk_face.write_digit(1, hour % 10, False)

        clk_face.write_digit(2, int(minute / 10), False)
        clk_face.write_digit(3, int(minute % 10), pm)

def bttn_main():
    print("bttn_main started")
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.add_event_detect(10, GPIO.RISING, callback=bttn_callbk_0, bouncetime=100)
    GPIO.add_event_detect(22, GPIO.RISING, callback=bttn_callbk_1, bouncetime=100)
    GPIO.add_event_detect(27, GPIO.RISING, callback=bttn_callbk_2, bouncetime=100)
    GPIO.add_event_detect(17, GPIO.RISING, callback=bttn_callbk_3, bouncetime=100)

    while(not exit_evt.is_set()):
        if (bttn_0_evt.is_set()):
            bttn_q.put(BTTN_0)
            bttn_0_evt.clear()

        if (bttn_1_evt.is_set()):
            bttn_q.put(BTTN_1)
            bttn_1_evt.clear()

        if (bttn_2_evt.is_set()):
            bttn_q.put(BTTN_2)
            bttn_2_evt.clear()

        if (bttn_3_evt.is_set()):
            bttn_q.put(BTTN_3)
            bttn_3_evt.clear()

clk_thread = threading.Thread(target=clk_main)
bttn_thread = threading.Thread(target=bttn_main)

clk_thread.start()
bttn_thread.start()
