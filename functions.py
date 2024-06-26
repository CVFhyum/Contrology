"""
Change all functions here to include docstrings instead of comments.
"""

import tkinter as tk
import zlib
import screeninfo
from header import Header
from constants import *
from datetime import datetime
from icecream import ic
import random as r
from PIL import Image, ImageTk
import socket
from typing import Dict, Union, Optional
from mss.windows import MSS
import threading as thr
import time
import pickle
from sql_handler import SQLHandler
from tkinter import ttk
from remote import Remote
from control_event import ControlEvent

# With a given window width and height, get geometry string with offsets to place it in the middle of the screen.
def get_geometry_string(window_width: int, window_height: int) -> str:
    screen_width, screen_height = get_resolution_of_primary_monitor()
    x_offset = int((screen_width-window_width)/2)
    y_offset = int((screen_height-window_height)/2)
    return f"{window_width}x{window_height}+{x_offset}+{y_offset}"

# Get resolution of monitor that is marked as primary by the OS.
def get_resolution_of_primary_monitor() -> tuple[int,int]:
    for m in screeninfo.get_monitors():
        if m.is_primary:
            return m.width,m.height

# Given a socket and a constant length, receive exactly length bytes from that socket and return them.
# Used always, recv() is only used for receiving initial headers.
# The point is to make sure no data gets lost because of data being bigger than the maximum recv() limit.
def recvall(sock: socket.socket, length: int) -> bytes:
    buffer = b''
    while len(buffer) < length: # Since we keep adding to buffer, we will continue if it hasn't surpassed the desired length
        data = sock.recv(length - len(buffer))
        if not data: # Client disconnected during data receipt?
            raise Exception("Error occurred while trying to receive data")
        buffer += data
    return buffer

# Takes care of attaching a header and compressing the data
def create_sendable_data(data: bytes, data_type: str, recipient_code: str, pickled=False) -> bytes:
    if not pickled:
        if len(data) != 0:
            data = zlib.compress(data, zlib.Z_DEFAULT_COMPRESSION)
    data_header = Header(len(data), data_type, recipient_code)
    return data_header.get_header_bytes() + data

# Given a header, parse it into its components (data length, data type, recipient code) and return them.
def parse_header(header: bytes) -> tuple[int, str, str]:
    header = header.decode('utf-8', 'ignore')
    data_length = int(header[:DATA_LENGTH_LENGTH])
    header = header[DATA_LENGTH_LENGTH:]
    data_type = header[:DATA_TYPE_LENGTH].strip()
    header = header[DATA_TYPE_LENGTH:]
    recipient_code = header[:RECIPIENT_CODE_LENGTH]
    header = header[RECIPIENT_CODE_LENGTH:]
    if len(header) != 0:
        raise Exception(f"Not all of header information was parsed")
    return data_length, data_type, recipient_code


# Takes care of decompressing, depickling, and decoding the data
def parse_raw_data(data: bytes, pickled=False, image=False) -> Union[str, bytes, Remote, ControlEvent]:
    if pickled:
        return pickle.loads(data)
    if len(data) != 0:
        data = zlib.decompress(data)
    if image:
        return data
    return data.decode('utf-8', 'ignore')

# Given a ready piece of data created by create_sendable_data(), return the header components of that data
def parse_header_from_data(data: bytes):
    header = data[:HEADER_LENGTH]
    components = parse_header(header)
    return components

# Get the time in the form of HH:MM:SS (Example: 14:37:06)
def get_hhmmss():
    return str(datetime.now().time()).split('.')[0]

# Generate a 10-digit code for every client that connects to the server
# This code is used for identifying clients.
def generate_code(db_handler: SQLHandler) -> str:
    while True:
        new_code = ''.join(r.choice(CODE_CHARACTER_POOL) for _ in range(RECIPIENT_CODE_LENGTH))  # Adjust length as needed
        if not db_handler.code_exists(new_code):
            return new_code

def get_resized_image(image_path: str, size: Union[tuple[int,int], int]) -> ImageTk.PhotoImage:
    img = Image.open(image_path)
    if size >= 1:
        new_width, new_height = size[0], size[1]
    else:
        new_width, new_height = int(img.width * size), int(img.height * size)
    return ImageTk.PhotoImage(img.resize((new_width, new_height)), Image.Resampling.LANCZOS)

# Performs a reverse DNS lookup to get the hostname of a socket. Truncates the hostname by removing DNS suffixes.
def get_bare_hostname(ip_addr: str) -> str:
    try:
        # Perform a reverse DNS lookup to get the hostname
        hostname = socket.gethostbyaddr(ip_addr)[0]
        # Split the hostname by '.' and take the first part (bare hostname)
        bare_hostname = hostname.split('.')[0]
        return bare_hostname
    except socket.herror as e:
        # Handle the case where the hostname could not be resolved
        print(f"Error resolving hostname: {e}")
        return None

def get_screenshot_bytes(mss_object: MSS, top, left, width, height):
    rect = {'top': top,'left': left,'width': width,'height': height}
    screenshot = mss_object.grab(rect)
    screenshot_bytes = screenshot.rgb
    return screenshot_bytes

# This function takes a StringVar, changes it to new_text, then waits wait_seconds, before changing it back to old_text.
# todo: use .after instead of this
def set_temporary_message(var: tk.StringVar, old_text: str, new_text: str, wait_seconds: float):
    if thr.current_thread() is thr.main_thread():
        thr.Thread(target=set_temporary_message, args=(var, new_text, wait_seconds, old_text)).start()
    else:
        var.set(new_text)
        time.sleep(wait_seconds)
        var.set(old_text)

def bind_to_hierarchy(widget: tk.BaseWidget, binding, callback):
    widget.bind(binding, callback)
    children = widget.winfo_children()
    for child in children:
        bind_to_hierarchy(child, binding, callback)

# Generates a tkinter-formatted consolas font at a desired size. Made for code readability.
def consolas(size: int):
    return "Consolas", size

# https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/ttk-style-layer.html
# Makes a style that has the consolas font for a specific widget at a desired size
# Returns the string of the style name
def apply_consolas_to_widget(widget_type: str, size: int, colour: Optional[str] = None) -> str:
    s = ttk.Style()
    style_string = f'{size}{colour}.T{widget_type}'
    s.configure(style_string, font=consolas(size))
    if colour is not None:
        s.configure(style_string, foreground=colour)
    return style_string

# This function transposes a matrix (switches between the rows and the columns
# zip(*matrix) passes all the 1d lists into zip, making a tuple of the first elements, the second elements, etc.
# map(list, zip(*matrix)) converts all these new tuples into lists (by mapping the function list on every iterable)
# list(...) converts the iterator made by map into a list, effectively creating a 2d list
def transpose(matrix):
    return list(map(list, zip(*matrix)))


def map_coords_to_original(scaled_x,scaled_y,scale_factor):
    original_x = int(scaled_x / scale_factor)
    original_y = int(scaled_y / scale_factor)
    return original_x,original_y
