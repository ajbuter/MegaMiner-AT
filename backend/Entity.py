import Constants

class Entity:
    def __init__(self, health: int, x : int, y : int):
        self.x = x
        self.y = y
        self.health = health
        self.name = 'NO NAME'