import sys
sys.path.append("..")
import kris_engine.files

from os import listdir

kris_engine.files.build({
    "ultra_high": 1,
    "high": 0.25,
    "medium": 0.0625,
    "low": 0.015625,
    "ultra_low": 0.00390625
}, [x for x in listdir() if x[-3:] == "png"], [x for x in listdir() if x[-3:] == "ogg"], "..\\base.kap")