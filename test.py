import threading as thr

def foo(name):
    print(f"hi {name}")

thread = thr.Thread(target=foo)
thread.__init__(target=foo, args=("hello",))

thread.start()