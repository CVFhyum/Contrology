"""
Make attributes here private
"""

import socket
from icecream import ic

# Implementation of the DataHandler class.
# This class has one object during runtime which allows communication between the thread handling the client and other GUI callbacks/widgets.

class DataHandler:
    def __init__(self):
        # Incoming data queue -> Tuples of data -> (data type, data)
        # Outgoing data queue -> Ready data (with headers)
        self.incoming_data_queue: list = []
        self.outgoing_data_queue: list = []
        self._last_image_received = None

    # Insert data as a tuple (data type, data)
    def insert_new_incoming_message(self, data: tuple[str, str]):
        self.incoming_data_queue.append(data)

    # Insert data as "ready data" (with a header)
    def insert_new_outgoing_message(self, data: bytes):
        # todo: add a function in functions.py called has_header to make sure data has a header here
        self.outgoing_data_queue.append(data)

    def set_last_image(self, image: bytes):
        self._last_image_received = image

    def get_last_image(self):
        return self._last_image_received


    def send_all_outgoing_data(self, sock: socket.socket):
        for outgoing_data in self.outgoing_data_queue:
            try:
                sock.sendall(outgoing_data)
            except Exception as e:
                print(f"Error sending data to socket: {e}")  # todo: remove this and handle the socket closing properly
        self.outgoing_data_queue = []

