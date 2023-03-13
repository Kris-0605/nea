from kris_engine import Entity
from random import randint
from copy import copy
import pygame
# Pygame used for key library and some constants

# Constants that effect program behaviour

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

# Grid is an entity
class Grid(Entity):
    # columns is more important as rows is not restricting, the grid can contain more than that many rows of beans but it defines the death point for the grid
    # values allows a non-empty grid to be loaded
    def __init__(self, engine, scene, id, input_handler, rows=12, columns=6, values=[], position=(16/320, 16/224), bean_queue_position=(0.4, 40/224)):
        super().__init__(engine, scene, id)
        self.input_handler = input_handler
        # score entity aggregated by grid entity
        self.score = self.engine.load_entity(Score, scene)
        # 1D list filled with Bean objects or None representing an empty cell
        self.values = values
        # used to store GravityBeans
        self.gravity = []
        self.state = "GRAVITY"
        # Used for score calculation
        # Falling beans can set off chains, chain power increments each time we reach the VERIFY state without spawning a new falling bean
        # Spawning a new FallingBean will reset the counter
        self.chain_power = 0
        # Scoring bonus for when multiple groups are popped at once that have different colours
        self.colour_bonus = 0
        # Scoring bonus for when more than 4 beans are popped at once
        self.group_bonus = 0
        # Scoring calculation variable representing the maximum number of beans popped at once during any point in the chain reaction
        self.beans_popped = 0
        self.rows, self.columns = rows, columns
        # Commonly used in drawing calculations, so precalculated to prevent unnecessary repeated division
        self.cache = (16/320, 16/224)
        self.position = position
        # Correct textures if a non-empty grid has been loaded
        self.eval_all_textures()
        # List representing groups that are being popped during a chain reaction
        self.groups = []
        # Set of all beans that need to be popped
        self.verify = self.count_all()

        # BeanQueue entity aggregated by Grid object
        self.queue = self.engine.load_entity(BeanQueue, self.scene, bean_queue_position)
        # method of BeanQueue used to get the next falling bean
        self.falling = FallingBean(*self.queue.get_next(), self)

    def __str__(self): # Used to convert the current grid into a neat string for debugging
        return "\n".join(" ".join(str(self.values[y].colour if y < len(self.values) and self.values[y] else 0) for y in range((x-1)*self.columns, x*self.columns)) for x in range(self.rows, 0, -1))

    def update(self):
        # Lookup table for what to do depending on what state the program is in
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
        # If we are in the verify state, check if there are any beans to be popped (calculated by gravity beans when they terminate)
        if self.verify:
            self.chain_power += 1
            # We use a set to remove duplicates to get the number of unique colours that are currently being popped, for the colour bonus
            colours = set()
            if (z:= sum(len(x) for x in self.groups)) > self.beans_popped:
                # beans_popped is the maximum number of beans that are popped at the same time during the chain reaction
                # So we overwrite it if we have bigger than the current value
                self.beans_popped = z
            # Bonus for the number of groups being popped at a time
            for x in self.groups:
                self.group_bonus += self.group_bonus_lookup(len(x))
                colours.add(x.pop())
            self.colour_bonus += self.colour_bonus_lookup(len(colours))
            # Change the score display to show the current ongoing score calculation
            # Score is not added until the chain is complete
            self.score.text = (f"{10*self.beans_popped}x{z}" if (z := self.chain_power_lookup(self.chain_power)+self.group_bonus+self.colour_bonus) else str(10*self.beans_popped)).rjust(9)
            self.state = "VERIFY_ANIMATION"
            self.counter = 0
            self.counter_goal = 300
            temp = copy(self.verify)
            # Reset the variables containing the beans we're about to pop
            self.verify = set()
            self.groups = []
            for x in temp:
                # Remove our colour groups from the grid
                self.values[x].row = x // self.columns
                self.values[x].column = x % self.columns
                self.verify.add(self.values[x])
                self.values[x] = None
        else: # The chain has ended
            try:
                # Check for death
                if self.values[(self.rows-1)*self.columns + 2]:
                    self.state = "DIE"
                    self.score.dump_score()
                    self.score.output_top_scores()
            except: pass # If the function errored then the grid isn't big enough to contain the death cell
            # In which case it definitely doesn't have anything in it
            if self.state != "DIE":
                # Get our next falling bean
                self.falling = FallingBean(*self.queue.get_next(), self)
                self.state = "FALL"
                # Update the score and the score text to match
                self.score.score += 10*self.beans_popped*(z if (z := self.chain_power_lookup(self.chain_power)+self.group_bonus+self.colour_bonus) else 1)
                self.score.text = str(self.score.score).zfill(9)
                # Reset our calculating variables
                self.chain_power = 0
                self.colour_bonus = 0
                self.group_bonus = 0
                self.beans_popped = 0

    @staticmethod
    def chain_power_lookup(CP):
        if CP == 1:
            return 0
        if CP > 8:
            return 999
        return 2**(CP+1)
    
    @staticmethod
    def colour_bonus_lookup(CB):
        if CB == 1:
            return 0
        return 2**(CB-2)*3
    
    @staticmethod
    def group_bonus_lookup(GB):
        if GB < 5:
            return 0
        if GB > 10:
            return 10
        return GB-3

    def animate_verify(self): # Simple animation implementation
        self.counter += 1
        if self.counter == self.counter_goal:
            self.verify = set()
            self.state = "GRAVITY"
        elif self.counter == 180:
            for x in self.verify:
                x.state = TEXTURE_STATE_IDS["SHOCKED"]
        elif self.counter == 230: # The pitch of the sound gets higher as longer chains are produced
            self.engine.get_asset(f"pop{self.chain_power if self.chain_power < 7 else 6}.ogg", audio=True).play()

    def animate_gravity(self):
        for x in self.gravity:
            try:
                # Gravity beans are animated using generator objects that can cleanly set things like their current position and texture
                next(x.position)
            except StopIteration:
                # When the animation finishes we make a new bean in it's place, update it's texture and see if it fell to make a group
                self.gravity.remove(x)
                col = x.colour
                bean = Bean(col)
                self.values[x.destination] = bean
                self.eval_surrounding(x.destination)
                self.count(x.destination)
        if not self.gravity: # Once all gravity beans have finished their animations
            self.counter += 1 # A short pause before the next verification
            if self.counter == self.counter_goal:
                self.state = "VERIFY"

    def update_gravity_quick(self): # A faster implementation of gravity, but it doesn't let use know which beans have fallen in the resulting grid
        # Would be useful for replays
        for n in range(self.columns):
            column = [self.values[x] for x in range(n, len(self.values), self.columns) if self.values[x] != None]
            for x in range(n, len(self.values), self.columns):
                if column:
                    self.values[x] = column[0] if column else None
                    column.pop(0)
                else:
                    self.values[x] = None

    def update_gravity(self):
        # For every column
        for n in range(self.columns):
            # Extracts a column from the 1D list
            column = [self.values[x] for x in range(n, len(self.values), self.columns)]
            # If there are no empty cells then there's no reason to check for falling beans
            if None in column:
                # Returns a 2D list which, flattened into a 1D list would tell us the final resulting output of the column on the grid
                # However, the position of the list in the outer list tells us how many rows a bean will fall
                split_column = self.split_list(column, None)
                # For all the distances of 1 or more
                for a in range(1, len(split_column)):
                    # For all the beans falling that distance
                    for b in split_column[a]:
                        # Get the current row from the original column data
                        row =  column.index(b)
                        # Create a gravity bean, inputing the bean's destination with what we already calculated
                        self.gravity.append(GravityBean(b, n+(row-a)*self.columns, a, row, n))
                # For all the beans in the column above the ones that didn't fall at all
                for x in range(n + len(split_column[0])*self.columns, len(self.values), self.columns):
                    # Remove them from the grid (they'll be replaced when the gravity beans are done falling)
                    self.values[x] = None
        # This represents the small wait after all the beans are finished falling
        self.counter = 0
        self.counter_goal = 50
        self.state = "GRAVITY_ANIMATION"

    @staticmethod
    # Works like the split method on a string, but on a 1D list, returning a 2D list
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
        # Pads the list with empty cells if it's not long enough already
        self.values += [None]*(position-len(self.values))
        self.values[position] = bean
        # Checks for new colour groups and updates the bean's texture
        self.count(position)
        self.eval_surrounding(position)

    def render(self):
        # Draw the grid with all the beans in it
        self.render_grid()
        # Do any special drawing a state may require
        match self.state:
            case "GRAVITY_ANIMATION":
                self.render_gravity()
            case "VERIFY_ANIMATION":
                self.render_verify()
            case "FALL":
                self.render_falling()
            case _:
                pass
        # Then draw backdrop3.png last
        # This means that beans that are outside of the grid, such as falling beans that just spawned in, appear behind the background
        # Not seeing this represents death, since the bottom of the grid has opened up 
        self.engine.screen.blit(self.engine.get_asset("backdrop3.png", scale=(self.engine.width, self.engine.height)), (0, 0))

    def render_grid(self):
        # Draws our 1D array in a 2D grid on screen by moving to the next row each time we hit the number of columns
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
        # Used all over the code to draw a bean on screen
        self.engine.screen.blit(
            self.engine.get_asset(x.texture, scale=self.cache[1]),
            ((self.cache[0]*column+self.position[0])*self.engine.width,
            (1-(self.cache[1]*row+self.position[1]*2))*self.engine.height)
        )

    def render_gravity(self):
        # Gravity beans are already being animated by the update thread so we just need to draw them in their current state
        for x in self.gravity:
            self.render_bean(x, x.row, x.column)

    def render_verify(self):
        # Beans that are being popped flash on and off the screen every other frame, which instead of having an empty texture is done by just not drawing it
        if self.counter > 230:
            pass
        if 25 < self.counter < 180 and self.counter%10 < 5:
            for x in self.verify:
                self.render_bean(x, x.row, x.column)

    def render_falling(self):
        # Draws the primary falling bean, renders the position of the secondary bean, which is relative to the primary bean and dependant on rotation state
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
        # Used for getting the right texture for every bean when loading in a grid instead of updating in real time
        for pos in range(len(self.values)):
            self.eval_texture(pos)

    def eval_texture(self, bean_pos):
        # Updates the texture for a given bean, in every direction
        try:
            bean = self.values[bean_pos]
            col = bean.colour
        except:
            return None

        self.eval_up(bean_pos, bean, col),
        self.eval_down(bean_pos, bean, col),
        self.eval_left(bean_pos, bean, col),
        self.eval_right(bean_pos, bean, col)

    # The below are functions that check whether a bean in a given direction exists and is of the same colour and sets that attribute of the bean

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
        # Updates the texture for a bean as well as all the beans surrounding it
        for x in (bean_pos, bean_pos+self.columns, bean_pos-self.columns, bean_pos-1, bean_pos+1):
            self.eval_texture(x)

    def count_all(self): # A function to scan the entire grid for colour groups. Similar to count, see explanation there
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
                self.groups.append(group)
        return to_be_destroyed
    
    def count(self, bean): # Checks if a bean is in a colour group
        # First, we check if the bean has already been detected as being in a colour group. If it hasn't, 
        if bean not in self.verify:
            # Create a set containing the bean
            group = {bean}
            # Use get surroundings to get all the adjacent beans of the same colour
            surroundings = self.get_surroundings(bean, group)
            # We iterate through the list
            for x in surroundings:
                # And add all of these adjacent same colour beans to our set
                # We will get duplicates but those will be removed by the set
                group.add(x)
                # And then we find the same colour beans that are adjacent to those beans
                surroundings += self.get_surroundings(x, group)
            # Iteration will continue until the end of the list is reached, which signifies that every bean in the set doesn't have an adjacent bean that isn't already in the set
            # So if the group is bigger than 4, then set it to be popped
            if len(group) >= 4:
                self.verify = self.verify.union(group)
                self.groups.append(group)

    def get_surroundings(self, x, group):
        tests = []
        if x+self.columns < len(self.values): # If the row above the bean is contained within the grid
            tests.append(x+self.columns) # Check the bean above
        if x-self.columns >= 0: # If the bean isn't on the bottom row
            tests.append(x-self.columns) # Check the bean below
        if x % self.columns: # If the bean isn't on the left edge
            tests.append(x-1) # Check the bean on the left
        if (x + 1) % self.columns: # If the bean isn't on the right edge
            tests.append(x+1) # Check the bean on the right
        # Return a list of beans that share the same colour
        return [y for y in tests if y >= 0 and y < len(self.values) and self.values[y] and self.values[y].colour == self.values[x].colour and y not in group]

# BeanQueue is an Entity
class BeanQueue(Entity):
    def __init__(self, engine, scene, id, position):
        super().__init__(engine, scene, id)
        # Beans are randomly generated using randint
        self.next = (Bean(randint(1,5)), Bean(randint(1, 5)))
        self.cache = 16/224
        self.position = position

    def render(self): # An exact copy of the render_bean function, but must be duplicated because passing in the grid overcomplicates things
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
        # Was planned to be animated but dropped due to time constraints, the potential is still there
        pass

    def get_next(self): # Returns a tuple of two beans and queues the next pair
        x = self.next
        self.next = (Bean(randint(1,5)), Bean(randint(1, 5)))
        return x

# Bean is NOT an Entity, it is just aggregated by Grid
class Bean:
    # The values of up, down, left and right may be slightly confusing
    # But they are restricted to 0, False and True for performance
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

    def __str__(self): # For debugging
        return f"Bean({self.colour})"
    __repr__ = __str__

    def get_texture(self):
        # The combination of up, down, left and right bits can be used to generate a unique 4-bit integer representing the correct texture
        # self.state is used to assign other textures that don't apply to this, and it takes priority over this texture
        if self.state:
            texture = self.state
        else:
            texture = (self.up << 3) + (self.down << 2) + (self.left << 1) + self.right
        if texture == 0:
            texture = TEXTURE_STATE_IDS["NORMAL"]
        self.texture = f"{self.colour}_{texture}.png"
        return self.texture

    # The below setters are used to automatically update the texture of a bean when one of the parameters affecting it's texture changes

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

# GravityBean inherits from Bean, but it is not an Entity
class GravityBean(Bean):
    def __init__(self, bean, destination, row_distance, row, column):
        super().__init__(bean.colour)

        self.row = row
        self.column = column
        self.destination = destination
        # Row distance is the number of rows that the bean will fall
        self.row_distance = row_distance


        # As shown above generators are really helpful for animations
        # They allow me to use for loops where each iteration of the for loop represents an update
        # It allows for this really clean animation code that allows me to run any code I want, in this case changing positions and textures
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

# FallingBean is not an entity
# It has an update method, but this is simply called by the grid
# The grid is passed in upon initialisation because grid values are accessed a lot
class FallingBean:
    def __init__(self, top, bottom, grid: Grid):
        # The secondary bean rotates around the primary bean
        self.primary = Bean(bottom.colour)
        self.secondary = Bean(top.colour)
        self.grid = grid

        self.row = grid.rows
        self.column = 2
        self.counter = 0
        # It would be really easy to implement levels I just ran out of time
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

        # Flashes the primary bean with a white outline
        if self.counter % 200 == 90:
            self.primary.state = TEXTURE_STATE_IDS["WHITE"]
        elif self.counter % 200 == 0:
            self.primary.state = TEXTURE_STATE_IDS["NORMAL"]

        try:
            # Rotation
            if self.grid.input_handler.rotation:
                self.rotate()

            # Movement right or left
            if self.grid.input_handler.state == ACTION_IDS["MOVE_RIGHT"] or self.grid.input_handler.state == ACTION_IDS["MOVE_LEFT"]:
                if self.verify_placement():
                    self.column += 1 if self.grid.input_handler.state == ACTION_IDS["MOVE_RIGHT"] else -1

            # Falling
            # Holding the down key will temporarily greatly increase the fall rate used
            if self.counter % (self.fall_rate//20 if self.grid.input_handler.state == ACTION_IDS["DOWN"] else self.fall_rate) == 0:
                # If half way between two grid cells, then fall another half a grid cell you know there's nothing beneath you
                if self.row % 1 == 0.5:
                    self.row -= 0.5
                # If we hit the bottom of the grid then place there
                elif self.row == 0 or (self.rotation_state == 2 and self.row == 1):
                    self.place_beans()
                # If there is a bean below either the primary or secondary bean then place here
                elif self.grid.values[self.primary_position()-self.grid.columns] or self.grid.values[self.secondary_position()-self.grid.columns]:
                    self.place_beans()
                # Otherwise, fall down half a grid cell
                # If the down arrow is being pressed, this adds a point for every grid cell
                else:
                    self.row -= 0.5
                    if self.grid.input_handler.state == ACTION_IDS["DOWN"]:
                        self.grid.score.score += 1
                        self.grid.score.text = str(self.grid.score.score).zfill(9)
        # If we have an index error, we pad grid out with Nones
        except IndexError:
            self.grid.values += [None]*(int(self.column+self.grid.columns*(self.row+1))-len(self.grid.values))
            if self.counter % self.fall_rate == 0:
                self.row -= 0.5

    def primary_position(self):
        # Gets position from row and column. Row is truncated.
        return self.column+self.grid.columns*int(self.row)

    def secondary_position(self):
        # Secondary position is relative to primary position and rotation state
        match self.rotation_state:
            case 0:
                return self.column+self.grid.columns*int(self.row+1)
            case 1:
                return self.column+1+self.grid.columns*int(self.row)
            case 2:
                return self.column+self.grid.columns*int(self.row-1)
            case 3:
                return self.column-1+self.grid.columns*int(self.row)
            case _:
                raise ValueError("Invalid rotation state")

    def rotate(self):
        position = self.primary_position()
        # Adding 1 is clockwise, subtracting 1 is anti-clockwise, that's how rotation state is defined
        self.rotation_state += self.grid.input_handler.rotation
        self.rotation_state %= 4
        # If you try to rotate a pair of beans and that rotation would cause the bean to be inside a wall, these if statements push you away from the wall
        if self.rotation_state == 1 and (self.column == self.grid.columns-1 or self.grid.values[position+1]):
            self.column -= 1
        if self.rotation_state == 3 and (self.column == 0 or self.grid.values[position-1]):
            self.column += 1
        if (self.rotation_state == 0 or self.rotation_state == 2) and (self.row < 1 or self.grid.values[position-self.grid.columns]):
            self.row += 1

    def relative_to_falling(self, primary_or_secondary): # True for primary, False for secondary
        # Calculates if there is a bean, or the edge of the grid, to the left or to the right of the secondary or primary bean
        offset = 1 if self.grid.input_handler.state == ACTION_IDS["MOVE_RIGHT"] else -1
        position = self.primary_position() if primary_or_secondary else self.secondary_position()
        if offset == 1 and position % self.grid.columns == self.grid.columns - 1:
            return True
        if offset == -1 and position % self.grid.columns == 0:
            return True
        # or is for extra check when half way between two grids cells
        return bool(self.grid.values[position+offset]) or (False if not self.row % 1 else bool(self.grid.values[position+offset+self.grid.columns]))

    def verify_placement(self):
        # If there's nothing next to the primary and secondary bean we're safe to move in a direction
        return not (self.relative_to_falling(True) or self.relative_to_falling(False))

    def place_beans(self):
        # While it seems strange to me, the original game this is based on awards 1 point if the down arrow is held when a bean is placed 
        if self.grid.input_handler.state == ACTION_IDS["DOWN"]:
            self.grid.score.score += 1
            self.grid.score.text = str(self.grid.score.score).zfill(9)
        # Reset the bean textures and place them
        self.primary.state, self.secondary.state = 0, 0
        self.grid.place_bean(self.primary, int(self.column+self.grid.columns*self.row))
        self.grid.place_bean(self.secondary, self.secondary_position())
        # End the falling state and make the newly placed beans fall
        self.grid.state = "GRAVITY"
        
# InputHandler is an Entity
class InputHandler(Entity):
    def __init__(self, engine, scene, id):
        super().__init__(engine, scene, id)
        self.state = ACTION_IDS["NOTHING"]
        self.direction = 0
        self.rotation = 0

    def render(self):
        # While nothing is currently visible this could easily be used for something that displays what keys are currently being pressed
        pass

    def get_inputs(self):
        self.left = False
        self.right = False
        self.down = False
        self.A = False
        self.B = False
        self.start = False

        # These keys, register only when they are initially pressed
        for x in self.engine.events:
            if x.type == pygame.KEYDOWN:
                match x.key:
                    case pygame.K_RETURN:
                        self.state = True
                    case pygame.K_c:
                        self.A = True
                    case pygame.K_x:
                        self.B = True

        # These keys register when they are pressed, i.e. they register when held down
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.left = True
        if keys[pygame.K_RIGHT]:
            self.right = True
        if keys[pygame.K_DOWN]:
            self.down = True

    def update(self):
        self.get_inputs()

        # You get output from two different attributes, rotation and state, because those two things can happen simultaneously, with rotation taking priority

        # If both rotation button are pressed then they cancel out
        if self.A and self.B:
            self.rotation = 0
        elif self.A:
            self.rotation = 1
        elif self.B:
            self.rotation = -1
        else:
            self.rotation = 0
        
        # DAS causes the piece to repeatedly move in a direction when it is held down, so we need to record how long a direction has been held for
        # Pressing both directions is impossible on a hardward controller and cancels your DAS completely 
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

        # Start overrides everything but I actually never got round to implementing pause
        if self.start:
            self.state = ACTION_IDS["START"]
        else:
            # In this game, moving left or right cancels movement downwards. So, not moving left or right means moving downwards or doing nothing.
            if not self.direction:
                if self.down:
                    self.state = ACTION_IDS["DOWN"]
                else:
                    self.state = ACTION_IDS["NOTHING"]
            # If direction is 1 or -1 then we just pressed the arrow down so we move left or move right
            elif self.direction == 1:
                self.state = ACTION_IDS["MOVE_RIGHT"]
            elif self.direction == -1:
                self.state = ACTION_IDS["MOVE_LEFT"]
            # If we hit the DAS amount we move again
            elif self.direction == HANDLING_SETTINGS["DAS"]:
                self.state = ACTION_IDS["MOVE_RIGHT"]
            elif self.direction == -HANDLING_SETTINGS["DAS"]:
                self.state = ACTION_IDS["MOVE_LEFT"]
            elif self.direction > HANDLING_SETTINGS["DAS"]:
                # Then you move every <ARR time>, provided the button is still held down, as letting go resets the counter to 0
                if (self.direction-HANDLING_SETTINGS["DAS"]) % HANDLING_SETTINGS["ARR"] == 0:
                    self.state = ACTION_IDS["MOVE_RIGHT"]
                else:
                    self.state = ACTION_IDS["NOTHING"]
            elif self.direction < -HANDLING_SETTINGS["DAS"]:
                if (self.direction+HANDLING_SETTINGS["DAS"]) % HANDLING_SETTINGS["ARR"] == 0:
                    self.state = ACTION_IDS["MOVE_LEFT"]
                else:
                    self.state = ACTION_IDS["NOTHING"]
            # If you're not on any of these special amounts, do nothing
            else:
                self.state = ACTION_IDS["NOTHING"]

# Score is an Entity
class Score(Entity):
    def __init__(self, engine, scene, id):
        super().__init__(engine, scene, id)
        # I didn't have time to get the actual font from the game so here is a placeholder
        self.font = self.engine.get_asset("ComicMono.ttf", font=40)
        self.score = 0
        self.text = "000000000" # Due to the ability to display calculations text has to be controlled separately

    def update(self):
        pass
    
    def render(self):
        text = self.font.render(self.text, True, 0xffffffff)
        self.engine.screen.blit(text, (0.4*self.engine.width, 0.5*self.engine.height))

    def output_top_scores(self):
        # Read scores from text files, split by new lines, sort them and print out the top 5
        with open("scores.txt", "r") as f:
            scores = [int(x) for x in f.read().split("\n") if x]
        sorted_scores = self.merge_sort(scores)
        MAX_SCORES_OUTPUT = 5
        print("Top scores:")
        iter_length = len(sorted_scores) if len(sorted_scores) < MAX_SCORES_OUTPUT else MAX_SCORES_OUTPUT
        for x in range(1, iter_length+1):
            print(f"{x}. {sorted_scores[-x]}")

    def dump_score(self):
        # Try writing to the already existing file
        try:
            with open("scores.txt", "a") as f:
                f.write("\n")
                f.write(str(self.score))
        # If that file doesn't exist make a new one
        except:
            with open("scores.txt", "w") as f:
                f.write(str(self.score))

    def merge_sort(self, lst):
        length = len(lst)
        if length == 1:
            return lst
        length //= 2
        left = self.merge_sort(lst[:length])
        right = self.merge_sort(lst[length:])
        out = []
        while left and right:
            out.append((left if left[0]<right[0] else right).pop(0))
        return out + left + right