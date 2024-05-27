import socket
from functions import *
from constants import *
from configuration import *


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
    c.connect((SERVER_IP, SERVER_PORT))
    data_length,connection_status,self_code = parse_header(c.recv(HEADER_LENGTH))
    if data_length > 0:
        raise Exception("Extra data was sent on initialisation")
    if connection_status == "INITIAL_ACCEPT":
        ic(self_code)
        while True:
            try:
                header = c.recv(HEADER_LENGTH)
                ic(header)
                if header:  # if header is not empty
                    data_length, data_type, code = parse_header(header)
                    data = parse_raw_data(recvall(c, data_length))
                    if code == self_code or code == ALL_CODE:
                        if len(data) < 100:
                            print(data)
                        else:
                            print(len(data), data_length)
                    else:
                        raise Exception(f"Intended code {code} didn't match with self code {self_code} or ALL_CODE {ALL_CODE}")
                else: # header is empty
                    break
            except ConnectionResetError as e:
                print(f"Something went wrong with the connection: {e}")
            except KeyboardInterrupt:
                print("Client interrupted...")
                c.close()
                break
