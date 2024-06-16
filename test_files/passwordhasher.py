import argon2

ph = argon2.PasswordHasher()
for i in range(10):
    h = ph.hash("")
    print(h)