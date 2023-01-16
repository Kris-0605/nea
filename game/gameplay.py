from kris_engine import Entity
#from math import ceil

class Grid(Entity):
    def init(self, rows=12, columns=6, values=[]):
        self.values = values if values else [[Bean()]*columns]*rows

class Bean:
    pass

# Doesn't work but is a good reference for drawing stuff
'''
class DRMBMGridBackground(Entity):
    persist = True
    force_priority = True

    def init(self):
        self.cache = [209/224, 16/224, 49/224, 32/224, 96/224]

    def render(self):
        t = self.engine.get_asset("backdrop4.png", scale=self.cache[0])
        self.engine.screen.blit(t, (ceil(self.engine.width*0.05), ceil(self.engine.height*self.cache[1])))
        self.engine.screen.blit(t, (ceil(self.engine.width*0.65), ceil(self.engine.height*self.cache[1])))

        t = self.engine.get_asset("backdrop5.png", scale=self.cache[2])
        self.engine.screen.blit(t, (ceil(self.engine.width*0.375), ceil(self.engine.height*self.cache[3])))
        self.engine.screen.blit(t, (ceil(self.engine.width*0.525), ceil(self.engine.height*self.cache[3])))

        t = self.engine.get_asset("backdrop6.png", scale=0.25)
        self.engine.screen.blit(t, (ceil(self.engine.width*0.375), ceil(self.engine.height*self.cache[4])))

    def update(self):
        pass
'''