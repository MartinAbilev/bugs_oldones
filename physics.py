from Box2D import b2ContactListener, b2PolygonShape, b2World


class ContactListener(b2ContactListener):
    def __init__(self, objects):
        super().__init__()
        self.objects = objects

    def BeginContact(self, contact):
        actor_ids = (contact.fixtureA.body.userData, contact.fixtureB.body.userData)
        if "as" in actor_ids:
            return

        for obj in self.objects:
            if obj.oId in actor_ids:
                obj.lives -= 1


class PhysicsWorld:
    def __init__(self, objects):
        self.world = b2World(
            contactListener=ContactListener(objects),
            gravity=(0, 1),
            doSleep=True,
        )
        self.timeStep = 1.0 / 60
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
