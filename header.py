from constants import DATA_HEADER_LENGTH, RECIPIENT_HEADER_LENGTH, HEADER_LENGTH

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

