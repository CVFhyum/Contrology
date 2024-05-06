from pyautogui import position
import keyboard as kb

kb.on_press_key('p', lambda event: print(position()), suppress=True)
kb.wait()