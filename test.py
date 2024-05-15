# import argon2
# import os
#
# # Function to hash and salt the password
# def hash_and_salt_password(password):
#     salt = os.urandom(16).hex()  # Generate a random salt
#     hasher = argon2.PasswordHasher()
#     hashed_password = hasher.hash(password + salt)
#     return hashed_password, salt
#
# # Function to verify the entered password
# def verify_password(stored_hash, stored_salt, entered_password):
#     hasher = argon2.PasswordHasher()
#     try:
#         hasher.verify(stored_hash, entered_password + stored_salt)
#         return True
#     except argon2.exceptions.VerifyMismatchError:
#         return False
#
# # Example usage
# password = "Hello123"
#
# # Hash and salt the password
# hashed_password, salt = hash_and_salt_password(password)
#
# print(type(hashed_password))
# print()
# print(salt)

class MyClass:
    def __init__(self, a, b):
        self._a = a
        self.b = b

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, value):
        if value is not None and self._a is not None:
            raise ValueError("Attribute 'a' cannot be changed once it is set.")
        self._a = value

# Create an object of MyClass
obj = MyClass(a=None, b=10)

# Changing attribute 'a'
obj.a = 5  # This will raise an error because 'a' is not None

# Output:
# ValueError: Attribute 'a' cannot be changed once it is set.