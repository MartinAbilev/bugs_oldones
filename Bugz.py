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


pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("BUGZ // NEURAL SWARM")
clock = pygame.time.Clock()
ui = SimulationUI()
thruster_overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

# The contact listener keeps this shared list to map Box2D bodies back to creatures.
objects = []
world = PhysicsWorld(objects)
best_network = None  # Network with the longest lifetime in the current run.
generation_requested = False  # Set by the lifetime callback to start a new generation.
next_id = 0  # Unique creature/body ID counter.
life_time_record = 0  # Best lifetime reached since the last record reset.
radiation = 1.0  # Shared mutation scale controlled by the sidebar slider.
radiation_slider_dragging = False  # Keeps slider updates active while the mouse is held.
simulation_paused = False  # Freezes physics and lifecycle while sensors remain visible.
dragged_creature = None  # Creature currently captured by a middle-button drag.
creature_drag_offset = b2Vec2(0, 0)  # Keeps the grab point fixed during dragging.


def on_lifetime_update(creature, alive_count):
    """Track the best creature and decide when the current generation should end."""
    global best_network, generation_requested, life_time_record
    if simulation_paused:
        return
    if creature.time > life_time_record:
        life_time_record = creature.time
        best_network = creature.Ann
        if alive_count <= 1 or alive_count > 25:
            generation_requested = True
        if alive_count > 5:
            creature.death = 1


def spawn_creature(position, network_file):
    """Load a network and add its creature body to the shared simulation."""
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
    """Create a mutated child network and spawn its creature."""
    child_network = copy.deepcopy(parent.Ann)
    child_network.randomizeWeights(radiation)
    child_network.saveNet("child")
    spawn_creature(b2Vec2(random.randint(10, 400), 200), "child")


def create_next_generation():
    """Persist the best network and seed the next group with mutations."""
    global next_id, generation_requested
    best_network.saveNet("Best")
    for x in range(6):
        spawn_creature(
            b2Vec2(50 + x * 50, random.randint(10, 350)),
            "Best",
        )
    for creature in objects:
        if creature.death == 0 and creature.oId <= next_id + 3:
            creature.mutate(radiation)
    generation_requested = False


for x in range(3):
    spawn_creature(b2Vec2(50 + x * 50, 50), "Best")


def open_editor():
    """Run the network editor, then apply its saved network to living creatures."""
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
            creature.update_body_properties()


running = True
while running:
    # The current input state controls godhand sensing, mutations, and Radiation.
    pause_requested = False
    edit_requested = False
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
            dragged_creature = None
            if 0 <= event.pos[0] < 500 and 0 <= event.pos[1] < 400:
                for creature in reversed(objects):
                    if creature.death != 0:
                        continue
                    dx = event.pos[0] - creature.body.position.x
                    dy = event.pos[1] - creature.body.position.y
                    if dx * dx + dy * dy <= (creature.r + 6) ** 2:
                        dragged_creature = creature
                        creature_drag_offset = b2Vec2(
                            event.pos[0] - creature.body.position.x,
                            event.pos[1] - creature.body.position.y,
                        )
                        break
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
            dragged_creature = None
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and ui.pause_button.collidepoint(event.pos)
        ):
            pause_requested = True
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and ui.edit_button.collidepoint(event.pos)
        ):
            edit_requested = True

    if pause_requested:
        simulation_paused = not simulation_paused

    if edit_requested:
        open_editor()

    mouse_pos = pygame.mouse.get_pos()
    if dragged_creature is not None and pygame.mouse.get_pressed()[1]:
        target_x = mouse_pos[0] - creature_drag_offset.x
        target_y = mouse_pos[1] - creature_drag_offset.y
        dragged_creature.move_to(b2Vec2(target_x, target_y))

    screen.blit(ui.background, (0, 0))
    ui.draw_arena_border(screen)
    # Keep creature graphics from overwriting environmental sensor targets.
    sensor_surface = screen.copy()
    ui.draw_sensor_border(sensor_surface)

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
            creature.draw(screen, update_lifecycle=not simulation_paused)
            alive_count += 1

    if mouse_pos[0] < 500 and mouse_pos[1] < 400:
        ui.draw_godhand(screen, mouse_pos)
        ui.draw_godhand(sensor_surface, mouse_pos)

    thruster_overlay.fill((0, 0, 0, 0))
    pixel_array = pygame.surfarray.pixels3d(sensor_surface)
    to_remove = []
    for creature in objects:
        if creature.death == 0:
            creature.sense(
                pixel_array,
                alive_count,
                apply_physics=not simulation_paused,
            )
            if left_click and not simulation_paused:
                creature.mutate(radiation)
        if creature.death == 1:
            creature.body.active = False
            to_remove.append(creature)
        else:
            creature.draw_sensor_lights(thruster_overlay)
            creature.draw_thruster_indicators(thruster_overlay)
    del pixel_array

    screen.blit(thruster_overlay, (0, 0))
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
        paused=simulation_paused,
    )
    if not simulation_paused:
        world.world.Step(world.timeStep, 32, 32)
        world.world.ClearForces()
    pygame.display.flip()

    if not simulation_paused and (alive_count <= 0 or generation_requested):
        create_next_generation()

    clock.tick(60)

pygame.quit()
