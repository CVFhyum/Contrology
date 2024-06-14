from constants import DATA_LENGTH_LENGTH, DATA_TYPE_LENGTH, RECIPIENT_CODE_LENGTH, HEADER_LENGTH

# Implementation of a header. A header is always HEADER_LENGTH long
# The data length is DATA_LENGTH_LENGTH long (padded with whitespaces)
# The data type is DATA_TYPE_LENGTH long (padded with whitespaces)
# The recipient code is RECIPIENT_CODE_LENGTH long
class Header:
    def __init__(self, data_length, data_type, recipient_code):
        self.data_length = data_length
        self.data_type = data_type
        self.recipient_code = recipient_code
        self.header_string = f"{data_length:>{DATA_LENGTH_LENGTH}}{data_type:>{DATA_TYPE_LENGTH}}{recipient_code:>{RECIPIENT_CODE_LENGTH}}"

    def __str__(self):
        return self.header_string

    def __repr__(self):
        return self.header_string

    def get_header_bytes(self):
        return self.header_string.encode('utf-8')

