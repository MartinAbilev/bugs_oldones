import pygame
from shared import *
import gfx as gx

# Initialize global variables
step = 0
Ann = Ann2(0)

# Display initial status
gx.status(Ann)

def AnnStep():
    global step
    step += 1
    if step > 4:
        step = 0
        for n in Ann.neurons:
            for c in n.conection:
                c.value = Ann.neurons[c.to].out
                n.output()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    AnnStep()
    gx.clear()
    gx.gloop(Ann)

# Cleanup
pygame.quit()
