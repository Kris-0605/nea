from kris_engine import Scene
from gameplay import Grid

class ExerciseClassic(Scene):
    kap = ["base.kap"]
    load_with_pbar = ["backdrop2.png", "exercise.ogg"]
    music = lambda self: self.engine.get_asset("exercise.ogg", audio=True)


    def background(self):
        self.engine.screen.fill(0)
        t = self.engine.get_asset("backdrop2.png", scale=(self.engine.width, self.engine.height))
        self.engine.screen.blit(t, (0, 0))

    def __init__(self, engine):
        self.engine = engine
        initialise = [Grid]
        entities = [self.engine.load_entity(x, self) for x in initialise]
        for x in entities:
            x.init()