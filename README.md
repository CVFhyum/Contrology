## How do you send data?
Use **create_sendable_data()** and pass the following arguments:
- Data in the form of bytes, with no header
- The data type (see below)
- 10 Character Recipient Code

You will get ready bytes to send.

## How do you receive data?
Wait for a header of length **HEADER_LENGTH**\
Parse the header bytes by using **parse_header()**, this will return a tuple: (data_length, data_type, recipient_code)\
Use **recvall()** and pass the following arguments:
- Socket object (If you are the client, pass yourself. If you are the server, pass the readable client)
- Data length, the first item of the returned tuple

You will get compressed data in bytes.\
Pass this data into **parse_raw_data()** and you will get a string of data.

## List of data types that can be sent:
* **ACCEPTED** - Sent by the server to notify a client that a connection can be and has been established
* **REJECTED** - Sent by the server to notify a client that a connection can not be and has not been established
* **CODE** - Sent by the server to indicate the client's code to them (at the start of the program)
* **IMAGE** - Sent by a client that is sending image bytes that should be decoded and displayed
