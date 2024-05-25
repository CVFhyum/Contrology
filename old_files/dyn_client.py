from socket import socket
from zlib import decompress
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import io
import threading as thr

WIDTH = 400
HEIGHT = 500
current_image = b""
tkinter_image = None
image_lock = thr.Lock()
# if changing or accessing current image, take the lock



def bytes_to_PIL_image(bytes):
    img = Image.open(io.BytesIO(bytes))
    return img

def recvall(conn, length):
    """ Retreive all pixels. """

    buf = b''
    while len(buf) < length:
        data = conn.recv(length - len(buf))
        if not data:
            return data
        buf += data
    return buf

def fetch_image_data(sock):
    global current_image, tkinter_image
    watching = True
    try:
        while watching:
            # Retreive the size of the pixels length, the pixels length and pixels
            size_len = int.from_bytes(sock.recv(1), byteorder='big')
            size = int.from_bytes(sock.recv(size_len), byteorder='big')
            pixels = decompress(recvall(sock, size))
            image_lock.acquire()
            current_image = pixels
            tkinter_image = ImageTk.PhotoImage(Image.open(io.BytesIO(current_image)))
            print("watched")
            image_lock.release()
    except Exception as e:
        print(e)


def update_image_repeatedly(label):
    while True:
        label.config(image=tkinter_image)
        print(tkinter_image)

def main(host='10.168.63.28', port=5000):
    root = Tk()
    root.geometry(f"{WIDTH}x{HEIGHT}")
    base_label = ttk.Label(root)
    base_label.grid(row=0, column=0)
    sock = socket()
    sock.connect((host, port))
    listening_thr = thr.Thread(target=fetch_image_data, args=(sock,), daemon=False)
    listening_thr.start()
    updating_thr = thr.Thread(target=update_image_repeatedly, args=(base_label,), daemon=False)
    updating_thr.start()

    root.mainloop()



if __name__ == '__main__':
    main()