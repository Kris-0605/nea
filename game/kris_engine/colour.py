# Implementation of ANSI escape codes for coloured text in console
# Credit to Hope Shivlock
# Add to the front of a string, pass in a hexcode

try:
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
except: pass
# allows processing of ANSI codes on Windows

class Colour:
    default="\033[0m"
    def __init__(self,hexcode):
        if type(hexcode)==int:
            # Convert hex codes to 3 integers
            hexcode = ((hexcode%16777216)//65536,(hexcode%65536)//256,hexcode%256)
        self._col=hexcode
        # Generate ANSI
        self._ansi="\033[38;2;"+";".join([str(num) for num in hexcode])+"m"
    def __call__(self,text="",change=True): # Get code when class is called as a function
        if change:
            return self._ansi+text+self.default
        else:
            return self._ansi
    def __add__(self,other): # Get code when class is added to string
        return self._ansi+other
    def __str__(self): # I added this bit it's useful for f-strings
        return self._ansi
    # Hope likes getters and setters she added this so you can change the colour
    # But personally I just call a new instance of the very lightweight class
    @property
    def col(self):
        return self._col
    @col.setter
    def col(self,hexcode):
        if type(hexcode)==int:
            hexcode = ((hexcode%16777216)//65536,(hexcode%65536)//256,hexcode%256)
        self._col=hexcode
        self._ansi="\033[38;2;"+";".join([str(num) for num in hexcode])+"m"
    @property
    def ansi(self):
        return self._ansi