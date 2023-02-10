from kris_engine import Entity
from random import randint

# Constants

COLOUR_IDS = {
    "RED": 1,
    "GREEN": 2,
    "YELLOW": 3,
    "PURPLE": 4,
    "CYAN": 5
    }

TEXTURE_STATE_IDS = {
    "WHITE": 16,
    "NORMAL": 17,
    "SQUISH1": 18,
    "SQUISH2": 19,
    "SHOCKED": 20
}

GAMEPLAY_STATES = (
    "FALL",
    "GRAVITY_ANIMATION",
    "VERIFY",
    "VERIFY_ANIMATION",
    "DIE"
)

class Grid(Entity):
    def init(self, rows=12, columns=6, values=[]):
        self.values = values
        self.animated = []
        self.state = "VERIFY"
        self.rows, self.columns = rows, columns
        self.cache = (16/320, 16/224)
        self.eval_all_textures()

        self.queue = self.engine.load_entity(BeanQueue, self.scene)
        self.queue.init()
        self.falling = FallingBean(*self.queue.get_next(), self)

    def update(self):
        print(self.state)
        match self.state:
            case "GRAVITY_ANIMATION":
                self.animate_gravity()
            case "VERIFY":
                self.eval_all_textures()
                self.animated = self.count_all()
                if self.animated:
                    self.state = "VERIFY_ANIMATION"
                    self.counter = 0
                    self.counter_goal = 460
                else:
                    self.falling = FallingBean(*self.queue.get_next(), self)
                    self.state = "FALL"
            case "VERIFY_ANIMATION":
                self.counter += 1
                if self.counter == self.counter_goal:
                    new_animated = []
                    for pos in self.animated:
                        self.values[pos] = None
                        for y in range(pos, len(self.values), self.columns):
                            if self.values[y]:
                                z = GravityBean(self.values[y].colour, y, self)
                                self.values[y] = z
                                new_animated.append(z)
                    self.animated = new_animated
                    self.state = "GRAVITY_ANIMATION"
                elif self.counter == 360:
                    for x in self.animated:
                        self.values[x].state = TEXTURE_STATE_IDS["SHOCKED"]
            case "FALL":
                self.falling.update()
            case _:
                pass

    def render(self):
        self.render_grid()
        match self.state:
            case "GRAVITY_ANIMATION":
                self.render_gravity()
            case "FALL":
                self.render_falling()
            case _:
                pass

    def place_bean(self, colour):
        pass

    def render_grid(self):
        column = 0
        row = 0
        for x in self.values:
            if x and not (self.state == "VERIFY_ANIMATION" and 50 < self.counter < 360 and (self.counter%20 < 10) and x in self.animated):
                self.render_bean(x, row, column)
            column += 1
            if column == self.columns:
                column = 0
                row += 1

    def render_bean(self, x, row, column):
        self.engine.screen.blit(
            self.engine.get_asset(x.texture, scale=self.cache[1]),
            (self.cache[0]*(column+1)*self.engine.width,
            (1-(self.cache[1]*(row+2)))*self.engine.height)
        )

    def render_gravity(self):
        for x in self.animated:
            self.render_bean(x, x.row, x.column)

    def animate_gravity(self):
        for x in self.animated:
            x.update()
        if not self.animated:
            self.state = "VERIFY"

    def render_falling(self):
        self.render_bean(self.falling.primary, self.falling.row+1, self.falling.column)
        self.render_bean(self.falling.secondary, self.falling.row, self.falling.column)

    def eval_all_textures(self):
        for pos in range(len(self.values)):
            self.eval_texture(pos)

    def eval_texture(self, bean_pos):
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

    def eval_surrounding(self, bean_pos):
        for x in (bean_pos, bean_pos+self.columns, bean_pos-self.columns, bean_pos-1, bean_pos+1):
            self.eval_texture(x)

    def count_all(self):
        to_be_counted = [x for x in range(len(self.values)) if type(self.values[x]) == Bean]
        to_be_destroyed = []
        while to_be_counted:
            group = {to_be_counted[0]}
            surroundings = self.get_surroundings(to_be_counted[0], group)
            for x in surroundings:
                group.add(x)
                surroundings += self.get_surroundings(x, group)
            for x in group:
                to_be_counted.remove(x)
            if len(group) >= 4:
                to_be_destroyed += list(group)
        return to_be_destroyed

    def get_surroundings(self, x, group):
        tests = []
        if x+self.columns < len(self.values):
            tests.append(x+self.columns)
        if x-self.columns > 0:
            tests.append(x-self.columns)
        if x % self.columns:
            tests.append(x-1)
        if (x + 1) % self.columns:
            tests.append(x+1)
        return [y for y in tests if y >= 0 and y < len(self.values) and self.values[y] and self.values[y].colour == self.values[x].colour and y not in group]

class BeanQueue(Entity):
    def init(self):
        self.next = (Bean(randint(1,5)), Bean(randint(1, 5)))
        self.cache = (16/224, 40/224, 56/224)

    def render(self):
        self.engine.screen.blit(
            self.engine.get_asset(self.next[0].texture, scale=self.cache[0]),
            (0.4*self.engine.width,
            self.cache[1]*self.engine.height)
        )
        self.engine.screen.blit(
            self.engine.get_asset(self.next[1].texture, scale=self.cache[0]),
            (0.4*self.engine.width,
            self.cache[2]*self.engine.height)
        )
    
    def update(self):
        # Will be animated later
        pass

    def get_next(self):
        x = self.next
        self.next = (Bean(randint(1,5)), Bean(randint(1, 5)))
        return x

class Bean:
    # The values of up, down, left and right may be slightly confusing
    # But they are restricted to None, False and True for performance
    # 0 means there is no bean there
    # False means there is a bean there, but it's not the same colour
    # True means there is a bean there, and it's the same colour
    def __init__(self, colour, up=0, down=0, left=0, right=0, state=0, neighbours=0):
        self.colour = colour if type(colour) == int else COLOUR_IDS[colour]
        self.__up = up
        self.__down = down
        self.__left = left
        self.__right = right
        self.__state = state if state else TEXTURE_STATE_IDS["NORMAL"]
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
            return TEXTURE_STATE_IDS["NORMAL"]
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

    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, a):
        self.__state = a
        self.get_texture()

class GravityBean(Bean):
    def __init__(self, colour, pos, grid: Grid):
        Bean.__init__(self, colour)
        self.state = TEXTURE_STATE_IDS["SQUISH1"]

        self.grid = grid
        
        self.column = pos % self.grid.columns
        self.row = pos // self.grid.columns

        dest = pos
        n = 0
        while grid.values[dest] != None:
            dest -= grid.columns
            n += 1
            if dest < 0:
                dest = pos
                n = 0
                break
        self.destination = dest
        self.counter = n * 110
        self.increment = 1/110

    def update(self):
        if self.counter == 0:
            self.grid.animated.remove(self)
            self.grid.values[self.destination] = Bean(self.colour)
            self.grid.eval_surrounding(self.destination)
        self.counter -= 1
        self.row -= self.increment

class FallingBean(Bean):
    def __init__(self, primary, secondary, grid: Grid):
        self.primary = Bean(primary.colour)
        self.secondary = Bean(secondary.colour)
        self.grid = grid

        self.row = grid.rows
        self.column = 2
        self.counter = 0

    def update(self):
        self.counter += 1
        if self.counter % 120 == 0:
            try:
                if self.row % 1 == 0.5:
                    self.row -= 0.5
                elif self.row == 0:
                    self.grid.values[self.column] = self.primary
                    self.grid.values[self.grid.rows + self.column] = self.secondary
                    self.grid.state = "GRAVITY_ANIMATION"
                elif self.grid.values[int((self.row-1)*self.grid.columns + self.column)]:
                    self.grid.values[int(self.row*self.grid.columns + self.column)] = self.primary
                    self.grid.values[int((self.row+1)*self.grid.columns + self.column)] = self.secondary
                    self.grid.state = "GRAVITY_ANIMATION"
                else:
                    self.row -= 0.5
            except Exception as e:
                print(e)
                self.row -= 0.5