import tkinter as tk
from tkinter import ttk
from PIL import Image,ImageTk


def on_image_click(event):
    # Get the coordinates relative to the canvas
    canvas_x,canvas_y = event.x,event.y

    # Calculate the coordinates relative to the image
    image_x = canvas_x - image_x_offset
    image_y = canvas_y - image_y_offset

    # Check if the click is within the image bounds
    if 0 <= image_x < new_width and 0 <= image_y < new_height:
        # Map the coordinates to the original image
        original_x,original_y = map_coords_to_original(image_x,image_y,scale_factor)
        print(f"Scaled Coordinates: ({image_x}, {original_y})")
        print(f"Original Coordinates: ({original_x}, {original_y})")
    else:
        print("Click outside the image bounds")


def map_coords_to_original(scaled_x,scaled_y,scale_factor):
    original_x = int(scaled_x / scale_factor)
    original_y = int(scaled_y / scale_factor)
    return original_x,original_y


def create_main_window():
    global image_x_offset,image_y_offset,scale_factor,new_width,new_height,remote_screen_width,remote_screen_height

    root = tk.Tk()
    root.title("Remote Control Viewer")

    # Controller's screen dimensions
    controller_screen_width = 1920
    controller_screen_height = 1080

    # Remote screen dimensions
    remote_screen_width = 1920
    remote_screen_height = 1080

    # Toolbar height
    toolbar_height = 50

    # Calculate the available canvas size
    canvas_width = controller_screen_width
    canvas_height = controller_screen_height - toolbar_height

    # Create the window with the specified size
    root.geometry(f"{controller_screen_width}x{controller_screen_height}")
    root.attributes("-fullscreen", True)

    # Create a frame for the toolbar
    toolbar_frame = ttk.Frame(root,height=toolbar_height)
    toolbar_frame.pack(side=tk.TOP,fill=tk.X)

    # Add some buttons to the toolbar for demonstration
    ttk.Button(toolbar_frame,text="Tool 1").pack(side=tk.LEFT,padx=5,pady=5)
    ttk.Button(toolbar_frame,text="Tool 2").pack(side=tk.LEFT,padx=5,pady=5)
    ttk.Button(toolbar_frame,text="Tool 3").pack(side=tk.LEFT,padx=5,pady=5)

    # Create a canvas for displaying the remote screen content
    canvas_frame = ttk.Frame(root)
    canvas_frame.pack(fill=tk.BOTH,expand=True)

    remote_canvas = tk.Canvas(canvas_frame,bg="black")
    remote_canvas.pack(fill=tk.BOTH,expand=True)

    # Load the remote screen image (dummy image used here, replace with actual remote screen image)
    remote_image = Image.open("../assets/9c7be43979a736a8695361a544630b97.png")

    # Scale the image to fit within the canvas while maintaining the aspect ratio
    scale_factor = min(canvas_width / remote_screen_width,canvas_height / remote_screen_height)
    new_width = int(remote_screen_width * scale_factor)
    new_height = int(remote_screen_height * scale_factor)
    scaled_image = remote_image.resize((new_width,new_height),Image.Resampling.LANCZOS)

    # Calculate the offsets to center the image
    image_x_offset = (canvas_width - new_width) // 2
    image_y_offset = (canvas_height - new_height) // 2

    # Convert the image to PhotoImage
    photo_image = ImageTk.PhotoImage(scaled_image)

    # Display the scaled image on the canvas
    remote_canvas.create_image(canvas_width // 2,canvas_height // 2,image=photo_image,anchor=tk.CENTER)

    # Bind the click event to the canvas
    remote_canvas.bind("<Button-1>",on_image_click)

    # Keep a reference to the image to prevent garbage collection
    remote_canvas.image = photo_image

    root.mainloop()


if __name__ == "__main__":
    create_main_window()
