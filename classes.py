import tkinter as tk
from PIL import Image, ImageTk, ImageSequence

class FlagObject:
    def __init__(self, flag):
        self.flag = flag

    def true(self):
        self.flag = True

    def false(self):
        self.flag = False

    def __bool__(self):
        return self.flag

    def __repr__(self):
        return f"{self.flag}"

# Label that breaks down a gif into multiple images and displays them, seeming like a gif.
class AnimatedGIF(tk.Label):
    def __init__(self, parent, path, size=None, *args, **kwargs):
        super().__init__(parent,*args,**kwargs)
        self.parent = parent
        self.path = path
        self.size = size
        self.frames = self.load_frames()
        self.current_frame = 0
        self._job = None
        self.update_animation()

    def load_frames(self):
        frames = []
        gif = Image.open(self.path)
        for frame in ImageSequence.Iterator(gif):
            if self.size is not None:
                frame = frame.resize(self.size, Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(frame))
        return frames

    def update_animation(self):
        self.configure(image=self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self._job = self.after(100, self.update_animation)

    def destroy(self):
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        super().destroy()