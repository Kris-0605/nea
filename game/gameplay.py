from kris_engine import Entity
from random import randint

class Grid(Entity):
    def init(self, rows=12, columns=6, values=[]):
        self.values = values
        self.rows, self.columns = rows, columns
        self.cache = (16/320, 16/224)
        self.eval_all()

    def render(self):
        self.values[randint(0, 71)].colour = randint(1,5)
        self.eval_all()
        column = 0
        row = 0
        for x in self.values:
            if x:
                self.engine.screen.blit(
                    self.engine.get_asset(x.texture, scale=self.cache[1]),
                    (self.cache[0]*(column+1)*self.engine.width,
                    (1-(self.cache[1]*(row+2)))*self.engine.height)
                )
            column += 1
            if column == self.columns:
                column = 0
                row += 1

    def eval_all(self):
        for pos in range(len(self.values)):
            self.eval(pos)

    def eval(self, bean_pos):
        try:
            bean = self.values[bean_pos]
            col = bean.colour
        except:
            return None

        self.eval_up(bean_pos, bean, col),
        self.eval_down(bean_pos, bean, col),
        self.eval_left(bean_pos, bean, col),
        self.eval_right(bean_pos, bean, col)

    def eval_up(self, bean_pos, bean, col):
        try:
            if self.values[bean_pos+self.columns].colour == col:
                x = True
            else:
                x = False
        except:
            x = 0

        bean.up = x

    def eval_down(self, bean_pos, bean, col):
        try:
            if bean_pos-self.columns < 0:
                x = 0
            elif self.values[bean_pos-self.columns].colour == col:
                x = True
            else:
                x = False
        except:
            x = 0

        bean.down = x

    def eval_left(self, bean_pos, bean, col):
        try:
            if not bean_pos % self.columns:
                x = 0
            elif bean_pos-1 < 0:
                x = 0
            elif self.values[bean_pos-1].colour == col:
                x = True
            else:
                x = False
        except:
            x = 0

        bean.left = x

    def eval_right(self, bean_pos, bean, col):
        try:
            if not (bean_pos + 1) % self.columns:
                x = 0
            elif self.values[bean_pos+1].colour == col:
                x = True
            else:
                x = False
        except:
            x = 0

        bean.right = x


class Bean:
    # The values of up, down, left and right may be slightly confusing
    # But they are restricted to None, False and True for performance
    # 0 means there is no bean there
    # False means there is a bean there, but it's not the same colour
    # True means there is a bean there, and it's the same colour
    def __init__(self, colour, up=0, down=0, left=0, right=0, state=0):
        self.colour = colour if type(colour) == int else COLOUR_IDS[colour]
        self.__up = up
        self.__down = down
        self.__left = left
        self.__right = right
        self.__state = state
        self.get_texture()

    def get_texture(self):
        if self.state:
            texture = self.state
        else:
            texture = (self.up << 3) + (self.down << 2) + (self.left << 1) + self.right
        self.texture = f"{self.colour}_{texture}.png"
        return self.texture

    @property
    def state(self):
        if not (self.up or self.down or self.left or self.right) and not self.__state:
            return STATE_IDS["NORMAL"]
        return self.__state

    @property
    def up(self):
        return self.__up

    @up.setter
    def up(self, a):
        self.__up = a
        self.get_texture()
    
    @property
    def down(self):
        return self.__down

    @down.setter
    def down(self, a):
        self.__down = a
        self.get_texture()

    @property
    def left(self):
        return self.__left

    @left.setter
    def left(self, a):
        self.__left = a
        self.get_texture()

    @property
    def right(self):
        return self.__right

    @right.setter
    def right(self, a):
        self.__right = a
        self.get_texture()

# Constants

COLOUR_IDS = {
    "RED": 1,
    "GREEN": 2,
    "YELLOW": 3,
    "PURPLE": 4,
    "CYAN": 5
    }

STATE_IDS = {
    "WHITE": 16,
    "NORMAL": 17,
    "SQUISH1": 18,
    "SQUISH2": 19,
    "SHOCKED": 20
}