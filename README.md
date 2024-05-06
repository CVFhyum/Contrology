## How do you send data?
Use **create_sendable_data()** and pass the following arguments:
- Data in the form of bytes, with no header
- 10 Character Recipient Code

You will get bytes to send.

## How do you receive data?
Wait for a header of length **HEADER_LENGTH**\
Parse the header bytes by using **parse_header()**, this will return a tuple: (data_length, recipient_code)\
Use **recvall()** and pass the following arguments:
- Socket object (If you are the client, pass yourself. If you are the server, pass the readable client)
- Data length, the first item of the returned tuple

You will get compressed data in bytes.\
Pass this data into **parse_raw_data()** and you will get a string of data.