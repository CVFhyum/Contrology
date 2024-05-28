import threading as thr
from time import sleep as sl

def foo():
    print("hello")
    sl(5)
    event.set()

event = thr.Event()
thread = thr.Thread(target=foo)
thread.start()

event.wait()
print("hi")