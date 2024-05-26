import socket

# Implementation of the DataHandler class.
# This class has one object during runtime which allows communication between the thread handling the client and other GUI callbacks/widgets.

class DataHandler:
    def __init__(self):
        # Incoming data queue -> Tuples of data -> (data type, data)
        # Outgoing data queue -> Ready data (with headers)
        self.incoming_data_queue: list = []
        self.outgoing_data_queue: list = []

    def insert_new_incoming_message(self, data):
        self.incoming_data_queue.append(data)

    def insert_new_outgoing_message(self, data):
        self.outgoing_data_queue.append(data)

    def get_most_recent_message(self):
        if len(self.incoming_data_queue) == 0:
            raise Exception("No incoming messages are in the queue.")
        return self.incoming_data_queue.pop(0)

    def send_all_outgoing_data(self, sock: socket.socket):
        for outgoing_data in self.outgoing_data_queue:
            try:
                sock.sendall(outgoing_data)
            except Exception as e:
                print(f"Error sending data to socket: {e}")  # todo: remove this and handle the socket closing properly

