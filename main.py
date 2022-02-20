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

        if (cur_time.hour%12 < 10):
            clk_face.write_digit(0, 0)
            clk_face.write_digit(1, int(cur_time.hour%12))
        else:
            clk_face.write_digit(0, 1)
            clk_face.write_digit(1, int((cur_time.hour%12)%10))

        if (cur_time.minute < 10):
            clk_face.write_digit(2, 0)
            clk_face.write_digit(3, int(cur_time.minute))
        else:
            clk_face.write_digit(2, int(cur_time.minute/10))
            clk_face.write_digit(3, int(cur_time.minute%10))

clk_thread = threading.Thread(target=clk_main)
clk_thread.start()
