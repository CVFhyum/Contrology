import tkinter as tk

class Frame(tk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        self.grid(row=0,column=0) # change
        self.configure(width=parent.width,height=parent.height) # change
        self.configure(highlightthickness=1,highlightbackground='green')  # debug view

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        pass

    def dimensions(self):
        pass