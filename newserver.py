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
from header import Header
from message_handler import MessageHandler

# When a socket raises an error, it should be immediately closed gracefully.
# This function removes it from clients, client_ids, and closes it.
def handle_sock_closing(sock: socket.socket):
    clients.remove(sock)
    for code, socket in client_ids.items():
        if socket is sock:
            print(f"[{get_hhmmss()}] Client Disconnected {sock.getsockname()} | {code}")
            del client_ids[code]
            break
    sock.close()

# When the server detects data incoming from an existing socket, this function is called.
# This function listens out for headers, and uses those to listen to data that is later resent.
def handle_client(sock):
    try:
        header = sock.recv(HEADER_LENGTH)  # Receive the header
        data_length,recipient_code = parse_header(header)  # Parse the header
        data = recvall(sock,data_length)  # Receive all the data
        data = parse_raw_data(data)  # Parse the data
        # TODO: handle messages that are meant for the server
        data = data.encode('utf-8')  # Encode the data
        data = create_sendable_data(data,recipient_code) # Wrap the data so it's ready to be resent
        m_handler.update(recipient_code,data)
    except Exception as e:
        print(f"Error handling socket: {e}") # todo: remove this
        handle_sock_closing(sock)

m_handler = MessageHandler()
clients = []  # list of all client socket objects
client_ids = {}  # alphanumeric id: client_socket

def main():
    screen_width, screen_height = get_resolution_of_primary_monitor()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server = ssl.wrap_socket(server, ssl_version=ssl.PROTOCOL_TLSv1_2)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2**30) # Make send buffer 2^30 bytes long

    print(f"Server started on IP {SERVER_IP} and port {SERVER_PORT}")
    server.bind((SERVER_IP,SERVER_PORT))
    server.listen(5)

    try:
        while True:
            TIME = get_hhmmss()  # Returns a time string in the format hh:mm:ss
            rlist, wlist, xlist = select.select([server] + clients,[],[])
            for sock in rlist:
                if sock is server:  # New connection pending
                    # Accept the connection, add the client, assign a code, log their connection, and send them their code
                    client, addr = server.accept()
                    clients.append(client)
                    new_code = generate_alphanumeric_code(client_ids)
                    client_ids.update({new_code: client})
                    print(f"[{TIME}] New Client Connected {addr} | {new_code}")
                    client.send(new_code.encode('utf-8'))  # Send the client their code
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

if __name__ == "__main__":
    main()
