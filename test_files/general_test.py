import tkinter as tk

# Create the main window
root = tk.Tk()
root.title("Grid Manager Example")

# Create labels to demonstrate columnspan and rowspan
label1 = tk.Label(root, text="Label 1", bg="lightblue", padx=10, pady=10)
label2 = tk.Label(root, text="Label 2", bg="lightgreen", padx=10, pady=10)
label3 = tk.Label(root, text="Label 3", bg="lightyellow", padx=10, pady=10)
label4 = tk.Label(root, text="Label 4", bg="lightpink", padx=10, pady=10)
label5 = tk.Label(root, text="Label 5", bg="lightgray", padx=10, pady=10)

# Place the labels using grid manager with columnspan and rowspan
label1.grid(row=0, column=0, columnspan=2, sticky="nsew")
label2.grid(row=0, column=2, rowspan=2, sticky="nsew")
label3.grid(row=1, column=0, columnspan=2, sticky="nsew")
label4.grid(row=2, column=0, columnspan=3, sticky="nsew")
label5.grid(row=3, column=0, columnspan=3, sticky="nsew")

# Configure the grid to make the columns and rows expand
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
#root.grid_rowconfigure(0, weight=1)
#root.grid_rowconfigure(1, weight=1)
root.grid_rowconfigure(2, weight=1)
root.grid_rowconfigure(3, weight=1)

# Run the application
root.mainloop()
