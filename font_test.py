from sql_handler import SQLHandler
from icecream import ic
import pickle

db_handler = SQLHandler("contrology.db")
a = []
for row in db_handler.get_all_logs():
    for data in row:
        a.append(data)

b = pickle.dumps(a)
print(len(b))