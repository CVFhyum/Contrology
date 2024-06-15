import argon2

ph = argon2.PasswordHasher()
h = ph.hash("")
print(h)