from kris_engine import Scene
from gameplay import Grid, Bean
from random import randint

class ExerciseClassic(Scene):
    kap = ["base.kap"]
    load_with_pbar = ["exercise.ogg", "pop1.ogg", "pop2.ogg", "pop3.ogg", "pop4.ogg", "pop5.ogg", "pop6.ogg", '1_1.png', '1_10.png', '1_11.png', '1_12.png', '1_13.png', '1_14.png', '1_15.png', '1_16.png', '1_17.png', '1_18.png', '1_19.png', '1_2.png', '1_20.png', '1_21.png', '1_22.png', '1_23.png', '1_24.png', '1_25.png', '1_26.png', '1_27.png', '1_3.png', '1_4.png', '1_5.png', '1_6.png', '1_7.png', '1_8.png', '1_9.png', '2_1.png', '2_10.png', '2_11.png', '2_12.png', '2_13.png', '2_14.png', '2_15.png', '2_16.png', '2_17.png', '2_18.png', '2_19.png', '2_2.png', '2_20.png', '2_21.png', '2_22.png', '2_23.png', '2_24.png', '2_25.png', '2_26.png', '2_27.png', '2_3.png', '2_4.png', '2_5.png', '2_6.png', '2_7.png', '2_8.png', '2_9.png', '3_1.png', '3_10.png', '3_11.png', '3_12.png', '3_13.png', '3_14.png', '3_15.png', '3_16.png', '3_17.png', '3_18.png', '3_19.png', '3_2.png', '3_20.png', '3_21.png', '3_22.png', '3_23.png', '3_24.png', '3_25.png', '3_26.png', '3_27.png', '3_3.png', '3_4.png', '3_5.png', '3_6.png', '3_7.png', '3_8.png', '3_9.png', '4_1.png', '4_10.png', '4_11.png', '4_12.png', '4_13.png', '4_14.png', '4_15.png', '4_16.png', '4_17.png', '4_18.png', '4_19.png', '4_2.png', '4_20.png', '4_21.png', '4_22.png', '4_23.png', '4_24.png', '4_25.png', '4_26.png', '4_27.png', '4_3.png', '4_4.png', '4_5.png', '4_6.png', '4_7.png', '4_8.png', '4_9.png', '5_1.png', '5_10.png', '5_11.png', '5_12.png', '5_13.png', '5_14.png', '5_15.png', '5_16.png', '5_17.png', '5_18.png', '5_19.png', '5_2.png', '5_20.png', '5_21.png', '5_22.png', '5_23.png', '5_24.png', '5_25.png', '5_26.png', '5_27.png', '5_3.png', '5_4.png', '5_5.png', '5_6.png', '5_7.png', '5_8.png', '5_9.png', 'backdrop2.png']
    music = lambda self: self.engine.get_asset("exercise.ogg", audio=True)
    update_rate = 300

    def background(self):
        self.engine.screen.fill(0)
        t = self.engine.get_asset("backdrop2.png", scale=(self.engine.width, self.engine.height))
        self.engine.screen.blit(t, (0, 0))

    def __init__(self, engine):
        self.engine = engine
        e = self.engine.load_entity(Grid, self)
        #e.init(values=[Bean(randint(1,5)) for x in range(60)])
        e.init(values=[
            Bean(1), Bean(5), Bean(5), Bean(5), Bean(1), Bean(2),
            Bean(1), Bean(2), Bean(3), Bean(4), Bean(1), Bean(2),
            Bean(1), Bean(2), Bean(3), Bean(4), Bean(1), Bean(2),
            Bean(1), Bean(3), Bean(4), Bean(5), Bean(2), None,
            Bean(2), Bean(3), Bean(4), Bean(1), None, None,
            Bean(2), None, None, None, None, None,
            None, None, None, None, None, None,
            None, None, None, None, None, None,
            None, None, None, None, None, None,
            None, None, None, None, None, None,
            None, None, None, None, None, None,
            None, None, None, None, None, None,
        ])