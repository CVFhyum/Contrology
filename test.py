import tkinter as tk
from tkinter import ttk
from icecream import ic
import threading as thr
from time import sleep

root = tk.Tk()
root.geometry("1920x1080")
root.attributes('-fullscreen', True)
var = tk.StringVar()

def hi():
    while True:
        var.set(f"{root.winfo_width()}, {root.winfo_height()}")
        sleep(0.05)

b = ttk.Button(root, textvariable=var, command=thr.Thread(target=hi).start)
b.pack()

root.mainloop()