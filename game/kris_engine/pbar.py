from kris_engine import Scene, Entity
from kris_engine.colour import Colour
import threading
import pygame

class ProgressBar(Entity):
    # func is the thing that's going to be called on each item during loading, this is get_asset by default
    # iterable is the list of things that func is being called on
    # total represents the size of the progress bar, not on screen but relative to prog_incr
    # prog_incr is a function that each item of iterable can be passed into, that returns the amount that the progress bar should increase by upon processing that item
    # exit_scene is the scene that will be loaded once loading is complete
    # *args and **kwargs are the initialisation parameters for the scene
    def __init__(self, engine, scene, id, func, iterable, total, prog_incr, exit_scene, *args, **kwargs):
        super().__init__(engine, scene, id)
        self.total = total
        self.prog_incr = prog_incr
        self.progress = 0
        self.engine.pbar_out = None
        # Start the progress bar thread
        self.thread = threading.Thread(target=self.monitor_progress, args=(func, iterable, self.engine, exit_scene, *args), kwargs=kwargs)
        self.thread.start()

    def update(self):
        pass

    def render(self):
        # Draws the progress bar, it's just a rectangle that is cropped by the area parameter based on how much progress we've made relative to total
        w, h = self.engine.width, self.engine.height
        thickness = 0.006*h

        t = self.engine.get_asset("pbar.png", scale=(0.8*w, 0.1*h))
        self.engine.screen.blit(t, (0.1*w, 0.7*h), area=(0, 0, t.get_width()*(self.progress/self.total), t.get_height()))

        pygame.draw.rect(self.engine.screen, 0xffffff, (w*0.1, h*0.7, w*0.8, h*0.1), round(thickness))

    def monitor_progress(self, func, iterable, engine, exit_scene, *args, **kwargs):
        # Give the progress bar thread a text colour
        self.engine.threads[threading.get_ident()] = {"colour": Colour(0x4C19FF), "name": "Progress Bar"}
        engine.pbar_out = []
        # For each item in iterable, call function on it, update the progress variable and check if the engine is still running
        # This check is done so that if the user quits during a progress bar, then loading quits also
        for x in iterable:
            try: engine.pbar_out.append(func(x))
            except: pass
            try: self.progress += self.prog_incr(x)
            except: pass
            if not self.engine.running:
                return
        # Load the exit scene once loading is complete, but this time without using the progress bar again
        engine.load_scene(exit_scene, *args, pbar=False, **kwargs)

class Pbar(Scene):
    update_rate = 1
    # A low render rate make the progress bar appear choppy but reduces load times
    render_rate = 5
    music = None

    def __init__(self, engine, func, iterable, total, prog_incr, exit_scene, *args, **kwargs):
        # Loads the image used on the progress bar and initialises the progress bar entity
        self.engine = engine
        self.engine.get_asset("pbar.png")
        e = self.engine.load_entity(ProgressBar, self, func, iterable, total, prog_incr, exit_scene, *args, **kwargs)