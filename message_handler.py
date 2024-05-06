from typing import Dict
from constants import *
from icecream import ic

class MessageHandler:

    def __init__(self):
        # message_queue is a dictionary
        # {client_code: data_to_send}
        self.message_queue: Dict[str, bytes] = {}

    # Update the dictionary with a new code:data pair to send at the end of the server loop.
    def update(self, client_code: str, ready_data_to_send: bytes):
        if len(client_code) != 10: raise Exception(f"Client code {client_code} passed to MessageHandler is not 10 characters long")
        if not isinstance(ready_data_to_send, bytes): raise Exception("Data passed to MessageHandler is not bytes")
        # Check if the arg is a string
        if isinstance(client_code, str):
            self.message_queue.update({client_code: ready_data_to_send})
        # Check if the arg is a list (to allow data to be sent to multiple clients), and if so make sure it's only strings
        if isinstance(client_code, list) and all(isinstance(item, str) for item in client_code):
            for code in client_code:
                self.message_queue.update({code: ready_data_to_send})

    # Unpack the codes and data from message_queue, receive the id:socket dictionary and dish it all out!
    def send_all(self, client_ids):
        for client_code, data_to_send in list(self.message_queue.items()): # Unpack values from message_queue
            ic(client_code)

            if client_code == ALL_CODE:
                for client in client_ids.values():
                    client.sendall(data_to_send)
                    ic(f"just sent all some data")
            elif client_code == SERVER_CODE:
                raise Exception("Message with recipient as server had a sent attempt - this message was not received properly by the server")
            else:
                client_ids[client_code].sendall(data_to_send)
                ic(f"just sent {client_code} some data")
        self.message_queue = {}


