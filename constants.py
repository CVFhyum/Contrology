from string import ascii_lowercase, ascii_uppercase, digits

# Header info
DATA_HEADER_LENGTH = 20
DATA_TYPE_LENGTH = 20
RECIPIENT_HEADER_LENGTH = 10
HEADER_LENGTH = DATA_HEADER_LENGTH + DATA_TYPE_LENGTH + RECIPIENT_HEADER_LENGTH

# Alphanumeric string
# TODO: consider making this only digits
ALPHANUMERIC_CHARACTERS = ascii_lowercase + ascii_uppercase + digits

# Server info
SERVER_CODE = "0000000000"
ALL_CODE = "9999999999"
