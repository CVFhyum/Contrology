from typing import Dict
from constants import ALL_CODE, SERVER_CODE, RECIPIENT_CODE_LENGTH
from functions import parse_header_from_data
from sql_handler import SQLHandler
from bidirectional_dict import BidirectionalDict
from icecream import ic
import socket


class MessageHandler:
    def __init__(self, db_handler):
        # message_queue is a dictionary
        # {client_code: data_to_send}
        self.message_queue: list[bytes] = []
        self.db_handler: SQLHandler = db_handler

    # Update the dictionary with a new code:data pair to send at the end of the server loop.
    def add(self, ready_data_to_send: bytes) -> None:
        if not isinstance(ready_data_to_send, bytes):
            raise Exception("Data passed to MessageHandler is not bytes")
        _, _, client_code = parse_header_from_data(ready_data_to_send)
        if len(client_code) != RECIPIENT_CODE_LENGTH:
            raise Exception(f"Client code {client_code} that MessageHandler parsed is not 10 characters long")
        self.message_queue.append(ready_data_to_send)

    # Unpack the data from message_queue, receive the user_id:socket dictionary and dish it all out!
    def send_all(self, client_ids: BidirectionalDict) -> None:
        for data_to_send in self.message_queue:
            _, _, client_code = parse_header_from_data(data_to_send)
            recipient_info = self.db_handler.get_user_info(code=client_code)
            if client_code == ALL_CODE:
                for client in client_ids:  # Loop over the keys in the bidirectional dictionary
                    if isinstance(client, socket.socket):  # Only try sending data for the sockets
                        try:
                            client.sendall(data_to_send)
                        except Exception as e:
                            print(f"Error sending data to socket: {e}")  # todo: remove this and handle the socket closing properly
            elif client_code == SERVER_CODE:
                raise Exception("Message with recipient as server had a sent attempt - this message was not received properly by the server")
            else:
                try:
                    client_ids[recipient_info["id"]].sendall(data_to_send)
                except Exception as e:
                    print(f"Error sending data to socket: {e}") # todo: remove this and handle the socket closing properly
        self.message_queue = []


