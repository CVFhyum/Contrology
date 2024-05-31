import tkinter as tk
from tkinter import ttk
import random
from icecream import ic


class ScrollableCanvas(tk.Canvas):
    def __init__(self,parent):
        super().__init__(parent)
        self.parent = parent
        self.scrollable_frame = tk.Frame(self, highlightthickness=1, highlightbackground='red')

        self.create_window((0,0),window=self.scrollable_frame,anchor="nw")
        self.scrollable_frame.bind("<Configure>",self.on_frame_configure)

        self.scrollbar = ttk.Scrollbar(parent,orient="vertical",command=self.yview)
        self.configure(yscrollcommand=self.scrollbar.set)

        self.grid(row=0,column=0,sticky="nsew")
        self.scrollbar.grid(row=0,column=1,sticky="ns")

        # Bind mouse wheel events
        self.bind_all("<MouseWheel>",self.on_mouse_wheel)  # Windows
        self.bind_all("<Button-4>",self.on_mouse_wheel)  # Linux
        self.bind_all("<Button-5>",self.on_mouse_wheel)  # Linux

    def on_frame_configure(self,event):
        ic(self.bbox("all"))
        self.configure(scrollregion=self.bbox("all"))

    def on_mouse_wheel(self,event):
        # For Windows and macOS
        ic(event.delta)
        if event.delta:
            self.yview_scroll(int(-1 * (event.delta / 120)),"units")
        # For Linux (event.num is used instead of event.delta)
        elif event.num == 4:
            self.yview_scroll(-1,"units")
        elif event.num == 5:
            self.yview_scroll(1,"units")

    def dim(self, event):
        print(self.scrollable_frame.winfo_width(), self.scrollable_frame.winfo_height())

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Scrollable Canvas with Frames")
        self.geometry("400x400")

        # Configure grid layout
        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0,weight=1)

        self.scrollable_canvas = ScrollableCanvas(self)
        self.frames = []

        self.bind("<KeyPress-s>", self.scrollable_canvas.dim)
        self.bind("<KeyPress-a>", self.add_frame)

    def add_frame(self,event=None):
        frame = tk.Frame(self.scrollable_canvas.scrollable_frame)
        random_number = random.randint(1,100)
        label = ttk.Label(frame,text=f"Random Number: {random_number}")
        label.grid(row=0,column=0)

        button = ttk.Button(frame,text="Click Me",command=lambda f=frame: self.remove_frame(f))
        button.grid(row=0,column=1)

        frame.grid(row=len(self.frames),column=0,sticky="ew",pady=5)
        self.frames.append(frame)

        self.scrollable_canvas.on_frame_configure(None)

    def remove_frame(self,frame):
        frame.grid_forget()
        self.frames.remove(frame)
        self.update_frames()

    def update_frames(self):
        for i,frame in enumerate(self.frames):
            frame.grid(row=i,column=0,sticky="ew")
        self.scrollable_canvas.on_frame_configure(None)


if __name__ == "__main__":
    app = Application()
    app.mainloop()