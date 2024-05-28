import socket
import threading as thr
import zlib
import lzma
from time import perf_counter
from icecream import ic
from mss.windows import MSS as mss
import screeninfo

# Mine
from configuration import *
from functions import *
from constants import *


SCREEN_WIDTH, SCREEN_HEIGHT = get_resolution_of_primary_monitor()

# todo: don't hardcode the rect on the first screen.
# use screeninfo to find out the coordinate system and from that make a gui to choose monitors
def send_continuous_screenshots(sock: socket.socket):
    with mss() as sct:
        while True:
            rect = {'top': 0,'left': 0,'width': SCREEN_WIDTH,'height': SCREEN_HEIGHT}
            new_screenshot = sct.grab(rect)
            ss_bytes = new_screenshot.rgb
            ready_data = create_sendable_data(ss_bytes, "IMAGE", ALL_CODE)
            try:
                sock.sendall(ready_data)
            except Exception as e:
                print(f"Something went wrong with the connection: {e}")
                break


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((SERVER_IP, SERVER_PORT))
    data_length, connection_status, self_code = parse_header(client.recv(HEADER_LENGTH))
    if data_length > 0:
        raise Exception(f"Extra data was sent on initialisation")
    if connection_status == "INITIAL_ACCEPT":
        ic(self_code)
        thread = thr.Thread(target=send_continuous_screenshots,args=(client,))
        thread.start()
        while thread.is_alive():
            try:
                pass
            except KeyboardInterrupt:
                print("Client interrupted....")

