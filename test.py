# from functions import *
# from constants import *
# import tkinter as tk
# from tkinter import ttk
# import zlib
#
# import base64
# from io import BytesIO
#
#
# root = tk.Tk()
# width, height = 800, 600
# root.geometry(get_geometry_string(width, height))
# im = ImageTk.PhotoImage(Image.open("assets/banner.png"))
# l = ttk.Label(root, image=im)
# l.grid(row=0,column=0)
#
# root.mainloop()

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class ImageDisplayApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Display")
        self.geometry("800x600")
        self.resizable(False, False)

        # Load the image
        image_path = "assets/banner.png"
        self.image = Image.open(image_path)
        self.photo = ImageTk.PhotoImage(self.image)

        # Create a label to display the image
        self.image_label = ttk.Label(self, image=self.photo)
        self.image_label.pack(pady=10)

if __name__ == "__main__":
    app = ImageDisplayApp()
    app.mainloop()

