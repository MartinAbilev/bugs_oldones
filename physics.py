from Box2D import b2ContactListener, b2PolygonShape, b2World


class ContactListener(b2ContactListener):
    """Apply creature damage when two non-arena bodies collide."""

    def __init__(self, objects):
        """Retain the shared creature list used to resolve body user data."""
        super().__init__()
        self.objects = objects

    def BeginContact(self, contact):
        """Remove one life from each participating creature."""
        actor_ids = (contact.fixtureA.body.userData, contact.fixtureB.body.userData)
        if "as" in actor_ids:
            return

        for obj in self.objects:
            if obj.oId in actor_ids:
                obj.lives -= 1


class PhysicsWorld:
    """Own the Box2D world, fixed timestep, and arena boundary bodies."""

    def __init__(self, objects):
        """Create a screen-coordinate world and attach its creature contact listener."""
        self.world = b2World(
            contactListener=ContactListener(objects),
            gravity=(0, 1),
            doSleep=True,
        )
        self.timeStep = 1.0 / 60  # Keep physics updates synchronized with the 60 FPS loop.
        for position, size in (
            ((0, 0), (500, 5)),
            ((0, 400), (500, 5)),
            ((0, 0), (5, 500)),
            ((500, 0), (5, 500)),
        ):
            ground = self.world.CreateStaticBody(
                position=position,
                shapes=b2PolygonShape(box=size),
            )
            ground.userData = "passive"
