import pygame
from NeuralNetwork import *
import gfx as gx

# Initialize global variables
step = 0
Ann = Ann2()
Ann.loadNet('Best')
clock = pygame.time.Clock()

# Display initial status
gx.status(Ann)

# Main loop
running = True
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    Ann.annStep()
    gx.clear()
    gx.gloop(Ann, events)
    clock.tick(60)

# Cleanup
pygame.quit()
