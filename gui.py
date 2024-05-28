import base64

from functions import *
from constants import *
from configuration import *
from data_handler import DataHandler

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import socket
import threading as thr
import select
from typing import Optional
from pyperclip import copy as cc_copy
from time import sleep

# Global variables that can be accessed all throughout the code
self_code = ""  # This client's code
data_handler_lock = thr.Lock()  # Lock to prevent race conditions on the DataHandler obj
accept_data = True  # Flag that is disabled when the client is interrupted or quits. This will make sure that necessary information-receiving threads are stopped.
connected = False  # Flag that documents if the client is currently connected to the socket.
wait_for_connection_response = thr.Event()

def trackvar():
    while accept_data:
        sleep(1)
        with data_handler_lock:
            length = len(d_handler.incoming_data_queue)
            ic(d_handler.incoming_data_queue)
        ic(client_thread.is_alive(), length)


# Implementation of the WindowManager class.
# This class has one object during runtime and manages the current window that is open.
# This class makes sure only one window is open at once, and raises an error if more than one is open.
# This class has functions for opening different windows (per the user's request).
class WindowManager:
    def __init__(self):
        # Optional[tk.Tk] -> tk.Tk or None
        self._launch_screen_root: Optional[tk.Tk] = None
        self._main_screen_root: Optional[tk.Tk] = None

    @property
    def launch_screen_root(self):
        return self._launch_screen_root

    @launch_screen_root.setter
    def launch_screen_root(self,value):
        if value is not None and self._launch_screen_root is not None:
            raise ValueError("Launch Screen Root modify attempt failed")
        self._launch_screen_root = value

    @property
    def main_screen_root(self):
        return self._main_screen_root

    @main_screen_root.setter
    def main_screen_root(self,value):
        if value is not None and self._main_screen_root is not None:
            raise ValueError("Main Screen Root modify attempt failed")
        self._main_screen_root = value

    def open_launch_screen(self):
        if self.main_screen_root is not None:
            self.main_screen_root.destroy()
            self.main_screen_root = None  # Clean-up
        self.launch_screen_root = LaunchScreen()
        self.launch_screen_root.mainloop()

    def open_main_screen(self):
        if self.launch_screen_root is not None:
            self.launch_screen_root.destroy()
            self.launch_screen_root = None  # Clean-up
        self.main_screen_root = MainScreen()
        self.main_screen_root.mainloop()

    def close_all(self):
        if self.launch_screen_root is not None:
            self.launch_screen_root.destroy()
        if self.main_screen_root is not None:
            self.main_screen_root.destroy()


# When the "Launch App" button is pressed, and a connection is established, this function starts in a thread.
# This thread takes care of receiving incoming data from the server and loading it into incoming_data
def handle_general_connection(c: socket.socket):
    global self_code, connected, accept_data
    data_length,connection_status,self_code = parse_header(c.recv(HEADER_LENGTH))
    ic(self_code)
    # If the initialisation header that was sent by the server has extra data, raise this error
    if data_length > 0:
        raise Exception("Extra data was sent on initialisation")
    if connection_status == "INITIAL_ACCEPT":
        c.setblocking(False)
        while accept_data:
            try:
                # This thread should not block, so data is read asynchronously
                ready = select.select([c],[],[], 0.1)
                if ready[0]:
                    # Receiving data protocol: listen for header, parse it, listen for all of data
                    header = c.recv(HEADER_LENGTH)
                    if header:
                        data_length, data_type, code = parse_header(header)
                        data = parse_raw_data(recvall(c,data_length))
                        if code == self_code or code == ALL_CODE:
                            with data_handler_lock:
                                match data_type:
                                    case "CONNECT_REQUEST":
                                        requester_code, requester_hostname = data[:RECIPIENT_HEADER_LENGTH], data[RECIPIENT_HEADER_LENGTH:]
                                        # TODO: instantly accepting if a request is sent currently, handle that here.
                                        d_handler.insert_new_outgoing_message((create_sendable_data(b"", "CONNECT_ACCEPT", requester_code)))
                                        # d_handler.insert_new_incoming_message((data_type, data)) # TODO: change this if decide to use connec requests attr
                                    case "CONNECT_ACCEPT":
                                        wait_for_connection_response.set()
                                    case _:
                                        d_handler.insert_new_incoming_message((data_type, data))
                        else:
                            raise Exception(f"Intended code {code} didn't match with self code {self_code} or ALL_CODE {ALL_CODE}")
                    else:
                        break
                d_handler.send_all_outgoing_data(c)
            except ConnectionResetError as e:
                print(f"Something went wrong with the connection: {e}")
                connected = False
                accept_data = False
            except KeyboardInterrupt:
                print("Runtime interrupted...")
                connected = False
                accept_data = False
                c.close()
                break

        c.close()

def handle_controlling_connection(connect_code):
    if connect_code == self_code:
        raise Exception("Self code was given") # TODO: make this part of the code not raise an error, but change a label in tkinter
    with data_handler_lock:
        d_handler.insert_new_outgoing_message(create_sendable_data(b"","CONNECT_REQUEST",connect_code))
    wait_for_connection_response.wait()
    wait_for_connection_response.clear()
    print("Permission granted!")


def on_main_close():
    global accept_data
    wm.close_all()
    accept_data = False


# banner = ImageTk.PhotoImage(Image.open("assets/Banner.png"))
# banner_trans = ImageTk.PhotoImage(Image.open("assets/Banner_Trans.png"))
# logo = ImageTk.PhotoImage(Image.open("assets/Logo.png"))
# logo32 = ImageTk.PhotoImage(Image.open("assets/Logo32.png"))


# Generates a tkinter-formatted consolas font at a desired size. Made for code readability.
def consolas(size: int):
    return "Consolas", size

# https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/ttk-style-layer.html
# Makes a style that has the consolas font for a specific widget at a desired size
# Returns the string of the style name
def apply_consolas_to_widget(widget_type: str, size: int) -> str:
    s = ttk.Style()
    s.configure(f'{size}.T{widget_type}', font=consolas(size))
    return f"{size}.T{widget_type}"


class LaunchScreen(tk.Tk):
    # Main setup
    def __init__(self):
        # Simple configuration and variable loading
        super().__init__()
        self.title("Launch - Contrology")
        self.width = 700
        self.height = 700
        self.logo32 = ImageTk.PhotoImage(Image.open("assets/Logo32.png"))

        # Complex configuration
        self.geometry(get_geometry_string(self.width, self.height))
        # self.resizable(False, False) # todo: removed for debug
        self.iconphoto(True, self.logo32)
        self.protocol("WM_DELETE_WINDOW", on_main_close)

        # Widgets
        self.banner_frame = LaunchScreenBannerFrame(self)
        self.button_frame = LaunchScreenButtonsFrame(self)

        # Functions
        self.dimensions()

    def dimensions(self):
        self.columnconfigure(0, weight=1)

# Frames belonging to LaunchScreen
class LaunchScreenBannerFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid(row=0,column=0)
        self.banner_trans = ImageTk.PhotoImage(Image.open("assets/Banner_Trans.png"))
        self.configure(width=parent.width,height=parent.height/2)
        self.configure(highlightthickness=1,highlightbackground='green')  # debug view

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        # Creation
        main_banner = ttk.Label(self,image=self.banner_trans)
        # Placement
        main_banner.grid(row=0,column=0)

    def dimensions(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.grid_propagate(False)
class LaunchScreenButtonsFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.grid(row=1,column=0)
        self.configure(width=parent.width,height=parent.height / 2)
        self.configure(highlightthickness=1,highlightbackground='green')  # debug view

        self.feedback_label_var = tk.StringVar()
        self.admin_password_entry_var = tk.StringVar()
        self.admin_password_entry_var.set("Enter password...")
        self.admin_password_entry_style = ttk.Style()
        self.admin_password_entry_style.configure('grey.TEntry', foreground='grey')
        self.admin_password_entry_style.configure('black.TEntry', foreground='black')
        self.admin_button_view = True

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        # Callbacks
        def switch_admin_widgets(_=None):  # todo: doc
            # _ is not None if the function is invoked by pressing the escape key
            # admin_button_view is True if the button is currently visible
            # If the parenthetical expression evaluates to True, the button is visible and escape was pressed
            # Negate the parenthetical expression to only switch the widgets if escape was pressed while the entry was visible
            if not (_ is not None and self.admin_button_view):
                if self.admin_button_view:
                    admin_log_in_button.grid_remove()
                    admin_password_entry.grid()
                    self.admin_button_view = False
                else:
                    admin_log_in_button.grid()
                    admin_password_entry.grid_remove()
                    self.admin_password_entry_var.set("")
                    self.admin_button_view = True

        def admin_password_entry_focus_in(_=None):  # todo: doc
            admin_password_entry.configure(style='black.TEntry',show='')
            if self.admin_password_entry_var.get() == "Enter password...":
                self.admin_password_entry_var.set("")

        def admin_password_entry_focus_out(_=None):  # todo: doc
            if self.admin_password_entry_var.get() == "":
                admin_password_entry.configure(style='grey.TEntry',show='')
                self.admin_password_entry_var.set("Enter password...")

        def admin_password_entry_handle_enter(_=None):  # todo: doc
            # todo: handle the entered password (verify it)
            print(self.admin_password_entry_var.get())

        def try_to_connect():
            global connected, client_thread
            self.feedback_label_var.set("Trying to connect...")
            feedback_label.config(foreground='green')
            self.update()  # Fixes weird bug where screen doesn't update
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((SERVER_IP,SERVER_PORT))
                self.feedback_label_var.set("Connected!")
                feedback_label.config(foreground='green')
                self.update()
            except (ConnectionRefusedError, ConnectionResetError, ConnectionError, ConnectionAbortedError, OSError) as e:
                print(f"Couldn't connect to server: {e}")
                self.feedback_label_var.set("Couldn't connect to server.")
                feedback_label.config(foreground='red')
                connected = None
                return
            connected = True
            client_thread = thr.Thread(target=handle_general_connection,args=(sock,))
            client_thread.start()
            wm.open_main_screen()

        # Creation
        launch_app_button = ttk.Button(self,text="Launch App", style=apply_consolas_to_widget("Button", 32), command=try_to_connect)
        feedback_label = ttk.Label(self, textvariable=self.feedback_label_var, font=consolas(12), foreground='green')
        admin_log_in_button = ttk.Button(self, text="Administrator Log In", style=apply_consolas_to_widget("Button", 12), command=switch_admin_widgets)
        admin_password_entry = ttk.Entry(self, textvariable=self.admin_password_entry_var, style='grey.TEntry',font=consolas(13))

        # Placement
        launch_app_button.grid(row=0,column=0,sticky='s')
        feedback_label.grid(row=1,column=0,sticky='n')
        admin_log_in_button.grid(row=2,column=0)
        admin_password_entry.grid(row=2,column=0)
        admin_password_entry.grid_remove()  # Remove it at initialization because it should only appear when the button is pressed

        # Bindings
        admin_password_entry.bind("<FocusIn>",admin_password_entry_focus_in)
        admin_password_entry.bind("<FocusOut>",admin_password_entry_focus_out)
        admin_password_entry.bind("<Return>",admin_password_entry_handle_enter)
        admin_password_entry.bind("<Escape>",switch_admin_widgets)

    def dimensions(self):
        self.grid_propagate(False)
        self.rowconfigure((0,1,2), weight=1)
        self.columnconfigure(0, weight=1)


class MainScreen(tk.Tk):
    def __init__(self):
        # Simple configuration and variable loading
        super().__init__()
        self.title("Home - Contrology")
        self.width = 1200
        self.height = 800

        # Complex configuration
        self.geometry(get_geometry_string(self.width,self.height))
        # self.resizable(False, False) # todo: removed for debug
        self.protocol("WM_DELETE_WINDOW",on_main_close)

        # Widgets
        self.top_frame = MainScreenInfoFrame(self)
        self.middle_frame = MainScreenConnectFrame(self)
        self.bottom_frame = MainScreenRecentFrame(self)

        # Functions
        self.dimensions()

    def dimensions(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure((0,1,2), weight=1)

# Frames belonging to MainScreen
class MainScreenInfoFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid(row=0, column=0)  # change
        self.configure(width=parent.width,height=parent.height*0.2)  # change
        self.configure(highlightthickness=1,highlightbackground='green')  # debug view
        self.update()

        self.banner_trans = get_resized_image("assets/Banner_Trans.png", 0.36)
        self.self_code = tk.StringVar()

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        def show_copied_message():
            my_code_click_to_copy_label.configure(text="Copied to Clipboard!", foreground='green')
            sleep(1)
            my_code_click_to_copy_label.configure(text="(Click to Copy)", foreground='black')

        main_banner = ttk.Label(self, image=self.banner_trans)
        code_container_frame = tk.Frame(self, highlightthickness=1, highlightbackground='green', height=self.winfo_height(), width=self.winfo_reqwidth()*0.25)
        code_container_frame.rowconfigure((0,1,2), weight=1)
        code_container_frame.columnconfigure(0, weight=1)
        code_container_frame.grid_propagate(False)
        my_code_info_label = ttk.Label(code_container_frame, text="My Code", font=consolas(14))
        my_code_value_label = ttk.Label(code_container_frame, text=self_code, font=consolas(32))
        my_code_click_to_copy_label = ttk.Label(code_container_frame, text="(Click to Copy)", font=consolas(12))

        main_banner.grid(row=0,column=0)
        code_container_frame.grid(row=0,column=1,sticky='e')
        my_code_info_label.grid(row=0,column=0)
        my_code_value_label.grid(row=1,column=0)
        my_code_click_to_copy_label.grid(row=2,column=0)

        my_code_value_label.bind('<1>', lambda event: [cc_copy(self_code), thr.Thread(target=show_copied_message).start()])
        my_code_click_to_copy_label.bind('<1>', lambda event: [cc_copy(self_code), thr.Thread(target=show_copied_message).start()])


    def dimensions(self):
        self.columnconfigure(1, weight=1)
        self.grid_propagate(False)

class MainScreenConnectFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid(row=1, column=0)  # change
        self.configure(width=parent.width,height=parent.height*0.4)  # change
        self.configure(highlightthickness=1,highlightbackground='green')  # debug view
        self.connect_code_var = tk.StringVar()

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        connect_label = ttk.Label(self, text="Connect to a remote machine", font=consolas(32))
        connect_code_entry = ttk.Entry(self, textvariable=self.connect_code_var, font=consolas(32),width=10)
        connect_button = ttk.Button(self, text="->",style=apply_consolas_to_widget('Button', 32),width=2,command=self.set_up_connection_thread)

        connect_label.grid(row=0,column=0,sticky='s')
        connect_code_entry.grid(row=1,column=0,sticky='')
        connect_button.grid(row=2,column=0,sticky='n')

    def dimensions(self):
        self.grid_propagate(False)
        self.rowconfigure((0,1,2), weight=1)
        self.columnconfigure(0, weight=1)

    def set_up_connection_thread(self):
        connection_thread = thr.Thread(target=handle_controlling_connection,args=(self.connect_code_var.get(),))
        connection_thread.start()




class MainScreenRecentFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid(row=2, column=0)  # change
        self.configure(width=parent.width,height=parent.height*0.4)  # change
        self.configure(highlightthickness=1,highlightbackground='green')  # debug view

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        pass

    def dimensions(self):
        self.grid_propagate(False)


if __name__ == "__main__":
    client_thread = thr.Thread()
    track = thr.Thread(target=trackvar, daemon=True)
    track.start()
    d_handler = DataHandler()
    wm = WindowManager()
    wm.open_launch_screen()

