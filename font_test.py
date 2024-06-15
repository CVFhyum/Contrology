from sql_handler import SQLHandler

db_handler = SQLHandler("contrology.db")
a = []
for row in db_handler.get_all_logs():
    a.append(row)

print(a[0])