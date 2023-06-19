import sys
sys.path.append("..\\..")
import kris_engine.files

from os import listdir

kris_engine.files.build({}, [], [x for x in listdir() if x[-2:] != "py"], "..\\default.kap")