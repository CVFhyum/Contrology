import tkinter as tk

root = tk.Tk()

t = tk.Text(root)
t.grid(row=0,column=0)
t.tag_configure("red", foreground="red")
t.insert(tk.END, "hello", "red")


root.mainloop()