from functions import *
from constants import *
from configuration import *
from data_handler import DataHandler

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageSequence
import socket
import threading as thr
import select
from typing import Optional, Any
from pyperclip import copy as cc_copy
from time import sleep
from random import randint as ri
from mss.windows import MSS

# Global variables that can be accessed all throughout the code
self_code = ""  # This client's code
data_handler_lock = thr.Lock()  # Lock to prevent race conditions on the DataHandler obj
accept_data = True  # Flag that is disabled when the client is interrupted or quits. This will make sure that necessary information-receiving threads are stopped.
connected = False  # Flag that documents if the client is currently connected to the socket.
incoming_requests_frame_obj: Any = None
outgoing_requests_frame_obj: Any = None
connect_feedback_var: Optional[tk.StringVar] = None
controlling_connection_thread_flags = thr.Event(), FlagObject(False)
code_flags = thr.Event(), FlagObject(False)
remote_connection_thread_flags = {}
remote_thread_id = 0

wait_for_connection_response = thr.Event()
control_permission_granted = False  # Flag that signifies permission to control a remote.

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
class WindowManager:
    def __init__(self):
        # Optional[tk.Tk] -> tk.Tk or None
        self._launch_screen_root: Optional[tk.Tk] = None
        self._main_screen_root: Optional[tk.Tk] = None
        self._share_screen_root: Optional[tk.Tk] = None

    @property
    def launch_screen_root(self):
        return self._launch_screen_root

    @launch_screen_root.setter
    def launch_screen_root(self,value):
        if value is not None and self.launch_screen_root is not None:
            raise ValueError("Launch Screen Root modify attempt failed")
        self._launch_screen_root = value

    @property
    def main_screen_root(self):
        return self._main_screen_root

    @main_screen_root.setter
    def main_screen_root(self,value):
        if value is not None and self.main_screen_root is not None:
            raise ValueError("Main Screen Root modify attempt failed")
        self._main_screen_root = value

    @property
    def share_screen_root(self):
        return self._share_screen_root

    @share_screen_root.setter
    def share_screen_root(self,value):
        if value is not None and self.share_screen_root is not None:
            raise ValueError("Share Screen Root modify attempt failed")
        self._share_screen_root = value

    def open_launch_screen(self):
        if self.main_screen_root is not None:
            self.main_screen_root.destroy()
            self.main_screen_root = None
        if self.share_screen_root is not None:
            self.share_screen_root.destroy()
            self.share_screen_root = None
        self.launch_screen_root = LaunchScreen()
        self.launch_screen_root.mainloop()

    def open_main_screen(self):
        if self.launch_screen_root is not None:
            self.launch_screen_root.destroy()
            self.launch_screen_root = None
        if self.share_screen_root is not None:
            self.share_screen_root.destroy()
            self.share_screen_root = None
        self.main_screen_root = MainScreen()
        self.main_screen_root.mainloop()

    def open_share_screen(self):
        if self.launch_screen_root is not None:
            self.launch_screen_root.destroy()
            self.launch_screen_root = None
        if self.main_screen_root is not None:
            self.main_screen_root.destroy()
            self.main_screen_root = None
        self.share_screen_root = ShareScreen()
        self.share_screen_root.mainloop()

    def update_all(self):
        if self.launch_screen_root is not None:
            self.launch_screen_root.update()
        if self.main_screen_root is not None:
            self.main_screen_root.update()
        if self.share_screen_root is not None:
            self.main_screen_root.update()

    def close_all(self):
        if self.launch_screen_root is not None:
            self.launch_screen_root.destroy()
        if self.main_screen_root is not None:
            self.main_screen_root.destroy()
        if self.share_screen_root is not None:
            self.share_screen_root.destroy()


# When the "Launch App" button is pressed, and a connection is established, this function starts in a thread.
# This thread takes care of receiving incoming data from the server and loading it into incoming_data
def handle_general_connection(c: socket.socket):
    global self_code, connected, accept_data, control_permission_granted, remote_thread_id
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
                        data = parse_raw_data(recvall(c,data_length))
                        if code == self_code or code == ALL_CODE:
                            with data_handler_lock:
                                match data_type:
                                    case "CONNECT_REQUEST":
                                        requester_code, requester_hostname = data[:RECIPIENT_HEADER_LENGTH], data[RECIPIENT_HEADER_LENGTH:]
                                        remote_connection_thread = thr.Thread(target=handle_remote_connection, args=(requester_code, requester_hostname, remote_thread_id))
                                        remote_connection_thread_flags.update({remote_thread_id: (thr.Event(),FlagObject(False))})
                                        remote_connection_thread.start()
                                        remote_thread_id += 1
                                        # TODO: instantly accepting if a request is sent currently, handle that here.
                                        # permission_granted = True
                                        # if permission_granted:
                                        #     d_handler.insert_new_outgoing_message((create_sendable_data(b"", "CONNECT_ACCEPT", requester_code)))
                                        # else:
                                        #     d_handler.insert_new_outgoing_message((create_sendable_data(b"","CONNECT_DENY",requester_code)))
                                        # d_handler.insert_new_incoming_message((data_type, data)) # TODO: change this if decide to use connec requests attr in dhandler
                                    case "CONNECT_ACCEPT":
                                        event, flag = controlling_connection_thread_flags
                                        event.set()
                                        flag.true()
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
        print("You clicked yes!")
        with MSS() as mss_obj:
            while True:
                screenshot_bytes = get_screenshot_bytes(mss_obj, 0, 0, 1920, 1080)
                screenshot_data = create_sendable_data(screenshot_bytes, "IMAGE",controller_code)
                d_handler.insert_new_outgoing_message(screenshot_data)
    else:
        d_handler.insert_new_outgoing_message((create_sendable_data(b"","CONNECT_DENY",controller_code)))
        del remote_connection_thread_flags[thread_name]


# Handles requesting control of another machine
def handle_controlling_connection(remote_code):
    if remote_code == self_code:
        raise Exception("Self code was given") # TODO: make this part of the code not raise an error, but change a label in tkinter
    # TODO: make sure that the same machine isn't receiving a request multiple times
    with data_handler_lock:
        d_handler.insert_new_outgoing_message(create_sendable_data(b"","CONNECT_REQUEST",remote_code))
    code_event, code_flag = code_flags
    event,flag = controlling_connection_thread_flags
    code_event.wait()
    if code_flag:
        outgoing_requests_frame_obj.add_request_frame("Unknown",remote_code)
        event.wait()
        event.clear()
        if flag:
            print("Permission granted!")
            ic()
            wm.open_share_screen()
            ic()
        else:
            connect_feedback_var.set("Request was denied.")
    else:
        # TODO:  display code not found in tkinter
        connect_feedback_var.set("Code not found.")
    sleep(2)
    connect_feedback_var.set("")






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
def apply_consolas_to_widget(widget_type: str, size: int, colour: Optional[str] = None) -> str:
    s = ttk.Style()
    style_string = f'{size}{colour}.T{widget_type}'
    s.configure(style_string, font=consolas(size))
    if colour is not None:
        s.configure(style_string, foreground=colour)
    return style_string


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
        # Takes care of swapping the button widget with the entry widget on the launch screen
        def switch_admin_widgets(_=None):
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

        # When Enter is pressed while the password entry has focus, this callback is invoked. It verifies the password and TODO: tells the wm to open the admin screen.
        def admin_password_entry_handle_enter(_=None):
            # todo: handle the entered password (verify it)
            print(self.admin_password_entry_var.get())

        def try_to_connect():
            global connected, general_connection_thread
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
            general_connection_thread = thr.Thread(target=handle_general_connection,args=(sock,))
            general_connection_thread.start()
            wm.open_main_screen()

        """ Creation """
        launch_app_button = ttk.Button(self,text="Launch App", style=apply_consolas_to_widget("Button", 32), command=try_to_connect)
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
        ic()
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
        # self.configure(width=parent.winfo_reqwidth(), height=parent.winfo_reqheight())
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
        self.configure(highlightthickness=1, highlightcolor='green')

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

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        hostname_label = ttk.Label(self, text=self.hostname_text,font=consolas(12))
        code_label = ttk.Label(self,text=self.code_text,font=consolas(12))

        hostname_label.grid(row=0,column=0)
        code_label.grid(row=1,column=0)

        match self.request_type:
            case "incoming":
                accept_button = ttk.Button(self, text="Accept",style=apply_consolas_to_widget("Button", 12, "green"), command=lambda: [self.event.set(), self.flag.true()])
                deny_button = ttk.Button(self,text="Deny",style=apply_consolas_to_widget("Button", 12, "red"),command=lambda: [self.event.set(), self.flag.false(), self.parent.remove_request_frame(self)])
                accept_button.grid(row=0,column=1,padx=3,pady=3)
                deny_button.grid(row=1,column=1,padx=3,pady=3)
                widgets = [hostname_label,code_label,accept_button,deny_button]
            case "outgoing":
                waiting_label = ttk.Label(self, text="Waiting...",font=consolas(10))
                loading_gif_label = AnimatedGIF(self,"assets/loading.gif",size=(25,25))
                waiting_label.grid(row=0,column=1,padx=3,pady=3,sticky='e')
                loading_gif_label.grid(row=1,column=1,padx=3,pady=3,sticky='e')
                widgets = [hostname_label,code_label,waiting_label,loading_gif_label]
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
        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)

# Frame that acts as a separator between RequestFrame's/
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
class AnimatedGIF(tk.Label):
    def __init__(self, parent, path, size=None, *args, **kwargs):
        super().__init__(parent,*args,**kwargs)
        self.path = path
        self.size = size
        self.frames = self.load_frames()
        self.current_frame = 0
        self.update_animation()

    def load_frames(self):
        frames = []
        gif = Image.open(self.path)
        for frame in ImageSequence.Iterator(gif):
            if self.size:
                frame = frame.resize(self.size, Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(frame))
        return frames

    def update_animation(self):
        self.configure(image=self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.after(100, self.update_animation)


class ShareScreen(tk.Tk):
    def __init__(self):
        # Simple configuration and variable loading
        super().__init__()
        self.title("Share - Contrology")

        # Complex configuration
        screen_width, screen_height = get_resolution_of_primary_monitor()
        self.geometry(f"{screen_width}x{screen_height}")
        self.attributes('-fullscreen', True)
        # self.resizable(False, False) # todo: removed for debug
        self.protocol("WM_DELETE_WINDOW",on_main_close) # todo: consider changing to opening the main screen again

        # Widgets
        pass

        # Functions
        self.dimensions()

    def dimensions(self):
        pass


if __name__ == "__main__":
    general_connection_thread = thr.Thread()
    track = thr.Thread(target=trackvar, daemon=True)
    track.start()
    d_handler = DataHandler()
    wm = WindowManager()
    wm.open_launch_screen()
