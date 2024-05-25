from socket import socket
from threading import Thread
from zlib import compress

from mss.windows import MSS as mss


WIDTH = 1920
HEIGHT = 1080


def retreive_screenshot(conn):
    with mss() as sct:
        # The region to capture

        while 'recording':
            # Capture the screen
            print(sct.monitors)
            img = sct.grab(sct.monitors[3])
            # Tweak the compression level here (0-9)
            pixels = compress(img.rgb, 6)

            # Send the size of the pixels length
            size = len(pixels)
            size_len = (size.bit_length() + 7) // 8
            conn.send(bytes([size_len]))

            # Send the actual pixels length
            size_bytes = size.to_bytes(size_len, 'big')
            conn.send(size_bytes)

            # Send pixels
            conn.sendall(pixels)


def main(host='localhost', port=5001):
    sock = socket()
    sock.bind((host, port))
    try:
        sock.listen(5)
        print('Server started.')

        while 'connected':
            conn, addr = sock.accept()
            print('Client connected IP:', addr)
            thread = Thread(target=retreive_screenshot, args=(conn,))
            thread.start()
    finally:
        sock.close()


if __name__ == '__main__':
    main()