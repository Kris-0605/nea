# pygame is a third-party module for rendering graphics and playing sound
import pygame
# Here, json is used to create a config file where settings can be stored
import json
# os is used for file system operations such as checking if a file exists
import os
# My own module for outputting coloured text in the console using ANSI escape codes
# Much of the code was written by another student so will not be included in the Technical Solution
from kris_engine.colour import Colour
# Used for global except hook and dumping to stdout
import sys
# Used for managing threading
import threading
# Used for running function on program termination
import atexit
# Used for getting information about the current time and how long the program has been running for as well as sleeping
import time
# Used to assign random text colour to an unidentified thread
import random
# A module of my own creation used to load textures from a custom file type
# See files.py for documentation around this
import kris_engine.files

# Defining the main engine class
# When an Engine object is initialised, it will loop forever until something causes self.running to become False
class Engine:
    # These keyword parameters were formerly stored in a config.json file but this is more convenient
    # Scene refers to the scene loaded upon initialisation
    # width and height represent the size in pixels of the window created
    # engine_path represents where the folder that the engine is stored in is relative to where the program is being run. So here, the program from the directory where the engine is stored, and it must be specified if it is not.
    # log_path is the same as engine path but specifically refers to where the log file is stored
    # texture_quality refers to the resolution of the texture that is loaded, as loading maximum quality texture can often require gigabytes of RAM. Only applies to images currently, uses the texture quality feature of KAP files from the files module.
    # log_max_size is the maximum size that the log file can be in bytes, defaulting to 10MB
    # *args and **kwargs are the arguments and keyword arguments for initialising the scene passed into the scene keyword
    def __init__(self, *args,
        scene=None,
        width = 1280,
        height = 720,
        engine_path = "kris_engine",
        log_path = "kris_engine/engine_log.txt",
        texture_quality = "high",
        log_max_size = 10000000,
        **kwargs):

        # If a scene is passed in, load that scene. Else, load the default scene defined by the Scene class.
        scene = scene or Scene

        # Imports the program bar module. This is a built-in Scene and Entity used for loading screens.
        # It must be imported separate from other modules, upon initilisation of an Engine object, because the module imports classes from this module, and importing it while this module has not yet finished importing creates an unresolvable dependancy loop.
        import kris_engine.pbar

        # DO NOT USE WHILE TRUE
        # Only self.running, so threads terminate
        # Threads should be written in such a way that settings self.running to False stops whatever the thread is doing as soon as possible, and this should be taken into account during iteration, for example when loading something with the progress bar.
        # self.ready is used for starting and stopping the updating and rendering process, so that it can be paused during the loading of a scene
        self.running = True
        self.ready = False

        # Assign the keyword arguments to private attibutes so they cannot be altered by other objects during execution
        self.__width = width
        self.__height = height
        self.__engine_path = engine_path
        self.__log_path = log_path
        self.__texture_quality = texture_quality
        self.__log_max_size = log_max_size

        # Counter for generating unique integers, see the id property
        self.__id = 0

        self.init_log() # Initialises logging thread
        time.sleep(0.01) # Just to make sure the thread has started

        self.append_log("Loading config file...")
        self.load_config() # Config file has been largely replaced by keyword arguments but remains in case a developer wants to use it for their own settings

        # Attibutes used to store the last time a message saying that the update or render threads were behind was sent so that the console doesn't get spammed
        self.lag, self.lag2 = time.perf_counter(), time.perf_counter()

        # self.event_gotten is an attibute used to synchronise the fetching of pygame events on the main thread and the rendering of frames on the render thread.
        # This is because events must be gotten once per frame.
        self.event_gotten = True

        self.append_log("Initialising pygame...")
        pygame.init()   

        self.append_log("Loading default assets...")
        # I made missing.png but it's based on an industry standard
        # I made missing.ogg in Audacity it's 1 second of 0.8dB 1000Hz sine wave
        # temp_shop.ogg from https://undertale.fandom.com/wiki/Tem_Shop_(Soundtrack)
        # ComicMono.ttf from https://dtinth.github.io/comic-mono-font/

        # Loads the KAP file containing default assets. These are used if an asset is not found.
        # KAP files contain assets. To learn more about them, look at files.py
        self.kap = kris_engine.files.KAP(self.engine_path+"/default.kap", engine=self)
        # Fonts are stored in the font assets dictionary due to the need to store different font sizes, and all other assets (audio, textures) are stored in the assets dictionary
        self.assets, self.font_assets = {}, {}
        
        # Used for storing pygame events
        self.events = []

        # Ordered list of all loaded entities, order decides rendering and updating order
        self.__entities = []
        # The key is a unique integer ID and the value is an entity object
        self.entity_id = {}
        
        # Create window
        self.append_log(f"Creating window, (width, height) = ({self.width}, {self.height})")
        self.screen = pygame.display.set_mode((self.width,self.height))
        # Set window title
        pygame.display.set_caption("Kris's Engine")
        
        self.append_log("Spawning threads...")
        self.__update_thread = threading.Thread(target=self.update_loop)
        self.__update_thread.start()
        self.__render_thread = threading.Thread(target=self.render_loop)
        self.__render_thread.start()
        self.append_log("Loading scene...")
        self.load_scene(scene, *args, **kwargs)

        # Pygame is weird and getting events must be done on the main thread. The event_gotten attribute is set to False every frame and True every time events are fetched. Pygame will crash if events are not gotten every frame so this attribute prevents a frame from proceeding before events are collected, however this should be hardly needed as there is a sleep statement to sync it with the framerate. The subtraction of 1ms is to account for the time it take to run the get events function.
        while self.running:
            self.get_events()
            self.event_gotten = True
            if self.render_rate != 0:
                time.sleep((1/self.render_rate)-0.001)
        pygame.quit()

    def init_log(self):
        self.__start_time = time.perf_counter() # Used for calculating how long the program has been running
        # Use the built in thread ID system to assign colours to threads
        self.threads = {threading.get_ident(): {"colour": Colour(0xff00ff), "name": "Main"}}
        # The coloured thing we flush to the console
        self.__console_log = Colour(0xff00ff)+"Welcome to Kris's Engine!\n"
        # The thing we dump to a text file
        self.__full_log = "Welcome to Kris's Engine!\n"
        self.log_loop = 0.5 # Number of seconds between dumping to console
        atexit.register(self.exit_log) # Log will be saved on termination
        threading.Thread(target=self.loop_log).start() # Create logging thread

    def loop_log(self):
        # Assign a colour to the logging thread
        self.threads[threading.get_ident()] = {"colour": Colour(0x10ebe1), "name": "Logging"}
        self.append_log(f"Logging thread initialised at {time.time()}")
        while self.running:
            sys.stdout.write(self.__console_log) # Flush to console, faster than print!
            self.__console_log = "" # Clear console log
            time.sleep(self.log_loop) # Wait. Note this only pauses this logging thread, not other threads

    def exit_log(self): # Dump log to text file on program termination
        try: # Try and read from the file and trim the front from it to comply with the maximum log size
            with open(self.log_path, "r") as f:
                log = f.read()
            log += self.__full_log + "\n"
            with open(self.log_path, "w") as f:
                f.write(log[-self.__log_max_size:])
        except FileNotFoundError: # If the log doesn't exist just write what we have
            with open(self.__log_path, "w") as f:
                f.write(self.__full_log)

    def append_log(self, message, name="Unknown"):
        # Get information about the thread that the logging request is being made from
        # Pick a colour if we don't know about it
        # Name is only used the first time a thread is started, to give it a name, otherwise it is ignored
        t = threading.get_ident()
        if t not in self.threads:
            self.threads[t] = {"colour": Colour(random.randint(0, (2**24)-1)), "name": name}
        thread = self.threads[t]
        # Only call time function once so time is consistent across logs
        name_and_time = f"{thread['name']} thread at {time.perf_counter()-self.__start_time}"
        self.__console_log += f"{thread['colour']}[{name_and_time}] {Colour(0xffffff)}{message}\n"
        self.__full_log += f"[{name_and_time}] {message}\n"

    # reads from config file, converts json to dictionary, sets config attribute to data and returns data
    def load_config(self):
        self.config_exists = os.path.exists("config.json")
        if self.config_exists:
            with open("config.json", "r") as f:
                self.config = json.loads(f.read())
            self.append_log("config.json loaded")
        else:
            self.append_log("No config.json found")

        # The config file has been replaced with keyword arguments
        # This function still exists if a developer wants to use it

    # overwrites file with the config attribute converted to json format
    def save_config(self):
        with open("config.json", "w") as f:
            f.write(json.dumps(self.config))
        self.append_log("The config file was overwritten.")

    def get_events(self):
        # Simple alias for getting pygame events
        for x in pygame.event.get():
            if x.type == pygame.QUIT:
                self.running = False
            self.events.append(x)

    # All assets should always be gotten through get_asset so they can be cached
    # This prevents a rookie developer from making the mistake of loading a file every frame
    # It also caches scaled copies of images to prevent the lag causes by scaling an image every frame
    # And if an asset is not found then it replaces that asset with a default that will be noticeable and indicitive to a user of a problem.
    # path represents the name of the texture, note that this does not refer to a real file but the name of a file in a loaded KAP file
    # If audio is set to true, then an audio file is loaded. If a font size is specifies, a font of that size is loaded. Otherwise, an image is loaded
    # More details on the contents of scale are given at the __scale function
    def get_asset(self, path, audio=False, font=0, scale="raw"):
        # If we are loading an audio file
        if audio:
            try: # If it's in the cache, return it, otherwise
                return self.assets[path]
            except:
                try: # Load it as a pygame Sound object and assign it to the cache then return it
                    self.assets[path] = pygame.mixer.Sound(self.kap.load(path, engine=self))
                    return self.assets[path]
                except: # If it failed to load, output an error message and call this function again but getting missing.ogg as a replacement
                    # Note that if default.kap is missing this will recursively error as the engine is not installed properly
                    self.append_log(f"Error! Asset {path} was not found! Is your required KAP file loaded?")
                    return self.get_asset("missing.ogg", audio=True)

        # If we are loading a font of a given size font
        if font:
            try: # See if that font size is in the cache and return it
                return self.font_assets[path][font]
            except:
                try:
                    try: # See if that font is loaded into the cache at all
                        self.font_assets[path]
                    except:
                        self.font_assets[path] = {} # If it isn't loaded into the cache, we store a dictionary at that path name
                        # This dictionary has font sizes as keys
                    # We then load in the font at the desired size, store it in cache and return it
                    self.font_assets[path][font] = pygame.font.Font(self.kap.load(path, engine=self), font)
                    return self.font_assets[path][font]
                except: # If it failed to load, output an error message and call this function again but getting ComicMono.ttf at the same font size as a replacement
                    # Note that if default.kap is missing this will recursively error as the engine is not installed properly
                    self.append_log(f"Error! Asset {path} was not found! Is your required KAP file loaded?")
                    return self.get_asset("ComicMono.ttf", font=font)

        # If it's not a font or an audio file then it's an image (that's everything that is supported)
        try: # See if it's in cache or not
            self.assets[path]
        except: # We use a dictionary again but this time with different scaling factors as keys
            self.assets[path] = {}
        try: # If we already have this scale in cache then return it
            return self.assets[path][scale]
        except: # Otherwise, we call the scaling function. Yes, even if the scale is raw, we let the function handle it.
            self.assets[path][scale] = self.__scale(scale, path)
            return self.assets[path][scale]

    def __scale(self, scale, path):
        # scale can be three things: the string "raw", a tuple of width and height floats, or a float
        # The float represents maintaining the original aspect ratio of the texture but scaling it so that the height equals the provided float multipled by the height of the engine's window
        # If we got this far and the scale is raw thaen we actually need to load it, and all scales are transformations of this raw image
        if scale == "raw":
            try: # Try and load the image as a surface object
                return pygame.image.load(self.kap.load(path, quality=self.texture_quality, engine=self))
            except: # If we can't find it, load the default missing.png
                self.append_log(f"Error! Asset {path} was not found! Is your required KAP file loaded?")
                return self.get_asset("missing.png")
        self.append_log(f"Scaling asset {path} with settings {scale}")
        obj = self.get_asset(path)
        if isinstance(scale, tuple):
            # Just in case someone decided to not follow my instructions, ensures tuple of size 2
            if len(scale) == 1:
                scale = scale[0]
            else:
                scale = scale[:2]
        if isinstance(scale, float) or isinstance(scale, int):
            x = self.height*scale
            scale = (int((x/obj.get_height())*obj.get_width()), int(x))
        # Now in both cases we have a tuple of length two with target pixel values
        return pygame.transform.scale(obj, scale)

    def load_entity(self, entity, scene, *args, **kwargs):
        # While one could theoretically initialise an entity directly, it wouldn't do anything without the engine having ownership of it
        # So the parameter name entity is slightly misleading, as you actually pass in the uninitialised class as a type object
        # Here we assign the engine an ID and initialise it with it's required and optional parameters
        # The initialised entity is returned
        if Entity not in entity.__mro__:
            # This rudimentary check ensures that the type being passed in has inherited from the Entity class
            # At some point hopefully I'll be able to ensure than an entity has been set up properly with the right initalisation parameters
            raise TypeError("Cannot initialise non-entity")
        id = self.id
        e = entity(self, scene, id, *args, **kwargs)
        self.__entities.append(e)
        self.entity_id[id] = e
        return e
    
    def destroy_entity(self, entity):
        # Check if the object passed in is an entity (has inherited from the Entity class)
        if Entity not in type(entity).__mro__:
            raise TypeError("Cannot destroy non-entity")
        # Remove the object from the entity list and the entity ID dictionary.
        # Python will return an error if the object does not exist.
        self.__entities.remove(entity)
        del self.entity_id[entity.id]

    def load_scene(self, scene, *args, pbar=True, **kwargs):
        # Similar to load_entity, scene should not be an initialised scene but instead the class of the scene to be initialised
        # pbar being set to False will automatically not use the pbar even if the scene provided requests it, and should be True in most cases
        # *args and **kwargs will be passed into the scene that is being initialised
        # self.ready being set to False pauses the execution of updates and rendering while a scene is being loaded
        self.ready = False
        # Verifies that the class being passed in inherits from the Scene class
        if Scene not in scene.__mro__:
            raise TypeError("Invalid scene was blocked!")
        for x in scene.kap: # A scene should specify the KAP files it needs to be loaded
            # These files will already be loaded if they are not loaded already, so if multiple scenes need the same KAP file there is no reason to not list those KAP files in every scene
            if x not in self.kap.open:
                self.kap.load_kap(x, engine=self)
        # Destroy all non-persistant entities
        for x in self.__entities:
            if not x.persist:
                self.destroy_entity(x)
        # If pbar is enabled by the keyword parameter, and the scene has assets to load by pbar, then we call this function again to load the pbar class
        # This rudimentary implementation loads textures in their raw form, perhaps later I will implement the ability to scale with a progress bar
        # More information about the progress bar scene can be found in pbar.py
        if pbar and scene.load_with_pbar:
            self.load_scene(kris_engine.pbar.Pbar,
            # Function to get audio and image files
            # Pbar loading does not support fonts as fonts are always scaled to a given size, there is no raw form
            lambda x: self.get_asset(x, **({"audio": True} if x[-3:] == "ogg" or x[-3:] == "wav" else {})),
            scene.load_with_pbar,
            # Calls a function to get the size of files
            # This allows for the pbar to be incremented a different amount depending on the size of the file being loaded
            sum(self.__size(x) for x in scene.load_with_pbar),
            self.__size, # Function for measuring the amount to increment for each file
            # Information about the scene to be loaded once the progress bar is complete
            scene, *args, **kwargs)
        else:
            self.append_log(f"Scene being loaded: {scene}")
            # Grab information from the scene and initialise a scene object.
            self.update_rate, self.render_rate = scene.update_rate, scene.render_rate
            self.scene = scene(self, *args, **kwargs)
            self.update_counter, self.render_counter = 0, 0
            # Loop the music infinitely
            if self.scene.music:
                self.scene.music().play(loops=-1)
            # Reset timers
            self.scene_time = time.perf_counter()
            self.lag, self.lag2 = time.perf_counter(), time.perf_counter()
            # Allow updates and rendering to process
            self.ready = True

    def __size(self, x):
        # Gets information about a file's size from KAP file header. Returns raw size or size of given texture quality if available
        # It may be worth noting that the size being used for the pbar is the compressed size of the file, not it's uncompressed size
        try: return self.kap.assets[x][1] if type(self.kap.assets[x]) == tuple else self.kap.assets[x][self.texture_quality][1]
        except: return 0

    def update_loop(self):
        # The function that is executed by the update threads
        # Assign the thread a text colour
        self.threads[threading.get_ident()] = {"colour": Colour(0x6cd663), "name": "Update"}
        self.append_log("Update thread started!")
        while self.running: # The thread will continue until every entity has been updated. Simply the most convenient way to implement it
            if self.ready: # If updates are allowed to proceed, otherwise do nothing
                self.update_counter += 1
                event = len(self.events)
                # Go through list of entities in order
                for e in self.__entities:
                    e.update()
                # All events are appended to self.events by the main thread
                # But it's the update thread that actually needs them so this means the events will be processed in the update then removed
                self.events = self.events[event:]
                t = time.perf_counter()
                # "How long do I have to wait to limit the rate of updates"
                # Except a millisecond less actually because it's better to do an update early than late
                s = (self.update_counter/self.update_rate)-(t-self.scene_time)-0.001
                if s > 0:
                    time.sleep(s) # wait
                # If it's negative then oh no we're behind
                elif self.lag2+2 < t:  # Explained earlier, no console spam
                    x = int(self.update_rate*-s)
                    if x > self.update_rate/20: # If we're less than 0.05 seconds behind why even bother
                        self.append_log(f"Warning! Update was {round(-s*1000, 1)}ms behind! {x+1} updates behind!")
                        self.lag2 = time.perf_counter()

    def render_loop(self):
        # The function that is executed by the update threads
        # Assign the thread a text colour
        self.threads[threading.get_ident()] = {"colour": Colour(0xf2e40d), "name": "Render"}
        self.append_log("Render thread started!")
        while self.running: # The thread will continue until every entity has been rendered and the frame updated. Simply the most convenient way to implement it
            if self.ready: # If rendering is allowed to proceed, otherwise do nothing
                self.render_counter += 1
                # Draw a scene's background, pygame applications typically wipe the entire screen every frame
                self.scene.background()
                # Go through list of entities in order
                for x in self.__entities:
                    x.render()
                while not self.event_gotten: # Wait for the main thread to get events
                    time.sleep(0.001)
                pygame.display.update() # Draw the next frame on screen
                self.event_gotten = False # Tell the main thread to get the next updates
                t = time.perf_counter()
                if self.render_rate != 0: # The render thread allows frame rate to be uncapped, in which case we don't need waiting or lag reporting
                    # "How long do I have to wait to limit the frame rate"
                    # Except a millisecond less actually because it's better to do a frame early than late
                    s = (self.render_counter/self.render_rate)-(t-self.scene_time)-0.001
                    if s > 0:
                        time.sleep(s)# wait
                    # If it's negative then oh no we're behind
                    elif self.lag+2 < t: # Explained earlier, no console spam
                        x = int(self.render_rate*-s)
                        if x > 10: # If we're less than 10 frames behind why even bother
                            self.append_log(f"Warning! Frame was {round(-s*1000, 1)}ms behind! {x+1} frames behind target framerate!")
                            self.lag = time.perf_counter()

    @property # Getter that increments id every time you access the attibute to always produce a unique ID
    def id(self):
        self.__id += 1
        return self.__id

    @property # All these simple getters exist to make a private attribute accessible but read only
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height

    @property
    def engine_path(self):
        return self.__engine_path

    @property
    def log_path(self):
        return self.__log_path

    @property
    def texture_quality(self):
        return self.__texture_quality

    @texture_quality.setter # Setter so that if the texture quality is changed, all the old textures of incorrect quality are flushed from the cache
    def texture_quality(self, a):
        self.append_log(f"Changing texture quality to {a}... this may take a moment")
        for x in list(self.assets.keys()):
            if type(self.assets[x]) == dict:
                del self.assets[x]
        self.__texture_quality = a

class Entity: # Every entity should inherit from this class
    persist = False # The entity will be destroyed upon loading a new scene
    # If True, then the entity will remain across scenes until explicitly destoroyed

    def __init__(self, engine: Engine, scene, id): # Every entity should have an engine, ID and scene attribute
        self.engine = engine
        self.id = id
        self.scene = scene
        # This code needs to be in a separate init function so that it's not called for every entity
        # The correct implementation is to:
        # - Inherit from the Entity class
        # - Have the first 3 positional arguments of the __init__ function be engine, scene and id, followed by your own parameters
        # - run super().__init__(engine, scene, id) as the first line to properly give your entity the attributes above
        if type(self) == Entity:
            self.init()
    
    def init(self): # Used for defining a default entity, for use in the default Scene class
        self.engine.append_log("The default entity class has been initialised. Please check the log for errors.")
        self.rotation = 0
        self.pre_calc_width = self.engine.width*0.99
        self.pre_calc_height = self.engine.height*0.01

    def update(self): # spin
        if type(self) == Entity:
            self.rotation += 0.025
            self.rotation %= 360
        # It is recommended that this function be overriden and replaced with pass if not used, or your own code
        # This is because checking if the current entity is the Entity class is more computationally expensive than skipping that check
        # It is additionally worth noting that that this is the function called every update by the update thread

    def render(self):
        if type(self) == Entity:
            w, h = self.engine.width/2, self.engine.height/2
            t = self.engine.get_asset("missing.png", scale=0.2)
            self.engine.screen.blit(pygame.transform.rotate(t, self.rotation), ((w)-(t.get_width()/2), (h)-(t.get_height()/2)))
        # It is recommended that this function be overriden and replaced with pass if not used, or your own code
        # This is because checking if the current entity is the Entity class is more computationally expensive than skipping that check
        # It is additionally worth noting that that this is the function called every frame by the render thread

class Scene: # Every scene should inherit from this class
    load_with_pbar = [] # The raw versions of the image and audio files in this list will be loaded with a progress bar displayed before the scene is initialised 
    update_rate = 2400 # Updates per second, must be positive integer
    render_rate = 0 # Frames per second, must be positive integer, or 0 for uncapped
    # The background function is called every frame before any entities are rendered and is usually used to clear the screen
    background = lambda self: self.engine.screen.fill(0) # Fills the screen with black
    # The music function should return a pygame sound object that will be looped for the duration of the scene
    # Tem Shop from the Undertale soundtrack belongs to Toby Fox and Materia Collective
    music = lambda self: self.engine.get_asset("tem_shop.ogg", audio=True)
    # This should be a list containing all KAP files that are required to be loaded for the scene to work
    kap = ["default.kap"]
    
    def __init__(self, engine: Engine):
        # Override this function! Use it to load your textures and entities
        # Have engine as your first input parameter and run super().__init__(engine), or just assign self.engine = engine yourself
        self.engine = engine
        if type(self) == Scene:
            self.engine.get_asset("missing.png", scale=0.2)
            e = engine.load_entity(Entity, self)