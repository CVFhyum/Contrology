import socket
import threading as thr
import zlib
from time import perf_counter
from icecream import ic
from mss.windows import MSS as mss
import screeninfo
import select
import random as r
from datetime import datetime
import ssl

# Mine
from configuration import *
from functions import *
from constants import *
from message_handler import MessageHandler
from sql_handler import SQLHandler

# When a socket raises an error, it should be immediately closed gracefully.
# This function removes it from clients, client_ids, and closes it.
def handle_sock_closing(closing_sock: socket.socket):
    clients.remove(closing_sock)
    for code, sock in client_ids.items():
        if sock is closing_sock:
            print(f"[{get_hhmmss()}] Client Disconnected {closing_sock.getsockname()} | {code}")
            del client_ids[code]
            break
    closing_sock.close()

# When the server detects data incoming from an existing socket, this function is called.
# This function listens out for headers, and uses those to listen to data that is later resent.
def handle_client(sock: socket.socket):
    try:
        header = sock.recv(HEADER_LENGTH)  # Receive the header
        data_length, data_type, code = parse_header(header)  # Parse the header
        data = recvall(sock,data_length)  # Receive all the data
        data = parse_raw_data(data)  # Parse the data
        ic(len(data), data_length)
        ic(data_type, code)
        # TODO: handle messages that are meant for the server

        # TODO: rethink way of handling request packets and sending a not_found packet back.
        # TODO: maybe make message handler read the code from the header and then it wont need to be a dictionary
        # TODO: maybe make a function to handle different data types and what we need to do with them
        if data_type == "CONNECT_REQUEST":
            if code not in list(client_ids.keys()):
                code = list(client_ids.keys())[list(client_ids.values()).index(sock)] # get code from socket object
                data = create_sendable_data(b"", "CONNECT_NOT_FOUND", code)
        else:
            data = data.encode('utf-8')  # Encode the data
            data = create_sendable_data(data, data_type, code) # Wrap the data so it's ready to be resent
        m_handler.update(code, data)
    except Exception as e:
        print(f"Error handling socket: {e}") # todo: remove this
        handle_sock_closing(sock)

# Create handlers
m_handler = MessageHandler()
db_handler = SQLHandler("contrology.db")

clients = []  # List of all client socket objects
client_ids = {}  # alphanumeric id: client socket


def main():
    screen_width, screen_height = get_resolution_of_primary_monitor()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server = ssl.wrap_socket(server, ssl_version=ssl.PROTOCOL_TLSv1_2)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2**30) # Make send buffer 2^30 bytes long

    print(f"Server started on IP {SERVER_IP} and port {SERVER_PORT}")
    server.bind((SERVER_IP,SERVER_PORT))
    server.listen(5)

    try:
        while True:
            rlist, wlist, xlist = select.select([server] + clients,[],[])
            for sock in rlist:
                if sock is server:  # New connection pending
                    client, addr = server.accept()  # Accept the connection
                    if db_handler.is_value_in("addresses", "address", addr[0]):  # Check if the address has connected before and has a record in the database
                        new_code = db_handler.get_code_for_address(addr[0])
                    else:  # If they are new, give them a new code and add them to the database
                        new_code = generate_alphanumeric_code(client_ids)
                        db_handler.insert_address_and_code(addr[0], new_code)
                    m_handler.update(new_code,create_sendable_data(b"","INITIAL_ACCEPT", new_code))
                    client_ids.update({new_code: client})  # Add socket:code to dictionary
                    clients.append(client)
                    print(f"[{get_hhmmss()}] New Client Connected {addr} | {new_code}")

                else:  # Incoming data from existing client, so handle them
                    handle_client(sock)
            # End
            m_handler.send_all(client_ids)
    except KeyboardInterrupt:
        print("Server interrupted...")
    finally:
        for client in clients:
            client.close()
        server.close()
        db_handler.disconnect()

if __name__ == "__main__":
    main()
