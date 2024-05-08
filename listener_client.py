import socket
from functions import *
from constants import *
from configuration import *


with socket.socket() as c:
    c.connect((SERVER_IP, SERVER_PORT))
    my_code = c.recv(RECIPIENT_HEADER_LENGTH).decode()
    print(my_code)
    while True:
        try:
            header = c.recv(HEADER_LENGTH)
            ic(header)
            if header:  # if header is not empty
                data_length, code = parse_header(header)
                data = parse_raw_data(recvall(c, data_length))
                if code == my_code or code == ALL_CODE:
                    if len(data) < 100:
                        print(data)
                    else:
                        print(len(data), data_length)
                else:
                    raise Exception("Intended code didn't match with self code")
            else: # header is empty
                break
        except ConnectionResetError as e:
            print(f"Something went wrong with the connection: {e}")
        except KeyboardInterrupt:
            print("Client interrupted...")
            c.close()
            break
