import math

import pygame
from Box2D import b2CircleShape, b2Vec2

from NeuralNetwork import Ann2
from simulation_utils import dcircle, rotate_polygon, vector2d


class Creature:
    """A Box2D body paired with its neural controller and morphology."""

    def __init__(
        self,
        position,
        world,
        creature_id,
        network_file,
        on_lifetime_update,
        on_birth,
    ):
        """Load a network and create its dynamic body and contact fixture."""
        self.oId = creature_id
        self.death = 0
        self.Ann = Ann2()
        self.Ann.loadNet(network_file)
        self.step = 0
        self.time = 0  # Frames survived; used for best-lifetime tracking.
        self.birthTimer = 0
        self.r = self.Ann.body_radius
        self.max_lives = 3 * self.r / 10
        self.lives = self.max_lives
        self.centerpos = 0
        self.sensor_values = [0] * len(self.Ann.poly)
        self.on_lifetime_update = on_lifetime_update
        self.on_birth = on_birth
        self.body = world.world.CreateDynamicBody(position=position)
        self.body.userData = creature_id
        self.poly = self.Ann.poly
        self.box = self._create_body_fixture()
        self.body.angularDamping = 0.99

    def angle(self):
        """Return the body's current orientation in degrees."""
        return math.degrees(self.body.angle)

    def ann_step(self):
        """Advance the creature's layered neural network by one simulation step."""
        self.Ann.annStep()

    def move_to(self, position):
        """Move the body within the arena and clear momentum while it is dragged."""
        self.body.position = b2Vec2(
            max(self.r, min(500 - self.r, position.x)),
            max(self.r, min(400 - self.r, position.y)),
        )
        self.body.linearVelocity = b2Vec2(0, 0)
        self.body.angularVelocity = 0

    def _create_body_fixture(self):
        """Create the circular collision fixture using the creature's current size."""
        return self.body.CreateFixture(
            shape=b2CircleShape(radius=self.r),
            density=1,
            friction=0.8,
            restitution=0.2,
        )

    def update_body_properties(self):
        """Apply inherited or mutated body size to collision, mass, and health."""
        new_radius = max(5.0, min(20.0, float(self.Ann.body_radius)))
        self.Ann.body_radius = new_radius
        if math.isclose(new_radius, self.r):
            return

        old_max_lives = self.max_lives
        old_lives = self.lives
        self.r = new_radius
        self.max_lives = 3 * self.r / 10
        self.lives = max(
            0.0,
            min(self.max_lives, old_lives * self.max_lives / old_max_lives),
        )
        self.body.DestroyFixture(self.box)
        self.box = self._create_body_fixture()
        self.body.ResetMassData()

    def mutate(self, factor):
        """Mutate inherited DNA and synchronize its physical body properties."""
        self.Ann.randomizeWeights(factor)
        self.update_body_properties()
        self.poly = rotate_polygon(self.Ann.poly, self.angle())
        if len(self.sensor_values) != len(self.Ann.poly):
            self.sensor_values = [0] * len(self.Ann.poly)

    def read_color(self, pixel_array, center, point_index):
        """Read the red-channel sensor value at one morphology point."""
        x = int(center.x + self.poly[point_index][0] * 1.2)
        y = int(center.y + self.poly[point_index][1] * 1.2)
        x = max(0, min(639, x))
        y = max(0, min(479, y))
        try:
            color = pixel_array[x, y]
            return color[0]
        except Exception:
            return 0

    def sense(self, pixel_array, alive_count, apply_physics=True):
        """Sample sensors and evaluate the network, optionally actuating the body."""
        if self.death != 0:
            return

        center = vector2d(self.body.position.x, self.body.position.y)
        colors = [
            self.read_color(pixel_array, center, index)
            for index in range(len(self.poly))
        ]
        self.sensor_values = colors
        hidden_size = self.Ann.hiddenSize
        for index, value in enumerate(colors):
            self.Ann.outSet(index + hidden_size, value)
        self.Ann.outSet(
            len(self.poly) + hidden_size,
            self.body.angularVelocity,
        )
        self.Ann.outSet(
            len(self.poly) + 1 + hidden_size,
            (self.body.linearVelocity.x + self.body.linearVelocity.y) / 2,
        )

        # Outputs are thrusters except output 4, reserved for angular rotation.
        output_start = len(self.poly) + 2 + hidden_size
        self.ann_step()
        power = 100
        outputs = self.Ann.neurons[output_start:]
        rotation = outputs[4].out * power if len(outputs) > 4 else 0
        if apply_physics:
            self.truster(
                [
                    (index, neuron.out * power)
                    for index, neuron in enumerate(outputs)
                    if index != 4
                ],
                rotation,
            )
            self.on_lifetime_update(self, alive_count)
            self.time += 1

    def draw(self, surface, update_lifecycle=True):
        """Render the creature and trigger periodic offspring creation."""
        if self.lives <= 0:
            self.death = 1
        if self.death != 0:
            self.body.active = False
            self.time = 0
            self.Ann = []
            return

        position = vector2d(self.body.position.x, self.body.position.y)
        self.centerpos = position
        self.poly = rotate_polygon(self.Ann.poly, self.angle())
        hidden_size = self.Ann.hiddenSize
        dcircle(
            surface,
            position,
            self.angle(),
            round(self.r),
            255,
            self.Ann.colorG,
            self.Ann.colorB,
        )
        dcircle(
            surface,
            self.centerpos,
            self.angle(),
            2,
            0,
            255,
            0,
        )
        for index, point in enumerate(self.poly):
            dcircle(
                surface,
                vector2d(
                    self.centerpos.x + point[0] * 1.2,
                    self.centerpos.y + point[1] * 1.2,
                ),
                self.angle(),
                2,
                0,
                self.Ann.neurons[index + hidden_size].out,
                0,
            )

        if update_lifecycle:
            self.birthTimer += 1
            if self.birthTimer > 300:
                self.birthTimer = 0
                self.on_birth(self)

    def draw_sensor_lights(self, surface):
        """Draw white lights showing the red-channel values sampled this frame."""
        for point, value in zip(self.poly, self.sensor_values):
            brightness = max(0, min(255, int(value)))
            if brightness <= 16:
                continue

            x = max(0, min(639, int(self.centerpos.x + point[0] * 1.2)))
            y = max(0, min(479, int(self.centerpos.y + point[1] * 1.2)))
            halo_alpha = round(40 + 160 * brightness / 255)
            pygame.draw.circle(surface, (255, 255, 255, halo_alpha), (x, y), 6)
            pygame.draw.circle(surface, (255, 255, 255, 255), (x, y), 2)

    def draw_membrane(self, surface):
        """Draw a subtle translucent, body-colored fill inside the perimeter."""
        if len(self.poly) < 3:
            return

        points = [
            (
                round(self.centerpos.x + point[0] * 1.2),
                round(self.centerpos.y + point[1] * 1.2),
            )
            for point in self.poly
        ]
        color = (255, self.Ann.colorG, self.Ann.colorB, 26)
        pygame.draw.polygon(surface, color, points)
        pygame.draw.aalines(surface, color, True, points)

    def draw_thruster_indicators(self, surface):
        """Draw direction arrows for every thruster; highlight active outputs."""
        output_start = self.Ann.hiddenSize + len(self.Ann.poly) + 2
        outputs = self.Ann.neurons[output_start:]
        thrusters = [
            (index, neuron.out)
            for index, neuron in enumerate(outputs)
            if index != 4
        ]
        vectors = self._thruster_vectors([index for index, _ in thrusters])
        for (_, activation), (vertex_x, vertex_y) in zip(thrusters, vectors):
            vector_length = math.hypot(vertex_x, vertex_y)
            if vector_length == 0:
                continue

            direction = 1 if activation > 0 else -1
            start_x = self.centerpos.x + vertex_x
            start_y = self.centerpos.y + vertex_y
            arrow_length = 8
            end_x = start_x + direction * vertex_x / vector_length * arrow_length
            end_y = start_y + direction * vertex_y / vector_length * arrow_length
            start = (round(start_x), round(start_y))
            end = (round(end_x), round(end_y))

            angle = math.atan2(end_y - start_y, end_x - start_x)
            arrow_head_length = 3
            base_x = end_x - arrow_head_length * math.cos(angle)
            base_y = end_y - arrow_head_length * math.sin(angle)
            color = (255, 255, 0) if abs(activation) >= 0.05 else (90, 150, 170)
            line_width = 2 if abs(activation) >= 0.05 else 1
            pygame.draw.line(
                surface,
                color,
                start,
                (round(base_x), round(base_y)),
                line_width,
            )
            for side in (-1, 1):
                head_x = base_x + side * arrow_head_length / 2 * math.sin(angle)
                head_y = base_y - side * arrow_head_length / 2 * math.cos(angle)
                pygame.draw.line(
                    surface,
                    color,
                    end,
                    (round(head_x), round(head_y)),
                    line_width,
                )

    def _thruster_vectors(self, output_indices):
        """Map actuator outputs to rotated local vectors using saved node positions."""
        local_vectors = self.Ann.thrusterVectors(output_indices)
        angle = math.radians(self.angle())
        cosine = math.cos(angle)
        sine = math.sin(angle)
        vectors = []

        for local_x, local_y in local_vectors:
            vectors.append(
                (
                    local_x * cosine - local_y * sine,
                    local_x * sine + local_y * cosine,
                )
            )

        return vectors

    def truster(self, activations, rotation):
        """Apply angular rotation and each indexed linear thruster impulse."""
        trust_center = b2Vec2(self.centerpos.x, self.centerpos.y)
        self.body.ApplyAngularImpulse(rotation, wake=True)
        vectors = self._thruster_vectors([index for index, _ in activations])
        for (_, activation), vector in zip(activations, vectors):
            trust_vector = b2Vec2(vector)
            self.body.ApplyLinearImpulse(
                trust_vector * activation,
                trust_center,
                wake=True,
            )
