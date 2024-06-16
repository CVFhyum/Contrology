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
import pickle

# Mine
from configuration import *
from functions import *
from constants import *
from message_handler import MessageHandler
from sql_handler import SQLHandler
from bidirectional_dict import BidirectionalDict

# When a socket raises an error, it should be immediately closed gracefully.
# This function removes it from clients, client_ids, and closes it.
def handle_sock_closing(closing_sock: socket.socket):
    user_id = new_client_ids[closing_sock]
    user_info = db_handler.get_user_info(user_id=user_id)
    user_address = user_info["address"]
    db_handler.set_user_connection_status(user_id, False)
    print(f"[{get_hhmmss()}] Client Disconnected | {get_bare_hostname(user_address)} | {user_address} | {user_info['code']}")
    db_handler.log(user_id=user_info["id"],user_hostname=user_info["hostname"],action="DISCONNECTION")
    del new_client_ids[user_id]
    clients.remove(closing_sock)
    closing_sock.close()

# When the server detects data incoming from an existing socket, this function is called.
# This function listens out for headers, and uses those to listen to data that is later resent.
def handle_client(sock: socket.socket):
    try:
        header = sock.recv(HEADER_LENGTH)  # Receive the header
        data_length, data_type, code = parse_header(header)  # Parse the header
        data = recvall(sock,data_length)  # Receive all the data
        if data_type in PICKLED_DATA_TYPES:
            data = parse_raw_data(data, pickled=True)  # Parse the data
        elif data_type == "IMAGE":
            data = parse_raw_data(data, image=True)
        else:
            data = parse_raw_data(data)
        ic(len(data), data_length)
        ic(data_type, code)
        # TODO: handle messages that are meant for the server
        # TODO: maybe make a function to handle different data types and what we need to do with them
        sender_info = db_handler.get_user_info(user_id=new_client_ids[sock])
        target_info = db_handler.get_user_info(code=code)
        if (not db_handler.code_exists(code)) and code not in (ALL_CODE, SERVER_CODE):
            data = create_sendable_data(b"", "CODE_NOT_FOUND", sender_info["code"])
            m_handler.add(data)
        else:
            m_handler.add(create_sendable_data(b"", "CODE_FOUND", sender_info["code"]))
            match data_type:
                case "CONNECT_REQUEST":  # Controller --> Remote
                    # The data should be {code}{hostname} (both of the controller so the remote knows)
                    # todo: change this to a UserInfo class ^^^
                    data = f"{sender_info['code']}{get_bare_hostname(sock.getpeername()[0])}"
                    data = data.encode('utf-8')
                    data = create_sendable_data(data, data_type, code)
                    m_handler.add(data)
                    db_handler.log(user_id=sender_info['id'],
                                   user_hostname=sender_info['hostname'],
                                   action="REQUEST",
                                   target_user_id=target_info['id'],
                                   target_user_hostname=target_info['hostname'])
                case "CONNECT_ACCEPT":  # Remote --> Controller
                    data = pickle.dumps(data)
                    data = create_sendable_data(data, data_type, code, pickled=True)
                    m_handler.add(data)
                    db_handler.log(user_id=sender_info['id'],
                                   user_hostname=sender_info['hostname'],
                                   action="ACCEPT_REQUEST",
                                   target_user_id=target_info['id'],
                                   target_user_hostname=target_info['hostname'])
                case "CONNECT_DENY":  # Remote --> Controller
                    data = data.encode('utf-8')  # Encode the data
                    data = create_sendable_data(data,data_type,code)  # Wrap the data so it's ready to be resent
                    m_handler.add(data)
                    db_handler.log(user_id=sender_info['id'],
                                   user_hostname=sender_info['hostname'],
                                   action="DENY_REQUEST",
                                   target_user_id=target_info['id'],
                                   target_user_hostname=target_info['hostname'])
                case "IMAGE":
                    data = create_sendable_data(data, data_type, code)
                    m_handler.add(data)
                case "CONTROL_EVENT":
                    data = pickle.dumps(data)
                    data = create_sendable_data(data, data_type, code, pickled=True)
                    m_handler.add(data)
                case "DB_LOGS_REQUEST":
                    for chunk_of_rows in db_handler.get_all_logs():
                        pickled_chunk = pickle.dumps(chunk_of_rows)
                        m_handler.add(create_sendable_data(pickled_chunk, "DB_LOGS", sender_info["code"], pickled=True))
                case "DB_USERS_REQUEST":
                    # todo: implement
                    pass
                case _:
                    data = data.encode('utf-8')  # Encode the data
                    data = create_sendable_data(data, data_type, code) # Wrap the data so it's ready to be resent
                    m_handler.add(data)
    except Exception as e:
        print(f"Error handling socket: {e}") # todo: remove this
        handle_sock_closing(sock)

# Create handlers
db_handler = SQLHandler("contrology.db")
m_handler = MessageHandler(db_handler)


clients = []  # List of all client socket objects
client_ids = {}  # alphanumeric code: client socket
new_client_ids = BidirectionalDict() # user id: client socket


def main():
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
                    # Get the user info
                    user_info = db_handler.get_user_info(ip_addr=addr[0])
                    if user_info is not None:  # Check if the user exists
                        new_code = user_info["code"]
                        db_handler.set_user_connection_status(user_info["id"], True)
                    # If the user is new, give them a new code and add them to the database
                    else:
                        new_code = generate_code(db_handler)
                        user_id = db_handler.add_user(hostname=get_bare_hostname(addr[0]), address=addr[0], code=new_code, is_connected=True)
                        user_info = db_handler.get_user_info(user_id=user_id)
                    new_client_ids[user_info["id"]] = client
                    db_handler.log(user_id=user_info["id"],
                                   user_hostname=user_info["hostname"],
                                   action="CONNECTION")
                    m_handler.add(create_sendable_data(b"", "INITIAL_ACCEPT", new_code))  # Send client initialisation packet
                    clients.append(client)
                    print(f"[{get_hhmmss()}] Client Connected | {get_bare_hostname(addr[0])} | {addr} | {new_code}")

                else:  # Incoming data from existing client, so handle them
                    handle_client(sock)
            # End
            m_handler.send_all(new_client_ids)
    except KeyboardInterrupt:
        print("Server interrupted...")
    finally:
        for client in clients:
            client.close()
        server.close()
        db_handler.set_all_users_disconnected()
        db_handler.disconnect()

if __name__ == "__main__":
    main()
