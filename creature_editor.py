"""Live phenotype editor using the simulation's creature renderer and physics."""

import math

import pygame
from Box2D import b2Vec2

from NeuralNetwork import vector2d
from creature import Creature
from physics import PhysicsWorld
from simulation_ui import SimulationUI
from viewport import fit_viewport, window_to_logical


LOGICAL_SIZE = (960, 480)
PREVIEW_SIZE = (640, 480)
PREVIEW_CENTER = (250, 200)
MIN_OUTPUTS = 5
MAX_OUTPUTS = 32


class CreatureEditor:
    """Edit a saved network while previewing its real in-simulation creature."""

    def __init__(self):
        self.ui = SimulationUI()
        self.world = PhysicsWorld([])
        self.creature = Creature(
            b2Vec2(*PREVIEW_CENTER),
            self.world,
            0,
            "Best",
            lambda *_: None,
            lambda *_: None,
        )
        self.preview = pygame.Surface(PREVIEW_SIZE)
        self.overlay = pygame.Surface(PREVIEW_SIZE, pygame.SRCALPHA)
        self.creature.centerpos = b2Vec2(*PREVIEW_CENTER)
        self.font = pygame.font.SysFont("arial", 14)
        self.small_font = pygame.font.SysFont("arial", 11)
        self.tiny_font = pygame.font.SysFont("arial", 9)
        self.playing = False
        self.dirty = False
        self.status = "Best.json loaded"
        self.adding_sensor = False
        self.selected_sensor = None
        self.dragging_sensor = None
        self.active_slider = None
        self.buttons = {}
        self.sliders = {
            "radius": pygame.Rect(690, 242, 232, 8),
            "colorG": pygame.Rect(690, 286, 232, 8),
            "colorB": pygame.Rect(690, 330, 232, 8),
        }

    @property
    def ann(self):
        return self.creature.Ann

    def _mark_changed(self, message):
        self.dirty = True
        self.status = message

    def _button(self, surface, key, label, rect, mouse_pos, enabled=True):
        self.buttons[key] = rect
        hovered = enabled and rect.collidepoint(mouse_pos)
        fill = (28, 67, 75) if hovered else (17, 35, 48)
        edge = (70, 220, 205) if hovered else (35, 82, 94)
        text_color = (230, 246, 245) if enabled else (86, 102, 113)
        pygame.draw.rect(surface, fill, rect, border_radius=5)
        pygame.draw.rect(surface, edge, rect, 1, border_radius=5)
        rendered = self.small_font.render(label, True, text_color)
        surface.blit(rendered, rendered.get_rect(center=rect.center))

    def _set_slider(self, key, mouse_x):
        track = self.sliders[key]
        fraction = max(0.0, min(1.0, (mouse_x - track.left) / track.width))
        if key == "radius":
            self.ann.body_radius = round(5 + fraction * 15, 1)
            self.creature.update_body_properties()
            label = f"Body radius {self.ann.body_radius:.1f}"
        else:
            setattr(self.ann, key, round(fraction * 255))
            channel = "Green" if key == "colorG" else "Blue"
            label = f"{channel} color {getattr(self.ann, key)}"
        self._mark_changed(label)

    def _draw_slider(self, surface, key, label, value, low, high):
        track = self.sliders[key]
        self.ui.text(surface, label, (658, track.top - 20), (177, 201, 211), self.tiny_font)
        pygame.draw.line(
            surface,
            (42, 66, 78),
            (track.left, track.centery),
            (track.right, track.centery),
            4,
        )
        fraction = max(0.0, min(1.0, (value - low) / (high - low)))
        knob_x = round(track.left + fraction * track.width)
        pygame.draw.line(
            surface,
            (74, 205, 184),
            (track.left, track.centery),
            (knob_x, track.centery),
            3,
        )
        pygame.draw.circle(surface, (224, 248, 242), (knob_x, track.centery), 6)
        pygame.draw.circle(surface, (53, 142, 138), (knob_x, track.centery), 6, 1)

    def _draw_panel(self, surface, mouse_pos):
        panel = pygame.Rect(640, 0, 320, 480)
        pygame.draw.rect(surface, (10, 17, 29), panel)
        pygame.draw.line(surface, (25, 54, 68), (640, 0), (640, 480), 2)
        self.ui.text(surface, "CREATURE EDITOR", (658, 16), (235, 248, 255), self.font)
        self.ui.text(
            surface,
            "LIVE SIMULATION PREVIEW",
            (658, 39),
            (93, 191, 197),
            self.tiny_font,
        )

        node_counts = (
            f"SENSORS {len(self.ann.poly):02d}   "
            f"HIDDEN {self.ann.hiddenSize:02d}   "
            f"OUTPUTS {len(self.ann.neurons) - self.ann.hiddenSize - len(self.ann.poly) - 2:02d}"
        )
        self.ui.text(surface, node_counts, (658, 62), (165, 190, 201), self.tiny_font)

        self._button(surface, "save", "SAVE TO BEST", pygame.Rect(658, 84, 138, 29), mouse_pos)
        self._button(surface, "load", "RELOAD BEST", pygame.Rect(806, 84, 138, 29), mouse_pos)
        self._button(
            surface,
            "add_sensor",
            "ADD SENSOR",
            pygame.Rect(658, 120, 138, 29),
            mouse_pos,
        )
        self._button(
            surface,
            "remove_sensor",
            "REMOVE SELECTED",
            pygame.Rect(806, 120, 138, 29),
            mouse_pos,
            enabled=self.selected_sensor is not None,
        )
        output_count = len(self.ann.neurons) - self.ann.hiddenSize - len(self.ann.poly) - 2
        self._button(
            surface,
            "add_thruster",
            "ADD THRUSTER",
            pygame.Rect(658, 156, 138, 29),
            mouse_pos,
            enabled=output_count < MAX_OUTPUTS,
        )
        self._button(
            surface,
            "remove_thruster",
            "REMOVE EXTRA",
            pygame.Rect(806, 156, 138, 29),
            mouse_pos,
            enabled=output_count > MIN_OUTPUTS,
        )
        self._button(
            surface,
            "play",
            "PAUSE PREVIEW" if self.playing else "PLAY PREVIEW",
            pygame.Rect(658, 192, 138, 29),
            mouse_pos,
        )
        self._button(
            surface,
            "reset",
            "RESET POSITION",
            pygame.Rect(806, 192, 138, 29),
            mouse_pos,
        )

        self._draw_slider(
            surface,
            "radius",
            f"BODY SIZE  {self.ann.body_radius:.1f}",
            self.ann.body_radius,
            5,
            20,
        )
        self._draw_slider(surface, "colorG", f"INHERITED GREEN  {self.ann.colorG}", self.ann.colorG, 0, 255)
        self._draw_slider(surface, "colorB", f"INHERITED BLUE  {self.ann.colorB}", self.ann.colorB, 0, 255)

        pygame.draw.line(surface, (24, 37, 53), (658, 355), (942, 355))
        self.ui.text(
            surface,
            "DRAG SENSOR DOTS TO EDIT MORPHOLOGY",
            (658, 366),
            (143, 175, 187),
            self.tiny_font,
        )
        self.ui.text(
            surface,
            "ADD SENSOR, THEN CLICK IN THE ARENA",
            (658, 383),
            (143, 175, 187),
            self.tiny_font,
        )
        state = "UNSAVED CHANGES" if self.dirty else self.status
        state_color = (255, 190, 95) if self.dirty else (93, 191, 197)
        self.ui.text(surface, state[:42], (658, 414), state_color, self.tiny_font)
        self.ui.text(surface, "Close window to return to simulation", (658, 448), (103, 133, 149), self.tiny_font)

    def _draw_preview(self, mouse_pos):
        self.preview.blit(self.ui.background, (0, 0))
        self.ui.draw_arena_border(self.preview)
        sensor_surface = self.preview.copy()
        self.ui.draw_sensor_border(sensor_surface)
        if 0 <= mouse_pos[0] < 500 and 0 <= mouse_pos[1] < 400:
            self.ui.draw_godhand(self.preview, mouse_pos)
            self.ui.draw_godhand(sensor_surface, mouse_pos)

        self.creature.draw(self.preview, update_lifecycle=False)
        pixels = pygame.surfarray.pixels3d(sensor_surface)
        self.creature.sense(pixels, 1, apply_physics=self.playing)
        del pixels

        self.overlay.fill((0, 0, 0, 0))
        self.creature.draw_membrane(self.overlay)
        self.creature.draw_sensor_lights(self.overlay)
        self.creature.draw_thruster_indicators(self.overlay)
        if self.selected_sensor is not None and self.selected_sensor < len(self.creature.poly):
            point = self.creature.poly[self.selected_sensor]
            marker = (
                round(self.creature.centerpos.x + point[0] * 1.2),
                round(self.creature.centerpos.y + point[1] * 1.2),
            )
            pygame.draw.circle(self.overlay, (255, 215, 75, 220), marker, 7, 1)
        self.preview.blit(self.overlay, (0, 0))

        pygame.draw.rect(self.preview, (30, 43, 58), (505, 0, 135, 480))
        self.ui.text(self.preview, "SIM VIEW", (519, 18), (130, 158, 177), self.ui.font_10)
        self.ui.text(self.preview, "BODY", (519, 44), (130, 158, 177), self.ui.font_9)
        self.ui.text(
            self.preview,
            f"r {self.creature.r:.1f}  mass {self.creature.body.mass:.0f}",
            (519, 59),
            (220, 235, 240),
            self.ui.font_9,
        )
        self.ui.text(
            self.preview,
            f"HP {self.creature.max_lives:.1f}",
            (519, 76),
            (220, 235, 240),
            self.ui.font_9,
        )

    def _local_point(self, screen_position):
        dx = (screen_position[0] - self.creature.centerpos.x) / 1.2
        dy = (screen_position[1] - self.creature.centerpos.y) / 1.2
        angle = math.radians(self.creature.angle())
        cosine = math.cos(angle)
        sine = math.sin(angle)
        return [dx * cosine + dy * sine, -dx * sine + dy * cosine]

    def _set_sensor_position(self, sensor_index, screen_position):
        self.ann.poly[sensor_index] = self._local_point(screen_position)
        self.ann.syncMorphologyPositions()
        self.creature.sensor_values = [0] * len(self.ann.poly)
        self._mark_changed(f"Sensor {sensor_index + 1} moved")

    def _add_sensor(self, screen_position):
        if len(self.ann.poly) >= 32:
            self.status = "Maximum of 32 sensors reached"
            return
        point = self._local_point(screen_position)
        sensor_index = self.ann.hiddenSize + len(self.ann.poly)
        self.ann.poly.append(point)
        self.ann.insertNeuron(
            sensor_index,
            1,
            vector2d(
                self.creature.centerpos.x + point[0] * 1.2,
                self.creature.centerpos.y + point[1] * 1.2,
            ),
        )
        source_end = self.ann.hiddenSize + len(self.ann.poly) + 2
        target_indices = list(range(self.ann.hiddenSize)) + list(
            range(source_end, len(self.ann.neurons))
        )
        sensor = self.ann.neurons[sensor_index]
        for target_index in target_indices:
            target = self.ann.neurons[target_index]
            target.conections.append(sensor_index)
            target.weights.append(1.0)
            target.parent.append(sensor_index)
            sensor.child.append(target_index)
        self.ann.syncMorphologyPositions()
        self.creature.sensor_values = [0] * len(self.ann.poly)
        self.selected_sensor = len(self.ann.poly) - 1
        self.adding_sensor = False
        self._mark_changed("Sensor added; existing weights preserved")

    def _remove_sensor(self):
        if self.selected_sensor is None:
            return
        sensor_index = self.selected_sensor
        self.ann.removeNeuron(self.ann.hiddenSize + sensor_index)
        self.ann.poly.pop(sensor_index)
        self.ann.syncMorphologyPositions()
        self.creature.sensor_values = [0] * len(self.ann.poly)
        self.selected_sensor = None
        self._mark_changed("Sensor removed; existing weights preserved")

    def _add_thruster(self):
        output_count = len(self.ann.neurons) - self.ann.hiddenSize - len(self.ann.poly) - 2
        if output_count >= MAX_OUTPUTS:
            self.status = f"Maximum of {MAX_OUTPUTS} outputs reached"
            return
        output = self.ann.insertNeuron(len(self.ann.neurons), 2, vector2d(320, 240))
        source_end = self.ann.hiddenSize + len(self.ann.poly) + 2
        output.conections = list(range(source_end))
        output.weights = [1.0] * source_end
        output.parent = list(range(source_end))
        for source_index in range(source_end):
            self.ann.neurons[source_index].child.append(output.id)
        self.ann.syncMorphologyPositions()
        self._mark_changed("Thruster added; existing weights preserved")

    def _remove_thruster(self):
        output_count = len(self.ann.neurons) - self.ann.hiddenSize - len(self.ann.poly) - 2
        if output_count <= MIN_OUTPUTS:
            return
        self.ann.removeNeuron(len(self.ann.neurons) - 1)
        self.ann.syncMorphologyPositions()
        self._mark_changed("Extra thruster removed; existing weights preserved")

    def _reload(self):
        self.ann.loadNet("Best")
        self.creature.update_body_properties()
        self.creature.sensor_values = [0] * len(self.ann.poly)
        self.selected_sensor = None
        self.adding_sensor = False
        self.dirty = False
        self.status = "Best.json reloaded"

    def _save(self):
        self.ann.saveNet("Best")
        self.dirty = False
        self.status = "Saved Best.json"

    def _activate_button(self, key):
        if key == "save":
            self._save()
        elif key == "load":
            self._reload()
        elif key == "add_sensor":
            self.adding_sensor = True
            self.status = "Click inside the arena to place a sensor"
        elif key == "remove_sensor":
            self._remove_sensor()
        elif key == "add_thruster":
            self._add_thruster()
        elif key == "remove_thruster":
            self._remove_thruster()
        elif key == "play":
            self.playing = not self.playing
        elif key == "reset":
            self.creature.body.position = b2Vec2(*PREVIEW_CENTER)
            self.creature.body.angle = 0
            self.creature.body.linearVelocity = b2Vec2(0, 0)
            self.creature.body.angularVelocity = 0

    def _handle_click(self, position):
        for key, rect in self.buttons.items():
            if rect.collidepoint(position):
                if key == "remove_sensor" and self.selected_sensor is None:
                    return
                if key == "add_thruster":
                    count = len(self.ann.neurons) - self.ann.hiddenSize - len(self.ann.poly) - 2
                    if count >= MAX_OUTPUTS:
                        return
                if key == "remove_thruster":
                    count = len(self.ann.neurons) - self.ann.hiddenSize - len(self.ann.poly) - 2
                    if count <= MIN_OUTPUTS:
                        return
                self._activate_button(key)
                return

        for key, rect in self.sliders.items():
            if rect.inflate(0, 16).collidepoint(position):
                self.active_slider = key
                self._set_slider(key, position[0])
                return

        if position[0] >= 500 or position[1] >= 400:
            self.adding_sensor = False
            return
        if self.adding_sensor:
            self._add_sensor(position)
            return

        sensor_points = [
            (
                self.creature.centerpos.x + point[0] * 1.2,
                self.creature.centerpos.y + point[1] * 1.2,
            )
            for point in self.creature.poly
        ]
        nearest = min(
            range(len(sensor_points)),
            key=lambda index: math.dist(sensor_points[index], position),
            default=None,
        )
        if nearest is not None and math.dist(sensor_points[nearest], position) <= 11:
            self.selected_sensor = nearest
            self.dragging_sensor = nearest
            self.status = f"Sensor {nearest + 1} selected"
        else:
            self.selected_sensor = None
            self.dragging_sensor = None

    def _handle_event(self, event, viewport):
        if event.type == pygame.VIDEORESIZE:
            return pygame.display.set_mode(
                (max(640, event.w), max(320, event.h)),
                pygame.RESIZABLE,
            )

        position = None
        if hasattr(event, "pos"):
            position = window_to_logical(event.pos, viewport, LOGICAL_SIZE)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(position)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_sensor = None
            self.active_slider = None
        elif event.type == pygame.MOUSEMOTION:
            if self.active_slider is not None:
                self._set_slider(self.active_slider, position[0])
            elif self.dragging_sensor is not None and event.buttons[0]:
                self._set_sensor_position(self.dragging_sensor, position)
        return None

    def run(self):
        display = pygame.display.set_mode(LOGICAL_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("BUGZ // CREATURE EDITOR")
        clock = pygame.time.Clock()
        running = True
        while running:
            window_size = display.get_size()
            viewport = fit_viewport(LOGICAL_SIZE, window_size)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                else:
                    resized_display = self._handle_event(event, viewport)
                    if resized_display is not None:
                        display = resized_display
                        viewport = fit_viewport(LOGICAL_SIZE, display.get_size())

            mouse_pos = window_to_logical(
                pygame.mouse.get_pos(),
                viewport,
                LOGICAL_SIZE,
            )
            self._draw_preview(mouse_pos)
            canvas = pygame.Surface(LOGICAL_SIZE)
            canvas.blit(self.preview, (0, 0))
            self._draw_panel(canvas, mouse_pos)

            if self.playing:
                self.world.world.Step(self.world.timeStep, 32, 32)
                self.world.world.ClearForces()

            display.fill((0, 0, 0))
            scaled = pygame.transform.smoothscale(canvas, viewport.size)
            display.blit(scaled, viewport.topleft)
            pygame.display.flip()
            clock.tick(60)


def run_editor():
    """Start the editor in its own Pygame process."""
    pygame.init()
    CreatureEditor().run()
    pygame.quit()
