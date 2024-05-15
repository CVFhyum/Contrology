import base64

from functions import *
from constants import *
from configuration import *

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import socket
import threading as thr
import select
from typing import Optional

self_code = ""
incoming_data = ""
accept_data = True

class WindowManager:
    def __init__(self):
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
        if wm.launch_screen_root is not None:
            wm.launch_screen_root.destroy()
        if wm.main_screen_root is not None:
            wm.main_screen_root.destroy()


def handle_connection():
    global self_code, incoming_data
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
        c.connect((SERVER_IP, SERVER_PORT))
        self_code = c.recv(RECIPIENT_HEADER_LENGTH).decode()
        ic(self_code)
        c.setblocking(False)
        while accept_data:
            try:
                ready = select.select([c],[],[], 1)
                if ready[0]:
                    header = c.recv(HEADER_LENGTH)
                    if header:
                        data_length,code = parse_header(header)
                        data = parse_raw_data(recvall(c,data_length))
                        if code == self_code or code == ALL_CODE:
                            incoming_data = data
                            ic(len(incoming_data))
                        else:
                            raise Exception("Intended code didn't match with self code")
                    else:
                        break
            except ConnectionResetError as e:
                print(f"Something went wrong with the connection: {e}")
            except KeyboardInterrupt:
                print("Runtime interrupted...")
                c.close()
                break

        c.close()

def on_main_close():
    global accept_data
    wm.close_all()
    accept_data = False


# todo: make on_closing function using root.protocol to handle explicit quit gracefully
# banner = ImageTk.PhotoImage(Image.open("assets/Banner.png"))
# banner_trans = ImageTk.PhotoImage(Image.open("assets/Banner_Trans.png"))
# logo = ImageTk.PhotoImage(Image.open("assets/Logo.png"))
# logo32 = ImageTk.PhotoImage(Image.open("assets/Logo32.png"))

def consolas(size):
    return "Consolas", size

# https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/ttk-style-layer.html
# todo: doc
def apply_consolas_to_widget(widget_type, size):
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


        # Creation
        launch_app_button = ttk.Button(self,text="Launch App", style=apply_consolas_to_widget("Button", 32), command=lambda: [client_thread.start(), wm.open_main_screen()])
        admin_log_in_button = ttk.Button(self, text="Administrator Log In", style=apply_consolas_to_widget("Button", 12), command=switch_admin_widgets)
        admin_password_entry = ttk.Entry(self, textvariable=self.admin_password_entry_var, style='grey.TEntry',font=consolas(13))

        # Placement
        launch_app_button.grid(row=0,column=0)
        admin_log_in_button.grid(row=1,column=0)
        admin_password_entry.grid(row=1,column=0)
        admin_password_entry.grid_remove()  # Remove it at initialization because it should only appear when the entry is pressed

        # Bindings
        admin_password_entry.bind("<FocusIn>",admin_password_entry_focus_in)
        admin_password_entry.bind("<FocusOut>",admin_password_entry_focus_out)
        admin_password_entry.bind("<Return>",admin_password_entry_handle_enter)
        admin_password_entry.bind("<Escape>",switch_admin_widgets)

    def dimensions(self):
        self.grid_propagate(False)
        self.rowconfigure((0,1), weight=1)
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
        self.my_code_value_var = tk.StringVar()
        self.my_code_value_var.set("Asiw93mska")

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        main_banner = ttk.Label(self, image=self.banner_trans)
        code_container_frame = tk.Frame(self, highlightthickness=1, highlightbackground='green', height=self.winfo_height(), width=self.winfo_reqwidth()/2)
        code_container_frame.grid_propagate(False)
        my_code_info_label = ttk.Label(code_container_frame, text="My Code")
        my_code_value_label = ttk.Label(code_container_frame, textvariable=self.my_code_value_var)
        my_code_click_to_copy_label = ttk.Label(code_container_frame, text="(Click to Copy)")

        main_banner.grid(row=0,column=0)
        code_container_frame.grid(row=0,column=1)
        my_code_info_label.grid(row=0,column=0)
        my_code_value_label.grid(row=1,column=0)
        my_code_click_to_copy_label.grid(row=2,column=0)

    def dimensions(self):
        self.grid_propagate(False)

class MainScreenConnectFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid(row=1, column=0)  # change
        self.configure(width=parent.width,height=parent.height*0.4)  # change
        self.configure(highlightthickness=1,highlightbackground='green')  # debug view

        self.create_widgets()
        self.dimensions()

    def create_widgets(self):
        pass

    def dimensions(self):
        self.grid_propagate(False)


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
    client_thread = thr.Thread(target=handle_connection)
    wm = WindowManager()
    wm.open_launch_screen()

