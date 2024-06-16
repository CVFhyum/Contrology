"""
Consistency checks:
- Make sure that each frame is gridded outside the frame __init__ method itself, but rather the class that is creating the frame
- Make sure that all containers (roots, toplevels, frames) have their width and height as attributes and are defined as such
- > self.width, self.height = w, h
- Make sure that all functions have type hints
- Make sure that for every window with a create_widgets method and a dimensions method, that dimensions is called before widget creation.
- Make sure that every frame in a container is an attribute of it (using self.)
- Make sure that all frames inherit from ttk.Frame
- todo: Make sure that the scrollbar in incoming requests does not move when not active (check table for docs)
"""

from functions import *
from constants import *
from configuration import *
from data_handler import DataHandler
from remote import Remote
from control_event import ControlEvent

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageSequence
import socket
import threading as thr
import select
from typing import Optional, Any
from pyperclip import copy as cc_copy
from time import sleep, time
from random import randint as ri
from mss.windows import MSS
from functools import partial
import argon2

t = time()
# Global variables that can be accessed all throughout the code
SCREEN_WIDTH, SCREEN_HEIGHT = get_resolution_of_primary_monitor()
self_code = ""  # This client's code
data_handler_lock = thr.Lock()  # Lock to prevent race conditions on the DataHandler obj
accept_data = True  # Flag that is disabled when the client is interrupted or quits. This will make sure that necessary information-receiving threads are stopped.
connected = False  # Flag that documents if the client is currently connected to the socket.
incoming_requests_frame_obj: Any = None  # The frame object of incoming requests, so it can be edited in the global scope.
outgoing_requests_frame_obj: Any = None  # The frame object of outgoing requests, so it can be edited in the global scope.
connect_feedback_var: Optional[tk.StringVar] = None  # StringVar of the feedback label in the connect screen
controlling_connection_thread_flags = thr.Event(), FlagObject(False)
code_flags = thr.Event(), FlagObject(False)
remote_connection_thread_flags = {}
remote_thread_id = 0
logs_table_obj: Any = None


def trackvar():
    while accept_data:
        sleep(1)
        with data_handler_lock:
            length = len(d_handler.incoming_data_queue)
            # ic(d_handler.incoming_data_queue)
        ic(general_connection_thread.is_alive(),length)


# Implementation of the WindowManager class.
# This class has one object during runtime and manages the current window that is open.
# This class makes sure only one window is open at once, and raises an error if more than one is open.
# This class has functions for opening different windows (per the user's request).
# The roots attribute of this object is a list of roots, either None or the tk.Tk object.
# [launch_root, main_root, share_root, admin_root]
class WindowManager:
    def __init__(self):
        # Optional[tk.Tk] -> tk.Tk or None
        self._launch_screen_root: Optional[tk.Tk] = None
        self._main_screen_root: Optional[tk.Tk] = None
        self._share_screen_root: Optional[tk.Tk] = None
        self._admin_screen_root: Optional[tk.Tk] = None
        self._roots: list[Optional[tk.Tk]] = [None]*4

    @property
    def launch_screen_root(self):
        return self._launch_screen_root

    @launch_screen_root.setter
    def launch_screen_root(self,value):
        if value is not None and self.launch_screen_root is not None:
            raise ValueError("Launch Screen Root modify attempt failed")
        self._launch_screen_root = value
        self._roots[0] = value

    @property
    def main_screen_root(self):
        return self._main_screen_root

    @main_screen_root.setter
    def main_screen_root(self,value):
        if value is not None and self.main_screen_root is not None:
            raise ValueError("Main Screen Root modify attempt failed")
        self._main_screen_root = value
        self._roots[1] = value

    @property
    def share_screen_root(self):
        return self._share_screen_root

    @share_screen_root.setter
    def share_screen_root(self,value):
        if value is not None and self.share_screen_root is not None:
            raise ValueError("Share Screen Root modify attempt failed")
        self._share_screen_root = value
        self._roots[2] = value

    @property
    def admin_screen_root(self):
        return self._admin_screen_root

    @admin_screen_root.setter
    def admin_screen_root(self,value):
        if value is not None and self.admin_screen_root is not None:
            raise ValueError("Admin Screen Root modify attempt failed")
        self._admin_screen_root = value
        self._roots[3] = value

    def open_launch_screen(self):
        for root_index, root in enumerate(self._roots):
            if root is not None:
                root.destroy()
                self._roots[root_index] = None
        self.launch_screen_root = LaunchScreen()
        self.launch_screen_root.mainloop()

    def open_main_screen(self):
        for root_index,root in enumerate(self._roots):
            if root is not None:
                root.destroy()
                self._roots[root_index] = None
        self.main_screen_root = MainScreen()
        self.main_screen_root.mainloop()

    def open_share_screen(self):
        for root_index,root in enumerate(self._roots):
            if root is not None:
                root.destroy()
                self._roots[root_index] = None
        self.share_screen_root = ShareScreen(current_remote)
        self.share_screen_root.mainloop()

    def open_admin_screen(self):
        for root_index, root in enumerate(self._roots):
            if root is not None:
                root.destroy()
                self._roots[root_index] = None
        self.admin_screen_root = AdminScreen()
        self.admin_screen_root.mainloop()

    def update_all(self):
        for root_index, root in enumerate(self._roots):
            if root is not None:
                root.update()

    def close_all(self):
        for root_index,root in enumerate(self._roots):
            if root is not None:
                root.destroy()


# When the "Launch App" button is pressed, and a connection is established, this function starts in a thread.
# This thread takes care of receiving incoming data from the server and loading it into incoming_data
def handle_general_connection(c: socket.socket):
    # todo - move lines from here to connection_status condition statement into try_to_connect - if the client gets INITIAL_DENY main screen should not be open!
    global self_code, connected, accept_data, remote_thread_id
    data_length,connection_status,self_code = parse_header(c.recv(HEADER_LENGTH))
    ic(self_code)
    # If the initialisation header that was sent by the server has extra data, raise this error
    if data_length > 0:
        raise Exception(f"Extra data was sent on initialisation {data_length}")
    if connection_status == "INITIAL_ACCEPT":
        # c.setblocking(False)
        while accept_data:
            try:
                # This thread should not block, so data is read asynchronously
                ready = select.select([c],[],[], 0.1)
                if ready[0]:
                    # Receiving data protocol: listen for header, parse it, listen for all of data
                    header = c.recv(HEADER_LENGTH)
                    if header:
                        data_length, data_type, code = parse_header(header)
                        data = recvall(c,data_length)
                        if data_type in PICKLED_DATA_TYPES:
                            data = parse_raw_data(data, pickled=True)
                        elif data_type == "IMAGE":
                            data = parse_raw_data(data, image=True)
                        else:
                            data = parse_raw_data(data)
                        if code == self_code or code == ALL_CODE:
                            match data_type:
                                case "CONNECT_REQUEST":
                                    requester_code, requester_hostname = data[:RECIPIENT_CODE_LENGTH],data[RECIPIENT_CODE_LENGTH:]
                                    remote_connection_thread = thr.Thread(target=handle_remote_connection, args=(requester_code, requester_hostname, remote_thread_id))
                                    remote_connection_thread_flags.update({remote_thread_id: (thr.Event(),FlagObject(False))})
                                    remote_connection_thread.start()
                                    remote_thread_id += 1
                                case "CONNECT_ACCEPT":
                                    event, flag = controlling_connection_thread_flags
                                    event.set()
                                    flag.true()
                                    current_remote.copy_from(data)
                                case "CONNECT_DENY":
                                    event, flag = controlling_connection_thread_flags
                                    event.set()
                                    flag.false()
                                case "CODE_FOUND":
                                    code_event, code_flag = code_flags
                                    code_event.set()
                                    code_flag.true()
                                case "CODE_NOT_FOUND":
                                    code_event, code_flag = code_flags
                                    code_event.set()
                                    code_flag.false()
                                case "IMAGE":
                                    with data_handler_lock:
                                        d_handler.set_last_image(data)
                                case "CONTROL_EVENT":
                                    data.execute_event()
                                case "DB_LOGS":
                                    parsed_logs = [list(tup) for tup in data]
                                    logs_table_obj.push_data_to_table(parsed_logs)
                                case _:
                                    with data_handler_lock:
                                        d_handler.insert_new_incoming_message((data_type, data))
                        else:
                            raise Exception(f"Intended code {code} didn't match with self code {self_code} or ALL_CODE {ALL_CODE}")
                    else:
                        break
                with data_handler_lock:
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
        connected = False
        c.close()


# Handles an incoming request to control self machine
# This function controls everything from the socket receiving a request packet, until the user presses accept or deny.
# If deny is pressed, it is handled here.
# If accept is pressed, another thread is called
def handle_remote_connection(controller_code, controller_hostname, thread_name):
    # display a new request frame in the incoming requests using the two args
    # use the third arg to receive the event and flag objects from the main dictionary
    event, flag = remote_connection_thread_flags[thread_name]
    incoming_requests_frame_obj.add_request_frame(controller_hostname,controller_code,event,flag)
    event.wait()
    if flag:
        my_remote_info = Remote(socket.gethostname(), self_code, SCREEN_WIDTH, SCREEN_HEIGHT)
        info_bytes = pickle.dumps(my_remote_info)
        with data_handler_lock:
            d_handler.insert_new_outgoing_message(create_sendable_data(info_bytes,"CONNECT_ACCEPT",controller_code,pickled=True))
        with MSS() as mss_obj:
            while True: # todo: change this to be put in a thread. add while code still exists, while controller has not closed, etc.
                screenshot_bytes = get_screenshot_bytes(mss_obj, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
                screenshot_data = create_sendable_data(screenshot_bytes, "IMAGE",controller_code)
                with data_handler_lock:
                    d_handler.insert_new_outgoing_message(screenshot_data)
    else:
        with data_handler_lock:
            d_handler.insert_new_outgoing_message(create_sendable_data(b"","CONNECT_DENY",controller_code))
        del remote_connection_thread_flags[thread_name]


# Handles requesting control of another machine
def handle_controlling_connection(remote_code):
    temp_message_setter = partial(set_temporary_message, var=connect_feedback_var, old_text="", wait_seconds=2)
    if remote_code == self_code:
        temp_message_setter(new_text="You cannot give your own code!")
    else:
        # TODO: make sure that the same machine isn't receiving a request multiple times
        with data_handler_lock:
            d_handler.insert_new_outgoing_message(create_sendable_data(b"","CONNECT_REQUEST",remote_code))
        code_event, code_flag = code_flags
        event,flag = controlling_connection_thread_flags
        code_event.wait()
        code_event.clear()
        if code_flag:
            current_request_frame: RequestFrame = outgoing_requests_frame_obj.add_request_frame("Unknown",remote_code)
            event.wait()
            event.clear()
            if flag:
                current_remote.code = remote_code
                current_request_frame.switch_to_connect_button()
            else:
                temp_message_setter(new_text="Request was denied.")
                outgoing_requests_frame_obj.remove_request_frame(current_request_frame)
        else:
            temp_message_setter(new_text="Code not found.")


def on_main_close():
    global accept_data, connected
    wm.close_all()
    connected = False
    accept_data = False


# banner = ImageTk.PhotoImage(Image.open("assets/Banner.png"))
# banner_trans = ImageTk.PhotoImage(Image.open("assets/Banner_Trans.png"))
# logo = ImageTk.PhotoImage(Image.open("assets/Logo.png"))
# logo32 = ImageTk.PhotoImage(Image.open("assets/Logo32.png"))





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
        """ Creation """
        main_banner = ttk.Label(self,image=self.banner_trans)
        """ Placement """
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

        """ Callbacks """

        def try_to_connect():
            global connected,general_connection_thread
            self.feedback_label_var.set("Trying to connect...")
            feedback_label.config(foreground='green')
            self.update()  # Fixes weird bug where screen doesn't update
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            try:
                sock.connect((SERVER_IP,SERVER_PORT))
                self.feedback_label_var.set("Connected!")
                feedback_label.config(foreground='green')
                self.update()
            except (ConnectionRefusedError,ConnectionResetError,ConnectionError,ConnectionAbortedError,OSError) as e:
                print(f"Couldn't connect to server: {e}")
                self.feedback_label_var.set("Couldn't connect to server.")
                feedback_label.config(foreground='red')
                connected = None
                return
            connected = True
            general_connection_thread = thr.Thread(target=handle_general_connection,args=(sock,))
            general_connection_thread.start()

        def general_connect():
            try_to_connect()
            if connected:
                wm.open_main_screen()

        def admin_connect():
            try_to_connect()
            if connected:
                wm.open_admin_screen()

        # Takes care of swapping the button widget with the entry widget on the launch screen
        def switch_admin_widgets(_=None):
            # _ is not None if the function is invoked by pressing the escape key
            # admin_button_view is True if the button is currently visible
            # If the parenthetical expression evaluates to True, the button is visible and escape was pressed, which shouldn't do anything
            # Negate the parenthetical expression to only switch the widgets if escape was pressed while the *entry* was visible
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

        # When the password entry gets focus, this callback is invoked, which deletes the default "Enter password..." text
        def admin_password_entry_focus_in(_=None):
            admin_password_entry.configure(style='black.TEntry',show='')
            if self.admin_password_entry_var.get() == "Enter password...":
                self.admin_password_entry_var.set("")

        # When the password entry loses focus, this callback is invoked, which sets the default "Enter password..." text if the entry is empty
        def admin_password_entry_focus_out(_=None):
            if self.admin_password_entry_var.get() == "":
                admin_password_entry.configure(style='grey.TEntry',show='')
                self.admin_password_entry_var.set("Enter password...")

        # When Enter is pressed while the password entry has focus, this callback is invoked. It verifies the password and TODO: tells the w_manager to open the admin screen.
        def admin_password_entry_handle_enter(_=None):
            # todo: handle the entered password (verify it)
            ic(self.admin_password_entry_var.get())
            try:
                ph = argon2.PasswordHasher()
                ph.verify(ADMIN_PASSWORD,self.admin_password_entry_var.get())
                admin_connect()
            except (argon2.exceptions.VerificationError, argon2.exceptions.InvalidHashError):
                # todo: add wrong password label.
                print("incorrect password")

        """ Creation """
        launch_app_button = ttk.Button(self,text="Launch App", style=apply_consolas_to_widget("Button", 32), command=general_connect)
        feedback_label = ttk.Label(self, textvariable=self.feedback_label_var, font=consolas(12), foreground='green')
        admin_log_in_button = ttk.Button(self, text="Administrator Log In", style=apply_consolas_to_widget("Button", 12), command=switch_admin_widgets)
        admin_password_entry = ttk.Entry(self, textvariable=self.admin_password_entry_var, style='grey.TEntry',font=consolas(13))

        """ Placement """
        launch_app_button.grid(row=0,column=0,sticky='s')
        feedback_label.grid(row=1,column=0,sticky='n')
        admin_log_in_button.grid(row=2,column=0)
        admin_password_entry.grid(row=2,column=0)
        admin_password_entry.grid_remove()  # Remove it at initialization because it should only appear when the button is pressed

        """ Bindings """
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
        self.bottom_frame = MainScreenUtilitiesFrame(self)

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
        # todo: change this using tk.after or using a thread, cannot sleep and block in a tkinter program
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
        global connect_feedback_var
        super().__init__(parent)
        self.grid(row=1, column=0)  # change
        self.configure(width=parent.width,height=parent.height*0.4)  # change
        self.configure(highlightthickness=1,highlightbackground='green')  # debug view
        self.connect_code_var = tk.StringVar()
        self.feedback_var = tk.StringVar()
        connect_feedback_var = self.feedback_var

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        connect_label = ttk.Label(self, text="Connect to a remote machine", font=consolas(32))
        connect_code_entry = ttk.Entry(self, textvariable=self.connect_code_var, font=consolas(32),width=10)
        connect_button = ttk.Button(self, text="->",style=apply_consolas_to_widget('Button', 32),width=2,command=self.set_up_connection_thread)
        feedback_label = ttk.Label(self, textvariable=self.feedback_var, font=consolas(16), foreground='red')

        connect_label.grid(row=0,column=0,sticky='s')
        connect_code_entry.grid(row=1,column=0,sticky='')
        connect_button.grid(row=2,column=0,sticky='n')
        feedback_label.grid(row=3,column=0,sticky='s')

    def dimensions(self):
        self.grid_propagate(False)
        self.rowconfigure((0,1,2), weight=1)
        self.columnconfigure(0, weight=1)

    def set_up_connection_thread(self):
        controlling_connection_thread = thr.Thread(target=handle_controlling_connection,args=(self.connect_code_var.get(),))
        controlling_connection_thread.start()
class MainScreenUtilitiesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.grid(row=2, column=0)  # change
        self.configure(width=parent.width,height=parent.height*0.4)  # change
        # self.configure(highlightthickness=1,highlightbackground='green')  # debug view
        self.update()


        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        incoming_title_label = ttk.Label(self,text="Incoming Requests", font=consolas(16))
        outgoing_title_label = ttk.Label(self,text="Outgoing Requests", font=consolas(16))
        recent_title_label = ttk.Label(self,text="Recent Sessions", font=consolas(16))
        incoming_title_label.grid(row=0,column=0)
        outgoing_title_label.grid(row=0,column=1)
        recent_title_label.grid(row=0,column=2)

        scrollable_incoming_canvas = CanvasScrollbarFrame(parent=self,row=1,column=0,width_multiplier=0.2, request_type="incoming")
        scrollable_outgoing_canvas = CanvasScrollbarFrame(parent=self,row=1,column=1,width_multiplier=0.2, request_type="outgoing")

    def dimensions(self):
        self.grid_rowconfigure(1,weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_propagate(False)


# Frame that encapsulates the ScrollableCanvasWidget and belongs to MainScreenUtilitiesFrame
class CanvasScrollbarFrame(tk.Frame):
    def __init__(self, *, parent, row, column, width_multiplier, request_type):
        super().__init__(parent)
        self.configure(width=parent.winfo_width()*width_multiplier)
        self.scrollable_canvas = ScrollableCanvasWidget(parent=self,width=parent.winfo_width() * width_multiplier,request_type=request_type)
        self.grid(row=row,column=column,sticky='nsew')
        self.update_idletasks()
        self.grid_propagate(False)

# Custom widget that is a combination of a scrollable canvas and a scrollbar.
# The scrollable frame inside is either a UtilitiesIncomingRequestsFrame or a UtilitiesOutgoingRequestsFrame
class ScrollableCanvasWidget(tk.Canvas):
    def __init__(self, *, parent, width, request_type):
        global incoming_requests_frame_obj, outgoing_requests_frame_obj
        super().__init__(parent)
        self.parent = parent
        self.configure(width=width)
        self.configure(highlightthickness=0)
        match request_type:
            case "incoming":
                self.scrollable_frame = UtilitiesIncomingRequestsFrame(self)
                incoming_requests_frame_obj = self.scrollable_frame
            case "outgoing":
                self.scrollable_frame = UtilitiesOutgoingRequestsFrame(self)
                outgoing_requests_frame_obj = self.scrollable_frame
            case _:
                raise Exception("Invalid request type (not incoming/outgoing)")

        self.create_window((0,0),window=self.scrollable_frame,anchor="nw")
        self.scrollable_frame.bind("<Configure>",self.on_frame_configure)

        self.scrollbar = ttk.Scrollbar(parent,orient="vertical",command=self.yview)
        self.configure(yscrollcommand=self.scrollbar.set)

        self.grid(row=0,column=0,sticky="nsew")
        self.scrollbar.grid(row=0,column=1,sticky="ns")

        # Bind mouse wheel events
        self.bind("<MouseWheel>",self.on_mouse_wheel)  # Windows
        self.bind("<Button-4>",self.on_mouse_wheel)  # Linux
        self.bind("<Button-5>",self.on_mouse_wheel)  # Linux

    def on_frame_configure(self, event):
        self.configure(scrollregion=self.bbox("all"))

    def on_mouse_wheel(self,event):
        # For Windows and macOS
        if event.delta:
            self.yview_scroll(int(-1 * (event.delta / 120)),"units")
        # For Linux (event.num is used instead of event.delta)
        elif event.num == 4:
            self.yview_scroll(-1,"units")
        elif event.num == 5:
            self.yview_scroll(1,"units")

class UtilitiesIncomingRequestsFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.grid(row=0, column=0) # change
        self.configure(highlightthickness=0)

        self.request_frames = []
        self.separator_frames: list[tk.Frame] = []

        self.create_widgets()
        self.dimensions()

    def add_request_frame(self, hostname_text,code_text,event,flag,_=None):
        separator_row = 2 * len(self.request_frames)
        request_frame_row = separator_row + 1
        separator = SeparatorFrame(self,self.parent.winfo_reqwidth() / 2,"grey")
        separator.grid(row=separator_row,column=0)
        request_frame = RequestFrame(parent=self,hostname_text=hostname_text,code_text=code_text,request_type="incoming",event=event,flag=flag)
        request_frame.grid(row=request_frame_row,column=0,sticky='ew',pady=5)
        self.request_frames.append(request_frame)
        self.separator_frames.append(separator)
        self.parent.on_frame_configure(None)

    def remove_request_frame(self, request_frame):
        request_frame_index = self.request_frames.index(request_frame)
        separator = self.separator_frames[request_frame_index]
        request_frame.grid_forget()
        separator.grid_forget()
        self.request_frames.remove(request_frame)
        self.separator_frames.remove(separator)
        self.update_frames()

    def update_frames(self):
        for i,(request_frame,separator) in enumerate(zip(self.request_frames,self.separator_frames)):
            separator_row = 2 * i
            frame_row = 2 * i + 1
            separator.grid(row=separator_row,column=0)
            request_frame.grid(row=frame_row,column=0,sticky='ew',pady=5)
        self.parent.on_frame_configure(None)

    def create_widgets(self):
        self.bind("<MouseWheel>",self.parent.on_mouse_wheel)  # Windows
        self.bind("<Button-4>",self.parent.on_mouse_wheel)  # Linux
        self.bind("<Button-5>",self.parent.on_mouse_wheel)  # Linux

    def dimensions(self):
        self.grid_columnconfigure(0, weight=1)

class UtilitiesOutgoingRequestsFrame(tk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        self.parent = parent
        self.grid(row=0,column=0)  # change
        # self.configure(width=parent.winfo_reqwidth(), height=parent.winfo_reqheight())
        self.configure(highlightthickness=0)

        self.request_frames = []
        self.separator_frames: list[tk.Frame] = []

        self.create_widgets()
        self.dimensions()

    def add_request_frame(self,hostname_text,code_text,event=None):
        separator_row = 2 * len(self.request_frames)
        request_frame_row = separator_row + 1
        separator = SeparatorFrame(self,self.parent.winfo_reqwidth() / 2,"grey")
        separator.grid(row=separator_row,column=0)
        event, flag = controlling_connection_thread_flags
        request_frame = RequestFrame(parent=self,hostname_text=hostname_text,code_text=code_text,request_type="outgoing", event=event, flag=flag)
        request_frame.grid(row=request_frame_row,column=0,sticky='ew',pady=5)
        self.request_frames.append(request_frame)
        self.separator_frames.append(separator)
        self.parent.on_frame_configure(None)
        return request_frame

    def remove_request_frame(self,request_frame):
        request_frame_index = self.request_frames.index(request_frame)
        separator = self.separator_frames[request_frame_index]
        request_frame.grid_forget()
        separator.grid_forget()
        self.request_frames.remove(request_frame)
        self.separator_frames.remove(separator)
        self.update_frames()

    def update_frames(self):
        for i,(request_frame,separator) in enumerate(zip(self.request_frames,self.separator_frames)):
            separator_row = 2 * i
            frame_row = 2 * i + 1
            separator.grid(row=separator_row,column=0)
            request_frame.grid(row=frame_row,column=0,sticky='ew',pady=5)
        self.parent.on_frame_configure(None)

    def create_widgets(self):
        self.bind("<MouseWheel>",self.parent.on_mouse_wheel)  # Windows
        self.bind("<Button-4>",self.parent.on_mouse_wheel)  # Linux
        self.bind("<Button-5>",self.parent.on_mouse_wheel)  # Linux

    def dimensions(self):
        self.grid_columnconfigure(0,weight=1)

# Frame that holds the widgets of each individual request to control/to be a remote
class RequestFrame(ttk.Frame):
    def __init__(self, *, parent, hostname_text, code_text, request_type, event, flag):
        super().__init__(parent)
        self.parent = parent
        self.hostname_text = hostname_text
        self.code_text = code_text
        self.configure(width=parent.parent.winfo_reqwidth(),height=70)
        self.request_type = request_type
        self.event = event
        self.flag = flag
        self.waiting_label = None
        self.loading_gif_label = None
        self.connect_button = None

        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        def accept_connection():
            self.flag.true()
            self.event.set()

        def deny_connection():
            self.flag.false()
            self.event.set()
            self.parent.remove_request_frame(self)

        hostname_label = ttk.Label(self, text=self.hostname_text,font=consolas(12))
        code_label = ttk.Label(self,text=self.code_text,font=consolas(12))

        hostname_label.grid(row=0,column=0)
        code_label.grid(row=1,column=0)

        match self.request_type:
            case "incoming":
                accept_button = ttk.Button(self, text="Accept",style=apply_consolas_to_widget("Button", 12, "green"), command=accept_connection)
                deny_button = ttk.Button(self,text="Deny",style=apply_consolas_to_widget("Button", 12, "red"),command=deny_connection)
                accept_button.grid(row=0,column=1,padx=3,pady=3)
                deny_button.grid(row=1,column=1,padx=3,pady=3)
                widgets = [hostname_label,code_label,accept_button,deny_button]
            case "outgoing":
                self.waiting_label = ttk.Label(self, text="Waiting",font=consolas(10))
                self.loading_gif_label = AnimatedGIF(self,"assets/loading.gif",size=(25,25))
                self.connect_button = ttk.Button(self,text="Connect",style=apply_consolas_to_widget("Button", 12, "green"),width=7,command=self.accept_control)
                self.waiting_label.grid(row=0,column=1,padx=20,sticky='e')
                self.loading_gif_label.grid(row=1,column=1,padx=20,sticky='e')
                self.connect_button.grid(row=0,column=1,rowspan=2,padx=20,sticky='e')
                self.connect_button.grid_remove()
                widgets = [hostname_label,code_label,self.waiting_label,self.loading_gif_label,self.connect_button]
            case _:
                raise Exception("Invalid request type (not incoming/outgoing)")

        for widget in widgets:
            widget.bind("<MouseWheel>",self.parent.parent.on_mouse_wheel)  # Windows
            widget.bind("<Button-4>",self.parent.parent.on_mouse_wheel)  # Linux
            widget.bind("<Button-5>",self.parent.parent.on_mouse_wheel)  # Linux

        self.bind("<MouseWheel>",self.parent.parent.on_mouse_wheel)  # Windows
        self.bind("<Button-4>",self.parent.parent.on_mouse_wheel)  # Linux
        self.bind("<Button-5>",self.parent.parent.on_mouse_wheel)  # Linux

    def dimensions(self):
        self.grid_rowconfigure((0,1), weight=1)
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_propagate(False)

    def switch_to_connect_button(self):
        self.waiting_label.grid_remove()
        self.loading_gif_label.grid_remove()
        self.connect_button.grid()

    def accept_control(self):
        self.parent.remove_request_frame(self)
        wm.open_share_screen()


# Frame that acts as a separator between RequestFrame's
class SeparatorFrame(tk.Frame):
    def __init__(self, parent, width, colour):
        super().__init__(parent)
        self.parent = parent
        self.width = width
        self.colour = colour
        self.configure(background=colour)
        self.configure(width=width, height=1)
        self.bind("<MouseWheel>",self.parent.parent.on_mouse_wheel)  # Windows
        self.bind("<Button-4>",self.parent.parent.on_mouse_wheel)  # Linux
        self.bind("<Button-5>",self.parent.parent.on_mouse_wheel)  # Linux

# Label that breaks down a gif into multiple images and displays them, seeming like a gif.
# todo: get this out of here, possibly into a new classes.py
class AnimatedGIF(tk.Label):
    def __init__(self, parent, path, size=None, *args, **kwargs):
        super().__init__(parent,*args,**kwargs)
        self.path = path
        self.size = size
        self.frames = self.load_frames()
        self.current_frame = 0
        self._job = None
        self.update_animation()

    def load_frames(self):
        frames = []
        gif = Image.open(self.path)
        for frame in ImageSequence.Iterator(gif):
            if self.size is not None:
                frame = frame.resize(self.size, Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(frame))
        return frames

    def update_animation(self):
        self.configure(image=self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self._job = self.after(100, self.update_animation)

    def destroy(self):
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        super().destroy()


class ShareScreen(tk.Tk):
    def __init__(self, remote: Remote):
        # Simple configuration and variable loading
        super().__init__()
        self.remote = remote
        self.title("Share - Contrology")

        # Complex configuration
        screen_width, screen_height = get_resolution_of_primary_monitor()
        self.geometry(f"{screen_width}x{screen_height}")
        self.attributes('-fullscreen', True)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW",on_main_close) # todo: consider changing to opening the main screen again

        # Widgets
        info_frame_height = 80
        canvas_height = screen_height - info_frame_height
        self.info_frame = ShareScreenInfoFrame(self, info_frame_height, self.remote)
        self.info_frame.pack(side="top",fill="x")
        self.canvas_frame = ShareScreenCanvasFrame(self, canvas_height, self.remote)
        self.canvas_frame.pack(fill="both", expand=True)

        # Functions
        self.dimensions()

    def dimensions(self):
        pass

class ShareScreenInfoFrame(tk.Frame):
    def __init__(self, parent, height: int, remote: Remote):
        super().__init__(parent)
        self.parent = parent
        self.configure(height=height, width=SCREEN_WIDTH)
        self.remote = remote

        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        now_controlling_label = ttk.Label(self, text="Now controlling", font=consolas(10))
        hostname_label = ttk.Label(self, text=self.remote.hostname, font=consolas(12))
        code_label = ttk.Label(self, text=self.remote.code, font=consolas(12))

        now_controlling_label.grid(row=0,column=0)
        hostname_label.grid(row=1, column=0)
        code_label.grid(row=2, column=0)

    def dimensions(self):
        self.grid_rowconfigure((0,1,2), weight=1)

class ShareScreenCanvasFrame(ttk.Frame):
    def __init__(self, parent, height: int, remote: Remote):
        super().__init__(parent)
        self.parent = parent
        self.remote = remote
        self.height = height
        self.width = SCREEN_WIDTH
        self.configure(height=self.height, width=self.width)

        self.canvas: Optional[tk.Canvas] = None
        self.canvas_image_id = None
        self.display_image = None
        self.scale_factor = min(self.width / remote.res_width,self.height / remote.res_height)
        ic(self.scale_factor)
        self.resized_width = int(self.remote.res_width * self.scale_factor)
        self.resized_height = int(self.remote.res_height * self.scale_factor)
        ic(self.resized_width, self.resized_height)
        self.image_x_offset = (self.width-self.resized_width) // 2
        self.image_y_offset = (self.height-self.resized_height) // 2

        self.dimensions()
        self.create_widgets()

        self.update_image_thread = thr.Thread(target=self.load_latest_image,daemon=True)
        self.update_image_thread.start()

    def create_widgets(self):
        self.canvas = tk.Canvas(self, bg="black", width=self.width, height=self.height)
        self.canvas.pack(fill="both",expand=True)
        default_image = Image.new('RGB', (self.remote.res_width, self.remote.res_height), (0,0,0))
        default_image.resize((self.resized_width, self.resized_height), Image.Resampling.LANCZOS)
        self.display_image = ImageTk.PhotoImage(default_image)
        self.canvas_image_id = self.canvas.create_image(self.width // 2,self.height // 2,anchor="center",image=self.display_image)
        self.canvas.bind("<Button-1>",self.on_canvas_event)
        self.canvas.bind_all("<KeyPress>",self.on_canvas_event)

    def load_latest_image(self):
        # todo: add checks to make sure that the remote is still connected
        while accept_data and connected:
            with data_handler_lock:
                new_image = d_handler.get_last_image()
            new_image = Image.frombytes("RGB", (self.remote.res_width, self.remote.res_height), new_image)
            new_image = new_image.resize((self.resized_width, self.resized_height),Image.Resampling.LANCZOS)
            self.display_image = ImageTk.PhotoImage(new_image)
            self.canvas.itemconfig(self.canvas_image_id, image=self.display_image)
            self.canvas.image = self.display_image

    def on_canvas_event(self, event):
        if event.type == tk.EventType.ButtonPress:  # Mouse click
            x, y = event.x, event.y
            # Calculate the coordinates relative to the image
            image_x = x - self.image_x_offset
            image_y = y - self.image_y_offset

            # Check if the click is within the image bounds
            if 0 <= image_x < self.resized_width and 0 <= image_y < self.resized_height:
                # Map the coordinates to the original image
                original_x,original_y = map_coords_to_original(image_x,image_y,self.scale_factor)
                print(f"Scaled Coordinates: ({image_x}, {image_y})")
                print(f"Original Coordinates: ({original_x}, {original_y})")  # where the remote needs to simulate a click
                control_event_data = ControlEvent(click=True, coordinates=(original_x, original_y))
                control_event_data = pickle.dumps(control_event_data)
                ic()
                with data_handler_lock:
                    d_handler.insert_new_outgoing_message(
                        create_sendable_data(control_event_data, "CONTROL_EVENT", self.remote.code, pickled=True))
                    ic()

        if event.type == tk.EventType.KeyPress:  # Keyboard press
            control_event_data = ControlEvent(keypress=True, key=event.char)
            ic(control_event_data)
            control_event_data = pickle.dumps(control_event_data)
            with data_handler_lock:
                d_handler.insert_new_outgoing_message(
                    create_sendable_data(control_event_data,"CONTROL_EVENT",self.remote.code, pickled=True))

    def dimensions(self):
        pass


class AdminScreen(tk.Tk):
    def __init__(self):
        # Simple configuration and variable loading
        super().__init__()
        self.title("Admin - Contrology")

        # Complex configuration
        self.width, self.height = 1200, 800
        self.geometry(get_geometry_string(self.width, self.height))
        #self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW",on_main_close)

        # Widgets
        self.title_frame = AdminScreenTitleFrame(self)
        self.info_frame = AdminScreenInfoFrame(self)
        self.content_frame = AdminScreenContentFrame(self)

        self.title_frame.grid(row=0,column=0)
        self.info_frame.grid(row=0,column=1)
        self.content_frame.grid(row=1,column=0,columnspan=2)
        self.update_idletasks()

        # Functions
        self.dimensions()

    def dimensions(self):
        pass

class AdminScreenTitleFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(highlightthickness=1, highlightbackground='green')
        self.width, self.height = int(parent.width*3/4),int(parent.height*3/20)
        self.configure(width=self.width, height=self.height)
        self.admin_logo = ImageTk.PhotoImage(Image.open("assets/admin_logo.png"))

        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        # todo: if you wish to add space between the logo and the label, prompt chatgpt for style with the padding configuration.
        title_label = ttk.Label(self, text="Administrator Panel", image=self.admin_logo, compound='left', font=consolas(36))
        title_label.grid(row=0,column=0)

    def dimensions(self):
        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0,weight=1)
        self.grid_propagate(False)

class AdminScreenInfoFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(highlightthickness=1, highlightbackground='red')
        self.width, self.height = int(parent.width*1/4),int(parent.height*3/20)
        self.configure(width=self.width,height=self.height)

        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        # todo: if changing Remote to UserInfo class, use the described helper function to fetch the information here
        hostname_label = ttk.Label(self, text=socket.gethostname(), font=consolas(16))
        code_label = ttk.Label(self, text=self_code,font=consolas(16))
        administrator_label = ttk.Label(self, text="Administrator", font=consolas(12), foreground='grey')

        hostname_label.grid(row=0,column=0,sticky='s')
        code_label.grid(row=1,column=0,sticky='n')
        administrator_label.grid(row=2,column=0)


    def dimensions(self):
        self.grid_rowconfigure((0,1), weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)

class AdminScreenContentFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(highlightthickness=1, highlightbackground='blue')
        self.width, self.height = parent.width,int(parent.height*17/20)
        self.configure(width=self.width,height=self.height)

        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        notebook = AdminScreenNotebook(self)
        notebook.pack(fill="both",expand=True)

    def dimensions(self):
        self.pack_propagate(False)

class AdminScreenNotebook(ttk.Notebook):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=consolas(14))
        style.map("TNotebook.Tab", foreground=[("!selected", "grey")])
        self.enable_traversal()

        self.configure(style="TNotebook")
        self.logs_tab = None
        self.users_tab = None
        self.logs_tab_logo = ImageTk.PhotoImage(Image.open("assets/logs_icon.png"))
        self.users_tab_logo = ImageTk.PhotoImage(Image.open("assets/users_icon.png"))
        self.loaded_initial_logs = False
        self.loaded_initial_users = False

        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        self.logs_tab = AdminScreenNotebookLogs(self)
        self.users_tab = AdminScreenNotebookUsers(self)

        self.add(self.logs_tab, text="Logs", image=self.logs_tab_logo, compound='left')
        self.add(self.users_tab, text="Users", image=self.users_tab_logo, compound='left')

        self.bind("<<NotebookTabChanged>>", self.on_tab_change)

        self.select(self.logs_tab)

    def on_tab_change(self,event):
        if not self.loaded_initial_logs or not self.loaded_initial_users:
            notebook = event.widget
            selected_tab = notebook.select()
            new_tab = notebook.tab(selected_tab,"text")
            match new_tab:
                case "Logs":
                    if not self.loaded_initial_logs:
                        with data_handler_lock:
                            d_handler.insert_new_outgoing_message(create_sendable_data(b"", "DB_LOGS_REQUEST", SERVER_CODE))
                case "Users":
                    if not self.loaded_initial_users:
                        with data_handler_lock:
                            d_handler.insert_new_outgoing_message(create_sendable_data(b"", "DB_USERS_REQUEST", SERVER_CODE))
                case _:
                    raise Exception("Switched to unfamiliar tab")

    def dimensions(self):
        pass

# This frame takes up the entire space of the Logs tab in the Admin Notebook.
# This frame encapsulates two frames.
# The first frame contains the scrollable canvas which contains a canvas and a scrollbar.
# This canvas contains the table of data.
# The second frame is the suite of options that be committed on the Logs table.
class AdminScreenNotebookLogs(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.update_idletasks()

        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        scrollable_table_frame = ScrollableTableFrame(self, "Logs")
        scrollable_table_frame.pack(side="left", fill="both", expand=True)
        options = OptionsFrame(self)
        options.pack(side="right", fill="y")

    def dimensions(self):
        pass

class ScrollableTableFrame(tk.Frame):
    def __init__(self, parent, table_name):
        super().__init__(parent)
        self.parent = parent
        self.table_name = table_name
        self.configure(highlightthickness=1, highlightbackground='purple')


        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        scrollable_table_canvas = ScrollableTableCanvas(parent=self, table_name=self.table_name)

    def dimensions(self):
        pass


class ScrollableTableCanvas(tk.Canvas):
    def __init__(self, *, parent, table_name):
        global logs_table_obj
        super().__init__(parent)
        self.parent = parent
        self.table_name = table_name
        self.configure(highlightthickness=0)
        idata = []
        for i in range(100):
            idata.append(gen_random_record())
        self.scrollable_frame = Table(self, ["ID", "Timestamp", "U.ID", "U.Hostname", "Action", "TU.ID", "TU.Hostname"], [])
        match table_name:
            case "Logs":
                logs_table_obj = self.scrollable_frame

        self.create_window((0,0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)

        self.yscrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.yview)
        self.configure(yscrollcommand=self.yscrollbar.set)
        self.xscrollbar = ttk.Scrollbar(parent, orient="horizontal", command=self.xview)
        self.configure(xscrollcommand=self.xscrollbar.set)

        self.yscrollbar.pack(side="right",fill="y")
        self.xscrollbar.pack(side="bottom",fill="x")
        self.pack(side="left",fill="both",expand=True)


        # Bind mouse wheel events
        bind_to_hierarchy(self, "<MouseWheel>", self.on_mouse_wheel)
        # self.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.bind("<Button-4>", self.on_mouse_wheel)  # Linux
        self.bind("<Button-5>", self.on_mouse_wheel)  # Linux

    def on_frame_configure(self, event):
        self.configure(scrollregion=self.bbox("all"))

    def on_mouse_wheel(self, event):
        # Only scroll if the scrollbar is active (-> there is actually content to scroll)
        if "disabled" not in self.yscrollbar.state():
            # For Windows and macOS
            if event.delta:
                self.yview_scroll(int(-1 * (event.delta / 120)), "units")
            # For Linux (event.num is used instead of event.delta)
            elif event.num == 4:
                self.yview_scroll(-1, "units")
            elif event.num == 5:
                self.yview_scroll(1, "units")

class ColumnsFrame(tk.Frame):
    def __init__(self, parent, columns: list[str]):
        super().__init__(parent)
        self.parent = parent
        self.columns = columns
        self.column_label_widgets: list[tk.Label] = []
        #self.configure(highlightthickness=1, highlightbackground='red')
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
        #self.configure(highlightthickness=1, highlightbackground='blue')
        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        for idx, datum in enumerate(self.data):
            datum = tk.Label(self, text=str(datum), highlightthickness=1, highlightbackground="black", font=consolas(16))
            datum.grid(row=0,column=idx)
            self.data_label_widgets.append(datum)

    def dimensions(self):
        pass

class Table(tk.Frame):
    def __init__(self, parent, column_headings: list[str], initial_data: list[list[str]]):
        print(f"table init at {time()-t}")
        super().__init__(parent)
        self.parent = parent
        self.configure(highlightthickness=1, highlightbackground='green')
        self.columns_frame = None
        self.data_frames = []
        self.column_headings = column_headings
        self.initial_data = initial_data
        self.dimensions()
        self.create_widgets()

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
        print(f"pushing data at {time()-t}")
        for idx, datum in enumerate(data):
            data_frame = DataFrame(self, datum)
            data_frame.grid(row=len(self.data_frames)+1, column=0, sticky='ew')
            self.data_frames.append(data_frame)
            bind_to_hierarchy(data_frame,"<MouseWheel>",self.parent.on_mouse_wheel)
        self.set_labels_to_highest_width()
        print(f"finished pushing data at {time()-t}")

    def remove_data_from_table(self, data_frame: DataFrame):
        data_frame.grid_forget()
        self.data_frames.remove(data_frame)
        self.reload_table_data()

    def reload_table_data(self):
        print(f"reloading table at {time()-t}")
        # todo: if columns need reloading too, do that here
        for data_frame in self.data_frames:
            data_frame.grid_forget()
        for idx, data_frame in enumerate(self.data_frames):
            data_frame.grid(row=idx+1, column=0, sticky='ew')
        self.set_labels_to_highest_width()




    def dimensions(self):
        self.grid_columnconfigure(0, weight=1)


class OptionsFrame(tk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        self.width = int(parent.parent.parent.width * 1/6) # the widget mentioned here is the content frame
        self.configure(highlightthickness=1,highlightbackground='pink')
        self.configure(width=self.width)
        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        pass

    def dimensions(self):
        self.grid_propagate(False)

class AdminScreenNotebookUsers(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.dimensions()
        self.create_widgets()

    def create_widgets(self):
        pass

    def dimensions(self):
        pass


if __name__ == "__main__":
    general_connection_thread = thr.Thread()
    track = thr.Thread(target=trackvar, daemon=True)
    track.start()
    d_handler = DataHandler()
    current_remote = Remote()
    wm = WindowManager()
    wm.open_launch_screen()
