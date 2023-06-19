from PIL import Image
from copy import copy

# Class for making rainbows by Hope Shivlock
class Rainbow:
    def __init__(self,start=(255,0,0),reverse=False):
        self._col=list(start)
        self.inverted=reverse
        self._phase=0
    @staticmethod
    def flip(col): return (255-col[0],255-col[1],255-col[2])
    @property
    def current(self): return (self.flip(self._col) if self.inverted else tuple(self._col))
    @current.setter
    def current(self,new):self._col = list(self.flip(new) if self.inverted else new)
    def __call__(self,step=1):
        self._col[self._phase]+=step
        self._col[self._phase-1]-=step
        if self._col[self._phase]>=255: self._col[self._phase]=255;self._col[self._phase-1]=0;self._phase+=1;self._phase%=3
        return self.current
    def __str__(self):return str(self.current)
    __repr__=__str__

r = Rainbow(reverse=True)

width, height = 2**12, 2**12//12
x = Image.new("RGB", (width, height))
inp = [tuple(int(y) for y in r(0.25)) for x in range(width)]
row = copy(inp)
for i in range(height-1):
    row = [row.pop(-1)] + row
    inp += row
x.putdata(inp)
x = x.crop((height, 0, width, height))
x.save("pbar.png")