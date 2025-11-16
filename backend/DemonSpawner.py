import Constants

class DemonSpawner:
    def __init__(self, x: int, y: int, target_team: str) -> None:
        self.x = x
        self.y = y
        self.reload_time_max = Constants.DEMON_SPAWNER_RELOAD_TURNS
        self.reload_time_left = self.reload_time_max
        self.target_team = target_team
        self.activation_count = 0
        self.queued = 0