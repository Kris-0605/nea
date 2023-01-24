from kris_engine import Scene
from gameplay import Grid

class Exercise(Scene):
    kap = ["base.kap"]
    #load_with_pbar = ["backdrop2.png", "backdrop3.png", "backdrop4.png", "backdrop5.png", "backdrop6.png", "exercise.ogg"]
    load_with_pbar = ['backdrop1.png', 'backdrop2.png', 'backdrop3.png', 'backdrop4.png', 'backdrop5.png', 'backdrop6.png', 'backdrop7.png', 'cyan1.png', 'cyan10.png', 'cyan11.png', 'cyan12.png', 'cyan13.png', 'cyan14.png', 'cyan15.png', 'cyan16.png', 'cyan17.png', 'cyan18.png', 'cyan19.png', 'cyan2.png', 'cyan20.png', 'cyan21.png', 'cyan22.png', 'cyan23.png', 'cyan24.png', 'cyan25.png', 'cyan26.png', 'cyan27.png', 'cyan3.png', 'cyan4.png', 'cyan5.png', 'cyan6.png', 'cyan7.png', 'cyan8.png', 'cyan9.png', 'exercise.ogg', 'garbageicon1.png', 'garbageicon2.png', 'garbageicon3.png', 'green1.png', 'green10.png', 'green11.png', 'green12.png', 'green13.png', 'green14.png', 'green15.png', 'green16.png', 'green17.png', 'green18.png', 'green19.png', 'green2.png', 'green20.png', 'green21.png', 'green22.png', 'green23.png', 'green24.png', 'green25.png', 'green26.png', 'green27.png', 'green3.png', 'green4.png', 'green5.png', 'green6.png', 'green7.png', 'green8.png', 'green9.png', 'purple1.png', 'purple10.png', 'purple11.png', 'purple12.png', 'purple13.png', 'purple14.png', 'purple15.png', 'purple16.png', 'purple17.png', 'purple18.png', 'purple19.png', 'purple2.png', 'purple20.png', 'purple21.png', 'purple22.png', 'purple23.png', 'purple24.png', 'purple25.png', 'purple26.png', 'purple27.png', 'purple3.png', 'purple4.png', 'purple5.png', 'purple6.png', 'purple7.png', 'purple8.png', 'purple9.png', 'red1.png', 'red10.png', 'red11.png', 'red12.png', 'red13.png', 'red14.png', 'red15.png', 'red16.png', 'red17.png', 'red18.png', 'red19.png', 'red2.png', 'red20.png', 'red21.png', 'red22.png', 'red23.png', 'red24.png', 'red25.png', 'red26.png', 'red27.png', 'red3.png', 'red4.png', 'red5.png', 'red6.png', 'red7.png', 'red8.png', 'red9.png', 'yellow1.png', 'yellow10.png', 'yellow11.png', 'yellow12.png', 'yellow13.png', 'yellow14.png', 'yellow15.png', 'yellow16.png', 'yellow17.png', 'yellow18.png', 'yellow19.png', 'yellow2.png', 'yellow20.png', 'yellow21.png', 'yellow22.png', 'yellow23.png', 'yellow24.png', 'yellow25.png', 'yellow26.png', 'yellow27.png', 'yellow3.png', 'yellow4.png', 'yellow5.png', 'yellow6.png', 'yellow7.png', 'yellow8.png', 'yellow9.png']
    music = lambda self: self.engine.get_asset("exercise.ogg", audio=True)


    def background(self):
        self.engine.screen.fill(0)
        t = self.engine.get_asset("backdrop2.png", scale=(self.engine.width, self.engine.height))
        self.engine.screen.blit(t, (0, 0))

    def __init__(self, engine):
        self.engine = engine
        for x in ["backdrop3.png", "backdrop4.png", "backdrop5.png", "backdrop6.png"]:
            self.engine.get_asset(x)
        self.engine.get_asset("exercise.ogg", audio=True)
        initialise = [Grid]
        entities = [self.engine.load_entity(x, self) for x in initialise]
        for x in entities:
            x.init()