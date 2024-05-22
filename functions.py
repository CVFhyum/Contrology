import zlib
import screeninfo
from header import Header
from constants import *
from datetime import datetime
from icecream import ic
import random as r
from PIL import Image, ImageTk

# With a given window width and height, get geometry string with offsets to place it in the middle of the screen.
def get_geometry_string(window_width, window_height):
    screen_width, screen_height = get_resolution_of_primary_monitor()
    x_offset, y_offset = int((screen_width-window_width)/2), int((screen_height-window_height)/2)
    return f"{window_width}x{window_height}+{x_offset}+{y_offset}"

# Get resolution of monitor that is marked as primary by the OS.
def get_resolution_of_primary_monitor():
    for m in screeninfo.get_monitors():
        if m.is_primary:
            return m.width,m.height

# Given a socket and a constant length, receive exactly length bytes from that socket and return them.
# Used always, recv() is only used for receiving initial headers.
# The point is to make sure no data gets lost because of data being bigger than the maximum recv() limit.
def recvall(sock, length) -> bytes:
    buffer = b''
    while len(buffer) < length: # Since we keep adding to buffer, we will continue if it hasn't surpassed the desired length
        data = sock.recv(length - len(buffer))
        if not data: # Client disconnected during data receipt?
            raise Exception("Error occurred while trying to receive data")
        buffer += data
    return buffer

# Takes care of attaching a header and compressing the data
def create_sendable_data(data: bytes, data_type: str, recipient_code: str):
    data = zlib.compress(data, zlib.Z_DEFAULT_COMPRESSION)
    data_header = Header(len(data), data_type, recipient_code)
    return data_header.get_header_bytes() + data

# Given a header, parse it into its components (data length, recipient code) and return them.
def parse_header(header: bytes) -> tuple[int, str, str]:
    header = header.decode('utf-8')
    data_length = int(header[:DATA_HEADER_LENGTH])
    data_type = header[DATA_HEADER_LENGTH:DATA_TYPE_LENGTH].strip()
    recipient_code = header[DATA_TYPE_LENGTH:HEADER_LENGTH]
    return data_length, data_type, recipient_code


# Takes care of decompressing and decoding the data
def parse_raw_data(data: bytes) -> str:
    return zlib.decompress(data).decode('utf-8', 'ignore')

# Get the time in the form of HH:MM:SS (Example: 14:37:06)
def get_hhmmss():
    return str(datetime.now().time()).split('.')[0]

# Generate a 10 character alphanumeric code for every client that connects to the server
# This code is used for identifying clients.
def generate_alphanumeric_code(existing_client_ids: dict):
    code = "".join([r.choice(ALPHANUMERIC_CHARACTERS) for x in range(RECIPIENT_HEADER_LENGTH)])  # Make new code
    while code in existing_client_ids.keys() or code == SERVER_CODE or code == ALL_CODE:  # Check code doesn't exist, if it does make another one
        code = "".join([r.choice(ALPHANUMERIC_CHARACTERS) for x in range(RECIPIENT_HEADER_LENGTH)])
    return code

def get_resized_image(image_path, size):
    img = Image.open(image_path)
    if size >= 1:
        new_width, new_height = size[0], size[1]
    else:
        new_width, new_height = int(img.width * size), int(img.height * size)
    return ImageTk.PhotoImage(img.resize((new_width, new_height)), Image.Resampling.LANCZOS)