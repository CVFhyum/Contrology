from constants import DATA_HEADER_LENGTH, RECIPIENT_HEADER_LENGTH, HEADER_LENGTH

# Implementation of a header. A header is always HEADER_LENGTH long
# The data length and the recipient code are concatenated to each other
# The data length is DATA_HEADER_LENGTH long (padded with whitespaces)
# The recipient code is RECIPIENT_HEADER_LENGTH long
class Header:
    def __init__(self, data_length_raw, recipient_code):
        self.data_length_raw = data_length_raw
        self.recipient_code = recipient_code
        self.header_string = f"{data_length_raw:>{DATA_HEADER_LENGTH}}{recipient_code:>{RECIPIENT_HEADER_LENGTH}}"

    def __str__(self):
        return self.header_string

    def __repr__(self):
        return self.header_string

    def get_header_bytes(self):
        return self.header_string.encode('utf-8')

