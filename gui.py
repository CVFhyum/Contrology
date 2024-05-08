import base64

from functions import *
from constants import *

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO

def consolas(size):
    return tk.font.Font(family="Consolas",size=size)

class LogInScreen(tk.Tk):
    # Main setup
    def __init__(self):
        super().__init__()
        self.title("Log In - Contrology")
        self.width = 800
        self.height = 800
        self.geometry(get_geometry_string(self.width, self.height))
        self.resizable(False, False)
        icon_photo = ImageTk.PhotoImage(Image.open("assets/Logo32.png"))
        self.iconphoto(False, icon_photo)
        self.banner = ImageTk.PhotoImage(Image.open("assets/Banner.png"))
        self.logo = Image

        self.create_widgets()

        self.mainloop()

    # Widgets
    def create_widgets(self):
        # Creation
        main_banner = ttk.Label(self,image=self.banner, text="Hello",compound='top')



        # Placement
        main_banner.grid(row=0,column=0)

app = LogInScreen()
