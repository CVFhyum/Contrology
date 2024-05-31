import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
from functions import get_resized_image

class AnimatedGIF(tk.Label):
    def __init__(self, master, path, size=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.path = path
        self.size = size
        self.frames = self.load_frames()
        self.current_frame = 0
        self.update_animation()

    def load_frames(self):
        frames = []
        gif = Image.open(self.path)
        for frame in ImageSequence.Iterator(gif):
            if self.size:
                frame = frame.resize(self.size, Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(frame))
        return frames

    def update_animation(self):
        self.configure(image=self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.after(100, self.update_animation)

root = tk.Tk()
animated_gif = AnimatedGIF(root, "C:\\Users\cvfhy\PycharmProjects\\finalproj\\assets\loading.gif", size=(10, 10))
animated_gif.pack()
root.mainloop()
