from argon2 import PasswordHasher
from icecream import ic
import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function '{func.__name__}' executed in {execution_time:.6f} seconds")
        return result
    return wrapper

@timer
def main():
    ph = PasswordHasher()
    hash = ph.hash("123")
    print(hash)

main()