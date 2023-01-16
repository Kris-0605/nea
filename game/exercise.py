from kris_engine import Scene
from gameplay import Grid

class Exercise(Scene):
    kap = ["base.kap"]
    music = lambda self: self.engine.get_asset("exercise.ogg", audio=True)

    def background(self):
        self.engine.screen.fill(0)
        t = self.engine.get_asset("backdrop2.png", scale=(self.engine.width, self.engine.height))
        self.engine.screen.blit(t, (0, 0))

    def __init__(self, engine):
        self.engine = engine
        for x in ["backdrop3.png", "backdrop4.png", "backdrop5.png", "backdrop6.png"]:
            self.engine.get_asset(x)
        initialise = [Grid]
        entities = [self.engine.load_entity(x, self) for x in initialise]
        for x in entities:
            x.init()