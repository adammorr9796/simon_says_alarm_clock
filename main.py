import threading
import time
import display
from datetime import datetime

exit_evt = threading.Event()
exit_evt.clear()

clk_face = display.Display(0x70, 1)
clk_face.setup()
clk_face.write_colon(True)

cur_time = datetime.now()

def clk_main():
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

clk_thread = threading.Thread(target=clk_main)
clk_thread.start()
