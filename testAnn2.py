from shared import *

poly=[(20,20), (-20,20), (-20,-20), (20,-20),   (0,20), (20,0), (0,-20), (-20,0), (40,40) ]

ann=Ann2()

ann.createGrid(3)
ann.createInputs(len(poly)+2)
ann.createOutputs(5)
ann.poly=poly
ann.saveNet("Best")
ann.saveNet("child")

a=0
