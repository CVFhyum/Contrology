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

# Mine
from configuration import *
from functions import *
from constants import *
from header import Header
from message_handler import MessageHandler

def generate_alphanumeric_code(existing_client_ids: dict):
    code = "".join([r.choice(ALPHANUMERIC_CHARACTERS) for x in range(10)])  # Make new code
    while code in existing_client_ids.keys() or code == SERVER_CODE or code == ALL_CODE:  # Check code doesn't exist, if it does make another one
        code = "".join([r.choice(ALPHANUMERIC_CHARACTERS) for x in range(10)])
    return code


SCREEN_WIDTH, SCREEN_HEIGHT = get_resolution_of_primary_monitor()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2**30)
    m_handler = MessageHandler()
    clients = []  # list of all client socket objects
    client_ids = {}  # alphanumeric id: client_socket

    print(f"Server started on IP {SERVER_IP} and port {SERVER_PORT}")
    server.bind((SERVER_IP,SERVER_PORT))
    server.listen(5)

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
                print(f"[{TIME}] New Client Connected {addr} | Assigned code {new_code}")
                client.send(new_code.encode('utf-8'))  # Send the client their code
            else:  # Start receiving headers
                header = sock.recv(HEADER_LENGTH) # buggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg
                data_length, recipient_code = parse_header(header)
                data = recvall(sock, data_length)
                ic(data_length, recipient_code)
                data = parse_raw_data(data)
                data = data.encode('utf-8')
                data = create_sendable_data(data, recipient_code)
                m_handler.update(recipient_code, data)

        # End
        m_handler.send_all(client_ids)
