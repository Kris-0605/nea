from kris_engine import Entity
from random import randint
from copy import copy
import pygame

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
    "GRAVITY",
    "GRAVITY_ANIMATION",
    "VERIFY",
    "VERIFY_ANIMATION",
    "DIE"
)

ACTION_IDS = {
    "NOTHING": 0,
    "START": 1,
    "MOVE_LEFT": 2,
    "MOVE_RIGHT": 3,
    "DOWN": 6,
}

HANDLING_SETTINGS = {
    "DAS": 45,
    "ARR": 15
}

class Grid(Entity):
    def __init__(self, engine, scene, id, input_handler, rows=12, columns=6, values=[], position=(16/320, 16/224), bean_queue_position=(0.4, 40/224)):
        super().__init__(engine, scene, id)
        self.input_handler = input_handler
        self.values = values
        self.gravity = []
        self.state = "GRAVITY"
        self.chain_power = 1
        self.rows, self.columns = rows, columns
        self.cache = (16/320, 16/224)
        self.position = position
        self.eval_all_textures()
        self.verify = self.count_all()

        self.queue = self.engine.load_entity(BeanQueue, self.scene, bean_queue_position)
        self.falling = FallingBean(*self.queue.get_next(), self)

    def __str__(self):
        return "\n".join(" ".join(str(self.values[y].colour if y < len(self.values) and self.values[y] else 0) for y in range((x-1)*self.columns, x*self.columns)) for x in range(self.rows, 0, -1))

    def update(self):
        self.eval_all_textures()
        match self.state:
            case "GRAVITY":
                self.update_gravity()
            case "GRAVITY_ANIMATION":
                self.animate_gravity()
            case "VERIFY":
                self.update_verify()
            case "VERIFY_ANIMATION":
                self.animate_verify()
            case "FALL":
                self.falling.update()
            case "DIE":
                self.engine.append_log("Death not yet implemented, terminating, close the program")
                self.engine.destroy_entity(self)
            case _:
                pass

    def update_verify(self):
        if self.verify:
            self.chain_power += 1
            self.state = "VERIFY_ANIMATION"
            self.counter = 0
            self.counter_goal = 300
            temp = copy(self.verify)
            self.verify = set()
            for x in temp:
                self.values[x].row = x // self.columns
                self.values[x].column = x % self.columns
                self.verify.add(self.values[x])
                self.values[x] = None
        else:
            try:
                if self.values[(self.rows-1)*self.columns + 2]:
                    self.state = "DIE"
            except: pass
            if self.state != "DIE":
                self.falling = FallingBean(*self.queue.get_next(), self)
                self.state = "FALL"
                self.chain_power = 0

    def animate_verify(self):
        self.counter += 1
        if self.counter == self.counter_goal:
            self.verify = set()
            self.state = "GRAVITY"
        elif self.counter == 180:
            for x in self.verify:
                x.state = TEXTURE_STATE_IDS["SHOCKED"]
        elif self.counter == 230:
            self.engine.get_asset(f"pop{self.chain_power if self.chain_power < 7 else 6}.ogg", audio=True).play()

    def animate_gravity(self):
        for x in self.gravity:
            try:
                next(x.position)
            except StopIteration:
                self.gravity.remove(x)
                col = x.colour
                bean = Bean(col)
                self.values[x.destination] = bean
                self.eval_texture(x.destination)
                self.count(x.destination)
        if not self.gravity:
            self.counter += 1
            if self.counter == self.counter_goal:
                self.state = "VERIFY"

    def update_gravity_quick(self):
        for n in range(self.columns):
            column = [self.values[x] for x in range(n, len(self.values), self.columns) if self.values[x] != None]
            for x in range(n, len(self.values), self.columns):
                if column:
                    self.values[x] = column[0] if column else None
                    column.pop(0)
                else:
                    self.values[x] = None

    def update_gravity(self):
        for n in range(self.columns):
            column = [self.values[x] for x in range(n, len(self.values), self.columns)]
            if None in column:
                split_column = self.split_list(column, None)
                for a in range(1, len(split_column)):
                    for b in split_column[a]:
                        row =  column.index(b)
                        self.gravity.append(GravityBean(b, n+(row-a)*self.columns, a, row, n))
                for x in range(n + len(split_column[0])*self.columns, len(self.values), self.columns):
                    self.values[x] = None
        self.counter = 0
        self.counter_goal = 50
        self.state = "GRAVITY_ANIMATION"

    @staticmethod
    def split_list(lst, sep):
        out = []
        x = 0
        for n in range(len(lst)):
            if lst[n] == sep:
                out.append(lst[x:n])
                x = n + 1
        out.append(lst[x:])
        return out

    def place_bean(self, bean, position):
        self.values += [None]*(position-len(self.values))
        self.values[position] = bean
        self.count(position)

    def render(self):
        self.render_grid()
        match self.state:
            case "GRAVITY_ANIMATION":
                self.render_gravity()
            case "VERIFY_ANIMATION":
                self.render_verify()
            case "FALL":
                self.render_falling()
            case _:
                pass
        self.engine.screen.blit(self.engine.get_asset("backdrop3.png", scale=(self.engine.width, self.engine.height)), (0, 0))

    def render_grid(self):
        column = 0
        row = 0
        for x in self.values:
            if type(x) == Bean:
                self.render_bean(x, row, column)
            column += 1
            if column == self.columns:
                column = 0
                row += 1

    def render_bean(self, x, row, column):
        self.engine.screen.blit(
            self.engine.get_asset(x.texture, scale=self.cache[1]),
            ((self.cache[0]*column+self.position[0])*self.engine.width,
            (1-(self.cache[1]*row+self.position[1]*2))*self.engine.height)
        )

    def render_gravity(self):
        for x in self.gravity:
            self.render_bean(x, x.row, x.column)

    def render_verify(self):
        if self.counter > 230:
            pass
        if 25 < self.counter < 180 and self.counter%10 < 5:
            for x in self.verify:
                self.render_bean(x, x.row, x.column)

    def render_falling(self):
        self.render_bean(self.falling.primary, self.falling.row, self.falling.column)
        match self.falling.rotation_state:
            case 0:
                self.render_bean(self.falling.secondary, self.falling.row+1, self.falling.column)
            case 1:
                self.render_bean(self.falling.secondary, self.falling.row, self.falling.column+1)
            case 2:
                self.render_bean(self.falling.secondary, self.falling.row-1, self.falling.column)
            case 3:
                self.render_bean(self.falling.secondary, self.falling.row, self.falling.column-1)
            case _:
                raise ValueError("Invalid rotation state")

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
        to_be_destroyed = set()
        while to_be_counted:
            group = {to_be_counted[0]}
            surroundings = self.get_surroundings(to_be_counted[0], group)
            for x in surroundings:
                group.add(x)
                surroundings += self.get_surroundings(x, group)
            for x in group:
                to_be_counted.remove(x)
            if len(group) >= 4:
                to_be_destroyed = to_be_destroyed.union(group)
        return to_be_destroyed
    
    def count(self, bean):
        if bean not in self.verify:
            group = {bean}
            surroundings = self.get_surroundings(bean, group)
            for x in surroundings:
                group.add(x)
                surroundings += self.get_surroundings(x, group)
            if len(group) >= 4:
                self.verify = self.verify.union(group)

    def get_surroundings(self, x, group):
        tests = []
        if x+self.columns < len(self.values):
            tests.append(x+self.columns)
        if x-self.columns >= 0:
            tests.append(x-self.columns)
        if x % self.columns:
            tests.append(x-1)
        if (x + 1) % self.columns:
            tests.append(x+1)
        return [y for y in tests if y >= 0 and y < len(self.values) and self.values[y] and self.values[y].colour == self.values[x].colour and y not in group]

class BeanQueue(Entity):
    def __init__(self, engine, scene, id, position):
        super().__init__(engine, scene, id)
        self.next = (Bean(randint(1,5)), Bean(randint(1, 5)))
        self.cache = 16/224
        self.position = position

    def render(self):
        self.engine.screen.blit(
            self.engine.get_asset(self.next[0].texture, scale=self.cache),
            (self.position[0]*self.engine.width,
            self.position[1]*self.engine.height)
        )
        self.engine.screen.blit(
            self.engine.get_asset(self.next[1].texture, scale=self.cache),
            (self.position[0]*self.engine.width,
            (self.cache+self.position[1])*self.engine.height)
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
    def __init__(self, colour, up=0, down=0, left=0, right=0, state=0):
        self.colour = colour if type(colour) == int else COLOUR_IDS[colour]
        self.__up = up
        self.__down = down
        self.__left = left
        self.__right = right
        self.__state = state
        self.get_texture()

    def __str__(self):
        return f"Bean({self.colour})"
    __repr__ = __str__

    def get_texture(self):
        if self.state:
            texture = self.state
        else:
            texture = (self.up << 3) + (self.down << 2) + (self.left << 1) + self.right
        if texture == 0:
            texture = TEXTURE_STATE_IDS["NORMAL"]
        self.texture = f"{self.colour}_{texture}.png"
        return self.texture

    @property
    def state(self):
        if not self.__state and not (self.up or self.down or self.left or self.right):
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
    def __init__(self, bean, destination, row_distance, row, column):
        super().__init__(bean.colour)

        self.row = row
        self.column = column
        self.destination = destination
        self.row_distance = row_distance

        def position():
            #for n in range(40):
            #    yield
            self.state = TEXTURE_STATE_IDS["NORMAL"]
            for n in range(row_distance*10):
                if n % 5 == 0:
                    self.row -= 0.5
                yield
            for i in range(2):
                self.state = TEXTURE_STATE_IDS["NORMAL"]
                for n in range(5):
                    yield
                self.state = TEXTURE_STATE_IDS["SQUISH2"]
                for n in range(15):
                    yield
                self.state = TEXTURE_STATE_IDS["NORMAL"]
                for n in range(5):
                    yield
                self.state = TEXTURE_STATE_IDS["SQUISH1"]
                for n in range(10):
                    yield
            self.state = TEXTURE_STATE_IDS["NORMAL"]
            for n in range(5):
                yield
            self.state = TEXTURE_STATE_IDS["SQUISH2"]
            for n in range(10):
                yield
            self.state = TEXTURE_STATE_IDS["NORMAL"]
            for n in range(5):
                yield
            self.state = TEXTURE_STATE_IDS["SQUISH1"]
            for n in range(5):
                yield
            self.state = TEXTURE_STATE_IDS["NORMAL"]
            for n in range(5):
                yield
            self.state = TEXTURE_STATE_IDS["SQUISH2"]
            for n in range(30):
                yield

        self.position = position()

class FallingBean(Bean):
    def __init__(self, top, bottom, grid: Grid):
        self.primary = Bean(bottom.colour)
        self.secondary = Bean(top.colour)
        self.grid = grid

        self.row = grid.rows
        self.column = 2
        self.counter = 0
        self.fall_rate = 120

        self.rotation_state = 0
        # Let P be the primary bean and S be the secondary bean
        # 0 -   S
        #       P
        # 1 -   PS
        # 2 -   P
        #       S
        # 3 -   SP

    def update(self):
        self.counter += 1

        if self.counter % 200 == 90:
            self.primary.state = TEXTURE_STATE_IDS["WHITE"]
        elif self.counter % 200 == 0:
            self.primary.state = TEXTURE_STATE_IDS["NORMAL"]
        
        while True:
            try:
                if self.grid.input_handler.rotation:
                    self.rotate()

                if self.grid.input_handler.state == ACTION_IDS["MOVE_RIGHT"] or self.grid.input_handler.state == ACTION_IDS["MOVE_LEFT"]:
                    if self.verify_placement():
                        self.column += 1 if self.grid.input_handler.state == ACTION_IDS["MOVE_RIGHT"] else -1

                if self.counter % (self.fall_rate//20 if self.grid.input_handler.state == ACTION_IDS["DOWN"] else self.fall_rate) == 0:
                    if self.row % 1 == 0.5:
                        self.row -= 0.5
                    elif self.row == 0 or (self.rotation_state == 2 and self.row == 1):
                        self.place_beans()
                    elif self.grid.values[self.primary_position()-self.grid.columns] or self.grid.values[self.secondary_position()-self.grid.columns]:
                        self.place_beans()
                    else:
                        self.row -= 0.5

                break
            except IndexError:
                self.grid.values += [None]*(int(self.column+self.grid.columns*(self.row+1))-len(self.grid.values))
                if self.counter % self.fall_rate == 0:
                    self.row -= 0.5

    def primary_position(self):
        return self.column+self.grid.columns*int(self.row)

    def secondary_position(self):
        match self.rotation_state:
            case 0:
                return int(self.column+self.grid.columns*(self.row+1))
            case 1:
                return int(self.column+1+self.grid.columns*self.row)
            case 2:
                return int(self.column+self.grid.columns*(self.row-1))
            case 3:
                return int(self.column-1+self.grid.columns*self.row)
            case _:
                raise ValueError("Invalid rotation state")

    def rotate(self):
        position = self.column+self.grid.columns*int(self.row)
        self.rotation_state += self.grid.input_handler.rotation
        self.rotation_state %= 4
        if self.rotation_state == 1 and (self.column == self.grid.columns-1 or self.grid.values[position+1]):
            self.column -= 1
        if self.rotation_state == 3 and (self.column == 0 or self.grid.values[position-1]):
            self.column += 1

    def relative_to_falling(self, primary_or_secondary): # True for primary, False for secondary
        offset = 1 if self.grid.input_handler.state == ACTION_IDS["MOVE_RIGHT"] else -1
        position = self.primary_position() if primary_or_secondary else self.secondary_position()
        if offset == 1 and position % self.grid.columns == self.grid.columns - 1:
            return True
        if offset == -1 and position % self.grid.columns == 0:
            return True
        return bool(self.grid.values[position-offset]) or False if not self.row % 1 else bool(self.grid.values[position-1+self.grid.columns])

    def verify_placement(self):
        return not (self.relative_to_falling(True) or self.relative_to_falling(False))

    def place_beans(self):
        self.primary.state, self.secondary.state = 0, 0
        self.grid.place_bean(self.primary, int(self.column+self.grid.columns*self.row))
        self.grid.place_bean(self.secondary, self.secondary_position())
        self.grid.state = "GRAVITY"

    def render(self):
        pass
        
class InputHandler(Entity):
    def __init__(self, engine, scene, id):
        super().__init__(engine, scene, id)
        self.state = ACTION_IDS["NOTHING"]
        self.direction = 0
        self.rotation = 0

    def render(self):
        pass

    def get_inputs(self):
        self.left = False
        self.right = False
        self.down = False
        self.A = False
        self.B = False
        self.start = False

        for x in self.engine.events:
            if x.type == pygame.KEYDOWN:
                match x.key:
                    case pygame.K_RETURN:
                        self.state = True
                    case pygame.K_c:
                        self.A = True
                    case pygame.K_x:
                        self.B = True

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.left = True
        if keys[pygame.K_RIGHT]:
            self.right = True
        if keys[pygame.K_DOWN]:
            self.down = True

    def update(self):
        self.get_inputs()

        if self.A and self.B:
            self.rotation = 0
        elif self.A:
            self.rotation = 1
        elif self.B:
            self.rotation = -1
        else:
            self.rotation = 0
        
        if self.left and self.right:
            self.direction = 0
        elif self.left:
            if self.direction > 0:
                self.direction = -1
            else:
                self.direction -= 1
        elif self.right:
            if self.direction < 0:
                self.direction = 1
            else:
                self.direction += 1
        else:
            self.direction = 0

        if self.start:
            self.state = ACTION_IDS["START"]
        else:
            if not self.direction:
                if self.down:
                    self.state = ACTION_IDS["DOWN"]
                else:
                    self.state = ACTION_IDS["NOTHING"]
            elif self.direction == 1:
                self.state = ACTION_IDS["MOVE_RIGHT"]
            elif self.direction == -1:
                self.state = ACTION_IDS["MOVE_LEFT"]
            elif self.direction == HANDLING_SETTINGS["DAS"]:
                self.state = ACTION_IDS["MOVE_RIGHT"]
            elif self.direction == -HANDLING_SETTINGS["DAS"]:
                self.state = ACTION_IDS["MOVE_LEFT"]
            elif self.direction > HANDLING_SETTINGS["DAS"]:
                if (self.direction-HANDLING_SETTINGS["DAS"]) % HANDLING_SETTINGS["ARR"] == 0:
                    self.state = ACTION_IDS["MOVE_RIGHT"]
                else:
                    self.state = ACTION_IDS["NOTHING"]
            elif self.direction < -HANDLING_SETTINGS["DAS"]:
                if (self.direction+HANDLING_SETTINGS["DAS"]) % HANDLING_SETTINGS["ARR"] == 0:
                    self.state = ACTION_IDS["MOVE_LEFT"]
                else:
                    self.state = ACTION_IDS["NOTHING"]
            else:
                self.state = ACTION_IDS["NOTHING"]