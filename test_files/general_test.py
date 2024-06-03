from PIL import Image

# Example pixel data
mode = 'RGB'
size = (4, 4)  # 4x4 image
data = bytes([
    255, 0, 0,   0, 255, 0,   0, 0, 255,   255, 255, 0,   # First row: Red, Green, Blue, Yellow
    255, 0, 255, 0, 255, 255, 0, 0, 0,     255, 255, 255, # Second row: Magenta, Cyan, Black, White
    127, 127, 127, 64, 64, 64, 32, 32, 32, 16, 16, 16,    # Third row: Various shades of gray
    255, 127, 0,   127, 255, 0, 127, 0, 255, 0, 127, 255  # Fourth row: Various colors
])

# Create an image from the byte data
image = Image.frombytes(mode, size, data)

# Show the image
image.show()