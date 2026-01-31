import tkinter
from tkinter import ttk
import eel
import sv_ttk
import darkdetect

root = tkinter.Tk()

button = ttk.Button(root, text="Click me!")
button.pack()



sv_ttk.set_theme(darkdetect.theme())

root.mainloop()