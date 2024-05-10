import base64

from functions import *
from constants import *

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO

# todo: make on_closing function using root.protocol
# banner = ImageTk.PhotoImage(Image.open("assets/Banner.png"))
# banner_trans = ImageTk.PhotoImage(Image.open("assets/Banner_Trans.png"))
# logo = ImageTk.PhotoImage(Image.open("assets/Logo.png"))
# logo32 = ImageTk.PhotoImage(Image.open("assets/Logo32.png"))

def consolas(size):
    return tk.font.Font(family="Consolas",size=size)

class LaunchScreen(tk.Tk):
    # Main setup
    def __init__(self):
        # Simple configuration and variable loading
        super().__init__()
        self.title("Launch - Contrology")
        self.width = 800
        self.height = 800
        self.logo32 = ImageTk.PhotoImage(Image.open("assets/Logo32.png"))

        # Complex configuration
        self.geometry(get_geometry_string(self.width, self.height))
        self.resizable(False, False)
        self.iconphoto(False, self.logo32)

        # Widgets
        self.banner_frame = LaunchScreenBannerFrame(self)

        # Functions
        self.dimensions()

        self.mainloop()

    # Widgets

    def dimensions(self):
        self.columnconfigure(0, weight=1)

# Frames belonging to LaunchScreen
class LaunchScreenBannerFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid(row=0,column=0)
        self.banner_trans = ImageTk.PhotoImage(Image.open("assets/Banner_Trans.png"))
        self.configure(width=parent.width,height=parent.height/2)
        self.configure(highlightthickness=1,highlightbackground='green')  # debug view

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        # Creation
        main_banner = ttk.Label(self,image=self.banner_trans)

        # Placement
        main_banner.grid(row=0,column=0)

    def dimensions(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.grid_propagate(False)
class LaunchScreenButtonsFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid(row=0,column=0)
        self.configure(width=parent.width,height=parent.height / 2)
        self.configure(highlightthickness=1,highlightbackground='green')  # debug view

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        pass

    def dimensions(self):
        pass






app = LaunchScreen()
