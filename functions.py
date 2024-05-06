import zlib
import screeninfo
from header import Header
from constants import DATA_HEADER_LENGTH, RECIPIENT_HEADER_LENGTH, HEADER_LENGTH
from datetime import datetime
from icecream import ic


def get_resolution_of_primary_monitor():
    for m in screeninfo.get_monitors():
        if m.is_primary:
            return m.width,m.height

# Given a socket and a constant length, receive exactly length bytes from that socket and return them.
# Used always, recv() is only used for receiving initial headers.
# The point is to make sure no data gets lost because of data being bigger than the maximum recv() limit.
def recvall(sock, length) -> bytes:
    buffer = b''
    while len(buffer) < length: # Since we keep adding to buffer, we will continue if it hasn't surpassed the desired length
        data = sock.recv(length - len(buffer))
        if not data:
            raise Exception("Error occured while trying to receive data")
        buffer += data
    return buffer

# Takes care of attaching a header and compressing the data
def create_sendable_data(data: bytes, recipient_code: str):
    data = zlib.compress(data, zlib.Z_DEFAULT_COMPRESSION)
    data_header = Header(len(data), recipient_code)
    return data_header.get_header_bytes() + data

def parse_header(header: bytes) -> tuple:
    header = header.decode('utf-8')
    data_length = int(header[:DATA_HEADER_LENGTH])
    recipient_code = header[DATA_HEADER_LENGTH:HEADER_LENGTH]
    return data_length, recipient_code


# Takes care of decompressing and decoding the data
def parse_raw_data(data: bytes) -> str:
    return zlib.decompress(data).decode('utf-8', 'ignore')

def get_hhmmss():
    return str(datetime.now().time()).split('.')[0]
