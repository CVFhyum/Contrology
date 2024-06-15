import tkinter as tk
from tkinter import ttk
from functions import *
from icecream import ic
import random as r

# test function

def gen_random_record():
    id_num = str(r.randint(0, 100))
    hostname = f"PC-{r.randint(1, 200)}"
    address = f"{r.randint(1, 255)}.{r.randint(1, 255)}.{r.randint(1, 255)}.{r.randint(1, 255)}"
    code = ''.join(r.choices('0123456789', k=10))
    return [id_num, hostname, address, code]

class ColumnsFrame(tk.Frame):
    def __init__(self, parent, columns: list[str]):
        super().__init__(parent)
        self.parent = parent
        self.columns = columns
        self.column_label_widgets: list[tk.Label] = []
        self.configure(highlightthickness=1, highlightbackground='red')
        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        for idx, column in enumerate(self.columns):
            column = tk.Label(self, text=column, highlightthickness=1, highlightbackground="black",font=consolas(16) + ("bold",))
            column.grid(row=0,column=idx)
            self.column_label_widgets.append(column)

    def dimensions(self):
        self.grid_propagate()

class DataFrame(tk.Frame):
    def __init__(self, parent, data: list[str]):
        super().__init__(parent)
        self.parent = parent
        self.data = data
        self.data_label_widgets = []
        self.configure(highlightthickness=1, highlightbackground='blue')
        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        for idx, column in enumerate(self.data):
            column = tk.Label(self, text=column, highlightthickness=1, highlightbackground="black", font=consolas(16))
            column.grid(row=0,column=idx)
            self.data_label_widgets.append(column)

    def dimensions(self):
        pass

class Table(tk.Frame):
    def __init__(self, parent, column_headings: list[str], initial_data: list[list[str]]):
        super().__init__(parent)
        self.configure(highlightthickness=1, highlightbackground='green')
        self.columns_frame = None
        self.data_frames = []
        self.column_headings = column_headings
        self.initial_data = initial_data
        self.dimensions()
        self.create_widgets()
        self.bind_all('s', lambda e: self.push_data_to_table([gen_random_record()]))

    def create_widgets(self):
        self.columns_frame = ColumnsFrame(self, self.column_headings)
        self.columns_frame.grid(row=0,column=0,sticky='ew')
        self.push_data_to_table(self.initial_data)

    def req_label_table(self):
        columns_labels = [label for label in self.columns_frame.column_label_widgets]
        data_labels = [[label for label in data_frame.data_label_widgets] for data_frame in self.data_frames]
        data_labels.insert(0,columns_labels)
        return data_labels

    # This function calculates the max width of all the columns inside the table.
    def get_required_widths_list(self):
        self.update_idletasks()  # Update the geometry manager to get the correct label measurements
        # Generate a 2d list that represents the width of each label in the table, including the columns
        # Get the length of the text in each widget, since label width is measured by characters
        # 1 is added to all widths to add extra padding around the label so the table doesn't look compressed
        columns_labels_width = [
            len(label.cget("text")) + 1
            for label in self.columns_frame.column_label_widgets]
        data_labels_width = [
            [
                len(label.cget("text")) + 1
                for label in data_frame.data_label_widgets]
            for data_frame in self.data_frames]
        data_labels_width.insert(0,columns_labels_width)
        #ic(data_labels_width)

        # Find the maximum width value of each column and return it
        required_widths = [max(widths) for widths in transpose(data_labels_width)]
        return required_widths

    def set_labels_to_highest_width(self):
        required_widths = self.get_required_widths_list()
        label_table = self.req_label_table()
        transposed_label_table = transpose(label_table)
        for col_idx, column_labels in enumerate(transposed_label_table):
            for label in column_labels:
                label.configure(width=required_widths[col_idx])

    def push_data_to_table(self, data: list[list[str]]):
        for idx, datum in enumerate(data):
            data_frame = DataFrame(self, datum)
            data_frame.grid(row=len(self.data_frames)+1, column=0, sticky='ew')
            self.data_frames.append(data_frame)
            bind_to_hierarchy(data_frame,"<Button-1>",lambda e,df=data_frame: self.remove_data_from_table(df))
        self.reload_table_data()

    def remove_data_from_table(self, data_frame: DataFrame):
        data_frame.grid_forget()
        self.data_frames.remove(data_frame)
        self.reload_table_data()

    def reload_table_data(self):
        # todo: if columns need reloading too, do that here
        for data_frame in self.data_frames:
            data_frame.grid_forget()
        for idx, data_frame in enumerate(self.data_frames):
            data_frame.grid(row=idx+1, column=0, sticky='ew')
        self.set_labels_to_highest_width()

    def dimensions(self):
        self.grid_columnconfigure(0, weight=1)





if __name__ == "__main__":
    pdata = []
    for i in range(10):
        pdata.append(gen_random_record())

    root = tk.Tk()
    root.geometry("1200x800")
    table = Table(root, ["id", "hostname", "address", "code"], pdata)
    table.pack(expand=True, fill="both")
    root.mainloop()
