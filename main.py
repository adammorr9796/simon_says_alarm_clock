import threading
import time

def callback_0():
	while(not evt.is_set()):
		print("callback 0")
		time.sleep(1)

def callback_1():
	while(not evt.is_set()):
		print("callback 1")
		time.sleep(1)

t0 = threading.Thread(target=callback_0)
t1 = threading.Thread(target=callback_1)

evt = threading.Event()

evt.clear()

t0.start()
t1.start()

for _ in range(3):
	print("main")
	time.sleep(1)

evt.set()

print("Done main")

