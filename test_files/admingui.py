import tkinter as tk
from tkinter import ttk,messagebox
from PIL import Image,ImageTk
from functions import get_geometry_string  # Assume this function is defined in functions.py

# Placeholder pdata
logs = [
    "2024-06-12 10:15:32 - User1 connected",
    "2024-06-12 10:17:45 - User2 connected",
    "2024-06-12 10:18:22 - User1 disconnected",
    "2024-06-12 10:20:11 - User3 connected",
    "2024-06-12 10:25:30 - User2 disconnected"
]

users = [
    {"id": "1","hostname": "PC1","address": "1.1.1.1","code": "1234"},
    {"id": "2","hostname": "PC2","address": "2.2.2.2","code": "5678"},
    {"id": "3","hostname": "PC3","address": "3.3.3.3","code": "9101"},
    {"id": "4","hostname": "PC4","address": "4.4.4.4","code": "1121"}
]


# Font utility functions
def consolas(size: int):
    return "Consolas",size


def apply_consolas_to_widget(widget_type: str,size: int,colour: str = None) -> str:
    s = ttk.Style()
    style_string = f'{size}{colour}.T{widget_type}'
    s.configure(style_string,font=consolas(size))
    if colour:
        s.configure(style_string,foreground=colour)
    return style_string


class AdminGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Admin Panel")
        self.geometry(get_geometry_string(1200,800))

        # Grid configuration
        self.columnconfigure(0,weight=1)
        self.rowconfigure([0,1,2],weight=1)

        # Admin Panel Label
        self.title_label = ttk.Label(self,text="Admin Panel",style=apply_consolas_to_widget("Label",24))
        self.title_label.grid(row=0,column=0,pady=20,sticky="ew")

        # Notebook for Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1,column=0,padx=10,pady=10,sticky="nsew")

        # Logs Tab
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame,text="Logs")

        self.log_label = ttk.Label(self.logs_frame,text="Connection Logs",style=apply_consolas_to_widget("Label",14))
        self.log_label.grid(row=0,column=0,padx=5,pady=5,sticky='w')

        self.log_listbox = tk.Listbox(self.logs_frame,font=consolas(12),width=80,height=20)
        self.log_listbox.grid(row=1,column=0,padx=5,pady=5,sticky='nsew')
        for log in logs:
            self.log_listbox.insert(tk.END,log)

        # Users Tab
        self.users_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.users_frame,text="Users")

        self.user_label = ttk.Label(self.users_frame,text="Manage Users",style=apply_consolas_to_widget("Label",14))
        self.user_label.grid(row=0,column=0,padx=5,pady=5,sticky='w')

        self.user_listbox = tk.Listbox(self.users_frame,font=consolas(12),width=30,height=20)
        self.user_listbox.grid(row=1,column=0,padx=5,pady=5,sticky='nsew')
        for user in users:
            self.user_listbox.insert(tk.END,user["id"])

        self.user_listbox.bind("<<ListboxSelect>>",self.display_user_details)

        # User details frame
        self.user_details_frame = ttk.Frame(self.users_frame)
        self.user_details_frame.grid(row=1,column=1,padx=10,pady=10,sticky='nsew')

        # Placeholder for user details (will be filled dynamically)
        self.user_details = {}

        # Return to Launch Screen and Log Out button
        self.logout_button = ttk.Button(self,text="Return to Launch Screen and Log Out",command=self.exit_application,
                                        style=apply_consolas_to_widget("Button",14))
        self.logout_button.grid(row=2,column=0,pady=20,sticky='ew')

    def display_user_details(self,event):
        selected_index = self.user_listbox.curselection()
        if not selected_index:
            return

        # Clear existing details
        for widget in self.user_details_frame.winfo_children():
            widget.destroy()

        user_id = self.user_listbox.get(selected_index)
        user = next(user for user in users if user["id"] == user_id)

        self.user_details = {key: tk.StringVar(value=value) for key,value in user.items()}

        for idx,(key,var) in enumerate(self.user_details.items()):
            label = ttk.Label(self.user_details_frame,text=key.capitalize(),style=apply_consolas_to_widget("Label",12))
            label.grid(row=idx,column=0,padx=10,pady=5,sticky='w')

            value_label = ttk.Label(self.user_details_frame,textvariable=var,style=apply_consolas_to_widget("Label",12))
            value_label.grid(row=idx,column=1,padx=10,pady=5,sticky='w')
            value_label.bind("<Button-1>",self.make_editable(var,value_label))

        self.save_button = ttk.Button(self.user_details_frame,text="Save",command=self.save_user_details,
                                      style=apply_consolas_to_widget("Button",12))
        self.save_button.grid(row=len(self.user_details),column=0,padx=10,pady=10,sticky='ew')

        self.cancel_button = ttk.Button(self.user_details_frame,text="Don't Save",command=self.cancel_edit,
                                        style=apply_consolas_to_widget("Button",12))
        self.cancel_button.grid(row=len(self.user_details),column=1,padx=10,pady=10,sticky='ew')

    def make_editable(self,var,label):
        def callback(event):
            entry = ttk.Entry(self.user_details_frame,textvariable=var,font=consolas(12))
            entry.grid(row=label.grid_info()['row'],column=1,padx=10,pady=5,sticky='w')
            entry.focus()
            entry.bind("<Return>",lambda e: self.make_label(var,entry))
            entry.bind("<FocusOut>",lambda e: self.make_label(var,entry))

        return callback

    def make_label(self,var,entry):
        label = ttk.Label(self.user_details_frame,textvariable=var,style=apply_consolas_to_widget("Label",12))
        label.grid(row=entry.grid_info()['row'],column=1,padx=10,pady=5,sticky='w')
        label.bind("<Button-1>",self.make_editable(var,label))

    def save_user_details(self):
        updated_user = {key: var.get() for key,var in self.user_details.items()}
        print("Stuff changed:",updated_user)

    def cancel_edit(self):
        for key,var in self.user_details.items():
            var.set(users[int(var.get()) - 1][key])

    def exit_application(self):
        print("Exit requested")
        # Additional code to handle exiting can be added here


if __name__ == "__main__":
    app = AdminGUI()
    app.mainloop()
