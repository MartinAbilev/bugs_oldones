import copy
import os
import random
import subprocess
import sys

import pygame
from Box2D import b2Vec2

from NeuralNetwork import Ann2
from creature import Creature
from physics import PhysicsWorld
from simulation_ui import SimulationUI
from simulation_utils import vector2d


pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("BUGZ // NEURAL SWARM")
clock = pygame.time.Clock()
ui = SimulationUI()

objects = []
world = PhysicsWorld(objects)
best_network = None
generation_requested = False
next_id = 0
life_time_record = 0
radiation = 1.0
radiation_slider_dragging = False


def on_lifetime_update(creature, alive_count):
    global best_network, generation_requested, life_time_record
    if creature.time > life_time_record:
        life_time_record = creature.time
        best_network = creature.Ann
        if alive_count <= 1 or alive_count > 25:
            generation_requested = True
        if alive_count > 5:
            creature.death = 1


def spawn_creature(position, network_file):
    global next_id
    creature = Creature(
        position,
        world,
        next_id,
        network_file,
        on_lifetime_update,
        on_birth,
    )
    next_id += 1
    objects.append(creature)


def on_birth(parent):
    child_network = copy.deepcopy(parent.Ann)
    child_network.randomizeWeights(radiation)
    child_network.saveNet("child")
    spawn_creature(b2Vec2(random.randint(10, 400), 200), "child")


def create_next_generation():
    global next_id, generation_requested
    best_network.saveNet("Best")
    for x in range(6):
        spawn_creature(
            b2Vec2(50 + x * 50, random.randint(10, 350)),
            "Best",
        )
    for creature in objects:
        if creature.death == 0 and creature.oId <= next_id + 3:
            creature.Ann.randomizeWeights(radiation)
    generation_requested = False


for x in range(3):
    spawn_creature(b2Vec2(50 + x * 50, 50), "Best")


def open_editor():
    global best_network
    editor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bugEdit.py")
    subprocess.run(
        [sys.executable, editor_path],
        cwd=os.path.dirname(editor_path),
        check=True,
    )
    best_network = Ann2()
    best_network.loadNet("Best")
    for creature in objects:
        if creature.death == 0:
            creature.Ann.loadNet("Best")


running = True
mouse_position = vector2d(0, 0)
while running:
    edit_requested = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and ui.edit_button.collidepoint(event.pos)
        ):
            edit_requested = True

    if edit_requested:
        open_editor()

    mouse_pos = pygame.mouse.get_pos()
    mouse_position = vector2d(mouse_pos[0], mouse_pos[1])
    screen.blit(ui.background, (0, 0))

    right_click = pygame.mouse.get_pressed()[2]
    left_click = pygame.mouse.get_pressed()[0]
    if not left_click:
        radiation_slider_dragging = False
    elif radiation_slider_dragging or ui.radiation_slider_hitbox.collidepoint(mouse_pos):
        radiation_slider_dragging = True
        slider_position = (mouse_pos[0] - ui.radiation_slider.left) / ui.radiation_slider.width
        slider_position = max(0, min(1, slider_position))
        radiation = round(slider_position * 2 * 20) / 20
        left_click = False
    elif mouse_pos[0] >= 505:
        left_click = False
    if right_click:
        life_time_record = 0

    alive_count = 0
    for creature in objects:
        if creature.death == 0:
            creature.draw(screen)
            alive_count += 1

    pixel_array = pygame.surfarray.pixels3d(screen)
    to_remove = []
    for creature in objects:
        if creature.death == 0:
            creature.sense(pixel_array, alive_count)
            if left_click:
                creature.Ann.randomizeWeights(radiation)
        if creature.death == 1:
            creature.body.active = False
            to_remove.append(creature)
    del pixel_array

    for creature in objects:
        if creature.death == 0:
            creature.draw_thruster_indicators(screen)
    for creature in to_remove:
        objects.remove(creature)

    best_live_time = max(
        (creature.time for creature in objects if creature.death == 0),
        default=0,
    )
    ui.draw_dashboard(
        screen,
        alive_count,
        best_live_time,
        life_time_record,
        radiation,
        objects,
    )
    if mouse_pos[0] < 500 and mouse_pos[1] < 400:
        pygame.draw.circle(
            screen,
            (70, 235, 220),
            (int(mouse_position.x), int(mouse_position.y)),
            4,
            1,
        )
        pygame.draw.line(
            screen,
            (70, 235, 220),
            (mouse_position.x - 7, mouse_position.y),
            (mouse_position.x + 7, mouse_position.y),
            1,
        )
        pygame.draw.line(
            screen,
            (70, 235, 220),
            (mouse_position.x, mouse_position.y - 7),
            (mouse_position.x, mouse_position.y + 7),
            1,
        )

    world.world.Step(world.timeStep, 32, 32)
    world.world.ClearForces()
    pygame.display.flip()

    if alive_count <= 0 or generation_requested:
        create_next_generation()

    clock.tick(60)

pygame.quit()
