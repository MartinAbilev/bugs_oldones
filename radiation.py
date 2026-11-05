import math
import random
from dataclasses import dataclass

import pygame

from simulation_utils import rotate_polygon


@dataclass
class RadiationParticle:
    """A faint particle traveling in a straight line through the arena."""

    x: float
    y: float
    velocity_x: float
    velocity_y: float
    age: float = 0.0


@dataclass
class SpiralEmitter:
    """A short-lived emitter that spirals out from a particle impact."""

    x: float
    y: float
    age: float = 0.0
    lifetime: float = 0.65
    phase: float = 0.0
    start_angular_speed: float = 24.0
    end_angular_speed: float = 24.0
    start_radial_speed: float = 7.0
    end_radial_speed: float = 7.0
    radial_acceleration: float = 0.0
    start_eccentricity: float = 0.8
    end_eccentricity: float = 0.8
    start_size: float = 1.0
    end_size: float = 1.0
    start_emission_rate: float = 90.0
    end_emission_rate: float = 90.0
    spiral_onset: float = 0.0
    start_spiral_strength: float = 1.0
    end_spiral_strength: float = 1.0
    spiral_shape: str = "logarithmic"
    emission_remainder: float = 0.0


@dataclass
class TrailPixel:
    """A stationary single-pixel mark that fades after being emitted."""

    x: int
    y: int
    color: tuple[int, int, int]
    age: float = 0.0
    lifetime: float = 1.0


class RadiationField:
    """Draw straight radiation particles and spiral impact-emitter trails."""

    def __init__(self, size):
        self.width, self.height = size
        self.particles = []
        self.emitters = []
        self.trail_pixels = []
        self.spawn_remainder = 0.0
        self.track_surface = pygame.Surface(size, pygame.SRCALPHA)

    def _spawn_particle(self):
        return RadiationParticle(
            x=random.uniform(0, min(self.width, 500)),
            y=-4.0,
            velocity_x=random.uniform(95, 155),
            velocity_y=random.uniform(205, 275),
        )

    @staticmethod
    def _segment_circle_fraction(start, end, center, radius):
        """Return the first intersection fraction between a segment and circle."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        offset_x = start[0] - center[0]
        offset_y = start[1] - center[1]
        a = dx * dx + dy * dy
        c = offset_x * offset_x + offset_y * offset_y - radius * radius
        if c <= 0:
            return 0.0
        if a == 0:
            return None

        b = 2 * (offset_x * dx + offset_y * dy)
        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            return None
        fraction = (-b - math.sqrt(discriminant)) / (2 * a)
        return fraction if 0 <= fraction <= 1 else None

    @staticmethod
    def _collision_targets(creatures):
        targets = []
        for creature in creatures:
            if creature.death != 0:
                continue

            center = (creature.body.position.x, creature.body.position.y)
            targets.append((center, creature.r + 1.5))
            for point in rotate_polygon(creature.Ann.poly, creature.angle()):
                targets.append(
                    (
                        (
                            center[0] + point[0] * 1.2,
                            center[1] + point[1] * 1.2,
                        ),
                        3.5,
                    )
                )
        return targets

    def _find_impact(self, start, end, targets):
        impact = None
        for center, radius in targets:
            fraction = self._segment_circle_fraction(start, end, center, radius)
            if fraction is not None and (impact is None or fraction < impact):
                impact = fraction

        if impact is None:
            return None
        return (
            start[0] + (end[0] - start[0]) * impact,
            start[1] + (end[1] - start[1]) * impact,
        )

    def _spawn_emitter(self, position):
        start_rate = random.uniform(14, 52)
        end_rate = random.uniform(22, 72)
        self.emitters.append(
            SpiralEmitter(
                x=position[0],
                y=position[1],
                phase=random.uniform(0, 2 * math.pi),
                lifetime=random.uniform(0.45, 1.0),
                start_angular_speed=start_rate,
                end_angular_speed=end_rate,
                start_radial_speed=random.uniform(2, 8),
                end_radial_speed=random.uniform(5, 14),
                radial_acceleration=random.uniform(-4, 12),
                start_eccentricity=random.uniform(0.3, 1.0),
                end_eccentricity=random.uniform(0.3, 1.0),
                start_size=random.uniform(0.5, 1.3),
                end_size=random.uniform(0.8, 2.2),
                start_emission_rate=random.uniform(55, 110),
                end_emission_rate=random.uniform(75, 160),
                spiral_onset=random.uniform(0, 0.72),
                start_spiral_strength=random.uniform(0.15, 1.4),
                end_spiral_strength=random.uniform(0.15, 1.8),
                spiral_shape=random.choice(("logarithmic", "golden", "irregular")),
            )
        )

    @staticmethod
    def _emitter_position(emitter, age):
        progress = max(0.0, min(1.0, age / emitter.lifetime))
        eased_progress = progress * progress * (3 - 2 * progress)
        radial_speed = (
            emitter.start_radial_speed
            + (emitter.end_radial_speed - emitter.start_radial_speed)
            * eased_progress
        )
        size = emitter.start_size + (emitter.end_size - emitter.start_size) * progress
        eccentricity = (
            emitter.start_eccentricity
            + (emitter.end_eccentricity - emitter.start_eccentricity) * progress
        )
        radius = size * (
            radial_speed * age + 0.5 * emitter.radial_acceleration * age * age
        )

        spin_progress = max(
            0.0,
            min(1.0, (progress - emitter.spiral_onset) / (1 - emitter.spiral_onset)),
        )
        spiral_strength = (
            emitter.start_spiral_strength
            + (emitter.end_spiral_strength - emitter.start_spiral_strength)
            * eased_progress
        )
        angular_speed = (
            emitter.start_angular_speed
            + (emitter.end_angular_speed - emitter.start_angular_speed) * progress
        )
        turns = angular_speed * age * spiral_strength * spin_progress
        if emitter.spiral_shape == "golden":
            # Logarithmic radial growth approximates the expanding Fibonacci spiral.
            golden_ratio = (1 + math.sqrt(5)) / 2
            turn_fraction = turns / (2 * math.pi)
            golden_growth = golden_ratio ** min(turn_fraction, 5)
            radius *= 0.35 + 0.65 * golden_growth
        elif emitter.spiral_shape == "irregular":
            turns += 0.45 * math.sin(progress * math.pi * 3)

        angle = emitter.phase + turns
        return (
            emitter.x + radius * math.cos(angle),
            emitter.y + radius * eccentricity * math.sin(angle),
        )

    def _update_emitters(self, delta_time):
        active_emitters = []
        for emitter in self.emitters:
            previous_age = emitter.age
            emitter.age = min(emitter.lifetime, emitter.age + delta_time * 2)
            active_time = emitter.age - previous_age
            progress = emitter.age / emitter.lifetime
            emission_rate = (
                emitter.start_emission_rate
                + (emitter.end_emission_rate - emitter.start_emission_rate)
                * progress
            )
            emitter.emission_remainder += active_time * emission_rate
            pixel_count = int(emitter.emission_remainder)
            emitter.emission_remainder -= pixel_count

            for pixel_index in range(pixel_count):
                sample_age = previous_age + (pixel_index + 1) / pixel_count * active_time
                x, y = self._emitter_position(emitter, sample_age)
                pixel_x = round(x)
                pixel_y = round(y)
                if 0 <= pixel_x < self.width and 0 <= pixel_y < self.height:
                    self.trail_pixels.append(
                        TrailPixel(
                            pixel_x,
                            pixel_y,
                            color=(
                                random.choice((135, 165, 195)),
                                random.choice((205, 230, 250)),
                                255,
                            ),
                            lifetime=emitter.lifetime * random.uniform(0.65, 1.5),
                        )
                    )

            if emitter.age < emitter.lifetime:
                active_emitters.append(emitter)
        self.emitters = active_emitters

    def _draw_trail_pixels(self, delta_time):
        self.track_surface.fill((0, 0, 0, 0))
        active_pixels = []
        for mark in self.trail_pixels:
            mark.age += delta_time
            if mark.age >= mark.lifetime:
                continue

            alpha = round(160 * (1 - mark.age / mark.lifetime))
            self.track_surface.set_at(
                (mark.x, mark.y),
                (*mark.color, alpha),
            )
            active_pixels.append(mark)
        self.trail_pixels = active_pixels

    def update_and_draw(self, surface, creatures, intensity, delta_time):
        """Advance straight rays and render fading pixels from spiral emitters."""
        delta_time = max(0.0, min(delta_time, 0.05))
        intensity = max(0.0, min(float(intensity), 2.0))
        self.spawn_remainder += intensity * 12 * delta_time
        spawn_count = int(self.spawn_remainder)
        self.spawn_remainder -= spawn_count
        for _ in range(spawn_count):
            self.particles.append(self._spawn_particle())

        collision_targets = self._collision_targets(creatures)
        active_particles = []
        for particle in self.particles:
            start = (particle.x, particle.y)
            end = (
                particle.x + particle.velocity_x * delta_time,
                particle.y + particle.velocity_y * delta_time,
            )
            impact = self._find_impact(start, end, collision_targets)
            if impact is not None:
                self._spawn_emitter(impact)
                continue

            particle.x, particle.y = end
            particle.age += delta_time
            if particle.y > self.height or particle.x > min(self.width, 520):
                continue

            tail = (
                round(particle.x - particle.velocity_x * 0.035),
                round(particle.y - particle.velocity_y * 0.035),
            )
            head = (round(particle.x), round(particle.y))
            pygame.draw.line(surface, (80, 146, 174), tail, head, 1)
            active_particles.append(particle)

        self.particles = active_particles
        self._update_emitters(delta_time)
        self._draw_trail_pixels(delta_time)
