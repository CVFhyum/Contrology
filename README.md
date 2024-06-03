# How do you send data?
Use **create_sendable_data()** and pass the following arguments:
- Data in the form of bytes, with no header
- The data type (see below)
- 10 Character Recipient Code

You will get ready bytes to send.

# How do you receive data?
Wait for a header of length **HEADER_LENGTH**\
Parse the header bytes by using **parse_header()**, this will return a tuple: (data_length, data_type, recipient_code)\
Use **recvall()** and pass the following arguments:
- Socket object (If you are the client, pass yourself. If you are the server, pass the readable client)
- Data length, the first item of the returned tuple

You will get compressed data in bytes.\
Pass this data into **parse_raw_data()** and you will get a string of data.

# List of data types that can be sent:
### On initial connection to server
* **INITIAL_ACCEPT** - Sent by the server to notify a client that a connection can be and has been established
* **INITIAL_REJECT** - Sent by the server to notify a client that a connection can not be and has not been established
* **CODE** - Sent by the server to indicate the client's code to them (at the start of the program)
### Protocol for a client (controller) asking permission of a client (remote)
* **CONNECT_REQUEST** - Sent by a controller that is requesting to take control of a remote. The code of the remote is in the header.
* **CONNECT_REQUEST** - Sent by the server to the remote to request control. The data contains the controller's code concatenated to their hostname *CODE+HOSTNAME* for display purposes.
* **CODE_FOUND** - Sent by the server to the controller if the remote requested was found and the request was sent successfully.
* **CODE_NOT_FOUND** - Sent by the server to the controller if the remote requested was not found.
* **CONNECT_ACCEPT** - Sent by the remote to signify a positive response. The code of the controller is in the header.
* **CONNECT_ACCEPT** - Sent by the server to the controller to signify that controlling permission has been granted. The hostname of the remote is in the data for display purposes.
* **CONNECT_DENY** - Sent by the remote to signify a negative response. The code of the controller is in the header.
* **CONNECT_DENY** - Sent by the server to the controller to signify that controlling permission has been denied
* **IMAGE** - Sent by a client that is sending image bytes that should be decoded and displayed.